from __future__ import annotations
__all__ = ['BackendConfig', 'all_backends_have_projects', 'configs_from_tokens', 'get_first_backend_project', 'parse_api_tokens', 'validate_backends_unique']
import os
from dataclasses import dataclass
from minfx.neptune_v2.common.envs import API_TOKEN_ENV_NAME
from minfx.neptune_v2.exceptions import NeptuneDuplicateBackendError, NeptuneMissingApiTokenException

@dataclass
class BackendConfig:
    api_token: str
    proxies: dict[str, str] | None = None
    project: str | None = None

def parse_api_tokens(api_token):
    if api_token is None:
        api_token = os.getenv(API_TOKEN_ENV_NAME)
    if api_token is None:
        raise NeptuneMissingApiTokenException()
    tokens = [t.strip() for t in api_token.split(',')]
    return [t for t in tokens if t]

def configs_from_tokens(api_tokens, proxies=None, project=None):
    if isinstance(api_tokens, str):
        tokens = parse_api_tokens(api_tokens)
    elif api_tokens is None:
        tokens = parse_api_tokens(None)
    else:
        tokens = api_tokens
    return [BackendConfig(api_token=token, proxies=proxies, project=project) for token in tokens]

def validate_backends_unique(backends):
    seen_tokens = set()
    for i, config in enumerate(backends):
        if config.api_token in seen_tokens:
            raise NeptuneDuplicateBackendError(f'Duplicate backend at index {i}: same api_token used multiple times')
        seen_tokens.add(config.api_token)

def all_backends_have_projects(backends):
    if not backends:
        return False
    return all((config.project is not None for config in backends))

def get_first_backend_project(backends):
    if not backends:
        return None
    return backends[0].project