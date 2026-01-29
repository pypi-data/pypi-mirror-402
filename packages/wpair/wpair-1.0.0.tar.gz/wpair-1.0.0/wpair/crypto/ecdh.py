"""ECDH key generation and exchange for Fast Pair protocol."""

from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization
from typing import Tuple


def generate_ecdh_keypair() -> Tuple[ec.EllipticCurvePrivateKey, ec.EllipticCurvePublicKey]:
    """
    Generate ECDH key pair using secp256r1 curve.

    Returns:
        Tuple of (private_key, public_key)
    """
    private_key = ec.generate_private_key(ec.SECP256R1())
    public_key = private_key.public_key()
    return private_key, public_key


def compute_shared_secret(
    private_key: ec.EllipticCurvePrivateKey,
    peer_public_key: ec.EllipticCurvePublicKey
) -> bytes:
    """
    Compute ECDH shared secret.

    Args:
        private_key: Our private key
        peer_public_key: Peer's public key

    Returns:
        Shared secret bytes
    """
    shared_secret = private_key.exchange(ec.ECDH(), peer_public_key)
    return shared_secret


def get_public_key_bytes(public_key: ec.EllipticCurvePublicKey) -> bytes:
    """
    Get public key as uncompressed point (64 bytes: X || Y).

    Args:
        public_key: EC public key

    Returns:
        64-byte uncompressed point (without 0x04 prefix)
    """
    public_bytes = public_key.public_bytes(
        encoding=serialization.Encoding.X962,
        format=serialization.PublicFormat.UncompressedPoint
    )
    # Remove 0x04 prefix
    return public_bytes[1:]
