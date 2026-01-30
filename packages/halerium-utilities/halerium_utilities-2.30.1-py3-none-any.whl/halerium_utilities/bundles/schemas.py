from pydantic import BaseModel, Field
from typing import Optional, Literal, List, Dict


class StoreBundleContents(BaseModel):
    hales: List[str] = Field(default_factory=list)
    capabilities: List[str] = Field(default_factory=list)
    infostores: List[str] = Field(default_factory=list)
    files: List[str] = Field(default_factory=list)


class UpdateEntry(BaseModel):
    name: str
    operation: str  # Literal['keep', 'remove', 'update']


class UpdateData(BaseModel):
    hales: List[UpdateEntry] = Field(default_factory=list)
    capabilities: List[UpdateEntry] = Field(default_factory=list)
    infostores: List[UpdateEntry] = Field(default_factory=list)
    files: List[UpdateEntry] = Field(default_factory=list)


ConflictActions = Literal["skip", "replace"]


class ConflictHandling(BaseModel):
    hales: Dict[str, ConflictActions] = Field(default_factory=dict)
    capabilities: Dict[str, ConflictActions] = Field(default_factory=dict)
    infostores: Dict[str, ConflictActions] = Field(default_factory=dict)
    files: Dict[str, ConflictActions] = Field(default_factory=dict)


class Publisher(BaseModel):
    name: str
    verified: bool


class StoreBundle(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    access_scope: Literal["public", "tenant", "user_and_usergroup"]
    publisher: Publisher
    category: str
    version: Optional[str] = None
    featured: Optional[bool] = None
    contents: Optional[StoreBundleContents] = None


class InstallationCheck(BaseModel):
    success: bool
    installed_assets: Optional[Dict[str, bool]] = None
    conflicts: Optional[StoreBundleContents] = None
    update_data: Optional[UpdateData] = None
    missing_runner_type: Optional[List[str]] = None
    required_runner_types: Optional[List[str]] = None


class InstalledBundle(BaseModel):
    installed_version: StoreBundle
    store_version: Optional[StoreBundle] = None


def map_template_keys_to_contents_keys(template_dict):
    contents_dict = {
        "hales": template_dict.get("appConfigNames"),
        "capabilities": template_dict.get("capabilityNames"),
        "infostores": template_dict.get("infoStoreNames"),
        "files": template_dict.get("filePaths")
    }
    return contents_dict


def map_update_keys_to_contents_keys(update_dict):
    contents_dict = {
        "hales": update_dict.get("appConfigs"),
        "capabilities": update_dict.get("capabilities"),
        "infostores": update_dict.get("infoStores"),
        "files": update_dict.get("files")
    }
    return contents_dict


def get_bundle_model_from_response_data(response_data, variant=Literal["short", "long"]):

    parsed_data = {
        "id": response_data["id"],
        "name": response_data["name"],
        "description": response_data.get("description"),
        "access_scope": response_data.get("accessScope"),
        "publisher": {
            "name": response_data["tenant"]["name"],
            "verified": response_data["tenant"].get("verifiedPublisher", False)
        },
        "category": response_data["category"],
        "featured": response_data.get("featured", False),
    }

    latest_version = None
    if variant == "long":
        versions = sorted(response_data["versions"], key=lambda k: k.get("appVersion"))
        if versions:
            latest_version = versions[-1]
    else:
        latest_version = response_data.get("latestVersion")
    if latest_version:
        parsed_data["version"] = latest_version["appVersion"]
        template_data = latest_version.get("appTemplateData")
        if template_data:
            parsed_data["contents"] = map_template_keys_to_contents_keys(template_data)

    return StoreBundle.validate(parsed_data)


def get_installed_bundle_from_response_data(response_data):
    snapshot = response_data["installedPublishedAppSnapshot"]
    published = response_data.get("installedPublishedApp")

    snapshot = get_bundle_model_from_response_data(snapshot, variant="long")
    if published:
        published = get_bundle_model_from_response_data(published, variant="short")

    return InstalledBundle.validate({
        "installed_version": snapshot,
        "store_version": published
    })


def get_installation_check_model_from_response_data(response_data):

    parsed_data = {
        "success": response_data["success"],
        "installed_assets": response_data.get("importedAssets"),
        "missing_runner_type": response_data.get("missingRunnerTypes"),
        "required_runner_types": response_data.get("requiredRunnerTypes"),
    }

    conflicts_data = response_data.get("conflicts")
    if conflicts_data:
        parsed_data["conflicts"] = map_template_keys_to_contents_keys(conflicts_data)

    update_data = response_data.get("updateData")
    if update_data:
        parsed_data["update_data"] = map_update_keys_to_contents_keys(update_data)

    return InstallationCheck.validate(parsed_data)


def conflict_handling_to_install_payload(conflict_handling):
    conflict_dict = conflict_handling.dict()

    payload = {
        "appConfigNames": conflict_dict["hales"],
        "capabilityNames": conflict_dict["capabilities"],
        "infoStoreNames": conflict_dict["infostores"],
        "filePaths": conflict_dict["files"],
    }

    return payload
