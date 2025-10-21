import logging
from csv import DictReader
from typing import Any

from flask import Blueprint, render_template
from urllib3.util import parse_url

from ipsportal.db import get_data_information, get_run, get_runid

logger = logging.getLogger(__name__)

bp = Blueprint('index', __name__)


@bp.route('/')
def index() -> tuple[str, int]:
    return render_template('index.html'), 200


@bp.route('/<int:runid>')
def run(runid: int) -> tuple[str, int]:
    run = get_run({'runid': runid})
    if run is None:
        return render_template('notfound.html', run=runid), 404

    if run.get('parent_portal_runid') is not None:
        run['parent_runid'] = get_runid(str(run.get('parent_portal_runid')))
    else:
        run['parent_runid'] = None
    data_info, jupyter_urls, ensemble_information_meta = get_data_information(runid)
    if jupyter_urls:
        resolved_jupyter_urls = [[jupyter_url, parse_url(jupyter_url).host] for jupyter_url in jupyter_urls]
    else:
        resolved_jupyter_urls = None
    ensemble_information = []
    if ensemble_information_meta:
        for listing in ensemble_information_meta:
            try:
                with open(listing['path']) as fd:
                    data: list[dict[str, Any]] = list(DictReader(fd))
                    # component keys should ALWAYS have a ':' in them, and non-component keys should NEVER have a ':' in them. Make sure the framework follows this convention.
                    component_keys = list(filter(lambda column: ':' in column, data[0].keys()))
                    ensemble_information.append(
                        {
                            'data': data,
                            'ensemble_name': listing['ensemble_name'],
                            'component_keys': component_keys,
                        }
                    )
            except Exception:
                logger.exception('potentially invalid listing: %s', listing)
    return render_template(
        'events.html',
        run=run,
        data_info=data_info,
        jupyter_urls=resolved_jupyter_urls,
        ensemble_information=ensemble_information,
    ), 200
