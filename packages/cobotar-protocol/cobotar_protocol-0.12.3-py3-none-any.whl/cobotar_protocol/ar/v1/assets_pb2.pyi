from ar.v1 import property_pb2 as _property_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class AssetType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    ASSET_TYPE_UNSPECIFIED: _ClassVar[AssetType]
    ASSET_TYPE_CAMERA: _ClassVar[AssetType]
    ASSET_TYPE_LIGHT: _ClassVar[AssetType]
    ASSET_TYPE_CONVEYOR: _ClassVar[AssetType]

class AssetDriverType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    ASSET_DRIVER_TYPE_UNSPECIFIED: _ClassVar[AssetDriverType]
    ASSET_DRIVER_TYPE_DEFAULT: _ClassVar[AssetDriverType]
ASSET_TYPE_UNSPECIFIED: AssetType
ASSET_TYPE_CAMERA: AssetType
ASSET_TYPE_LIGHT: AssetType
ASSET_TYPE_CONVEYOR: AssetType
ASSET_DRIVER_TYPE_UNSPECIFIED: AssetDriverType
ASSET_DRIVER_TYPE_DEFAULT: AssetDriverType

class AssetMessage(_message.Message):
    __slots__ = ("id", "name", "icon", "description", "type", "asset_driver_type", "properties")
    ID_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    ICON_FIELD_NUMBER: _ClassVar[int]
    DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
    TYPE_FIELD_NUMBER: _ClassVar[int]
    ASSET_DRIVER_TYPE_FIELD_NUMBER: _ClassVar[int]
    PROPERTIES_FIELD_NUMBER: _ClassVar[int]
    id: str
    name: str
    icon: str
    description: str
    type: AssetType
    asset_driver_type: AssetDriverType
    properties: _containers.RepeatedCompositeFieldContainer[_property_pb2.Property]
    def __init__(self, id: _Optional[str] = ..., name: _Optional[str] = ..., icon: _Optional[str] = ..., description: _Optional[str] = ..., type: _Optional[_Union[AssetType, str]] = ..., asset_driver_type: _Optional[_Union[AssetDriverType, str]] = ..., properties: _Optional[_Iterable[_Union[_property_pb2.Property, _Mapping]]] = ...) -> None: ...

class AssetMessages(_message.Message):
    __slots__ = ("assets",)
    ASSETS_FIELD_NUMBER: _ClassVar[int]
    assets: _containers.RepeatedCompositeFieldContainer[AssetMessage]
    def __init__(self, assets: _Optional[_Iterable[_Union[AssetMessage, _Mapping]]] = ...) -> None: ...
