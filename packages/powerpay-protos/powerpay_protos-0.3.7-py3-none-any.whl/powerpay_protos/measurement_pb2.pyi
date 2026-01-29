from google.protobuf import timestamp_pb2 as _timestamp_pb2
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class EnergyUnit(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    ENERGY_UNIT_NOT_SET: _ClassVar[EnergyUnit]
    WATT_HOUR: _ClassVar[EnergyUnit]
    KILO_WATT_HOUR: _ClassVar[EnergyUnit]
    MEGA_WATT_HOUR: _ClassVar[EnergyUnit]

class PowerUnit(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    POWER_UNIT_NOT_SET: _ClassVar[PowerUnit]
    WATT: _ClassVar[PowerUnit]
    KILO_WATT: _ClassVar[PowerUnit]
    MEGA_WATT: _ClassVar[PowerUnit]
ENERGY_UNIT_NOT_SET: EnergyUnit
WATT_HOUR: EnergyUnit
KILO_WATT_HOUR: EnergyUnit
MEGA_WATT_HOUR: EnergyUnit
POWER_UNIT_NOT_SET: PowerUnit
WATT: PowerUnit
KILO_WATT: PowerUnit
MEGA_WATT: PowerUnit

class Measurement(_message.Message):
    __slots__ = ("energy", "power", "state", "session", "signal_strength", "rfid_event")
    ENERGY_FIELD_NUMBER: _ClassVar[int]
    POWER_FIELD_NUMBER: _ClassVar[int]
    STATE_FIELD_NUMBER: _ClassVar[int]
    SESSION_FIELD_NUMBER: _ClassVar[int]
    SIGNAL_STRENGTH_FIELD_NUMBER: _ClassVar[int]
    RFID_EVENT_FIELD_NUMBER: _ClassVar[int]
    energy: Energy
    power: Power
    state: State
    session: Session
    signal_strength: SignalStrength
    rfid_event: RFIDEvent
    def __init__(self, energy: _Optional[_Union[Energy, _Mapping]] = ..., power: _Optional[_Union[Power, _Mapping]] = ..., state: _Optional[_Union[State, _Mapping]] = ..., session: _Optional[_Union[Session, _Mapping]] = ..., signal_strength: _Optional[_Union[SignalStrength, _Mapping]] = ..., rfid_event: _Optional[_Union[RFIDEvent, _Mapping]] = ...) -> None: ...

class Energy(_message.Message):
    __slots__ = ("value", "unit", "type")
    class EnergyType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        ENERGY_MEASUREMENT_TYPE_NOT_SET: _ClassVar[Energy.EnergyType]
        LIFETIME: _ClassVar[Energy.EnergyType]
        SESSION: _ClassVar[Energy.EnergyType]
    ENERGY_MEASUREMENT_TYPE_NOT_SET: Energy.EnergyType
    LIFETIME: Energy.EnergyType
    SESSION: Energy.EnergyType
    VALUE_FIELD_NUMBER: _ClassVar[int]
    UNIT_FIELD_NUMBER: _ClassVar[int]
    TYPE_FIELD_NUMBER: _ClassVar[int]
    value: int
    unit: EnergyUnit
    type: Energy.EnergyType
    def __init__(self, value: _Optional[int] = ..., unit: _Optional[_Union[EnergyUnit, str]] = ..., type: _Optional[_Union[Energy.EnergyType, str]] = ...) -> None: ...

class Power(_message.Message):
    __slots__ = ("value", "unit")
    VALUE_FIELD_NUMBER: _ClassVar[int]
    UNIT_FIELD_NUMBER: _ClassVar[int]
    value: float
    unit: PowerUnit
    def __init__(self, value: _Optional[float] = ..., unit: _Optional[_Union[PowerUnit, str]] = ...) -> None: ...

class State(_message.Message):
    __slots__ = ("energized", "online", "connected")
    class EnergizedState(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        ENERGIZED_STATE_UNDEFINED: _ClassVar[State.EnergizedState]
        ENERGIZED: _ClassVar[State.EnergizedState]
        DE_ENERGIZED: _ClassVar[State.EnergizedState]
    ENERGIZED_STATE_UNDEFINED: State.EnergizedState
    ENERGIZED: State.EnergizedState
    DE_ENERGIZED: State.EnergizedState
    class OnlineState(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        ONLINE_STATE_UNDEFINED: _ClassVar[State.OnlineState]
        ONLINE: _ClassVar[State.OnlineState]
        OFFLINE: _ClassVar[State.OnlineState]
    ONLINE_STATE_UNDEFINED: State.OnlineState
    ONLINE: State.OnlineState
    OFFLINE: State.OnlineState
    class ConnectedState(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        CONNECTED_STATE_UNDEFINED: _ClassVar[State.ConnectedState]
        CONNECTED: _ClassVar[State.ConnectedState]
        DISCONNECTED: _ClassVar[State.ConnectedState]
    CONNECTED_STATE_UNDEFINED: State.ConnectedState
    CONNECTED: State.ConnectedState
    DISCONNECTED: State.ConnectedState
    ENERGIZED_FIELD_NUMBER: _ClassVar[int]
    ONLINE_FIELD_NUMBER: _ClassVar[int]
    CONNECTED_FIELD_NUMBER: _ClassVar[int]
    energized: State.EnergizedState
    online: State.OnlineState
    connected: State.ConnectedState
    def __init__(self, energized: _Optional[_Union[State.EnergizedState, str]] = ..., online: _Optional[_Union[State.OnlineState, str]] = ..., connected: _Optional[_Union[State.ConnectedState, str]] = ...) -> None: ...

class Session(_message.Message):
    __slots__ = ("start", "end", "session_consumed_energy", "meter_start", "meter_end")
    START_FIELD_NUMBER: _ClassVar[int]
    END_FIELD_NUMBER: _ClassVar[int]
    SESSION_CONSUMED_ENERGY_FIELD_NUMBER: _ClassVar[int]
    METER_START_FIELD_NUMBER: _ClassVar[int]
    METER_END_FIELD_NUMBER: _ClassVar[int]
    start: _timestamp_pb2.Timestamp
    end: _timestamp_pb2.Timestamp
    session_consumed_energy: Energy
    meter_start: Energy
    meter_end: Energy
    def __init__(self, start: _Optional[_Union[_timestamp_pb2.Timestamp, _Mapping]] = ..., end: _Optional[_Union[_timestamp_pb2.Timestamp, _Mapping]] = ..., session_consumed_energy: _Optional[_Union[Energy, _Mapping]] = ..., meter_start: _Optional[_Union[Energy, _Mapping]] = ..., meter_end: _Optional[_Union[Energy, _Mapping]] = ...) -> None: ...

class SignalStrength(_message.Message):
    __slots__ = ("value", "unit", "radio_type")
    class SignalStrengthUnit(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        SIGNAL_STRENGTH_UNIT_NOT_SET: _ClassVar[SignalStrength.SignalStrengthUnit]
        DECIBEL_MILLIWATT: _ClassVar[SignalStrength.SignalStrengthUnit]
        RECEIVED_SIGNAL_STRENGTH_INDICATOR: _ClassVar[SignalStrength.SignalStrengthUnit]
        SIGNAL_NOISE_RATIO: _ClassVar[SignalStrength.SignalStrengthUnit]
    SIGNAL_STRENGTH_UNIT_NOT_SET: SignalStrength.SignalStrengthUnit
    DECIBEL_MILLIWATT: SignalStrength.SignalStrengthUnit
    RECEIVED_SIGNAL_STRENGTH_INDICATOR: SignalStrength.SignalStrengthUnit
    SIGNAL_NOISE_RATIO: SignalStrength.SignalStrengthUnit
    class RadioType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        RADIO_TYPE_NOT_SET: _ClassVar[SignalStrength.RadioType]
        CELLULAR: _ClassVar[SignalStrength.RadioType]
        WIFI: _ClassVar[SignalStrength.RadioType]
        LORA: _ClassVar[SignalStrength.RadioType]
        LOCAL: _ClassVar[SignalStrength.RadioType]
    RADIO_TYPE_NOT_SET: SignalStrength.RadioType
    CELLULAR: SignalStrength.RadioType
    WIFI: SignalStrength.RadioType
    LORA: SignalStrength.RadioType
    LOCAL: SignalStrength.RadioType
    VALUE_FIELD_NUMBER: _ClassVar[int]
    UNIT_FIELD_NUMBER: _ClassVar[int]
    RADIO_TYPE_FIELD_NUMBER: _ClassVar[int]
    value: float
    unit: SignalStrength.SignalStrengthUnit
    radio_type: SignalStrength.RadioType
    def __init__(self, value: _Optional[float] = ..., unit: _Optional[_Union[SignalStrength.SignalStrengthUnit, str]] = ..., radio_type: _Optional[_Union[SignalStrength.RadioType, str]] = ...) -> None: ...

class RFIDEvent(_message.Message):
    __slots__ = ("uid",)
    UID_FIELD_NUMBER: _ClassVar[int]
    uid: bytes
    def __init__(self, uid: _Optional[bytes] = ...) -> None: ...
