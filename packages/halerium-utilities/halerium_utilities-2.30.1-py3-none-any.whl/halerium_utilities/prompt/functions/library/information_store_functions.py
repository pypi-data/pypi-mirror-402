# --------------------------------------------------- #
#
# Ticket: https://erium.atlassian.net/browse/HAL-5157
#
# --------------------------------------------------- #

from halerium_utilities.stores.api import (
    get_workspace_information_stores_async,
    InformationStoreException,
)

from halerium_utilities.stores import (
    get_information_store_by_name_async,
    create_information_store_async,
    delete_information_store_async,
)


async def get_information_stores():
    """
    Get all information stores in the current workspace.

    Returns:
        List of information stores.
    """
    return await get_workspace_information_stores_async()


async def get_information_store_by_name(name: str):
    """
    Get an information store by name.

    Args:
        name: The name of the information store.

    Returns:
        The information store object.
    """
    return await get_information_store_by_name_async(name)


async def create_information_store(name: str):
    """
    Create a new information store.

    Args:
        name: The name of the information store.
        description: The description of the information store.

    Returns:
        A message indicating the result of the creation.
    """
    try:
        await create_information_store_async(name)
    except InformationStoreException:
        return f"Information Store with name {name} already exists."
    else:
        return f"Information Store with name {name} created successfully."


async def delete_information_store(name: str):
    """
    Delete an information store by name.

    Args:
        name: The name of the information store.

    Returns:
        A message indicating the result of the deletion.
    """
    try:
        # get infostore id from name
        info_store = await get_information_store_by_name_async(name)
        if not info_store:
            raise InformationStoreException()

        info_store_id = info_store.store_id

        await delete_information_store_async(info_store_id)
    except InformationStoreException:
        return f"Information Store with name {name} could not be deleted. Does it exist?"
    else:
        return f"Information Store with name {name} deleted successfully."
