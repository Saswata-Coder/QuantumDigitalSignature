"""Message preprocessing and digest generation."""

import hashlib


# Encoding the message in UTF-8 Model
def normalize_message(message: str) -> bytes:
    if not isinstance(message, str):
        raise TypeError("message must be a string")
    
    return message.encode("utf-8")


# SHA-256 Hashing to 256 Binary Bit  
def sha256_bits(message: str) -> str:
    digest = hashlib.sha256(normalize_message(message)).digest()
    return "".join(f"{byte:08b}" for byte in digest)


# Returning n bit-length HASH 
def message_digest(message: str, n_bits: int | None = None) -> str:
    bits = sha256_bits(message)
    if n_bits is None : 
        return bits  

    bits[:n_bits]
