# Registro de Decisiones Técnicas (ADR ligeros)

Formato: título, fecha, estado, contexto, decisión, consecuencias.

---

## ADR-001: Uso de sqlite3 directo sin ORM + Foreign Keys por conexión

**Fecha:** 2025-01-21  
**Estado:** Aceptada

### Contexto
Necesidad de persistencia local simple, cero dependencias externas, control total sobre SQL y esquema. El challenge exige que las reservas persistan al reiniciar la aplicación.

### Decisión
Usar `sqlite3` del estándar library de Python (stdlib). No usar SQLAlchemy, Django ORM, Peewee u otros.

Las claves foráneas en SQLite **no se enforcean por defecto**; deben habilitarse en **cada conexión** con:
```python
conn.execute("PRAGMA foreign_keys = ON")
```
Esto se hace en `app/models.py:get_db()` y `get_db_connection()`.

### Consecuencias
- ✅ Cero dependencias extra
- ✅ Control total sobre migraciones (manuales vía `scripts/schema.sql`)
- ✅ Esquema simple y auditable
- ⚠️ Más código boilerplate (conexiones, cursores, mapeo Row→dict)
- ⚠️ Migraciones manuales (aceptable para alcance del challenge)
- ⚠️ Recordar `PRAGMA foreign_keys = ON` en **cada** conexión nueva

---

## ADR-002: Esquema v1 — `code` único, `name` no único, tipos inferidos

**Fecha:** 2025-01-21  
**Estado:** Aceptada

### Contexto
El challenge define 5 equipos con códigos únicos (MIC-01, MIC-02, OSC-01, MUL-01, FUE-01). Dos equipos (MIC-01, MIC-02) comparten el mismo nombre "Microscopio digital". El enunciado **no especifica** una taxonomía de tipos/categorías.

### Decisión
Tabla `units` con:
- `code TEXT NOT NULL UNIQUE` — clave de negocio, identificador único por equipo
- `name TEXT NOT NULL` — **sin UNIQUE**, permite nombres repetidos
- `type TEXT NOT NULL` — categoría inferida como decisión técnica:
  - "Microscopía" para microscopios
  - "Medición" para osciloscopio y multímetro
  - "Potencia" para fuente de alimentación
- Sin campo `location` (no está en el enunciado)

Tabla `reservations` preparada para Sprint 2+ con FK a `units(id)`.

### Consecuencias
- ✅ Respeta requisito: códigos únicos, nombres repetidos permitidos
- ✅ Esquema normalizado, listo para reservas
- ⚠️ `type` es decisión técnica documentada; si el stakeholder define taxonomía distinta, requerirá migración
- ⚠️ Sin `location` — si se necesita después, migración `ALTER TABLE`

---

## ADR-003: Seed idempotente con `INSERT OR IGNORE` (implícito por UNIQUE)

**Fecha:** 2025-01-21  
**Estado:** Aceptada

### Contexto
La inicialización del inventario debe ser reproducible: ejecutar `seed.py` múltiples veces no debe duplicar equipos ni borrar datos existentes.

### Decisión
`scripts/seed.py` usa `INSERT INTO ...` capturando `sqlite3.IntegrityError` por violación de `UNIQUE(code)`. Alternativa `INSERT OR IGNORE` también válida; se eligió try/except para claridad y logging de inserciones reales.

```python
try:
    cursor.execute("INSERT INTO units (code, name, type) VALUES (?, ?, ?)", ...)
    inserted += 1
except sqlite3.IntegrityError:
    pass  # code ya existe → idempotente
```

### Consecuencias
- ✅ Re-ejecutable sin efectos secundarios
- ✅ Seguro para CI/CD y setup local
- ✅ No borra datos existentes (solo inserta si falta)
- ⚠️ No actualiza `name`/`type` si cambian en el seed (comportamiento intencional: seed solo inicializa)

---

## ADR-004: Zona horaria UTC en BD, ART en UI

**Fecha:** 2025-01-21 (heredada de Sprint 0)  
**Estado:** Aceptada

### Contexto
El laboratorio opera en Argentina (ART, UTC-3, sin DST desde 2009). La BD debe ser portable y consistente.

### Decisión
- **Almacenamiento**: UTC ISO 8601 (`YYYY-MM-DD HH:MM:SS`) en columnas `start_utc`, `end_utc`, `created_at`, `cancelled_at`
- **Entrada/Salida UI**: Hora local Argentina via `datetime-local` nativo
- **Conversión**: En boundaries (entrada: parse local → UTC; salida: UTC → local para display)
- **Implementación**: `app/utils/dates.py` (Sprint 0) con `ZoneInfo("America/Argentina/Buenos_Aires")`

### Consecuencias
- ✅ Sin ambigüedad de zona horaria en BD
- ✅ Compatible con futuras multi-zona
- ⚠️ Requiere disciplina: nunca guardar `naive` datetime

---

## ADR-005: Tests con BD temporal aislada por test

**Fecha:** 2025-01-21  
**Estado:** Aceptada

### Contexto
Los tests no deben tocar la base de datos real del proyecto (`data/reservations.db`). Cada test debe tener su BD limpia.

### Decisión
Fixture `app` en `tests/conftest.py` crea BD temporal con `tempfile.mkstemp()`, pasa su ruta via `app.config["DB_PATH"]`, y llama `init_db()` en contexto. Cleanup automático al final del test.

### Consecuencias
- ✅ Tests aislados, repetibles, paralelos
- ✅ No contaminan BD de desarrollo
- ✅ Rápidos (archivo temporal en disco, no en memoria para permitir conexiones múltiples)

---