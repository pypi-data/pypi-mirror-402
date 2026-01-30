import asyncio
import httpx
import os
import time

from typing import List, Literal, Optional
from urllib.parse import quote

from halerium_utilities.board import Board
from halerium_utilities.hal_es.schemas import (
    HalEData, HalEPayload, get_session_data_from_response_data)
from halerium_utilities.utils.api_config import get_api_headers, get_api_base_url
from halerium_utilities.utils.workspace_paths import runner_path_to_workspace_path


def _get_endpoint():
    return f"{get_api_base_url()}/token-access/hal-es"


def get_workspace_hales() -> List["HalE"]:
    """
    Fetches HalE instances for the workspace and converts the data into HalE objects.

    Returns
    -------
    List[HalE]
        A list of HalE instances representing available boards in the workspace.
    """
    raw_data = _get_workspace_hale_data()
    hales = []

    for hale_data in raw_data.get('data', []):
        hale_instance = _create_hale_from_data(hale_data)
        if hale_instance:
            hales.append(hale_instance)
        else:
            print(f"Failed to create HalE instance for: {hale_data}")

    return hales


async def get_workspace_hales_async() -> List["HalE"]:
    """
    Fetches available HalE instances in the workspace asynchronously.

    Returns
    -------
    List[HalE]
        A list of HalE instances representing available HalE boards in the workspace.
    """
    raw_data = await _get_workspace_hale_data_async()
    hales = []

    for hale_data in raw_data.get('data', []):
        hale_instance = _create_hale_from_data(hale_data)
        if hale_instance:
            hales.append(hale_instance)
        else:
            print(f"Failed to create HalE instance for: {hale_data}")

    return hales


def _get_workspace_hale_data() -> List[dict]:
    """
    Fetches raw data of available HalEs in the workspace.

    Returns
    -------
    List[dict]
        A list of dictionaries representing available HalE boards in the workspace.
    """
    endpoint = _get_endpoint()
    with httpx.Client() as client:
        response = client.get(
            endpoint,
            headers=get_api_headers()
        )
        response.raise_for_status()
        return response.json()


async def _get_workspace_hale_data_async() -> List[dict]:
    """
    Fetches raw data of available HalEs in the workspace asynchronously.

    Returns
    -------
    List[dict]
        A list of dictionaries representing available HalE boards in the workspace.
    """
    endpoint = _get_endpoint()
    async with httpx.AsyncClient() as client:
        response = await client.get(
            endpoint,
            headers=get_api_headers()
        )
        response.raise_for_status()
        return response.json()


def _get_hale_data_by_name(hale_name: str):
    hale_datas = _get_workspace_hale_data()
    hale_name = hale_name.lower()
    for hale_data in hale_datas.get("data", []):
        remote_name = hale_data.get("appConfig", {}).get("name")
        if remote_name and remote_name.lower() == hale_name:
            return hale_data
    raise ValueError(f"Could not find a Hal-E named '{hale_name}'.")


async def _get_hale_data_by_name_async(hale_name: str):
    hale_datas = await _get_workspace_hale_data_async()
    hale_name = hale_name.lower()
    for hale_data in hale_datas.get("data", []):
        remote_name = hale_data.get("appConfig", {}).get("name")
        if remote_name and remote_name.lower() == hale_name:
            return hale_data
    raise ValueError(f"Could not find a Hal-E named '{hale_name}'.")


def _is_hale_name_occupied(hale_name):
    try:
        _get_hale_data_by_name(hale_name)
        return True
    except ValueError:
        return False


async def _is_hale_name_occupied_async(hale_name):
    try:
        await _get_hale_data_by_name_async(hale_name)
        return True
    except ValueError:
        return False


def _get_temp_boardfile():
    # save board to temp file
    basename = ".board_template"
    fname = basename + ".board"
    counter = 0
    while os.path.exists(fname):
        counter += 1
        fname = basename + f"_{counter}.board"
    return fname


