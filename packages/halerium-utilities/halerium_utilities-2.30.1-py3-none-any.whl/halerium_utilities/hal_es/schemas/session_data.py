from datetime import datetime
from pydantic import BaseModel, ValidationError
from typing import Literal, Optional


class SessionData(BaseModel):

    hale_name: Optional[str] = None
    session_id: Optional[str] = None
    created_at: Optional[datetime] = None
    session_path: Optional[str] = None
    create_username: Optional[str] = None
    session_name: Optional[str] = None


def get_session_data_from_response_data(
        data: dict, variant: Literal["post", "get"]):
    """
    Create a SessionData object from a data dict.

    Parameters
    ----------
    data : dict
        The input data.
    variant : Literal["post", "get"]
        Whether the data come from the session creation post request
        or the session retrieval get request.

    Returns
    -------
    SessionData
        The SessionData object
    """
    if variant == "post":
        parsed_data = dict(
            hale_name=data.get("halETemplate", {}).get("name"),
            session_id=data.get("halESessionId"),
            created_at=data.get("sessionContent", {}).get("created_at"),
            session_path=data.get("sessionContent", {}).get("path"),
            create_username=None,
            session_name=None,
        )
    elif variant == "get":
        parsed_data = dict(
            hale_name=data.get("appName"),
            session_id=data.get("key"),
            created_at=data.get("createdAt"),
            session_path=data.get("halESessionPath"),
            create_username=data.get("username"),
            session_name=data.get("name"),
        )
    else:
        raise ValueError(f"Unsupported data variant '{variant}'")

    return SessionData.validate(parsed_data)
