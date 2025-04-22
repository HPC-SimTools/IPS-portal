import re

ALLOWED_PROPS_RUN = [
    'runid',
    'state',
    'rcomment',
    'simname',
    'host',
    'user',
    'startat',
    'stopat',
    'walltime',
]
"""
Properties we allow sort queries on for the runs table.

THIS MUST MATCH THE CLIENT SIDE CONFIGURATION.
"""

VALID_FILENAME_REGEX = re.compile('^[a-zA-Z0-9._-]+$')


# based on https://stackoverflow.com/a/31976060
def is_valid_filename(filename: str) -> bool:
    """Make sure that users submit a file which is reasonable and would be valid on any OS"""
    return bool(VALID_FILENAME_REGEX.match(filename))
