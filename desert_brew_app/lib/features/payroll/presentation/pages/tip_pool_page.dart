import 'package:flutter/material.dart';
import '../../../../core/theme/app_theme.dart';

/// Tip pool — Weekly tip distribution for taproom staff.
class TipPoolPage extends StatelessWidget {
  const TipPoolPage({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Pool de Propinas')),
      body: const Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.volunteer_activism_rounded, size: 64, color: DesertBrewColors.textHint),
            SizedBox(height: 16),
            Text('Tip Pool Distribution', style: TextStyle(color: DesertBrewColors.textSecondary)),
            SizedBox(height: 8),
            Text('Sun-Sat · Equal split · Linked to PayrollEntry',
                style: TextStyle(color: DesertBrewColors.textHint, fontSize: 12)),
          ],
        ),
      ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: () => ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Creación de tip pool pendiente de implementación'),
            backgroundColor: DesertBrewColors.info,
          ),
        ),
        icon: const Icon(Icons.add_rounded),
        label: const Text('Nuevo Pool'),
      ),
    );
  }
}
