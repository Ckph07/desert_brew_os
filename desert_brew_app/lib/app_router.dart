import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import 'features/dashboard/presentation/pages/home_dashboard_page.dart';
import 'features/inventory/presentation/pages/stock_dashboard_page.dart';
import 'features/inventory/presentation/pages/keg_management_page.dart';
import 'features/inventory/presentation/pages/finished_products_page.dart';
import 'features/inventory/presentation/pages/receive_stock_page.dart';
import 'features/inventory/presentation/pages/supplier_list_page.dart';
import 'features/inventory/presentation/pages/ingredient_catalog_page.dart';
import 'features/sales/presentation/pages/client_list_page.dart';
import 'features/sales/presentation/pages/product_catalog_page.dart';
import 'features/sales/presentation/pages/sales_notes_page.dart';
import 'features/sales/presentation/pages/create_sales_note_page.dart';
import 'features/sales/presentation/pages/sales_note_detail_page.dart';
import 'features/sales/presentation/pages/liters_by_style_page.dart';
import 'features/production/presentation/pages/recipe_list_page.dart';
import 'features/production/presentation/pages/recipe_detail_page.dart';
import 'features/production/presentation/pages/batch_list_page.dart';
import 'features/production/presentation/pages/batch_detail_page.dart';
import 'features/production/presentation/pages/cost_management_page.dart';
import 'features/production/domain/entities/recipe.dart';
import 'features/finance/presentation/pages/finance_dashboard_page.dart';
import 'features/finance/presentation/pages/income_list_page.dart';
import 'features/finance/presentation/pages/expense_list_page.dart';
import 'features/finance/presentation/pages/balance_cashflow_page.dart';
import 'features/finance/presentation/pages/transfer_pricing_rules_page.dart';
import 'features/finance/presentation/pages/internal_transfers_page.dart';
import 'features/finance/presentation/pages/profit_center_summary_page.dart';
import 'features/payroll/presentation/pages/employee_list_page.dart';
import 'features/payroll/presentation/pages/tip_pool_page.dart';
import 'features/security/presentation/pages/device_list_page.dart';
import 'app_shell.dart';

/// GoRouter configuration for Desert Brew OS.
///
/// Uses [ShellRoute] for persistent bottom navigation.
class AppRouter {
  AppRouter._();

  static final _rootNavigatorKey = GlobalKey<NavigatorState>();
  static final _shellNavigatorKey = GlobalKey<NavigatorState>();

