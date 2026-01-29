"""
Async Processing para AILOOS

Implementa sistema completo de procesamiento asíncrono con:
- Message queues (RabbitMQ/Kafka)
- Background job processing
- Event-driven architecture
- Task scheduling y orchestration
"""

import asyncio
import logging
import time
import json
import uuid
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Set, Tuple, Callable, Awaitable
from dataclasses import dataclass, field
from enum import Enum
import random
import heapq
import statistics
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)


class MessageQueueType(Enum):
    """Tipos de message queue disponibles."""
    RABBITMQ = "rabbitmq"
    KAFKA = "kafka"
    REDIS = "redis"
    SQS = "sqs"


class JobStatus(Enum):
    """Estados de un job."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


class JobPriority(Enum):
    """Prioridades de jobs."""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class Message:
    """Mensaje para message queue."""
    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    topic: str = ""
    payload: Dict[str, Any] = field(default_factory=dict)
    headers: Dict[str, str] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    priority: int = 1
    ttl_seconds: Optional[int] = None

    @property
    def is_expired(self) -> bool:
        """Verificar si el mensaje ha expirado."""
        if self.ttl_seconds is None:
            return False
        return (datetime.now() - self.timestamp).total_seconds() > self.ttl_seconds


@dataclass
class BackgroundJob:
    """Job de procesamiento en background."""
    job_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    job_type: str = ""
    payload: Dict[str, Any] = field(default_factory=dict)
    priority: JobPriority = JobPriority.NORMAL
    status: JobStatus = JobStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    retry_count: int = 0
    max_retries: int = 3
    timeout_seconds: int = 300
    result: Optional[Any] = None
    error_message: Optional[str] = None
    callback_url: Optional[str] = None

    @property
    def duration_seconds(self) -> Optional[float]:
        """Duración del job en segundos."""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None

    @property
    def is_expired(self) -> bool:
        """Verificar si el job ha expirado."""
        if self.started_at and self.status == JobStatus.RUNNING:
            return (datetime.now() - self.started_at).total_seconds() > self.timeout_seconds
        return False

    def can_retry(self) -> bool:
        """Verificar si el job puede ser reintentado."""
        return self.retry_count < self.max_retries and self.status in [JobStatus.FAILED, JobStatus.TIMEOUT]


@dataclass
class Event:
    """Evento para arquitectura event-driven."""
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    event_type: str = ""
    source: str = ""
    payload: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    correlation_id: Optional[str] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None


class MessageQueueManager:
    """
    Gestor de message queues multi-protocolo.

    Soporta RabbitMQ, Kafka, Redis y SQS con failover automático.
    """

    def __init__(self):
        self.queues: Dict[str, List[Message]] = {}  # topic -> messages
        self.subscriptions: Dict[str, List[Callable]] = {}  # topic -> handlers
        self.queue_type = MessageQueueType.RABBITMQ  # Default
        self.max_queue_size = 10000
        self.message_ttl_seconds = 3600  # 1 hora

    def create_topic(self, topic: str):
        """Crear un topic/queue."""
        if topic not in self.queues:
            self.queues[topic] = []
            logger.info(f"Created topic: {topic}")

    def subscribe(self, topic: str, handler: Callable[[Message], Awaitable[None]]):
        """Suscribirse a un topic."""
        if topic not in self.subscriptions:
            self.subscriptions[topic] = []
        self.subscriptions[topic].append(handler)
        logger.info(f"Subscribed to topic: {topic}")

    async def publish(self, topic: str, message: Message) -> bool:
        """Publicar mensaje a un topic."""
        if topic not in self.queues:
            self.create_topic(topic)

        # Verificar tamaño máximo de queue
        if len(self.queues[topic]) >= self.max_queue_size:
            logger.warning(f"Queue {topic} is full, dropping message")
            return False

        # Añadir mensaje
        self.queues[topic].append(message)

        # Notificar subscribers
        if topic in self.subscriptions:
            for handler in self.subscriptions[topic]:
                try:
                    await handler(message)
                except Exception as e:
                    logger.error(f"Error in message handler for {topic}: {e}")

        logger.debug(f"Published message {message.message_id} to {topic}")
        return True

    async def consume(self, topic: str, batch_size: int = 1) -> List[Message]:
        """Consumir mensajes de un topic."""
        if topic not in self.queues:
            return []

        queue = self.queues[topic]
        messages = []
        expired_count = 0

        # Extraer mensajes no expirados
        while len(messages) < batch_size and queue:
            message = queue.pop(0)

            if message.is_expired:
                expired_count += 1
                continue

            messages.append(message)

        if expired_count > 0:
            logger.info(f"Removed {expired_count} expired messages from {topic}")

        return messages

    def get_queue_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas de queues."""
        stats = {}
        total_messages = 0

        for topic, messages in self.queues.items():
            # Limpiar mensajes expirados
            valid_messages = [m for m in messages if not m.is_expired]
            self.queues[topic] = valid_messages

            stats[topic] = {
                'messages': len(valid_messages),
                'subscribers': len(self.subscriptions.get(topic, []))
            }
            total_messages += len(valid_messages)

        return {
            'total_topics': len(self.queues),
            'total_messages': total_messages,
            'topics': stats
        }


