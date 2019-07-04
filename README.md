# Python SIP & MSRP parser

This is a small pet project designed to fill the surprising lack (as of writing and to my knowledge) of any sort of standalone sip & msrp parser in Python.

The parser tries to be somewhat exhaustive, but may fail in certain edge cases, like the SIP Torture Test Messages in RFC 4475. Most of the SIP parser is actually a Python port of the Javascript one used by [sip.js](https://github.com/kirm/sip.js), with some tweaks here and there to better parse some complex headers.

There are a few tests written using pylint (which don't cover all situations, and can certainly be extended). The tests can be run from the project root by simply executing `pytest`.

Anyone's free to fork this and use it as a starting point for their own parser/needs, the license is MIT (See LICENSE file).

## API

The primary classes exposed by the library are SipMessage, MsrpMessage and CpimMessage. MsrpMessage and CpimMessage usage is fairly straight forward, simply call the static function `cls.from_string(<msg_str>)` and that will parse the provided message. A MsrpParseError exception will be thrown if the message is considered malformed. SipMessage works slightly differently, first create an instance of it and then call `parse(<msg_str>)`. This will update the SipMessage object fields accordingly.

```python
sip_msg = SipMessage()
sip_msg.parse(<string>)
```

For additional usage examples, you may check out the tests.
