from __future__ import annotations
__all__ = ['Credentials']
import base64
from dataclasses import dataclass
import json
import os
from minfx.neptune_v2.common.envs import API_TOKEN_ENV_NAME
from minfx.neptune_v2.common.exceptions import NeptuneInvalidApiTokenException
from minfx.neptune_v2.constants import ANONYMOUS_API_TOKEN
from minfx.neptune_v2.exceptions import NeptuneMissingApiTokenException
from minfx.neptune_v2.internal.constants import ANONYMOUS_API_TOKEN_CONTENT

@dataclass(frozen=True)
class Credentials:
    api_token: str
    token_origin_address: str
    api_url_opt: str

    @classmethod
    def from_token(cls, api_token=None):
        if api_token is None:
            api_token = os.getenv(API_TOKEN_ENV_NAME)
        if api_token == ANONYMOUS_API_TOKEN:
            api_token = ANONYMOUS_API_TOKEN_CONTENT
        if api_token is None:
            raise NeptuneMissingApiTokenException
        api_token = api_token.strip()
        token_dict = Credentials._api_token_to_dict(api_token)
        if 'api_address' not in token_dict:
            raise NeptuneInvalidApiTokenException
        token_origin_address = token_dict['api_address']
        api_url = token_dict.get('api_url', None)
        return Credentials(api_token=api_token, token_origin_address=token_origin_address, api_url_opt=api_url)

    @staticmethod
    def _api_token_to_dict(api_token):
        try:
            return json.loads(base64.b64decode(api_token.encode()).decode('utf-8'))
        except Exception:
            raise NeptuneInvalidApiTokenException