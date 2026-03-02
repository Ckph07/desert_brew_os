import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:desert_brew_app/main.dart';

void main() {
  testWidgets('App renders without exception', (WidgetTester tester) async {
    await tester.pumpWidget(const DesertBrewApp());
    // Verify app scaffold renders
    expect(find.byType(MaterialApp), findsOneWidget);
  });
}
