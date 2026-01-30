from datetime import datetime
from typing import List, Optional
import uuid as uuid_lib

from pydantic import BaseModel, Field, field_validator

from drax_sdk.model.dynamic import BaseValueObject


class ActivatorType:
    EVENT = "event"
    STATE = "state"
    SCHEDULED = "scheduled"


class Activator(BaseModel):
    type: str = Field(alias="type")
    selector: Optional[str] = Field(default=None, alias="selector")

    class Config:
        populate_by_name = True


class RuleVariable(BaseModel):
    name: str = Field(alias="name")
    label: str = Field(alias="label")
    value: str = Field(alias="value")

    class Config:
        populate_by_name = True


class ValuedDescriptor(BaseModel):
    variables: List[RuleVariable] = Field(alias="variables")

    class Config:
        populate_by_name = True


class ConditionDescriptor(ValuedDescriptor):
    uuid: str = Field(default_factory=lambda: str(uuid_lib.uuid4()), alias="uuid")
    type: str = Field(alias="type")

    class Config:
        populate_by_name = True


class ActionDescriptor(ValuedDescriptor):
    uuid: str = Field(default_factory=lambda: str(uuid_lib.uuid4()), alias="uuid")
    type: str = Field(alias="type")

    class Config:
        populate_by_name = True


class RuleDescriptor(BaseModel):
    id: Optional[str] = Field(default=None, alias="id")
    uuid: str = Field(default_factory=lambda: str(uuid_lib.uuid4()), alias="uuid")
    priority: int = Field(alias="priority")
    conditions: List[ConditionDescriptor] = Field(alias="conditions")
    actions: List[ActionDescriptor] = Field(alias="actions")
    is_or: bool = Field(alias="or")

    class Config:
        populate_by_name = True


class Automation(BaseModel):
    id: Optional[str] = Field(default=None, alias="id")
    code: str = Field(default="", alias="code")
    activator: Activator = Field(alias="activator")
    rules: List[RuleDescriptor] = Field(alias="rules")
    last_execution: Optional[datetime] = Field(alias="lastExecution", default=None)
    description: str = Field(alias="description")
    project_id: str = Field(alias="projectId")
    active: bool = Field(alias="active")
    last_activation: Optional[datetime] = Field(alias="lastActivation", default=None)
    idle_time_from_last_activation: int = Field(alias="idleTimeFromLastActivation", default=0)
    extras: Optional[BaseValueObject] = Field(alias="extras", default=None)
    modified: Optional[int] = Field(default=None, alias="modified")
    log_enabled: bool = Field(default=False, alias="logEnabled")

    class Config:
        populate_by_name = True
