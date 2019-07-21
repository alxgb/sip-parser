from sip_parser.sdp_fields import (
    FieldRaw,
    MediaField,
    OriginField,
    TimingField,
    RepeatTimesField,
    TimeDescription,
    MediaDescription,
    ConnectionDataField,
)
from sip_parser.exceptions import SdpParseError


def parse_version(value):
    if value != "0":
        raise SdpParseError(
            f"Unexpected SDP protocol version number {value}. Only version 0 supported"
        )

    return 0


def parse_origin(value):
    subfields = value.split(" ")
    if len(subfields) != 6:
        raise SdpParseError("Unexpected format found while parsing origin header (o=)")

    return OriginField(*subfields)


def parse_media(value):
    subfields = value.split(" ")
    port_str = subfields[1]
    try:
        if "/" in port_str:
            port_parts = port_str.split("/")
            port = int(port_parts[0])
            number_of_ports = int(port_parts[1])
        else:
            number_of_ports = 1
            port = int(port_str)
    except ValueError:
        raise SdpParseError(f"Invalid media description's port sub-field found: <{port_str}>")

    return MediaField(
        media=subfields[0],
        port=port,
        number_of_ports=number_of_ports,
        proto=subfields[2],
        fmt=subfields[3],
    )


def parse_repeat(value):
    # TODO: Support SDP compressed repeat times using letters, transform to seconds
    subfields = value.split(" ")
    return RepeatTimesField(
        repeat_interval=subfields[0], active_duration=subfields[1], offsets=subfields[2:]
    )


def parse_media_attributes(value):
    subfields = value.split(":")
    if len(subfields) > 1:
        return (subfields[0], subfields[1])

    # Otherwise, it's a property attribute
    return (value, True)


parse_functions = {
    "v": parse_version,
    "o": parse_origin,
    "s": lambda val: val,
    "i": lambda val: val,
    "u": lambda val: val,
    "m": parse_media,
    "t": lambda val: TimingField(*val.split(" ")),
    "r": parse_repeat,
    "a": parse_media_attributes,
    "e": lambda val: val,
    "p": lambda val: val,
    "c": lambda val: ConnectionDataField(*val.split(" ")),
}
