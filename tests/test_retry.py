"""Tests for retry logic."""
from src.retry import RetryConfig, calculate_backoff_delay, should_retry
from src.models import HttpStatusError


def test_calculate_backoff_delay():
    """Test exponential backoff calculation."""
    config = RetryConfig(initial_delay=1.0, exponential_base=2.0, max_delay=60.0, jitter=False)
    
    # First retry
    delay = calculate_backoff_delay(0, config)
    assert delay == 1.0
    
    # Second retry
    delay = calculate_backoff_delay(1, config)
    assert delay == 2.0
    
    # Third retry
    delay = calculate_backoff_delay(2, config)
    assert delay == 4.0
    
    # Should cap at max_delay
    delay = calculate_backoff_delay(10, config)
    assert delay == 60.0


def test_calculate_backoff_with_jitter():
    """Test backoff with jitter adds randomness."""
    config = RetryConfig(initial_delay=1.0, exponential_base=2.0, jitter=True)
    
    delays = [calculate_backoff_delay(1, config) for _ in range(10)]
    
    # All delays should be different due to jitter
    assert len(set(delays)) > 1
    
    # All delays should be in reasonable range (2.0 to 2.5)
    assert all(2.0 <= d <= 2.5 for d in delays)


def test_should_retry_on_retryable_errors():
    """Test that retryable status codes are detected."""
    config = RetryConfig(retryable_status_codes=[429, 502, 503, 504])
    
    # Should retry on rate limit
    error = HttpStatusError(429, "Rate limit", None)
    assert should_retry(error, config) is True
    
    # Should retry on bad gateway
    error = HttpStatusError(502, "Bad gateway", None)
    assert should_retry(error, config) is True
    
    # Should retry on service unavailable
    error = HttpStatusError(503, "Service unavailable", None)
    assert should_retry(error, config) is True


def test_should_not_retry_on_client_errors():
    """Test that client errors are not retried."""
    config = RetryConfig(retryable_status_codes=[429, 502, 503, 504])
    
    # Should not retry on bad request
    error = HttpStatusError(400, "Bad request", None)
    assert should_retry(error, config) is False
    
    # Should not retry on unauthorized
    error = HttpStatusError(401, "Unauthorized", None)
    assert should_retry(error, config) is False
    
    # Should not retry on not found
    error = HttpStatusError(404, "Not found", None)
    assert should_retry(error, config) is False
