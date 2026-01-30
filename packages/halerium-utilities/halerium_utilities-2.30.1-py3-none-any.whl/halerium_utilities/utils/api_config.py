import logging
import os
from urllib.parse import urljoin, quote


def _get_runner_headers():
    headers = {"halerium-runner-token": os.environ["HALERIUM_TOKEN"]}
    return headers


def _get_runner_api_base_url():
    tenant = os.getenv('HALERIUM_TENANT_KEY', '')
    workspace = os.getenv('HALERIUM_PROJECT_ID', '')
    runner_id = os.getenv('HALERIUM_ID', '')
    base_url = os.getenv('HALERIUM_BASE_URL', '')

    url = urljoin(base_url,
                  f"/api/tenants/{quote(tenant, safe='')}"
                  f"/projects/{quote(workspace, safe='')}"
                  f"/runners/{quote(runner_id, safe='')}")
    return url


def _on_runner():
    tenant = os.getenv('HALERIUM_TENANT_KEY', '')
    workspace = os.getenv('HALERIUM_PROJECT_ID', '')
    runner_id = os.getenv('HALERIUM_ID', '')
    base_url = os.getenv('HALERIUM_BASE_URL', '')
    runner_token = os.getenv('HALERIUM_TOKEN', '')
    if tenant and workspace and runner_id and base_url and runner_token:
        return True

    return False


API_PARAMETERS = {
    "api_base_url": None,
    "headers": None
}


def update_api_parameters(api_base_url: str = None,
                          headers: dict = None):
    """
    Updates the api_base_url or headers for all
    Halerium API based functions like the `collab`, `hal_es`, `prompt` and `stores` submodules.

    Parameters
    ----------
    api_base_url : str, optional
    headers : dict, optional
    """

    if api_base_url:
        API_PARAMETERS["api_base_url"] = api_base_url
    if headers is not None:
        API_PARAMETERS["headers"] = headers


def reset_api_parameters():
    for key in API_PARAMETERS:
        API_PARAMETERS[key] = None


def _get_api_base_url():
    if API_PARAMETERS["api_base_url"]:
        return API_PARAMETERS["api_base_url"]

    if _on_runner():
        return _get_runner_api_base_url()

    logging.warning(
        "No API base url available. Set them with "
        "`halerium_utilities.utils.api_config.update_api_parameters`.")
    return ""


def get_api_base_url():
    """
    Returns the api base url without a trailing "/".
    The result is based on environment variables or previous inputs to `update_api_parameters`.

    Returns
    -------
    url: str
        The url without a trailing slash,
        e.g. 'https://pro.halerium.ai/api/tenants/test/projects/123123123/runners/456456456'
    """
    return _get_api_base_url().rstrip("/")


def get_api_headers():
    """
    Returns the api headers.
    The result is based on environment variables or previous inputs to `update_api_parameters`.

    Returns
    -------
    headers: dict
        The headers.
    """
    if API_PARAMETERS["headers"] is not None:
        return API_PARAMETERS["headers"]

    if _on_runner():
        return _get_runner_headers()

    logging.warning(
        "No API headers available. Set them with "
        "`halerium_utilities.utils.api_config.update_api_parameters`.")
    return {}
