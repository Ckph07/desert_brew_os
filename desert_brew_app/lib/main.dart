import 'package:flutter/material.dart';
import 'core/theme/app_theme.dart';
import 'app_router.dart';
import 'core/sync/sync_manager.dart';
import 'features/production/domain/entities/style_guidelines.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await BeerStyleGuidelines.initialize();
  await SyncManager.instance.initialize();
  runApp(const DesertBrewApp());
}

class DesertBrewApp extends StatelessWidget {
  const DesertBrewApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp.router(
      title: 'Desert Brew OS',
      debugShowCheckedModeBanner: false,
      theme: AppTheme.darkTheme,
      routerConfig: AppRouter.router,
    );
  }
}
