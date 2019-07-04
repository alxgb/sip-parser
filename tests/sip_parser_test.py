import textwrap
from src.sip.sip_message import SipMessage


def prepare_msg(msg: str):
    # Message lines must be CRLF-terminated and not indented
    return textwrap.dedent(msg).replace("\n", "\r\n")


def test_basic_register_message():
    msg = """\
        REGISTER sip:ims.mnc123.mcc123.3gppnetwork.org SIP/2.0
        Via: SIP/2.0/TCP 127.0.0.1:51372;branch=4y479aZgQ6b15d63F;rport
        Route: <sip:127.0.0.1:5060;lr>
        From: <sip:97321761314732@ims.mnc123.mcc123.3gppnetwork.org>;tag=14028fvx4vg
        To: <sip:97321761314732@ims.mnc123.mcc123.3gppnetwork.org>
        Call-ID: 1111aa63F@127.0.0.1
        CSeq: 1 REGISTER
        Contact: <sip:97321761314732@127.0.0.1:51372;transport=tcp>;expires=600000;+g.3gpp.icsi-ref="urn%3Aurn-7%3A3gpp-service.ims.icsi.mmtel,urn%3Aurn-7%3A3gpp-service.ims.icsi.gsma.callcomposer";+g.3gpp.iari-ref="urn%3Aurn-7%3A3gpp-application.ims.iari.rcse.im,urn%3Aurn-7%3A3gpp-application.ims.iari.rcs.fthttp";+g.3gpp.cs-voice;+g.oma.sip-im;+g.3gpp.smsip;video;+sip.instance="<urn:gsma:imei:12345678-023451-0>"
        Authorization: Digest username="97321761314732@ims.mnc123.mcc123.3gppnetwork.org", realm="ims.mnc123.mcc123.3gppnetwork.org", nonce="", uri="sip:ims.mnc021.mcc658.3gppnetwork.org", response=""
        Max-Forwards: 70
        User-Agent: iPhone 9.0
        Supported: gruu,path,sec-agree,timer
        P-Access-Network-Info: IEEE-802.11;i-wlan-node-id=34a84edc9615
        Content-Length: 0
        Expires: 0

        """

    sip_msg = SipMessage()
    sip_msg.parse(prepare_msg(msg))

    assert sip_msg.type == SipMessage.TYPE_REQUEST
    assert sip_msg.version == "2.0"
    assert sip_msg.method == "REGISTER"
    assert len(sip_msg.headers) == 14
    assert sip_msg.headers["cseq"]["seq"] == 1
    assert sip_msg.headers["max-forwards"] == 70
    assert sip_msg.headers["content-length"] == 0
    assert len(sip_msg.content) == 0


def test_header_parsing_case():
    """ Make sure we properly ignore casing when parsing headers """
    msg = """\
        METHOD irrelevant SIP/2.0
        vIa: SIP/2.0/TCP 127.0.0.1:51372;branch=4y479aZgQ6b15d63F;rport
        cseq: 65 SOMETHING
        mAx-ForwarDS: 11

        """

    sip_msg = SipMessage()
    sip_msg.parse(prepare_msg(msg))
    assert len(sip_msg.headers) == 3
    assert sip_msg.headers["via"]
    assert sip_msg.headers["cseq"]["seq"] == 65
    assert sip_msg.headers["max-forwards"] == 11


def test_header_parsing_spaces():
    """ Make sure we properly ignore extra spaces when parsing headers """

    msg = """\
        METHOD irrelevant SIP/2.0
        Via     : SIP/2.0/TCP
            127.0.0.1:51372;branch=4y479aZgQ6b15d63F;rport
        cseq: 65
          SOMETHING
        Max-Forwards  : 011
        To     : sip:vivekg@chair-dnrc.example.com ;   tag    = 1918181833n

        """

    sip_msg = SipMessage()
    sip_msg.parse(prepare_msg(msg))
    assert len(sip_msg.headers) == 4
    assert sip_msg.headers["via"]
    assert sip_msg.headers["via"][0]["protocol"] == "TCP"
    assert sip_msg.headers["via"][0]["host"] == "127.0.0.1"
    assert sip_msg.headers["cseq"]["seq"] == 65
    assert sip_msg.headers["cseq"]["method"] == "SOMETHING"
    assert sip_msg.headers["max-forwards"] == 11
    assert sip_msg.headers["to"]["params"]["tag"] == "1918181833n"


def test_multiline_headers():
    # Verify we can deal with the headers properly even if they're split across lines

    msg = """\
        METHOD irrelevant SIP/2.0
        Max-Forwards: 1257
        To:
           sip:vivekg@chair-dnrc.example.com ;   tag    = 1918181833n
        CSeq: 42 HI
        Route:
         <sip:127.0.0.1:5060;lr>

        """

    sip_msg = SipMessage()
    sip_msg.parse(prepare_msg(msg))
    assert len(sip_msg.headers) == 4
    assert sip_msg.headers["cseq"]["seq"] == 42
    assert sip_msg.headers["max-forwards"] == 1257
    assert sip_msg.headers["to"]["params"]["tag"] == "1918181833n"
    assert sip_msg.headers["route"][0]["uri"]["params"]["lr"] is None


def test_via_header_parsing():
    msg = """\
        METHOD irrelevant SIP/2.0
        Via: SIP/2.0/TCP 127.0.0.1:51372;branch=4y479aZgQ6b15d63F;rport

        """

    sip_msg = SipMessage()
    sip_msg.parse(prepare_msg(msg))

    assert sip_msg.type == SipMessage.TYPE_REQUEST
    assert len(sip_msg.headers) == 1
    via = sip_msg.headers["via"][0]
    assert via["protocol"] == "TCP"
    assert via["host"] == "127.0.0.1"
    assert via["port"] == 51372
    assert len(via["params"]) == 2
    assert via["params"]["branch"] == "4y479aZgQ6b15d63F"
    assert "rport" in via["params"] and via["params"]["rport"] is None

