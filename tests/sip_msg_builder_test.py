import textwrap
from sip_parser.sip_message import SipMessage, SipBuildError
import pytest


def prepare_msg(msg: str):
    # Message lines must be CRLF-terminated and not indented
    return textwrap.dedent(msg).replace("\n", "\r\n")


def test_build_basic_message():
    msg = """\
        METHODA somecooluri@example.com SIP/2.0
        Route: <sip:127.0.0.1:5060;lr>

        """

    parsed_message = SipMessage.from_string(prepare_msg(msg))
    sip_message = SipMessage.from_dict(
        {
            "method": "METHODA",
            "uri": "somecooluri@example.com",
            "version": "2.0",
            "headers": {"route": "<sip:127.0.0.1:5060;lr>"},
        }
    )

    assert parsed_message.stringify() == sip_message.stringify()


def test_build_uri_full():
    msg = """\
        METHODA somecooluri@example.com SIP/2.0
        Route: <sip:127.0.0.1:5060;lr>

        """

    parsed_message = SipMessage.from_string(prepare_msg(msg))
    sip_message = SipMessage.from_dict(
        {
            "method": "METHODA",
            "uri": "somecooluri@example.com",
            "version": "2.0",
            "headers": {
                "route": {
                    "uri": {
                        "scheme": "sip",
                        "host": "127.0.0.1",
                        "port": 5060,
                        "params": {"lr": None},
                    }
                }
            },
        }
    )

    assert parsed_message.stringify() == sip_message.stringify()


def test_multiple_routes():
    msg = """\
        METHODA somecooluri@example.com SIP/2.0
        Route: <sip:127.0.0.1:5060;lr>
        Route: <sip:somehost:5060;plain-uri>

        """

    parsed_message = SipMessage.from_string(prepare_msg(msg))
    sip_message = SipMessage.from_dict(
        {
            "method": "METHODA",
            "uri": "somecooluri@example.com",
            "version": "2.0",
            "headers": {
                "route": [
                    {
                        "uri": {
                            "scheme": "sip",
                            "host": "127.0.0.1",
                            "port": 5060,
                            "params": {"lr": None},
                        }
                    },
                    "<sip:somehost:5060;plain-uri>",
                ]
            },
        }
    )

    assert parsed_message.stringify() == sip_message.stringify()


def test_response_params():
    sip_msg = SipMessage.from_dict({"status": 200, "reason": "OK", "headers": {"contact": "*"}})

    assert sip_msg.type == SipMessage.TYPE_RESPONSE
    assert sip_msg.status == 200
    assert sip_msg.reason == "OK"


def test_request_params():
    sip_msg = SipMessage.from_dict(
        {"method": "SOMEMETHOD", "uri": "sip:hello@bye.com", "headers": {"contact": "*"}}
    )

    assert sip_msg.type == SipMessage.TYPE_REQUEST
    assert sip_msg.uri == "sip:hello@bye.com"
    assert sip_msg.method == "SOMEMETHOD"


def test_invalid_request_response_mix():
    with pytest.raises(SipBuildError, match="^Found.*[Rr]equest.*properties.*[Rr]esponse.*"):
        SipMessage.from_dict(
            {
                "status": 200,
                "reason": "OK",
                "method": "BAD",
                "headers": {"route": "<sip:127.0.0.1:5060;lr>"},
            }
        )

    with pytest.raises(SipBuildError, match="^Found.*[Rr]esponse.*properties.*[Rr]equest.*"):
        SipMessage.from_dict(
            {
                "method": "GOOD",
                "uri": "sip:example@world.com",
                "reason": "NOTOK",
                "headers": {"route": "<sip:127.0.0.1:5060;lr>"},
            }
        )
