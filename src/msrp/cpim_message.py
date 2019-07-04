import re

# pylint: disable=relative-beyond-top-level; VSCode is dumb and can't understand the project structure
from .msrp_message import HEADER_REGEX, MsrpParseError


class CpimMessage:
    """ Parse a CPIM content-type message (RFC3862) """

    def __init__(self):
        self.headers = {}
        self.content = {"headers": {}, "body": []}

    @staticmethod
    def from_lines(lines):
        """ Generate a CpimMessage structure based on a given message """
        cpim_m = CpimMessage()
        for h_line_num, line in enumerate(lines):
            # First come the headers until a linebreak is found
            if line == "":
                break

            m = re.match(HEADER_REGEX, line)
            if not m:
                raise MsrpParseError(
                    f"Expected header while parsing CPIM message (line {h_line_num+1}, {line})"
                )

            cpim_m.headers[m.group(1)] = m.group(2)

        # Next is the encapsulated MIME message-body
        content_start_line = h_line_num + 1
        for c_line_num, line in enumerate(lines[content_start_line:], start=content_start_line):
            if line == "":
                break

            m = re.match(HEADER_REGEX, line)
            if not m:
                raise MsrpParseError(
                    f"Expected header while parsing CPIM's message body (line {c_line_num+1}, {line})"
                )

            cpim_m.content["headers"][m.group(1)] = m.group(2)

        if len(lines) > c_line_num:
            cpim_m.content["body"] = lines[c_line_num + 1 :]

        return cpim_m
