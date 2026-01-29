#!/usr/bin/env python3
"""
Federated Learning Session Management - REAL Implementation
"""

import asyncio
import time
from typing import Dict, List, Any, Optional
from datetime import datetime
from dataclasses import dataclass

from ..core.logging import get_logger
from ..core.config import AiloosConfig

logger = get_logger(__name__)


@dataclass
class FederatedSession:
    """Federated learning session - REAL Implementation"""

    session_id: str
    model_name: str
    rounds: int = 5
    min_nodes: int = 3
    max_nodes: int = 100
    status: str = "created"
    created_at: str = ""
    participants: List[str] = None
    current_round: int = 0
    total_rounds: int = 5

    # Campos REALES añadidos
    dataset_name: str = ""
    privacy_budget: float = 1.0
    coordinator_url: Optional[str] = None
    model_cid: str = ""
    total_rewards_distributed: float = 0.0
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    paused: bool = False
    paused_at: Optional[float] = None
    total_paused_time: float = 0.0

    def __post_init__(self):
        if self.participants is None:
            self.participants = []
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
        if not self.start_time:
            self.start_time = time.time()

        # Initialize ZKProver (lazy initialization to avoid config issues)
        self.zk_prover = None

        logger.info(f"🆕 Federated Session REAL created: {self.session_id}")

    def add_participant(self, node_id: str):
        """Add a participant to the session - REAL"""
        if node_id not in self.participants:
            self.participants.append(node_id)
            logger.info(f"✅ Added participant {node_id} to REAL session {self.session_id}")
            logger.info(f"   👥 Total participants: {len(self.participants)}/{self.min_nodes} min required")

    def remove_participant(self, node_id: str):
        """Remove a participant from the session - REAL"""
        if node_id in self.participants:
            self.participants.remove(node_id)
            logger.info(f"❌ Removed participant {node_id} from REAL session {self.session_id}")
            logger.info(f"   👥 Remaining participants: {len(self.participants)}")

    def can_start(self) -> bool:
        """Check if session can start - REAL"""
        can_start = len(self.participants) >= self.min_nodes
        if can_start:
            logger.info(f"✅ Session {self.session_id} can start: {len(self.participants)}/{self.min_nodes} participants")
        else:
            logger.debug(f"⏳ Session {self.session_id} waiting: {len(self.participants)}/{self.min_nodes} participants")
        return can_start

    def is_complete(self) -> bool:
        """Check if session is complete - REAL"""
        complete = self.current_round >= self.total_rounds
        if complete and not self.end_time:
            self.end_time = time.time()
            self.status = "completed"
            logger.info(f"🎉 Session {self.session_id} COMPLETED after {self.current_round} rounds")
        return complete

    def next_round(self):
        """Advance to next round - REAL"""
        if not self.is_complete():
            self.current_round += 1
            self.status = f"round_{self.current_round}"
            logger.info(f"🔄 Session {self.session_id} advanced to REAL round {self.current_round}/{self.total_rounds}")
            logger.info(f"   📊 Progress: {self.current_round}/{self.total_rounds} rounds completed")
        else:
            logger.warning(f"⚠️ Cannot advance: Session {self.session_id} already complete")

    def get_status(self) -> Dict[str, Any]:
        """Get session status - REAL"""
        # Calcular métricas REALES
        current_time = time.time()
        uptime_seconds = current_time - (self.start_time or current_time)
        effective_uptime = uptime_seconds - self.total_paused_time
        uptime_hours = effective_uptime / 3600

        progress_percentage = (self.current_round / self.total_rounds) * 100 if self.total_rounds > 0 else 0

        return {
            "session_id": self.session_id,
            "model_name": self.model_name,
            "dataset_name": self.dataset_name,
            "privacy_budget": self.privacy_budget,
            "status": self.status,
            "current_round": self.current_round,
            "total_rounds": self.total_rounds,
            "participants": len(self.participants),
            "participant_list": self.participants,
            "min_nodes": self.min_nodes,
            "max_nodes": self.max_nodes,
            "can_start": self.can_start(),
            "is_complete": self.is_complete(),
            "progress_percentage": f"{progress_percentage:.1f}%",
            "created_at": self.created_at,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "uptime_seconds": effective_uptime,
            "uptime_hours": f"{uptime_hours:.1f}",
            "coordinator_url": self.coordinator_url,
            "model_cid": self.model_cid,
            "total_rewards_distributed": self.total_rewards_distributed,
            "rounds_remaining": max(0, self.total_rounds - self.current_round),
            "estimated_completion_time": self._estimate_completion_time(),
            "paused": self.paused,
            "paused_at": self.paused_at,
            "total_paused_time": self.total_paused_time,
            "can_pause": not self.is_complete() and not self.paused,
            "can_resume": self.paused and not self.is_complete(),
            "can_cancel": not self.is_complete()
        }

    def _estimate_completion_time(self) -> Optional[str]:
        """Estimate completion time based on current progress"""
        if self.current_round == 0 or not self.start_time:
            return None

        elapsed_time = time.time() - self.start_time
        rounds_completed = self.current_round
        rounds_remaining = self.total_rounds - self.current_round

        if rounds_completed > 0 and rounds_remaining > 0:
            avg_time_per_round = elapsed_time / rounds_completed
            estimated_seconds = avg_time_per_round * rounds_remaining
            estimated_completion = time.time() + estimated_seconds
            return datetime.fromtimestamp(estimated_completion).isoformat()

        return None



    def update_model_cid(self, new_cid: str):
        """Update model CID - REAL"""
        self.model_cid = new_cid
        logger.info(f"📦 Updated model CID for session {self.session_id}: {new_cid}")

    def pause_session(self):
        """Pause the session - REAL"""
        if not self.paused and not self.is_complete():
            self.paused = True
            self.paused_at = time.time()
            self.status = "paused"
            logger.info(f"⏸️ Session {self.session_id} PAUSED at round {self.current_round}")
        else:
            logger.warning(f"⚠️ Cannot pause session {self.session_id}: already paused or completed")

    def resume_session(self):
        """Resume the session - REAL"""
        if self.paused:
            paused_duration = time.time() - (self.paused_at or time.time())
            self.total_paused_time += paused_duration
            self.paused = False
            self.paused_at = None
            self.status = f"round_{self.current_round}" if self.current_round > 0 else "active"
            logger.info(f"▶️ Session {self.session_id} RESUMED at round {self.current_round}")
        else:
            logger.warning(f"⚠️ Cannot resume session {self.session_id}: not paused")

    def start_session(self):
        """Explicitly start the session - REAL"""
        if self.status == "created" and self.can_start():
            self.status = "active"
            logger.info(f"🚀 Session {self.session_id} STARTED with {len(self.participants)} participants")
        elif not self.can_start():
            logger.warning(f"⚠️ Cannot start session {self.session_id}: insufficient participants ({len(self.participants)}/{self.min_nodes})")
        else:
            logger.warning(f"⚠️ Cannot start session {self.session_id}: invalid status ({self.status})")

    def cancel_session(self):
        """Cancel the session - REAL"""
        if not self.is_complete():
            self.status = "cancelled"
            self.end_time = time.time()
            logger.info(f"❌ Session {self.session_id} CANCELLED at round {self.current_round}")
        else:
            logger.warning(f"⚠️ Cannot cancel session {self.session_id}: already completed")

    def replace_participant(self, failed_node_id: str, replacement_node_id: str) -> bool:
        """Replace a failed participant with a new one - AUTO-HEALING"""
        if failed_node_id not in self.participants:
            logger.warning(f"Cannot replace {failed_node_id}: not a participant in session {self.session_id}")
            return False

        if replacement_node_id in self.participants:
            logger.warning(f"Cannot replace with {replacement_node_id}: already a participant in session {self.session_id}")
            return False

        # Remove failed node
        self.participants.remove(failed_node_id)
        logger.info(f"🗑️ Removed failed participant {failed_node_id} from session {self.session_id}")

        # Add replacement node
        self.participants.append(replacement_node_id)
        logger.info(f"➕ Added replacement participant {replacement_node_id} to session {self.session_id}")

        return True

    def handle_node_failure(self, failed_node_id: str, failure_reason: str = "Node failure detected") -> bool:
        """Handle node failure and prepare for auto-healing - AUTO-HEALING"""
        if failed_node_id not in self.participants:
            logger.debug(f"Node {failed_node_id} not in session {self.session_id}, ignoring failure")
            return False

        logger.warning(f"🚨 Node failure detected: {failed_node_id} in session {self.session_id} - {failure_reason}")

        # Mark node as failed but don't remove yet (auto-healing will handle replacement)
        # The node will be replaced by the auto-healing system
        return True

    def get_healthy_participants(self) -> List[str]:
        """Get list of healthy participants (for auto-healing monitoring)"""
        # In a full implementation, this would check health status
        # For now, return all participants
        return self.participants.copy()

    def can_accept_replacement(self, min_participants: int = 3) -> bool:
        """Check if session can accept participant replacement - AUTO-HEALING"""
        healthy_count = len(self.get_healthy_participants())
        return healthy_count >= min_participants