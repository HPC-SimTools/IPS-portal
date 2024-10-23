// in a URL for jupyter.nersc.gov , users must provide NERSC Shibboleth (auth manager) credentials in the URL, but this will only work for a single user.
// We can dynamically create this URL on the frontend.

const NERSC_URL_HELPER_STORAGE_KEY = "username__jupyter.nersc.gov";

function onJupyterUrlBtnClick() {
  const nersc_username = prompt(
    "Enter the username you authenticate with on NERSC Shibboleth.",
    window.localStorage.getItem(NERSC_URL_HELPER_STORAGE_KEY) || ""
  );
  if (nersc_username != null) {
    window.localStorage.setItem(NERSC_URL_HELPER_STORAGE_KEY, nersc_username);
    const result = jupyterUrlBtn
      .getAttribute("data-original-url")
      .replace(new RegExp("/user/[^/]+/"), `/user/${nersc_username}/`);
    window.location.href = result;
  }
}

for (jupyterUrlBtn of document.getElementsByClassName("jupyter-url-btn")) {
  jupyterUrlBtn.addEventListener("click", onJupyterUrlBtnClick);
}
