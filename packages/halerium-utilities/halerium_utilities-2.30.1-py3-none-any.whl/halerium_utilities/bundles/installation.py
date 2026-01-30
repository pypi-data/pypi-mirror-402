import httpx
from typing import List, Literal

from halerium_utilities.utils.api_config import get_api_headers, get_api_base_url
from halerium_utilities.logging.exceptions import (
    BundleInstallationError,
    StoreBundleError,
)
from .schemas import (
    InstallationCheck,
    get_installation_check_model_from_response_data,
    ConflictHandling,
    conflict_handling_to_install_payload,
    InstalledBundle,
    get_installed_bundle_from_response_data,
)


def _get_bundle_url():
    return get_api_base_url() + "/token-access/published-apps"


def precheck_bundle_installation(bundle_id: str) -> InstallationCheck:
    """
    Prechecks the installation of a bundle by its ID.

    Parameters
    ----------
    bundle_id: str

    Returns
    -------
    InstallationCheck
    """
    url = _get_bundle_url().rstrip("/") + f"/{bundle_id}/validate-import"
    with httpx.Client() as client:
        response = client.get(url=url, headers=get_api_headers())
        if response.status_code == 404:
            raise StoreBundleError(f"Bundle with id {bundle_id} was not found.")
        response.raise_for_status()
    data = response.json()["data"]

    return get_installation_check_model_from_response_data(data)


async def precheck_bundle_installation_async(bundle_id: str):
    """
    Checks whether a bundle can be installed into the current workspace.
    The returned installation check contains any conflicts that need to be resolved.

    Parameters
    ----------
    bundle_id: str
        The bundle id.

    Returns
    -------
    InstallationCheck
    """
    url = _get_bundle_url().rstrip("/") + f"/{bundle_id}/validate-import"
    async with httpx.AsyncClient() as client:
        response = await client.get(url=url, headers=get_api_headers())
        if response.status_code == 404:
            raise StoreBundleError(f"Bundle with id {bundle_id} was not found.")
        response.raise_for_status()
    data = response.json()["data"]

    return get_installation_check_model_from_response_data(data)


def install_bundle(
    bundle_id: str, conflict_handling: ConflictHandling = None
) -> InstallationCheck:
    """
    Installs a bundle by its ID, with optional conflict handling.
    The conflict handling can be constructed with the help
    of the installation check returned by precheck_bundle_installation
    and the create_conflict_handling_from_check function.

    Parameters
    ----------
    bundle_id
    conflict_handling

    Returns
    -------
    InstallationCheck
    """
    if conflict_handling:
        conflict_actions = ConflictHandling.validate(conflict_handling)
        payload = conflict_handling_to_install_payload(conflict_actions)
    else:
        payload = None
    url = _get_bundle_url().rstrip("/") + f"/{bundle_id}/import"
    with httpx.Client() as client:
        response = client.post(
            url=url,
            headers=get_api_headers(),
            json=payload,
        )
        if response.status_code == 409:
            raise BundleInstallationError(
                "Unhandled conflicts prevent installation."
                "\nConsider using the precheck_bundle_installation and "
                "create_conflict_handling_from_check functions."
            )
        elif response.status_code == 404:
            raise StoreBundleError(f"Bundle with id {bundle_id} was not found.")
        response.raise_for_status()
    data = response.json()["data"]

    return get_installation_check_model_from_response_data(data)


async def install_bundle_async(
    bundle_id: str, conflict_handling: ConflictHandling = None
) -> InstallationCheck:
    """
    Installs a bundle by its ID, with optional conflict handling.
    The conflict handling can eb constructed with the help
    of the installation check returned by precheck_bundle_installation
    and the create_conflict_handling_from_check function.

    Parameters
    ----------
    bundle_id
    conflict_handling : ConflictHandling, optional

    Returns
    -------
    InstallationCheck
    """
    if conflict_handling:
        conflict_actions = ConflictHandling.validate(conflict_handling)
        payload = conflict_handling_to_install_payload(conflict_actions)
    else:
        payload = None
    url = _get_bundle_url().rstrip("/") + f"/{bundle_id}/import"
    async with httpx.AsyncClient() as client:
        response = await client.post(
            url=url,
            headers=get_api_headers(),
            json=payload,
        )
        if response.status_code == 409:
            raise BundleInstallationError(
                "Unhandled conflicts prevent installation."
                "\nConsider using the precheck_bundle_installation and "
                "create_conflict_handling_from_check functions."
            )
        elif response.status_code == 404:
            raise StoreBundleError(f"Bundle with id {bundle_id} was not found.")
        response.raise_for_status()
    data = response.json()["data"]

    return get_installation_check_model_from_response_data(data)


def create_conflict_handling_from_check(
    installation_check, default: Literal["skip", "replace"] = "skip"
) -> ConflictHandling:
    """
    Creates a ConflictHandling model from an InstallationCheck model,
    applying the same default action to all conflicts.

    Parameters
    ----------
    installation_check : InstallationCheck
    default : Literal["skip", "replace"], optional

    Returns
    -------
    ConflictHandling
    """
    installation_check = InstallationCheck.validate(installation_check)
    conflicts = installation_check.conflicts
    if not conflicts:
        return ConflictHandling()

    handling_dict = {}
    for key, value in conflicts.dict().items():
        handling_dict[key] = {}
        for item in value:
            handling_dict[key][item] = default

    return ConflictHandling.validate(handling_dict)


def get_installed_bundles() -> List[InstalledBundle]:
    """
    Returns the list of installed bundles in the current workspace.

    Returns
    -------
    List[InstalledBundle]
    """
    url = get_api_base_url() + "/token-access/installed-apps"
    with httpx.Client() as client:
        response = client.get(url=url, headers=get_api_headers())
        response.raise_for_status()
    data = response.json()["data"]
    installed_bundles = []
    for entry in data:
        installed_bundles.append(get_installed_bundle_from_response_data(entry))

    return installed_bundles


async def get_installed_bundles_async() -> List[InstalledBundle]:
    """
    Returns the list of installed bundles in the current workspace.

    Returns
    -------
    List[InstalledBundle]
    """
    url = get_api_base_url() + "/token-access/installed-apps"
    async with httpx.AsyncClient() as client:
        response = await client.get(url=url, headers=get_api_headers())
        response.raise_for_status()
    data = response.json()["data"]
    installed_bundles = []
    for entry in data:
        installed_bundles.append(get_installed_bundle_from_response_data(entry))

    return installed_bundles
