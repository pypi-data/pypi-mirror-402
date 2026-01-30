# --------------------------------------------------- #
#
# Ticket: https://erium.atlassian.net/browse/HAL-5158
#
# --------------------------------------------------- #
import os
from typing import Optional

from halerium_utilities.bundles.installation import (
    install_bundle_async,
    precheck_bundle_installation_async,
    # create_conflict_handling_from_check,
    StoreBundleError,
    BundleInstallationError,
)

from halerium_utilities.bundles.schemas import StoreBundle
from halerium_utilities.bundles.browsing import (
    get_published_bundles_async,
    get_published_bundle_async,
)


async def halerium_store_list_bundles() -> list:
    """
    Lists all available bundles in the halerium store.

    Returns:
        list: List of StoreBundle objects available in the store
    """
    try:
        bundles = await get_published_bundles_async()
        return bundles
    except StoreBundleError as e:
        return str(e)


async def halerium_store_search(
        name: Optional[str] = None,
        description: Optional[str] = None,
        publisher_name: Optional[str] = None,
        access_scope: Optional[str] = None,
        has_hales: Optional[bool] = None,
        has_capabilities: Optional[bool] = None,
        has_infostores: Optional[bool] = None,
        has_files: Optional[bool] = None,
) -> list:
    """
    Enables searching the halerium store with various filter arguments.

    Args:
        name (str, optional): name of the bundle (for "is in" match)
        description (str, optional): description of the bundle (for "is in" match)
        publisher_name (str, optional): name of the publisher (for "is in" match)
        access_scope (str, optional): scope of the bundle (for exact match).
            Allowed values are "public", "tenant", "user_and_usergroup"
        has_hales (bool, optional): whether the bundle has a hales
        has_capabilities (bool, optional): whether the bundle has a capability groups
        has_infostores (bool, optional): whether the bundle has information stores
        has_files (bool, optional): whether the bundle has files

    Returns:
        list: List of StoreBundle objects matching the search criteria
    """
    try:
        results = await get_published_bundles_async()
        if name:
            results = [bundle for bundle in results if name.lower() in bundle.name.lower()]
        if description:
            results = [bundle for bundle in results if description.lower() in bundle.description.lower()]
        if publisher_name:
            results = [bundle for bundle in results if publisher_name.lower() in bundle.publisher.name.lower()]
        if access_scope:
            results = [bundle for bundle in results if access_scope.lower() == bundle.access_scope.lower()]
        if has_hales is not None:
            results = [bundle for bundle in results if has_hales == bool(bundle.contents.hales)]
        if has_capabilities is not None:
            results = [bundle for bundle in results if has_capabilities == bool(bundle.contents.capabilities)]
        if has_infostores is not None:
            results = [bundle for bundle in results if has_infostores == bool(bundle.contents.infostores)]
        if has_files is not None:
            results = [bundle for bundle in results if has_files == bool(bundle.contents.files)]
        return results
    except StoreBundleError as e:
        return str(e)


async def install_bundle(bundle_id: str) -> str:
    """
    Installs the bundle at the given bundle id

    Args:
        bundle_id (str): bundle ID

    Returns:
        str: Result message indicating success or failure
    """
    try:
        installation_precheck = await precheck_bundle_installation_async(bundle_id)
    except StoreBundleError as e:
        return str(e)

    # If there are conflicts, show them to the user
    if installation_precheck.conflicts:
        # generate sharing link for that bundle:
        bundle_sharing_link = await halerium_store_get_bundle_sharing_link(bundle_id)
        return f"Bundle with id {bundle_id} cannot be installed due to conflicts: {installation_precheck.conflicts}. Please have the user review and resolve the conflicts at {bundle_sharing_link}."

    # not really needed, but for the sake of completeness
    # conflict_handling = create_conflict_handling_from_check(installation_precheck)
    try:
        installation_check = await install_bundle_async(bundle_id=bundle_id)
        return (
            f"Bundle with id {bundle_id} installed successfully: {installation_check}"
        )
    except (StoreBundleError, BundleInstallationError) as e:
        return str(e)


async def get_bundle_link(bundle_id: str) -> str:
    """
    Builds the sharing link for a halerium bundle

    Args:
        bundle_id (str): bundle ID

    Returns:
        str: Sharing link URL
    """
    # get the bundle
    tenant = os.getenv("HALERIUM_TENANT_KEY", "")
    bundle_info: StoreBundle = await get_published_bundle_async(bundle_id)
    scope = "public" if bundle_info.access_scope == "public" else tenant
    base_url = os.getenv("HALERIUM_BASE_URL", "https://pro.halerium.ai")

    return f"{base_url}/{scope}/store/{bundle_id}"
