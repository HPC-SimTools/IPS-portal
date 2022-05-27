import os
from flask import Blueprint, session, redirect
import requests
from ipsportal.login import login_required

bp = Blueprint('analysis', __name__)


@bp.route("/to_jupyter/<path:url>")
@login_required
def to_jupyter(url):
    filename = os.path.join(os.path.dirname(__file__), 'notebooks/monitor.ipynb')
    ipynb = open(filename).read()
    username = session['username']
    new_notebook = f"/global/homes/r/{username}/monitor.ipynb"
    requests.put("https://newt.nersc.gov/newt/file/cori/"+new_notebook,
                 data=ipynb.replace("$URL", url),
                 cookies={"newt_sessionid": session['newt_sessionid']})
    return redirect(f"https://jupyter.nersc.gov/user/{username}/cori-shared-node-cpu/lab/tree/{new_notebook}")
