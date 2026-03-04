import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import '../../../../core/theme/app_theme.dart';
import '../../data/datasources/inventory_remote_datasource.dart';
import '../../data/repositories/inventory_repository_impl.dart';
import '../../domain/entities/supplier.dart';
import '../bloc/supplier/supplier_bloc.dart';

class SupplierListPage extends StatelessWidget {
  const SupplierListPage({super.key});

  @override
  Widget build(BuildContext context) {
    return BlocProvider(
      create: (_) => SupplierBloc(
        InventoryRepositoryImpl(InventoryRemoteDataSource()),
      )..add(SupplierLoadRequested()),
      child: const _SupplierListView(),
    );
  }
}

class _SupplierListView extends StatelessWidget {
  const _SupplierListView();

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Proveedores'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh_rounded),
            onPressed: () =>
                context.read<SupplierBloc>().add(SupplierLoadRequested()),
          ),
        ],
      ),
      body: BlocBuilder<SupplierBloc, SupplierState>(
        builder: (context, state) {
          if (state is SupplierLoading || state is SupplierInitial) {
            return const Center(child: CircularProgressIndicator());
          }
          if (state is SupplierError) {
            return Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  const Icon(Icons.wifi_off_rounded,
                      size: 64, color: DesertBrewColors.error),
                  const SizedBox(height: 12),
                  Text(state.message,
                      style: const TextStyle(
                          color: DesertBrewColors.textHint, fontSize: 12),
                      textAlign: TextAlign.center),
                  const SizedBox(height: 12),
                  ElevatedButton(
                    onPressed: () => context
                        .read<SupplierBloc>()
                        .add(SupplierLoadRequested()),
                    child: const Text('Reintentar'),
                  ),
                ],
              ),
            );
          }
          if (state is SupplierLoaded) {
            if (state.suppliers.isEmpty) {
              return const Center(
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Icon(Icons.business_rounded,
                        size: 64, color: DesertBrewColors.textHint),
                    SizedBox(height: 12),
                    Text('Sin proveedores registrados',
                        style:
                            TextStyle(color: DesertBrewColors.textSecondary)),
                  ],
                ),
              );
            }
            return ListView.builder(
              padding: const EdgeInsets.all(8),
              itemCount: state.suppliers.length,
              itemBuilder: (_, i) =>
                  _SupplierTile(supplier: state.suppliers[i]),
            );
          }
          return const SizedBox.shrink();
        },
      ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: () => _showCreateDialog(context),
        icon: const Icon(Icons.add_rounded),
        label: const Text('Nuevo Proveedor'),
      ),
    );
  }

  void _showCreateDialog(BuildContext context) {
    final nameCtrl = TextEditingController();
    final rfcCtrl = TextEditingController();
    final phoneCtrl = TextEditingController();
    final emailCtrl = TextEditingController();
    final formKey = GlobalKey<FormState>();

    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Nuevo Proveedor'),
        content: Form(
          key: formKey,
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              TextFormField(
                controller: nameCtrl,
                decoration: const InputDecoration(labelText: 'Nombre *'),
                validator: (v) =>
                    (v == null || v.isEmpty) ? 'Requerido' : null,
              ),
              TextFormField(
                controller: rfcCtrl,
                decoration: const InputDecoration(labelText: 'RFC'),
              ),
              TextFormField(
                controller: phoneCtrl,
                decoration: const InputDecoration(labelText: 'Teléfono'),
              ),
              TextFormField(
                controller: emailCtrl,
                decoration: const InputDecoration(labelText: 'Email'),
              ),
            ],
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx),
            child: const Text('Cancelar'),
          ),
          FilledButton(
            onPressed: () {
              if (formKey.currentState!.validate()) {
                context.read<SupplierBloc>().add(SupplierCreateSubmitted(
                      name: nameCtrl.text.trim(),
                      rfc: rfcCtrl.text.trim().isNotEmpty
                          ? rfcCtrl.text.trim()
                          : null,
                      phone: phoneCtrl.text.trim().isNotEmpty
                          ? phoneCtrl.text.trim()
                          : null,
                      email: emailCtrl.text.trim().isNotEmpty
                          ? emailCtrl.text.trim()
                          : null,
                    ));
                Navigator.pop(ctx);
              }
            },
            child: const Text('Guardar'),
          ),
        ],
      ),
    );
  }
}

class _SupplierTile extends StatelessWidget {
  const _SupplierTile({required this.supplier});
  final Supplier supplier;

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: const EdgeInsets.only(bottom: 8),
      child: ListTile(
        leading: CircleAvatar(
          backgroundColor:
              DesertBrewColors.primary.withValues(alpha: 0.15),
          child: Text(
            supplier.name[0].toUpperCase(),
            style: const TextStyle(
                color: DesertBrewColors.primary,
                fontWeight: FontWeight.bold),
          ),
        ),
        title: Text(supplier.name,
            style: const TextStyle(fontWeight: FontWeight.w600)),
        subtitle: Text(
          [
            if (supplier.rfc != null) 'RFC: ${supplier.rfc}',
            if (supplier.phone != null) '📞 ${supplier.phone}',
            if (supplier.email != null) supplier.email!,
          ].join(' · '),
          style: const TextStyle(
              color: DesertBrewColors.textHint, fontSize: 12),
        ),
        trailing: supplier.isActive
            ? const Icon(Icons.check_circle_rounded,
                color: DesertBrewColors.success, size: 18)
            : const Icon(Icons.cancel_rounded,
                color: DesertBrewColors.error, size: 18),
      ),
    );
  }
}
