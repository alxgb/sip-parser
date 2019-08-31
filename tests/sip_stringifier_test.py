import textwrap
from sip_parser.sip_message import SipMessage


def prepare_msg(msg: str):
    # Message lines must be CRLF-terminated and not indented
    return textwrap.dedent(msg).replace("\n", "\r\n")


def test_basic_stringify():
    msg = """\
        REGISTER sip:ims.mnc123.mcc123.3gppnetwork.org SIP/2.0
        From: <sip:97321761314732@ims.mnc123.mcc123.3gppnetwork.org>;tag=14028fvx4vg
        To: <sip:97321761314732@ims.mnc123.mcc123.3gppnetwork.org>
        Content-Length: 0

        """

    original_message = prepare_msg(msg)
    sip_msg = SipMessage.from_string(original_message)
    sip_msg2 = SipMessage.from_string(sip_msg.stringify())

    assert sip_msg.stringify() == sip_msg2.stringify()
    assert sip_msg.stringify() == original_message


def test_full_message_stringify():
    msg = """\
        REGISTER sip:ims.mnc123.mcc123.3gppnetwork.org SIP/2.0
        From: <sip:97321761314732@ims.mnc123.mcc123.3gppnetwork.org>;tag=14028fvx4vg
        To: <sip:97321761314732@ims.mnc123.mcc123.3gppnetwork.org>
        Via: SIP/2.0/TCP 127.0.0.1:51372;branch=4y479aZgQ6b15d63F;rport
        Route: <sip:127.0.0.1:5060;lr>
        CSeq: 1 REGISTER
        Call-ID: 1111aa63F@127.0.0.1
        Contact: <sip:97321761314732@127.0.0.1:51372;transport=tcp>;expires=600000;+g.3gpp.icsi-ref="urn%3Aurn-7%3A3gpp-service.ims.icsi.mmtel,urn%3Aurn-7%3A3gpp-service.ims.icsi.gsma.callcomposer";+g.3gpp.iari-ref="urn%3Aurn-7%3A3gpp-application.ims.iari.rcse.im,urn%3Aurn-7%3A3gpp-application.ims.iari.rcs.fthttp";+g.3gpp.cs-voice;+g.oma.sip-im;+g.3gpp.smsip;video;+sip.instance="<urn:gsma:imei:12345678-023451-0>"
        Authorization: Digest username="97321761314732@ims.mnc123.mcc123.3gppnetwork.org",realm="ims.mnc123.mcc123.3gppnetwork.org",nonce="",uri="sip:ims.mnc021.mcc658.3gppnetwork.org",response=""
        Max-Forwards: 70
        User-Agent: iPhone 9.0
        Supported: gruu,path,sec-agree,timer
        P-Access-Network-Info: IEEE-802.11;i-wlan-node-id=34a84edc9615
        Expires: 0
        Content-Length: 4

        Hi
        """

    original_message = prepare_msg(msg)
    sip_msg = SipMessage.from_string(original_message)
    sip_msg2 = SipMessage.from_string(sip_msg.stringify())

    assert sip_msg.stringify() == sip_msg2.stringify()
    assert sip_msg.stringify() == original_message


def test_stringify_multiple_routes_one_header():
    msg = """\
        REGISTER sip:ims.mnc123.mcc123.3gppnetwork.org SIP/2.0
        From: <sip:97321761314732@ims.mnc123.mcc123.3gppnetwork.org>;tag=14028fvx4vg
        To: <sip:97321761314732@ims.mnc123.mcc123.3gppnetwork.org>
        Route: <sip:10.0.0.1:5061;lr>, <sip:uuu:ppp@127.0.0.1:5060;aaaa>
        Content-Length: 0

        """

    original_message = prepare_msg(msg)
    sip_msg = SipMessage.from_string(original_message)
    sip_msg2 = SipMessage.from_string(sip_msg.stringify())

    assert sip_msg.stringify() == sip_msg2.stringify()
    assert sip_msg.stringify() == original_message


def test_stringify_multiple_route_headers():
    # This message has no extraneous spaces, but the output is NOT equal to the input
    # because the multi route header is compressed into one. So we don't check for that.
    msg = """\
        REGISTER sip:ims.mnc123.mcc123.3gppnetwork.org SIP/2.0
        From: <sip:97321761314732@ims.mnc123.mcc123.3gppnetwork.org>;tag=14028fvx4vg
        To: <sip:97321761314732@ims.mnc123.mcc123.3gppnetwork.org>
        Route: <sip:10.0.0.1:5061;lr>
        Route: <sip:uuu:ppp@127.0.0.1:5060;aaaa>
        Content-Length: 0

        """

    sip_msg = SipMessage.from_string(prepare_msg(msg))
    sip_msg2 = SipMessage.from_string(sip_msg.stringify())

    assert sip_msg.stringify() == sip_msg2.stringify()
