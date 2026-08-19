"""
Universal response parser for multiple format types from any Provider or Router.

Handles:
- Standard OpenAI JSON
- Server-Sent Events (SSE) streaming
- Chunked streaming (Transfer-Encoding: chunked)
- NDJSON (newline-delimited JSON)
- Error responses (4xx, 5xx)
"""

import json
from typing import Dict, Any, Optional
from requests import Response


class ResponseParser:
    """Universal parser for any Provider or Router responses in multiple formats"""

    def __init__(self, response: Response):
        """Initialize parser with response object"""
        self.response = response
        self._cached_text = ""  # Cache for response text
        self.content_type = response.headers.get('Content-Type', '').lower()
        self.transfer_encoding = response.headers.get('Transfer-Encoding', '').lower()

    def parse(self) -> Dict[str, Any]:
        """Main entry point - detect format and parse accordingly"""

        # Error responses (4xx, 5xx)
        if self.response.status_code >= 400:
            return self._parse_openai_error()

        # Detect format based on headers and content
        if 'text/event-stream' in self.content_type:
            return self._parse_sse()

        elif 'chunked' in self.transfer_encoding:
            return self._parse_streaming()

        elif 'application/x-ndjson' in self.content_type or 'application/jsonlines' in self.content_type:
            return self._parse_ndjson()

        else:
            # Try standard JSON first
            try:
                return self._parse_standard_json()
            except:
                # Fallback to streaming if JSON fails
                return self._parse_streaming()

    def _parse_streaming(self) -> Dict[str, Any]:
        """Parse chunked streaming responses"""
        accumulated_content = ""
        chunks = []

        try:
            for chunk in self.response.iter_content(decode_unicode=True, chunk_size=None):
                if not chunk:
                    continue

                chunks.append(chunk)

                # Try to extract content from chunk
                try:
                    chunk_data = json.loads(chunk)
                    if 'choices' in chunk_data:
                        for choice in chunk_data['choices']:
                            if 'delta' in choice and 'content' in choice['delta']:
                                accumulated_content += choice['delta']['content']
                            elif 'message' in choice and 'content' in choice['message']:
                                accumulated_content += choice['message']['content']
                except:
                    pass

        except Exception:
            pass

        # Build standard response
        return self._build_standard_response(
            "streaming-" + str(hash(''.join(chunks))),
            "unknown",
            None,
            accumulated_content,
            "stop",
            None
        )

    def _parse_sse(self) -> Dict[str, Any]:
        """Parse Server-Sent Events format"""
        accumulated_content = ""
        chunks = []
        response_id = None
        model_name = None
        created = None
        finish_reason = None
        usage = None

        # Cache the raw text for later use
        raw_lines = []

        for line in self.response.iter_lines(decode_unicode=True):
            if line:
                raw_lines.append(line)

            if not line or not line.startswith('data: '):
                continue

            data_str = line[6:].strip()  # Remove 'data: ' prefix

            if data_str == '[DONE]':
                finish_reason = 'stop'
                break

            try:
                chunk = json.loads(data_str)
                chunks.append(chunk)

                # Extract metadata
                if not response_id and 'id' in chunk:
                    response_id = chunk['id']
                if not model_name and 'model' in chunk:
                    model_name = chunk['model']
                if not created and 'created' in chunk:
                    created = chunk['created']

                # Extract content from delta
                if 'choices' in chunk:
                    for choice in chunk['choices']:
                        if 'delta' in choice:
                            delta = choice['delta']
                            if 'content' in delta:
                                accumulated_content += delta['content']
                            if 'finish_reason' in choice and choice['finish_reason']:
                                finish_reason = choice['finish_reason']

                # Extract usage
                if 'usage' in chunk:
                    usage = chunk['usage']

            except json.JSONDecodeError:
                continue

        # Cache response text for debugging
        if not hasattr(self, '_cached_text'):
            try:
                # Response already consumed, use a placeholder
                self._cached_text = "[SSE stream - already consumed]"
            except:
                self._cached_text = "[SSE stream - text not cacheable]"

        return self._build_standard_response(
            response_id, model_name, created, accumulated_content, finish_reason, usage
        )

    def _parse_ndjson(self) -> Dict[str, Any]:
        """Parse newline-delimited JSON format"""
        accumulated_content = ""
        chunks = []
        response_id = None
        model_name = None
        created = None
        finish_reason = None
        usage = None

        for line in self.response.iter_lines(decode_unicode=True):
            if not line.strip():
                continue

            try:
                chunk = json.loads(line)
                chunks.append(chunk)

                # Extract metadata
                if not response_id and 'id' in chunk:
                    response_id = chunk['id']
                if not model_name and 'model' in chunk:
                    model_name = chunk['model']
                if not created and 'created' in chunk:
                    created = chunk['created']

                # Extract content
                if 'choices' in chunk:
                    for choice in chunk['choices']:
                        if 'delta' in choice and 'content' in choice['delta']:
                            accumulated_content += choice['delta']['content']
                        elif 'message' in choice and 'content' in choice['message']:
                            accumulated_content += choice['message']['content']

                        if 'finish_reason' in choice and choice['finish_reason']:
                            finish_reason = choice['finish_reason']

                # Extract usage
                if 'usage' in chunk:
                    usage = chunk['usage']

            except json.JSONDecodeError:
                continue

        return self._build_standard_response(
            response_id, model_name, created, accumulated_content, finish_reason, usage
        )

    def _parse_standard_json(self) -> Dict[str, Any]:
        """Parse standard OpenAI JSON response"""
        data = self.response.json()

        # Already in standard format
        if 'choices' in data and data['choices']:
            choice = data['choices'][0]

            # Extract content from message or delta
            content = ""
            if 'message' in choice and 'content' in choice['message']:
                content = choice['message']['content']
            elif 'delta' in choice and 'content' in choice['delta']:
                content = choice['delta']['content']
            elif 'text' in choice:
                content = choice['text']

            # Return normalized format
            return {
                'id': data.get('id', 'unknown'),
                'object': data.get('object', 'chat.completion'),
                'created': data.get('created'),
                'model': data.get('model', 'unknown'),
                'choices': [{
                    'index': 0,
                    'message': {
                        'role': 'assistant',
                        'content': content
                    },
                    'finish_reason': choice.get('finish_reason', 'stop')
                }],
                'usage': data.get('usage')
            }

        # Fallback - return as-is
        return data

    def _parse_openai_error(self) -> Dict[str, Any]:
        """Parse error responses"""
        try:
            data = self.response.json()
            if 'error' in data:
                return data
        except:
            pass

        # Build error response
        try:
            text = self.response.text[:500]
        except:
            text = ""

        return {
            'error': {
                'message': text or f'HTTP {self.response.status_code}',
                'type': 'api_error',
                'code': self.response.status_code
            }
        }

    def _build_standard_response(
        self,
        response_id: Optional[str],
        model: Optional[str],
        created: Optional[int],
        content: str,
        finish_reason: Optional[str],
        usage: Optional[Dict[str, int]]
    ) -> Dict[str, Any]:
        """Build standard OpenAI-compatible response"""
        import time

        return {
            'id': response_id or f'chatcmpl-{int(time.time())}',
            'object': 'chat.completion',
            'created': created or int(time.time()),
            'model': model or 'unknown',
            'choices': [{
                'index': 0,
                'message': {
                    'role': 'assistant',
                    'content': content
                },
                'finish_reason': finish_reason or 'stop'
            }],
            'usage': usage or {
                'prompt_tokens': 0,
                'completion_tokens': 0,
                'total_tokens': 0
            }
        }


    def get_error_message(self) -> Optional[str]:
        """Extract error message from response"""
        try:
            # Try to parse as JSON first
            data = self.response.json()
            if 'error' in data:
                if isinstance(data['error'], dict):
                    return data['error'].get('message', str(data['error']))
                return str(data['error'])
        except:
            pass

        # Return raw text
        try:
            text = self.response.text[:500]
            if text:
                return text
        except:
            pass

        return f"HTTP {self.response.status_code}"


def parse_response(response: Response) -> Dict[str, Any]:
    """Convenience function for parsing responses"""
    parser = ResponseParser(response)
    return parser.parse()
