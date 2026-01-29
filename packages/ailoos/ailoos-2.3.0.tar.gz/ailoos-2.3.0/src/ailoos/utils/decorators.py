"""
Common decorators for Ailoos.
Includes retry logic, circuit breakers, and execution time logging.
"""

import asyncio
import functools
import time
import logging
from typing import Callable, Any, Type, Union, Tuple

logger = logging.getLogger(__name__)

def retry(max_attempts: int = 3, delay: float = 1.0, backoff: float = 2.0, 
          exceptions: Tuple[Type[Exception], ...] = (Exception,)):
    """
    Decorator to retry an async function upon failure.
    
    Args:
        max_attempts: Maximum number of attempts.
        delay: Initial delay between retries in seconds.
        backoff: Multiplier for delay after each failure.
        exceptions: Tuple of exceptions to catch and retry.
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            current_delay = delay
            last_exception = None
            
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt == max_attempts - 1:
                        logger.error(f"❌ Function {func.__name__} failed after {max_attempts} attempts: {e}")
                        raise last_exception
                    
                    logger.warning(f"⚠️ Attempt {attempt + 1}/{max_attempts} for {func.__name__} failed: {e}. Retrying in {current_delay}s...")
                    await asyncio.sleep(current_delay)
                    current_delay *= backoff
            
            raise last_exception
        return wrapper
    return decorator

def log_execution_time():
    """Decorator to log the execution time of a function."""
    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                execution_time = time.time() - start_time
                logger.debug(f"⏱️ {func.__name__} executed in {execution_time:.4f}s")
                return result
            except Exception as e:
                execution_time = time.time() - start_time
                logger.error(f"❌ {func.__name__} failed after {execution_time:.4f}s: {e}")
                raise e
        return wrapper
    return decorator

class CircuitBreakerOpenException(Exception):
    """Exception raised when the circuit breaker is open."""
    pass

def circuit_breaker(failure_threshold: int = 5, recovery_timeout: int = 60):
    """
    Simple circuit breaker decorator.
    
    Args:
        failure_threshold: Number of failures before opening the circuit.
        recovery_timeout: Time in seconds to wait before trying to close the circuit.
    """
    def decorator(func: Callable):
        # State stored in the wrapper function object
        wrapper_state = {
            "failures": 0,
            "last_failure_time": 0,
            "state": "CLOSED"  # CLOSED, OPEN, HALF-OPEN
        }
        
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            current_time = time.time()
            
            if wrapper_state["state"] == "OPEN":
                if current_time - wrapper_state["last_failure_time"] > recovery_timeout:
                    wrapper_state["state"] = "HALF-OPEN"
                    logger.info(f"🔌 Circuit breaker for {func.__name__} is HALF-OPEN (testing recovery)")
                else:
                    logger.warning(f"🔌 Circuit breaker for {func.__name__} is OPEN. Call rejected.")
                    raise CircuitBreakerOpenException(f"Circuit breaker open for {func.__name__}")
            
            try:
                result = await func(*args, **kwargs)
                
                if wrapper_state["state"] == "HALF-OPEN":
                    wrapper_state["state"] = "CLOSED"
                    wrapper_state["failures"] = 0
                    logger.info(f"🔌 Circuit breaker for {func.__name__} is now CLOSED (recovered)")
                elif wrapper_state["failures"] > 0:
                    wrapper_state["failures"] = 0
                    
                return result
                
            except Exception as e:
                wrapper_state["failures"] += 1
                wrapper_state["last_failure_time"] = current_time
                
                if wrapper_state["failures"] >= failure_threshold:
                    wrapper_state["state"] = "OPEN"
                    logger.error(f"🔌 Circuit breaker for {func.__name__} OPENED after {wrapper_state['failures']} failures")
                
                raise e
                
        return wrapper
    return decorator
