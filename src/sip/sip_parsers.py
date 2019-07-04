from typing import List, Dict, Any, Callable, Tuple, Union, Optional

import urllib.parse
import re

# Dict of headers that can be shortened to a single letter
COMPACT_HEADERS = {
    "i": "call-id",
    "m": "contact",
    "e": "contact-encoding",
    "l": "content-length",
    "c": "content-type",
    "f": "from",
    "s": "subject",
    "k": "supported",
    "t": "to",
    "v": "via",
}


def parse_params(data):
    """ Parse the parameters of the header, separated by semicolons (;) """

    params = {}
    while True:
        m = re.match(
            r'\s*;\s*([\w\-.!%*_+`\'~]+)(?:\s*=\s*([\w\-.!%*_+`\'~]+|"[^"\\]*(\\.[^"\\]*)*"))?',
            data,
        )
        if not m:  # We're done matching
            break

        params[m.group(1).lower()] = m.group(2)
        data = data[m.end() :]

    # Return the list of parameters AND the leftover data
    return params, data


def parse_multiheader(parse_fn: Callable, data: str) -> Tuple[List, str]:
    """ Parse a header that can have multiple values in comma-separated times within the same header line.

        These headers (e.g Contact) can also just appear multiple times in the message, but this function
        just parses a single line. The function with which to parse the header is the first arg
    """
    values = []
    header, data = parse_fn(data)
    values.append(header)

    if data:
        # If there's leftover data, this is probably a multi header
        while True:
            # Find a comma at the start, and discard it, then parse the header
            m = re.match(r"^\s*,\s*", data)
            if not m:
                break  # ... until no more commas exist

            header, data = parse_fn(data[m.end() :])
            values.append(header)

    return values, data


def parse_via(data: str):
    m = re.match(r"SIP\s*\/\s*(\d+\.\d+)\s*\/\s*([\S]+)\s+([^\s;:]+)(?:\s*:\s*(\d+))?", data)
    if not m:
        raise RuntimeError("Could not parse Via header!")

    params, data = parse_params(data[m.end() :])
    val = {
        "version": m.group(1),  # Can be None!
        "protocol": m.group(2),
        "host": m.group(3),
        "port": int(m.group(4)) if m.group(4) else None,
        "params": params,
    }

    return val, data


def parse_auth_header_with_scheme(data: str):
    """ Parse an auth header that begins with a scheme """
    sch_match = re.match(r"([^\s]*)\s+", data)
    if not sch_match:
        raise RuntimeError("Could not extract scheme from authentication header")

    val, data = parse_auth_header(data[sch_match.end() :])
    val["scheme"] = sch_match.group(1)

    return val, data


def parse_auth_header(data: str):
    """ Parse an auth header (without a prefix scheme) """
    val = {}
    while True:
        m = re.match(r'([^\s,"=]*)\s*=\s*([^\s,"]+|"[^"\\]*(?:\\.[^"\\]*)*")\s*', data)
        if not m:  # We're done processing
            break

        # Extract the rest of the information, one by one
        val[m.group(1)] = m.group(2)
        data = data[m.end() :]

        # There must be a comma now, or we're done
        if not data or data[0] != ",":
            break

        data = data[
            1:
        ].lstrip()  # Skip the comma and strip whitespace right after the comma and before the data

    return val, data


def parse_cseq(data: str) -> Dict[str, Any]:
    """ Parses a CSeq header value (<number> <method>)"""
    m = re.match(r"(\d+)\s*([\S]+)", data)
    if not m:
        raise RuntimeError("Could not parse CSeq header")

    return {"seq": int(m.group(1)), "method": urllib.parse.unquote(m.group(2))}


def parse_aor(data: str):
    """ Parses an Address Of Record """

    aor_match = re.match(
        r'((?:[\w\-.!%*_+`\'~]+)(?:\s+[\w\-.!%*_+`\'~]+)*|"[^"\\]*(?:\\.[^"\\]*)*")?\s*\<\s*([^>]*)\s*\>|((?:[^\s@"<]@)?[^\s;]+)',
        data,
    )
    if not aor_match:
        raise RuntimeError('Invalid AOR found: "%s"' % data)

    name = aor_match.group(1)
    uri = ""
    if aor_match.group(2):
        uri = aor_match.group(2)
    elif aor_match.group(3):
        uri = aor_match.group(3)

    params, data = parse_params(data[aor_match.end() :])
    props = {"name": name, "uri": uri, "params": params}  # Can be None!

    # Return the extracted header and leftover data
    return props, data


def parse_uri(uri: str):
    """ Breaks down a URI into its different components """
    m = re.match(
        r"^(sips?):(?:([^\s>:@]+)(?::([^\s@>]+))?@)?([\w\-\.]+)(?::(\d+))?((?:;[^\s=\?>;]+(?:=[^\s?\;]+)?)*)(?:\?(([^\s&=>]+=[^\s&=>]+)(&[^\s&=>]+=[^\s&=>]+)*))?$",
        uri,
    )
    if not m:
        raise RuntimeError('Could not parse URI: "%s"' % uri)

    # Extract params
    params: Dict[str, Optional[str]] = {}
    if m.group(6):
        for param_m in re.finditer(r"([^;=]+)(=([^;=]+))?", m.group(6)):
            if m.group(2):
                params[param_m.group(1)] = param_m.group(2)
            else:
                # The param has no specific value (e.g loose routing indicator, ;lr)
                params[param_m.group(1)] = None

    # Extract headers
    headers: Dict[str, str] = {}
    if m.group(7):
        for header_m in re.finditer(r"([^&=]+)=([^&=]+)", m.group(7)):
            headers[header_m.group(1)] = header_m.group(2)

    if m.group(5):
        try:
            port = int(m.group(5))
        except ValueError:
            raise RuntimeError("Invalid port in route (couldn't cast to a valid int)")
    else:
        port = None

    return {
        "schema": m.group(1),
        "user": m.group(2),
        "password": m.group(3),
        "host": m.group(4),
        "port": port,
        "params": params,
        "headers": headers,
    }


def parse_aor_with_uri(data: str) -> Tuple[Dict, str]:
    """ Parses AOR and then parses the URI that we extracted """
    props, data = parse_aor(data)
    if not props["uri"]:
        raise RuntimeError("There's no URI to parse when trying to parse AOR with URI")

    props["uri"] = parse_uri(props["uri"])
    return props, data


def parse_response(lines: List[str]) -> Optional[Dict[str, Any]]:
    res_match = re.match(r"^SIP\/(\d+\.\d+)\s+(\d+)\s*(.*)\s*$", lines[0])
    if not res_match:
        return None

    return {
        "version": res_match.group(1),
        "status": int(res_match.group(2)),
        "reason": res_match.group(3),
    }


def parse_request(lines: List[str]) -> Optional[Dict[str, Any]]:
    req_match = re.match(r"^([\w\-.!%*_+`'~]+)\s([^\s]+)\sSIP\s*\/\s*(\d+\.\d+)", lines[0])
    if not req_match:
        return None

    return {
        "method": urllib.parse.unquote(req_match.group(1)),
        "uri": req_match.group(2),
        "version": req_match.group(3),
    }
