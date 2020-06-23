import copy

def safe_raw(raw: dict):
    '''remove all tokens from a raw request for logging'''
    safe = copy.deepcopy(raw)
    safe.pop('secret', None)
    safe.get('session', dict()).get('user', dict()).pop('access_token', None)
    return safe
