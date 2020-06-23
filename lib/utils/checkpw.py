import bcrypt
import functools

def checkpw(password: bytes, hash: bytes):
    if len(password) > 128: #to avoid possible memory DoS
        return False
    return _checkpw(password, hash)

@functools.lru_cache(maxsize=50)
def _checkpw(password: bytes, hash: bytes):
    return bcrypt.checkpw(password, hash)
