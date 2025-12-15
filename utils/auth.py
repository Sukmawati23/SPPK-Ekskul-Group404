# utils/auth.py
import hashlib
import json
import os

USER_DB = "data/users.json"

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def load_users():
    if not os.path.exists(USER_DB):
        os.makedirs(os.path.dirname(USER_DB), exist_ok=True)
        with open(USER_DB, "w") as f:
            json.dump({}, f)
        return {}
    with open(USER_DB, "r") as f:
        return json.load(f)

def save_users(users):
    with open(USER_DB, "w") as f:
        json.dump(users, f, indent=4)

def register_user(email: str, password: str) -> bool:
    users = load_users()
    if email in users:
        return False  # Email sudah terdaftar
    users[email] = hash_password(password)
    save_users(users)
    return True

def authenticate_user(email: str, password: str) -> bool:
    users = load_users()
    if email not in users:
        return False
    return users[email] == hash_password(password)

def reset_password(email: str, new_password: str) -> bool:
    """Reset password untuk email yang sudah terdaftar."""
    users = load_users()
    if email not in users:
        return False
    users[email] = hash_password(new_password)
    save_users(users)
    return True