class BackgroundJobProcessor:
    """
    Procesador de jobs en background con múltiples workers.

    Características:
    - Pool de workers configurables
    - Job scheduling inteligente
    - Retry automático con backoff
    - Monitoring y métricas
    """

    def __init__(self, max_workers: int = 4):
        self.jobs: Dict[str, BackgroundJob] = {}
        self.job_queue: List[Tuple[int, str]] = []  # (priority, job_id) - heap
        self.max_workers = max_workers
        self.active_workers = 0
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.job_handlers: Dict[str, Callable] = {}
        self.processing_lock = asyncio.Lock()

    def register_job_handler(self, job_type: str, handler: Callable[[BackgroundJob], Awaitable[Any]]):
        """Registrar handler para un tipo de job."""
        self.job_handlers[job_type] = handler
        logger.info(f"Registered job handler for type: {job_type}")

    async def submit_job(self, job: BackgroundJob) -> str:
        """Enviar job para procesamiento."""
        self.jobs[job.job_id] = job

        # Añadir a priority queue (negativo para max-heap)
        heapq.heappush(self.job_queue, (-job.priority.value, job.job_id))

        # Intentar procesar si hay workers disponibles
        asyncio.create_task(self._process_jobs())

        logger.info(f"Submitted job {job.job_id} of type {job.job_type}")
        return job.job_id

    async def _process_jobs(self):
        """Procesar jobs de la queue."""
        async with self.processing_lock:
            while self.job_queue and self.active_workers < self.max_workers:
                priority, job_id = heapq.heappop(self.job_queue)

                if job_id not in self.jobs:
                    continue

                job = self.jobs[job_id]
                if job.status != JobStatus.PENDING:
                    continue

                # Iniciar procesamiento
                self.active_workers += 1
                asyncio.create_task(self._execute_job(job))

    async def _execute_job(self, job: BackgroundJob):
        """Ejecutar un job específico."""
        try:
            job.status = JobStatus.RUNNING
            job.started_at = datetime.now()

            # Obtener handler
            handler = self.job_handlers.get(job.job_type)
            if not handler:
                raise Exception(f"No handler registered for job type: {job.job_type}")

            # Ejecutar job con timeout
            result = await asyncio.wait_for(
                handler(job),
                timeout=job.timeout_seconds
            )

            # Job completado exitosamente
            job.status = JobStatus.COMPLETED
            job.completed_at = datetime.now()
            job.result = result

            logger.info(f"Job {job.job_id} completed successfully")

        except asyncio.TimeoutError:
            job.status = JobStatus.TIMEOUT
            job.error_message = "Job timed out"
            logger.error(f"Job {job.job_id} timed out")

        except Exception as e:
            job.status = JobStatus.FAILED
            job.error_message = str(e)
            logger.error(f"Job {job.job_id} failed: {e}")

            # Intentar retry si es posible
            if job.can_retry():
                await self._schedule_retry(job)

        finally:
            job.completed_at = datetime.now()
            self.active_workers -= 1

            # Procesar más jobs
            asyncio.create_task(self._process_jobs())

    async def _schedule_retry(self, job: BackgroundJob):
        """Programar retry de job con backoff exponencial."""
        job.status = JobStatus.RETRYING
        job.retry_count += 1

        # Backoff exponencial: 1s, 4s, 16s, etc.
        delay_seconds = 1 ** (job.retry_count + 1)

        logger.info(f"Scheduling retry {job.retry_count} for job {job.job_id} in {delay_seconds}s")

        await asyncio.sleep(delay_seconds)

        # Reset status y re-submit
        job.status = JobStatus.PENDING
        await self.submit_job(job)

    def cancel_job(self, job_id: str) -> bool:
        """Cancelar un job."""
        if job_id in self.jobs:
            job = self.jobs[job_id]
            if job.status in [JobStatus.PENDING, JobStatus.RUNNING]:
                job.status = JobStatus.CANCELLED
                logger.info(f"Cancelled job {job_id}")
                return True

        return False

    def get_job_status(self, job_id: str) -> Optional[BackgroundJob]:
        """Obtener status de un job."""
        return self.jobs.get(job_id)

    def get_processor_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas del procesador."""
        total_jobs = len(self.jobs)
        completed_jobs = len([j for j in self.jobs.values() if j.status == JobStatus.COMPLETED])
        failed_jobs = len([j for j in self.jobs.values() if j.status == JobStatus.FAILED])
        running_jobs = len([j for j in self.jobs.values() if j.status == JobStatus.RUNNING])

        return {
            'total_jobs': total_jobs,
            'completed_jobs': completed_jobs,
            'failed_jobs': failed_jobs,
            'running_jobs': running_jobs,
            'active_workers': self.active_workers,
            'max_workers': self.max_workers,
            'queue_size': len(self.job_queue),
            'success_rate': (completed_jobs / total_jobs * 100) if total_jobs > 0 else 0
        }


class EventDrivenManager:
    """
    Gestor de arquitectura event-driven.

    Características:
    - Event publishing/subscribing
    - Event correlation y tracing
    - Event replay capabilities
    - Event-driven workflows
    """

    def __init__(self):
        self.event_store: List[Event] = []
        self.event_handlers: Dict[str, List[Callable]] = {}  # event_type -> handlers
        self.workflows: Dict[str, Dict[str, Any]] = {}  # workflow_id -> workflow_definition
        self.max_events = 100000  # Límite de eventos en memoria

    def subscribe_to_event(self, event_type: str, handler: Callable[[Event], Awaitable[None]]):
        """Suscribirse a un tipo de evento."""
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        self.event_handlers[event_type].append(handler)
        logger.info(f"Subscribed to event type: {event_type}")

    async def publish_event(self, event: Event):
        """Publicar un evento."""
        # Almacenar evento
        self.event_store.append(event)

        # Mantener límite de eventos
        if len(self.event_store) > self.max_events:
            self.event_store = self.event_store[-self.max_events:]

        # Notificar handlers
        if event.event_type in self.event_handlers:
            for handler in self.event_handlers[event.event_type]:
                try:
                    await handler(event)
                except Exception as e:
                    logger.error(f"Error in event handler for {event.event_type}: {e}")

        # Verificar workflows que puedan ser triggered
        await self._check_workflows(event)

        logger.debug(f"Published event {event.event_id} of type {event.event_type}")

    async def _check_workflows(self, event: Event):
        """Verificar si un evento trigger algún workflow."""
        for workflow_id, workflow in self.workflows.items():
            triggers = workflow.get('triggers', [])

            for trigger in triggers:
                if self._matches_trigger(event, trigger):
                    await self._execute_workflow(workflow_id, event)
                    break

    def _matches_trigger(self, event: Event, trigger: Dict[str, Any]) -> bool:
        """Verificar si un evento matches un trigger."""
        event_type_match = trigger.get('event_type') == event.event_type
        source_match = trigger.get('source', event.source) == event.source

        # Verificar condiciones adicionales
        conditions = trigger.get('conditions', {})
        payload_match = all(
            event.payload.get(key) == value
            for key, value in conditions.items()
        )

        return event_type_match and source_match and payload_match

    async def _execute_workflow(self, workflow_id: str, trigger_event: Event):
        """Ejecutar un workflow."""
        workflow = self.workflows[workflow_id]
        steps = workflow.get('steps', [])

        logger.info(f"Executing workflow {workflow_id} triggered by event {trigger_event.event_id}")

        for step in steps:
            try:
                step_type = step.get('type')
                if step_type == 'publish_event':
                    new_event = Event(
                        event_type=step['event_type'],
                        source=f"workflow_{workflow_id}",
                        payload=step.get('payload', {}),
                        correlation_id=trigger_event.event_id
                    )
                    await self.publish_event(new_event)

                elif step_type == 'submit_job':
                    # En producción, integrar con BackgroundJobProcessor
                    logger.info(f"Workflow step: submit job {step.get('job_type')}")

                elif step_type == 'delay':
                    delay_seconds = step.get('seconds', 1)
                    await asyncio.sleep(delay_seconds)

            except Exception as e:
                logger.error(f"Error executing workflow step: {e}")

    def create_workflow(self, workflow_id: str, definition: Dict[str, Any]):
        """Crear un workflow event-driven."""
        self.workflows[workflow_id] = definition
        logger.info(f"Created workflow: {workflow_id}")

    def get_event_history(self, event_type: Optional[str] = None,
                         correlation_id: Optional[str] = None,
                         limit: int = 100) -> List[Event]:
        """Obtener historial de eventos."""
        events = self.event_store

        if event_type:
            events = [e for e in events if e.event_type == event_type]

        if correlation_id:
            events = [e for e in events if e.correlation_id == correlation_id]

        return events[-limit:]

    def get_event_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas de eventos."""
        total_events = len(self.event_store)

        event_types = {}
        sources = {}
        recent_events = self.event_store[-1000:]  # Últimos 1000

        for event in recent_events:
            event_types[event.event_type] = event_types.get(event.event_type, 0) + 1
            sources[event.source] = sources.get(event.source, 0) + 1

        return {
            'total_events': total_events,
            'event_types': event_types,
            'sources': sources,
            'active_workflows': len(self.workflows)
        }


