from google.protobuf import timestamp_pb2 as _timestamp_pb2
from powerpay_protos import measurement_pb2 as _measurement_pb2
from powerpay_protos import device_pb2 as _device_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class Telemetry(_message.Message):
    __slots__ = ("timestamp", "device", "measurement")
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    DEVICE_FIELD_NUMBER: _ClassVar[int]
    MEASUREMENT_FIELD_NUMBER: _ClassVar[int]
    timestamp: _timestamp_pb2.Timestamp
    device: _device_pb2.Device
    measurement: _containers.RepeatedCompositeFieldContainer[_measurement_pb2.Measurement]
    def __init__(self, timestamp: _Optional[_Union[_timestamp_pb2.Timestamp, _Mapping]] = ..., device: _Optional[_Union[_device_pb2.Device, _Mapping]] = ..., measurement: _Optional[_Iterable[_Union[_measurement_pb2.Measurement, _Mapping]]] = ...) -> None: ...
