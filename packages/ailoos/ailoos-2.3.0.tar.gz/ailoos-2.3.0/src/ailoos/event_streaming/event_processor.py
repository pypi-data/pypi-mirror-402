import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class ProcessingResult:
    """Resultado del procesamiento de un evento."""
    event: Dict[str, Any]
    processed: bool
    errors: List[str]
    metadata: Dict[str, Any]

class EventProcessor:
    """
    Procesamiento avanzado de eventos para el sistema de streaming.
    Incluye validación, transformación, enriquecimiento y filtrado.
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.running = False
        self.filters = config.get('filters', [])
        self.transformers = config.get('transformers', [])
        self.enrichers = config.get('enrichers', [])
        self.validators = config.get('validators', [])
        self.stats = {
            'events_processed': 0,
            'events_filtered': 0,
            'events_transformed': 0,
            'events_enriched': 0,
            'errors': 0
        }

    async def start(self):
        """Inicia el procesador de eventos."""
        if self.running:
            return
        self.running = True
        logger.info("EventProcessor iniciado")

    async def stop(self):
        """Detiene el procesador de eventos."""
        self.running = False
        logger.info("EventProcessor detenido")

    async def process_event(self, event: Dict[str, Any]) -> ProcessingResult:
        """Procesa un evento individual."""
        if not self.running:
            return ProcessingResult(event, False, ["Procesador no está ejecutándose"], {})

        errors = []
        metadata = {
            'processed_at': datetime.utcnow().isoformat(),
            'original_event': event.copy()
        }

        try:
            # Validación
            if not await self._validate_event(event, errors):
                return ProcessingResult(event, False, errors, metadata)

            # Filtrado
            if not await self._filter_event(event, errors):
                self.stats['events_filtered'] += 1
                return ProcessingResult(event, False, errors, metadata)

            # Transformación
            transformed_event = await self._transform_event(event, errors)
            if transformed_event:
                event = transformed_event
                self.stats['events_transformed'] += 1

            # Enriquecimiento
            enriched_event = await self._enrich_event(event, errors)
            if enriched_event:
                event = enriched_event
                self.stats['events_enriched'] += 1

            self.stats['events_processed'] += 1
            metadata['final_event'] = event
            return ProcessingResult(event, True, errors, metadata)

        except Exception as e:
            self.stats['errors'] += 1
            errors.append(f"Error procesando evento: {str(e)}")
            logger.error(f"Error procesando evento: {e}")
            return ProcessingResult(event, False, errors, metadata)

    async def batch_process(self, events: List[Dict[str, Any]]) -> List[ProcessingResult]:
        """Procesa un lote de eventos."""
        tasks = [self.process_event(event) for event in events]
        return await asyncio.gather(*tasks)

    async def _validate_event(self, event: Dict[str, Any], errors: List[str]) -> bool:
        """Valida el evento según las reglas configuradas."""
        if not isinstance(event, dict):
            errors.append("El evento debe ser un diccionario")
            return False

        if 'type' not in event:
            errors.append("El evento debe tener un campo 'type'")
            return False

        # Validaciones adicionales
        for validator in self.validators:
            try:
                if not await self._run_validator(validator, event):
                    errors.append(f"Validación fallida: {validator}")
                    return False
            except Exception as e:
                errors.append(f"Error en validador {validator}: {e}")
                return False

        return True

    async def _filter_event(self, event: Dict[str, Any], errors: List[str]) -> bool:
        """Filtra el evento según las reglas configuradas."""
        for filter_rule in self.filters:
            try:
                if not await self._apply_filter(filter_rule, event):
                    return False
            except Exception as e:
                errors.append(f"Error aplicando filtro {filter_rule}: {e}")
                return False
        return True

    async def _transform_event(self, event: Dict[str, Any], errors: List[str]) -> Optional[Dict[str, Any]]:
        """Transforma el evento según las reglas configuradas."""
        transformed = event.copy()
        for transformer in self.transformers:
            try:
                result = await self._apply_transformer(transformer, transformed)
                if result:
                    transformed = result
            except Exception as e:
                errors.append(f"Error aplicando transformador {transformer}: {e}")
                return None
        return transformed

    async def _enrich_event(self, event: Dict[str, Any], errors: List[str]) -> Optional[Dict[str, Any]]:
        """Enriquece el evento con información adicional."""
        enriched = event.copy()
        enriched['processed_at'] = datetime.utcnow().isoformat()
        enriched['processor_version'] = '1.0'

        for enricher in self.enrichers:
            try:
                result = await self._apply_enricher(enricher, enriched)
                if result:
                    enriched = result
            except Exception as e:
                errors.append(f"Error aplicando enricher {enricher}: {e}")
                return None
        return enriched

    async def _run_validator(self, validator: str, event: Dict[str, Any]) -> bool:
        """Ejecuta un validador específico."""
        # Implementación básica - se puede extender
        if validator == 'required_fields':
            required = ['type', 'timestamp']
            return all(field in event for field in required)
        return True

    async def _apply_filter(self, filter_rule: str, event: Dict[str, Any]) -> bool:
        """Aplica una regla de filtrado."""
        # Implementación básica - se puede extender
        if filter_rule.startswith('type!='):
            forbidden_type = filter_rule.split('!=')[1]
            return event.get('type') != forbidden_type
        return True

    async def _apply_transformer(self, transformer: str, event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Aplica un transformador."""
        # Implementación básica - se puede extender
        if transformer == 'lowercase_keys':
            return {k.lower(): v for k, v in event.items()}
        return event

    async def _apply_enricher(self, enricher: str, event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Aplica un enricher."""
        # Implementación básica - se puede extender
        if enricher == 'add_id':
            event['id'] = f"event_{datetime.utcnow().timestamp()}"
        return event

    def get_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas del procesador."""
        return self.stats.copy()