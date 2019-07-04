import textwrap
from src.msrp.msrp_message import MsrpMessage, MsrpParseError
import pytest


def clean_msg(msg):
    return textwrap.dedent(msg.strip())


def test_basic_send():
    msg = """\
        MSRP a786hjs2 SEND
        To-Path: msrp://biloxi.example.com:12763/kjhd37s2s20w2a;tcp
        From-Path: msrp://atlanta.example.com:7654/jshA7weztas;tcp
        Message-ID: 87652491
        Byte-Range: 1-25/25
        Content-Type: text/plain

        Hello bob, congratulation to your graduation!
        -------a786hjs2$
    """

    m = MsrpMessage.from_string(clean_msg(msg))
    # Verify request line
    assert m.id == "a786hjs2"
    assert m.method == "SEND"

    # Verify headers
    assert m.headers["To-Path"] == "msrp://biloxi.example.com:12763/kjhd37s2s20w2a;tcp"
    assert m.headers["From-Path"] == "msrp://atlanta.example.com:7654/jshA7weztas;tcp"
    assert m.headers["Message-ID"] == "87652491"
    assert m.headers["Byte-Range"] == "1-25/25"
    assert m.headers["Content-Type"] == "text/plain"

    # Validate body
    assert m.content == ["Hello bob, congratulation to your graduation!"]


def test_basic_report():
    msg = """\
        MSRP dkei38sd REPORT
        To-Path: msrp://alicepc.example.com:7777/iau39soe2843z;tcp
        From-Path: msrp://bob.example.com:8888/9di4eae923wzd;tcp
        Message-ID: 12339sdqwer
        Byte-Range: 1-106/106
        Status: 000 200 OK
        -------dkei38sd$
    """

    m = MsrpMessage.from_string(clean_msg(msg))
    assert m.id == "dkei38sd"
    assert m.method == "REPORT"
    assert m.headers["Status"] == "000 200 OK"
    # The other headers shared with SEND are tested under SEND


def test_wrong_method():
    msg = """\
        MSRP dkei38sd WRONG_METHOD
        To-Path: msrp://alicepc.example.com:7777/iau39soe2843z;tcp
        From-Path: msrp://bob.example.com:8888/9di4eae923wzd;tcp
        Message-ID: 12339sdqwer
        Byte-Range: 1-106/106
        Status: 000 200 OK
        -------dkei38sd$
    """

    with pytest.raises(MsrpParseError):
        MsrpMessage.from_string(clean_msg(msg))


def test_message_chunk_parse():
    msg = """\
        MSRP helloworld2vavsasgd SEND
        To-Path: msrp://biloxi.example.com:12763/kjhd37s2s20w2a;tcp
        From-Path: msrp://atlanta.example.com:7654/jshA7weztas;tcp
        Message-ID: 87652491
        Byte-Range: 1-*/50
        Content-Type: text/plain

        This would be the first part of a larger message (note the +)
        -------helloworld2vavsasgd+
    """

    m = MsrpMessage.from_string(clean_msg(msg))
    # Verify request line
    assert m.id == "helloworld2vavsasgd"
    assert m.method == "SEND"
    assert m.headers["Byte-Range"] == "1-*/50"

    # Validate body
    assert m.content == ["This would be the first part of a larger message (note the +)"]


def test_html_message():
    msg = """\
        MSRP d93kswow SEND
        To-Path: msrp://bob.example.com:8888/9di4eae923wzd;tcp
        From-Path: msrp://alicepc.example.com:7777/iau39soe2843z;tcp
        Message-ID: 12339sdqwer
        Byte-Range: 1-106/106
        Success-Report: yes
        Failure-Report: no
        Content-Type: text/html

        <html><body>
        <p>Something something <a href="http://www.example.com/foobar">foobar</a></p>
        </body></html>
        -------d93kswow$
    """

    m = MsrpMessage.from_string(clean_msg(msg))
    # Verify request line
    assert m.id == "d93kswow"
    assert m.method == "SEND"
    assert m.content == [
        "<html><body>",
        '<p>Something something <a href="http://www.example.com/foobar">foobar</a></p>',
        "</body></html>",
    ]


