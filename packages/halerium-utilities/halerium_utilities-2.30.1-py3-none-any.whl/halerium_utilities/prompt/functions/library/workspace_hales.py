# --------------------------------------------------- #
#
# Ticket: https://erium.atlassian.net/browse/HAL-5156
#
# --------------------------------------------------- #

from halerium_utilities.hal_es import (
    HalE,
    get_workspace_hales_async,
    create_workspace_hale_async,
)
from halerium_utilities.hal_es.hal_e_session import HalESession
from halerium_utilities.hal_es.schemas import SessionData

from halerium_utilities.board import Board
from halerium_utilities.board.navigator import BoardNavigator
from halerium_utilities.board.schemas import Node

from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any, Literal

# --------------------------------------------------- #
#
# helper functions
#
# --------------------------------------------------- #


def _cleanup_template_board(board: Board) -> Board:
    """
    Clean up a board template by removing all outputs from bot cards.

    Args:
        board (Board): The board to clean up.

    Returns:
        Board: The cleaned-up board.
    """
    navigator = BoardNavigator(board=board)

    for cid in navigator.cards:
        card_type = navigator.get_card_type(cid)
        if card_type == "bot":
            # delete prompt output
            bot_node: Node = board.get_card_by_id(cid)
            bot_node.type_specific.prompt_output = ""
        elif card_type == "note":
            # check if linked to output of bot card
            note_connections = board.get_all_connections_of_card(cid)
            for conn in note_connections:
                source_card_type = navigator.get_card_type(conn.connections.source.id)
                if source_card_type == "bot":
                    # remove contents of note
                    note_node: Node = board.get_card_by_id(cid)
                    note_node.type_specific.message = ""
                    # note_node.type_specific.title = "" # keep title

    return board


# --------------------------------------------------- #
#
# READ methods
#
# --------------------------------------------------- #


async def get_workspace_hales() -> Dict[str, Any]:
    """
    Get workspace Hales information.

    Returns:
        Dict[str, Any]: A dictionary containing information about all Hales in the workspace.
    """
    all_hales: List[HalE] = await get_workspace_hales_async()
    response_dict = {}
    for hale in all_hales:
        response_dict[hale.name] = {
            "name": hale.name,
            "description": hale.description,
            "url": hale.init_url,
        }
    return response_dict


async def get_hale_sessions(
    hale_name: str = None,
    min_date: str = None,
    max_date: str = None,
    user: str = None,
) -> Dict[str, Any]:
    """
    Get sessions for a specific Hal-E in the workspace.

    Args:
        hale_name (str, optional): The name of the Hal-E. Defaults to None.
        min_date (str, optional): Minimum date filter for sessions. Defaults to None.
        max_date (str, optional): Maximum date filter for sessions. Defaults to None.
        user (str, optional): User filter for sessions. Defaults to None.

    Returns:
        Dict[str, Any]: A dictionary containing session information for the specified Hale.
    """
    all_hales: List[HalE] = await get_workspace_hales_async()

    all_sessions = []
    for hale in all_hales:
        sessions: List[SessionData] = await hale.get_session_data_async()
        for session in sessions:
            all_sessions.append(
                {
                    "hale_name": hale.name,
                    "session_id": session.session_id,
                    "session_name": session.session_name,
                    # "session_path": session.session_path,
                    "user": session.create_username,
                    "created_at": session.created_at,
                    "created_by": session.create_username,
                }
            )

    # apply filters
    if hale_name is not None:
        all_sessions = [
            session for session in all_sessions if session["hale_name"] == hale_name
        ]
    if min_date is not None:
        # cast to datetime
        min_date = datetime.fromisoformat(min_date).replace(tzinfo=timezone.utc)

        all_sessions = [
            session for session in all_sessions if session["created_at"] >= min_date
        ]
    if max_date is not None:
        max_date = datetime.fromisoformat(max_date).replace(tzinfo=timezone.utc)
        all_sessions = [
            session for session in all_sessions if session["created_at"] <= max_date
        ]
    if user is not None:
        all_sessions = [session for session in all_sessions if session["user"] == user]

    return {"sessions": all_sessions}


# --------------------------------------------------- #
#
# UPDATE methods
#
# --------------------------------------------------- #


async def update_hale_session_name(
    hale_name: str, session_id: str, new_name: str
) -> Dict[str, Any]:
    """
    Rename a specific session for a Hal-E.

    Args:
        hale_name (str): The name of the Hale.
        session_id (str): The ID of the session to rename.
        new_name (str): The new name for the session.

    Returns:
        Dict[str, Any]: A dictionary indicating the success of the operation.
    """
    all_hales: List[HalE] = await get_workspace_hales_async()
    target_hale: HalE = next(
        (hale for hale in all_hales if hale.name == hale_name), None
    )

    target_session_data: SessionData = None
    if target_hale is not None:
        sessions: List[SessionData] = await target_hale.get_session_data_async()
        target_session_data = next(
            (session for session in sessions if session.session_id == session_id), None
        )

    if target_hale is None or target_session_data is None:
        return {"success": False, "message": "Hale or session not found."}

    target_session = HalESession(hale=target_hale, session_data=target_session_data)

    try:
        await target_session.rename_async(name=new_name)
    except Exception as e:
        return {"success": False, "message": f"Failed to rename session: {str(e)}"}

    return {"success": True, "message": "Session renamed successfully."}


# --------------------------------------------------- #
#
# CREATE methods
#
# --------------------------------------------------- #


async def create_hale_from_template(
    board_path: str,
    hale_name: str,
    description: str = "",
    access: Literal[
        "workspace", "company-user-groups", "company", "public"
    ] = "workspace",
    log_sessions: bool = True,
    log_path: str = None,
) -> Dict[str, Any]:
    """
    Create a new Hal-E from a given board template.

    Args:
        board_path (str): The path to the board template.
        hale_name (str): The name of the new Hal-E.
        description (str, optional): A description for the new Hal-E. Defaults to "".
        access (Literal["workspace", "company-user-groups", "company", "public"], optional): The access level for the new Hal-E. Defaults to "workspace".
        log_sessions (bool, optional): Whether to log sessions. Defaults to True.
        log_path (str, optional): The path for logging. Defaults to None.

    Returns:
        Dict[str, Any]: A dictionary containing information about the created Hal-E.
    """
    if not Path(board_path).exists():
        if not Path.home().joinpath(board_path).exists():
            return {"success": False, "message": "Board template path does not exist."}
        else:
            board_path = str(Path.home().joinpath(board_path))

    if not Path(board_path).suffix == ".board":
        return {"success": False, "message": "Invalid board template file."}

    board = Board.from_json(board_path)
    board = _cleanup_template_board(board=board)

    new_hale: HalE = await create_workspace_hale_async(
        name=hale_name,
        description=description,
        board=board,
        access=access,
        log_sessions=log_sessions,
        log_path=log_path,
    )

    return {
        "success": True,
        "hale_name": new_hale.name,
        "hale_description": new_hale.description,
        "hale_url": new_hale.init_url,
    }


#! Todo: update EXISTING hale.
