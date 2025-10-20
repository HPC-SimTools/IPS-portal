import csv
import logging
import os
from io import StringIO
from typing import Any

from ._jupyter.hub_implementations import get_jupyter_url_prefix

logger = logging.getLogger(__name__)


def save_initial_csv(initial_csv: bytes, path: str | os.PathLike[Any]) -> None:
    data = list(csv.reader(StringIO(initial_csv.decode())))

    # generate columns for later
    data[0] = ['portal_runid', 'run_url', 'instance_analysis_url', *data[0]]
    for i in range(1, len(data)):
        data[i] = ['?', '?', '?', *data[i]]

    # TODO this path should be created earlier...
    dirname = os.path.dirname(path)
    if not os.path.exists(dirname):
        logger.warning('needed to create %s, this should not happen here', dirname)
        os.makedirs(path, exist_ok=True)

    with open(path, 'w', newline='') as fd:
        writer = csv.writer(fd)
        writer.writerows(data)


def update_ensemble_information(
    runid: int, base_url: str, sim_name: str, username: str, csv_path: str | os.PathLike[Any]
) -> None:
    # we will want to make sure that each call to this function has an exclusive read/write to the file descriptor at one time.
    # do not read from one FD and write to a separate FD, as this can cause update issues.
    with open(csv_path, 'r+') as fd:
        # we will need to read the entire file into memory while still holding the file descriptor
        reader = csv.reader(fd.readlines())
        fd.seek(0)
        writer = csv.writer(fd)

        # handle header row separately
        header_row = next(reader)
        writer.writerow(header_row)

        for row in reader:
            # sim names are unique per ensemble, find the name and insert
            if row[3] == sim_name:
                row[0] = str(runid)
                row[1] = f'{base_url}/{runid}'
                row[2] = f'{get_jupyter_url_prefix(username)}/{username}/{runid}'
            writer.writerow(row)
