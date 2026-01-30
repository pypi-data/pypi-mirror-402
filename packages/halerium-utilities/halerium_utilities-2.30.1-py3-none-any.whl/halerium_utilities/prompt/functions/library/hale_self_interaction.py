# --------------------------------------------------- #
#
# Ticket: https://erium.atlassian.net/browse/HAL-5155
#
# --------------------------------------------------- #

import json
from pathlib import Path

from halerium_utilities.hal_es import HalE, HalESession, get_workspace_hales_async
from halerium_utilities.hal_es.schemas.session_data import SessionData

from halerium_utilities.stores import (
    get_information_store_by_name_async,
    create_information_store_async,
)
from halerium_utilities.stores.api import get_workspace_information_stores_async
from halerium_utilities.prompt.capabilities.capabilities import (
    get_capability_groups_async,
    get_capability_group_async,
    _get_capability_id_by_name_async,
)


from halerium_utilities.collab import CollabBoard

# --------------------------------------------------- #
#
# helper functions
#
# --------------------------------------------------- #


async def _get_own_session_data(__halerium_card) -> SessionData:
    all_hales = await get_workspace_hales_async()
    for hale in all_hales:
        sessions = await hale.get_session_data_async()
        for sess in sessions:
            if sess.session_path.lstrip("/") == __halerium_card["path"].lstrip("/"):
                return sess


async def _build_session_url(session: SessionData) -> dict:
    hale = HalE.from_name(session.hale_name)
    init_url = hale.init_url
    session_url = init_url.rstrip("/") + "/" + session.session_id
    return {
        "init_url": init_url,
        "session_url": session_url,
    }


async def _get_hale_session_board(__halerium_card) -> CollabBoard:
    session_data: SessionData = await _get_own_session_data(__halerium_card)
    if session_data is None:
        raise ValueError("No session found.")

    hale = HalE.from_name(session_data.hale_name)
    hal_e_session = HalESession(hale=hale, session_data=session_data)
    return hal_e_session.board


# --------------------------------------------------- #
#
# session and hale data functions
#
# --------------------------------------------------- #

# --------------------------------------------------- #
# I've decided to aggregate of the Hal-E data once.
# That way, the bot only calls this function once
# per interaction, and then just reuses the data
# instead of calling the function multiple times.
# Pro:
# - Fewer API calls -> faster responses
# - Potentially less token usage
# Con:
# - Changes in the session data during the interaction
#   are not reflected
# --------------------------------------------------- #


async def get_own_session_data(__halerium_card) -> dict:
    """
    Fetches the current Hal-E's session data. This includes:
    - Hal-E Name
    - Hal-E URL
    - Session ID
    - Session Name
    - Session URL
    - Created At
    - Creator Username
    - Session Path

    Args:
        __halerium_card (dict): Injected at runtime.
    Returns:
        dict: The session data of the current Hal-E.
    """
    session_data: SessionData = await _get_own_session_data(__halerium_card)
    if session_data is None:
        return "No session found."
    hale_urls = await _build_session_url(session_data)

    return_dict = {
        "created_at": session_data.created_at,
        "create_username": session_data.create_username,
        "hale_name": session_data.hale_name,
        "hale_url": hale_urls.get("init_url", ""),
        "session_id": session_data.session_id,
        "session_name": session_data.session_name,
        "session_path": session_data.session_path,
        "session_url": hale_urls.get("session_url", ""),
    }

    return return_dict


async def get_own_hale_data(__halerium_card) -> dict:
    """
    Fetches a Hal-E's Name, Description, Access Type, Logs Path, Templat Board Path.

    Args:
        __halerium_card (dict): Injected at runtime.

    Returns:
        dict: Information about the Hal-E
    """
    session_data: SessionData = await _get_own_session_data(__halerium_card)
    if session_data is None:
        return "No session found."
    hale = HalE.from_name(session_data.hale_name)

    return {
        "name": hale.name,
        "description": hale.description,
        # everything below here is not mentioned in the ticket,
        # but might be useful for the user:
        "access": hale.access,
        "logs_path": str(
            Path.home() / hale.log_path.lstrip("/")
        ),  # may want to get rid of the Path.home() part (can be confusing to the user )
        "template_board": str(
            Path.home() / hale.template_board.lstrip("/")
        ),  # may want to get rid of the Path.home() part (can be confusing to the user )
    }


