from google.protobuf import struct_pb2 as _struct_pb2
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class IntegrationType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    INTEGRATION_TYPE_UNDEFINED: _ClassVar[IntegrationType]
    CHIRPSTACK: _ClassVar[IntegrationType]
    EASEE: _ClassVar[IntegrationType]
    NETMORE: _ClassVar[IntegrationType]
    OCPP: _ClassVar[IntegrationType]
    MQTT: _ClassVar[IntegrationType]
    THINGPARK: _ClassVar[IntegrationType]
    RESIOT: _ClassVar[IntegrationType]
INTEGRATION_TYPE_UNDEFINED: IntegrationType
CHIRPSTACK: IntegrationType
EASEE: IntegrationType
NETMORE: IntegrationType
OCPP: IntegrationType
MQTT: IntegrationType
THINGPARK: IntegrationType
RESIOT: IntegrationType

class IntegrationTemplateRequest(_message.Message):
    __slots__ = ("integration_type",)
    INTEGRATION_TYPE_FIELD_NUMBER: _ClassVar[int]
    integration_type: IntegrationType
    def __init__(self, integration_type: _Optional[_Union[IntegrationType, str]] = ...) -> None: ...

class IntegrationTemplate(_message.Message):
    __slots__ = ("integration_config", "integration_properties", "device_config")
    INTEGRATION_CONFIG_FIELD_NUMBER: _ClassVar[int]
    INTEGRATION_PROPERTIES_FIELD_NUMBER: _ClassVar[int]
    DEVICE_CONFIG_FIELD_NUMBER: _ClassVar[int]
    integration_config: Schema
    integration_properties: Schema
    device_config: Schema
    def __init__(self, integration_config: _Optional[_Union[Schema, _Mapping]] = ..., integration_properties: _Optional[_Union[Schema, _Mapping]] = ..., device_config: _Optional[_Union[Schema, _Mapping]] = ...) -> None: ...

class Schema(_message.Message):
    __slots__ = ("ui_schema", "json_schema")
    UI_SCHEMA_FIELD_NUMBER: _ClassVar[int]
    JSON_SCHEMA_FIELD_NUMBER: _ClassVar[int]
    ui_schema: _struct_pb2.Struct
    json_schema: _struct_pb2.Struct
    def __init__(self, ui_schema: _Optional[_Union[_struct_pb2.Struct, _Mapping]] = ..., json_schema: _Optional[_Union[_struct_pb2.Struct, _Mapping]] = ...) -> None: ...

class HealthCheckResponse(_message.Message):
    __slots__ = ("status", "message")
    STATUS_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    status: bool
    message: str
    def __init__(self, status: bool = ..., message: _Optional[str] = ...) -> None: ...

class Integration(_message.Message):
    __slots__ = ("integration_type", "integration_name", "integration_config", "integration_properties")
    INTEGRATION_TYPE_FIELD_NUMBER: _ClassVar[int]
    INTEGRATION_NAME_FIELD_NUMBER: _ClassVar[int]
    INTEGRATION_CONFIG_FIELD_NUMBER: _ClassVar[int]
    INTEGRATION_PROPERTIES_FIELD_NUMBER: _ClassVar[int]
    integration_type: IntegrationType
    integration_name: str
    integration_config: _struct_pb2.Struct
    integration_properties: _struct_pb2.Struct
    def __init__(self, integration_type: _Optional[_Union[IntegrationType, str]] = ..., integration_name: _Optional[str] = ..., integration_config: _Optional[_Union[_struct_pb2.Struct, _Mapping]] = ..., integration_properties: _Optional[_Union[_struct_pb2.Struct, _Mapping]] = ...) -> None: ...
