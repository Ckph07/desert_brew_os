# Desert Brew OS - Catálogo de SKUs e Inventario

> **Catálogo completo de insumos, proveedores y estructura de precios**

---

## 📦 Categorías de Inventario

### 1. Materia Prima - Granos

| SKU | Nombre | Proveedor Principal | Unidad | Vida Útil | Ubicación |
|-----|--------|-------------------|--------|-----------|-----------|
| `MALT-PALE-2ROW` | Malta Pale Ale 2 Hileras | Malterías Tepeyac | KG | 12 meses | Silo A |
| `MALT-MUNICH` | Malta Munich | Malterías Tepeyac | KG | 12 meses | Silo A |
| `MALT-CARAMEL-60L` | Malta Caramelo 60L | Briess | KG | 12 meses | Silo B |
| `MALT-CHOCOLATE` | Malta Chocolate | Weyermann | KG | 12 meses | Silo B |
| `MALT-BLACK-PATENT` | Malta Black Patent | Crisp Malting | KG | 12 meses | Silo B |

### 2. Materia Prima - Lúpulo

| SKU | Variedad | Proveedor | % AA Típico | Unidad | Almacenamiento |
|-----|----------|-----------|-------------|--------|----------------|
| `HOPS-CASCADE` | Cascade | Yakima Chief | 5.5-7.0 | G | Congelador A (-18°C) |
| `HOPS-CENTENNIAL` | Centennial | Yakima Chief | 9.5-11.5 | G | Congelador A |
| `HOPS-SIMCOE` | Simcoe | Yakima Chief | 12.0-14.0 | G | Congelador A |
| `HOPS-MOSAIC` | Mosaic | Yakima Chief | 11.5-13.5 | G | Congelador A |
| `HOPS-CITRA` | Citra | Yakima Chief | 11.0-13.0 | G | Congelador A |
| `HOPS-SAAZ` | Saaz (Noble) | Barth-Haas | 3.0-4.5 | G | Congelador B |

### 3. Materia Prima - Levadura

| SKU | Cepa | Laboratorio | Formato | Temperatura | Viabilidad |
|-----|------|-------------|---------|-------------|------------|
| `YEAST-US05` | US-05 (Ale Americana) | Fermentis | Sobre 11.5g | 2-8°C | 24 meses |
| `YEAST-S04` | S-04 (Ale Inglesa) | Fermentis | Sobre 11.5g | 2-8°C | 24 meses |
| `YEAST-W34/70` | W-34/70 (Lager) | Fermentis | Sobre 11.5g | 2-8°C | 24 meses |
| `YEAST-BE134` | BE-134 (Saison) | Fermentis | Sobre 11.5g | 2-8°C | 24 meses |
| `YEAST-WLP001` | California Ale | White Labs | Vial líquido | 2-8°C | 4 meses |

**Nota:** Se maneja propagación interna (generaciones G2-G8) para reducir costos.

### 4. Empaque - Botellas

| SKU | Tipo | Capacidad | Color | Proveedor | Unidad |
|-----|------|-----------|-------|-----------|--------|
| `BOTTLE-355-AMBER` | Botella Long Neck | 355 ml | Ámbar | Vitro | UNIDAD |
| `BOTTLE-473-AMBER` | Botella Alta | 473 ml | Ámbar | Vitro | UNIDAD |
| `BOTTLE-940-AMBER` | Caguama | 940 ml | Ámbar | Vitro | UNIDAD |

### 5. Empaque - Corcholatas

| SKU | Tipo | Diseño | Proveedor | Unidad |
|-----|------|--------|-----------|--------|
| `CAP-STANDARD-GOLD` | Corcholata Estándar | Logo dorado | Crown Holdings | UNIDAD |
| `CAP-TWIST-OFF` | Tapa Rosca | Logo plateado | Silgan | UNIDAD |

### 6. Químicos de Limpieza (CIP/COP)

| SKU | Producto | Tipo | Uso | Dilución | Proveedor |
|-----|----------|------|-----|----------|-----------|
| `CHEM-DET-CAUSTIC` | Detergente Cáustico | NaOH al 50% | Limpieza pesada | 2-3% | Diversey |
| `CHEM-DET-ACID` | Detergente Ácido | Ácido nítrico/fosfórico | Descalcificación | 1-2% | Diversey |
| `CHEM-PERACETIC` | Ácido Peracético | Desinfectante | Sanitización | 200-400 ppm | Ecolab |
| `CHEM-IODOPHOR` | Iodóforo | Desinfectante | Sanitización fría | 12.5-25 ppm | Five Star |

**Regla HACCP:** Todo químico requiere MSDS (Hoja de Seguridad) en archivo.