async def update_own_session_name(new_name: str, __halerium_card) -> str:
    """
    Updates the name of the current Hal-E's session.

    Args:
        new_name (str): The new name for the session.
        __halerium_card (dict): Injected at runtime.
    Returns:
        str: Success or error message.
    """
    session_data: SessionData = await _get_own_session_data(__halerium_card)
    if session_data is None:
        return "No session found."

    hale = HalE.from_name(session_data.hale_name)
    hal_e_session = HalESession(hale=hale, session_data=session_data)

    try:
        await hal_e_session.rename_async(new_name)
        return f"Session name updated to '{new_name}'."
    except Exception as e:
        return f"Failed to update session name: {str(e)}"


# --------------------------------------------------- #
#
# session setup card functions
#
# --------------------------------------------------- #


async def get_setup(__halerium_card) -> dict:
    """
    Fetches the setup card of the current Hal-E's session.

    Args:
        __halerium_card (dict): Injected at runtime.
    Returns:
        dict: The setup card content or an error message.
    """
    session_data: SessionData = await _get_own_session_data(__halerium_card)
    if session_data is None:
        return "No session found."

    hale = HalE.from_name(session_data.hale_name)
    hal_e_session = HalESession(hale=hale, session_data=session_data)
    setup_card_id = __halerium_card.get("setup_id")
    setup_card = hal_e_session.board.get_card_by_id(setup_card_id)

    if not setup_card:
        return "Error: Setup card not found."

    return setup_card.dict()


async def update_setup_card(
    __halerium_card,
    bot_type: str = None,  # update the agent, can be "chat-gpt-41" (GPT-4.1), "chat-gpt-40-turbo" (GPT-4o), "chat-gpt-4o-mini" (GPT-4o-mini), "mistral-large" (Mistral Large)
    system_setup: str = None,  # update the system message of the bot
    default_functions: str = None,  #  updates the default_functions, can be '[]', '["image_generator"]', '["websearch"]', '["image_generator", "websearch"]'
    knows_user: bool = None,  #  whether the bot can see the users name and email
    knows_platform: bool = None,  # whether the bot knows about Halerium
    temperature: float = None,  # temperature between 0 and 1 in increments of 0.1
) -> dict:
    """
    Allows the user to update the setup card.

    Args:
        __halerium_card (dict): Injected at runtime.
        bot_type (str, optional): The type of bot to use. Defaults to None.
        system_setup (str, optional): The system setup message. Defaults to None.
        default_functions (str, optional): JSON string of default functions. Defaults to None.
        knows_user (bool, optional): Whether the bot knows the user. Defaults to None.
        knows_platform (bool, optional): Whether the bot knows the platform. Defaults to None.
        temperature (float, optional): The temperature setting for the bot. Defaults to None.

    Returns:
        dict: The updated setup card.
    """
    board = await _get_hale_session_board(__halerium_card)
    setup_card_id = __halerium_card.get("setup_id")

    type_specific = {}
    if bot_type:
        type_specific["bot_type"] = bot_type

    setup_args = board.get_card_by_id(setup_card_id).type_specific.setup_args
    type_specific["setup_args"] = setup_args

    if system_setup is not None:
        type_specific["setup_args"]["system_setup"] = str(system_setup)

    if default_functions is not None:
        default_functions = json.loads(default_functions)
        type_specific["setup_args"]["default_functions"] = default_functions

    if knows_user is not None:
        type_specific["setup_args"]["knows_user"] = bool(knows_user)
    if knows_platform is not None:
        type_specific["setup_args"]["knows_platform"] = bool(knows_platform)

    if temperature is not None:
        temperature = round(float(temperature), 1)
        if not (0 <= temperature <= 1):
            return f"Temperature must be between 0 and 1. Got {temperature}"
        type_specific["setup_args"]["temperature"] = temperature

    board.update_card(
        {"id": setup_card_id, "type": "setup", "type_specific": type_specific}
    )
    await board.push_async()
    return board.get_card_by_id(setup_card_id).dict()


