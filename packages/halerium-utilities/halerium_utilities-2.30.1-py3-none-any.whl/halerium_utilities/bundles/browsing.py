import httpx

from halerium_utilities.utils.api_config import (
    get_api_headers, get_api_base_url)
from halerium_utilities.logging.exceptions import StoreBundleError

from .schemas import get_bundle_model_from_response_data


def _get_bundle_url():
    return get_api_base_url() + "/token-access/published-apps"


def _create_bundle_list(response_data):
    bundles = []
    for d in response_data:
        bundle = get_bundle_model_from_response_data(d, variant="short")
        bundles.append(bundle)

    return bundles


def get_published_bundles():
    """
    Returns a list of all bundles that can be installed from the store.

    Returns
    -------
    List[StoreBundle]
    """
    url = _get_bundle_url()
    with httpx.Client() as client:
        response = client.get(
            url=url,
            headers=get_api_headers()
        )
        response.raise_for_status()
    data = response.json()["data"]

    return _create_bundle_list(data)


async def get_published_bundles_async():
    """
    Returns a list of all bundles that can be installed from the store.

    Returns
    -------
    List[StoreBundle]
    """
    url = _get_bundle_url()
    async with httpx.AsyncClient() as client:
        response = await client.get(
            url=url,
            headers=get_api_headers()
        )
        response.raise_for_status()
    data = response.json()["data"]

    return _create_bundle_list(data)


def get_published_bundle(bundle_id: str):
    """
    Returns the details of a specific bundle from the store.

    Parameters
    ----------
    bundle_id : str
        The id of the bundle

    Returns
    -------
    StoreBundle
    """
    url = _get_bundle_url().rstrip("/") + f"/{bundle_id}"
    with httpx.Client() as client:
        response = client.get(
            url=url,
            headers=get_api_headers()
        )
        if response.status_code == 404:
            raise StoreBundleError(
                f"Bundle with id {bundle_id} was not found."
            )
        response.raise_for_status()
    data = response.json()["data"]
    return get_bundle_model_from_response_data(data, variant="long")


async def get_published_bundle_async(bundle_id: str):
    """
    Returns the details of a specific bundle from the store.

    Parameters
    ----------
    bundle_id : str
        The id of the bundle

    Returns
    -------
    StoreBundle
    """
    url = _get_bundle_url().rstrip("/") + f"/{bundle_id}"
    async with httpx.AsyncClient() as client:
        response = await client.get(
            url=url,
            headers=get_api_headers()
        )
        if response.status_code == 404:
            raise StoreBundleError(
                f"Bundle with id {bundle_id} was not found."
            )
        response.raise_for_status()
    data = response.json()["data"]
    return get_bundle_model_from_response_data(data, variant="long")
