import 'package:flutter/material.dart';
import '../../../../core/theme/app_theme.dart';

/// Employee list — Brewery + Taproom staff with payroll details.
class EmployeeListPage extends StatelessWidget {
  const EmployeeListPage({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Nómina')),
      body: const Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.badge_rounded, size: 64, color: DesertBrewColors.textHint),
            SizedBox(height: 16),
            Text('Employee Management', style: TextStyle(color: DesertBrewColors.textSecondary)),
            SizedBox(height: 8),
            Text('Cervecería (3 fijos) · Taproom (fijos + temps) · Tip Pool',
                style: TextStyle(color: DesertBrewColors.textHint, fontSize: 12)),
          ],
        ),
      ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: () => ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Alta de empleado pendiente de implementación'),
            backgroundColor: DesertBrewColors.info,
          ),
        ),
        icon: const Icon(Icons.person_add_rounded),
        label: const Text('Nuevo Empleado'),
      ),
    );
  }
}
