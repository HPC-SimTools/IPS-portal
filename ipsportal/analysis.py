import os
from flask import Blueprint, session, redirect, request
import requests
from ipsportal.login import login_required

bp = Blueprint('analysis', __name__)


@bp.route("/to_jupyter")
@login_required
def to_jupyter():
    filename = os.path.join(os.path.dirname(__file__), 'notebooks/monitor.ipynb')
    ipynb = open(filename).read()
    username = session['username']
    new_notebook = f"/global/homes/r/{username}/monitor.ipynb"
    requests.put("https://newt.nersc.gov/newt/file/cori/"+new_notebook,
                 data=ipynb.replace("$URL", request.args.get('url')),
                 cookies={"newt_sessionid": session['newt_sessionid']})
    return redirect(f"https://jupyter.nersc.gov/user-redirect/lab/tree/{new_notebook}?url={request.args.get('url')}")
