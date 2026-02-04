"""
Signature Verification Logic for Ed25519.

Purpose: Verify cryptographic signatures from mobile devices for Proof of Delivery.
Uses PyNaCl (libsodium) for Ed25519 operations.
"""
from nacl.signing import VerifyKey
from nacl.exceptions import BadSignatureError
import json
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from typing import Tuple

from models.device_enrollment import DeviceEnrollment, DeviceStatus


class SignatureVerifier:
    """
    Verifies Ed25519 signatures for offline payloads.
    
    Security Guarantees:
    - Cryptographic proof of authenticity (device possesses private key)
    - Timestamp freshness check (prevents replay attacks)
    - Device status validation (only ACTIVE devices)
    """
    
    MAX_PAYLOAD_AGE_SECONDS = 300  # 5 minutes
    
    @staticmethod
    def verify_pod_signature(
        payload: dict,
        signature_hex: str,
        device_id: str,
        db: Session
    ) -> Tuple[bool, str]:
        """
        Verifies Proof of Delivery signature.
        
        Args:
            payload: Dict with delivery data (must include 'timestamp')
            signature_hex: Hex-encoded signature (128 chars)
            device_id: Device identifier
            db: Database session
            
        Returns:
            (is_valid, error_message)
            - (True, "") if signature valid
            - (False, "reason") if invalid
        """
        # 1. Get device public key
        device = db.query(DeviceEnrollment).filter_by(
            device_id=device_id
        ).first()
        
        if not device:
            return (False, f"Device '{device_id}' not enrolled")
        
        if device.status != DeviceStatus.ACTIVE:
            return (False, f"Device '{device_id}' status: {device.status} (expected: ACTIVE)")
        
        # 2. Validate payload contains timestamp
        if 'timestamp' not in payload:
            return (False, "Payload missing required field: 'timestamp'")
        
        # 3. Reconstruct canonical message
        # CRITICAL: Sort keys for deterministic JSON
        try:
            canonical_json = json.dumps(payload, sort_keys=True, separators=(',', ':'))
            message_bytes = canonical_json.encode('utf-8')
        except Exception as e:
            return (False, f"Payload serialization failed: {str(e)}")
        
        # 4. Verify signature
        try:
            verify_key = VerifyKey(bytes.fromhex(device.public_key_ed25519))
            signature_bytes = bytes.fromhex(signature_hex)
            
            # This raises BadSignatureError if invalid
            verify_key.verify(message_bytes, signature_bytes)
            
        except BadSignatureError:
            return (False, "Invalid signature - cryptographic verification failed")
        except ValueError as e:
            return (False, f"Invalid hex encoding: {str(e)}")
        except Exception as e:
            return (False, f"Signature verification error: {str(e)}")
        
        # 5. Check timestamp freshness (prevent replay attacks)
        try:
            payload_timestamp = datetime.fromisoformat(payload['timestamp'])
        except (ValueError, TypeError) as e:
            return (False, f"Invalid timestamp format: {str(e)}")
        
        age_seconds = (datetime.utcnow() - payload_timestamp).total_seconds()
        
        if age_seconds > SignatureVerifier.MAX_PAYLOAD_AGE_SECONDS:
            return (False, f"Payload too old: {age_seconds:.0f}s (max: {SignatureVerifier.MAX_PAYLOAD_AGE_SECONDS}s). Possible replay attack.")
        
        if age_seconds < -60:  # Tolerance for clock skew
            return (False, f"Payload timestamp in future: {abs(age_seconds):.0f}s. Check device clock.")
        
        return (True, "")
    
    @staticmethod
    def verify_signature_only(
        message: bytes,
        signature_hex: str,
        public_key_hex: str
    ) -> bool:
        """
        Verify signature without database lookup (for testing).
        
        Args:
            message: Raw bytes to verify
            signature_hex: Signature (hex)
            public_key_hex: Public key (hex)
            
        Returns:
            True if valid, False otherwise
        """
        try:
            verify_key = VerifyKey(bytes.fromhex(public_key_hex))
            signature_bytes = bytes.fromhex(signature_hex)
            verify_key.verify(message, signature_bytes)
            return True
        except:
            return False
