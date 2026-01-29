import base64


def encode_base64_str(data: str, encoding: str = 'utf-8'):
    data_bytes = data.encode(encoding)
    base64_bytes = base64.b64encode(data_bytes)
    return base64_bytes.decode(encoding)


def decode_base64_str(data: str, encoding: str = 'utf-8'):
    data_bytes = data.encode(encoding)
    base64_bytes = base64.b64decode(data_bytes)
    return base64_bytes.decode(encoding)


def encode_base64_bytes(data: bytes):
    return base64.b64encode(data)


def decode_base64_bytes(data: bytes):
    return base64.b64decode(data)


def to_bytes(data: str, encoding: str = 'utf-8'):
    return data.encode(encoding)
