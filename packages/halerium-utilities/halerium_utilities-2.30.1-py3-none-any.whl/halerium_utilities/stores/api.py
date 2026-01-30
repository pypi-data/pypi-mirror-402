from typing import List, Union, Optional, Dict

import httpx

from halerium_utilities.stores.chunker import Document
from halerium_utilities.stores.models import FilterPayload, RangeParam, SearchParam
from halerium_utilities.logging.exceptions import InformationStoreException
from halerium_utilities.utils.api_config import get_api_headers, get_api_base_url


REQUEST_PARAMETERS = {
    "base_url": None,
    "headers": None,
    "timeout": None
}


def update_request_parameters(base_url=None, headers=None, timeout=None):
    """Update global request parameters."""
    if base_url:
        REQUEST_PARAMETERS["base_url"] = base_url
    if headers:
        REQUEST_PARAMETERS["headers"] = headers
    if timeout:
        REQUEST_PARAMETERS["timeout"] = timeout


def reset_request_parameters(reset_base_url=True,
                             reset_headers=True,
                             reset_timeout=True):
    """Reset the global request parameters using environment variables."""
    update_request_parameters(
        base_url=get_api_base_url() + "/information-store" if reset_base_url else None,
        headers=get_api_headers() if reset_headers else None,
        timeout=120 if reset_timeout else None,
    )


def get_request_parameters():
    reset_base_url = not REQUEST_PARAMETERS.get("base_url")
    reset_headers = not REQUEST_PARAMETERS.get("headers")
    reset_timeout = not REQUEST_PARAMETERS.get("timeout")
    reset_request_parameters(reset_base_url=reset_base_url,
                             reset_headers=reset_headers,
                             reset_timeout=reset_timeout)
    return {**REQUEST_PARAMETERS}


def get_workspace_information_stores():
    """
    Retrieve all information stores in the workspace.

    Returns:
        dict: JSON response containing information about all stores.
    Raises:
        InformationStoreException: If the request fails.
    """
    request_parameters = get_request_parameters()
    url = request_parameters["base_url"] + "/stores/"
    headers = request_parameters["headers"]
    timeout = request_parameters["timeout"]

    with httpx.Client() as client:
        response = client.get(url, headers=headers, timeout=timeout)

    if response.status_code != 200:
        raise InformationStoreException(
            f"Could not get information stores ({response.status_code}).\n{response.text}"
        )

    return response.json()


async def get_workspace_information_stores_async():
    """
    Asynchronously retrieve all information stores in the workspace.

    Returns:
        dict: JSON response containing information about all stores.
    Raises:
        InformationStoreException: If the request fails.
    """
    request_parameters = get_request_parameters()
    url = request_parameters["base_url"] + "/stores/"
    headers = request_parameters["headers"]
    timeout = request_parameters["timeout"]

    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers, timeout=timeout)

    if response.status_code != 200:
        raise InformationStoreException("Could not get information stores (%d).\n%s" % (response.status_code, response.text))

    return response.json()


def get_information_store_info(store_id):
    """
    Retrieve information about a specific information store.

    Args:
        store_id (str): The ID of the information store.

    Returns:
        dict: JSON response containing information about the specified store.
    Raises:
        InformationStoreException: If the request fails.
    """
    request_parameters = get_request_parameters()
    url = request_parameters["base_url"] + f"/stores/{store_id}/"
    headers = request_parameters["headers"]
    timeout = request_parameters["timeout"]

    with httpx.Client() as client:
        response = client.get(url, headers=headers, timeout=timeout)

    if response.status_code != 200:
        raise InformationStoreException("Could not get information store (%d).\n%s" % (response.status_code, response.text))

    return response.json()


async def get_information_store_info_async(store_id):
    """
    Asynchronously retrieve information about a specific information store.

    Args:
        store_id (str): The ID of the information store.

    Returns:
        dict: JSON response containing information about the specified store.
    Raises:
        InformationStoreException: If the request fails.
    """
    request_parameters = get_request_parameters()
    url = request_parameters["base_url"] + f"/stores/{store_id}/"
    headers = request_parameters["headers"]
    timeout = request_parameters["timeout"]

    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers, timeout=timeout)

    if response.status_code != 200:
        raise InformationStoreException("Could not get information store (%d).\n%s" % (response.status_code, response.text))

    return response.json()


def add_information_store(name, description=""):
    """
    Add a new information store.

    Args:
        name (str): The name of the new information store.
        description (str, optional): The description of the information store.

    Returns:
        dict: JSON response containing information about the added store.
    Raises:
        InformationStoreException: If the request fails.
    """
    request_parameters = get_request_parameters()
    url = request_parameters["base_url"] + "/stores/"
    headers = request_parameters["headers"]
    timeout = request_parameters["timeout"]

    payload = {"name": name,
               "description": description}

    with httpx.Client() as client:
        response = client.post(url, headers=headers, json=payload, timeout=timeout)

    if response.status_code != 200:
        raise InformationStoreException("Could not add information store (%d).\n%s" % (response.status_code, response.text))

    return response.json()


