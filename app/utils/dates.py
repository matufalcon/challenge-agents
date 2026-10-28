"""Utilidades de fechas y zona horaria — Sprint 2.

Política (ADR-004):
- Almacenamiento en BD: UTC como TEXT 'YYYY-MM-DD HH:MM:SS' (formato SQLite datetime('now'))
- API entrada: ISO 8601 con zona horaria explícita (ej. '2025-01-15T10:00:00-03:00' o '2025-01-15T13:00:00Z')
- API salida: ISO 8601 con offset ART '-03:00' (ej. '2025-01-15T10:00:00-03:00')
- UI: datetime-local naive (asumido ART), conversión en boundaries
"""

from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from typing import Optional

# Zona horaria Argentina (ART, UTC-3, sin DST desde 2009)
ART = ZoneInfo("America/Argentina/Buenos_Aires")
UTC = timezone.utc

# Formatos
DB_FMT = "%Y-%m-%d %H:%M:%S"           # Almacenamiento BD: 'YYYY-MM-DD HH:MM:SS' (UTC implícito)
ISO_FMT = "%Y-%m-%dT%H:%M:%S%z"        # ISO 8601 con offset: '2025-01-15T10:00:00-0300'
ISO_FMT_COLON = "%Y-%m-%dT%H:%M:%S%z"  # Para parsing (strptime no soporta : en %z directamente)
UI_FMT = "%d/%m/%Y %H:%M"              # Display local: '15/01/2025 10:00'
HTML_DATETIME_LOCAL_FMT = "%Y-%m-%dT%H:%M"  # <input type="datetime-local">: '2025-01-15T10:00'


def now_utc() -> datetime:
    """Retorna ahora en UTC (aware)."""
    return datetime.now(UTC)


def now_art() -> datetime:
    """Retorna ahora en ART (aware)."""
    return datetime.now(ART)


def to_utc(dt: datetime) -> datetime:
    """Convierte cualquier datetime a UTC (aware).
    
    - Si naive: asume ART (zona horaria del laboratorio)
    - Si aware: convierte a UTC
    """
    if dt.tzinfo is None:
        return dt.replace(tzinfo=ART).astimezone(UTC)
    return dt.astimezone(UTC)


def to_art(dt: datetime) -> datetime:
    """Convierte cualquier datetime a ART (aware).
    
    - Si naive: asume ART
    - Si aware: convierte a ART
    """
    if dt.tzinfo is None:
        return dt.replace(tzinfo=ART)
    return dt.astimezone(ART)


def parse_iso_with_tz(s: str) -> datetime:
    """Parsea string ISO 8601 con zona horaria explícita a datetime aware UTC.
    
    Acepta:
    - '2025-01-15T10:00:00-03:00' (offset con dos puntos)
    - '2025-01-15T10:00:00-0300' (offset sin dos puntos)
    - '2025-01-15T13:00:00Z' (UTC)
    - '2025-01-15T13:00:00+00:00'
    - Con o sin segundos
    
    Raises:
        ValueError: Si el formato es inválido o falta zona horaria.
    """
    if not s or not isinstance(s, str):
        raise ValueError("Fecha vacía o tipo inválido")
    
    s = s.strip()
    if not s:
        raise ValueError("Fecha vacía")
    
    # Normalizar Z a +00:00 para manejo uniforme
    if s.endswith('Z') or s.endswith('z'):
        s = s[:-1] + '+00:00'
    
    # Si el offset tiene dos puntos (HH:MM), quitar los dos puntos para strptime
    # strptime %z espera HHMM o HH:MM (Python 3.7+ soporta ambos, pero aseguramos)
    # Buscar patrón de offset al final: ±HH:MM o ±HHMM
    import re
    offset_pattern = re.compile(r'([+-])(\d{2}):(\d{2})$')
    match = offset_pattern.search(s)
    if match:
        s = s[:-6] + match.group(1) + match.group(2) + match.group(3)
    
    # Intentar parsear con segundos primero, luego sin segundos
    for fmt in ("%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M%z"):
        try:
            dt = datetime.strptime(s, fmt)
            return dt.astimezone(UTC)
        except ValueError:
            continue
    
    raise ValueError(
        f"Formato ISO 8601 inválido: '{s}'. "
        f"Use 'YYYY-MM-DDTHH:MM:SS±HH:MM', 'YYYY-MM-DDTHH:MM±HH:MM' o 'Z'"
    )


def parse_html_datetime_local(s: str) -> datetime:
    """Parsea input HTML datetime-local (naive) asumiendo ART → retorna UTC aware.
    
    Input: '2025-01-15T10:00' (naive, hora local Argentina)
    Output: datetime aware UTC
    """
    if not s:
        raise ValueError("Fecha vacía")
    try:
        dt_naive = datetime.strptime(s, HTML_DATETIME_LOCAL_FMT)
    except ValueError:
        raise ValueError(f"Formato datetime-local inválido: '{s}'. Use 'YYYY-MM-DDTHH:MM'")
    return dt_naive.replace(tzinfo=ART).astimezone(UTC)


def fmt_db(dt_utc: datetime) -> str:
    """Formatea datetime UTC aware para almacenamiento en BD: 'YYYY-MM-DD HH:MM:SS'.
    
    Asume dt_utc es aware UTC. Si naive, asume UTC.
    """
    if dt_utc.tzinfo is None:
        dt_utc = dt_utc.replace(tzinfo=UTC)
    elif dt_utc.tzinfo != UTC:
        dt_utc = dt_utc.astimezone(UTC)
    return dt_utc.strftime(DB_FMT)


def fmt_iso_with_offset(dt_utc: datetime) -> str:
    """Formatea datetime UTC aware a ISO 8601 con offset ART (-03:00).
    
    Output: '2025-01-15T10:00:00-03:00'
    """
    dt_art = to_art(dt_utc)
    # strftime %z da -0300, insertar ':'
    offset = dt_art.strftime("%z")
    offset_with_colon = f"{offset[:3]}:{offset[3:]}"
    return dt_art.strftime("%Y-%m-%dT%H:%M:%S") + offset_with_colon


def fmt_ui(dt_utc: datetime) -> str:
    """Formatea datetime UTC aware para display en UI (ART): 'DD/MM/YYYY HH:MM'."""
    dt_art = to_art(dt_utc)
    return dt_art.strftime(UI_FMT)


def parse_db_utc(s: str) -> datetime:
    """Parsea string de BD 'YYYY-MM-DD HH:MM:SS' (UTC implícito) → datetime aware UTC."""
    if not s:
        raise ValueError("Fecha vacía")
    dt = datetime.strptime(s, DB_FMT)
    return dt.replace(tzinfo=UTC)


def validate_interval(start_utc: datetime, end_utc: datetime) -> Optional[str]:
    """Valida que start < end. Retorna mensaje de error o None si OK."""
    if start_utc >= end_utc:
        return "La fecha/hora de inicio debe ser anterior a la de fin"
    return None


def validate_user(user: str) -> Optional[str]:
    """Valida que user no sea vacío. Retorna mensaje de error o None si OK."""
    if not user or not user.strip():
        return "El solicitante (user) es obligatorio"
    return None