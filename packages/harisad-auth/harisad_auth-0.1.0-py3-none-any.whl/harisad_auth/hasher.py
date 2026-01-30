import hashlib
import hmac
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

class SecureHasher:
    def __init__(self, pepper: str, hash_len: int = 64):
        self.pepper = pepper
        self.ph = PasswordHasher(
            time_cost=3,
            memory_cost=65536,
            parallelism=4,
            hash_len=hash_len,  # Menghasilkan hash panjang
            salt_len=16
        )

    def hash_password(self, password: str) -> str:
        # Layer 1: HMAC-SHA512 (Peppered)
        pre_hash = hmac.new(self.pepper.encode(), password.encode(), hashlib.sha512).hexdigest()
        # Layer 2: Argon2id
        return self.ph.hash(pre_hash)

    def verify_password(self, hashed: str, password: str) -> bool:
        pre_hash = hmac.new(self.pepper.encode(), password.encode(), hashlib.sha512).hexdigest()
        try:
            return self.ph.verify(hashed, pre_hash)
        except (VerifyMismatchError, Exception):
            return False