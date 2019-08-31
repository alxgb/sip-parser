import textwrap
from sip_parser.sip_message import SipMessage


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

    sip_msg = SipMessage.from_string(prepare_msg(msg))

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

    sip_msg = SipMessage.from_string(prepare_msg(msg))

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

    sip_msg = SipMessage.from_string(prepare_msg(msg))

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

    sip_msg = SipMessage.from_string(prepare_msg(msg))
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

    sip_msg = SipMessage.from_string(prepare_msg(msg))

    assert sip_msg.type == SipMessage.TYPE_REQUEST
    assert len(sip_msg.headers) == 1
    via = sip_msg.headers["via"][0]
    assert via["protocol"] == "TCP"
    assert via["host"] == "127.0.0.1"
    assert via["port"] == 51372
    assert len(via["params"]) == 2
    assert via["params"]["branch"] == "4y479aZgQ6b15d63F"
    assert "rport" in via["params"] and via["params"]["rport"] is None


def test_route_header_parsing():
    msg = """\
        METHOD irrelevant SIP/2.0
        Route: <sip:127.0.0.1:5060;lr>

        """

    sip_msg = SipMessage.from_string(prepare_msg(msg))

    assert sip_msg.type == SipMessage.TYPE_REQUEST
    assert len(sip_msg.headers) == 1
    route = sip_msg.headers["route"][0]
    assert route["uri"]["schema"] == "sip"
    assert route["uri"]["user"] is None
    assert route["uri"]["password"] is None
    assert route["uri"]["host"] == "127.0.0.1"
    assert route["uri"]["port"] == 5060
    assert route["uri"]["params"]["lr"] is None
    assert not route["params"]


def test_multiroute_header_parsing():
    msg = """\
        METHOD irrelevant SIP/2.0
        Route: <sip:10.0.0.1:5061;lr>
        Route: <sip:uuu:ppp@127.0.0.1:5060;aaaa>

        """

    sip_msg = SipMessage.from_string(prepare_msg(msg))

    assert sip_msg.type == SipMessage.TYPE_REQUEST
    assert len(sip_msg.headers) == 1
    # Make sure we're properly differentiating both URIs
    assert sip_msg.headers["route"][0]["uri"]["host"] == "10.0.0.1"
    route2 = sip_msg.headers["route"][1]

    # Verify we got all values on the 2nd one right
    assert route2["uri"]["schema"] == "sip"
    assert route2["uri"]["user"] == "uuu"
    assert route2["uri"]["password"] == "ppp"
    assert route2["uri"]["host"] == "127.0.0.1"
    assert route2["uri"]["port"] == 5060
    assert len(route2["uri"]["params"].keys()) == 1
    assert route2["uri"]["params"]["aaaa"] is None
    assert not route2["params"]


def test_route_with_no_port():
    msg = """\
        METHOD irrelevant SIP/2.0
        Route: <sip:services.example.com;lr;unknownwith=value;unknown-no-value>

        """

    sip_msg = SipMessage.from_string(prepare_msg(msg))
    assert sip_msg.type == SipMessage.TYPE_REQUEST
    assert len(sip_msg.headers) == 1
    assert sip_msg.headers["route"][0]["uri"]["port"] is None


def test_tortuous_invite_parsing():
    # RFC 4475 "A Short Tortuous INVITE"
    # Note: Every \ has been escaped again to prevent Python string escaping breaking
    # the original escaping

    msg = """\
        INVITE sip:vivekg@chair-dnrc.example.com;unknownparam SIP/2.0
        TO :
         sip:vivekg@chair-dnrc.example.com ;   tag    = 1918181833n
        from   : "J Rosenberg \\\\\\""         <sip:jdrosen@example.com>
          ;
          tag = 98asjd8
        MaX-fOrWaRdS: 0068
        Call-ID: wsinv.ndaksdj@192.0.2.1
        Content-Length   : 150
        cseq: 0009
          INVITE
        Via  : SIP  /   2.0
         /UDP
            192.0.2.2;branch=390skdjuw
        s :
        NewFangledHeader:   newfangled value
         continued newfangled value
        UnknownHeaderWithUnusualValue: ;;,,;;,;
        Content-Type: application/sdp
        Route:
         <sip:services.example.com;lr;unknownwith=value;unknown-no-value>
        v:  SIP  / 2.0  / TCP     spindle.example.com   ;
          branch  =   z9hG4bK9ikj8  ,
         SIP  /    2.0   / UDP  192.168.255.111   ; branch=
         z9hG4bK30239
        m:"Quoted string \\"\\"" <sip:jdrosen@example.com> ; newparam =
                newvalue ;
          secondparam ; q = 0.33

        v=0
        o=mhandley 29739 7272939 IN IP4 192.0.2.3
        s=-
        c=IN IP4 192.0.2.4
        t=0 0
        m=audio 49217 RTP/AVP 0 12
        m=video 3227 RTP/AVP 31
        a=rtpmap:31 LPC
    """

    sip_msg = SipMessage.from_string(prepare_msg(msg))

    assert sip_msg.method == "INVITE"
    assert len(sip_msg.headers) == 13  # Via is declared twice
    assert len(sip_msg.headers["via"]) == 3
    contact = sip_msg.headers["contact"][0]
    assert contact["name"] == '"Quoted string \\"\\""'
    assert contact["params"]["q"] == "0.33"
    assert contact["params"]["newparam"] == "newvalue"
    assert contact["params"]["secondparam"] is None
    assert sip_msg.headers["via"][0]["protocol"] == "UDP"
    assert sip_msg.headers["via"][1]["protocol"] == "TCP"
    assert sip_msg.headers["via"][2]["protocol"] == "UDP"
    assert sip_msg.headers["from"]["params"]["tag"] == "98asjd8"
