from flask import Blueprint, render_template
from urllib3.util import parse_url

from ipsportal.db import get_data_information, get_run, get_runid

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
    data_info, jupyter_urls, ensemble_paths = get_data_information(runid)
    if jupyter_urls:
        resolved_jupyter_urls = [[jupyter_url, parse_url(jupyter_url).host] for jupyter_url in jupyter_urls]
    else:
        resolved_jupyter_urls = None
    return render_template('events.html', run=run, data_info=data_info, jupyter_urls=resolved_jupyter_urls), 200
