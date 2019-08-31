import re

HEADER_REGEX = r"([\w\-\.]+):\s*(.*)"


class CpimParseError(Exception):
    pass


class CpimMessage:
    """ Parse a CPIM content-type message (RFC3862) """

    def __init__(self):
        self.headers = {}
        self.content = {"headers": {}, "body": []}

    @classmethod
    def from_string(cls, message: str):
        """ Generate a CpimMessage structure based on a given message string """
        lines = [line.strip() for line in message.split("\n")]
        if not lines or len(lines) == 1 and not lines[0]:
            raise CpimParseError("Empty CPIM message")

        cpim_m = cls()
        for h_line_num, line in enumerate(lines):
            # First come the headers until a linebreak is found
            if line == "":
                break

            m = re.match(HEADER_REGEX, line)
            if not m:
                raise CpimParseError(
                    f"Invalid header found while parsing CPIM message (line {h_line_num+1}: {line})"
                )

            cpim_m.headers[m.group(1)] = m.group(2)

        # Next is the encapsulated MIME message-body
        content_start_line = h_line_num + 1
        for c_line_num, line in enumerate(lines[content_start_line:], start=content_start_line):
            if line == "":
                break

            m = re.match(HEADER_REGEX, line)
            if not m:
                raise CpimParseError(
                    f"Expected header while parsing CPIM's message body (line {c_line_num+1}, {line})"
                )

            cpim_m.content["headers"][m.group(1)] = m.group(2)

        if len(lines) > c_line_num:
            cpim_m.content["body"] = lines[c_line_num + 1 :]

        return cpim_m
