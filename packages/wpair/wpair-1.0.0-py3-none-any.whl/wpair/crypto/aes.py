"""AES encryption utilities for Fast Pair protocol."""

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend


def aes_encrypt_ecb(key: bytes, plaintext: bytes) -> bytes:
    """
    AES-ECB encryption without padding.

    Args:
        key: 16-byte AES key
        plaintext: Data to encrypt (must be multiple of 16)

    Returns:
        Encrypted ciphertext
    """
    cipher = Cipher(
        algorithms.AES(key[:16]),
        modes.ECB(),
        backend=default_backend()
    )
    encryptor = cipher.encryptor()
    return encryptor.update(plaintext) + encryptor.finalize()


def aes_decrypt_ecb(key: bytes, ciphertext: bytes) -> bytes:
    """
    AES-ECB decryption without padding.

    Args:
        key: 16-byte AES key
        ciphertext: Data to decrypt

    Returns:
        Decrypted plaintext
    """
    cipher = Cipher(
        algorithms.AES(key[:16]),
        modes.ECB(),
        backend=default_backend()
    )
    decryptor = cipher.decryptor()
    return decryptor.update(ciphertext) + decryptor.finalize()
