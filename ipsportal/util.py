from __future__ import annotations

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