def test_nocontent_message():
    msg = """\
        MSRP dkei38sd 200 OK
        To-Path: msrp://bob.example.com:8888/9di4eae923wzd;tcp
        From-Path: msrp://alicepc.example.com:7777/iau39soe2843z;tcp
        -------dkei38sd$
    """
    m = MsrpMessage.from_string(clean_msg(msg))
    assert m.id == "dkei38sd"
    assert m.request_status_code == 200
    assert m.request_status_name == "OK"
    assert len(m.headers) == 2
    assert not m.content


def test_invalid_header_detection_wrong_name():
    msg = """\
        MSRP dkei38sd 200 OK
        To-Path: msrp://bob.example.com:8888/9di4eae923wzd;tcp
        From-Path: msrp://alicepc.example.com:7777/iau39soe2843z;tcp
        Invalid-Header: this_header_doesnt_exist
        -------dkei38sd$
    """

    with pytest.raises(MsrpParseError, match="^Unexpected header .*"):
        MsrpMessage.from_string(clean_msg(msg))


def test_invalid_header_detection_case():
    msg = """\
        MSRP dkei38sd 200 OK
        To-Path: msrp://bob.example.com:8888/9di4eae923wzd;tcp
        from-Path: msrp://alicepc.example.com:7777/iau39soe2843z;tcp
        -------dkei38sd$
    """

    with pytest.raises(MsrpParseError, match="^Unexpected header .*"):
        MsrpMessage.from_string(clean_msg(msg))


def test_additional_content_unparsed():
    msg = """\
        MSRP dkei38sd 200 OK
        To-Path: msrp://bob.example.com:8888/9di4eae923wzd;tcp
        From-Path: msrp://alicepc.example.com:7777/iau39soe2843z;tcp
        -------dkei38sd$
        This shouldnt be here
    """

    with pytest.raises(MsrpParseError, match="^More lines found .*"):
        MsrpMessage.from_string(clean_msg(msg))


def test_example_cpim_message():
    # Only validate that we can parse this appropiately, with the multiple lines and such
    # Proper CPIM parsing will be tested under cpim_parser_test.

    msg = """\
        MSRP 1816g3gNxVlCDeg3gNxVlCDe SEND
        To-Path: msrps://127.0.0.1:12745/d1a465d8fb-cf6cfaf8fd-147bdc4d8a;tcp
        From-Path: msrp://127.0.0.1:59169/1816R3gNxV;tcp
        Message-ID: 1816g3gNxVlCDeg3gNxVlCDe
        Failure-Report: yes
        Byte-Range: 1-529/529
        Content-Type: Message/CPIM

        From: MR SANDERS <im:piglet@100akerwood.com>
        To: Depressed Donkey <im:eeyore@100akerwood.com>
        DateTime: 2000-12-13T13:40:00-08:00
        Subject: the weather will be fine today
        Subject:;lang=fr beau temps prevu pour aujourd'hui
        NS: MyFeatures <mid:MessageFeatures@id.foo.com>
        Require: MyFeatures.VitalMessageOption
        MyFeatures.VitalMessageOption: Confirmation-requested
        MyFeatures.WackyMessageOption: Use-silly-font

        Content-Type: text/xml; charset=utf-8
        Content-ID: <1234567890@foo.com>

        <body>
        Here is the text of my message.
        </body>
        -------1816g3gNxVlCDeg3gNxVlCDe$
    """

    m = MsrpMessage.from_string(clean_msg(msg))
    assert m.id == "1816g3gNxVlCDeg3gNxVlCDe"
    assert len(m.headers) == 6
    assert m.headers["Content-Type"] == "Message/CPIM"
