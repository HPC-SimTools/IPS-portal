const NERSC_URL_HELPER_STORAGE_KEY = "username__jupyter.nersc.gov";

// in a URL for jupyter.nersc.gov , users must provide NERSC Shibboleth (auth manager) credentials in the URL, but this will only work for a single user.
// We can dynamically create this URL on the frontend.
function onNerscJupyterUrlBtnClick(event) {
  const nerscUsername = window.prompt(
    "Enter your NERSC username.",
    window.localStorage.getItem(NERSC_URL_HELPER_STORAGE_KEY) || ""
  );
  if (nerscUsername != null) {
    window.localStorage.setItem(NERSC_URL_HELPER_STORAGE_KEY, nerscUsername);
    const result = event.currentTarget
      .getAttribute("data-original-url")
      .replace(new RegExp("/user/[^/]+/"), `/user/${nerscUsername}/`);
    window.open(result);
  }
}

for (let jupyterUrlBtn of document.getElementsByClassName("jupyter-nersc-url-btn")) {
  jupyterUrlBtn.addEventListener("click", onNerscJupyterUrlBtnClick);
}
