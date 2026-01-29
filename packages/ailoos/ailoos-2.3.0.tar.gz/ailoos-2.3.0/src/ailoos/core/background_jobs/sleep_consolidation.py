"""
Worker en segundo plano para consolidación REM Sleep.
Realiza optimizaciones y limpieza del sistema durante períodos de inactividad.
Preparación para FASE 4.
"""

import asyncio
import threading
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
import psutil
import gc

try:
    import torch
except ImportError:
    torch = None

from ...utils.logging import get_logger
from ..state_manager import get_tensor_state_manager
from ...inference.memory_manager import get_memory_manager
from ...inference.memory.adversarial_dreamer import DreamCritiqueResult


class ConsolidationPhase(Enum):
    """Fases de consolidación REM."""
    LIGHT_SLEEP = "light_sleep"      # Optimizaciones ligeras
    DEEP_SLEEP = "deep_sleep"        # Optimizaciones profundas
    REM_SLEEP = "rem_sleep"          # Consolidación de memoria neural


@dataclass
class ConsolidationMetrics:
    """Métricas de consolidación."""
    start_time: datetime
    end_time: Optional[datetime] = None
    phase: ConsolidationPhase = ConsolidationPhase.LIGHT_SLEEP
    memory_freed_mb: float = 0.0
    tensors_consolidated: int = 0
    models_optimized: int = 0
    cache_cleaned_mb: float = 0.0
    errors: List[str] = None

    def __post_init__(self):
        if self.errors is None:
            self.errors = []


