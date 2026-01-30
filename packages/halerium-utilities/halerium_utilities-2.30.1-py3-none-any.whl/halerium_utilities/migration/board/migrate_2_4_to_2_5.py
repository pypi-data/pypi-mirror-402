from copy import deepcopy
import uuid


def _find_node_by_id(board_dict, node_id):
    for node in board_dict.get("nodes", []):
        if node.get("id", None) == node_id:
            return node
    return None


def _append_bot_node(board, node_id, chat_text):
    """
    Append a bot node to the board and link it to the given node_id.

    Parameters
    ----------
    board
    node_id
    chat_text

    Returns
    -------
    new_node_id
    """
    old_node = _find_node_by_id(board, node_id)
    old_position = old_node.get("position", {"x": 0, "y": 0})
    new_position = {**old_position}
    new_position["x"] += old_node.get("size", {}).get("width", 520) + 100

    new_bot_node = {
        "id": str(uuid.uuid4()),
        "type": "bot",
        "position": new_position,
        "size": {"width": 520, "height": 320},
        "type_specific": {
            "prompt_input": chat_text,
            "prompt_output": "",
            "auto_size": True,
            "split_size": [16.73, 83.27],
            "state": "initial",
            "attachments": {}
        }
    }
    board["nodes"].append(new_bot_node)
    new_edge = {
        "id": str(uuid.uuid4()),
        "type": "prompt_line",
        "connections": {
            "source": {
                "id": node_id,
                "connector": "prompt-output"
            },
            "target": {
                "id": new_bot_node["id"],
                "connector": "prompt-input"
            }
        },
    }
    board["edges"].append(new_edge)

    return new_bot_node["id"]


def _create_setup_node(board):
    new_setup_node = {
        "id": str(uuid.uuid4()),
        "type": "setup",
        "position": {"x": 0, "y": 0},
        "size": {"width": 340, "height": 320},
        "type_specific": {
            "bot_type": "chat-gpt-41",
            "setup_args": {"system_setup": ""},
            "auto_size": True
        }
    }
    board["nodes"].append(new_setup_node)
    return new_setup_node["id"]


def migrate_board(board_dict):

    # 1. check version before starting migration
    if board_dict.get("version", None) != "2.4":
        raise Exception("Input board has wrong version.")

    migrated_board = deepcopy(board_dict)
    migrated_board["version"] = "2.5"

    if not migrated_board["workflows"]:
        # no migration needed
        return migrated_board

    # no need to migrate hidden workflows
    workflow = migrated_board["workflows"][0]

    link_id = None  # if one of the conditions below sets this, we create a new bot element

    # if workflow has a linked nodeId create a suitable bot link and card
    if workflow.get("linkedNodeId", None) and _find_node_by_id(migrated_board, workflow["linkedNodeId"]):
        node = _find_node_by_id(migrated_board, workflow["linkedNodeId"])
        chat_text = workflow.get("chatText", "")
        if node["type"] in ("bot", "setup"):
            link_id = _append_bot_node(migrated_board, node["id"], chat_text)

    # if the chat helper contains text but no linkedNodeId, create a setup node first
    elif workflow.get("chatText", "").strip():
        # if workflow has chatText but no linkedNodeId, create a new bot node and link to it
        chat_text = workflow.get("chatText", "")
        setup_id = _create_setup_node(migrated_board)
        link_id = _append_bot_node(migrated_board, setup_id, chat_text)

    # if the workflow is empty create a setup node and link to it
    elif not workflow.get("linearTasks", []):
        setup_id = _create_setup_node(migrated_board)
        link_id = _append_bot_node(migrated_board, setup_id, "")

    # If the path is not empty and the chat helper has no link or input, do nothing
    else:
        link_id = None

    if link_id:
        new_bot_element = {
            "id": str(uuid.uuid4()),
            "type": "bot",
            "type_specific": {
                "prompt_input": "",
                "prompt_output": "",
                "attachments": {},
                "linkedNodeId": link_id
            }
        }
        workflow["linearTasks"].append(new_bot_element)

    # now remove the obsolete fields
    for workflow in migrated_board["workflows"]:
        if "chatText" in workflow:
            del workflow["chatText"]
        if "linkedNodeId" in workflow:
            del workflow["linkedNodeId"]

    return migrated_board