async def add_information_store_async(name, description=""):
    """
    Asynchronously add a new information store.

    Args:
        name (str): The name of the new information store.
        description (str, optional): The description of the information store.

    Returns:
        dict: JSON response containing information about the added store.
    Raises:
        InformationStoreException: If the request fails.
    """
    request_parameters = get_request_parameters()
    url = request_parameters["base_url"] + "/stores/"
    headers = request_parameters["headers"]
    timeout = request_parameters["timeout"]

    payload = {"name": name,
               "description": description}

    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=headers, json=payload, timeout=timeout)

    if response.status_code != 200:
        raise InformationStoreException("Could not add information store (%d).\n%s" % (response.status_code, response.text))

    return response.json()


def rename_information_store(store_id, new_name):
    """
    Rename an existing information store.

    Args:
        store_id (str): The ID of the information store.
        new_name (str): The new name for the information store.

    Returns:
        dict: JSON response containing information about the renamed store.
    Raises:
        InformationStoreException: If the request fails.
    """
    request_parameters = get_request_parameters()
    url = request_parameters["base_url"] + f"/stores/{store_id}/"
    headers = request_parameters["headers"]
    timeout = request_parameters["timeout"]

    payload = {"name": new_name}

    with httpx.Client() as client:
        response = client.put(url, headers=headers, json=payload, timeout=timeout)

    if response.status_code != 200:
        raise InformationStoreException("Could not rename information store (%d).\n%s" % (response.status_code, response.text))

    return response.json()


async def rename_information_store_async(store_id, new_name):
    """
    Asynchronously rename an existing information store.

    Args:
        store_id (str): The ID of the information store.
        new_name (str): The new name for the information store.

    Returns:
        dict: JSON response containing information about the renamed store.
    Raises:
        InformationStoreException: If the request fails.
    """
    request_parameters = get_request_parameters()
    url = request_parameters["base_url"] + f"/stores/{store_id}/"
    headers = request_parameters["headers"]
    timeout = request_parameters["timeout"]

    payload = {"name": new_name}

    async with httpx.AsyncClient() as client:
        response = await client.put(url, headers=headers, json=payload, timeout=timeout)

    if response.status_code != 200:
        raise InformationStoreException("Could not rename information store (%d).\n%s" % (response.status_code, response.text))

    return response.json()


def delete_information_store(store_id):
    """
    Delete an information store.

    Args:
        store_id (str): The ID of the information store.

    Returns:
        dict: JSON response confirming deletion.
    Raises:
        InformationStoreException: If the request fails.
    """
    request_parameters = get_request_parameters()
    url = request_parameters["base_url"] + f"/stores/{store_id}"
    headers = request_parameters["headers"]
    timeout = request_parameters["timeout"]

    with httpx.Client() as client:
        response = client.delete(url, headers=headers, timeout=timeout)

    if response.status_code != 200:
        raise InformationStoreException("Could not delete information store (%d).\n%s" % (response.status_code, response.text))

    return response.json()


async def delete_information_store_async(store_id):
    """
    Asynchronously delete an information store.

    Args:
        store_id (str): The ID of the information store.

    Returns:
        dict: JSON response confirming deletion.
    Raises:
        InformationStoreException: If the request fails.
    """
    request_parameters = get_request_parameters()
    url = request_parameters["base_url"] + f"/stores/{store_id}"
    headers = request_parameters["headers"]
    timeout = request_parameters["timeout"]

    async with httpx.AsyncClient() as client:
        response = await client.delete(url, headers=headers, timeout=timeout)

    if response.status_code != 200:
        raise InformationStoreException("Could not delete information store (%d).\n%s" % (response.status_code, response.text))

    return response.json()


def delete_information_store_events(store_id):
    """
    Delete all events of an information store.

    Args:
        store_id (str): The ID of the information store.

    Returns:
        dict: JSON response confirming deletion of events.
    Raises:
        InformationStoreException: If the request fails.
    """
    request_parameters = get_request_parameters()
    url = request_parameters["base_url"] + f"/stores/{store_id}/events/"
    headers = request_parameters["headers"]
    timeout = request_parameters["timeout"]

    with httpx.Client() as client:
        response = client.delete(url, headers=headers, timeout=timeout)

    if response.status_code != 200:
        raise InformationStoreException("Could not delete events of information store (%d).\n%s" % (response.status_code, response.text))

    return response.json()


async def delete_information_store_events_async(store_id):
    """
    Asynchronously delete all events of an information store.

    Args:
        store_id (str): The ID of the information store.

    Returns:
        dict: JSON response confirming deletion of events.
    Raises:
        InformationStoreException: If the request fails.
    """
    request_parameters = get_request_parameters()
    url = request_parameters["base_url"] + f"/stores/{store_id}/events/"
    headers = request_parameters["headers"]
    timeout = request_parameters["timeout"]

    async with httpx.AsyncClient() as client:
        response = await client.delete(url, headers=headers, timeout=timeout)

    if response.status_code != 200:
        raise InformationStoreException("Could not delete events of information store (%d).\n%s" % (response.status_code, response.text))

    return response.json()


