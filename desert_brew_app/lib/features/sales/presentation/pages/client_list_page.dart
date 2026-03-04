import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:go_router/go_router.dart';
import '../../../../core/theme/app_theme.dart';
import '../../data/datasources/sales_remote_datasource.dart';
import '../../data/repositories/sales_repository_impl.dart';
import '../../domain/entities/sales_client.dart';
import '../bloc/client/client_bloc.dart';

class ClientListPage extends StatelessWidget {
  const ClientListPage({super.key});

  @override
  Widget build(BuildContext context) {
    return BlocProvider(
      create:
          (_) =>
              ClientBloc(SalesRepositoryImpl(SalesRemoteDataSource()))
                ..add(ClientLoadRequested()),
      child: const _ClientListView(),
    );
  }
}

class _ClientListView extends StatefulWidget {
  const _ClientListView();

  @override
  State<_ClientListView> createState() => _ClientListViewState();
}

class _ClientListViewState extends State<_ClientListView> {
  final _searchCtrl = TextEditingController();

  @override
  void dispose() {
    _searchCtrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Clientes'),
        actions: [
          IconButton(
            tooltip: 'Ver catálogo',
            icon: const Icon(Icons.inventory_2_rounded),
            onPressed: () => context.push('/sales/products'),
          ),
          IconButton(
            tooltip: 'Ver notas',
            icon: const Icon(Icons.receipt_long_rounded),
            onPressed: () => context.push('/sales/notes'),
          ),
          IconButton(
            icon: const Icon(Icons.refresh_rounded),
            onPressed:
                () => context.read<ClientBloc>().add(ClientLoadRequested()),
          ),
        ],
      ),
      body: Column(
        children: [
          // Search bar
          Padding(
            padding: const EdgeInsets.all(12),
            child: TextField(
              controller: _searchCtrl,
              decoration: InputDecoration(
                hintText: 'Buscar cliente...',
                prefixIcon: const Icon(Icons.search_rounded),
                suffixIcon:
                    _searchCtrl.text.isNotEmpty
                        ? IconButton(
                          icon: const Icon(Icons.clear_rounded),
                          onPressed: () {
                            _searchCtrl.clear();
                            context.read<ClientBloc>().add(
                              ClientLoadRequested(),
                            );
                            setState(() {});
                          },
                        )
                        : null,
              ),
              onChanged: (v) {
                setState(() {});
                context.read<ClientBloc>().add(
                  ClientLoadRequested(search: v.trim()),
                );
              },
            ),
          ),
          Expanded(
            child: BlocBuilder<ClientBloc, ClientState>(
              builder: (context, state) {
                if (state is ClientLoading || state is ClientInitial) {
                  return const Center(child: CircularProgressIndicator());
                }
                if (state is ClientError) {
                  return _ErrorRetry(
                    message: state.message,
                    onRetry:
                        () => context.read<ClientBloc>().add(
                          ClientLoadRequested(),
                        ),
                  );
                }
                if (state is ClientLoaded) {
                  if (state.clients.isEmpty) {
                    return const Center(
                      child: Column(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          Icon(
                            Icons.people_outline_rounded,
                            size: 64,
                            color: DesertBrewColors.textHint,
                          ),
                          SizedBox(height: 12),
                          Text(
                            'Sin clientes',
                            style: TextStyle(
                              color: DesertBrewColors.textSecondary,
                            ),
                          ),
                        ],
                      ),
                    );
                  }
                  return ListView.builder(
                    padding: const EdgeInsets.symmetric(horizontal: 8),
                    itemCount: state.clients.length,
                    itemBuilder:
                        (_, i) => _ClientTile(client: state.clients[i]),
                  );
                }
                return const SizedBox.shrink();
              },
            ),
          ),
        ],
      ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: () => _showCreateDialog(context),
        icon: const Icon(Icons.person_add_rounded),
        label: const Text('Nuevo Cliente'),
      ),
    );
  }

  void _showCreateDialog(BuildContext context) {
    final nameCtrl = TextEditingController();
    final rfcCtrl = TextEditingController();
    final emailCtrl = TextEditingController();
    final phoneCtrl = TextEditingController();
    final creditCtrl = TextEditingController();
    var clientType = 'B2B';
    var pricingTier = 'RETAIL';
    final formKey = GlobalKey<FormState>();

    showDialog(
      context: context,
      builder:
          (ctx) => StatefulBuilder(
            builder:
                (ctx, setSt) => AlertDialog(
                  title: const Text('Nuevo Cliente'),
                  content: SizedBox(
                    width: 400,
                    child: Form(
                      key: formKey,
                      child: SingleChildScrollView(
                        child: Column(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            TextFormField(
                              controller: nameCtrl,
                              decoration: const InputDecoration(
                                labelText: 'Nombre del negocio *',
                              ),
                              validator:
                                  (v) =>
                                      (v == null || v.isEmpty)
                                          ? 'Requerido'
                                          : null,
                            ),
                            TextFormField(
                              controller: rfcCtrl,
                              decoration: const InputDecoration(
                                labelText: 'RFC',
                              ),
                            ),
                            TextFormField(
                              controller: emailCtrl,
                              decoration: const InputDecoration(
                                labelText: 'Email',
                              ),
                            ),
                            TextFormField(
                              controller: phoneCtrl,
                              decoration: const InputDecoration(
                                labelText: 'Teléfono',
                              ),
                            ),
                            TextFormField(
                              controller: creditCtrl,
                              keyboardType:
                                  const TextInputType.numberWithOptions(
                                    decimal: true,
                                  ),
                              decoration: const InputDecoration(
                                labelText: 'Límite de crédito \$',
                              ),
                            ),
                            const SizedBox(height: 12),
                            DropdownButtonFormField<String>(
                              value: clientType,
                              decoration: const InputDecoration(
                                labelText: 'Tipo de cliente',
                              ),
                              items:
                                  ['B2B', 'B2C', 'DISTRIBUTOR']
                                      .map(
                                        (t) => DropdownMenuItem(
                                          value: t,
                                          child: Text(t),
                                        ),
                                      )
                                      .toList(),
                              onChanged: (v) => setSt(() => clientType = v!),
                            ),
                            DropdownButtonFormField<String>(
                              value: pricingTier,
                              decoration: const InputDecoration(
                                labelText: 'Tier de precio',
                              ),
                              items:
                                  ['PLATINUM', 'GOLD', 'SILVER', 'RETAIL']
                                      .map(
                                        (t) => DropdownMenuItem(
                                          value: t,
                                          child: Text(t),
                                        ),
                                      )
                                      .toList(),
                              onChanged: (v) => setSt(() => pricingTier = v!),
                            ),
                          ],
                        ),
                      ),
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
                          context.read<ClientBloc>().add(
                            ClientCreateSubmitted(
                              businessName: nameCtrl.text.trim(),
                              clientType: clientType,
                              pricingTier: pricingTier,
                              rfc:
                                  rfcCtrl.text.trim().isNotEmpty
                                      ? rfcCtrl.text.trim()
                                      : null,
                              email:
                                  emailCtrl.text.trim().isNotEmpty
                                      ? emailCtrl.text.trim()
                                      : null,
                              phone:
                                  phoneCtrl.text.trim().isNotEmpty
                                      ? phoneCtrl.text.trim()
                                      : null,
                              creditLimit: double.tryParse(creditCtrl.text),
                            ),
                          );
                          Navigator.pop(ctx);
                        }
                      },
                      child: const Text('Guardar'),
                    ),
                  ],
                ),
          ),
    );
  }
}

