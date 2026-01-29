from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.fernet import Fernet, InvalidToken
import base64

def derive_key(secret: str, salt: bytes, iterations: int = 10000):
    secret_bytes = secret.encode("utf-8")
    key_deriver = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=iterations)
    return key_deriver.derive(secret_bytes)

def encrypt(data: str, key: bytes):
    fernet_key = base64.urlsafe_b64encode(key)
    f_key = Fernet(fernet_key)
    return f_key.encrypt(data.encode("utf-8")).decode("utf-8")

def decrypt(encrypted_data: str, key: bytes):
    try:
        fernet_key = base64.urlsafe_b64encode(key)
        f_key = Fernet(fernet_key)
        return f_key.decrypt(encrypted_data.encode("utf-8")).decode("utf-8")
    except InvalidToken:
        return None