def export_information_store(store_id: str, output_path: str):
    """
    Export a store as downloadable file.

    Args:
        store_id (str): The ID of the information store.
        output_path (str): The file path to export the store to.

    Returns:
        output_path (str): the file path of the created file.
    Raises:
        InformationStoreException: If the request fails.
    """
    request_parameters = get_request_parameters()
    url = request_parameters["base_url"] + f"/stores/{store_id}/export"
    headers = request_parameters["headers"]
    timeout = request_parameters["timeout"]

    with httpx.Client() as client:
        response = client.get(url, headers=headers, timeout=timeout)

    if response.status_code != 200:
        raise InformationStoreException(
            f"Could not export information store ({response.status_code}).\n{response.text}"
        )

    with open(output_path, 'wb') as f:
        f.write(response.content)

    return output_path


async def export_information_store_async(store_id: str, output_path: str):
    """
    Export a store as downloadable file.

    Args:
        store_id (str): The ID of the information store.
        output_path (str): The file path to export the store to.

    Returns:
        output_path (str): the file path of the created file.
    Raises:
        InformationStoreException: If the request fails.
    """
    request_parameters = get_request_parameters()
    url = request_parameters["base_url"] + f"/stores/{store_id}/export"
    headers = request_parameters["headers"]
    timeout = request_parameters["timeout"]

    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers, timeout=timeout)

    if response.status_code != 200:
        raise InformationStoreException(
            f"Could not export information store ({response.status_code}).\n{response.text}"
        )

    with open(output_path, 'wb') as f:
        f.write(response.content)

    return output_path


def import_information_stores(file_paths: List[str]):
    """
    Import multiple information stores from .infostore JSON files.

    Args:
        file_paths (list): List of file paths of .infostore files.

    Returns:
        dict: JSON response confirming deletion of events.
    Raises:
        InformationStoreException: If the request fails.
    """
    request_parameters = get_request_parameters()
    url = request_parameters["base_url"] + "/import-stores/"
    headers = request_parameters["headers"]
    timeout = request_parameters["timeout"]

    files = [('files', open(fp, 'rb')) for fp in file_paths]

    with httpx.Client() as client:
        response = client.post(url, headers=headers, files=files, timeout=timeout)

    for _, f in files:
        f.close()

    if response.status_code != 200:
        raise InformationStoreException(
            f"Could not import information stores ({response.status_code}).\n{response.text}"
        )

    return response.json()


async def import_information_stores_async(file_paths: List[str]):
    """
    Import multiple information stores from .infostore JSON files.

    Args:
        file_paths (list): List of file paths of .infostore files.

    Returns:
        dict: JSON response confirming deletion of events.
    Raises:
        InformationStoreException: If the request fails.
    """
    request_parameters = get_request_parameters()
    url = request_parameters["base_url"] + "/import-stores/"
    headers = request_parameters["headers"]
    timeout = request_parameters["timeout"]

    files = [('files', open(fp, 'rb')) for fp in file_paths]

    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=headers, files=files, timeout=timeout)

    for _, f in files:
        f.close()

    if response.status_code != 200:
        raise InformationStoreException(
            f"Could not import information stores ({response.status_code}).\n{response.text}"
        )

    return response.json()


def add_memory_to_store(store_id, memory: str):
    """
    Add memory to a specific information store.

    Args:
        store_id (str): The ID of the information store.
        memory (str): The memory content to add.

    Returns:
        dict: JSON response containing information about the added memory.
    Raises:
        InformationStoreException: If the request fails.
    """
    request_parameters = get_request_parameters()
    url = request_parameters["base_url"] + f"/stores/{store_id}/memories"
    headers = request_parameters["headers"]
    timeout = request_parameters["timeout"]

    payload = {"memory": memory}

    with httpx.Client() as client:
        response = client.post(url, headers=headers, json=payload, timeout=timeout)

    if response.status_code != 200:
        raise InformationStoreException("Could not add memory to information store (%d).\n%s" % (response.status_code, response.text))

    return response.json()


async def add_memory_to_store_async(store_id, memory: str):
    """
    Asynchronously add memory to a specific information store.

    Args:
        store_id (str): The ID of the information store.
        memory (str): The memory content to add.

    Returns:
        dict: JSON response containing information about the added memory.
    Raises:
        InformationStoreException: If the request fails.
    """
    request_parameters = get_request_parameters()
    url = request_parameters["base_url"] + f"/stores/{store_id}/memories"
    headers = request_parameters["headers"]
    timeout = request_parameters["timeout"]

    payload = {"memory": memory}

    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=headers, json=payload, timeout=timeout)

    if response.status_code != 200:
        raise InformationStoreException("Could not add memory to information store (%d).\n%s" % (response.status_code, response.text))

    return response.json()


