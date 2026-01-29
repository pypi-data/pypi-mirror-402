from google.protobuf import struct_pb2 as _struct_pb2
from google.protobuf import timestamp_pb2 as _timestamp_pb2
from powerpay_protos import integration_pb2 as _integration_pb2
from powerpay_protos import measurement_pb2 as _measurement_pb2
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class OperationStatus(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    OPERATION_STATUS_UNDEFINED: _ClassVar[OperationStatus]
    SUCCESS: _ClassVar[OperationStatus]
    FAILURE: _ClassVar[OperationStatus]
    TIMEOUT: _ClassVar[OperationStatus]
    NOT_FOUND: _ClassVar[OperationStatus]
    NOT_SUPPORTED: _ClassVar[OperationStatus]
    INVALID: _ClassVar[OperationStatus]

class DeviceControlType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    DEVICE_CONTROL_UNDEFINED: _ClassVar[DeviceControlType]
    ENERGIZE: _ClassVar[DeviceControlType]
    DE_ENERGIZE: _ClassVar[DeviceControlType]
    RESTART: _ClassVar[DeviceControlType]
    READ_SERIAL_NUMBER: _ClassVar[DeviceControlType]
OPERATION_STATUS_UNDEFINED: OperationStatus
SUCCESS: OperationStatus
FAILURE: OperationStatus
TIMEOUT: OperationStatus
NOT_FOUND: OperationStatus
NOT_SUPPORTED: OperationStatus
INVALID: OperationStatus
DEVICE_CONTROL_UNDEFINED: DeviceControlType
ENERGIZE: DeviceControlType
DE_ENERGIZE: DeviceControlType
RESTART: DeviceControlType
READ_SERIAL_NUMBER: DeviceControlType

class Device(_message.Message):
    __slots__ = ("native_id", "integration_type", "outlet_index", "integration_name")
    NATIVE_ID_FIELD_NUMBER: _ClassVar[int]
    INTEGRATION_TYPE_FIELD_NUMBER: _ClassVar[int]
    OUTLET_INDEX_FIELD_NUMBER: _ClassVar[int]
    INTEGRATION_NAME_FIELD_NUMBER: _ClassVar[int]
    native_id: str
    integration_type: _integration_pb2.IntegrationType
    outlet_index: int
    integration_name: str
    def __init__(self, native_id: _Optional[str] = ..., integration_type: _Optional[_Union[_integration_pb2.IntegrationType, str]] = ..., outlet_index: _Optional[int] = ..., integration_name: _Optional[str] = ...) -> None: ...

class DeviceRequest(_message.Message):
    __slots__ = ("integration", "native_id", "outlet_index", "config", "properties")
    INTEGRATION_FIELD_NUMBER: _ClassVar[int]
    NATIVE_ID_FIELD_NUMBER: _ClassVar[int]
    OUTLET_INDEX_FIELD_NUMBER: _ClassVar[int]
    CONFIG_FIELD_NUMBER: _ClassVar[int]
    PROPERTIES_FIELD_NUMBER: _ClassVar[int]
    integration: _integration_pb2.Integration
    native_id: str
    outlet_index: int
    config: _struct_pb2.Struct
    properties: _struct_pb2.Struct
    def __init__(self, integration: _Optional[_Union[_integration_pb2.Integration, _Mapping]] = ..., native_id: _Optional[str] = ..., outlet_index: _Optional[int] = ..., config: _Optional[_Union[_struct_pb2.Struct, _Mapping]] = ..., properties: _Optional[_Union[_struct_pb2.Struct, _Mapping]] = ...) -> None: ...

class DeviceResponse(_message.Message):
    __slots__ = ("device", "status", "message")
    DEVICE_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    device: Device
    status: OperationStatus
    message: str
    def __init__(self, device: _Optional[_Union[Device, _Mapping]] = ..., status: _Optional[_Union[OperationStatus, str]] = ..., message: _Optional[str] = ...) -> None: ...

class DeviceControlCommand(_message.Message):
    __slots__ = ("type", "properties")
    TYPE_FIELD_NUMBER: _ClassVar[int]
    PROPERTIES_FIELD_NUMBER: _ClassVar[int]
    type: DeviceControlType
    properties: _struct_pb2.Struct
    def __init__(self, type: _Optional[_Union[DeviceControlType, str]] = ..., properties: _Optional[_Union[_struct_pb2.Struct, _Mapping]] = ...) -> None: ...

class DeviceControlRequest(_message.Message):
    __slots__ = ("device", "command")
    DEVICE_FIELD_NUMBER: _ClassVar[int]
    COMMAND_FIELD_NUMBER: _ClassVar[int]
    device: DeviceRequest
    command: DeviceControlCommand
    def __init__(self, device: _Optional[_Union[DeviceRequest, _Mapping]] = ..., command: _Optional[_Union[DeviceControlCommand, _Mapping]] = ...) -> None: ...

class CreateDeviceRequest(_message.Message):
    __slots__ = ("device", "outlet_count")
    DEVICE_FIELD_NUMBER: _ClassVar[int]
    OUTLET_COUNT_FIELD_NUMBER: _ClassVar[int]
    device: DeviceRequest
    outlet_count: int
    def __init__(self, device: _Optional[_Union[DeviceRequest, _Mapping]] = ..., outlet_count: _Optional[int] = ...) -> None: ...

class UpdateDeviceRequest(_message.Message):
    __slots__ = ("device",)
    DEVICE_FIELD_NUMBER: _ClassVar[int]
    device: DeviceRequest
    def __init__(self, device: _Optional[_Union[DeviceRequest, _Mapping]] = ...) -> None: ...

class DeleteDeviceRequest(_message.Message):
    __slots__ = ("device",)
    DEVICE_FIELD_NUMBER: _ClassVar[int]
    device: DeviceRequest
    def __init__(self, device: _Optional[_Union[DeviceRequest, _Mapping]] = ...) -> None: ...

class DeviceStatusRequest(_message.Message):
    __slots__ = ("device",)
    DEVICE_FIELD_NUMBER: _ClassVar[int]
    device: DeviceRequest
    def __init__(self, device: _Optional[_Union[DeviceRequest, _Mapping]] = ...) -> None: ...

class DeviceStatusResponse(_message.Message):
    __slots__ = ("device", "state", "last_seen")
    DEVICE_FIELD_NUMBER: _ClassVar[int]
    STATE_FIELD_NUMBER: _ClassVar[int]
    LAST_SEEN_FIELD_NUMBER: _ClassVar[int]
    device: Device
    state: _measurement_pb2.State
    last_seen: _timestamp_pb2.Timestamp
    def __init__(self, device: _Optional[_Union[Device, _Mapping]] = ..., state: _Optional[_Union[_measurement_pb2.State, _Mapping]] = ..., last_seen: _Optional[_Union[_timestamp_pb2.Timestamp, _Mapping]] = ...) -> None: ...
