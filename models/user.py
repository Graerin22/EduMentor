from dataclasses import dataclass

@dataclass
class User:
    user_id: int
    username: str
    password_hash: str
    salt: str
    encrypted_api_key: str