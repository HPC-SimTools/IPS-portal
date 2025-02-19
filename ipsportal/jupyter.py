import logging
import os
from pathlib import Path

from .environment import JUPYTERHUB_PORTAL_DIR, JUPYTERHUB_DIR
from ._jupyter.initializer import initialize_jupyter_import_module_file, initialize_jupyter_notebook, initialize_jupyter_python_api, update_module_file_with_data_files
from ._jupyter.hub_implementations import get_jupyter_url_prefix

logger = logging.getLogger(__name__)

def _initialize_jupyterhub_dir(root_dir: Path) -> bool:
    """
    This is boilerplate which needs to happen the first time a JupyterHub workflow is initiated in a directory.
    """
    # TODO need to figure how to do authorization per-user
    try:
        os.makedirs(root_dir / 'data', exist_ok=True)
        initialize_jupyter_import_module_file(root_dir)
        initialize_jupyter_python_api(root_dir.parent)
    except OSError as e:
        logger.warning(f'Could not make directories with provided JUPYTERHUB_DIR value "{root_dir}", full error: {e}')
        return False
    
    return True

def add_jupyter_notebook(runid: int, username: str, notebook_name: str, data: bytes) -> tuple[str, int]:
    root_dir = JUPYTERHUB_PORTAL_DIR / username / str(runid)
    if not root_dir.exists():
        if not _initialize_jupyterhub_dir(root_dir):
            return ('Server screwed up', 500)
    
    try:
        initialize_jupyter_notebook(data, root_dir / notebook_name)
    except Exception:
        return ('Notebook was not valid', 400)
    # Return the fully qualified URL
    notebook_path = JUPYTERHUB_DIR / username / str(runid) / notebook_name
    url = f'{get_jupyter_url_prefix(username)}{notebook_path}'
    print(url)
    return (url, 201)

def add_analysis_data_file_for_timestep(
    runid: int, 
    username: str,
    filename: str,
    data: bytes, 
    timestamp: float = 0.0, 
    replace: bool = False
) -> tuple[str, int]:
    root_dir = JUPYTERHUB_PORTAL_DIR / username / str(runid)
    if not root_dir.exists():
        if not _initialize_jupyterhub_dir(root_dir):
            return ('Server screwed up', 500)
    
    data_file_loc = root_dir / 'data' / filename
    if not replace and Path.exists(data_file_loc):
        return ('Replace flag was not set but file already exists', 400)
    
    with open(data_file_loc, 'wb') as f:
        f.write(data)
    
    try:
        update_module_file_with_data_files(root_dir, filename, replace, timestamp)
    except Exception as e:
        logger.error(e)
        return ("Server couldn't update module file", 500)

    return ('Created', 201)
