import asyncio
import logging
import time
import calendar
from typing import Dict, List, Optional, Any, Callable, Set, Tuple
from dataclasses import dataclass
from enum import Enum
from datetime import datetime, timedelta
import heapq

logger = logging.getLogger(__name__)

class ScheduleType(Enum):
    INTERVAL = "interval"  # Repeat every X seconds/minutes/hours
    CRON = "cron"  # Cron-like scheduling
    EVENT_DRIVEN = "event_driven"  # Triggered by events
    ON_DEMAND = "on_demand"  # Manual trigger only

class ReplicationTrigger(Enum):
    TIME_BASED = "time_based"
    DATA_CHANGE = "data_change"
    NODE_JOIN = "node_join"
    NODE_LEAVE = "node_leave"
    LOAD_THRESHOLD = "load_threshold"
    CONSISTENCY_CHECK = "consistency_check"

@dataclass
class ScheduleConfig:
    schedule_type: ScheduleType
    interval_seconds: Optional[int] = None
    cron_expression: Optional[str] = None
    trigger_events: List[ReplicationTrigger] = None
    enabled: bool = True
    priority: int = 1
    max_concurrent: int = 5

@dataclass
class ScheduledTask:
    task_id: str
    data_ids: List[str]
    schedule_config: ScheduleConfig
    next_run: float
    last_run: Optional[float] = None
    run_count: int = 0
    is_running: bool = False
    metadata: Dict[str, Any] = None