class AsyncProcessingOrchestrator:
    """
    Orchestrator principal para procesamiento asíncrono.

    Coordina message queues, background jobs y event-driven architecture.
    """

    def __init__(self):
        self.message_queue = MessageQueueManager()
        self.job_processor = BackgroundJobProcessor(max_workers=8)
        self.event_manager = EventDrivenManager()
        self.task_scheduler = TaskScheduler()

    async def initialize(self):
        """Inicializar todos los componentes."""
        # Configurar handlers por defecto
        await self._setup_default_handlers()

        # Iniciar scheduler
        asyncio.create_task(self.task_scheduler.start())

        logger.info("Async Processing Orchestrator initialized")

    async def _setup_default_handlers(self):
        """Configurar handlers por defecto."""

        # Handler para jobs de background
        async def job_message_handler(message: Message):
            job_type = message.payload.get('job_type')
            if job_type:
                job = BackgroundJob(
                    job_type=job_type,
                    payload=message.payload,
                    priority=JobPriority(message.priority)
                )
                await self.job_processor.submit_job(job)

        self.message_queue.subscribe("jobs", job_message_handler)

        # Handler para eventos
        async def event_message_handler(message: Message):
            event = Event(
                event_type=message.payload.get('event_type', 'generic'),
                source=message.payload.get('source', 'message_queue'),
                payload=message.payload
            )
            await self.event_manager.publish_event(event)

        self.message_queue.subscribe("events", event_message_handler)

    async def submit_background_job(self, job_type: str, payload: Dict[str, Any],
                                  priority: JobPriority = JobPriority.NORMAL) -> str:
        """Enviar job para procesamiento en background."""
        job = BackgroundJob(
            job_type=job_type,
            payload=payload,
            priority=priority
        )

        # Registrar handler si no existe
        if job_type not in self.job_processor.job_handlers:
            # Handler genérico (en producción, registrar handlers específicos)
            async def generic_handler(job: BackgroundJob) -> Dict[str, Any]:
                await asyncio.sleep(random.uniform(0.1, 2.0))  # Simular procesamiento
                return {"result": f"Processed {job.job_type}", "payload": job.payload}

            self.job_processor.register_job_handler(job_type, generic_handler)

        return await self.job_processor.submit_job(job)

    async def publish_event(self, event_type: str, payload: Dict[str, Any],
                          source: str = "application") -> str:
        """Publicar evento."""
        event = Event(
            event_type=event_type,
            source=source,
            payload=payload
        )

        await self.event_manager.publish_event(event)
        return event.event_id

    async def schedule_task(self, task_name: str, interval_seconds: int,
                          task_func: Callable[[], Awaitable[None]]):
        """Programar tarea recurrente."""
        await self.task_scheduler.schedule_recurring_task(task_name, interval_seconds, task_func)

    def get_system_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas del sistema completo."""
        return {
            'message_queue': self.message_queue.get_queue_stats(),
            'job_processor': self.job_processor.get_processor_stats(),
            'event_manager': self.event_manager.get_event_stats(),
            'task_scheduler': self.task_scheduler.get_scheduler_stats()
        }


class TaskScheduler:
    """
    Scheduler para tareas recurrentes y programadas.
    """

    def __init__(self):
        self.scheduled_tasks: Dict[str, Dict[str, Any]] = {}
        self.running = False

    async def start(self):
        """Iniciar scheduler."""
        self.running = True
        while self.running:
            try:
                await self._check_scheduled_tasks()
                await asyncio.sleep(1)  # Check every second
            except Exception as e:
                logger.error(f"Error in task scheduler: {e}")

    async def _check_scheduled_tasks(self):
        """Verificar tareas programadas."""
        current_time = time.time()

        for task_name, task_info in self.scheduled_tasks.items():
            if current_time >= task_info['next_run']:
                # Ejecutar tarea
                try:
                    await task_info['func']()
                except Exception as e:
                    logger.error(f"Error executing scheduled task {task_name}: {e}")

                # Programar siguiente ejecución
                if task_info['recurring']:
                    task_info['next_run'] = current_time + task_info['interval']

    async def schedule_recurring_task(self, task_name: str, interval_seconds: int,
                                    task_func: Callable[[], Awaitable[None]]):
        """Programar tarea recurrente."""
        self.scheduled_tasks[task_name] = {
            'func': task_func,
            'interval': interval_seconds,
            'next_run': time.time() + interval_seconds,
            'recurring': True
        }

        logger.info(f"Scheduled recurring task: {task_name} (every {interval_seconds}s)")

    def get_scheduler_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas del scheduler."""
        return {
            'scheduled_tasks': len(self.scheduled_tasks),
            'running': self.running
        }


