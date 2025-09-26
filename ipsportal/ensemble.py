import csv
import os
import shutil
from io import StringIO
from tempfile import NamedTemporaryFile
from typing import Any

from ._jupyter.hub_implementations import get_jupyter_url_prefix


def save_initial_csv(initial_csv: bytes, path: str | os.PathLike[Any]) -> None:
    data = list(csv.reader(StringIO(initial_csv.decode())))

    # generate columns for later
    data[0] = ['portal_runid', 'run_url', 'instance_analysis_url', *data[0]]
    for i in range(1, len(data)):
        data[i] = ['?', '?', '?', *data[i]]

    with open(path, 'w', newline='') as fd:
        writer = csv.writer(fd)
        writer.writerows(data)


def update_ensemble_information(
    runid: int, base_url: str, sim_name: str, username: str, csv_path: str | os.PathLike[Any]
) -> None:
    with NamedTemporaryFile(mode='w', delete=False, newline='') as tempfile, open(csv_path) as fd:
        reader = csv.reader(fd)

        writer = csv.writer(tempfile)

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

    shutil.move(tempfile.name, csv_path)
