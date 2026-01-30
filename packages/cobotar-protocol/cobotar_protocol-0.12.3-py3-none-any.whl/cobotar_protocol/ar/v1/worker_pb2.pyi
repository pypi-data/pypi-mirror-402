from ar.v1 import property_pb2 as _property_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class WorkerType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    WORKER_TYPE_UNSPECIFIED: _ClassVar[WorkerType]
    WORKER_TYPE_NOVICE: _ClassVar[WorkerType]
    WORKER_TYPE_INTERMEDIATE: _ClassVar[WorkerType]
    WORKER_TYPE_EXPERT: _ClassVar[WorkerType]

class WorkerPermission(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    WORKER_PERMISSION_UNSPECIFIED: _ClassVar[WorkerPermission]
    WORKER_PERMISSION_NONE: _ClassVar[WorkerPermission]
    WORKER_PERMISSION_COSMETIC: _ClassVar[WorkerPermission]
    WORKER_PERMISSION_FULL: _ClassVar[WorkerPermission]
WORKER_TYPE_UNSPECIFIED: WorkerType
WORKER_TYPE_NOVICE: WorkerType
WORKER_TYPE_INTERMEDIATE: WorkerType
WORKER_TYPE_EXPERT: WorkerType
WORKER_PERMISSION_UNSPECIFIED: WorkerPermission
WORKER_PERMISSION_NONE: WorkerPermission
WORKER_PERMISSION_COSMETIC: WorkerPermission
WORKER_PERMISSION_FULL: WorkerPermission

class WorkerMessage(_message.Message):
    __slots__ = ("id", "name", "icon", "description", "type", "permission", "properties")
    ID_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    ICON_FIELD_NUMBER: _ClassVar[int]
    DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
    TYPE_FIELD_NUMBER: _ClassVar[int]
    PERMISSION_FIELD_NUMBER: _ClassVar[int]
    PROPERTIES_FIELD_NUMBER: _ClassVar[int]
    id: str
    name: str
    icon: str
    description: str
    type: WorkerType
    permission: WorkerPermission
    properties: _containers.RepeatedCompositeFieldContainer[_property_pb2.Property]
    def __init__(self, id: _Optional[str] = ..., name: _Optional[str] = ..., icon: _Optional[str] = ..., description: _Optional[str] = ..., type: _Optional[_Union[WorkerType, str]] = ..., permission: _Optional[_Union[WorkerPermission, str]] = ..., properties: _Optional[_Iterable[_Union[_property_pb2.Property, _Mapping]]] = ...) -> None: ...

class WorkerMessages(_message.Message):
    __slots__ = ("workers",)
    WORKERS_FIELD_NUMBER: _ClassVar[int]
    workers: _containers.RepeatedCompositeFieldContainer[WorkerMessage]
    def __init__(self, workers: _Optional[_Iterable[_Union[WorkerMessage, _Mapping]]] = ...) -> None: ...
