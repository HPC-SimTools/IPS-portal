"""
NOTE: this is not intended to be a public API for framework users, use instead:
  - "services.initialize_jupyter_notebook" (to set up the JupyterHub interaction for a notebook, done only once)
  - "services.add_analysis_data_file" (each time you want to add or remove a data file from JupyterHub)

This module is designed to help generate JupyterNotebooks to be used with IPS Portal analysis.
Some parts of the script will need direction from users on the Framework side to generate.

Note that this module is currently biased towards working with NERSC (jupyter.nersc.gov), so will attempt to import specific libraries.

To see available libraries on NERSC, run:
  !pip list

...in a shell on Jupyter NERSC.
"""

import json
import logging
import mmap
import shutil
from pathlib import Path

import nbformat as nbf

_logger = logging.getLogger(__name__)

IPS_DATA_LIST_FILE = 'ips_analysis_api_data_listing.json'
IPS_CHILD_RUNS_FILE = 'ips_analysis_api_child_runs.txt'

CURRENT_API_VERSION = 'v1'


def replace_last(source_string: str, old: str, new: str) -> str:
    """Attempt to replace the last occurence of 'old' with 'new' in 'source_string', searching from the right.

    This should only be called if 'old' can effectively be guaranteed to exist in the string.
    """
    head, _sep, tail = source_string.rpartition(old)
    return f'{head}{new}{tail}'


def _jupyter_notebook_api_code() -> bytes:
    """Return the raw code of the JupyterNotebook file which will be placed in the JupyterHub multirun file directory."""
    return b"""
{
 "cells": [
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "## IPS workstation\\n",
    "\\n",
    "You can use this notebook to quickly generate a tarfile with desired runids for download. "
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": [
    "from pathlib import Path\\n",
    "\\n",
    "import ips_analysis_api_v1\\n",
    "from IPython.display import display\\n",
    "from ipywidgets import HTML, Button, Layout, Textarea\\n",
    "\\n",
    "widget1 = Textarea(\\n",
    "    value='',\\n",
    "    placeholder='Enter runids you want to download, delimited by either spaces or newlines',\\n",
    "    description='Enter runids you want to download, delimited by either spaces or newlines',\\n",
    "    layout=Layout(width='50%', display='flex', flex_flow='column')\\n",
    ")\\n",
    "\\n",
    "widget2 = Button(\\n",
    "    description='Generate tar from input',\\n",
    "    layout=Layout(width='300px')\\n",
    ")\\n",
    "\\n",
    "def generate_tarfile(_button_widget):\\n",
    "    runids = [int(v) for v in widget1.value.split()]\\n",
    "    display(f'Generating tar file from runids: {runids}')\\n",
    "    \\n",
    "    file = Path(ips_analysis_api_v1.generate_tar_from_runids(runids))\\n",
    "    display(f'Generated tar file {file.name} in directory {file.parent}, right click the file in the file browser to download it')\\n",
    "\\n",
    "widget2.on_click(generate_tarfile)\\n",
    "\\n",
    "display(widget1,widget2,HTML('''<style>\\n",
    "    .widget-label { width: unset !important; }\\n",
    "</style>'''))"
   ]
  }
 ],
 "metadata": {
  "language_info": {
   "name": "python"
  }
 },
 "nbformat": 4,
 "nbformat_minor": 2
}
"""


def initialize_jupyter_python_api(jupyterhub_dir: Path) -> None:
    """Set up all API files."""
    source_dir = Path(__file__).parent
    dest_dir = Path(jupyterhub_dir)

    python_fname = f'ips_analysis_api_{CURRENT_API_VERSION}.py'
    shutil.copyfile(
        source_dir / python_fname,
        dest_dir / python_fname,
    )

    with open(dest_dir / f'ips_analysis_api_{CURRENT_API_VERSION}_notebook.ipynb', 'wb') as f:
        f.write(_jupyter_notebook_api_code())


