import time
from typing import List, Optional
import requests
from requests import RequestException
from .models import ModelResult, HttpStatusError
from .client import request_json, build_chat_payload
from .validation import validate_response_text
from .response_parser import ResponseParser
from .retry import retry_with_backoff, RetryConfig, RetryError
from .output import (
    print_separator,
    print_start,
    print_request,
    print_end,
    print_verbose_response,
)


def run_model_test(
    completions_url: str,
    api_key: str,
    model: str,
    max_tokens: int,
    session: requests.Session,
    timeout: int,
    verbose: bool,
    run_label: str,
    max_model_len: int = 0,
    enable_retry: bool = True,
    retry_config: Optional[RetryConfig] = None,
) -> ModelResult:
    url = completions_url
    headers = {"Authorization": f"Bearer {api_key}"}
    payload = build_chat_payload(model, max_tokens)
    start = time.time()
    model_display = model.ljust(max_model_len)

    if verbose:
        print_separator()
        print_start(run_label, model_display)
        print_request(run_label, model_display, url)

    try:
        # Wrap request in retry logic if enabled
        if enable_retry:
            if retry_config is None:
                retry_config = RetryConfig(max_attempts=3, initial_delay=1.0)
            
            def make_request():
                return request_json(session, url, "POST", headers, payload, timeout)
            
            def on_retry_callback(attempt: int, error: Exception, delay: float):
                if verbose:
                    print(f"\n  Retry attempt {attempt} after {delay:.1f}s (error: {error})")
            
            try:
                response, status_code, response_text = retry_with_backoff(
                    make_request,
                    config=retry_config,
                    on_retry=on_retry_callback if verbose else None
                )
            except RetryError as e:
                # All retries exhausted, use last error
                raise e.last_error
        else:
            response, status_code, response_text = request_json(session, url, "POST", headers, payload, timeout)
        
        latency_ms = int((time.time() - start) * 1000)
        
        # Use ResponseParser to handle all formats
        # ResponseParser expects the raw Response object from requests
        from requests import Response as RequestsResponse
        
        # Create a mock Response object if we don't have one
        if not isinstance(response, RequestsResponse):
            # response is already parsed JSON, use it directly
            parsed_result = response
        else:
            parser = ResponseParser(response)
            parsed_result = parser.parse()
        
        if not parsed_result:
            error_msg = parser.get_error_message()
            print_end(run_label, model_display, False, latency_ms, reason="parse_failed")

            if verbose:
                print_verbose_response(status_code, response)
                if error_msg:
                    print(f"  Parse error: {error_msg}")

            return ModelResult(
                model=model,
                ok=False,
                error=error_msg or "parse_failed",
                latency_ms=latency_ms,
                raw_text=None,
                status_code=status_code,
                response_json=response or None,
                response_text=response_text or None,
            )
        
        # Extract text from parsed result
        text = parsed_result.get('choices', [{}])[0].get('message', {}).get('content', '')
        
        if not text:
            print_end(run_label, model_display, False, latency_ms, reason="no_text_in_response")

            if verbose:
                print_verbose_response(status_code, response)

            return ModelResult(
                model=model,
                ok=False,
                error="no_text_in_response",
                latency_ms=latency_ms,
                raw_text=None,
                status_code=status_code,
                response_json=response or None,
                response_text=response_text or None,
            )

        ok, error = validate_response_text(text)
        print_end(run_label, model_display, ok, latency_ms)

        if verbose:
            print_verbose_response(status_code, response)

        return ModelResult(
            model=model,
            ok=ok,
            error=error,
            latency_ms=latency_ms,
            raw_text=text,
            status_code=status_code,
            response_json=response or None,
            response_text=response_text or None,
        )

    except HttpStatusError as exc:
        latency_ms = int((time.time() - start) * 1000)
        print_end(run_label, model_display, False, latency_ms, reason=f"http_{exc.status_code}")

        return ModelResult(
            model=model,
            ok=False,
            error=f"http_error: {exc}",
            latency_ms=latency_ms,
            raw_text=None,
            status_code=exc.status_code,
            response_json=exc.data or None,
            response_text=exc.body or None,
        )

    except RequestException as exc:
        latency_ms = int((time.time() - start) * 1000)
        error_type = type(exc).__name__
        print_end(run_label, model_display, False, latency_ms, reason=error_type)

        return ModelResult(
            model=model,
            ok=False,
            error=f"request_error: {exc}",
            latency_ms=latency_ms,
            raw_text=None,
            status_code=None,
            response_json=None,
            response_text=None,
        )

    except Exception as exc:
        latency_ms = int((time.time() - start) * 1000)
        print_end(run_label, model_display, False, latency_ms, reason="unexpected_error")

        return ModelResult(
            model=model,
            ok=False,
            error=f"unexpected_error: {exc}",
            latency_ms=latency_ms,
            raw_text=None,
            status_code=None,
            response_json=None,
            response_text=None,
        )


def run_tests(
    models: List[str],
    completions_url: str,
    api_key: str,
    max_tokens: int,
    session: requests.Session,
    timeout: int,
    verbose: bool,
    delay: float,
    enable_retry: bool = True,
    retry_config: Optional[RetryConfig] = None,
) -> List[ModelResult]:
    max_model_len = max(len(m) for m in models)
    results = []

    for i, model in enumerate(models, 1):
        run_label = f"{i:02d}/{len(models)}"
        results.append(run_model_test(
            completions_url, api_key, model, max_tokens,
            session, timeout, verbose, run_label, max_model_len,
            enable_retry=enable_retry,
            retry_config=retry_config
        ))

        if delay:
            time.sleep(delay)

    return results
