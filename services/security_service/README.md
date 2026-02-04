# Desert Brew Security Service

Device Enrollment and Cryptographic Verification for offline operations.

## Features

- **Device Enrollment**: Register mobile devices with Ed25519 public keys
- **Signature Verification**: Verify offline Proof of Delivery signatures
- **Device Lifecycle**: PENDING → ACTIVE → REVOKED/SUSPENDED states
- **Heartbeat Monitoring**: Track device check-ins

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/security/enroll` | Request device enrollment |
| PATCH | `/api/v1/security/enrollments/{id}/approve` | Approve pending enrollment (admin) |
| PATCH | `/api/v1/security/enrollments/{id}/revoke` | Revoke device (admin) |
| POST | `/api/v1/security/enrollments/{id}/heartbeat` | Device check-in |
| GET | `/api/v1/security/enrollments` | List devices (admin) |
| POST | `/api/v1/security/verify-signature` | Verify Ed25519 signature |
| GET | `/api/v1/security/enrollments/stats` | Enrollment statistics |

## Security Model

**Cryptography:** Ed25519 (PyNaCl)

```
Mobile App (Offline)                 Backend (Online)
─────────────────────                ────────────────
1. Generate keypair
2. Store private_key in Secure Enclave
3. Send public_key to /enroll    →  Store public_key in DB
                                     Status: PENDING
4. Admin approves                 →  Status: ACTIVE
5. Sign PoD payload                  
   signature = sign(payload)
6. Submit PoD + signature         →  Verify signature
                                     Check timestamp < 5min
                                     ✓ Non-repudiation
```

**No Repudio:** Solo el dispositivo con la private key puede firmar payloads válidos.

## Installation

```bash
cd services/security_service
pip install -r requirements.txt
```

## Run

```bash
uvicorn main:app --reload --port 8003
```

## Database

Requires PostgreSQL. Set `DATABASE_URL`:

```bash
export DATABASE_URL="postgresql://user:pass@localhost:5432/desertbrew_security"
```

## Sprint 3 Status

- [x] DeviceEnrollment model
- [x] SignatureVerifier logic
- [x] 8 API endpoints
- [x] Pydantic schemas with hex validation
- [ ] Tests (in progress)
- [ ] Alembic migrations

**Version:** 0.1.0  
**Part of:** Sprint 3 - Security & B2B Foundations