def _cleanup_temp_boardfile(fname):
    if os.path.exists(fname):
        os.unlink(fname)


def _create_workspace_hale_prep(
        fname: str,
        name: str,
        description: str = None,
        board: Board = None,
        access: Literal["workspace", "company-user-groups", "company", "public"] = None,
        log_sessions: bool = True,
        log_path: str = None
):
    if board:
        board = Board(board)
    else:
        board = Board()
    log_sessions = bool(log_sessions)
    if log_sessions:
        if log_path:
            workspace_log_path = runner_path_to_workspace_path(log_path)
        else:
            workspace_log_path = f"/{name}"
    else:
        workspace_log_path = None
    if not access:
        access = "workspace"
    description = str(description) if description else ""

    board.to_json(fname)

    template_board_workspace_path = runner_path_to_workspace_path(fname)
    payload = HalEPayload.validate({
        "appConfig": {
            "appType": "hal-e",
            "name": name,
            "description": description,
            "accessType": access,
            "appParams": {
                "sourcePath": template_board_workspace_path,
                "config": {
                    "sessions": {
                        "path": workspace_log_path,
                        "persistSession": log_sessions
                    }
                }
            }
        }
    })
    return payload


def create_workspace_hale(
        name: str,
        description: str = "",
        board: Board = None,
        access: Literal["workspace", "company-user-groups", "company", "public"] = "workspace",
        log_sessions: bool = True,
        log_path: str = None,
) -> "HalE":
    if _is_hale_name_occupied(name):
        raise ValueError(f"Hal-E name {name} is already taken.")

    fname = _get_temp_boardfile()
    try:
        payload = _create_workspace_hale_prep(
            fname=fname, name=name, description=description, board=board,
            access=access, log_sessions=log_sessions, log_path=log_path)

        time.sleep(1)  # wait 1 second to allow the file to propagate through efs

        endpoint = _get_endpoint()
        with httpx.Client() as client:
            response = client.post(
                endpoint,
                headers=get_api_headers(),
                json=payload.dict()
            )
            response.raise_for_status()
            hale_data = response.json()["data"]
        return _create_hale_from_data(hale_data)
    finally:
        _cleanup_temp_boardfile(fname)


async def create_workspace_hale_async(
        name: str,
        description: str = "",
        board: Board = None,
        access: Literal["workspace", "company-user-groups", "company", "public"] = "workspace",
        log_sessions: bool = True,
        log_path: str = None,
) -> "HalE":
    if await _is_hale_name_occupied_async(name):
        raise ValueError(f"Hal-E name {name} is already taken.")

    fname = _get_temp_boardfile()
    try:
        payload = _create_workspace_hale_prep(
            fname=fname, name=name, description=description, board=board,
            access=access, log_sessions=log_sessions, log_path=log_path)

        await asyncio.sleep(1)  # wait 1 second to allow the file to propagate through efs

        endpoint = _get_endpoint()
        async with httpx.AsyncClient() as client:
            response = await client.post(
                endpoint,
                headers=get_api_headers(),
                json=payload.dict()
            )
            response.raise_for_status()
            hale_data = response.json()["data"]
        return _create_hale_from_data(hale_data)
    finally:
        _cleanup_temp_boardfile(fname)


def _create_hale_from_data(hale_data: dict) -> Optional["HalE"]:
    """
    Creates a HalE instance from a hale_data.

    Parameters
    ----------
    hale_data : dict
        A dictionary containing the necessary keys to instantiate a HalE object.

    Returns
    -------
    HalE
        A HalE instance
    """
    hale_data_model = HalEData.validate(hale_data)
    return HalE(hale_data_model)