async def get_information_stores() -> list:
    """
    Returns the workspace information stores

    Returns:
        list: List of available information stores.
    """
    response = await get_workspace_information_stores_async()
    return [r["name"] for r in response["items"]]


async def create_information_store(store_name: str) -> str:
    """
    Creates an information store with the given name.

    Args:
        store_name (str): Name of the information store.

    Returns:
        str: success or error message.
    """
    existing_stores = await get_information_stores()
    if store_name in existing_stores:
        return f"An information store with the name {store_name} already exists."

    await create_information_store_async(store_name)
    return f"Information Store {store_name} created."


async def remove_store(
    __halerium_card,
    store_name: str,
) -> str:
    """
    Removes an information store from the setup card.

    Args:
        __halerium_card (dict): Injected at runtime.
        store_name (str): Name of the store to be removed from the setup card.

    Returns:
        str: success message.
    """
    board = await _get_hale_session_board(__halerium_card)
    setup_card_id = __halerium_card.get("setup_id")

    store = await get_information_store_by_name_async(store_name)

    setup_card = board.get_card_by_id(setup_card_id)
    setup_args = setup_card.type_specific.setup_args

    store_uuids = setup_args.get("store_uuids", {})
    if store._store_id in store_uuids:
        store_uuids.pop(store._store_id)
    setup_args["store_uuids"] = store_uuids

    board.update_card(
        {"id": setup_card_id, "type_specific": {"setup_args": setup_args}}
    )
    await board.push_async()
    return "Information store removed"


async def add_store(
    __halerium_card,
    store_name: str,
    read=True,
    write=True,
    fullscan=False,
) -> str:
    """
    Adds an information store to the setup card.

    Args:
        __halerium_card (dict): Injected at runtime.
        store_name (str): Name of the store to be added to the setup card.
        read (bool, optional): Whether to grant read access. Defaults to True.
        write (bool, optional): Whether to grant write access. Defaults to True.
        fullscan (bool, optional): Whether to grant fullscan access. Defaults to False.

    Returns:
        str: success message.
    """
    board = await _get_hale_session_board(__halerium_card)
    setup_card_id = __halerium_card.get("setup_id")
    store = await get_information_store_by_name_async(store_name)
    setup_card = board.get_card_by_id(setup_card_id)
    setup_args = setup_card.type_specific.setup_args

    store_uuids = setup_args.get("store_uuids", {})
    entry = []
    if read:
        entry.append("read")
    if write:
        entry.append("write")
    if fullscan:
        entry.append("fullscan")
    store_uuids[store._store_id] = entry
    setup_args["store_uuids"] = store_uuids

    board.update_card(
        {"id": setup_card_id, "type_specific": {"setup_args": setup_args}}
    )
    await board.push_async()
    return "Information store added."


async def view_all_capability_groups() -> list | str:
    """
    Returns all available capability groups.

    Returns:
        list: List of capability groups or error message.
    """
    try:
        return await get_capability_groups_async()
    except Exception as exc:
        return f"Error fetching capability groups: {str(exc)}"


