import re

HEADER_REGEX = r"([\w\-\.]+):\s*(.*)"
END_OF_MESSAGE_REGEX = r"-------(\w+)[\$\+]"


class MsrpParseError(Exception):
    pass


class MsrpMessage:
    def __init__(self):
        self.id = ""
        self.method = ""
        self.request_status_code = None
        self.request_status_name = ""
        self.headers = {}
        self.content = None

    @classmethod
    def from_string(cls, raw_message: str):
        """ Generate a MsrpMessage structure based on a given message """
        lines = [line.strip() for line in raw_message.split("\n")]
        message = cls()

        # Fetch the header information (space-separated)
        # Examples:
        #   MSRP 1816g3gNxVlCDeg3gNxVlCDe SEND
        #   MSRP 1816g3gNxVlCDeg3gNxVlCDe 200 OK
        request_line = lines[0].split(" ")
        request_line_count = len(request_line)
        if request_line[0] != "MSRP":
            raise MsrpParseError(f"Expected header to begin with 'MSRP'")

        message.id = request_line[1]
        if request_line_count == 3:
            message.method = request_line[2]
            if message.method not in (
                "SEND",
                "REPORT",
            ):  # The only two acceptable based off of RFC4975
                raise MsrpParseError(f"Invalid method {message.method}")

        elif request_line_count == 4:
            try:
                message.request_status_code = int(request_line[2])
            except ValueError:
                raise MsrpParseError("Found a status code that is not a number")

            message.request_status_name = request_line[3]

        # Parse the *case sensitive* headers, checking against a valid headers list based on RFC4975
        valid_headers = [
            "To-Path",
            "From-Path",
            "Message-ID",
            "Success-Report",
            "Failure-Report",
            "Byte-Range",
            "Status",
            "Content-Type",
        ]

        content_start_line = 0
        end_of_message_line = 0
        for line_num, line in enumerate(lines[1:], start=1):
            if line.strip() == "":
                # We've found the content separator - add 1 to skip the linebreak, and abort header parsing
                content_start_line = line_num + 1
                break

            m = re.match(HEADER_REGEX, line)
            if not m:
                # Maybe we got to the end, and this line is the last?
                if not re.match(END_OF_MESSAGE_REGEX, line):
                    raise MsrpParseError(
                        f"Unexpected format on line {line_num+1}. Expected header, content start, or end of message"
                    )

                content_start_line = line_num
                break

            header_name = m.group(1)
            header_val = m.group(2)
            if header_name not in valid_headers:
                raise MsrpParseError(f"Unexpected header found: {header_name}")

            message.headers[header_name] = header_val

        # If there is content, we'll need to treat it
        if content_start_line:
            # ..but it's only really content until there's a message end marker
            for line_count, line in enumerate(lines[content_start_line:]):
                if re.match(END_OF_MESSAGE_REGEX, line):
                    end_of_message_line = content_start_line + line_count
                    break

            if not end_of_message_line:
                raise MsrpParseError("Could not find end of message line!")

            message.content = lines[content_start_line:end_of_message_line]
            last_processed_line = content_start_line + line_count
        else:
            last_processed_line = line_num

        # We're done processing. Verify that there's no more content afterwards
        if len(lines) > last_processed_line + 1:
            raise MsrpParseError(
                "More lines found in MSRP message after message end marker "
                f"(total lines: {len(lines)}, last parsed line: {last_processed_line})"
            )

        return message


# NOTE: Default MSRP port is 2855 -> rfc4975, section 15.4