def update_memory_in_store(store_id, memory_id: str, memory: str):
    """
    Update a memory in a specific information store.

    Args:
        store_id (str): The ID of the information store.
        memory_id (str): The ID of the memory to update.
        memory (str): The updated memory content.

    Returns:
        dict: JSON response containing information about the updated memory.
    Raises:
        InformationStoreException: If the request fails.
    """
    request_parameters = get_request_parameters()
    url = request_parameters["base_url"] + f"/stores/{store_id}/memories/{memory_id}"
    headers = request_parameters["headers"]
    timeout = request_parameters["timeout"]

    payload = {"memory": memory}

    with httpx.Client() as client:
        response = client.put(url, headers=headers, json=payload, timeout=timeout)

    if response.status_code != 200:
        raise InformationStoreException("Could not update memory in information store (%d).\n%s" % (response.status_code, response.text))

    return response.json()


async def update_memory_in_store_async(store_id, memory_id: str, memory: str):
    """
    Asynchronously update a memory in a specific information store.

    Args:
        store_id (str): The ID of the information store.
        memory_id (str): The ID of the memory to update.
        memory (str): The updated memory content.

    Returns:
        dict: JSON response containing information about the updated memory.
    Raises:
        InformationStoreException: If the request fails.
    """
    request_parameters = get_request_parameters()
    url = request_parameters["base_url"] + f"/stores/{store_id}/memories/{memory_id}"
    headers = request_parameters["headers"]
    timeout = request_parameters["timeout"]

    payload = {"memory": memory}

    async with httpx.AsyncClient() as client:
        response = await client.put(url, headers=headers, json=payload, timeout=timeout)

    if response.status_code != 200:
        raise InformationStoreException("Could not update memory in information store (%d).\n%s" % (response.status_code, response.text))

    return response.json()


def delete_memory_in_store(store_id, memory_id: str):
    """
    Delete a memory in a specific information store.

    Args:
        store_id (str): The ID of the information store.
        memory_id (str): The ID of the memory to delete.

    Returns:
        dict: JSON response confirming deletion.
    Raises:
        InformationStoreException: If the request fails.
    """
    request_parameters = get_request_parameters()
    url = request_parameters["base_url"] + f"/stores/{store_id}/memories/{memory_id}"
    headers = request_parameters["headers"]
    timeout = request_parameters["timeout"]

    with httpx.Client() as client:
        response = client.delete(url, headers=headers, timeout=timeout)

    if response.status_code != 200:
        raise InformationStoreException("Could not delete memory in information store (%d).\n%s" % (response.status_code, response.text))

    return response.json()


async def delete_memory_in_store_async(store_id, memory_id: str):
    """
    Asynchronously delete a memory in a specific information store.

    Args:
        store_id (str): The ID of the information store.
        memory_id (str): The ID of the memory to delete.

    Returns:
        dict: JSON response confirming deletion.
    Raises:
        InformationStoreException: If the request fails.
    """
    request_parameters = get_request_parameters()
    url = request_parameters["base_url"] + f"/stores/{store_id}/memories/{memory_id}"
    headers = request_parameters["headers"]
    timeout = request_parameters["timeout"]

    async with httpx.AsyncClient() as client:
        response = await client.delete(url, headers=headers, timeout=timeout)

    if response.status_code != 200:
        raise InformationStoreException("Could not delete memory in information store (%d).\n%s" % (response.status_code, response.text))

    return response.json()


def add_file_to_vectorstore(vectorstore_id, filepath: str,
                            chunker_args: Optional[Dict[str, Union[str, bool, List[str]]]] = None,
                            metadata: Optional[Dict[str, str]] = None,
                            chunk_size: int = None,
                            chunk_overlap: int = None):
    """
    Deprecated function. Use 'add_file_to_store' instead.
    """
    raise NotImplementedError(
        "'add_file_to_vectorstore' was deprecated.\n"
        "Use 'add_file_to_store' instead."
    )


def add_file_to_store(store_id, filepath: str,
                      chunker_args: Optional[Dict[str, Union[str, bool, List[str]]]] = None,
                      metadata: Optional[Dict[str, str]] = None,
                      chunk_size: int = None,
                      chunk_overlap: int = None):
    """
    Add a file to an information store.

    Args:
        store_id (str): The ID of the information store.
        filepath (str): The path to the file to add.
        chunker_args (Optional[Dict[str, Union[str, bool, List[str]]]]): Arguments for chunking.
        metadata (Optional[Dict[str, str]]): Metadata for the file.
        chunk_size (int): Size of chunks.
        chunk_overlap (int): Overlap between chunks.

    Returns:
        dict: JSON response containing information about the added file.
    Raises:
        InformationStoreException: If the request fails.
    """
    request_parameters = get_request_parameters()
    url = request_parameters["base_url"] + f"/stores/{store_id}/files"
    headers = request_parameters["headers"]
    timeout = request_parameters["timeout"]

    if chunker_args is None:
        chunker_args = dict()

    if metadata is None:
        metadata = dict()

    payload = {"filepath": filepath}
    if chunk_size is not None:
        payload["chunk_size"] = chunk_size
    if chunk_overlap is not None:
        payload["chunk_overlap"] = chunk_overlap
    if metadata is not None:
        payload["metadata"] = metadata
    if chunker_args:
        payload["chunker_args"] = chunker_args

    with httpx.Client() as client:
        response = client.post(url, headers=headers, json=payload, timeout=timeout)

    if response.status_code != 200:
        raise InformationStoreException("Could not add file to information store (%d).\n%s" % (response.status_code, response.text))

    return response.json()