async def remove_capability_group(
    __halerium_card,
    capability_group: str,
) -> dict:
    """
    Removes a whole capability GROUP from the setup card.

    Args:
        __halerium_card (dict): Injected at runtime
        capability_group (str): Name of the capability group.

    Returns:
        dict: What functions were removed.
    """
    board = await _get_hale_session_board(__halerium_card)
    setup_card_id = __halerium_card.get("setup_id")

    if capability_group.startswith("_Global_"):
        capability_id = capability_group
    else:
        capability_id = await _get_capability_id_by_name_async(capability_group)

    setup_card = board.get_card_by_id(setup_card_id)
    setup_args = setup_card.type_specific.setup_args
    runner_functions = setup_args.get("runner_functions", [])

    removed_functions = []
    for i in range(len(runner_functions) - 1, -1, -1):
        runfunc = runner_functions[i]
        if runfunc["manifestId"] == capability_id:
            removed_functions.append(runner_functions.pop(i))
    setup_args["runner_functions"] = runner_functions

    board.update_card(
        {"id": setup_card_id, "type_specific": {"setup_args": setup_args}}
    )
    await board.push_async()
    return {"removed_functions": [f["function"]["name"] for f in removed_functions]}


async def remove_capability_function(
    __halerium_card,
    function_name: str,
) -> dict:
    """
    Removes a single capability FUNCTION from the setup card.

    Args:
        __halerium_card (dict): Injected at runtime
        function_name (str): Name of the function to be removed.

    Returns:
        dict: What functions were removed.
    """
    board = await _get_hale_session_board(__halerium_card)
    setup_card_id = __halerium_card.get("setup_id")

    setup_card = board.get_card_by_id(setup_card_id)
    setup_args = setup_card.type_specific.setup_args
    runner_functions = setup_args.get("runner_functions", [])

    removed_functions = []
    for i in range(len(runner_functions) - 1, -1, -1):
        runfunc = runner_functions[i]
        if runfunc["function"]["name"] == function_name:
            removed_functions.append(runner_functions.pop(i))
    setup_args["runner_functions"] = runner_functions

    board.update_card(
        {"id": setup_card_id, "type_specific": {"setup_args": setup_args}}
    )
    await board.push_async()
    return {"removed_functions": [f["function"]["name"] for f in removed_functions]}


async def add_capability_group(
    __halerium_card,
    capability_group: str,
    functions: str = None,
) -> dict:
    """
    Adds a whole capability GROUP to the setup card.

    Args:
        __halerium_card (dict): Injected at runtime.
        capability_group (str): Name of the capability group.
        functions (str, optional): JSON string of specific functions to add. Defaults to None (all functions).

    Returns:
        dict: What functions were added.
    """
    board = await _get_hale_session_board(__halerium_card)
    setup_card_id = __halerium_card.get("setup_id")

    capability = await get_capability_group_async(capability_group)
    if capability_group.startswith("_Global_"):
        capability_id = capability_group
    else:
        capability_id = await _get_capability_id_by_name_async(capability_group)

    setup_card = board.get_card_by_id(setup_card_id)
    setup_args = setup_card.type_specific.setup_args
    runner_functions = setup_args.get("runner_functions", [])

    if functions is None:
        functions = [f["function"] for f in capability["functions"]]
    else:
        functions = json.loads(functions)
    added_runner_functions = []
    for func in capability["functions"]:
        fname = func["function"]
        if fname not in functions:
            continue
        if fname == "code_interpreter":
            endpoint = "/execute_kernel_code"
        else:
            endpoint = f"/custom/{fname}"
        runfunc = {
            "endpoint": endpoint,
            "pretty_name": func["pretty_name"],
            "manifestId": capability_id,
            "function": {
                "name": fname,
                "description": func["description"],
                "parameters": {"type": "object", **func["parameters"]},
            },
        }
        added_runner_functions.append(runfunc)

    runner_functions.extend(added_runner_functions)
    setup_args["runner_functions"] = runner_functions

    board.update_card(
        {"id": setup_card_id, "type_specific": {"setup_args": setup_args}}
    )
    await board.push_async()
    return {"added_functions": [f["function"]["name"] for f in added_runner_functions]}
