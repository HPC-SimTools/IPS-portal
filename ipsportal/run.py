import math
from flask import Blueprint, render_template, request
from . import api

bp = Blueprint('index', __name__)

ROWS_PER_PAGE = 20
SORT_BY_DEFAULT = 'runid'
SORT_DIRECTION_DEFAULT = -1
SORTABLE = ('runid', 'state', 'rcomment', 'simname', 'host', 'user')
INDEX_COLUMNS = ({'name': 'RunID', 'param': 'runid'},
                 {'name': 'Status', 'param': 'state'},
                 {'name': 'Comment', 'param': 'rcomment'},
                 {'name': 'Sim Name', 'param': 'simname'},
                 {'name': 'Host', 'param': 'host'},
                 {'name': 'User', 'param': 'user'},
                 {'name': 'Start Time', 'param': 'startat'},
                 {'name': 'Stop Time', 'param': 'stopat'})


@bp.route("/")
def index():
    page = {}
    page['page'] = request.args.get('page', 1, type=int)
    page['rows'] = request.args.get('rows', ROWS_PER_PAGE, type=int)
    page['rows'] = max(page['rows'], 5)
    page['rows_default'] = ROWS_PER_PAGE
    page['num_pages'] = math.ceil(api.runs_count() / page['rows'])
    page['page'] = min(page['page'], page['num_pages'])

    sort = {}
    sort['by'] = request.args.get('sort', SORT_BY_DEFAULT)
    sort['default'] = SORT_BY_DEFAULT
    if sort['by'] not in SORTABLE:
        sort['by'] = SORT_BY_DEFAULT
    sort['direction'] = request.args.get('direction', SORT_DIRECTION_DEFAULT, type=int)
    sort['direction_default'] = SORT_DIRECTION_DEFAULT
    if sort['direction'] not in (1, -1):
        sort['direction'] = SORT_DIRECTION_DEFAULT
    sort['sortable'] = SORTABLE

    json = {"page": page['page'],
            "per_page": page['rows'],
            "sort_by": sort['by'],
            "sort_direction": sort['direction']}

    return render_template("index.html", columns=INDEX_COLUMNS, runs=api.db_runs(json), page=page, sort=sort)


@bp.route("/<int:runid>")
def run(runid):
    return render_template("events.html", run=api.db_run_runid(runid), events=api.db_events_runid(runid))