class _ClientTile extends StatelessWidget {
  const _ClientTile({required this.client});
  final SalesClient client;

  Color get _tierColor {
    switch (client.pricingTier) {
      case 'PLATINUM':
        return const Color(0xFF9C27B0);
      case 'GOLD':
        return DesertBrewColors.primary;
      case 'SILVER':
        return Colors.blueGrey;
      default:
        return DesertBrewColors.textHint;
    }
  }

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: const EdgeInsets.only(bottom: 8),
      child: ListTile(
        leading: CircleAvatar(
          backgroundColor: _tierColor.withValues(alpha: 0.15),
          child: Text(
            client.businessName[0].toUpperCase(),
            style: TextStyle(color: _tierColor, fontWeight: FontWeight.bold),
          ),
        ),
        title: Row(
          children: [
            Expanded(
              child: Text(
                client.businessName,
                style: const TextStyle(fontWeight: FontWeight.w600),
              ),
            ),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
              decoration: BoxDecoration(
                color: _tierColor.withValues(alpha: 0.15),
                borderRadius: BorderRadius.circular(8),
              ),
              child: Text(
                client.pricingTier,
                style: TextStyle(color: _tierColor, fontSize: 10),
              ),
            ),
          ],
        ),
        subtitle: Text(
          [
            client.clientCode,
            client.clientType,
            if (client.city != null) client.city!,
            if (!client.hasCredit) '⚠ Crédito agotado',
          ].join(' · '),
          style: const TextStyle(
            color: DesertBrewColors.textHint,
            fontSize: 11,
          ),
        ),
        trailing: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          crossAxisAlignment: CrossAxisAlignment.end,
          children: [
            Text(
              '\$${client.currentBalance.toStringAsFixed(0)}',
              style: TextStyle(
                color:
                    client.currentBalance > 0
                        ? DesertBrewColors.warning
                        : DesertBrewColors.success,
                fontWeight: FontWeight.bold,
                fontSize: 13,
              ),
            ),
            Text(
              '${client.currentKegs} kegs',
              style: const TextStyle(
                color: DesertBrewColors.textHint,
                fontSize: 10,
              ),
            ),
          ],
        ),
        onTap: () => context.push('/sales/clients/${client.id}'),
      ),
    );
  }
}

class _ErrorRetry extends StatelessWidget {
  const _ErrorRetry({required this.message, required this.onRetry});
  final String message;
  final VoidCallback onRetry;

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          const Icon(
            Icons.wifi_off_rounded,
            size: 64,
            color: DesertBrewColors.error,
          ),
          const SizedBox(height: 12),
          Text(
            message,
            style: const TextStyle(
              color: DesertBrewColors.textHint,
              fontSize: 12,
            ),
            textAlign: TextAlign.center,
          ),
          const SizedBox(height: 12),
          ElevatedButton.icon(
            onPressed: onRetry,
            icon: const Icon(Icons.refresh_rounded),
            label: const Text('Reintentar'),
          ),
        ],
      ),
    );
  }
}
