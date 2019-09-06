# SIP & SDP parser for Python

This is a small pet project designed to fill the surprising lack (as of writing and to my knowledge) of any sort of standalone SIP parser in Python. The SDP parser comes as an extra, like in other SIP parser projects.

- The **SIP parser** tries to be somewhat exhaustive, but may fail in certain edge cases, like some of the SIP Torture Test Messages in RFC 4475. Most of the SIP parser is actually a Python port of the Javascript one used by [sip.js](https://github.com/kirm/sip.js), with a couple tweaks to better parse some complex headers.
- The **SDP parser** is less exhaustive than the SIP parser, and may have trouble detecting subtly malformed messages and/or directly pass strings off to the SDP fields, even when they could be parsed better.

There are a few tests written using pylint (which don't cover all situations, and can certainly be extended). The tests can be run from the project root by simply executing `pytest`.

Anyone's free to fork this and use it as a starting point for their own parser/needs, the license is MIT (See LICENSE file).

## API basics

The primary classes exposed by the library are `SipMessage` and `SdpMessage`. Their usage is fairly straight forward, simply call the static function `cls.from_string(<msg_str>)` and that will parse the provided message. An exception will be thrown if the message is considered malformed.

## Examples

(For additional usage examples, you may check out the tests)

### SipMessage
```python
try:
    sip_msg = SipMessage.from_string("<msg_str>")
except SipParseError as:
    print(f"Failed to parse message: {ex}")

# Use the parsed message (simply access the class properties, it's a pretty thin class)
```

Building a message:
```python
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
```

Transforming a SipMessage instance into a string:
```
sip_message.stringify()
```

### SdpMessage
`SdpMessage` works almost exactly the same as `SipMessage`.
