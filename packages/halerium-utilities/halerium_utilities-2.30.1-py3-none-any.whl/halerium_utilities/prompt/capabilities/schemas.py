from string import ascii_letters, digits
from typing import Dict, List, Literal, Optional
from pydantic import BaseModel, Field, model_validator


class ParameterModel(BaseModel):
    type: Literal["string", "number", "boolean", "object"]
    description: str = ""


class ParametersModel(BaseModel):
    properties: Optional[Dict[str, ParameterModel]] = Field(default_factory=dict)
    required: Optional[List[str]] = Field(default_factory=list)


class FunctionModel(BaseModel):
    function: str
    pretty_name: str = None
    group: Optional[str] = None
    description: str
    parameters: ParametersModel = Field(default_factory=ParametersModel)
    config_parameters: Dict[str, str] = Field(default_factory=dict)

    @model_validator(mode='before')
    def set_pretty_name(cls, values):
        if not values.get("pretty_name"):
            values['pretty_name'] = values.get('function')
        return values

    @model_validator(mode='before')
    def check_function_name(cls, values):
        function_name = values.get("function")
        if len(function_name) > (64-26):  # we reserve 26 chars for capability group id
            raise ValueError(
                f"'function' '{function_name}' is invalid. "
                "It must be at most 38 characters long.")
        allows_start = ascii_letters + "_"
        allowed = ascii_letters + digits + "_"
        if not all(c in allowed for c in function_name):
            raise ValueError(
                f"'function' '{function_name}' is invalid. "
                "It must only contain ascii letters, numbers, underscores.")

        if not function_name[0] in allows_start:
            raise ValueError(
                f"'function' '{function_name}' is invalid. "
                "It must start with an ascii letter or underscores.")

        return values


class SetupCommand(BaseModel):
    setupCommands: List[str] = Field(default_factory=list)


# Used for validation for create and get capability group methods
class CapabilityGroupModel(BaseModel):
    name: str = ""
    displayName: str = ""
    runnerType: Literal['nano', 'small', 'standard', 'performance', 'highend', 'gpu'] = "nano"
    sharedRunner: bool = False
    setupCommand: SetupCommand = Field(default_factory=SetupCommand)
    sourceCode: Optional[str] = None
    functions: List[FunctionModel] = Field(default_factory=list)


# Used for validation for update capability group method (everything is optional)
class UpdateCapabilityGroupModel(BaseModel):
    name: Optional[str] = None
    displayName: Optional[str] = None
    runnerType: Optional[Literal['nano', 'small', 'standard', 'performance', 'highend', 'gpu']] = None
    sharedRunner: Optional[bool] = None
    setupCommand: Optional[SetupCommand] = None
    sourceCode: Optional[str] = None
    functions: Optional[List[FunctionModel]] = None