### 7. Etiquetas por Estilo

| SKU | Estilo | Diseño | Cantidad/Rollo | Proveedor |
|-----|--------|--------|----------------|-----------|
| `LABEL-IPA-COAHUILACERATOPS` | Imperial IPA Coahuilaceratops | Dinosaurio verde | 1000 | Impresiones del Norte |
| `LABEL-LAGER-VELAFRONS` | Velafrons Neo Mexican Lager | Dinosaurio azul | 1000 | Impresiones del Norte |
| `LABEL-AMBER-CARNOTAURUS` | Amber Lager Carnotaurus | Dinosaurio naranja | 1000 | Impresiones del Norte |
| `LABEL-STOUT-TREX` | T-Rex American Stout | Dinosaurio negro | 1000 | Impresiones del Norte |

---

## 💰 Estructura de Precios Multi-Canal

### Canales de Venta

```python
class SalesChannel(Enum):
    TAPROOM_DIRECT = "TAPROOM"      # Venta directa en Taproom
    B2B_DISTRIBUTOR = "DISTRIBUTOR"  # Distribuidores (Beer Runners, etc.)
    B2B_ON_PREMISE = "ON_PREMISE"    # Restaurantes, bares
    B2B_OFF_PREMISE = "OFF_PREMISE"  # Tiendas, supermercados
    ECOMMERCE = "ECOMMERCE"          # Venta online
```

### Modelo de Precios

```python
class ChannelPricing(Base):
    id: int
    product_sku: str
    beer_style: str          # "IPA Coahuilaceratops"
    channel: SalesChannel
    base_price: Decimal      # Precio base antes de descuentos
    
    # Descuentos por volumen
    tier_platinum_discount: Decimal   # -18% (> 1000L/mes)
    tier_gold_discount: Decimal       # -12% (500-999L/mes)
    tier_silver_discount: Decimal     # -7% (100-499L/mes)
    
    # Metadata
    margin_percentage: Decimal
    last_updated: datetime
```

### Ejemplo de Precios

| Producto | Taproom | Distribuidor | On-Premise | Off-Premise | E-commerce |
|----------|---------|--------------|------------|-------------|------------|
| **IPA Coahuilaceratops (355ml)** | $65 | $38 | $42 | $45 | $60 |
| **Velafrons Lager (355ml)** | $55 | $32 | $36 | $39 | $50 |
| **Carnotaurus Amber (940ml)** | $140 | $85 | $95 | $105 | $130 |
| **T-Rex Stout (355ml)** | $70 | $42 | $46 | $50 | $65 |

**Precios en MXN, sin IVA/IEPS**

---

## 🏭 Compliance: BPM, ISO 22000, HACCP, Lean Six Sigma

### 1. Buenas Prácticas de Manufactura (BPM)

**Módulos del Sistema que Soportan BPM:**

#### Trazabilidad Completa
```python
# Requerimiento BPM: Rastreo de lote de inicio a fin
GET /api/v1/batches/{batch_id}/traceability

Response:
{
  "batch_id": "IPA-2026-042",
  "raw_materials": [
    {
      "sku": "MALT-PALE-2ROW",
      "provider_batch": "LOT-2025-450",
      "provider": "Malterías Tepeyac",
      "arrival_date": "2025-12-15",
      "lot_certificate": "url_to_pdf"
    }
  ],
  "production_date": "2026-02-01",
  "packaged_units": [
    {"keg_id": "KEG-050", "distribution": "Restaurante X"}
  ]
}
```

#### Control de Limpieza (CIP/COP)
```python
class CleaningLog(Base):
    id: int
    equipment_id: str        # "FV-01", "KETTLE-01"
    cleaning_date: datetime
    chemical_used: str       # "CHEM-DET-CAUSTIC"
    concentration: Decimal   # 2.5%
    temperature: Decimal     # 80°C
    duration_minutes: int    # 30 min
    responsible_operator: str
    approved_by: str         # QA Manager
    next_cleaning_due: datetime
```

### 2. ISO 22000 / HACCP

**Puntos Críticos de Control (CCP) Implementados:**

| CCP | Fase | Peligro | Límite Crítico | Monitoreo | Acción Correctiva |
|-----|------|---------|----------------|-----------|-------------------|
| CCP-1 | Cocción | Biológico (patógenos) | Temp > 100°C por 60 min | Sensor PT100 | Extender tiempo de hervor |
| CCP-2 | Fermentación | Químico (contaminación) | pH 4.0-4.5 | Sensor pH diario | Descarte de lote |
| CCP-3 | Envasado | Físico (vidrio roto) | Inspección visual 100% | Cámara AI | Rechazo de unidad |
| CCP-4 | Sanitización | Biológico (higiene) | PAA 200-400 ppm | Test strips | Re-sanitización |

