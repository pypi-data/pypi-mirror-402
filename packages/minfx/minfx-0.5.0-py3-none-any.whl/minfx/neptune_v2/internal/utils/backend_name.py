from __future__ import annotations
__all__ = ['backend_name_from_url', 'backend_address_from_url', 'url_matches_backend_name', 'get_backend_name_from_token', 'is_named_backend_directory']
import base64
import json
from urllib.parse import urlparse

def backend_name_from_url(url):
    parsed = urlparse(url)
    host = parsed.hostname or 'unknown'
    port = parsed.port or (443 if parsed.scheme == 'https' else 80)
    safe_host = host.replace('.', '_')
    return f'{safe_host}_{port}'

def backend_address_from_url(url):
    parsed = urlparse(url)
    host = parsed.hostname or 'unknown'
    port = parsed.port or (443 if parsed.scheme == 'https' else 80)
    return f'{host}:{port}'

def url_matches_backend_name(url, backend_name):
    return backend_name_from_url(url) == backend_name

def get_backend_name_from_token(api_token):
    try:
        decoded = json.loads(base64.b64decode(api_token.strip().encode()).decode('utf-8'))
        api_url = decoded.get('api_address')
        if api_url:
            return backend_name_from_url(api_url)
        return None
    except Exception:
        return None

def is_named_backend_directory(name):
    if '_' not in name:
        return False
    if name.startswith('backend_'):
        suffix = name[len('backend_'):]
        if suffix.isdigit():
            return False
    parts = name.rsplit('_', 1)
    if len(parts) != 2:
        return False
    last_part = parts[1]
    if not last_part.isdigit():
        return False
    port = int(last_part)
    return 1 <= port <= 65535

def _run_tests():
    assert backend_name_from_url('http://neptune2.localhost:8889') == 'neptune2_localhost_8889'
    assert backend_name_from_url('https://app.neptune.ai') == 'app_neptune_ai_443'
    assert backend_name_from_url('http://localhost') == 'localhost_80'
    assert backend_name_from_url('https://localhost:9000') == 'localhost_9000'
    assert backend_name_from_url('http://my.deep.nested.domain:1234') == 'my_deep_nested_domain_1234'
    assert backend_address_from_url('http://neptune2.localhost:8889') == 'neptune2.localhost:8889'
    assert backend_address_from_url('https://app.neptune.ai') == 'app.neptune.ai:443'
    assert backend_address_from_url('http://localhost') == 'localhost:80'
    assert url_matches_backend_name('http://neptune2.localhost:8889', 'neptune2_localhost_8889') is True
    assert url_matches_backend_name('http://neptune2.localhost:8889', 'neptune2_localhost_8890') is False
    assert url_matches_backend_name('https://app.neptune.ai', 'app_neptune_ai_443') is True
    test_token_data = {'api_address': 'http://neptune2.localhost:8889'}
    test_token = base64.b64encode(json.dumps(test_token_data).encode()).decode()
    assert get_backend_name_from_token(test_token) == 'neptune2_localhost_8889'
    assert get_backend_name_from_token(f'  {test_token}  ') == 'neptune2_localhost_8889'
    assert get_backend_name_from_token('invalid_token') is None
    assert get_backend_name_from_token('') is None
    empty_token = base64.b64encode(json.dumps({}).encode()).decode()
    assert get_backend_name_from_token(empty_token) is None
    assert is_named_backend_directory('neptune2_localhost_8889') is True
    assert is_named_backend_directory('app_neptune_ai_443') is True
    assert is_named_backend_directory('localhost_80') is True
    assert is_named_backend_directory('localhost_8889') is True
    assert is_named_backend_directory('backend_0') is False
    assert is_named_backend_directory('backend_1') is False
    assert is_named_backend_directory('backend_10') is False
    assert is_named_backend_directory('some_dir') is False
    assert is_named_backend_directory('nounderscores') is False
    assert is_named_backend_directory('port_99999') is False
    print('All backend_name tests passed!')
if __name__ == '__main__':
    _run_tests()