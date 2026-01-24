import os
import bcrypt
import pyotp
from cryptography.fernet import Fernet
import hashlib



jwt_secret = os.getenv("JWT_SECRET_KEY", "super-secret-jwt-key-change-me")
aes_secret = os.getenv("AES_SECRET_KEY", Fernet.generate_key().decode())

cipher_suite = Fernet(aes_secret.encode() if isinstance(aes_secret, str) else aes_secret)

def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def check_password(password: str, hashed_password: str) -> bool:
    """Check a password against a hash."""
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))

def generate_totp_uri(username: str) -> str:
    """Generate a new TOTP secret and provisioning URI."""
    secret = pyotp.random_base32()
    uri = pyotp.totp.TOTP(secret).provisioning_uri(name=username, issuer_name="Naya Judicial System")
    return secret, uri

def verify_totp(secret: str, token: str) -> bool:
    """Verify a TOTP token."""
    totp = pyotp.totp.TOTP(secret)
    return totp.verify(token)

def encrypt_data(data: bytes) -> bytes:
    """Encrypt binary data."""
    return cipher_suite.encrypt(data)

def decrypt_data(data: bytes) -> bytes:
    """Decrypt binary data."""
    return cipher_suite.decrypt(data)

def calculate_sha256(data: bytes) -> str:
    """Calculate SHA-256 hash of data."""
    sha256_hash = hashlib.sha256()
    sha256_hash.update(data)
    return sha256_hash.hexdigest()
