import 'dart:convert';
import 'package:cryptography/cryptography.dart';
import 'package:logger/logger.dart';

/// Ed25519 key management and signature creation for mobile devices.
///
/// Implements the crypto requirements from Desert Brew Constitution:
/// - Private keys live in Mobile Secure Storage
/// - Public keys are transmitted to the backend (Security Service)
/// - Deliveries (PoD) are JSON payloads signed offline
class Ed25519Manager {
  Ed25519Manager();

  final Logger _logger = Logger(
    printer: PrettyPrinter(methodCount: 0),
  );

  final _algorithm = Ed25519();

  SimpleKeyPair? _keyPair;

  /// Generate a new Ed25519 key pair.
  ///
  /// Returns the public key hex for enrollment with Security Service.
  Future<String> generateKeyPair() async {
    final keyPair = await _algorithm.newKeyPair();
    _keyPair = keyPair;

    final publicKey = await keyPair.extractPublicKey();
    final publicKeyHex = _bytesToHex(publicKey.bytes);

    _logger.i('Ed25519: Generated new key pair');
    _logger.d('Public key: $publicKeyHex');

    return publicKeyHex;
  }

  /// Sign a JSON payload and return the signature hex.
  ///
  /// Used for Proof of Delivery (PoD) signing when offline.
  Future<String> signPayload(Map<String, dynamic> payload) async {
    if (_keyPair == null) {
      throw StateError('No key pair generated. Call generateKeyPair() first.');
    }

    // Canonical JSON encoding (sorted keys for deterministic signing)
    final jsonString = _canonicalJson(payload);
    final data = utf8.encode(jsonString);

    final signature = await _algorithm.sign(data, keyPair: _keyPair!);
    final signatureHex = _bytesToHex(signature.bytes);

    _logger.d(
      'Ed25519: Signed payload (${data.length} bytes) → signature: '
      '${signatureHex.substring(0, 16)}...',
    );

    return signatureHex;
  }

  /// Get current public key hex (for enrollment).
  Future<String?> getPublicKeyHex() async {
    if (_keyPair == null) return null;
    final publicKey = await _keyPair!.extractPublicKey();
    return _bytesToHex(publicKey.bytes);
  }

  /// Convert bytes to hex string.
  String _bytesToHex(List<int> bytes) {
    return bytes.map((b) => b.toRadixString(16).padLeft(2, '0')).join();
  }

  /// Canonical JSON: sorted keys for deterministic signing.
  String _canonicalJson(Map<String, dynamic> data) {
    final sorted = Map.fromEntries(
      data.entries.toList()..sort((a, b) => a.key.compareTo(b.key)),
    );
    return jsonEncode(sorted);
  }
}
