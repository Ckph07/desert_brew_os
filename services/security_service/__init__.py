"""
Security Service - Device Enrollment and Cryptographic Verification.

Provides:
- Device registration with Ed25519 public keys
- Signature verification for offline Proof of Delivery
- Device lifecycle management (PENDING → ACTIVE → REVOKED)
"""

__version__ = "0.1.0"
