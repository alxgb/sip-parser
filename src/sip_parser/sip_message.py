from typing import List, Dict, Any, Optional, Union

import urllib
import re
from sip_parser.helpers.sip_parsers import (
    COMPACT_HEADERS,
    parse_params,
    parse_multiheader,
    parse_via,
    parse_auth_header_with_scheme,
    parse_auth_header,
    parse_cseq,
    parse_aor,
    parse_uri,
    parse_aor_with_uri,
    parse_response,
    parse_request,
)
from sip_parser.helpers.sip_stringifiers import (
    stringify_header,
    stringify_uri,
    prettify_header_name,
)
from sip_parser.exceptions import SipParseError, SipBuildError

# These headers MAY appear multiple times in a single message
MULTI_INSTANCE_HEADER_NAMES = (
    # MAY appear multiple times, but compressable into a single one with commas
    "contact",
    "route",
    "record-route",
    "path",
    "via",
    # Multi instance, but NOT compressable into a single one
    "www-authenticate",
    "authorization",
    "proxy-authenticate",
    "proxy-authorization",
)


class SipMessage:
    TYPE_REQUEST = 0
    TYPE_RESPONSE = 1

    def __init__(self):
        # Declaration of variables, NOT initialization
        self.type: int
        self.version: str  # Response/Request
        self.status: Optional[int]  # Response
        self.reason: Optional[str]  # Response
        self.method: Optional[str]  # Request
        self.uri: Optional[str]  # Request
        self.content: str

        # Headers
        self.headers: Dict[str, Any] = {}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        """ Creates an instance of the class based off the given data """

        message = cls()
        message.version = data.get("version")
        if data.get("status"):
            # Assume it's a Response message
            message.type = cls.TYPE_RESPONSE
            message.status = data.get("status")
            message.reason = data.get("reason")

            if not message.status or not message.reason:
                raise SipBuildError("Invalid response message: Expected reason & status")

            if data.get("method") or data.get("uri"):
                raise SipBuildError(
                    "Found uri/method (Request) properties alongside status/reason (Response)"
                )

        else:
            message.type = cls.TYPE_REQUEST
            message.method = data.get("method")
            message.uri = data.get("uri")

            if not message.method or not message.uri:
                raise SipBuildError("Invalid request message: Expected URI & method")

            if data.get("status") or data.get("reason"):
                raise SipBuildError(
                    "Found reason/status (Response) properties alongside uri/method (Request)"
                )

        message.headers = data.get("headers", {})
        if not message.headers:
            raise SipBuildError("Missing message headers")

        if not isinstance(message.headers, dict):
            raise SipBuildError("The message headers must be listed as a dictionary")

        for header, value in message.headers.items():
            # Make sure multi-headers are a list/tuple, even if the user provided it flat
            if header in MULTI_INSTANCE_HEADER_NAMES and not isinstance(value, (list, tuple)):
                message.headers[header] = (value,)

        message.content = data.get("content", "")

        return message

    @classmethod
    def from_string(cls, raw_message: str):
        """ Parses a message contained in raw_message and produces
            a class instance with values based off of it
        """

        message = cls()

        # Split header/content (header > 2 linebreaks > content)
        parts = re.match(r"^\s*([\S\s]*?)\r\n\r\n([\S\s]*)$", raw_message)
        if not parts:
            raise SipParseError(
                "Invalid SIP message format, couldn't find header/body division (header must be followed by 2 linebreaks)"
            )

        message.content = parts.group(2)
        lines = re.split(r"\r\n(?![ \t])", parts.group(1))
        if not lines:  # Empty message
            return

        # Is it a response?
        response_parsed = parse_response(lines)
        if response_parsed:
            # Yes, it is a response
            message.type = message.TYPE_RESPONSE
            message.version = response_parsed["version"]
            message.status = response_parsed["status"]
            message.reason = response_parsed["reason"]
        else:
            # We couldn't parse it as a response, it must be a request
            request_parsed = parse_request(lines)
            if not request_parsed:
                raise SipParseError(
                    "Invalid SIP message to parse, neither a response nor a request"
                )

            message.type = message.TYPE_REQUEST
            message.version = request_parsed["version"]
            message.method = request_parsed["method"]
            message.uri = request_parsed["uri"]

        # Parse the headers
        for line in lines[1:]:
            header_match = re.match(r"^([\S]*?)\s*:\s*([\s\S]*)$", line)
            if not header_match:
                raise SipParseError("Invalid SIP header detected. Parsing line: %s" % line)

            name = urllib.parse.unquote(header_match.group(1)).lower()
            if name in COMPACT_HEADERS:
                name = COMPACT_HEADERS[name]  # Uncompress shorteners

            message.add_header_from_str(name, header_match.group(2))

        return message

    def add_multi_header_from_str(self, name: str, raw_val: str):
        """ Extends or creates a multi-header
            Some headers (e.g Contact) can occur multiple times in the message, and must be parsed into a list of ocurrences.
        """

        values: Union[str, List]  # [Type declaration]
        if name == "contact":
            if raw_val == "*":
                values = "*"
            else:
                values, data = parse_multiheader(parse_aor, raw_val)
        elif name in ("route", "record-route", "path"):
            values, data = parse_multiheader(parse_aor_with_uri, raw_val)
        elif name == "via":
            values, data = parse_multiheader(parse_via, raw_val)
        elif name in (
            "www-authenticate",
            "proxy-authenticate",
            "authorization",
            "proxy-authorization",
        ):
            values, data = parse_multiheader(parse_auth_header_with_scheme, raw_val)
        else:
            raise SipParseError(f"Don't know how to process header {name} as a multi-header")

        # Make sure there's no leftover data after parsing (either we parsed wrong or the header is invalid, either way - bad)
        if data:
            raise SipParseError(f"Leftover data found after processing {name} header")

        # If we hadn't found this header before, create it. Otherwise, append to it
        if name not in self.headers:
            self.headers[name] = []

        self.headers[name].extend(values)

    def add_header_from_str(self, name: str, data: str):
        if name in MULTI_INSTANCE_HEADER_NAMES:
            self.add_multi_header_from_str(name, data)
        elif name in ("to", "from", "refer-to"):
            val, _ = parse_aor(data)
            self.headers[name] = val
        elif name == "cseq":
            self.headers["cseq"] = parse_cseq(data)
        elif name in ("content-length", "max-forwards"):
            self.headers[name] = int(data)
        elif name == "authentication-info":
            # Directly parse auth header, without scheme
            val, _ = parse_auth_header(data)
            self.headers[name] = val
        else:
            # Generic header parsing (just key -> value)
            if name in self.headers:  # Header existed, append
                self.headers[name] += "," + data
            else:
                self.headers[name] = data

    def stringify(self):
        ver = self.version if self.version else "2.0"
        if self.type == self.TYPE_RESPONSE:
            msg_str = f"SIP/{ver} {self.status} {self.reason}\r\n"
        else:
            uri = stringify_uri(self.uri)
            msg_str = f"{self.method} {uri} SIP/{ver}\r\n"

        self.headers["content-length"] = len(self.content) or 0
        for header_name, header_data in self.headers.items():
            if header_data is None:
                continue

            msg_str += stringify_header(header_name, header_data) + "\r\n"

        msg_str += "\r\n"

        if self.content:
            msg_str += self.content

        return msg_str

    def debug_print(self):
        import pprint

        pprint.pprint(self.__dict__)