def initialize_jupyter_notebook(notebook_src: bytes, notebook_dest: Path) -> None:
    """Create a new notebook from an old notebook, copying the result from 'src' to 'dest'.

    This adds an additional cell which will import the data files. The notebook should not be written again after this function.

    Params:
      - notebook_src - raw bytes of original notebook
      - notebook_dest - location of notebook to create on filesystem (absolute file path)
    """
    # to avoid conversion, use as_version=nbf.NO_CONVERT
    nb: nbf.NotebookNode = nbf.reads(notebook_src, as_version=4)  # type: ignore[no-untyped-call]

    nb['cells'] = [
        # explicitly mark the IPS cell for users inspecting the file, unused programatically
        # TODO add documentation link here
        nbf.v4.new_markdown_cell(f"""## Next cell generated by IPS Framework

Basic API instructions:
  - ips_analysis_api.get_data() - this generates a generic IPS mapping - a mapping of floating-point timesteps to a list of data file paths (absolute). Note that your notebook will need to handle the actual loading of the data.
  - ips_analysis_api.get_child_data() - this generates a mapping of child runids to the "generic IPS mapping" described above.

To understand how the API works, you can inspect the 'ips_analysis_api_{CURRENT_API_VERSION}.py' file directly by going up one directory from where this notebook is located.
"""),  # type: ignore[no-untyped-call]
        nbf.v4.new_code_cell(f"""
import importlib.util
import pathlib

# IPS API initialization code
def _ips_analysis_api():
    _IPS_THIS_DIR = pathlib.Path(globals()['_dh'][0])
    _ips_spec = importlib.util.spec_from_file_location(
        '', str(_IPS_THIS_DIR.parent / 'ips_analysis_api_{CURRENT_API_VERSION}.py')
    )
    _ips_module = importlib.util.module_from_spec(_ips_spec)  # type: ignore[arg-type]
    _ips_spec.loader.exec_module(_ips_module)  # type: ignore[union-attr]
    return _ips_module.IPSAnalysisApi(_IPS_THIS_DIR)

# IPS API for use in your custom notebook
ips_analysis_api = _ips_analysis_api()
"""),  # type: ignore[no-untyped-call]
    ] + nb['cells'][:]

    nbf.validate(nb)
    with open(notebook_dest, 'w') as f:
        nbf.write(nb, f)  # type: ignore[no-untyped-call]


def _initialize_child_runs_file(dest: Path) -> None:
    child_runs_file = dest / IPS_CHILD_RUNS_FILE
    child_runs_file.touch(mode=0o660, exist_ok=True)


def _initialize_jupyter_data_list_file(dest: Path) -> None:
    data_file = dest / IPS_DATA_LIST_FILE
    data_file.touch(mode=0o660, exist_ok=True)
    # generate an empty dictionary to guarantee that we have valid JSON
    with open(data_file, 'w') as f:
        f.write('{\n}\n')


def initialize_jupyter_data_files(dest: Path) -> None:
    """Initialize the dynamically written data files for a run.

    Params:
      - dest - directory where we will create the module file on filesystem (absolute file path)
    """
    _initialize_child_runs_file(dest)
    _initialize_jupyter_data_list_file(dest)


def update_data_listing_file(dest: Path, filename: str, timestamp: float = 0.0) -> None:
    """
    Potentially update the data listing file with new information.

    NOTE: You should handle the "replace" flag before calling this function.

    Params:
      - dest: directory of the module file which will be modified
      - filename: name of file which will be added to module
      - timestamp: key we associate the data file with

    """
    data_listing_file = dest / IPS_DATA_LIST_FILE
    if not data_listing_file.exists():
        # we will potentially raise an OSError here
        _initialize_jupyter_data_list_file(dest)

    datafile_dest = f'data/{filename}'
    with open(data_listing_file, 'r+') as f:
        try:
            mapping: dict[str, list[str]] = json.load(f)
        except json.JSONDecodeError:
            # file is not valid JSON, so we'll overwrite it outright
            mapping = {}
        string_timestamp = str(timestamp)
        timestamp_values = mapping.get(string_timestamp)
        if not isinstance(timestamp_values, list):
            mapping[string_timestamp] = [datafile_dest]
        elif datafile_dest not in timestamp_values:
            timestamp_values.append(datafile_dest)
        else:
            # no need to write, duplicate value detected
            return

        f.seek(0)
        f.truncate(0)
        f.write(json.dumps(mapping, indent=2))


def update_parent_module_file_with_child_runid(dest: Path, child_runid: int) -> None:
    child_runs_file = dest / IPS_CHILD_RUNS_FILE
    if not child_runs_file.exists():
        # attempt recovery
        _initialize_child_runs_file(dest)

    with open(child_runs_file, 'ab+') as f:
        encoded_child_runid = f'{child_runid}\n'.encode()
        try:
            map_file = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
            for line in iter(map_file.readline, b''):
                if line == encoded_child_runid:
                    # child run already exists
                    return
        except ValueError:
            # can't mmap empty files, we can write regardless
            pass
        f.write(encoded_child_runid)