async def add_file_to_vectorstore_async(vectorstore_id, filepath: str,
                                        chunker_args: Optional[Dict[str, Union[str, bool, List[str]]]] = None,
                                        metadata: Optional[Dict[str, str]] = None,
                                        chunk_size: int = None,
                                        chunk_overlap: int = None):
    """
    Deprecated function. Use 'add_file_to_store_async' instead.
    """
    raise NotImplementedError(
        "'add_file_to_vectorstore_async' was deprecated.\n"
        "Use 'add_file_to_store_async' instead."
    )


async def add_file_to_store_async(store_id, filepath: str,
                                  chunker_args: Optional[Dict[str, Union[str, bool, List[str]]]] = None,
                                  metadata: Optional[Dict[str, str]] = None,
                                  chunk_size: int = None,
                                  chunk_overlap: int = None):
    """
    Asynchronously add a file to an information store.

    Args:
        store_id (str): The ID of the information store.
        filepath (str): The path to the file to add.
        chunker_args (Optional[Dict[str, Union[str, bool, List[str]]]]): Arguments for chunking.
        metadata (Optional[Dict[str, str]]): Metadata for the file.
        chunk_size (int): Size of chunks.
        chunk_overlap (int): Overlap between chunks.

    Returns:
        dict: JSON response containing information about the added file.
    Raises:
        InformationStoreException: If the request fails.
    """
    request_parameters = get_request_parameters()
    url = request_parameters["base_url"] + f"/stores/{store_id}/files"
    headers = request_parameters["headers"]
    timeout = request_parameters["timeout"]

    if chunker_args is None:
        chunker_args = dict()

    if metadata is None:
        metadata = dict()

    payload = {"filepath": filepath}
    if chunk_size is not None:
        payload["chunk_size"] = chunk_size
    if chunk_overlap is not None:
        payload["chunk_overlap"] = chunk_overlap
    if metadata is not None:
        payload["metadata"] = metadata
    if chunker_args:
        payload["chunker_args"] = chunker_args

    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=headers, json=payload, timeout=timeout)

    if response.status_code != 200:
        raise InformationStoreException("Could not add file to information store (%d).\n%s" % (response.status_code, response.text))

    return response.json()


def add_chunks_to_vectorstore(vectorstore_id, chunks: List[Union[Document, dict]]):
    """
    Deprecated function. Use add_chunks_to_store instead.
    """
    raise NotImplementedError(
        "'add_chunks_to_vectorstore' was deprecated.\n"
        "Use 'add_chunks_to_store' instead."
    )


def add_chunks_to_store(store_id, chunks: List[Union[Document, dict]]):
    """
    Add chunks to a specific information store.

    Args:
        store_id (str): The ID of the information store.
        chunks (List[Union[Document, dict]]): List of chunks to add.

    Returns:
        dict: JSON response containing information about the added chunks.
    Raises:
        InformationStoreException: If the request fails.
    """
    chunks = [Document.validate(c) for c in chunks]

    request_parameters = get_request_parameters()
    url = request_parameters["base_url"] + f"/stores/{store_id}/chunks/"
    headers = request_parameters["headers"]
    timeout = request_parameters["timeout"]

    payload = {"chunks": [chunk.dict() for chunk in chunks]}

    with httpx.Client() as client:
        response = client.post(url, headers=headers, json=payload, timeout=timeout)

    if response.status_code != 200:
        raise InformationStoreException("Could not add chunks to information store (%d).\n%s" % (response.status_code, response.text))

    return response.json()


async def add_chunks_to_vectorstore_async(vectorstore_id, chunks: List[Union[Document, dict]]):
    """
    Deprecated function. Use add_chunks_to_store_async instead.
    """
    raise NotImplementedError(
        "'add_chunks_to_vectorstore_async' was deprecated.\n"
        "Use 'add_chunks_to_store_async' instead."
    )


async def add_chunks_to_store_async(store_id, chunks: List[Union[Document, dict]]):
    """
    Asynchronously add chunks to a specific information store.

    Args:
        store_id (str): The ID of the information store.
        chunks (List[Union[Document, dict]]): List of chunks to add.

    Returns:
        dict: JSON response containing information about the added chunks.
    Raises:
        InformationStoreException: If the request fails.
    """
    chunks = [Document.validate(c) for c in chunks]

    request_parameters = get_request_parameters()
    url = request_parameters["base_url"] + f"/stores/{store_id}/chunks/"
    headers = request_parameters["headers"]
    timeout = request_parameters["timeout"]

    payload = {"chunks": [chunk.dict() for chunk in chunks]}

    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=headers, json=payload, timeout=timeout)

    if response.status_code != 200:
        raise InformationStoreException("Could not add chunks to information store (%d).\n%s" % (response.status_code, response.text))

    return response.json()


def query_vectorstore(vectorstore_id,
                      query: str,
                      example_text: str = None,
                      keywords: str = None,
                      max_results: int = 5,
                      threshold: int = -1,
                      filters: List[Union[RangeParam, SearchParam]] = None):
    """
    Deprecated function. Use 'query_store' instead.
    """
    raise NotImplementedError(
        "'query_vectorstore' was deprecated.\n"
        "Use 'query_store' instead."
    )


