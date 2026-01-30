__all__ = ['send_checkpoint_created']
from minfx.neptune_v2.internal.utils.logger import get_logger
_logger = get_logger()

class MessageType:
    CHECKPOINT_CREATED = 'CHECKPOINT_CREATED'

def send_checkpoint_created(notebook_id, notebook_path, checkpoint_id):
    neptune_comm = _get_comm()
    neptune_comm.send(data={'message_type': MessageType.CHECKPOINT_CREATED, 'data': {'checkpoint_id': str(checkpoint_id), 'notebook_id': str(notebook_id), 'notebook_path': str(notebook_path)}})

def _get_comm():
    from ipykernel.comm import Comm
    return Comm(target_name='neptune_comm')