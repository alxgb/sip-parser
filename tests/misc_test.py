from sip_parser.helpers.sip_parsers import parse_uri


def test_uri_parsing01():
    uri = parse_uri("sip:[2a05:d014:aa00:2203:9408:00a7:cc2c:39f6]:5061;transport=tls;r2=on;lr;ftag=5eff5f3f048e43e1")
    assert uri["schema"] == "sip"
    assert uri["user"] is None
    assert uri["password"] is None
    assert uri["host"] == "[2a05:d014:aa00:2203:9408:00a7:cc2c:39f6]"
    assert uri["port"] == 5061
    assert uri["params"]["transport"] == "tls"
    assert uri["params"]["r2"] == "on"
    assert uri["params"]["lr"] is None
    assert uri["params"]["ftag"] == "5eff5f3f048e43e1"