class REMSleepConsolidationWorker:
    """
    Worker en segundo plano para consolidación REM Sleep.
    Ejecuta tareas de mantenimiento y optimización durante períodos de baja actividad.
    """

    def __init__(self, consolidation_interval_hours: int = 6,
                 deep_sleep_threshold_hours: int = 24,
                 rem_sleep_threshold_hours: int = 72):
        self.logger = get_logger(__name__)

        self.consolidation_interval = timedelta(hours=consolidation_interval_hours)
        self.deep_sleep_threshold = timedelta(hours=deep_sleep_threshold_hours)
        self.rem_sleep_threshold = timedelta(hours=rem_sleep_threshold_hours)

        # Estado del worker
        self.running = False
        self.worker_task: Optional[asyncio.Task] = None
        self.last_consolidation = datetime.now()
        self.system_idle_start: Optional[datetime] = None

        # Dependencias
        self.tensor_state_manager = get_tensor_state_manager()
        self.memory_manager = get_memory_manager()

        # Historial de consolidaciones
        self.consolidation_history: List[ConsolidationMetrics] = []

        # Locks
        self.lock = threading.RLock()

        self.logger.info("REM Sleep Consolidation Worker inicializado")

    async def start(self):
        """Iniciar el worker de consolidación."""
        if self.running:
            return

        self.running = True
        self.worker_task = asyncio.create_task(self._consolidation_loop())
        self.logger.info("Worker de consolidación REM Sleep iniciado")

    async def stop(self):
        """Detener el worker de consolidación."""
        self.running = False
        if self.worker_task:
            self.worker_task.cancel()
            try:
                await self.worker_task
            except asyncio.CancelledError:
                pass
        self.logger.info("Worker de consolidación REM Sleep detenido")

    async def _consolidation_loop(self):
        """Loop principal de consolidación."""
        while self.running:
            try:
                await self._check_consolidation_trigger()
                await asyncio.sleep(300)  # Verificar cada 5 minutos

            except Exception as e:
                self.logger.error(f"Error en consolidation loop: {e}")
                await asyncio.sleep(60)

    async def _check_consolidation_trigger(self):
        """Verificar si se debe iniciar una consolidación usando scheduler inteligente."""
        try:
            # Importar scheduler (lazy import)
            from ...inference.memory.sleep_scheduler import get_sleep_scheduler

            scheduler = get_sleep_scheduler()

            # Obtener decisión del scheduler
            decision = scheduler.force_consolidation_check()

            # Verificar si debemos consolidar
            if not decision.should_consolidate:
                self.logger.debug(f"Scheduler indica no consolidar: {decision.reasoning}")
                return

            # Determinar fase basada en tiempo desde última consolidación
            now = datetime.now()
            time_since_last = now - self.last_consolidation

            if time_since_last >= self.rem_sleep_threshold:
                phase = ConsolidationPhase.REM_SLEEP
            elif time_since_last >= self.deep_sleep_threshold:
                phase = ConsolidationPhase.DEEP_SLEEP
            elif time_since_last >= self.consolidation_interval:
                phase = ConsolidationPhase.LIGHT_SLEEP
            else:
                # Scheduler dice consolidar pero no ha pasado tiempo suficiente
                # Forzar light sleep si scheduler tiene alta confianza
                if decision.optimal_window and decision.optimal_window.confidence_score > 0.8:
                    phase = ConsolidationPhase.LIGHT_SLEEP
                    self.logger.info("Forzando consolidación por alta confianza del scheduler")
                else:
                    return

            # Verificación adicional de actividad del sistema (fallback)
            if self._system_is_active():
                self.logger.debug("Sistema activo según verificación adicional, postponiendo consolidación")
                return

            self.logger.info(f"Iniciando consolidación {phase.value} - Scheduler: {decision.reasoning}")
            await self._perform_consolidation(phase)

        except Exception as e:
            self.logger.warning(f"Error usando scheduler, cayendo a lógica básica: {e}")
            # Fallback a lógica original
            await self._fallback_consolidation_check()

    async def _fallback_consolidation_check(self):
        """Verificación de consolidación básica (fallback cuando scheduler falla)."""
        now = datetime.now()
        time_since_last = now - self.last_consolidation

        # Determinar fase basada en tiempo de inactividad
        if time_since_last >= self.rem_sleep_threshold:
            phase = ConsolidationPhase.REM_SLEEP
        elif time_since_last >= self.deep_sleep_threshold:
            phase = ConsolidationPhase.DEEP_SLEEP
        elif time_since_last >= self.consolidation_interval:
            phase = ConsolidationPhase.LIGHT_SLEEP
        else:
            return  # No consolidar aún

        # Verificar actividad del sistema
        if self._system_is_active():
            self.logger.debug("Sistema activo, postponiendo consolidación")
            return

        self.logger.info(f"Iniciando consolidación {phase.value} (fallback)")
        await self._perform_consolidation(phase)

    def _system_is_active(self) -> bool:
        """Verificar si el sistema está activo."""
        try:
            # Verificar uso de CPU
            cpu_percent = psutil.cpu_percent(interval=1)
            if cpu_percent > 50:  # Más del 50% de CPU en uso
                return True

            # Verificar conexiones de red activas
            net_connections = len(psutil.net_connections())
            if net_connections > 10:  # Muchas conexiones activas
                return True

            # Verificar procesos activos relacionados con ML/inferencia
            ml_processes = 0
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent']):
                try:
                    if any(keyword in proc.info['name'].lower() for keyword in
                          ['python', 'torch', 'cuda', 'inference', 'training']):
                        if proc.info['cpu_percent'] > 5:
                            ml_processes += 1
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue

            return ml_processes > 2  # Más de 2 procesos ML activos

        except Exception as e:
            self.logger.warning(f"Error verificando actividad del sistema: {e}")
            return True  # Asumir activo si hay error

    async def _perform_consolidation(self, phase: ConsolidationPhase):
        """Ejecutar la consolidación para la fase especificada."""
        metrics = ConsolidationMetrics(
            start_time=datetime.now(),
            phase=phase
        )

        try:
            # Ejecutar tareas según la fase
            if phase == ConsolidationPhase.LIGHT_SLEEP:
                await self._light_sleep_consolidation(metrics)
            elif phase == ConsolidationPhase.DEEP_SLEEP:
                await self._deep_sleep_consolidation(metrics)
            elif phase == ConsolidationPhase.REM_SLEEP:
                await self._rem_sleep_consolidation(metrics)

            # Limpiar memoria
            await self._memory_cleanup(metrics)

            # Actualizar métricas finales
            metrics.end_time = datetime.now()
            self.consolidation_history.append(metrics)
            self.last_consolidation = datetime.now()

            # Mantener solo las últimas 10 consolidaciones
            if len(self.consolidation_history) > 10:
                self.consolidation_history = self.consolidation_history[-10:]

            self.logger.info(f"Consolidación {phase.value} completada exitosamente")

        except Exception as e:
            metrics.errors.append(str(e))
            metrics.end_time = datetime.now()
            self.consolidation_history.append(metrics)
            self.logger.error(f"Error en consolidación {phase.value}: {e}")

    async def _light_sleep_consolidation(self, metrics: ConsolidationMetrics):
        """Consolidación de sueño ligero: optimizaciones básicas."""
        self.logger.info("Ejecutando consolidación de sueño ligero")

        # Limpiar tensores antiguos
        deleted = self.tensor_state_manager.cleanup_old_tensors(days=7)
        metrics.tensors_consolidated = deleted

        # Liberar páginas de memoria no utilizadas
        memory_stats = self.memory_manager.get_memory_stats()
        initial_memory = memory_stats.gpu_used + memory_stats.cpu_used

        # Paginar tensores de baja prioridad
        paged_out = self.memory_manager.page_out_least_recently_used()
        metrics.memory_freed_mb = (initial_memory - (memory_stats.gpu_used + memory_stats.cpu_used)) / (1024 * 1024)

        # Limpiar cache de PyTorch si está disponible
        if torch and torch.cuda.is_available():
            torch.cuda.empty_cache()

        self.logger.info(f"Sueño ligero: {deleted} tensores limpiados, {paged_out} páginas movidas")

    async def _deep_sleep_consolidation(self, metrics: ConsolidationMetrics):
        """Consolidación de sueño profundo: optimizaciones avanzadas."""
        self.logger.info("Ejecutando consolidación de sueño profundo")

        # Ejecutar primero light sleep
        await self._light_sleep_consolidation(metrics)

        # Limpiar tensores más antiguos
        deleted_old = self.tensor_state_manager.cleanup_old_tensors(days=30)
        metrics.tensors_consolidated += deleted_old

        # Optimizar ubicación de memoria
        pages = self.memory_manager.list_pages()
        optimized = 0

        for page_id, page in pages.items():
            # Mover tensores de GPU a CPU si no se usan recientemente
            if (page.location.name == 'GPU' and
                datetime.now() - page.last_accessed > timedelta(hours=1) and
                page.priority != page.priority.CRITICAL):
                tensor = self.memory_manager.access_tensor(page_id, 'cpu')
                if tensor is not None:
                    optimized += 1

        metrics.models_optimized = optimized

        # Forzar garbage collection
        gc.collect()

        self.logger.info(f"Sueño profundo: {deleted_old} tensores antiguos limpiados, {optimized} modelos optimizados")

    async def _rem_sleep_consolidation(self, metrics: ConsolidationMetrics):
        """Consolidación REM: consolidación de memoria neural avanzada con destilación inteligente y validación adversarial."""
        self.logger.info("Ejecutando consolidación REM con destilación de memoria y validación adversarial")

        # Ejecutar deep sleep primero
        await self._deep_sleep_consolidation(metrics)

        try:
            # Importar componentes necesarios (lazy import para evitar dependencias circulares)
            from ...inference.memory.memory_distiller import get_memory_distiller
            from ...inference.memory.adversarial_dreamer import create_adversarial_dreamer

            memory_distiller = get_memory_distiller()
            adversarial_dreamer = create_adversarial_dreamer()

            # Fase 1: Recopilar memorias candidatas para destilación
            candidate_memories = await self._collect_memory_candidates()
            self.logger.info(f"Encontradas {len(candidate_memories)} memorias candidatas para destilación")

            if not candidate_memories:
                self.logger.info("No hay memorias candidatas para destilación")
                return

            # Fase 2: Validación adversarial antes de destilación
            self.logger.info("Iniciando validación adversarial de memorias candidatas")
            validation_batch = self._prepare_memories_for_validation(candidate_memories)

            if validation_batch:
                critique_result = adversarial_dreamer.critique_memory_dream(validation_batch)

                # Filtrar memorias basadas en crítica adversarial
                filtered_memories = self._filter_memories_by_critique(candidate_memories, critique_result)

                self.logger.info(f"Validación adversarial completada: {len(filtered_memories)}/{len(candidate_memories)} "
                               f"memorias pasaron validación (acción recomendada: {critique_result.recommended_action})")

                # Registrar problemas críticos
                if critique_result.critical_issues:
                    metrics.errors.extend(critique_result.critical_issues)
                    self.logger.warning(f"Problemas críticos encontrados: {len(critique_result.critical_issues)}")

                # Si la crítica recomienda no consolidar, abortar
                if critique_result.recommended_action in ["discard", "quarantine"]:
                    self.logger.warning(f"Consolidación REM abortada por crítica adversarial: {critique_result.recommended_action}")
                    metrics.errors.append(f"Consolidación abortada: {critique_result.recommended_action}")
                    return

                candidate_memories = filtered_memories
            else:
                self.logger.warning("No se pudieron preparar memorias para validación adversarial")

            # Fase 3: Destilar memorias validadas en lotes
            batch_size = 20  # Procesar en lotes para eficiencia
            distillation_metrics = await memory_distiller.distill_memory_batch(
                candidate_memories, batch_size=batch_size
            )

            # Fase 4: Validación adversarial post-destilación
            if distillation_metrics.distilled_memories:
                self.logger.info("Validando memorias destiladas con Adversarial Dreamer")
                distilled_validation_batch = self._prepare_distilled_memories_for_validation(
                    distillation_metrics.distilled_memories
                )

                if distilled_validation_batch:
                    post_critique = adversarial_dreamer.critique_memory_dream(distilled_validation_batch)

                    # Filtrar memorias destiladas inconsistentes
                    final_memories = self._filter_memories_by_critique(
                        distillation_metrics.distilled_memories, post_critique
                    )

                    distillation_metrics.distilled_memories = final_memories
                    distillation_metrics.total_memories_processed = len(final_memories)

                    self.logger.info(f"Validación post-destilación: {len(final_memories)} memorias finales")

            # Fase 5: Integrar memorias destiladas y validadas en RAG
            await self._integrate_distilled_memories(distillation_metrics)

            # Actualizar métricas
            metrics.tensors_consolidated += distillation_metrics.total_memories_processed
            metrics.memory_freed_mb += distillation_metrics.memory_saved_mb
            metrics.models_optimized += 1  # Contar como optimización de modelo

            # Registrar errores si los hay
            if distillation_metrics.errors:
                metrics.errors.extend(distillation_metrics.errors)
                self.logger.warning(f"Errores en destilación: {len(distillation_metrics.errors)}")

            self.logger.info(f"Consolidación REM completada: {distillation_metrics.total_memories_processed} "
                           f"memorias destiladas y validadas, ratio compresión: {distillation_metrics.total_compression_ratio:.2f}")

        except Exception as e:
            error_msg = f"Error en consolidación REM: {e}"
            metrics.errors.append(error_msg)
            self.logger.error(error_msg)

    async def _collect_memory_candidates(self) -> List[str]:
        """Recopilar IDs de memorias candidatas para destilación durante REM sleep."""
        candidates = []

        try:
            # Recopilar de memory_manager
            memory_pages = self.memory_manager.list_pages()
            for page_id, page in memory_pages.items():
                # Candidatos: páginas no accedidas recientemente pero con alto uso histórico
                if (hasattr(page, 'last_accessed') and
                    hasattr(page, 'access_count') and
                    page.access_count > 5):  # Al menos 5 accesos

                    time_since_access = datetime.now() - page.last_accessed
                    if time_since_access > timedelta(hours=12):  # No accedida en 12+ horas
                        candidates.append(page_id)

            # Recopilar de tensor_state_manager
            tensor_metadata = self.tensor_state_manager.list_tensors()
            for tensor_name, metadata in tensor_metadata.items():
                # Candidatos: tensores antiguos pero no limpiados aún
                time_since_creation = datetime.now() - metadata.created_at
                if time_since_creation > timedelta(days=1):  # Más de 1 día
                    candidates.append(tensor_name)

            # Limitar número de candidatos para evitar sobrecarga
            max_candidates = 100
            if len(candidates) > max_candidates:
                # Priorizar por tamaño (más grandes primero para mayor beneficio de compresión)
                candidates_with_size = []
                for candidate in candidates[:max_candidates * 2]:  # Extra para filtrar
                    try:
                        # Estimar tamaño (aproximado)
                        if candidate in memory_pages:
                            page = memory_pages[candidate]
                            size = page.size_bytes if hasattr(page, 'size_bytes') else 1024 * 1024  # 1MB default
                        else:
                            size = 1024 * 1024  # 1MB default para tensores
                        candidates_with_size.append((candidate, size))
                    except:
                        candidates_with_size.append((candidate, 0))

                # Ordenar por tamaño descendente y tomar top max_candidates
                candidates_with_size.sort(key=lambda x: x[1], reverse=True)
                candidates = [c[0] for c in candidates_with_size[:max_candidates]]

        except Exception as e:
            self.logger.warning(f"Error recopilando candidatos de memoria: {e}")

        return candidates

    async def _integrate_distilled_memories(self, distillation_metrics):
        """Integrar memorias destiladas en el sistema RAG."""
        try:
            # Importar vector store (lazy import)
            from ...rag.core.vector_store import get_vector_store

            vector_store = get_vector_store()

            # Importar destilador para obtener memorias destiladas
            from ...inference.memory.memory_distiller import get_memory_distiller

            memory_distiller = get_memory_distiller()

            # Obtener memorias destiladas recientes
            distilled_memories = memory_distiller.get_distilled_memories(min_importance=0.5)

            integrated_count = 0
            for memory_id, distilled_memory in distilled_memories.items():
                try:
                    # Crear documento para RAG
                    document = {
                        'id': f"distilled_{memory_id}",
                        'content': f"Memoria neural destilada: {memory_id}",
                        'metadata': {
                            **distilled_memory.metadata,
                            'importance_score': distilled_memory.importance_score,
                            'compression_ratio': distilled_memory.compression_ratio,
                            'source': 'rem_consolidation'
                        },
                        'vector': distilled_memory.vector.tolist()
                    }

                    # Integrar en vector store
                    await vector_store.add_document(document)
                    integrated_count += 1

                except Exception as e:
                    self.logger.warning(f"Error integrando memoria destilada {memory_id}: {e}")

            self.logger.info(f"Integradas {integrated_count} memorias destiladas en RAG")

        except Exception as e:
            self.logger.error(f"Error integrando memorias destiladas: {e}")

    async def _memory_cleanup(self, metrics: ConsolidationMetrics):
        """Limpieza general de memoria."""
        try:
            # Forzar garbage collection
            collected = gc.collect()
            self.logger.debug(f"GC recolectó {collected} objetos")

            # Limpiar cache de CUDA
            if torch and torch.cuda.is_available():
                torch.cuda.empty_cache()
                freed_memory = torch.cuda.memory_reserved() - torch.cuda.memory_allocated()
                metrics.cache_cleaned_mb = freed_memory / (1024 * 1024)

            # Limpiar archivos temporales
            # (implementación específica del sistema)

        except Exception as e:
            self.logger.warning(f"Error en limpieza de memoria: {e}")

    def get_consolidation_history(self) -> List[ConsolidationMetrics]:
        """Obtener historial de consolidaciones."""
        with self.lock:
            return self.consolidation_history.copy()

    def get_last_consolidation_info(self) -> Optional[ConsolidationMetrics]:
        """Obtener información de la última consolidación."""
        with self.lock:
            return self.consolidation_history[-1] if self.consolidation_history else None

    def force_consolidation(self, phase: ConsolidationPhase = ConsolidationPhase.LIGHT_SLEEP):
        """Forzar una consolidación inmediata (para testing/debugging)."""
        async def _force():
            await self._perform_consolidation(phase)

        # Ejecutar en el loop de eventos actual
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # Si el loop ya está corriendo, crear una tarea
                loop.create_task(_force())
            else:
                loop.run_until_complete(_force())
        except Exception as e:
            self.logger.error(f"Error forzando consolidación: {e}")

    def get_system_idle_time(self) -> Optional[timedelta]:
        """Obtener tiempo de inactividad del sistema."""
        if self.system_idle_start:
            return datetime.now() - self.system_idle_start
        return None

    def _prepare_memories_for_validation(self, candidate_memories: List[str]) -> List[Dict[str, Any]]:
        """
        Prepara memorias candidatas para validación adversarial.

        Args:
            candidate_memories: Lista de IDs de memorias candidatas

        Returns:
            Lista de diccionarios con datos de memoria para validación
        """
        validation_batch = []

        try:
            # Convertir IDs de memoria a formato de validación
            for memory_id in candidate_memories[:50]:  # Limitar para eficiencia
                try:
                    # Intentar obtener datos de memoria del memory_manager
                    memory_data = self.memory_manager.get_memory_data(memory_id)
                    if memory_data:
                        # Formatear para Adversarial Dreamer
                        validation_memory = {
                            'id': memory_id,
                            'content': memory_data.get('content', ''),
                            'embedding': memory_data.get('embedding'),
                            'vector': memory_data.get('vector'),
                            'timestamp': memory_data.get('timestamp', time.time()),
                            'type': memory_data.get('type', 'unknown'),
                            'facts': memory_data.get('facts', []),
                            'semantic_tags': memory_data.get('semantic_tags', []),
                            'causes': memory_data.get('causes', []),
                            'effects': memory_data.get('effects', [])
                        }
                        validation_batch.append(validation_memory)
                except Exception as e:
                    self.logger.warning(f"Error preparando memoria {memory_id} para validación: {e}")
                    continue

        except Exception as e:
            self.logger.error(f"Error general preparando memorias para validación: {e}")

        return validation_batch

    def _filter_memories_by_critique(
        self,
        candidate_memories: List[str],
        critique_result: DreamCritiqueResult
    ) -> List[str]:
        """
        Filtra memorias basadas en resultados de crítica adversarial.

        Args:
            candidate_memories: Lista original de IDs de memorias
            critique_result: Resultado de la crítica adversarial

        Returns:
            Lista filtrada de IDs de memorias
        """
        filtered_memories = []

        # Crear mapping de memory_id a validation result
        validation_map = {vr.memory_id: vr for vr in critique_result.validation_results}

        for memory_id in candidate_memories:
            validation_result = validation_map.get(memory_id)
            if validation_result:
                # Incluir memoria si es consistente y no tiene problemas críticos
                if (validation_result.is_consistent and
                    validation_result.hallucination_probability <= 0.3 and
                    validation_result.contradiction_score <= 0.5):
                    filtered_memories.append(memory_id)
                else:
                    self.logger.debug(f"Memoria {memory_id} filtrada por validación: "
                                    f"consistente={validation_result.is_consistent}, "
                                    f"alucinación={validation_result.hallucination_probability:.3f}")
            else:
                # Si no hay resultado de validación, incluir por defecto
                filtered_memories.append(memory_id)

        return filtered_memories

    def _prepare_distilled_memories_for_validation(self, distilled_memories: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Prepara memorias destiladas para validación post-destilación.

        Args:
            distilled_memories: Lista de memorias destiladas

        Returns:
            Lista formateada para validación adversarial
        """
        validation_batch = []

        try:
            for distilled_memory in distilled_memories[:30]:  # Limitar para eficiencia
                try:
                    # Formatear memoria destilada para validación
                    validation_memory = {
                        'id': distilled_memory.get('id', f'distilled_{len(validation_batch)}'),
                        'content': distilled_memory.get('content', ''),
                        'embedding': distilled_memory.get('vector'),  # Memorias destiladas tienen 'vector'
                        'vector': distilled_memory.get('vector'),
                        'timestamp': distilled_memory.get('timestamp', time.time()),
                        'type': 'distilled',
                        'importance_score': distilled_memory.get('importance_score', 0.5),
                        'compression_ratio': distilled_memory.get('compression_ratio', 1.0),
                        'facts': distilled_memory.get('facts', []),
                        'semantic_tags': distilled_memory.get('semantic_tags', [])
                    }
                    validation_batch.append(validation_memory)
                except Exception as e:
                    self.logger.warning(f"Error preparando memoria destilada para validación: {e}")
                    continue

        except Exception as e:
            self.logger.error(f"Error general preparando memorias destiladas para validación: {e}")

        return validation_batch


# Instancia global
_rem_sleep_worker: Optional[REMSleepConsolidationWorker] = None


def get_rem_sleep_worker(consolidation_interval_hours: int = 6) -> REMSleepConsolidationWorker:
    """Obtener instancia global del worker de consolidación REM Sleep."""
    global _rem_sleep_worker
    if _rem_sleep_worker is None:
        _rem_sleep_worker = REMSleepConsolidationWorker(consolidation_interval_hours)
    return _rem_sleep_worker