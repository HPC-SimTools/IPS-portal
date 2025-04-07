import logging
import os
from pathlib import Path

from ._jupyter.hub_implementations import get_jupyter_url_prefix
from ._jupyter.initializer import (
    initialize_jupyter_data_files,
    initialize_jupyter_notebook,
    initialize_jupyter_python_api,
    update_data_listing_file,
    update_parent_module_file_with_child_runid,
)
from .db import get_parent_runid_by_child_runid
from .environment import JUPYTERHUB_DIR, JUPYTERHUB_PORTAL_DIR

logger = logging.getLogger(__name__)


def _initialize_jupyterhub_dir(root_dir: Path, runid: int) -> bool:
    """
    This is boilerplate which needs to happen the first time a JupyterHub workflow is initiated in a directory.
    """
    # TODO need to figure how to do authorization per-user
    try:
        os.makedirs(root_dir / 'data', exist_ok=True)
        initialize_jupyter_python_api(root_dir.parent)
        initialize_jupyter_data_files(root_dir)
        parent_portal_runid = get_parent_runid_by_child_runid(runid)
        if parent_portal_runid:
            update_parent_module_file_with_child_runid(root_dir.parent / str(parent_portal_runid), runid)

    except OSError as e:
        logger.warning(
            'Could not make directories with provided JUPYTERHUB_DIR value "%s", full error: %s', root_dir, e
        )
        return False

    return True


def add_jupyter_notebook(runid: int, username: str, notebook_name: str, data: bytes) -> tuple[str, int]:
    root_dir = JUPYTERHUB_PORTAL_DIR / username / str(runid)
    if not root_dir.exists() and not _initialize_jupyterhub_dir(root_dir, runid):
        return ('Server screwed up', 500)

    try:
        initialize_jupyter_notebook(data, root_dir / notebook_name)
    except Exception:  # noqa: BLE001
        return ('Notebook was not valid', 400)
    # Return the fully qualified URL
    notebook_path = JUPYTERHUB_DIR / username / str(runid) / notebook_name
    url = f'{get_jupyter_url_prefix(username)}{notebook_path}'
    return (url, 201)


def add_analysis_data_file_for_timestep(
    runid: int, username: str, filename: str, data: bytes, timestamp: float = 0.0, replace: bool = False
) -> tuple[str, int]:
    root_dir = JUPYTERHUB_PORTAL_DIR / username / str(runid)
    if not root_dir.exists() and not _initialize_jupyterhub_dir(root_dir, runid):
        return ('Server screwed up', 500)

    data_file_loc = root_dir / 'data' / filename
    if not replace and Path.exists(data_file_loc):
        return ('Replace flag was not set but file already exists', 400)

    with open(data_file_loc, 'wb') as f:
        f.write(data)

    try:
        update_data_listing_file(root_dir, filename, timestamp)
    except Exception:
        logger.exception('Unable to update module file with the data files')
        return ("Server couldn't update module file", 500)

    return ('Created', 201)