class HalE:
    """
    Represents a HalE instance within a workspace.
    """

    def __init__(self, hale_data: HalEData):
        """
        Initializes a HalE instance with the provided details.

        Parameters
        ----------
        hale_data : HalEData or dict
        """
        self.name = None
        self.description = None
        self.access = None
        self.log_sessions = None
        self.log_path = None

        self.init_url = None
        self.template_board = None

        self._set_params(hale_data)
        self._assets = Assets(self)

    def _set_params(self, hale_data):
        hale_data = HalEData.validate(hale_data)
        app_config = hale_data.appConfig

        self.name = app_config.name
        self.description = app_config.description
        self.access = app_config.accessType
        self.log_sessions = app_config.appParams.config.sessions.persistSession
        self.log_path = app_config.appParams.config.sessions.path

        self.init_url = hale_data.friendlyUrl
        self.template_board = app_config.appParams.sourcePath

    @property
    def assets(self):
        """
        The assets property bundles more methods that modify the
        Hal-E's description and logo.

        Returns
        -------
        Assets
            An instance of :class:`Assets` for managing logos and descriptions.
        """
        return self._assets

    def _del_params(self):
        self.name = None
        self.description = None
        self.access = None
        self.log_sessions = None
        self.log_path = None

        self.init_url = None
        self.template_board = None

    @property
    def data(self):
        """
        The data of the Hal-E instance

        Returns
        -------
        dict
        """
        return dict(
            name=self.name,
            description=self.description,
            access=self.access,
            log_sessions=self.log_sessions,
            log_path=self.log_path,
            init_url=self.init_url,
            template_board=self.template_board
        )

    @classmethod
    def from_name(cls, hale_name: str) -> "HalE":
        """
        Instanciates the HalE class from a Hal-E name.

        Parameters
        ----------
        hale_name

        Returns
        -------
        HalE
        """
        hale_data = _get_hale_data_by_name(hale_name)
        return _create_hale_from_data(hale_data)

    def get_instance(self) -> Optional["HalESession"]:
        """
        Creates and returns a new HalESession instance for this HalE.

        Returns
        -------
        HalESession
            Returns a HalESession instance.
        """
        from halerium_utilities.hal_es import HalESession

        return HalESession(self)

    def __repr__(self):
        return (f"HalE(name='{self.name}', access='{self.access}', "
                f"template_board='{self.template_board}', init_url='{self.init_url}')")

    def _get_update_endpoint(self):
        endpoint = _get_endpoint()
        endpoint = endpoint.rstrip("/") + f"/{quote(self.name)}"
        return endpoint

    @staticmethod
    def _prepare_update_payload(hale_data: dict,
                                name: str = None,
                                description: str = None,
                                access: Literal["workspace", "company-user-groups", "company", "public"] = None,
                                log_sessions: bool = None,
                                log_path: str = None):

        payload = HalEPayload.validate(hale_data)
        if name:
            payload.appConfig.name = name
        if description:
            payload.appConfig.description = description
        if access:
            payload.appConfig.accessType = access

        if log_sessions is not None:
            if log_sessions:
                if not (payload.appConfig.appParams.config.sessions.path or log_path):
                    raise ValueError("'log_sessions' cannot be set to True without providing a log_path.")
            payload.appConfig.appParams.config.sessions.persistSession = bool(log_sessions)

        if log_path:
            workspace_log_path = runner_path_to_workspace_path(log_path)
            payload.appConfig.appParams.config.sessions.path = workspace_log_path

        return HalEPayload.validate(payload.dict())

    def update(self,
               name: str = None,
               description: str = None,
               access: Literal["workspace", "company-user-groups", "company", "public"] = None,
               log_sessions: bool = None,
               log_path: str = None):
        """
        Updates the given properties of the Hal-E.

        Parameters
        ----------
        name : str, optional
        description : str, optional
        access : "workspace", "company-user-groups", "company", or "public", optional
        log_sessions : bool, optional
        log_path : str, optional
        """
        hale_data = _get_hale_data_by_name(self.name)
        if name:
            if _is_hale_name_occupied(name):
                raise ValueError(f"Hal-E name {name} is already taken.")

        endpoint = self._get_update_endpoint()
        payload = self._prepare_update_payload(
            hale_data=hale_data,
            name=name, description=description, access=access,
            log_sessions=log_sessions, log_path=log_path
        )

        with httpx.Client() as client:
            response = client.put(
                endpoint,
                headers=get_api_headers(),
                json=payload.dict()
            )
            response.raise_for_status()
            updated_data = response.json()["data"]

        self.__init__(updated_data)

    async def update_async(
            self,
            name: str = None,
            description: str = None,
            access: Literal["workspace", "company-user-groups", "company", "public"] = None,
            log_sessions: bool = None,
            log_path: str = None):
        """
        Updates the given properties of the Hal-E asynchronously.

        Parameters
        ----------
        name : str, optional
        description : str, optional
        access : "workspace", "company-user-groups", "company", or "public", optional
        log_sessions : bool, optional
        log_path : str, optional
        """
        hale_data = await _get_hale_data_by_name_async(self.name)
        if name:
            if await _is_hale_name_occupied_async(name):
                raise ValueError(f"Hal-E name {name} is already taken.")

        endpoint = self._get_update_endpoint()
        payload = self._prepare_update_payload(
            hale_data=hale_data,
            name=name, description=description, access=access,
            log_sessions=log_sessions, log_path=log_path
        )

        async with httpx.AsyncClient() as client:
            response = await client.put(
                endpoint,
                headers=get_api_headers(),
                json=payload.dict()
            )
            response.raise_for_status()
            updated_data = response.json()["data"]

        self.__init__(updated_data)

    def delete(self):
        """
        Deletes the Hal-E.
        """
        endpoint = self._get_update_endpoint()
        with httpx.Client() as client:
            response = client.delete(
                endpoint,
                headers=get_api_headers(),
            )
            response.raise_for_status()

        self._del_params()

    async def delete_async(self):
        """
        Deletes the Hal-E asynchronously.
        """
        endpoint = self._get_update_endpoint()
        async with httpx.AsyncClient() as client:
            response = await client.delete(
                endpoint,
                headers=get_api_headers(),
            )
            response.raise_for_status()

        self._del_params()

    def _get_sessions_endpoint(self):
        endpoint = _get_endpoint()
        endpoint = endpoint.rstrip("/") + f"/{quote(self.name)}/sessions"
        return endpoint

    @staticmethod
    def _create_sessions_list(response_data):
        sessions = []
        for d in response_data:
            sess = get_session_data_from_response_data(d, variant="get")
            sessions.append(sess)

        return sessions

    def get_session_data(self):
        endpoint = self._get_sessions_endpoint()
        with httpx.Client() as client:
            response = client.get(
                endpoint,
                headers=get_api_headers(),
            )
            response.raise_for_status()

        data = response.json()["data"]
        return self._create_sessions_list(
            response_data=data
        )

    async def get_session_data_async(self):
        endpoint = self._get_sessions_endpoint()
        async with httpx.AsyncClient() as client:
            response = await client.get(
                endpoint,
                headers=get_api_headers(),
            )
            response.raise_for_status()

        data = response.json()["data"]
        return self._create_sessions_list(
            response_data=data
        )


