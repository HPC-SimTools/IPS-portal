from functools import wraps
from flask import Blueprint, render_template, request, session, redirect, url_for, current_app, flash
import requests

bp = Blueprint('login', __name__)


def update_session(response):
    if response.status_code == requests.codes.OK:
        session.update(response.json())
    else:
        current_app.logger.info("Request failed for %s", session.get('username'))
        session['auth'] = False

    return session['auth']


def newt_login(username, password):
    current_app.logger.info("Attempt login for %s", username)
    response = requests.post("https://newt.nersc.gov/newt/auth", {"username": username,
                                                                  "password": password})

    return update_session(response)


def newt_check_login():
    if session.get('auth', False):
        response = requests.get("https://newt.nersc.gov/newt/login",
                                cookies={"newt_sessionid": session['newt_sessionid']})
        session.update(response.json())

        return update_session(response)

    return False


def newt_get_user_info():
    """Retireve user info and projects"""

    # get user info
    response = requests.post("https://newt.nersc.gov/newt/account/iris",
                             {"query": f"user(username: \\\"{session['username']}\\\") {{firstname, lastname}}"},
                             cookies={"newt_sessionid": session['newt_sessionid']})
    session.update(response.json()['data']['newt']['user'])

    # get projects
    response = requests.post("https://newt.nersc.gov/newt/account/iris",
                             {"query": f"roles(username: \\\"{session['username']}\\\") {{repoName}}"},
                             cookies={"newt_sessionid": session['newt_sessionid']})
    session['projects'] = [r['repoName'] for r in response.json()['data']['newt']['roles']]


def newt_logout():
    if session.get('auth', False):
        requests.post("https://newt.nersc.gov/newt/logout",
                      cookies={"newt_sessionid": session['newt_sessionid']})

        session.clear()

    return False


@bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if newt_login(request.form['username'], request.form['password']):
            newt_get_user_info()
            if next_url := request.form.get("next"):
                return redirect(next_url)
            return redirect(url_for('index.index'))
        else:
            flash("Incorrect username or password")
    else:
        if newt_check_login():
            return redirect(url_for('index.index'))

    return render_template("login.html")


@bp.route("/logout")
def logout():
    newt_logout()
    return redirect(url_for('index.index'))


# Remove this before going to production
@bp.route("/session")
def session_info():
    return session


def login_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if session.get('auth', False):
            return f(*args, **kwargs)

        flash("Login required")
        return redirect(url_for('login.login', next=request.path))

    return wrap
