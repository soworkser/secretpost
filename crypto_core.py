"""
SecretPost — Crypto Core
AES-256-GCM encryption with PBKDF2 key derivation
"""

import os
import base64
import hashlib
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.exceptions import InvalidTag


PBKDF2_ITERATIONS = 260_000
SALT_SIZE = 16
NONCE_SIZE = 12


def _derive_key(password: str, salt: bytes) -> bytes:
    """Derive a 256-bit AES key from a 10-digit code using PBKDF2-SHA256."""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=PBKDF2_ITERATIONS,
    )
    return kdf.derive(password.encode("utf-8"))


def encrypt(plaintext: str, code: str) -> str:
    """
    Encrypt plaintext with a 10-digit code.
    Returns a Base64-encoded string: SALT + NONCE + CIPHERTEXT+TAG
    """
    salt = os.urandom(SALT_SIZE)
    nonce = os.urandom(NONCE_SIZE)
    key = _derive_key(code, salt)

    aesgcm = AESGCM(key)
    ciphertext = aesgcm.encrypt(nonce, plaintext.encode("utf-8"), None)

    payload = salt + nonce + ciphertext
    return base64.b64encode(payload).decode("ascii")


def decrypt(encoded: str, code: str) -> str:
    """
    Decrypt a Base64-encoded ciphertext with a 10-digit code.
    Raises ValueError on wrong key or corrupted message.
    """
    try:
        payload = base64.b64decode(encoded.strip())
    except Exception:
        raise ValueError("Сообщение повреждено или имеет неверный формат.")

    if len(payload) < SALT_SIZE + NONCE_SIZE + 16:
        raise ValueError("Сообщение слишком короткое — возможно, оно повреждено.")

    salt = payload[:SALT_SIZE]
    nonce = payload[SALT_SIZE:SALT_SIZE + NONCE_SIZE]
    ciphertext = payload[SALT_SIZE + NONCE_SIZE:]

    key = _derive_key(code, salt)
    aesgcm = AESGCM(key)

    try:
        plaintext = aesgcm.decrypt(nonce, ciphertext, None)
        return plaintext.decode("utf-8")
    except InvalidTag:
        raise ValueError("Неверный ключ или сообщение было изменено.")


def validate_code(code: str) -> bool:
    """Check that code is exactly 10 digits."""
    return code.isdigit() and len(code) == 10
