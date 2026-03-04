import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'core/theme/app_theme.dart';

/// App shell with bottom navigation bar for main sections.
///
/// Persists across route changes via [ShellRoute].
class AppShell extends StatelessWidget {
  const AppShell({super.key, required this.child});

  final Widget child;

  static const _navItems = [
    _NavItem(icon: Icons.dashboard_rounded, label: 'Inicio', path: '/'),
    _NavItem(icon: Icons.inventory_2_rounded, label: 'Inventario', path: '/inventory'),
    _NavItem(icon: Icons.point_of_sale_rounded, label: 'Ventas', path: '/sales'),
    _NavItem(icon: Icons.science_rounded, label: 'Producción', path: '/production'),
    _NavItem(icon: Icons.account_balance_rounded, label: 'Finanzas', path: '/finance'),
  ];

  int _currentIndex(BuildContext context) {
    final location = GoRouterState.of(context).uri.toString();
    for (var i = _navItems.length - 1; i >= 0; i--) {
      if (location.startsWith(_navItems[i].path)) return i;
    }
    return 0;
  }

  @override
  Widget build(BuildContext context) {
    final index = _currentIndex(context);

    return Scaffold(
      body: child,
      bottomNavigationBar: NavigationBar(
        selectedIndex: index,
        onDestinationSelected: (i) => context.go(_navItems[i].path),
        backgroundColor: DesertBrewColors.surface,
        indicatorColor: DesertBrewColors.primary.withValues(alpha: 0.2),
        destinations: _navItems
            .map(
              (item) => NavigationDestination(
                icon: Icon(item.icon),
                selectedIcon: Icon(item.icon, color: DesertBrewColors.primary),
                label: item.label,
              ),
            )
            .toList(),
      ),
    );
  }
}

class _NavItem {
  const _NavItem({
    required this.icon,
    required this.label,
    required this.path,
  });

  final IconData icon;
  final String label;
  final String path;
}
