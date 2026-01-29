"""
Base Agent Class

This module defines the base agent class for AI agents in RAG systems.
Agents can plan, reason, and execute tasks autonomously.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Union
import logging

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """
    Abstract base class for all AI agents in RAG systems.

    Agents are autonomous entities that can perceive their environment,
    reason about situations, and take actions to achieve goals.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the agent.

        Args:
            config (Dict[str, Any]): Configuration dictionary containing:
                - model_config: Language model configuration
                - memory_config: Memory and context management
                - tools_config: Available tools and capabilities
                - reasoning_config: Reasoning strategy settings
        """
        self.config = config
        self.model_config = config.get('model_config', {})
        self.memory_config = config.get('memory_config', {})
        self.tools_config = config.get('tools_config', {})
        self.reasoning_config = config.get('reasoning_config', {})

        # Agent state
        self.memory = []
        self.goals = []
        self.current_task = None

        # Initialize language model
        self.llm = None

        logger.info(f"Initialized {self.__class__.__name__} agent")

    @abstractmethod
    def perceive(self, environment: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perceive and analyze the current environment.

        Args:
            environment (Dict[str, Any]): Current environment state

        Returns:
            Dict[str, Any]: Perception results
        """
        pass

    @abstractmethod
    def reason(self, perception: Dict[str, Any]) -> Dict[str, Any]:
        """
        Reason about the situation and determine next actions.

        Args:
            perception (Dict[str, Any]): Results from perception

        Returns:
            Dict[str, Any]: Reasoning results including planned actions
        """
        pass

    @abstractmethod
    def act(self, reasoning: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute actions based on reasoning.

        Args:
            reasoning (Dict[str, Any]): Results from reasoning

        Returns:
            Dict[str, Any]: Action results
        """
        pass

    def run(self, environment: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the complete agent loop: perceive -> reason -> act.

        Args:
            environment (Dict[str, Any]): Initial environment state

        Returns:
            Dict[str, Any]: Complete execution results
        """
        try:
            # Perception phase
            perception = self.perceive(environment)

            # Reasoning phase
            reasoning = self.reason(perception)

            # Action phase
            action_results = self.act(reasoning)

            # Update memory
            self.update_memory({
                'perception': perception,
                'reasoning': reasoning,
                'actions': action_results,
                'timestamp': None  # Could add timestamp
            })

            result = {
                'perception': perception,
                'reasoning': reasoning,
                'actions': action_results,
                'final_state': self.get_current_state()
            }

            logger.info(f"Agent {self.__class__.__name__} completed execution")
            return result

        except Exception as e:
            logger.error(f"Error in agent execution: {str(e)}")
            raise

    def update_memory(self, experience: Dict[str, Any]) -> None:
        """
        Update agent memory with new experiences.

        Args:
            experience (Dict[str, Any]): Experience to store
        """
        self.memory.append(experience)

        # Limit memory size
        max_memory = self.memory_config.get('max_size', 100)
        if len(self.memory) > max_memory:
            self.memory = self.memory[-max_memory:]

    def recall_relevant_memories(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Recall memories relevant to a query.

        Args:
            query (str): Query to match memories against
            limit (int): Maximum number of memories to return

        Returns:
            List[Dict[str, Any]]: Relevant memories
        """
        # Simple relevance check (could be improved with embeddings)
        relevant = []
        query_lower = query.lower()

        for memory in reversed(self.memory):  # Most recent first
            if any(query_lower in str(v).lower() for v in memory.values()):
                relevant.append(memory)
                if len(relevant) >= limit:
                    break

        return relevant

    def set_goal(self, goal: Dict[str, Any]) -> None:
        """
        Set a new goal for the agent.

        Args:
            goal (Dict[str, Any]): Goal specification
        """
        self.goals.append(goal)

    def get_current_state(self) -> Dict[str, Any]:
        """Get the current state of the agent."""
        return {
            'agent_type': self.__class__.__name__,
            'current_task': self.current_task,
            'active_goals': len(self.goals),
            'memory_size': len(self.memory),
            'config': self.config
        }

    def communicate(self, message: str, recipient: Optional[str] = None) -> Dict[str, Any]:
        """
        Send a message to another agent or system.

        Args:
            message (str): Message content
            recipient (Optional[str]): Recipient identifier

        Returns:
            Dict[str, Any]: Communication result
        """
        # Placeholder for inter-agent communication
        comm_result = {
            'message': message,
            'recipient': recipient,
            'sender': self.__class__.__name__,
            'timestamp': None
        }

        logger.info(f"Agent communication: {message}")
        return comm_result

    def learn_from_feedback(self, feedback: Dict[str, Any]) -> None:
        """
        Learn from external feedback to improve performance.

        Args:
            feedback (Dict[str, Any]): Feedback information
        """
        # Store feedback in memory for future learning
        self.update_memory({'feedback': feedback, 'type': 'learning'})

        # Could implement reinforcement learning or parameter updates
        logger.info(f"Agent learned from feedback: {feedback}")

    def __repr__(self) -> str:
        """String representation of the agent."""
        return f"{self.__class__.__name__}(goals={len(self.goals)}, memory={len(self.memory)})"