def query_store(store_id,
                query: str,
                example_text: str = None,
                keywords: str = None,
                max_results: int = 5,
                threshold: int = -1,
                filters: List[Union[RangeParam, SearchParam]] = None):
    """
    Query a specific information store.

    Args:
        store_id (str): The ID of the information store.
        query (str): The query string.
        example_text (str, optional): Example text to help refine the query.
        keywords (str, optional): Keywords to search for.
        max_results (int, optional): Maximum number of results to return. Defaults to 5.
        threshold (int, optional): Score threshold for filtering results. Defaults to -1.
        filters (List[Union[RangeParam, SearchParam]], optional): List of filters to apply.

    Returns:
        dict: JSON response containing query results.
    Raises:
        InformationStoreException: If the request fails.
    """
    request_parameters = get_request_parameters()
    url = request_parameters["base_url"] + f"/stores/{store_id}/search/"
    headers = request_parameters["headers"]
    timeout = request_parameters["timeout"]

    parameters = {
        "query": query,
        "example_text": example_text,
        "keywords": keywords,
        "max_results": max_results,
        "threshold": threshold,
    }

    body = FilterPayload.validate({"filter": filters}).dict() if filters else None

    with httpx.Client() as client:
        response = client.post(url, headers=headers, timeout=timeout,
                               params=parameters, json=body)

    if response.status_code != 200:
        raise InformationStoreException("Could not query information store (%d).\n%s" % (response.status_code, response.text))

    return response.json()


async def query_vectorstore_async(vectorstore_id,
                                  query: str,
                                  example_text: str = None,
                                  keywords: str = None,
                                  max_results: int = 5,
                                  threshold: int = -1,
                                  filters: List[Union[RangeParam, SearchParam]] = None):
    """
    Deprecated function. Use 'query_store_async' instead.
    """
    raise NotImplementedError(
        "'query_vectorstore_async' was deprecated.\n"
        "Use 'query_store_async' instead."
    )


async def query_store_async(store_id,
                            query: str,
                            example_text: str = None,
                            keywords: str = None,
                            max_results: int = 5,
                            threshold: int = -1,
                            filters: List[Union[RangeParam, SearchParam]] = None):
    """
    Asynchronously query a specific information store.

    Args:
        store_id (str): The ID of the information store.
        query (str): The query string.
        example_text (str, optional): Example text to help refine the query.
        keywords (str, optional): Keywords to search for.
        max_results (int, optional): Maximum number of results to return. Defaults to 5.
        threshold (int, optional): Score threshold for filtering results. Defaults to -1.
        filters (List[Union[RangeParam, SearchParam]], optional): List of filters to apply.

    Returns:
        dict: JSON response containing query results.
    Raises:
        InformationStoreException: If the request fails.
    """
    request_parameters = get_request_parameters()
    url = request_parameters["base_url"] + f"/stores/{store_id}/search/"
    headers = request_parameters["headers"]
    timeout = request_parameters["timeout"]

    parameters = {
        "query": query,
        "example_text": example_text,
        "keywords": keywords,
        "max_results": max_results,
        "threshold": threshold,
    }

    body = FilterPayload.validate({"filter": filters}).dict() if filters else None

    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=headers, timeout=timeout,
                                     params=parameters, json=body)

    if response.status_code != 200:
        raise InformationStoreException("Could not query information store (%d).\n%s" % (response.status_code, response.text))

    return response.json()


def get_file_as_text(filepath: str, chunker_args: Optional[Dict[str, Union[str, bool, List[str]]]] = None, return_json: bool = False):
    """
    Retrieve a file as plain text.

    Args:
        filepath (str): The path to the file.
        chunker_args (Optional[Dict[str, Union[str, bool, List[str]]]], optional): Arguments for chunking. Defaults to None.
        return_json (bool, optional): Whether to return the content in JSON format. Defaults to False.

    Returns:
        dict: JSON response containing the file content.
    Raises:
        InformationStoreException: If the request fails.
    """
    request_parameters = get_request_parameters()
    url = request_parameters["base_url"] + "/files"
    headers = request_parameters["headers"]
    timeout = request_parameters["timeout"]

    params = {"filepath": filepath, "return_json": return_json}
    if chunker_args:
        params.update(chunker_args)

    with httpx.Client() as client:
        response = client.get(url, headers=headers, params=params, timeout=timeout)

    if response.status_code != 200:
        raise InformationStoreException("Could not get file as text (%d).\n%s" % (response.status_code, response.text))

    return response.json()


