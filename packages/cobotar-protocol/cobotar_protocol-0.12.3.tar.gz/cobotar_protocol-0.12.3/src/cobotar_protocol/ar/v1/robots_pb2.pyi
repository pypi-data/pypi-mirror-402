from ar.v1 import property_pb2 as _property_pb2
from buf.validate import validate_pb2 as _validate_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class RobotType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    ROBOT_TYPE_UNSPECIFIED: _ClassVar[RobotType]
    ROBOT_TYPE_UR3E: _ClassVar[RobotType]
    ROBOT_TYPE_UR5E: _ClassVar[RobotType]
    ROBOT_TYPE_UR10E: _ClassVar[RobotType]
    ROBOT_TYPE_KUKA_IIWA: _ClassVar[RobotType]

class EndEffectorType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    END_EFFECTOR_TYPE_UNSPECIFIED: _ClassVar[EndEffectorType]
    END_EFFECTOR_TYPE_EMPTY: _ClassVar[EndEffectorType]
    END_EFFECTOR_TYPE_ROBOTIQ_HAND_E: _ClassVar[EndEffectorType]
    END_EFFECTOR_TYPE_CUSTOM_MOUNT: _ClassVar[EndEffectorType]

class RobotDriverType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    ROBOT_DRIVER_TYPE_UNSPECIFIED: _ClassVar[RobotDriverType]
    ROBOT_DRIVER_TYPE_UR: _ClassVar[RobotDriverType]
ROBOT_TYPE_UNSPECIFIED: RobotType
ROBOT_TYPE_UR3E: RobotType
ROBOT_TYPE_UR5E: RobotType
ROBOT_TYPE_UR10E: RobotType
ROBOT_TYPE_KUKA_IIWA: RobotType
END_EFFECTOR_TYPE_UNSPECIFIED: EndEffectorType
END_EFFECTOR_TYPE_EMPTY: EndEffectorType
END_EFFECTOR_TYPE_ROBOTIQ_HAND_E: EndEffectorType
END_EFFECTOR_TYPE_CUSTOM_MOUNT: EndEffectorType
ROBOT_DRIVER_TYPE_UNSPECIFIED: RobotDriverType
ROBOT_DRIVER_TYPE_UR: RobotDriverType

class RobotMessage(_message.Message):
    __slots__ = ("id", "name", "icon", "description", "robot_type", "end_effector_type", "robot_driver_type", "properties")
    ID_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    ICON_FIELD_NUMBER: _ClassVar[int]
    DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
    ROBOT_TYPE_FIELD_NUMBER: _ClassVar[int]
    END_EFFECTOR_TYPE_FIELD_NUMBER: _ClassVar[int]
    ROBOT_DRIVER_TYPE_FIELD_NUMBER: _ClassVar[int]
    PROPERTIES_FIELD_NUMBER: _ClassVar[int]
    id: str
    name: str
    icon: str
    description: str
    robot_type: RobotType
    end_effector_type: EndEffectorType
    robot_driver_type: RobotDriverType
    properties: _containers.RepeatedCompositeFieldContainer[_property_pb2.Property]
    def __init__(self, id: _Optional[str] = ..., name: _Optional[str] = ..., icon: _Optional[str] = ..., description: _Optional[str] = ..., robot_type: _Optional[_Union[RobotType, str]] = ..., end_effector_type: _Optional[_Union[EndEffectorType, str]] = ..., robot_driver_type: _Optional[_Union[RobotDriverType, str]] = ..., properties: _Optional[_Iterable[_Union[_property_pb2.Property, _Mapping]]] = ...) -> None: ...

class RobotMessages(_message.Message):
    __slots__ = ("robots",)
    ROBOTS_FIELD_NUMBER: _ClassVar[int]
    robots: _containers.RepeatedCompositeFieldContainer[RobotMessage]
    def __init__(self, robots: _Optional[_Iterable[_Union[RobotMessage, _Mapping]]] = ...) -> None: ...