  static final router = GoRouter(
    navigatorKey: _rootNavigatorKey,
    initialLocation: '/',
    routes: [
      ShellRoute(
        navigatorKey: _shellNavigatorKey,
        builder: (context, state, child) => AppShell(child: child),
        routes: [
          // ── Dashboard ──
          GoRoute(
            path: '/',
            name: 'dashboard',
            builder: (context, state) => const HomeDashboardPage(),
          ),

          // ── Inventory ──
          GoRoute(
            path: '/inventory',
            name: 'inventory',
            builder: (context, state) => const StockDashboardPage(),
            routes: [
              GoRoute(
                path: 'kegs',
                name: 'kegs',
                builder: (context, state) => const KegManagementPage(),
              ),
              GoRoute(
                path: 'finished',
                name: 'finished-products',
                builder: (context, state) => const FinishedProductsPage(),
              ),
              GoRoute(
                path: 'receive',
                name: 'receive-stock',
                builder: (context, state) => const ReceiveStockPage(),
              ),
              GoRoute(
                path: 'suppliers',
                name: 'suppliers',
                builder: (context, state) => const SupplierListPage(),
              ),
              GoRoute(
                path: 'ingredients',
                name: 'ingredients',
                builder: (context, state) => const IngredientCatalogPage(),
              ),
            ],
          ),

          // ── Sales ──
          GoRoute(
            path: '/sales',
            name: 'sales',
            builder: (context, state) => const SalesNotesPage(),
            routes: [
              GoRoute(
                path: 'clients',
                name: 'clients',
                builder: (context, state) => const ClientListPage(),
              ),
              GoRoute(
                path: 'clients/:id',
                name: 'client-detail',
                builder:
                    (context, state) =>
                    // Placeholder until ClientDetailPage is built in F3b
                    Scaffold(
                      appBar: AppBar(
                        title: Text('Cliente ${state.pathParameters['id']}'),
                      ),
                      body: const Center(
                        child: Text('Detalle del cliente — próximamente'),
                      ),
                    ),
              ),
              GoRoute(
                path: 'products',
                name: 'products',
                builder: (context, state) => const ProductCatalogPage(),
              ),
              GoRoute(
                path: 'notes',
                name: 'sales-notes',
                builder: (context, state) => const SalesNotesPage(),
                routes: [
                  GoRoute(
                    path: 'create',
                    name: 'create-sales-note',
                    builder: (context, state) => const CreateSalesNotePage(),
                  ),
                  GoRoute(
                    path: ':id',
                    name: 'sales-note-detail',
                    builder:
                        (context, state) => SalesNoteDetailPage(
                          noteId: int.parse(state.pathParameters['id'] ?? '0'),
                        ),
                  ),
                ],
              ),
              GoRoute(
                path: 'analytics',
                name: 'sales-analytics',
                builder: (context, state) => const LitersByStylePage(),
              ),
            ],
          ),

          // ── Production ──
          // ── Production ──
          GoRoute(
            path: '/production',
            name: 'production',
            builder: (context, state) => const RecipeListPage(),
            routes: [
              GoRoute(
                path: 'recipes/:id',
                name: 'recipe-detail',
                builder:
                    (context, state) => RecipeDetailPage(
                      recipeId: int.parse(state.pathParameters['id'] ?? '0'),
                      initialRecipe:
                          state.extra is Recipe ? state.extra as Recipe : null,
                    ),
              ),
              GoRoute(
                path: 'batches',
                name: 'batches',
                builder: (context, state) => const BatchListPage(),
                routes: [
                  GoRoute(
                    path: ':id',
                    name: 'batch-detail',
                    builder:
                        (context, state) => BatchDetailPage(
                          batchId: int.parse(state.pathParameters['id'] ?? '0'),
                        ),
                  ),
                ],
              ),
              GoRoute(
                path: 'costs',
                name: 'costs',
                builder: (context, state) => const CostManagementPage(),
              ),
            ],
          ),

          // ── Finance (Sprint 3.5 + 3.5b: 19 endpoints) ──
          GoRoute(
            path: '/finance',
            name: 'finance',
            builder: (context, state) => const FinanceDashboardPage(),
            routes: [
              GoRoute(
                path: 'income',
                name: 'income',
                builder: (context, state) => const IncomeListPage(),
              ),
              GoRoute(
                path: 'expenses',
                name: 'expenses',
                builder: (context, state) => const ExpenseListPage(),
              ),
              GoRoute(
                path: 'balance',
                name: 'balance',
                builder: (context, state) => const BalanceCashflowPage(),
              ),
              GoRoute(
                path: 'pricing-rules',
                name: 'pricing-rules',
                builder: (context, state) => const TransferPricingRulesPage(),
              ),
              GoRoute(
                path: 'internal-transfers',
                name: 'internal-transfers',
                builder: (context, state) => const InternalTransfersPage(),
              ),
              GoRoute(
                path: 'profit-center-summary',
                name: 'profit-center-summary',
                builder: (context, state) => const ProfitCenterSummaryPage(),
              ),
            ],
          ),

          // ── Payroll ──
          GoRoute(
            path: '/payroll',
            name: 'payroll',
            builder: (context, state) => const EmployeeListPage(),
            routes: [
              GoRoute(
                path: 'tip-pool',
                name: 'tip-pool',
                builder: (context, state) => const TipPoolPage(),
              ),
              GoRoute(path: 'tips', redirect: (_, __) => '/payroll/tip-pool'),
            ],
          ),

          // ── Security ──
          GoRoute(
            path: '/security',
            name: 'security',
            builder: (context, state) => const DeviceListPage(),
          ),
        ],
      ),
    ],
  );
}
