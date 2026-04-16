#!/bin/sh

# guarantees that non-root will have permissions managing files created from web interface, i.e. .ipynb_checkpoints
umask 007
exec start-notebook.py --NotebookApp.token=''