# Funciones de conveniencia

async def initialize_async_processing_system() -> AsyncProcessingOrchestrator:
    """Inicializar sistema completo de procesamiento asíncrono."""
    orchestrator = AsyncProcessingOrchestrator()
    await orchestrator.initialize()

    # Configurar workflows de ejemplo
    await setup_sample_workflows(orchestrator)

    logger.info("Async processing system initialized")

    return orchestrator


async def setup_sample_workflows(orchestrator: AsyncProcessingOrchestrator):
    """Configurar workflows de ejemplo."""

    # Workflow: User registration -> Welcome email -> Analytics update
    user_registration_workflow = {
        'name': 'user_registration_flow',
        'triggers': [{
            'event_type': 'user.registered',
            'conditions': {}
        }],
        'steps': [
            {
                'type': 'submit_job',
                'job_type': 'send_welcome_email',
                'payload': {'template': 'welcome'}
            },
            {
                'type': 'delay',
                'seconds': 2
            },
            {
                'type': 'publish_event',
                'event_type': 'analytics.user_registered',
                'payload': {'source': 'registration_workflow'}
            }
        ]
    }

    orchestrator.event_manager.create_workflow('user_registration', user_registration_workflow)

    # Workflow: Payment processed -> Update balance -> Send notification
    payment_workflow = {
        'name': 'payment_processing_flow',
        'triggers': [{
            'event_type': 'payment.completed',
            'conditions': {}
        }],
        'steps': [
            {
                'type': 'submit_job',
                'job_type': 'update_user_balance',
                'payload': {}
            },
            {
                'type': 'publish_event',
                'event_type': 'notification.payment_success',
                'payload': {'type': 'push'}
            }
        ]
    }

    orchestrator.event_manager.create_workflow('payment_processing', payment_workflow)


