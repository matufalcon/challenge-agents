# Equilab — Challenge

Sistema local de reservas de equipos de laboratorio.

## Descripción y alcance

Aplicación web local para gestionar reservas de cinco equipos de laboratorio fijos. Permite crear, consultar y cancelar reservas con validación de solapamiento y persistencia en SQLite.

**Reglas de negocio**
- Inventario fijo de 5 equipos (sin CRUD de inventario).
- Solicitante obligatorio y no vacío.
- Fecha/hora de inicio anterior a la de fin.
- No hay solapamiento entre reservas activas del mismo equipo.
- Intervalos consecutivos permitidos (fin = inicio).
- Equipos distintos pueden reservarse en el mismo horario.
- Cancelación conserva ID y datos, libera el intervalo, actualiza estado y fecha de cancelación.
- Persistencia en SQLite: los datos sobreviven a reinicios.

**Criterios de aceptación (resumen del challenge)**
- Reservas persisten tras reiniciar la aplicación.
- Reservas canceladas conservan ID y datos, pero liberan el intervalo.
- No hay superposición entre reservas activas de una misma unidad.
- Los límites de intervalos consecutivos se permiten.
- La disponibilidad y la creación de reservas aplican las mismas reglas.

## Stack tecnológico y estructura

| Componente | Versión / Detalle |
|------------|-------------------|
| Python     | 3.10+ (probado en 3.10.7) |
| Flask      | 3.0 |
| SQLite     | stdlib (`sqlite3`) |
| Pruebas    | `pytest` |
| Frontend   | HTML + CSS (sin frameworks) |

```
challenge-reservas/
├── app/
│   ├── __init__.py          # Factory Flask, init_db, teardown
│   ├── config.py            # Config centralizada (DB_PATH, TIMEZONE)
│   ├── models.py            # Acceso a datos (sqlite3 + FK)
│   ├── services/
│   │   ├── __init__.py
│   │   └── reservations.py  # Validación y lógica de negocio
│   ├── utils/
│   │   ├── __init__.py
│   │   └── dates.py         # Conversión UTC ↔ ART, parsing ISO 8601
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── api.py           # Endpoints REST /api/*
│   │   └── web.py           # GET /, GET /health
│   ├── templates/
│   │   ├── base.html
│   │   └── index.html
│   └── static/
│       ├── css/
│       │   ├── variables.css
│       │   └── base.css
│       └── js/
│           └── app.js
├── scripts/
│   ├── schema.sql           # DDL v1 (units, reservations)
│   └── seed.py              # Seed idempotente (5 equipos)
├── data/
│   └── reservations.db      # BD SQLite (gitignore)
├── tests/
│   ├── __init__.py
│   ├── conftest.py          # Fixtures pytest (BD temporal)
│   ├── test_health.py
│   ├── test_db.py
│   ├── test_reservations.py
│   └── test_api.py
├── docs/
│   ├── decisions.md         # ADRs (decisiones técnicas)
│   └── delegations.md       # Registro de delegaciones
├── run.py                   # Entry point
├── requirements.txt
├── pytest.ini
├── .gitignore
├── README.md
└── PROGRESS.md
```

## Instalación, configuración y ejecución (Windows PowerShell)

> Ejecutar desde la raíz del proyecto (`challenge-reservas/`).

```powershell
# 1. Crear entorno virtual (una sola vez)
python -m venv .venv

# 2. Activar entorno virtual
.venv\Scripts\Activate.ps1

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Inicializar base de datos e inventario (idempotente)
.venv\Scripts\python.exe scripts/seed.py

# 5. Ejecutar pruebas automatizadas
.venv\Scripts\python.exe -m pytest -v

# 6. Levantar servidor de desarrollo
.venv\Scripts\python.exe run.py
```

> Si PowerShell bloquea la activación del script:
> `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`
> y repetir el paso 2.

Servidor en **http://localhost:5000**

**Endpoints implementados**
- `GET /` — Página inicial
- `GET /health` — Health check JSON `{"status":"ok","tz":"America/Argentina/Buenos_Aires"}`
- `GET /api/units` — Lista el inventario fijo de 5 equipos
- `GET /api/reservations/<id>` — Consulta una reserva por ID
- `POST /api/reservations` — Crea una reserva con validación completa
- `PATCH /api/reservations/<id>/cancel` — Cancela una reserva (sin body)
- `GET /api/availability` — Consulta disponibilidad de un equipo en un intervalo

