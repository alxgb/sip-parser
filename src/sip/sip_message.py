from typing import List, Dict, Any, Optional, Union

# pylint: disable=relative-beyond-top-level; VSCode is dumb and can't understand the project structure
import urllib
import re
from .sip_parsers import (
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

    def parse(self, data: str):
        # Split header/content (header > 2 linebreaks > content)
        parts = re.match(r"^\s*([\S\s]*?)\r\n\r\n([\S\s]*)$", data)
        if not parts:
            raise RuntimeError(
                "Invalid SIP message format, couldn't find header/body division (header must be followed by 2 linebreaks)"
            )

        self.content = parts.group(2)
        lines = re.split(r"\r\n(?![ \t])", parts.group(1))
        if not lines:  # Empty message
            return

        # Is it a response?
        response_parsed = parse_response(lines)
        if response_parsed:
            # Yes, it is a response
            self.type = self.TYPE_RESPONSE
            self.version = response_parsed["version"]
            self.status = response_parsed["status"]
            self.reason = response_parsed["reason"]
        else:
            # We couldn't parse it as a response, it must be a request
            request_parsed = parse_request(lines)
            if not request_parsed:
                raise RuntimeError("Invalid SIP message to parse, neither a response nor a request")

            self.type = self.TYPE_REQUEST
            self.version = request_parsed["version"]
            self.method = request_parsed["method"]
            self.uri = request_parsed["uri"]

        # Parse the headers
        for line in lines[1:]:
            header_match = re.match(r"^([\S]*?)\s*:\s*([\s\S]*)$", line)
            if not header_match:
                raise RuntimeError("Invalid SIP header detected. Parsing line: %s" % line)

            name = urllib.parse.unquote(header_match.group(1)).lower()
            if name in COMPACT_HEADERS:
                name = COMPACT_HEADERS[name]  # Uncompress shorteners

            self.add_header(name, header_match.group(2))

    def add_multi_header(self, name: str, raw_val: str):
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

        # Make sure there's no leftover data after parsing (either we parsed wrong or the header is invalid, either way - bad)
        if data:
            raise RuntimeError(f"Leftover data found after processing {name} header")

        # If we hadn't found this header before, create it. Otherwise, append to it
        if name not in self.headers:
            self.headers[name] = []

        self.headers[name].extend(values)

    def add_header(self, name: str, data: str):
        if name in (
            "contact",
            "route",
            "record-route",
            "path",
            "via",
            "www-authenticate",
            "proxy-authenticate",
            "authorization",
            "proxy-authorization",
        ):
            # All these can be multi-value headers
            self.add_multi_header(name, data)
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

    def debug_print(self):
        import pprint

        pprint.pprint(self.__dict__)
