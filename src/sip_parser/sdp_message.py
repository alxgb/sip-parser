""" SDP message parser following RFC4566 """
from typing import List, Dict, Any, Optional, Union

import re
from sip_parser.exceptions import SdpParseError
from sip_parser.helpers.sdp_parsers import parse_functions
from sip_parser.sdp_fields import FieldRaw, TimeDescription, MediaDescription

REPEATABLE_HEADER_NAMES = ("b", "r", "a")


class SdpMessage:
    def __init__(self):
        self.session_description_fields: Dict[str, Any] = {}
        self.time_descriptions: List[Dict[str, Any]] = []
        self.media_descriptions: List[Dict[str, Any]] = []

    def add_session_description_field(self, name, value):
        if name in REPEATABLE_HEADER_NAMES:
            if name not in self.session_description_fields:
                self.session_description_fields[name] = []

            self.session_description_fields[name].append(value)
        else:
            self.session_description_fields[name] = value

    def add_time_description(self, time_desc):
        self.time_descriptions.append(time_desc)

    def add_media_description(self, media_desc):
        self.media_descriptions.append(media_desc)

    @staticmethod
    def from_string(raw_message: str):
        sdp_msg = SdpMessage()
        lines = [line.strip().split("=", maxsplit=1) for line in raw_message.split("\n")]

        fields_order = ""
        fields = []
        for line in lines:
            name, value = line[0], line[1]
            fields_order += name
            fields.append(FieldRaw(name, value))

        # This is the right order for the headers (repetition/optionality too)
        # If this doesn't match, it's the wrong order.
        m = re.match(r"vosi?u?e?p?c?b*(tr?)+z?k?a?(mi?c?b*k?a*)*", fields_order)
        if not m:
            raise SdpParseError(f"Incorrect SDP header order detected")

        # Now that we know how they're properly sorted, we can process the time descriptors
        time_fields = [field for field in fields if field.name in ("t", "r")]
        cur_time_attrs = {"timing": None, "repeat_times": []}
        for i, field in enumerate(time_fields):
            parsed_value = parse_functions[field.name](field.value)
            if field.name == "t":
                cur_time_attrs["timing"] = parsed_value
            else:
                cur_time_attrs["repeat_times"].append(parsed_value)

            # Determine if we're done with this time description: This happens when we either
            # are on a "r" attribute or there's "t" attribute next. If so, save it
            if i + 1 >= len(time_fields) or time_fields[i + 1][0] == "t":
                sdp_msg.add_time_description(TimeDescription(**cur_time_attrs))
                cur_time_attrs = {"timing": None, "repeat_times": []}

        # Then, process the media fields
        if "m" in fields_order:
            target_attr_map = {
                "m": "media",
                "i": "media_title",
                "c": "connection_information",
                "b": "bandwidth_information",
                "k": "encryption_key",
                "a": "media_attributes",
            }

            # Factory for new media descriptions
            new_media_desc = lambda: {name: None for name in target_attr_map.values()}

            # Iterate through all media fields
            cur_media_desc_attrs = new_media_desc()
            media_desc_fields = fields[fields_order.index("m") :]
            for i, field in enumerate(media_desc_fields):
                target_key = target_attr_map[field.name]
                processed_value = parse_functions[field.name](field.value)
                if target_key in REPEATABLE_HEADER_NAMES:
                    if cur_media_desc_attrs[target_key] is None:
                        cur_media_desc_attrs[target_key] = []

                    cur_media_desc_attrs[target_key].append(processed_value)
                else:
                    cur_media_desc_attrs[target_key] = processed_value

                # Determine if we're done with this media description. If so, save it
                if i + 1 >= len(media_desc_fields) or media_desc_fields[i + 1][0] == "m":
                    sdp_msg.add_media_description(MediaDescription(**cur_media_desc_attrs))
                    cur_media_desc_attrs = new_media_desc()

            # *Discard* the media fields
            fields = fields[: fields_order.index("m")]

        # Process the regular session description fields
        session_fields = [field for field in fields if field.name not in ("t", "r")]
        for i, field in enumerate(session_fields):
            sdp_msg.add_session_description_field(
                name=field.name, value=parse_functions[field.name](field.value)
            )

        return sdp_msg
