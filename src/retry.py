"""Retry mechanism with exponential backoff for API requests."""
import time
import random
from typing import Callable, TypeVar, Optional, List
from dataclasses import dataclass

T = TypeVar('T')


@dataclass
class RetryConfig:
    """Configuration for retry behavior."""
    max_attempts: int = 3
    initial_delay: float = 1.0
    max_delay: float = 60.0
    exponential_base: float = 2.0
    jitter: bool = True
    # HTTP status codes that should trigger retry
    retryable_status_codes: List[int] = None
    
    def __post_init__(self):
        if self.retryable_status_codes is None:
            # Retry on rate limits, gateway errors, service unavailable
            self.retryable_status_codes = [429, 502, 503, 504]


class RetryError(Exception):
    """Raised when all retry attempts are exhausted."""
    def __init__(self, last_error: Exception, attempts: int):
        self.last_error = last_error
        self.attempts = attempts
        super().__init__(f"Failed after {attempts} attempts: {last_error}")


def calculate_backoff_delay(attempt: int, config: RetryConfig) -> float:
    """Calculate delay for exponential backoff with optional jitter.
    
    Args:
        attempt: Current attempt number (0-indexed)
        config: Retry configuration
        
    Returns:
        Delay in seconds
    """
    delay = config.initial_delay * (config.exponential_base ** attempt)
    delay = min(delay, config.max_delay)
    
    if config.jitter:
        # Add random jitter (0-25% of delay)
        jitter_amount = delay * 0.25 * random.random()
        delay += jitter_amount
    
    return delay


def should_retry(error: Exception, config: RetryConfig) -> bool:
    """Determine if an error is retryable.
    
    Args:
        error: Exception that occurred
        config: Retry configuration
        
    Returns:
        True if error should trigger retry
    """
    # Import here to avoid circular dependency
    from .models import HttpStatusError
    
    if isinstance(error, HttpStatusError):
        return error.status_code in config.retryable_status_codes
    
    # Retry on timeout and connection errors
    import requests
    if isinstance(error, (requests.exceptions.Timeout, 
                         requests.exceptions.ConnectionError)):
        return True
    
    return False


def retry_with_backoff(
    func: Callable[[], T],
    config: Optional[RetryConfig] = None,
    on_retry: Optional[Callable[[int, Exception, float], None]] = None
) -> T:
    """Execute function with exponential backoff retry.
    
    Args:
        func: Function to execute
        config: Retry configuration (uses defaults if None)
        on_retry: Optional callback called before each retry
                 Receives: (attempt_number, error, delay_seconds)
        
    Returns:
        Result from successful function execution
        
    Raises:
        RetryError: If all retry attempts fail
    """
    if config is None:
        config = RetryConfig()
    
    last_error = None
    
    for attempt in range(config.max_attempts):
        try:
            return func()
        except Exception as e:
            last_error = e
            
            # Don't retry if not retryable or last attempt
            if not should_retry(e, config) or attempt == config.max_attempts - 1:
                break
            
            # Calculate backoff delay
            delay = calculate_backoff_delay(attempt, config)
            
            # Call retry callback if provided
            if on_retry:
                on_retry(attempt + 1, e, delay)
            
            # Wait before retry
            time.sleep(delay)
    
    # All attempts failed
    raise RetryError(last_error, config.max_attempts)