class ReplicationScheduler:
    """Automatic scheduling of replication tasks"""

    def __init__(self, replication_manager, data_partitioner=None):
        self.replication_manager = replication_manager
        self.data_partitioner = data_partitioner

        self.scheduled_tasks: Dict[str, ScheduledTask] = {}
        self.task_queue: List[Tuple[float, str]] = []  # (next_run_time, task_id)
        self.running_tasks: Set[str] = set()

        self.event_listeners: Dict[ReplicationTrigger, List[Callable]] = {}
        self._scheduler_task: Optional[asyncio.Task] = None
        self._event_monitor_task: Optional[asyncio.Task] = None

        self._lock = asyncio.Lock()
        self._task_counter = 0

    async def start_scheduler(self) -> None:
        """Start the replication scheduler"""
        if self._scheduler_task is None:
            self._scheduler_task = asyncio.create_task(self._scheduler_loop())
            logger.info("Started replication scheduler")

        if self._event_monitor_task is None:
            self._event_monitor_task = asyncio.create_task(self._event_monitor_loop())
            logger.info("Started event monitor")

    async def stop_scheduler(self) -> None:
        """Stop the replication scheduler"""
        if self._scheduler_task:
            self._scheduler_task.cancel()
            try:
                await self._scheduler_task
            except asyncio.CancelledError:
                pass
            self._scheduler_task = None

        if self._event_monitor_task:
            self._event_monitor_task.cancel()
            try:
                await self._event_monitor_task
            except asyncio.CancelledError:
                pass
            self._event_monitor_task = None

        logger.info("Stopped replication scheduler")

    def schedule_replication(self, task_id: str, data_ids: List[str],
                           schedule_config: ScheduleConfig,
                           metadata: Dict[str, Any] = None) -> bool:
        """Schedule a replication task"""
        if task_id in self.scheduled_tasks:
            logger.warning(f"Task {task_id} already scheduled")
            return False

        next_run = self._calculate_next_run(schedule_config)

        task = ScheduledTask(
            task_id=task_id,
            data_ids=data_ids,
            schedule_config=schedule_config,
            next_run=next_run,
            metadata=metadata or {}
        )

        self.scheduled_tasks[task_id] = task
        heapq.heappush(self.task_queue, (next_run, task_id))

        # Register event listeners if needed
        if schedule_config.trigger_events:
            for trigger in schedule_config.trigger_events:
                if trigger not in self.event_listeners:
                    self.event_listeners[trigger] = []
                self.event_listeners[trigger].append(lambda: self._trigger_task(task_id))

        logger.info(f"Scheduled replication task {task_id} with next run at {datetime.fromtimestamp(next_run)}")
        return True

    def _calculate_next_run(self, config: ScheduleConfig) -> float:
        """Calculate the next run time for a schedule"""
        now = time.time()

        if config.schedule_type == ScheduleType.INTERVAL:
            if config.interval_seconds:
                return now + config.interval_seconds
            else:
                return now + 3600  # Default 1 hour

        elif config.schedule_type == ScheduleType.CRON:
            # Simple cron parsing (basic implementation)
            return self._parse_cron_next_run(config.cron_expression or "0 * * * *", now)

        elif config.schedule_type == ScheduleType.EVENT_DRIVEN:
            return now + 86400  # Far future, triggered by events

        else:  # ON_DEMAND
            return now + 86400  # Far future, manual trigger only

    def _parse_cron_next_run(self, cron_expr: str, current_time: float) -> float:
        """Parse cron expression and calculate next run time (simplified)"""
        # Very basic cron parsing - supports "minute hour day month day_of_week"
        # Example: "0 * * * *" = every hour at minute 0
        try:
            parts = cron_expr.split()
            if len(parts) != 5:
                raise ValueError("Invalid cron expression")

            minute, hour, day, month, dow = parts

            dt = datetime.fromtimestamp(current_time)

            # Handle minutes
            if minute == "*":
                next_dt = dt.replace(second=0, microsecond=0)
                if dt.minute == 59:
                    next_dt = next_dt.replace(hour=dt.hour + 1, minute=0)
                else:
                    next_dt = next_dt.replace(minute=dt.minute + 1)
            else:
                next_minute = int(minute)
                next_dt = dt.replace(minute=next_minute, second=0, microsecond=0)
                if dt.minute >= next_minute:
                    next_dt = next_dt.replace(hour=dt.hour + 1)

            # Handle hours (simplified)
            if hour != "*":
                next_hour = int(hour)
                next_dt = next_dt.replace(hour=next_hour)
                if dt.hour > next_hour or (dt.hour == next_hour and dt.minute >= int(minute or "0")):
                    next_dt = next_dt.replace(day=dt.day + 1)

            return next_dt.timestamp()

        except (ValueError, IndexError):
            logger.error(f"Failed to parse cron expression: {cron_expr}")
            return current_time + 3600  # Fallback to 1 hour

    async def _scheduler_loop(self) -> None:
        """Main scheduler loop"""
        while True:
            try:
                now = time.time()

                # Process due tasks
                while self.task_queue and self.task_queue[0][0] <= now:
                    _, task_id = heapq.heappop(self.task_queue)

                    if task_id in self.scheduled_tasks:
                        task = self.scheduled_tasks[task_id]
                        if task.schedule_config.enabled and not task.is_running:
                            asyncio.create_task(self._execute_scheduled_task(task))

                # Sleep until next task or 30 seconds
                if self.task_queue:
                    next_run = self.task_queue[0][0]
                    sleep_time = min(30, max(1, next_run - now))
                else:
                    sleep_time = 30

                await asyncio.sleep(sleep_time)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in scheduler loop: {e}")
                await asyncio.sleep(30)

    async def _execute_scheduled_task(self, task: ScheduledTask) -> None:
        """Execute a scheduled replication task"""
        if task.is_running:
            return

        # Check concurrency limit
        if len(self.running_tasks) >= task.schedule_config.max_concurrent:
            logger.warning(f"Max concurrent tasks reached, skipping {task.task_id}")
            # Reschedule for later
            task.next_run = time.time() + 60
            heapq.heappush(self.task_queue, (task.next_run, task.task_id))
            return

        task.is_running = True
        task.last_run = time.time()
        task.run_count += 1
        self.running_tasks.add(task.task_id)

        try:
            logger.info(f"Executing scheduled replication task {task.task_id}")

            # Execute replication for each data ID
            for data_id in task.data_ids:
                try:
                    # Get data from a source node (simplified - assume we can get it)
                    source_data = await self._get_data_for_replication(data_id)
                    if source_data:
                        if self.data_partitioner:
                            # Use partitioner for replication
                            await self.data_partitioner.replicate_to_partition(data_id, source_data)
                        else:
                            # Direct replication to all nodes
                            await self.replication_manager.replicate_data(data_id, source_data)
                    else:
                        logger.warning(f"No data found for replication of {data_id}")

                except Exception as e:
                    logger.error(f"Failed to replicate {data_id}: {e}")

        finally:
            task.is_running = False
            self.running_tasks.discard(task.task_id)

            # Reschedule if interval-based
            if task.schedule_config.schedule_type == ScheduleType.INTERVAL:
                task.next_run = time.time() + (task.schedule_config.interval_seconds or 3600)
                heapq.heappush(self.task_queue, (task.next_run, task.task_id))

    async def _get_data_for_replication(self, data_id: str) -> Optional[bytes]:
        """Get data for replication from available nodes"""
        active_nodes = await self.replication_manager.get_active_nodes()

        for node_id in active_nodes:
            try:
                data = await self.replication_manager.get_data_from_node(data_id, node_id)
                if data:
                    return data
            except Exception as e:
                logger.error(f"Failed to get data from node {node_id}: {e}")
                continue

        return None

    async def _event_monitor_loop(self) -> None:
        """Monitor for events that trigger replication"""
        while True:
            try:
                # Check for various events
                await self._check_node_events()
                await self._check_load_events()
                await self._check_consistency_events()

                await asyncio.sleep(60)  # Check every minute

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in event monitor loop: {e}")
                await asyncio.sleep(60)

    async def _check_node_events(self) -> None:
        """Check for node join/leave events"""
        # This would integrate with node discovery service
        # For now, just a placeholder
        pass

    async def _check_load_events(self) -> None:
        """Check for load threshold events"""
        # Monitor replication load and trigger if needed
        active_tasks = len(self.replication_manager.active_tasks)
        if active_tasks > 10:  # Threshold
            await self._trigger_event(ReplicationTrigger.LOAD_THRESHOLD)

    async def _check_consistency_events(self) -> None:
        """Check for consistency issues that need replication"""
        # This would integrate with consistency manager
        # For now, just a placeholder
        pass

    async def _trigger_event(self, trigger: ReplicationTrigger) -> None:
        """Trigger event-driven tasks"""
        if trigger in self.event_listeners:
            for callback in self.event_listeners[trigger]:
                try:
                    await callback()
                except Exception as e:
                    logger.error(f"Error in event callback: {e}")

    async def _trigger_task(self, task_id: str) -> None:
        """Trigger a specific task immediately"""
        if task_id in self.scheduled_tasks:
            task = self.scheduled_tasks[task_id]
            if not task.is_running:
                logger.info(f"Triggering task {task_id} due to event")
                asyncio.create_task(self._execute_scheduled_task(task))

    def unschedule_task(self, task_id: str) -> bool:
        """Remove a scheduled task"""
        if task_id not in self.scheduled_tasks:
            return False

        del self.scheduled_tasks[task_id]

        # Remove from queue (rebuild queue)
        self.task_queue = [(t, tid) for t, tid in self.task_queue if tid != task_id]
        heapq.heapify(self.task_queue)

        logger.info(f"Unscheduled task {task_id}")
        return True

    def get_scheduled_tasks(self) -> Dict[str, Dict[str, Any]]:
        """Get information about all scheduled tasks"""
        result = {}
        for task_id, task in self.scheduled_tasks.items():
            result[task_id] = {
                "data_ids": task.data_ids,
                "schedule_type": task.schedule_config.schedule_type.value,
                "next_run": datetime.fromtimestamp(task.next_run).isoformat(),
                "last_run": datetime.fromtimestamp(task.last_run).isoformat() if task.last_run else None,
                "run_count": task.run_count,
                "is_running": task.is_running,
                "enabled": task.schedule_config.enabled
            }
        return result

    def get_scheduler_stats(self) -> Dict[str, Any]:
        """Get scheduler statistics"""
        now = time.time()
        upcoming_tasks = sum(1 for t, _ in self.task_queue if t > now)

        return {
            "total_scheduled_tasks": len(self.scheduled_tasks),
            "running_tasks": len(self.running_tasks),
            "upcoming_tasks": upcoming_tasks,
            "queue_size": len(self.task_queue)
        }

    async def trigger_manual_replication(self, data_ids: List[str],
                                       metadata: Dict[str, Any] = None) -> str:
        """Manually trigger replication for specific data"""
        task_id = f"manual_{self._task_counter}"
        self._task_counter += 1

        # Create temporary task
        config = ScheduleConfig(
            schedule_type=ScheduleType.ON_DEMAND,
            enabled=True
        )

        task = ScheduledTask(
            task_id=task_id,
            data_ids=data_ids,
            schedule_config=config,
            next_run=time.time(),
            metadata=metadata or {}
        )

        # Execute immediately
        asyncio.create_task(self._execute_scheduled_task(task))

        logger.info(f"Triggered manual replication for {len(data_ids)} data items")
        return task_id

    def enable_task(self, task_id: str) -> bool:
        """Enable a scheduled task"""
        if task_id in self.scheduled_tasks:
            self.scheduled_tasks[task_id].schedule_config.enabled = True
            logger.info(f"Enabled scheduled task {task_id}")
            return True
        return False

    def disable_task(self, task_id: str) -> bool:
        """Disable a scheduled task"""
        if task_id in self.scheduled_tasks:
            self.scheduled_tasks[task_id].schedule_config.enabled = False
            logger.info(f"Disabled scheduled task {task_id}")
            return True
        return False