## Inicialización de la base de datos e inventario

### Esquema (`scripts/schema.sql`)
- **units**: `id`, `code` (UNIQUE), `name`, `type`, `created_at`
- **reservations**: `id`, `unit_id` (FK→units), `user`, `start_utc`, `end_utc`, `notes`, `status` (`activa`/`cancelada`), `created_at`, `cancelled_at`
- Índices: `idx_reservations_unit_time` (`unit_id, start_utc, end_utc`), `idx_reservations_status`
- FK habilitadas por conexión (`PRAGMA foreign_keys = ON`)

### Inventario fijo (5 equipos del challenge)
| code | name | type |
|------|------|------|
| MIC-01 | Microscopio digital | Microscopía |
| MIC-02 | Microscopio digital | Microscopía |
| OSC-01 | Osciloscopio | Medición |
| MUL-01 | Multímetro | Medición |
| FUE-01 | Fuente de alimentación | Potencia |

> `type` es una decisión técnica documentada (el enunciado no especifica categorías).

### Seed idempotente
```powershell
.venv\Scripts\python.exe scripts/seed.py
```
Ejecutable múltiples veces sin duplicar equipos (usa `UNIQUE(code)`).

## Ejecución de pruebas

```powershell
# Suite completa
.venv\Scripts\python.exe -m pytest -v

# Solo tests de base de datos
.venv\Scripts\python.exe -m pytest tests/test_db.py -v

# Solo tests de salud
.venv\Scripts\python.exe -m pytest tests/test_health.py -v

# Solo tests de reservas (validación, persistencia, solapamiento)
.venv\Scripts\python.exe -m pytest tests/test_reservations.py -v

# Solo tests de API
.venv\Scripts\python.exe -m pytest tests/test_api.py -v
```

**Estado actual**: 107 tests aprobados (última ejecución verificada).

## Persistencia, fechas y zona horaria

- **Zona horaria**: `America/Argentina/Buenos_Aires` (ART, UTC-3, sin DST desde 2009).
- **Almacenamiento en BD**: UTC como `TEXT` formato `YYYY-MM-DD HH:MM:SS` (compatible con `datetime('now')` de SQLite).
- **API entrada**: ISO 8601 con zona horaria explícita (ej. `2025-01-15T10:00:00-03:00` o `Z`).
- **API salida**: ISO 8601 con offset ART (`-03:00`).
- **UI**: `datetime-local` naive (se asume ART), conversión en boundaries.
- **Política**: Nunca guardar `datetime` naive; convertir en boundaries (entrada/salida).

## Preparación y uso del agente de programación

Este proyecto incluye `AGENTS.md` con instrucciones para el agente:
- Trabajar en tareas pequeñas y verificables.
- Explicar plan y archivos antes de implementar.
- No agregar funcionalidades fuera de alcance sin consultar.
- No instalar dependencias ni ejecutar acciones destructivas sin informar.
- No modificar archivos ajenos al proyecto.
- No inventar resultados de pruebas ni decisiones humanas.
- No hacer commits automáticos.
- Mantener `README.md` y `PROGRESS.md` alineados con el comportamiento real.
- Registrar decisiones técnicas y delegaciones reales con evidencia verificable.

## Decisiones técnicas y registro de delegaciones

- **Decisiones técnicas (ADR)**: `docs/decisions.md`
  - ADR-001: `sqlite3` directo sin ORM + FK por conexión
  - ADR-002: Esquema v1 con `code` único, `name` no único, tipos inferidos
  - ADR-003: Seed idempotente con `INSERT` + captura `IntegrityError`
  - ADR-004: UTC en BD, ART en UI
  - ADR-005: Tests con BD temporal aislada
  - ADR-006: Validación de solapamiento con intervalos semiabiertos `[start, end)`

- **Delegaciones reales**: `docs/delegations.md` (tres delegaciones requeridas por el challenge, pendientes de completarse con evidencia verificable).

## Limitaciones y funcionalidades pendientes

- [ ] Interfaz web: calendario semanal, formulario de reserva, listado de reservas.
- [ ] Horarios de laboratorio (apertura/cierre, días hábiles).
- [ ] Tests de persistencia real (reinicio de proceso).
- [ ] Completar `docs/delegations.md` con tres delegaciones reales y evidencia verificable.

## Licencia

Challenge interno — uso educativo.