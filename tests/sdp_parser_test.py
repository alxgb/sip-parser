import textwrap
from sip_parser.sdp_message import SdpMessage, SdpParseError
import pytest


def prepare_msg(msg: str):
    # Message lines must be CRLF-terminated and not indented
    return textwrap.dedent(msg.strip())


def keys_found(keys, obj):
    return set(keys).issubset(set(obj.keys()))


def keys_missing(keys, obj):
    existing_keys = obj.keys()
    for key in keys:
        if key in existing_keys:
            return False

    return True


def test_wrong_attribute_order_1():
    msg = """\
        v=0
        s=
        o=jdoe 2890844526 2890842807 IN IP4 10.47.16.5
    """

    with pytest.raises(SdpParseError, match=r"^Incorrect SDP header order detected$"):
        SdpMessage.from_string(prepare_msg(msg))


def test_minimum_required_elements():
    msg = """\
        v=0
        o=jdoe 2890844526 2890842807 IN IP4 10.47.16.5
        s=
        t=2873397496 2873404696
    """

    # Just interested in seeing we found the elements here
    sdp_msg = SdpMessage.from_string(prepare_msg(msg))
    assert keys_found(("v", "o", "s"), sdp_msg.session_description_fields)
    assert len(sdp_msg.time_descriptions)
    assert sdp_msg.time_descriptions[0].timing
    assert sdp_msg.time_descriptions[0].repeat_times == []


def test_no_undeclared_elements():
    # Verify that headers that aren't present aren't detected
    msg = """\
        v=0
        o=jdoe 2890844526 2890842807 IN IP4 10.47.16.5
        s=
        t=2873397496 2873404696
    """
    sdp_msg = SdpMessage.from_string(prepare_msg(msg))

    assert len(sdp_msg.time_descriptions) == 1
    assert len(sdp_msg.media_descriptions) == 0
    assert keys_missing(("a", "e", "i", "b", "u", "c"), sdp_msg.session_description_fields)


def test_example_full_sdp():
    # Example from rfc4566, Section 5
    msg = """\
        v=0
        o=jdoe 2890844526 2890842807 IN IP4 10.47.16.5
        s=SDP Seminar
        i=A Seminar on the session description protocol
        u=http://www.example.com/seminars/sdp.pdf
        e=j.doe@example.com (Jane Doe)
        c=IN IP4 224.2.17.12/127
        t=2873397496 2873404696
        a=recvonly
        m=audio 49170 RTP/AVP 0
        m=video 51372 RTP/AVP 99
        a=rtpmap:99 h263-1998/90000
    """

    sdp_msg = SdpMessage.from_string(prepare_msg(msg))
    # Verify everything was parsed correctly
    assert sdp_msg.session_description_fields["v"] == 0
    assert sdp_msg.session_description_fields["o"].username == "jdoe"
    assert sdp_msg.session_description_fields["o"].session_id == "2890844526"
    assert sdp_msg.session_description_fields["o"].session_type == "2890842807"
    assert sdp_msg.session_description_fields["o"].nettype == "IN"
    assert sdp_msg.session_description_fields["o"].addrtype == "IP4"
    assert sdp_msg.session_description_fields["o"].unicast_address == "10.47.16.5"
    assert sdp_msg.session_description_fields["s"] == "SDP Seminar"
    assert (
        sdp_msg.session_description_fields["i"] == "A Seminar on the session description protocol"
    )
    assert sdp_msg.session_description_fields["u"] == "http://www.example.com/seminars/sdp.pdf"
    assert sdp_msg.session_description_fields["e"] == "j.doe@example.com (Jane Doe)"
    assert sdp_msg.session_description_fields["c"].net_type == "IN"
    assert sdp_msg.session_description_fields["c"].addr_type == "IP4"
    assert sdp_msg.session_description_fields["c"].connection_address == "224.2.17.12/127"
    assert isinstance(sdp_msg.session_description_fields["a"], list)
    assert sdp_msg.session_description_fields["a"] == [("recvonly", True)]

    assert "o" in sdp_msg.session_description_fields
    assert "s" in sdp_msg.session_description_fields
    assert len(sdp_msg.time_descriptions) == 1
    assert sdp_msg.time_descriptions[0].timing
    assert sdp_msg.time_descriptions[0].repeat_times == []
    assert len(sdp_msg.media_descriptions) == 2
    assert sdp_msg.media_descriptions[1].media.media == "video"
    assert sdp_msg.media_descriptions[1].media.port == 51372
    assert sdp_msg.media_descriptions[1].media.number_of_ports == 1
    assert sdp_msg.media_descriptions[1].media.proto == "RTP/AVP"
    assert sdp_msg.media_descriptions[1].media_attributes == ("rtpmap", "99 h263-1998/90000")


def test_multiple_attr_fields_sdp():
    msg = """\
        v=0
        o=jdoe 2890844526 2890842807 IN IP4 10.47.16.5
        s=
        t=2873397496 2873404696
        a=prop
        a=prop2
        a=prop3:value
    """
    sdp_msg = SdpMessage.from_string(prepare_msg(msg))
    assert sdp_msg.session_description_fields["a"] == [
        ("prop", True),
        ("prop2", True),
        ("prop3", "value"),
    ]