async def get_file_as_text_async(filepath: str, chunker_args: Optional[Dict[str, Union[str, bool, List[str]]]] = None, return_json: bool = False):
    """
    Asynchronously retrieve a file as plain text.

    Args:
        filepath (str): The path to the file.
        chunker_args (Optional[Dict[str, Union[str, bool, List[str]]]], optional): Arguments for chunking. Defaults to None.
        return_json (bool, optional): Whether to return the content in JSON format. Defaults to False.

    Returns:
        dict: JSON response containing the file content.
    Raises:
        InformationStoreException: If the request fails.
    """
    request_parameters = get_request_parameters()
    url = request_parameters["base_url"] + "/files"
    headers = request_parameters["headers"]
    timeout = request_parameters["timeout"]

    params = {"filepath": filepath, "return_json": return_json}
    if chunker_args:
        params.update(chunker_args)

    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers, params=params, timeout=timeout)

    if response.status_code != 200:
        raise InformationStoreException("Could not get file as text (%d).\n%s" % (response.status_code, response.text))

    return response.json()


def get_chunks(store_id: str, start=0, size=1000,
               full_chunk_content=False,
               filters: List[Union[RangeParam, SearchParam]] = None):
    """
    Retrieve chunks from a specific information store.

    Args:
        store_id (str): The ID of the information store.
        start (int, optional): The starting index for pagination. Defaults to 0.
        size (int, optional): The number of chunks to retrieve. Defaults to 1000.
        full_chunk_content (bool, optional): Whether to retrieve the full content of chunks. Defaults to False.
        filters (List[Union[RangeParam, SearchParam]], optional): List of filters to apply. Defaults to None.

    Returns:
        dict: JSON response containing the chunks.
    Raises:
        InformationStoreException: If the request fails.
    """
    request_parameters = get_request_parameters()
    url = request_parameters["base_url"] + f"/stores/{store_id}/chunks"
    headers = request_parameters["headers"]
    timeout = request_parameters["timeout"]

    params = {"start": start, "size": size, "full_chunk_content": full_chunk_content}
    body = FilterPayload.validate({"filter": filters}).dict() if filters else None

    with httpx.Client() as client:
        response = client.post(url, headers=headers, timeout=timeout,
                               params=params, json=body)

    if response.status_code != 200:
        raise InformationStoreException("Could not get chunks (%d).\n%s" % (response.status_code, response.text))

    return response.json()


async def get_chunks_async(store_id: str, start=0, size=1000,
                           full_chunk_content=False,
                           filters: List[Union[RangeParam, SearchParam]] = None):
    """
    Asynchronously retrieve chunks from a specific information store.

    Args:
        store_id (str): The ID of the information store.
        start (int, optional): The starting index for pagination. Defaults to 0.
        size (int, optional): The number of chunks to retrieve. Defaults to 1000.
        full_chunk_content (bool, optional): Whether to retrieve the full content of chunks. Defaults to False.
        filters (List[Union[RangeParam, SearchParam]], optional): List of filters to apply. Defaults to None.

    Returns:
        dict: JSON response containing the chunks.
    Raises:
        InformationStoreException: If the request fails.
    """
    request_parameters = get_request_parameters()
    url = request_parameters["base_url"] + f"/stores/{store_id}/chunks"
    headers = request_parameters["headers"]
    timeout = request_parameters["timeout"]

    params = {"start": start, "size": size, "full_chunk_content": full_chunk_content}
    body = FilterPayload.validate({"filter": filters}).dict() if filters else None

    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=headers, timeout=timeout,
                                     params=params, json=body)

    if response.status_code != 200:
        raise InformationStoreException("Could not get chunks (%d).\n%s" % (response.status_code, response.text))

    return response.json()


def get_chunk(store_id: str, chunk_id: str):
    """
    Retrieve a specific chunk from an information store.

    Args:
        store_id (str): The ID of the information store.
        chunk_id (str): The ID of the chunk to retrieve.

    Returns:
        dict: JSON response containing the chunk.
    Raises:
        InformationStoreException: If the request fails.
    """
    request_parameters = get_request_parameters()
    url = request_parameters["base_url"] + f"/stores/{store_id}/chunks/{chunk_id}"
    headers = request_parameters["headers"]
    timeout = request_parameters["timeout"]

    with httpx.Client() as client:
        response = client.get(url, headers=headers, timeout=timeout)

    if response.status_code != 200:
        raise InformationStoreException("Could not get chunk (%d).\n%s" % (response.status_code, response.text))

    return response.json()


async def get_chunk_async(store_id: str, chunk_id: str):
    """
    Asynchronously retrieve a specific chunk from an information store.

    Args:
        store_id (str): The ID of the information store.
        chunk_id (str): The ID of the chunk to retrieve.

    Returns:
        dict: JSON response containing the chunk.
    Raises:
        InformationStoreException: If the request fails.
    """
    request_parameters = get_request_parameters()
    url = request_parameters["base_url"] + f"/stores/{store_id}/chunks/{chunk_id}"
    headers = request_parameters["headers"]
    timeout = request_parameters["timeout"]

    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers, timeout=timeout)

    if response.status_code != 200:
        raise InformationStoreException("Could not get chunk (%d).\n%s" % (response.status_code, response.text))

    return response.json()


