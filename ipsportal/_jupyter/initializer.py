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

import logging
import re
import shutil
from pathlib import Path

import nbformat as nbf

_logger = logging.getLogger(__name__)

DIRECTORY_VARIABLE_NAME = 'DATA_DIR'
DATA_VARIABLE_NAME = 'DATA_FILES'
CHILD_RUNS_VARIABLE_NAME = 'CHILD_RUNS'
DATA_MODULE_NAME = 'portal_data_listing_'
CURRENT_API_VERSION = 'v1'

CHILD_RUNS_REGEX = re.compile(f'{CHILD_RUNS_VARIABLE_NAME}(.*?)\\]', re.DOTALL)


def replace_last(source_string: str, old: str, new: str) -> str:
    """Attempt to replace the last occurence of 'old' with 'new' in 'source_string', searching from the right.

    This should only be called if 'old' can effectively be guaranteed to exist in the string.
    """
    head, _sep, tail = source_string.rpartition(old)
    return f'{head}{new}{tail}'


def _initial_data_file_code() -> str:
    return f"""# This file should be imported by a jupyter notebook or the generated API. DO NOT EDIT UNTIL IPS RUN IS FINALIZED. It is highly recommended you do NOT further edit this file.

import os
import pathlib
import sys

{DIRECTORY_VARIABLE_NAME} = str(pathlib.Path(__file__).resolve().parent / 'data') + os.path.sep
{CHILD_RUNS_VARIABLE_NAME} = [
]

def ips_get_child_run_data():
    import importlib.util

    modname = 'api_{CURRENT_API_VERSION}'
    fname = str(pathlib.Path(__file__).parents[1] / f'{{modname}}.py')

    spec = importlib.util.spec_from_file_location(modname, fname)
    if spec is None:
        raise ImportError("Could not load spec for module '{{modname}}' at: {{fname}}")
    module = importlib.util.module_from_spec(spec)
    #sys.modules[modname] = module
    try:
        spec.loader.exec_module(module)
    except FileNotFoundError as e:
        raise ImportError(f"{{e.strerror}}: {{fname}}") from e

    return module.get_data_from_runids({CHILD_RUNS_VARIABLE_NAME})

{DATA_VARIABLE_NAME} = {{
}}
"""


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
    "import api_v1\\n",
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
    "    file = Path(api_v1.generate_tar_from_runids(runids))\\n",
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
    """Set up the multirun API files."""
    source_dir = Path(__file__).parent
    dest_dir = Path(jupyterhub_dir)

    python_fname = f'api_{CURRENT_API_VERSION}.py'
    shutil.copyfile(
        source_dir / python_fname,
        dest_dir / python_fname,
    )

    with open(dest_dir / f'api_{CURRENT_API_VERSION}_notebook.ipynb', 'wb') as f:
        f.write(_jupyter_notebook_api_code())


def initialize_jupyter_notebook(notebook_src: bytes, notebook_dest: Path, runid: int) -> None:
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
        nbf.v4.new_markdown_cell("""## Next cell generated by IPS Framework

Execute this cell again to use new data during the simulation.
"""),  # type: ignore[no-untyped-call]
        nbf.v4.new_code_cell(f"""
import importlib

import {DATA_MODULE_NAME}{runid}
importlib.reload({DATA_MODULE_NAME}{runid})
{DATA_VARIABLE_NAME} = {DATA_MODULE_NAME}{runid}.{DATA_VARIABLE_NAME}

ips_get_child_run_data = {DATA_MODULE_NAME}{runid}.ips_get_child_run_data

"""),  # type: ignore[no-untyped-call]
    ] + nb['cells'][:]

    nbf.validate(nb)
    with open(notebook_dest, 'w') as f:
        nbf.write(nb, f)  # type: ignore[no-untyped-call]


def initialize_jupyter_import_module_file(dest: Path, runid: int) -> None:
    """Create a new notebook from an old notebook, copying the result from 'src' to 'dest'.

    Params:
      - dest - directory where we will create the module file on filesystem (absolute file path)
    """

    with open(dest / f'{DATA_MODULE_NAME}{runid}.py', 'w') as f:
        f.write(_initial_data_file_code())


def update_module_file_with_data_files(
    dest: Path, runid: int, filename: str, replace: bool, timestamp: float = 0.0
) -> None:
    """
    Params:
      - dest: directory of the module file which will be modified
      - filename: name of file which will be added to module
      - replace: if True, we can update
      - timestamp: key we associate the data file with

    """
    module_file = dest / f'{DATA_MODULE_NAME}{runid}.py'
    with open(module_file) as f:
        old_module_code = f.read()

    new_listing = f"f'{{{DIRECTORY_VARIABLE_NAME}}}{filename}',"
    new_str = f'{timestamp}: [{new_listing}],\n'

    timestamp_regex = str(timestamp).replace('.', '\\.')
    search_pattern = f'{timestamp_regex}: \[(.*)\],\n'

    found_match = re.search(search_pattern, old_module_code)
    if found_match:
        if replace:
            # need to completely replace the timestamp dictionary value with the new file listing
            new_module_code = re.sub(search_pattern, new_str, old_module_code, count=1)
        else:
            # need to append the timestamp dictionary value with the new file listing
            new_module_code = re.sub(
                search_pattern, f'{found_match.group(0)[:-3]}{new_listing}],\n', old_module_code, count=1
            )
    else:
        # need to add new timestamp dictionary key
        new_module_code = replace_last(old_module_code, '}', new_str + '}')

    with open(module_file, 'w') as f:
        f.write(new_module_code)


def update_parent_module_file_with_child_runid(dest: Path, parent_runid: int, child_runid: int) -> None:
    module_file = dest / f'{DATA_MODULE_NAME}{parent_runid}.py'
    try:
        with open(module_file) as f:
            old_module_code = f.read()
    except OSError:
        _logger.exception('Module file for id %s may be missing', parent_runid)
        return

    # TODO this should generally work except in the event of people adding comments inside of the array variable
    found_match = CHILD_RUNS_REGEX.search(old_module_code)

    # failsafe, this should exist unless user modified file manually
    if not found_match:
        return

    result = found_match.group(0)
    # this regex should be much safer, it is unlikely that the child runid will already exist in the first match
    found_number_pattern = f'[^0-9]{child_runid}[^0-9]'
    found_number_search = re.search(found_number_pattern, result, re.MULTILINE)

    if found_number_search:
        # runid already exists
        return

    new_str = f'{result[:-1]}{child_runid},\n]'
    new_module_code = old_module_code.replace(result, new_str, 1)
    with open(module_file, 'w') as f:
        f.write(new_module_code)
