from ...environment import JUPYTERHUB_IMPLEMENTATION

from .generic import get_url_prefix_generic
from .nersc import get_url_prefix_nersc

def get_jupyter_url_prefix(username: str) -> str:
    if JUPYTERHUB_IMPLEMENTATION == 'nersc':
        return get_url_prefix_nersc(username)
    return get_url_prefix_generic()