class Assets:
    def __init__(self, parent: HalE):
        self.parent = parent  # Reference to HalE instance

    # Logo management
    def upload_logo(self, logo_path):
        """
        Uploads a logo file to the Hal-E.

        Parameters
        ----------
        logo_path : str
            Path to the logo file to be uploaded.

        Raises
        ------
        httpx.HTTPError
            If the HTTP request returned an error status.
        """
        endpoint = self.parent._get_update_endpoint().rstrip("/") + "/logo"
        files = [('files', open(logo_path, 'rb'))]

        with httpx.Client() as client:
            response = client.put(
                endpoint,
                headers=get_api_headers(),
                files=files
            )
        for _, f in files:
            f.close()
        response.raise_for_status()

    async def upload_logo_async(self, logo_path):
        """
        Asynchronously uploads a logo file to the Hal-E.

        Parameters
        ----------
        logo_path : str
            Path to the logo file to be uploaded.

        Raises
        ------
        httpx.HTTPError
            If the HTTP request returned an error status.
        """
        endpoint = self.parent._get_update_endpoint().rstrip("/") + "/logo"
        files = [('files', open(logo_path, 'rb'))]

        async with httpx.AsyncClient() as client:
            response = await client.put(
                endpoint,
                headers=get_api_headers(),
                files=files
            )
        for _, f in files:
            f.close()
        response.raise_for_status()

    def delete_logo(self):
        """
        Deletes the logo from the Hal-E.

        Raises
        ------
        httpx.HTTPError
            If the HTTP request returned an error status.
        """
        endpoint = self.parent._get_update_endpoint().rstrip("/") + "/logo"

        with httpx.Client() as client:
            response = client.delete(
                endpoint,
                headers=get_api_headers()
            )
        response.raise_for_status()

    async def delete_logo_async(self):
        """
        Asynchronously deletes the logo from the Hal-E.

        Raises
        ------
        httpx.HTTPError
            If the HTTP request returned an error status.
        """
        endpoint = self.parent._get_update_endpoint().rstrip("/") + "/logo"

        async with httpx.AsyncClient() as client:
            response = await client.delete(
                endpoint,
                headers=get_api_headers()
            )
        response.raise_for_status()

    # Description management
    def generate_description(self):
        """
        Generates and updates the Hal-E name and description
        using Halerium's AI describer.

        Returns
        -------
        dict
            The dictionary with the generated title and description.

        Raises
        ------
        httpx.HTTPError
            If the HTTP request returned an error status.
        """
        endpoint = self.parent._get_update_endpoint().rstrip("/") + "/describe"
        board_path = self.parent.template_board

        with httpx.Client() as client:
            response = client.get(
                endpoint,
                headers=get_api_headers(),
                params={"board": board_path}
            )
        response.raise_for_status()
        data = response.json()["data"]
        if "title" in data:
            self.parent.name = data["title"]
        if "description" in data:
            self.parent.description = data["description"]
        return data

    async def generate_description_async(self):
        """
        Asynchronously generates and updates the Hal-E name and description
        using Halerium's AI describer.

        Returns
        -------
        dict
            The dictionary with the generated title and description.

        Raises
        ------
        httpx.HTTPError
            If the HTTP request returned an error status.
        """
        endpoint = self.parent._get_update_endpoint().rstrip("/") + "/describe"
        board_path = self.parent.template_board

        async with httpx.AsyncClient() as client:
            response = await client.get(
                endpoint,
                headers=get_api_headers(),
                params={"board": board_path}
            )
        response.raise_for_status()
        data = response.json()["data"]
        if "title" in data:
            self.parent.name = data["title"]
        if "description" in data:
            self.parent.description = data["description"]
        return data

    # Logo generation
    def generate_logo(self):
        """
        Generates a new logo for the Hal-E using the current name and description.
        The logo is not returned by the function but instead generated by the server
        asynchronously.

        Raises
        ------
        httpx.HTTPError
            If the HTTP request returned an error status.
        """

        endpoint = self.parent._get_update_endpoint().rstrip("/") + "/create-avatar"

        with httpx.Client() as client:
            response = client.post(
                endpoint,
                headers=get_api_headers(),
                json={"title": self.parent.name,
                      "description": self.parent.description},
                timeout=300,
            )
        response.raise_for_status()

    async def generate_logo_async(self):
        """
        Asynchronously generates a new logo for the Hal-E using the current name and description.
        The logo is not returned by the function but instead generated by the server
        asynchronously.

        Raises
        ------
        httpx.HTTPError
            If the HTTP request returned an error status.
        """
        endpoint = self.parent._get_update_endpoint().rstrip("/") + "/create-avatar"

        async with httpx.AsyncClient() as client:
            response = await client.post(
                endpoint,
                headers=get_api_headers(),
                json={"title": self.parent.name,
                      "description": self.parent.description},
                timeout=300,
            )
        response.raise_for_status()

