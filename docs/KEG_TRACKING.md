# Keg Tracking - RFID vs QR Code

## Resumen de Opciones

### ✅ QR Code (RECOMENDADO para empezar)

**Ventajas:**
- ✅ **No necesitas hardware especial** - cualquier celular con cámara
- ✅ **Auto-generado por el sistema** (formato: `KEG-SERIAL-UUID`)
- ✅ **Gratis** - solo imprimir stickers resistentes al agua
- ✅ **Fácil de implementar** - app móvil Flutter con cámara
- ✅ **Backup visual** - puedes leer el código a simple vista

**Desventajas:**
- ❌ Requiere línea de vista (escanear uno por uno)
- ❌ Más lento para bulk scanning (10 kegs = 10 escaneos)

**Implementación:**
```python
# Al crear keg, sistema auto-genera QR
qr_code = f"KEG-{serial_number}-{uuid[:8]}"
# Ejemplo: KEG-2026-050-A3B4C5D6

# Desde app móvil
POST /api/v1/inventory/kegs/bulk-scan
{
  "qr_codes": ["KEG-2026-050-A3B4C5D6"],
  "new_state": "EMPTY",
  "user_id": 5
}
```

---

### 🔧 RFID (Opcional - para futuro)

**Ventajas:**
- ✅ **Bulk scanning** - 10+ kegs simultáneamente
- ✅ **No requiere línea de vista** - dentro de radio (~1-3 metros)
- ✅ **Más rápido** - escanear camión completo en segundos

**Desventajas:**
- ❌ **Necesitas RFID Writer** ($100-300 USD) para programar tags
- ❌ **Necesitas RFID Scanner** ($50-500 USD)
  - Handheld: $50-150 USD
  - Fixed reader: $200-500 USD
- ❌ **Tags RFID** ($1-5 USD cada uno)
- ❌ La mayoría de celulares **NO pueden escribir RFID**
  - Algunos Android con NFC pueden **leer** RFID pasivos
  - **No puedes programar tags desde celular**

**Hardware recomendado (si decides implementar):**
- **Tags:** UHF RFID tags (ISO 18000-6C/EPC Gen2)
- **Writer:** Handheld UHF RFID reader/writer
- **Rango:** 1-3 metros típico

---

## Implementación Actual

El sistema **soporta AMBOS**:

### Modelo KegAsset
```python
class KegAsset:
    serial_number: str    # Físico en el barril
    rfid_tag: str | None  # Opcional (para futuro)
    qr_code: str          # Auto-generado
```

### Bulk Scanning
```python
# Opción 1: Mobile QR scanning
POST /kegs/bulk-scan
{
  "qr_codes": ["KEG-001-A1B2", "KEG-002-C3D4"],
  "new_state": "EMPTY"
}

# Opción 2: RFID scanner (futuro)
POST /kegs/bulk-scan
{
  "rfid_tags": ["RFID123", "RFID456"],
 "new_state": "EMPTY"
}
```

---

## Flujo Recomendado - QR Code

### 1. Registrar Keg Nuevo
```http
POST /api/v1/inventory/kegs
{
  "serial_number": "KEG-2026-050",
  "size_liters": 30
}

Response:
{
  "id": "uuid-here",
  "serial_number": "KEG-2026-050",
  "qr_code": "KEG-2026-050-A3B4C5D6",  # AUTO-GENERADO
  "current_state": "EMPTY"
}
```

### 2. Imprimir Etiqueta QR
- Sistema genera QR code automáticamente
- Puedes usar biblioteca like `qrcode` en backend
- O generar desde app móvil
- Imprimir en sticker resistente al agua
- Pegar en el barril

### 3. Escanear con App Móvil
```dart
// Flutter app
import 'package:qr_code_scanner/qr_code_scanner.dart';

void onQRScanned(String qrCode) {
  // qrCode = "KEG-2026-050-A3B4C5D6"
  scannedKegs.add(qrCode);
}

// Al terminar escaneo
POST /api/v1/inventory/kegs/bulk-scan
{
  "qr_codes": scannedKegs,
  "new_state": "EMPTY",
  "location": "Dock A",
  "user_id": currentUser.id
}
```

---

## Generación de QR Stickers

### Backend (Python)
```python
import qrcode
from PIL import Image

def generate_keg_qr(serial_number: str, qr_code: str):
    """Generate QR code image for keg."""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )
    qr.add_data(qr_code)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Add text below QR
    # ... add serial number text ...
    
    return img
```

### Endpoint para Generar QR
```python
@router.get("/kegs/{id}/qr-image")
def get_keg_qr_image(keg_id: str, db: Session = Depends(get_db)):
    """Get QR code image for printing."""
    keg = db.query(KegAsset).filter(KegAsset.id == keg_id).first()
    
    img = generate_keg_qr(keg.serial_number, keg.qr_code)
    
    # Return as PNG
    return StreamingResponse(img_bytes, media_type="image/png")
```

---

## Stickers Recomendados

**Materiales:**
- Vinilo resistente al agua
- Laminado UV para protección
- Adhesivo industrial

**Tamaño:**
- QR Code: 2x2 inches (5x5 cm)
- Con texto: 3x2 inches (7.5x5 cm)

**Proveedores (México):**
- Vistaprint
- Stickermule
- PrintPlace

**Diseño sugerido:**
```
┌─────────────────┐
│  ▓▓▓▓▓▓▓▓▓▓▓▓  │
│  ▓▓        ▓▓  │  ← QR Code
│  ▓▓  ▓▓▓▓  ▓▓  │
│  ▓▓▓▓▓▓▓▓▓▓▓▓  │
│                 │
│ KEG-2026-050    │  ← Serial legible
│ Desert Brew Co. │
└─────────────────┘
```

---

## Roadmap de Tracking

### Fase 1: QR Code (NOW) ✅
- [x] QR auto-generation
- [x] Mobile scanning support
- [ ] Flutter app con cámara QR
- [ ] Endpoint para generar imágenes QR

### Fase 2: RFID (Futuro - Cuando tengas $$)
- [ ] Comprar tags RFID
- [ ] Comprar reader/writer
- [ ] Programar tags
- [ ] Integrar scanner

### Fase 3: Hybrid (Ideal)
- [ ] Operar con ambos simultáneamente
- [ ] QR como backup de RFID
- [ ] Quick scan con RFID, fallback a QR

---

**Recomendación Final:**
Empieza con **QR codes** (100% funcional con celulares). Cuando escales y tengas presupuesto, agrega RFID para bulk operations en muelle/almacén.
