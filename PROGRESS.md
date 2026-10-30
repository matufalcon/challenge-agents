# Progreso del proyecto

## Estado actual

- **Sprint 0:** Aplicación Flask inicial, configuración base, página de inicio con identidad visual.
- **Sprint 1:** Esquema SQLite, seed idempotente, inventario fijo de cinco equipos.
- **Sprint 2.1:** Utilidades de fechas/zonas horarias, validación de entrada de reservas.
- **Sprint 2.2:** Capa de persistencia (crear, consultar, cancelar reservas).
- **Sprint 2.3:** Validación de solapamientos entre reservas (`check_overlap`, `create_reservation_with_validation`).
- **Sprint 2.4:** Endpoints API REST (`GET /api/units`, `GET /api/reservations/<id>`, `POST /api/reservations`, `PATCH /api/reservations/<id>/cancel`, `GET /api/availability`).

## Verificaciones

- Suite completa: **107 tests aprobados** en la última ejecución (2025-10-27).
- Servidor Flask: inicio verificado (`python run.py`).
- Base de datos real (`data/reservations.db`): intacta tras la suite de tests (no se modifica mtime ni size).
- Persistencia de reservas: pruebas de creación, consulta, cancelación, conservación de datos y liberación de intervalos.
- Validación de solapamiento: 11 tests cubriendo mismo equipo, equipos distintos, intervalos consecutivos, contenido, envolvente, canceladas, solapamientos parciales, y creación con validación integrada.
- Endpoints API: 23 tests de integración cubriendo casos de éxito, errores de validación, equipo inexistente, solapamiento, cancelación y disponibilidad.

## Historial de tareas

| Tarea | Descripción | Tests añadidos | Estado |
|-------|-------------|----------------|--------|
| Sprint 0 | App Flask, health check, página inicial, CSS base | 3 | ✅ |
| Sprint 1 | Esquema BD, seed idempotente, inventario 5 equipos | 11 | ✅ |
| Sprint 2.1 | Utils fechas, validación input, tipos, zona horaria | 37 | ✅ |
| Sprint 2.2 | Modelos persistencia (create, get, cancel, listar activas) | 8 | ✅ |
| Sprint 2.3 | check_overlap, create_reservation_with_validation, 11 tests solapamiento | 11 | ✅ |
| Sprint 2.4 | 5 endpoints API REST + 23 tests de integración | 23 | ✅ |

**Total tests**: 107 (3 health + 11 DB + 37 validación/fechas + 8 persistencia + 11 solapamiento + 4 dict + 10 otros + 23 API).

## Pendiente

- **Sprint 3:** Disponibilidad y calendario semanal, interfaz web.
- Integración de funcionalidades y pruebas de extremo a extremo.
- Completar `docs/delegations.md` con tres delegaciones reales y evidencia verificable.
- Completar documentación final y revisión para entrega.

## Criterio de actualización

Actualizar este archivo al cerrar tareas relevantes, indicando los cambios realizados y los resultados reales de las pruebas ejecutadas.