import hashlib

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(stored_password: str, input_password: str) -> bool:
    return stored_password == hash_password(input_password) 