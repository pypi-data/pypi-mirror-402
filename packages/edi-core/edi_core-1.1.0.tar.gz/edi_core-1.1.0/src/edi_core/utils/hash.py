import hashlib

algorithms_available = hashlib.algorithms_available


def hash_str(data: str, algo='md5') -> str:
    h = hashlib.new(algo)
    h.update(data.encode('utf-8'))
    return h.hexdigest()
