import 'package:flutter/material.dart';
import '../../../../core/theme/app_theme.dart';
import '../../data/datasources/production_remote_datasource.dart';
import '../../data/repositories/production_repository_impl.dart';
import '../../domain/entities/recipe.dart';

class RecipeDetailPage extends StatelessWidget {
  const RecipeDetailPage({
    super.key,
    required this.recipeId,
    this.initialRecipe,
  });

  final int recipeId;
  final Recipe? initialRecipe;

  @override
  Widget build(BuildContext context) {
    final repo = ProductionRepositoryImpl(ProductionRemoteDataSource());
    return Scaffold(
      appBar: AppBar(title: const Text('Detalle de Receta')),
      body: FutureBuilder<Recipe>(
        future:
            initialRecipe != null
                ? Future.value(initialRecipe)
                : repo.getRecipe(recipeId),
        builder: (context, snapshot) {
          if (snapshot.connectionState != ConnectionState.done) {
            return const Center(child: CircularProgressIndicator());
          }
          if (!snapshot.hasData) {
            return Center(
              child: Text(
                snapshot.error?.toString() ?? 'No se pudo cargar la receta',
                style: const TextStyle(color: DesertBrewColors.error),
              ),
            );
          }
          final recipe = snapshot.data!;
          return ListView(
            padding: const EdgeInsets.all(16),
            children: [
              Text(
                recipe.name,
                style: const TextStyle(
                  fontWeight: FontWeight.bold,
                  fontSize: 22,
                ),
              ),
              const SizedBox(height: 4),
              Text(
                recipe.style ?? 'Estilo no definido',
                style: const TextStyle(
                  color: DesertBrewColors.textHint,
                  fontSize: 13,
                ),
              ),
              const SizedBox(height: 16),
              _StatRow(
                'Batch',
                '${recipe.batchSizeLiters.toStringAsFixed(1)} L',
              ),
              _StatRow(
                'ABV objetivo',
                recipe.expectedAbv != null
                    ? '${recipe.expectedAbv!.toStringAsFixed(1)}%'
                    : '—',
              ),
              _StatRow(
                'IBU',
                recipe.ibu != null ? recipe.ibu!.toStringAsFixed(0) : '—',
              ),
              _StatRow(
                'SRM',
                recipe.colorSrm != null
                    ? recipe.colorSrm!.toStringAsFixed(1)
                    : '—',
              ),
              _StatRow(
                'OG / FG',
                '${recipe.expectedOg?.toStringAsFixed(3) ?? '—'} / ${recipe.expectedFg?.toStringAsFixed(3) ?? '—'}',
              ),
              if (recipe.notes != null && recipe.notes!.trim().isNotEmpty) ...[
                const SizedBox(height: 12),
                Text(
                  recipe.notes!,
                  style: const TextStyle(color: DesertBrewColors.textSecondary),
                ),
              ],
              const SizedBox(height: 20),
              _SectionTitle('Fermentables'),
              ...recipe.fermentables.map(
                (f) => _Line(
                  f.name,
                  '${f.amountKg.toStringAsFixed(2)} kg${f.sku == null || f.sku!.isEmpty ? '' : ' · ${f.sku}'}',
                ),
              ),
              const SizedBox(height: 16),
              _SectionTitle('Lupulos'),
              ...recipe.hops.map(
                (h) => _Line(
                  h.name,
                  '${h.amountG.toStringAsFixed(1)} g · ${h.timeMim?.toStringAsFixed(0) ?? '0'} min${h.sku == null || h.sku!.isEmpty ? '' : ' · ${h.sku}'}',
                ),
              ),
              if (recipe.yeast.isNotEmpty) ...[
                const SizedBox(height: 16),
                _SectionTitle('Levadura'),
                ...recipe.yeast.map((y) {
                  final packets = (y['amount_packets'] as num?)?.toDouble();
                  final type = y['type']?.toString();
                  final sku = y['sku']?.toString();
                  final parts = <String>[
                    if (type != null && type.isNotEmpty) type,
                    if (packets != null) '${packets.toStringAsFixed(2)} pkg',
                    if (sku != null && sku.isNotEmpty) sku,
                  ];
                  return _Line(
                    y['name']?.toString() ?? 'Levadura',
                    parts.join(' · '),
                  );
                }),
              ],
              if (recipe.waterProfile != null &&
                  recipe.waterProfile!.isNotEmpty) ...[
                const SizedBox(height: 16),
                _SectionTitle('Perfil de Agua (ppm)'),
                _Line(
                  'Ca / Mg / Na',
                  '${(recipe.waterProfile!['ca'] ?? '—').toString()} / ${(recipe.waterProfile!['mg'] ?? '—').toString()} / ${(recipe.waterProfile!['na'] ?? '—').toString()}',
                ),
                _Line(
                  'Cl / SO4 / HCO3',
                  '${(recipe.waterProfile!['cl'] ?? '—').toString()} / ${(recipe.waterProfile!['so4'] ?? '—').toString()} / ${(recipe.waterProfile!['hco3'] ?? '—').toString()}',
                ),
              ],
            ],
          );
        },
      ),
    );
  }
}

class _SectionTitle extends StatelessWidget {
  const _SectionTitle(this.text);
  final String text;

  @override
  Widget build(BuildContext context) {
    return Text(
      text,
      style: const TextStyle(
        color: DesertBrewColors.textSecondary,
        fontWeight: FontWeight.bold,
        fontSize: 13,
      ),
    );
  }
}

class _StatRow extends StatelessWidget {
  const _StatRow(this.label, this.value);
  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 6),
      child: Row(
        children: [
          SizedBox(
            width: 120,
            child: Text(
              label,
              style: const TextStyle(color: DesertBrewColors.textHint),
            ),
          ),
          Expanded(
            child: Text(
              value,
              style: const TextStyle(fontWeight: FontWeight.w600),
            ),
          ),
        ],
      ),
    );
  }
}

class _Line extends StatelessWidget {
  const _Line(this.title, this.subtitle);
  final String title;
  final String subtitle;

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.only(top: 8),
      padding: const EdgeInsets.all(10),
      decoration: BoxDecoration(
        color: DesertBrewColors.surface,
        borderRadius: BorderRadius.circular(10),
      ),
      child: Row(
        children: [
          Expanded(
            child: Text(
              title,
              style: const TextStyle(fontWeight: FontWeight.w600),
            ),
          ),
          Text(
            subtitle,
            style: const TextStyle(
              color: DesertBrewColors.textHint,
              fontSize: 12,
            ),
          ),
        ],
      ),
    );
  }
}
