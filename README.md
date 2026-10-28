# Equilab — Challenge agents

Sistema local de reservas de equipos de laboratorio con identidad visual propia.

## Stack Tecnológico

- **Python** 3.10+ (probado en 3.10.7)
- **Flask** 3.0 — microframework web
- **SQLite** (stdlib) — persistencia local
- **HTML/CSS** — sin frameworks, tokens CSS personalizados
- **pytest** — pruebas automatizadas

## Identidad Visual: "Laboratorio Editorial"

| Token | Color | Uso |
|-------|-------|-----|
| `--color-petroleum` | `#0D3B3E` | Primario (headers, botones, enlaces) |
| `--color-ivory` | `#FDFBF7` | Fondo principal |
| `--color-sage` | `#7A9E7E` | Secundario (estados libre, acentos) |
| Tipografía | `IBM Plex Serif` + `IBM Plex Mono` | Editorial + instrumental |

## Zona Horaria y Fechas

- **Zona horaria**: `America/Argentina/Buenos_Aires` (ART, UTC-3, sin DST desde 2009)
- **Almacenamiento**: UTC ISO 8601 en BD
- **UI**: Entrada/salida en hora local Argentina (`datetime-local` nativo)
- **Política**: Nunca guardar naive; convertir en boundaries (entrada/salida)

## Estructura del Proyecto (Sprint 1)

```
challenge-reservas/
├── app/
│   ├── __init__.py          # Factory Flask + init_db + teardown
│   ├── config.py            # Config centralizada (DB_PATH, TIMEZONE)
│   ├── models.py            # Acceso a datos (sqlite3 + FK)
│   ├── routes/
│   │   ├── __init__.py
│   │   └── web.py           # GET /, GET /health
│   ├── templates/
│   │   ├── base.html        # Layout base
│   │   └── index.html       # Página inicial
│   └── static/
│       ├── css/
│       │   ├── variables.css # Tokens de color/tipografía
│       │   └── base.css     # Reset, layout, componentes
│       └── js/
│           └── app.js       # Placeholder
├── scripts/
│   ├── schema.sql           # DDL v1 (units, reservations)
│   └── seed.py              # Seed idempotente (5 equipos)
├── data/
│   └── reservations.db      # BD SQLite (gitignore)
├── tests/
│   ├── __init__.py
│   ├── conftest.py          # Fixtures pytest (BD temporal)
│   ├── test_health.py       # Tests /health y GET /
│   └── test_db.py           # Tests esquema, seed, constraints
├── docs/
│   └── decisions.md         # ADRs (decisiones técnicas)
├── run.py                   # Entry point
├── requirements.txt
├── pytest.ini
├── .gitignore
└── README.md
```

## Instalación y Ejecución (Windows PowerShell)

```powershell
# 1. Clonar/ubicarse en el directorio del proyecto
cd C:\Users\Matias\Desktop\challenge-reservas

# 2. Crear entorno virtual (una sola vez)
python -m venv .venv

# 3. Activar entorno virtual
.venv\Scripts\Activate.ps1

# 4. Instalar dependencias
pip install -r requirements.txt

# 5. Inicializar base de datos e inventario (idempotente)
.venv\Scripts\python.exe scripts/seed.py

# 6. Ejecutar pruebas automatizadas
.venv\Scripts\python.exe -m pytest -v

# 7. Levantar servidor de desarrollo
.venv\Scripts\python.exe run.py
```

> **Nota**: Si PowerShell bloquea la activación del script, ejecutar:
> `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`
> y volver a intentar el paso 3.

El servidor estará disponible en: **http://localhost:5000**

Endpoints:
- `GET /` — Página inicial con identidad visual
- `GET /health` — Health check JSON `{"status":"ok","tz":"America/Argentina/Buenos_Aires"}`

## Base de Datos e Inventario (Sprint 1)

### Esquema
- **units**: `id`, `code` (UNIQUE), `name`, `type`, `created_at`
- **reservations**: `id`, `unit_id` (FK→units), `user`, `start_utc`, `end_utc`, `notes`, `status`, `created_at`, `cancelled_at`
- Índices: `idx_reservations_unit_time`, `idx_reservations_status`
- Claves foráneas: habilitadas por conexión (`PRAGMA foreign_keys = ON`)

### Inventario fijo (5 equipos del challenge)
| code | name | type |
|------|------|------|
| MIC-01 | Microscopio digital | Microscopía |
| MIC-02 | Microscopio digital | Microscopía |
| OSC-01 | Osciloscopio | Medición |
| MUL-01 | Multímetro | Medición |
| FUE-01 | Fuente de alimentación | Potencia |

> **Nota**: `type` es una decisión técnica (el enunciado no especifica categorías).

### Seed idempotente
```powershell
# Ejecutable múltiples veces sin duplicar
.venv\Scripts\python.exe scripts/seed.py
```

## Pruebas Automatizadas

```powershell
# Suite completa (14 tests: 3 health + 11 DB)
.venv\Scripts\python.exe -m pytest -v

# Solo tests de base de datos
.venv\Scripts\python.exe -m pytest tests/test_db.py -v

# Solo tests de salud
.venv\Scripts\python.exe -m pytest tests/test_health.py -v
```

**Criterios de aceptación Sprint 1:**
- Esquema creado: tablas `units` y `reservations` con columnas, FK e índices correctos
- Seed inserta exactamente 5 equipos con codes/names/types correctos
- Seed idempotente: segunda ejecución = 0 inserciones, total 5
- Constraint UNIQUE en `code` (no duplicados)
- `name` NO es UNIQUE (MIC-01 y MIC-02 comparten nombre)
- FK enforced: insertar reservation con unit_id inexistente → IntegrityError
- Tests usan BD temporal aislada (no tocan `data/reservations.db`)
- Suite completa: 14 tests pasan en Python 3.10.7

## Decisiones Técnicas Documentadas

Ver `docs/decisions.md`:
- ADR-001: Uso de `sqlite3` directo sin ORM + FK por conexión
- ADR-002: Esquema v1 con `code` único, `name` no único, tipos inferidos

## Decisiones Pendientes (Próximos Sprints)

- [ ] Horarios de laboratorio (apertura/cierre, días hábiles)
- [ ] Lógica de disponibilidad (calendario semanal, bloques horarios)
- [ ] Creación/cancelación de reservas con validación de solapamiento
- [ ] Tests de persistencia real (reinicio de proceso)
- [ ] `docs/delegations.md` (tres delegaciones reales)

## Licencia

Challenge interno — uso educativo.