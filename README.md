# Reservas Lab — Challenge

Sistema local de reservas de equipos de laboratorio con identidad visual propia.

## Stack Tecnológico

- **Python** 3.10+ (probado en 3.10.7)
- **Flask** 3.0 — microframework web
- **SQLite** (stdlib) — persistencia local (Sprint 1+)
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

## Estructura del Proyecto (Sprint 0)

```
challenge-reservas/
├── app/
│   ├── __init__.py          # Factory Flask
│   ├── config.py            # Config centralizada
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
├── tests/
│   ├── __init__.py
│   ├── conftest.py          # Fixtures pytest
│   └── test_health.py       # Tests /health y GET /
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

# 5. Ejecutar pruebas automatizadas
pytest -v

# 6. Levantar servidor de desarrollo
python run.py
```

> **Nota**: Si PowerShell bloquea la activación del script, ejecutar:
> `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`
> y volver a intentar el paso 3.

El servidor estará disponible en: **http://localhost:5000**

Endpoints:
- `GET /` — Página inicial con identidad visual
- `GET /health` — Health check JSON `{"status":"ok","tz":"America/Argentina/Buenos_Aires"}`

## Pruebas Automatizadas

```powershell
# Ejecutar suite completa
pytest -v

# Ejecutar solo tests de salud
pytest tests/test_health.py -v
```

**Criterios de aceptación Sprint 0:**
- `GET /health` → 200 + JSON con `status: "ok"` y `tz: "America/Argentina/Buenos_Aires"`
- `GET /` → 200 + HTML que contiene "Reservas Lab", "Sistema de reservas de equipos de laboratorio", "Versión 0.1.0", "Argentina (ART, UTC-3)", y las tres funcionalidades previstas
- Tests pasan en Python 3.10.7

## Decisiones Pendientes (Próximos Sprints)

- [ ] Horarios de laboratorio (apertura/cierre, días hábiles)
- [ ] Esquema BD y `seed.py` con 5 unidades del challenge
- [ ] Lógica de disponibilidad (calendario semanal, bloques horarios)
- [ ] Creación/cancelación de reservas con validación de solapamiento
- [ ] Tests de persistencia real (reinicio de proceso)
- [ ] `docs/decisions.md` y `docs/delegations.md` (trazabilidad)

## Licencia

Challenge interno — uso educativo.