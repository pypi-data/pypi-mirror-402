import base64


def decode_base64_to_string(encoded_str: str) -> str:
    assert isinstance(encoded_str, str) and len(encoded_str) > 0, f'String with item required. Object {encoded_str} with type {type(encoded_str)} was given'
    encoded_bytes = encoded_str.encode('utf-8')
    decoded_bytes = base64.b64decode(encoded_bytes)
    decoded_str = decoded_bytes.decode('utf-8')
    return decoded_str
