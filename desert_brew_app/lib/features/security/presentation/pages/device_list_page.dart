import 'package:flutter/material.dart';
import '../../../../core/theme/app_theme.dart';

/// Device list — Ed25519 enrolled devices and status.
class DeviceListPage extends StatelessWidget {
  const DeviceListPage({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Seguridad — Dispositivos')),
      body: const Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.security_rounded, size: 64, color: DesertBrewColors.textHint),
            SizedBox(height: 16),
            Text('Device Enrollment', style: TextStyle(color: DesertBrewColors.textSecondary)),
            SizedBox(height: 8),
            Text('Ed25519 · Heartbeat · Approval · Revocation',
                style: TextStyle(color: DesertBrewColors.textHint, fontSize: 12)),
          ],
        ),
      ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: () => ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Enrollment de dispositivos pendiente de implementación'),
            backgroundColor: DesertBrewColors.info,
          ),
        ),
        icon: const Icon(Icons.phonelink_setup_rounded),
        label: const Text('Enroll Device'),
      ),
    );
  }
}
