import hashlib

def sha256_hash(data):
    return hashlib.sha256(data).hexdigest()

def base58_encode(b):
    alphabet = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'
    num = int.from_bytes(b, 'big')
    encoded = ''
    while num > 0:
        num, rem = divmod(num, 58)
        encoded = alphabet[rem] + encoded
    for byte in b:
        if byte == 0:
            encoded = '1' + encoded
        else:
            break
    return encoded
