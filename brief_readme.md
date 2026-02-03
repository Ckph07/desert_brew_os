Briefing Doc: Desert Brew OS - Modelo de Negocio y Operación Industrial

Resumen Ejecutivo

Desert Brew OS es un Sistema de Ejecución de Manufactura (MES) y ERP modular de alta eficiencia, diseñado específicamente para la industria de la cerveza artesanal bajo estándares de ingeniería industrial. El sistema se fundamenta en la separación financiera de unidades de negocio (Centros de Beneficio), permitiendo una visibilidad clara sobre la rentabilidad de la producción (fábrica) frente a la comercialización (Taproom).

Los pilares críticos del modelo incluyen:

* Independencia Financiera: Implementación de Transfer Pricing para productos propios y Pass-through para productos de terceros.
* Trazabilidad Total (Farm-to-Glass): Control estricto desde la recepción de materia prima vía FIFO hasta el consumo final.
* Gestión de Activos Críticos: Los barriles son tratados como activos serializados mediante una Máquina de Estados Finitos (FSM).
* Seguridad Industrial y Offline: Protocolos de Prueba de Entrega (PoD) con criptografía asimétrica para operaciones en zonas sin conectividad.
* Eficiencia en Manufactura: Integración de mantenimiento industrial (CMMS) y tratamiento de aguas como una sub-fábrica para un cálculo preciso del costo por litro.


--------------------------------------------------------------------------------


1. Arquitectura de Centros de Beneficio (Profit Centers)

El modelo de negocio impone una "pared" financiera entre la Planta (producción) y el Taproom (hospitalidad) para identificar dónde se genera realmente la ganancia.

Reglas de Precios de Transferencia

Para que las finanzas sean independientes, se definen dos mecanismos de transacción interna:

Tipo de Producto	Mecanismo	Lógica Financiera	Impacto en Margen
House Beer (Casa)	Transfer Pricing	Costo de Producción + Margen de Fábrica.	La fábrica genera utilidad por producir eficientemente.
Guest/Commercial	Pass-through	Costo exacto de adquisición (0% margen fábrica).	La fábrica actúa solo como operador logístico (3PL).

Estructura de Reportes (P&L)

* Estado de Resultados - Planta: Sus ingresos provienen de ventas a distribuidores y ventas internas al Taproom. Sus KPI son el Cost per Liter y el Factory Yield.
* Estado de Resultados - Taproom: Sus ingresos son las ventas directas al público. El costo de venta (COGS) para la cerveza de casa se basa en el precio de transferencia. Sus KPI incluyen el Gross Margin per Chair y el RevPASH.


--------------------------------------------------------------------------------


2. Gestión de Operaciones e Inventarios

El sistema abandona las hojas de cálculo para implementar una lógica transaccional robusta y "thread-safe".

Lógica de Consumo FIFO

El motor de inventarios utiliza un algoritmo de rotación basado en fecha de llegada:

* Bloqueo de Seguridad: Emplea select_for_update en la base de datos para evitar "inventarios negativos fantasmas" o condiciones de carrera durante pedidos simultáneos.
* Asignación Multi-lote: Si un pedido requiere más stock del disponible en un solo lote, el sistema consume automáticamente de múltiples capas FIFO, calculando el costo ponderado real.

Ciclo de Vida de Barriles (Asset Management)

Los barriles no son simples consumibles, sino activos serializados con ID único (QR/RFID). Se gestionan mediante una FSM de 10 estados para garantizar la calidad y evitar pérdidas de capital (CAPEX):

* Estados Críticos: DIRTY → CLEAN → SANITIZED → FILLING → FULL.
* Regla de Calidad: El software prohíbe el llenado de un barril que no haya pasado por el estado CLEAN.
* Rastreo: Permite identificar qué clientes tienen barriles específicos y detectar activos en riesgo de pérdida (>N días fuera).


--------------------------------------------------------------------------------


3. Modelo de Ventas y Distribución

El sistema diferencia drásticamente la venta minorista (B2C) de la distribución mayorista (B2B).

Venta B2B y Distribución Inteligente

* Comisiones por Volumen (CPV): Las comisiones de los vendedores se calculan sobre litros entregados, no sobre valor monetario, y se disparan solo tras una Prueba de Entrega (PoD) válida.
* Control de Crédito de Doble Compuerta: Antes de autorizar un pedido, el sistema valida atómicamente la deuda financiera y el saldo de barriles en posesión del cliente.
* Prueba de Entrega (PoD) "Iron-Clad": Para entregas sin internet, se utiliza criptografía Ed25519. El dispositivo del repartidor firma el payload de entrega, asegurando el "no repudio" y la integridad de los datos una vez recuperada la conexión.

Taproom POS

Plataforma completa de gestión de restaurante que incluye:

* Gestión de Barriles "Pinchados": Consumo por mililitros en tiempo real.
* Nómina y Propinas: Sistema de pooling configurable e integración con el salario diario.
* Catálogo Multi-Tier: Precios dinámicos basados en el volumen de compra y fidelidad del cliente (estilo plataformas BEES/HeiShop).


--------------------------------------------------------------------------------


4. Manufactura y Excelencia Operativa

Producción como MES (Sistema de Ejecución de Manufactura)

La producción no es un recetario estático, sino un flujo de parámetros de control:

* Costo Real del Litro: Se calcula post-producción distribuyendo los costos de insumos, mano de obra y energía sobre el volumen envasado real (considerando mermas).
* Integración BeerSmith: Importación de recetas vía XML para estandarizar procesos de maceración y perfiles de fermentación.

CMMS y Tratamiento de Aguas

* Mantenimiento Industrial: Seguimiento de "Vida Útil" de equipos (caldera, chiller, ósmosis). Los mantenimientos se disparan por tiempo, uso (horas) o condición (IoT).
* Sub-fábrica de Agua: El tratamiento de agua de ósmosis se costea como un producto intermedio. El sistema calcula el costo del litro de agua procesada integrando el costo del agua cruda, energía de bombas, químicos y desgaste de membranas.


--------------------------------------------------------------------------------


5. Contexto Tecnológico y Resiliencia

Ingeniería para la Realidad de Coahuila

Desert Brew OS está diseñado para soportar las condiciones industriales de Saltillo ("El Detroit de México"):

* Resiliencia: Capacidad de operar offline en el Taproom y rutas de entrega.
* Industria 5.0: Colaboración humano-máquina mediante un "Digital Twin" de la planta y analítica predictiva para fermentaciones.
* Compliance Fiscal: Cálculo automático de IEPS/IVA según la legislación mexicana para bebidas alcohólicas y tasa 0% para agua.

Estado Actual del Proyecto (v0.4.0)

A la fecha del informe (03-02-2026), el sistema presenta los siguientes avances:

* Inventory Service: 🟢 Production Ready (FIFO, Proveedores, Gases, Keg FSM).
* Métricas: 39 endpoints operacionales, >85% de cobertura de tests.
* Próximos Milestones: Implementación del motor de comisiones y el puente financiero de precios de transferencia.

"El sistema está diseñado para escalar de 2,000 a 50,000 hectolitros anuales bajo un régimen de eficiencia operativa estricta." (Fuente: Contexto Operativo)
