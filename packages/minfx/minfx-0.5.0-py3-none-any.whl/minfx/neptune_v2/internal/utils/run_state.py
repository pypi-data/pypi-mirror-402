__all__ = ['RunState']
import enum
from minfx.neptune_v2.common.exceptions import NeptuneException
_API_TO_STATE = {}
_STATE_TO_API = {}

class RunState(enum.Enum):
    ACTIVE = 'Active'
    INACTIVE = 'Inactive'

    @classmethod
    def from_string(cls, value):
        try:
            return cls(value.capitalize())
        except ValueError as e:
            raise NeptuneException(f"Can't map RunState from string: {value}") from e

    @classmethod
    def from_api(cls, value):
        if value not in _API_TO_STATE:
            raise NeptuneException(f'Unknown RunState from API: {value}')
        return _API_TO_STATE[value]

    def to_api(self):
        return _STATE_TO_API[self]
_API_TO_STATE.update({'running': RunState.ACTIVE, 'idle': RunState.INACTIVE})
_STATE_TO_API.update({RunState.ACTIVE: 'running', RunState.INACTIVE: 'idle'})