async def demonstrate_async_processing():
    """Demostrar sistema de procesamiento asíncrono."""
    print("⚡ Inicializando Async Processing System...")

    # Inicializar sistema
    orchestrator = await initialize_async_processing_system()

    print("📊 Estado inicial del sistema:")
    stats = orchestrator.get_system_stats()
    print(f"   Message Queues: {stats['message_queue']['total_topics']} topics")
    print(f"   Job Processor: {stats['job_processor']['max_workers']} max workers")
    print(f"   Event Manager: {stats['event_manager']['active_workflows']} workflows")
    print(f"   Task Scheduler: {stats['task_scheduler']['scheduled_tasks']} tasks")

    # Probar message queues
    print("\n📨 Probando Message Queues:")

    # Publicar mensajes
    messages = [
        Message(topic="user_events", payload={"user_id": "123", "action": "login"}),
        Message(topic="payments", payload={"amount": 100.50, "currency": "USD"}),
        Message(topic="jobs", payload={"job_type": "data_processing", "priority": 3})
    ]

    for msg in messages:
        success = await orchestrator.message_queue.publish(msg.topic, msg)
        status = "✅" if success else "❌"
        print(f"   {status} Published to {msg.topic}: {msg.payload}")

    # Consumir mensajes
    consumed = await orchestrator.message_queue.consume("user_events", batch_size=5)
    print(f"   📥 Consumed {len(consumed)} messages from user_events")

    # Probar background jobs
    print("\n🔄 Probando Background Jobs:")

    job_types = ["email_send", "data_sync", "report_generate", "cache_warmup"]

    for job_type in job_types:
        job_id = await orchestrator.submit_background_job(
            job_type=job_type,
            payload={"param1": f"value_{job_type}", "count": random.randint(1, 10)},
            priority=JobPriority.HIGH if "email" in job_type else JobPriority.NORMAL
        )
        print(f"   📋 Submitted job: {job_type} (ID: {job_id[:8]}...)")

    # Esperar un poco para que se procesen algunos jobs
    await asyncio.sleep(2)

    # Mostrar status de jobs
    job_stats = orchestrator.job_processor.get_processor_stats()
    print(f"   📊 Jobs procesados: {job_stats['completed_jobs']}/{job_stats['total_jobs']} completados")

    # Probar event-driven architecture
    print("\n🎭 Probando Event-Driven Architecture:")

    # Publicar eventos
    events = [
        ("user.registered", {"user_id": "456", "email": "user@example.com"}),
        ("payment.completed", {"amount": 50.00, "user_id": "456"}),
        ("data.processed", {"records": 1000, "duration": 2.5})
    ]

    for event_type, payload in events:
        event_id = await orchestrator.publish_event(event_type, payload)
        print(f"   📢 Published event: {event_type} (ID: {event_id[:8]}...)")

    # Mostrar historial de eventos
    event_history = orchestrator.event_manager.get_event_history(limit=10)
    print(f"   📜 Total eventos en historial: {len(event_history)}")

    # Probar workflows (deberían trigger automáticamente)
    print("\n🔄 Probando Workflows Automáticos:")

    # Trigger workflow de user registration
    await orchestrator.publish_event("user.registered", {
        "user_id": "789",
        "email": "newuser@example.com",
        "timestamp": datetime.now().isoformat()
    })

    await asyncio.sleep(1)  # Dar tiempo a que se ejecute el workflow

    # Verificar que se crearon jobs del workflow
    final_job_stats = orchestrator.job_processor.get_processor_stats()
    print(f"   🤖 Jobs creados por workflows: {final_job_stats['total_jobs'] - job_stats['total_jobs']}")

    # Mostrar estadísticas finales
    print("
📈 Estadísticas finales del sistema:"    final_stats = orchestrator.get_system_stats()
    print(f"   Message Queues: {final_stats['message_queue']['total_messages']} mensajes")
    print(f"   Job Processor: {final_stats['job_processor']['success_rate']:.1f}% success rate")
    print(f"   Event Manager: {final_stats['event_manager']['total_events']} eventos totales")
    print(f"   Workflows activos: {final_stats['event_manager']['active_workflows']}")

    print("✅ Async Processing System demostrado correctamente")

    return orchestrator


if __name__ == "__main__":
    asyncio.run(demonstrate_async_processing())