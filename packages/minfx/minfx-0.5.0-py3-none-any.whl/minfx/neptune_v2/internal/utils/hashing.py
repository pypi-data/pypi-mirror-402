__all__ = ['generate_hash']
import hashlib

def generate_hash(*descriptors, length):
    hasher = hashlib.sha256()
    for descriptor in descriptors:
        hasher.update(str(descriptor).encode())
    return hasher.hexdigest()[-length:]