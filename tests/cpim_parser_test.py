import textwrap
from src.msrp_message import MsrpMessage, MsrpParseError
from src.cpim_message import CpimMessage
import pytest


def clean_msg(msg):
    return textwrap.dedent(msg.strip())


def test_example_cpim_message():
    # Only validate that we can parse this appropiately, with the multiple lines and such
    # Proper CPIM parsing will be tested under cpim_parser_test.

    msg = """\
        MSRP 1816g3gNxVlCDeg3gNxVlCDe SEND
        To-Path: msrps://127.0.0.1:12745/f1a465d8fb-cf6cfaf8fd-147bdc4d8a;tcp
        From-Path: msrp://127.0.0.1:59169/7024R3gNxV;tcp
        Message-ID: 1816g3gNxVlCDeg3gNxVlCDe
        Failure-Report: yes
        Byte-Range: 1-418/418
        Content-Type: Message/CPIM

        From: MR SANDERS <im:piglet@100akerwood.com>
        To: Depressed Donkey <im:eeyore@100akerwood.com>
        DateTime: 2000-12-13T13:40:00-08:00
        Subject: the weather will be fine today
        NS: MyFeatures <mid:MessageFeatures@id.foo.com>
        Require: MyFeatures.VitalMessageOption
        MyFeatures.VitalMessageOption: Confirmation-requested
        MyFeatures.WackyMessageOption: Use-silly-font

        Content-Type: text/xml;charset=utf-8
        Content-ID: <1234567890@foo.com>

        <body>
        Here is the text of my message.
        </body>
        -------1816g3gNxVlCDeg3gNxVlCDe$
    """

    msrp_m = MsrpMessage.from_string(clean_msg(msg))
    assert msrp_m.id == "1816g3gNxVlCDeg3gNxVlCDe"
    assert len(msrp_m.headers) == 6
    assert msrp_m.headers["Content-Type"] == "Message/CPIM"

    cpim_m = CpimMessage.from_lines(msrp_m.content)
    assert len(cpim_m.headers) == 8
    assert cpim_m.headers["DateTime"] == "2000-12-13T13:40:00-08:00"
    assert cpim_m.content["body"] == ["<body>", "Here is the text of my message.", "</body>"]
    assert cpim_m.content["headers"]["Content-Type"] == "text/xml;charset=utf-8"
    assert cpim_m.content["headers"]["Content-ID"] == "<1234567890@foo.com>"


def test_sip_cpim_message():
    msg = """\
        MSRP 6371fg4AgjKAFvYn814VlCDd SEND
        To-Path: msrps://127.0.0.1:12012/a1a465d8fb-cf6cfaf8fd-147bdc4d8a;tcp
        From-Path: msrp://127.0.0.1:59169/9893R3gAxV;tcp
        Message-ID: 6371fg4AgjKAFvYn814VlCDd
        Failure-Report: yes
        Byte-Range: 1-418/418
        Content-Type: message/cpim

        From: <tel:+34666321123>
        To: <sip:SA77qga-hwn11xxpqafswks79wc2wwuw8gbyynaalv2e2ebbvdug8t6a8av77wu6qyrooiqvq0twvhhc64gppj1m8bq6@127.0.0.1:12012;fid=vularcvim02512_1;transport=tcp>
        DateTime: 2019-07-31T21:54:12.000Z
        NS: imdn <urn:ietf:params:imdn>
        imdn.Message-ID: 1816f9kChg
        imdn.Disposition-Notification: positive-delivery

        Content-Type: text/plain;charset=UTF-8
        Content-Length: 43

        Message sent on 2019-07-31
        @ 21:54:12.000Z!
        -------6371fg4AgjKAFvYn814VlCDd$
    """

    msrp_m = MsrpMessage.from_string(clean_msg(msg))
    assert msrp_m.id == "6371fg4AgjKAFvYn814VlCDd"
    assert len(msrp_m.headers) == 6
    assert msrp_m.headers["Content-Type"] == "message/cpim"

    cpim_m = CpimMessage.from_lines(msrp_m.content)
    assert len(cpim_m.headers) == 6
    assert cpim_m.headers["DateTime"] == "2019-07-31T21:54:12.000Z"
    assert cpim_m.headers["From"] == "<tel:+34666321123>"
    assert (
        cpim_m.headers["To"]
        == "<sip:SA77qga-hwn11xxpqafswks79wc2wwuw8gbyynaalv2e2ebbvdug8t6a8av77wu6qyrooiqvq0twvhhc64gppj1m8bq6@127.0.0.1:12012;fid=vularcvim02512_1;transport=tcp>"
    )
    assert cpim_m.headers["NS"] == "imdn <urn:ietf:params:imdn>"
    assert cpim_m.headers["imdn.Message-ID"] == "1816f9kChg"
    assert cpim_m.headers["imdn.Disposition-Notification"] == "positive-delivery"
    assert cpim_m.content["body"] == ["Message sent on 2019-07-31", "@ 21:54:12.000Z!"]
    assert cpim_m.content["headers"]["Content-Type"] == "text/plain;charset=UTF-8"
    assert cpim_m.content["headers"]["Content-Length"] == "43"
