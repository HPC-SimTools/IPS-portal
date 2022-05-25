from flask import Blueprint, render_template, request, session, redirect, url_for, current_app
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


@bp.route("/login")
def login():
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


@bp.route("/login", methods=['POST'])
def login_user():
    if 'username' not in request.form or 'password' not in request.form:
        return "Missing username or password", 400

    if newt_login(request.form['username'], request.form['password']):
        newt_get_user_info()
        return redirect(url_for('index.index'))

    return login()
