from ...environment import JUPYTERHUB_BASE_URL


# this URL needs to handle a few separate prefixes to the JupyterHub tree:
# 1) NERSC Shibboleth authentication (need username information to work this out)
# 2) which NERSC node to run on (will assume the login node by default)
def get_url_prefix_generic() -> str:
    return JUPYTERHUB_BASE_URL