**Registro Automático en DB:**
```python
class HACCPControlPoint(Base):
    id: int
    ccp_id: str              # "CCP-1"
    batch_id: str
    measurement_time: datetime
    parameter: str           # "temperature"
    value: Decimal
    limit_min: Decimal
    limit_max: Decimal
    status: str              # "IN_SPEC", "OUT_OF_SPEC"
    corrective_action: str | None
```

### 3. Lean Six Sigma

**Métricas DMAIC Integradas:**

#### Define
- **VOC (Voice of Customer):** Encuestas post-venta en POS
- **CTQ (Critical to Quality):** OG/FG, IBU, SRM dentro de spec

#### Measure
```python
# Dashboard de Variabilidad
GET /api/v1/reports/six-sigma/process-capability

{
  "process": "Fermentation OG",
  "target": 1.060,
  "ucl": 1.063,  # Upper Control Limit
  "lcl": 1.057,  # Lower Control Limit
  "cpk": 1.33,   # Process Capability (>1.33 = Six Sigma)
  "defect_rate_ppm": 3.4
}
```

#### Analyze
- **Ishikawa (Fishbone):** Causas de mermas > 15%
- **Pareto:** 80/20 de defectos (automatizado)

#### Improve
- **A/B Testing:** Recetas v3.1 vs v3.2
- **Kaizen Events:** Registro de mejoras continuas

#### Control
- **SPC Charts:** Control estadístico de procesos en tiempo real

### 4. Scrum Integration

**Sprint Planning basado en Roadmap:**
```python
class Sprint(Base):
    id: int
    sprint_number: int
    start_date: datetime
    end_date: datetime
    velocity_points: int
    
    # User Stories del Sprint
    stories: List[UserStory]
    
class UserStory(Base):
    id: str
    title: str
    description: str
    acceptance_criteria: List[str]
    story_points: int
    status: str  # "TODO", "IN_PROGRESS", "DONE"
```

**Daily Standup Dashboard:**
- Bloqueadores en producción
- Lotes en fermentación crítica
- Inventario bajo mínimo

---

## 📊 Reportes de Compliance

### Reporte HACCP Mensual

```python
GET /api/v1/reports/haccp?month=2026-02

{
  "total_ccps_monitored": 1240,
  "out_of_spec_events": 3,
  "corrective_actions_taken": 3,
  "compliance_rate": 99.76,
  "auditor_signature": "digital_signature.png"
}
```

### Certificado de Lote (para auditorías)

```python
GET /api/v1/batches/{batch_id}/certificate

# Genera PDF con:
# - Trazabilidad completa de ingredientes
# - Análisis microbiológico (mock)
# - Cumplimiento de CCPs
# - Firma digital QA Manager
```

---

## 🔐 Gestión de Proveedores

```python
class Supplier(Base):
    id: str
    business_name: str
    rfc: str
    category: str            # "MALT", "HOPS", "PACKAGING"
    
    # Calificación (Lean)
    quality_score: Decimal   # 1-5
    delivery_score: Decimal  # 1-5
    price_competitiveness: Decimal
    
    # Compliance
    has_valid_certificate: bool
    certificate_expiry: datetime
    last_audit_date: datetime
    
    # Contacto
    contact_name: str
    email: str
    phone: str
```

### Evaluación de Proveedores (Supplier Scorecard)

| Proveedor | Categoría | Calidad | Entrega | Precio | Score Total |
|-----------|-----------|---------|---------|--------|-------------|
| Malterías Tepeyac | Malta | 4.8 | 4.5 | 4.2 | **4.5** |
| Yakima Chief | Lúpulo | 5.0 | 4.8 | 3.8 | **4.5** |
| Vitro | Botellas | 4.2 | 4.9 | 4.5 | **4.5** |
| Diversey | Químicos | 4.7 | 5.0 | 3.5 | **4.4** |

---

## ✅ Checklist de Recepción de Insumos

**Al recibir cualquier insumo:**

```
[ ] Verificar orden de compra existe
[ ] Inspección visual (empaque dañado, contaminación)
[ ] Verificar lote del proveedor coincide
[ ] Verificar cantidad vs. factura
[ ] Temperatura correcta (para lúpulo, levadura)
[ ] Registrar en sistema (FIFO automático)
[ ] Etiqueta QR generada y pegada
[ ] Certificado de análisis archivado (si aplica)
[ ] Aprobar o rechazar lote
```

---

**Última Actualización:** 2026-02-02  
**Responsable:** Equipo de Calidad y Operaciones
