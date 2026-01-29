def disp_rsa() -> str:
    return """def power(base, expo, m):
    res = 1
    base = base % m
    while expo > 0:
        if expo & 1:
            res = (res * base) % m
        base = (base * base) % m
        expo = expo // 2
    return res


def modInverse(e, phi):
    for d in range(2, phi):
        if (e * d) % phi == 1:
            return d
    return -1


def generateKeys():
    p = 7919
    q = 1009

    n = p * q
    phi = (p - 1) * (q - 1)

    # Choose e, where 1 < e < phi and gcd(e, phi) == 1
    e = 0
    for e in range(2, phi):
        if gcd(e, phi) == 1:
            break

    # Compute d such that e * d % phi == 1
    d = modInverse(e, phi)

    return e, d, n


def gcd(a, b):
    while b != 0:
        a, b = b, a % b
    return a


def encrypt(m, e, n):
    return power(m, e, n)


def decrypt(c, d, n):
    return power(c, d, n)


if __name__ == "__main__":
    e, d, n = generateKeys()

    print(f"Public Key (e, n): ({e}, {n})")
    print(f"Private Key (d, n): ({d}, {n})")

    message = 123
    print(f"Original Message: {message}")

    cipher = encrypt(message, e, n)
    print(f"Encrypted Message: {cipher}")

    decrypted = decrypt(cipher, d, n)
    print(f"Decrypted Message: {decrypted}")"""


def disp_sha() -> str:
    return """import hashlib


def hash(text):
    data = text.encode("utf-8")
    sha256_hash = hashlib.sha256(data).hexdigest()
    sha512_hash = hashlib.sha512(data).hexdigest()
    return sha256_hash, sha512_hash


if __name__ == "__main__":
    hash_256, hash_512 = hash("Hello World")

    print(hash_256)
    print(hash_512)
"""