def edit_chunk(store_id: str, chunk_id: str, document: Union[Document, dict]):
    """
    Edit a specific chunk in an information store.

    Args:
        store_id (str): The ID of the information store.
        chunk_id (str): The ID of the chunk to edit.
        document (Union[Document, dict]): The updated chunk content.

    Returns:
        dict: JSON response containing information about the edited chunk.
    Raises:
        InformationStoreException: If the request fails.
    """
    document = Document.validate(document)

    request_parameters = get_request_parameters()
    url = request_parameters["base_url"] + f"/stores/{store_id}/chunks/{chunk_id}"
    headers = request_parameters["headers"]
    timeout = request_parameters["timeout"]

    with httpx.Client() as client:
        response = client.put(url, headers=headers, json=document.dict(), timeout=timeout)

    if response.status_code != 200:
        raise InformationStoreException("Could not edit chunk (%d).\n%s" % (response.status_code, response.text))

    return response.json()


async def edit_chunk_async(store_id: str, chunk_id: str, document: Union[Document, dict]):
    """
    Asynchronously edit a specific chunk in an information store.

    Args:
        store_id (str): The ID of the information store.
        chunk_id (str): The ID of the chunk to edit.
        document (Union[Document, dict]): The updated chunk content.

    Returns:
        dict: JSON response containing information about the edited chunk.
    Raises:
        InformationStoreException: If the request fails.
    """
    document = Document.validate(document)

    request_parameters = get_request_parameters()
    url = request_parameters["base_url"] + f"/stores/{store_id}/chunks/{chunk_id}"
    headers = request_parameters["headers"]
    timeout = request_parameters["timeout"]

    async with httpx.AsyncClient() as client:
        response = await client.put(url, headers=headers, json=document.dict(), timeout=timeout)

    if response.status_code != 200:
        raise InformationStoreException("Could not edit chunk (%d).\n%s" % (response.status_code, response.text))

    return response.json()


def delete_chunks(store_id: str, chunk_ids: list[str]):
    """
    Delete specific chunks from an information store.

    Args:
        store_id (str): The ID of the information store.
        chunk_ids (list[str]): List of chunk IDs to delete.

    Returns:
        dict: JSON response confirming deletion.
    Raises:
        InformationStoreException: If the request fails.
    """
    request_parameters = get_request_parameters()
    url = request_parameters["base_url"] + f"/stores/{store_id}/chunks/"
    headers = request_parameters["headers"]
    timeout = request_parameters["timeout"]

    payload = chunk_ids

    with httpx.Client() as client:
        response = client.request("DELETE", url, headers=headers, json=payload, timeout=timeout)

    if response.status_code != 200:
        raise InformationStoreException(
            f"Could not delete chunks ({response.status_code}).\n{response.text}"
        )

    return response.json()


async def delete_chunks_async(store_id: str, chunk_ids: list[str]):
    """
    Asynchronously delete specific chunks from an information store.

    Args:
        store_id (str): The ID of the information store.
        chunk_ids (list[str]): List of chunk IDs to delete.

    Returns:
        dict: JSON response confirming deletion.
    Raises:
        InformationStoreException: If the request fails.
    """
    request_parameters = get_request_parameters()
    url = request_parameters["base_url"] + f"/stores/{store_id}/chunks/"
    headers = request_parameters["headers"]
    timeout = request_parameters["timeout"]

    payload = chunk_ids

    async with httpx.AsyncClient() as client:
        response = await client.request("DELETE", url, headers=headers, json=payload, timeout=timeout)

    if response.status_code != 200:
        raise InformationStoreException(
            f"Could not delete chunks ({response.status_code}).\n{response.text}"
        )

    return response.json()


def delete_chunk(store_id: str, chunk_id: str):
    """
    Delete a specific chunk from an information store.

    Args:
        store_id (str): The ID of the information store.
        chunk_id (str): The ID of the chunk to delete.

    Returns:
        dict: JSON response confirming deletion.
    Raises:
        InformationStoreException: If the request fails.
    """
    request_parameters = get_request_parameters()
    url = request_parameters["base_url"] + f"/stores/{store_id}/chunks/{chunk_id}"
    headers = request_parameters["headers"]
    timeout = request_parameters["timeout"]

    params = {"chunk_id": chunk_id}

    with httpx.Client() as client:
        response = client.delete(url, headers=headers, params=params, timeout=timeout)

    if response.status_code != 200:
        raise InformationStoreException(
            f"Could not delete chunk ({response.status_code}).\n{response.text}"
        )

    return response.json()


async def delete_chunk_async(store_id: str, chunk_id: str):
    """
    Asynchronously delete a specific chunk from an information store.

    Args:
        store_id (str): The ID of the information store.
        chunk_id (str): The ID of the chunk to delete.

    Returns:
        dict: JSON response confirming deletion.
    Raises:
        InformationStoreException: If the request fails.
    """
    request_parameters = get_request_parameters()
    url = request_parameters["base_url"] + f"/stores/{store_id}/chunks/{chunk_id}"
    headers = request_parameters["headers"]
    timeout = request_parameters["timeout"]

    params = {"chunk_id": chunk_id}

    async with httpx.AsyncClient() as client:
        response = await client.delete(url, headers=headers, params=params, timeout=timeout)

    if response.status_code != 200:
        raise InformationStoreException(
            f"Could not delete chunk ({response.status_code}).\n{response.text}"
        )

    return response.json()
