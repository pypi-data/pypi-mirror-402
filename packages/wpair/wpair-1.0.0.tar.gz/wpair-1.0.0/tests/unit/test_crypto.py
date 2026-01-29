"""Unit tests for cryptography utilities."""

import pytest
from wpair.crypto.ecdh import generate_ecdh_keypair, compute_shared_secret, get_public_key_bytes
from wpair.crypto.aes import aes_encrypt_ecb, aes_decrypt_ecb


def test_generate_ecdh_keypair():
    """Test ECDH key pair generation."""
    private_key, public_key = generate_ecdh_keypair()

    assert private_key is not None
    assert public_key is not None

    # Verify key types
    from cryptography.hazmat.primitives.asymmetric import ec
    assert isinstance(private_key, ec.EllipticCurvePrivateKey)
    assert isinstance(public_key, ec.EllipticCurvePublicKey)


def test_get_public_key_bytes():
    """Test public key serialization."""
    _, public_key = generate_ecdh_keypair()

    public_bytes = get_public_key_bytes(public_key)

    # Uncompressed point without prefix should be 64 bytes (32 bytes X + 32 bytes Y)
    assert len(public_bytes) == 64


def test_compute_shared_secret():
    """Test ECDH shared secret computation."""
    # Generate two key pairs
    private_key1, public_key1 = generate_ecdh_keypair()
    private_key2, public_key2 = generate_ecdh_keypair()

    # Compute shared secrets from both sides
    shared_secret1 = compute_shared_secret(private_key1, public_key2)
    shared_secret2 = compute_shared_secret(private_key2, public_key1)

    # Both parties should compute the same shared secret
    assert shared_secret1 == shared_secret2
    assert len(shared_secret1) == 32  # secp256r1 produces 32-byte shared secret


def test_aes_encrypt_decrypt():
    """Test AES encryption and decryption."""
    key = b'\x00' * 16
    plaintext = b'Hello World!!!!!'  # 16 bytes

    ciphertext = aes_encrypt_ecb(key, plaintext)
    decrypted = aes_decrypt_ecb(key, ciphertext)

    assert decrypted == plaintext
    assert ciphertext != plaintext  # Should be encrypted


def test_aes_with_different_keys():
    """Test that different keys produce different ciphertexts."""
    key1 = b'\x00' * 16
    key2 = b'\xFF' * 16
    plaintext = b'TestData12345678'  # Exactly 16 bytes

    ciphertext1 = aes_encrypt_ecb(key1, plaintext)
    ciphertext2 = aes_encrypt_ecb(key2, plaintext)

    assert ciphertext1 != ciphertext2


def test_aes_account_key_encryption():
    """Test Account Key encryption format used in Fast Pair."""
    key = b'\x01\x02\x03\x04' * 4  # 16 bytes
    account_key = bytearray(16)
    account_key[0] = 0x04  # Account Key marker
    account_key[1:] = b'\xAA' * 15

    encrypted = aes_encrypt_ecb(key, bytes(account_key))

    assert len(encrypted) == 16
    assert encrypted != account_key  # Should be different after encryption

    # Decrypt to verify
    decrypted = aes_decrypt_ecb(key, encrypted)
    assert decrypted == bytes(account_key)


def test_aes_multiple_blocks():
    """Test AES with multiple 16-byte blocks."""
    key = b'\x12\x34\x56\x78' * 4
    plaintext = b'Block1Data123456Block2Data123456'  # Exactly 32 bytes (2 blocks)

    ciphertext = aes_encrypt_ecb(key, plaintext)
    decrypted = aes_decrypt_ecb(key, ciphertext)

    assert len(ciphertext) == 32
    assert decrypted == plaintext
