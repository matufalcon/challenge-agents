# Registro de delegaciones y uso del agente

## 1. Entorno y preparación del agente

### Entorno de trabajo

- **Sistema operativo:** Windows.
- **Lenguaje:** Python 3.10.7.
- **Framework:** Flask 3.0.
- **Persistencia:** SQLite mediante `sqlite3`.
- **Agente de programación:** Pi, versión 1.3.0.
- **Proveedor/modelo:** OpenRouter, `nvidia/nemotron-3-ultra-550b-a55b:free`, utilizado en algunas sesiones.
- **Repositorio:** `challenge-agents`.
- **Rama de entrega:** `main`.
- **Versión de referencia:** `f62479d646e042beda8b231c1bb14ad819485a64`.

El modelo se utilizó mediante un proveedor gratuito. No se conserva evidencia suficiente para asociar con certeza un modelo específico a cada episodio de delegación.

### Rol del agente

Pi se utilizó como agente de programación con acceso al repositorio y herramientas para inspeccionar y modificar archivos, ejecutar comandos y trabajar con las pruebas del proyecto.

Su función fue colaborar en tareas de implementación y documentación. La revisión de los cambios, la validación de resultados y las decisiones de aceptación quedaron bajo supervisión humana.

### Instrucciones aplicadas

El archivo `AGENTS.md` contiene las instrucciones persistentes del proyecto. Entre las reglas establecidas se encuentran:

> Antes de implementar, explicá brevemente el plan y los archivos que pensás modificar.

> No agregues funcionalidades fuera del alcance sin consultar.

> No inventes resultados de pruebas, decisiones humanas ni episodios de delegación.

> No hagas commits automáticamente.

> Antes de finalizar una tarea, informá los archivos modificados, las pruebas ejecutadas y sus resultados reales.

Estas instrucciones buscaron limitar el alcance de las tareas, favorecer cambios verificables y mantener el control humano sobre el repositorio.

### Contexto disponible

El agente trabajó sobre el repositorio existente y sus archivos de instrucciones y seguimiento, especialmente:

- `AGENTS.md`: reglas de trabajo, alcance y control humano.
- `PROGRESS.md`: estado de los sprints, verificaciones y tareas pendientes.
- Código fuente, pruebas y documentación del proyecto.
- Requisitos funcionales del challenge.

No se conserva una transcripción completa de todos los prompts ni un registro que permita reconstruir exactamente el contexto enviado en cada sesión. Por ese motivo, los fragmentos de instrucciones incluidos en este documento corresponden a reglas persistentes verificables, no a citas literales de cada conversación con el agente.

### Control humano

El agente podía realizar modificaciones en el repositorio y ejecutar herramientas. El control humano se aplicó mediante:

- Revisión de los archivos modificados y sus diferencias.
- Supervisión de los comandos ejecutados.
- Revisión de los resultados de las pruebas.
- Decisión humana sobre la aceptación de los cambios.
- Prohibición de commits automáticos y de operaciones destructivas sin autorización.

---

## 2. Episodios de delegación

### Episodio 1 — Validación de solapamientos

**Objetivo**

Implementar la validación que impide crear reservas superpuestas para una misma unidad, sin impedir intervalos consecutivos ni reservas simultáneas de unidades diferentes.

**Requisito funcional**

- Rechazar solapamientos entre reservas activas de una misma unidad.
- Permitir intervalos consecutivos.
- Permitir reservas simultáneas de unidades diferentes.
- No considerar las reservas canceladas como bloqueos.

**Contexto e instrucciones**

El agente trabajó sobre la capa de persistencia y servicios de reservas, siguiendo las reglas de `AGENTS.md`:

> Respetá el inventario y las reglas del enunciado.

> No debe haber superposición entre reservas activas de una misma unidad.

> Los límites de intervalos consecutivos deben permitirse.

**Acción y resultado**

Se incorporó la validación de solapamientos mediante `check_overlap` y su integración con `create_reservation_with_validation`.

La implementación contempla reservas activas de la misma unidad y excluye las canceladas del cálculo de conflictos.

**Decisión humana**

Se aceptó la implementación al comprobar que las reglas principales estaban cubiertas: rechazo de solapamientos en una misma unidad, aceptación de intervalos consecutivos, independencia entre unidades y exclusión de reservas canceladas. La suite incluye pruebas específicas para cada uno de esos comportamientos.

No se dispone de evidencia de una corrección funcional concreta solicitada al agente durante este episodio.

**Evidencia verificable**

- Commit: `b49fa92` — `feat: validar solapamientos de reservas`.
- Archivo de pruebas: `tests/test_reservations.py`.
- Pruebas relacionadas:
  - `test_overlap_same_unit_rejected`
  - `test_overlap_different_unit_allowed`
  - `test_consecutive_end_equals_start_allowed`
  - `test_consecutive_start_equals_end_allowed`
  - `test_cancelled_not_block`
  - `test_create_with_validation_rejects_overlap`
  - `test_create_with_validation_succeeds`

Estas pruebas forman parte de la suite de 110 tests cuyo resultado aprobado está registrado en `PROGRESS.md` el 5 de noviembre de 2026.

### Episodio 2 — Persistencia y ciclo de vida de las reservas

**Objetivo**

Implementar la persistencia de las reservas y las operaciones necesarias para consultarlas y cancelarlas, conservando sus datos.

**Requisito funcional**

- Guardar las reservas en una base de datos persistente.
- Permitir consultar una reserva por su identificador.
- Cancelar una reserva sin eliminar su registro.
- Conservar identificador y datos originales.
- Liberar el intervalo de una reserva cancelada.

**Contexto e instrucciones**

El agente trabajó sobre el esquema SQLite y la capa de modelos, siguiendo las instrucciones de `AGENTS.md`:

> Las reservas deben persistir al reiniciar la aplicación.

> Las reservas canceladas deben conservar su identificador y sus datos, pero liberar el intervalo.

> No borres datos ni reinicialices la base sin autorización explícita.

**Acción y resultado**

Se incorporaron las operaciones de creación, consulta y cancelación de reservas en la capa de persistencia.

La cancelación actualiza el estado del registro y conserva sus datos originales. Las consultas de reservas activas y la validación de disponibilidad dejan de considerar los intervalos cancelados.

**Decisión humana**

Se aceptó la implementación al verificar que las operaciones de creación, consulta y cancelación contaban con pruebas específicas, y que la cancelación conservaba los datos originales y liberaba el intervalo. Estos comportamientos coinciden con las reglas funcionales establecidas para el sistema.

No se dispone de evidencia de una corrección funcional concreta solicitada al agente durante este episodio. La recuperación de datos después de reiniciar la aplicación queda como una comprobación sin evidencia específica documentada.

**Evidencia verificable**

- Commit: `85a151d` — `feat: agregar persistencia de reservas`.
- Archivo de pruebas: `tests/test_reservations.py`.
- Pruebas relacionadas:
  - `test_create_reservation_persists`
  - `test_get_reservation_by_id`
  - `test_cancel_reservation_updates_status`
  - `test_cancel_reservation_frees_interval`
  - `test_cancel_reservation_idempotent`

La prueba `test_cancel_reservation_updates_status` verifica que la reserva conserva sus datos originales y cambia su estado a cancelada. `test_cancel_reservation_frees_interval` verifica que deja de aparecer entre las reservas activas de la unidad.

### Episodio 3 — Modal y creación de reservas desde la interfaz

**Objetivo**

Incorporar el flujo de creación de reservas desde la interfaz web, conectando el formulario con la API y contemplando los errores de validación y conflictos.

**Requisito funcional**

- Abrir el formulario desde un bloque disponible del calendario.
- Precargar equipo, fecha y horario.
- Permitir editar el horario de finalización.
- Enviar la solicitud a la API.
- Mostrar los errores sin perder los datos ingresados.
- Actualizar el calendario luego de una creación exitosa.
- Evitar envíos duplicados.

**Contexto e instrucciones**

El agente trabajó sobre las plantillas, los estilos y el JavaScript de la interfaz, además de los endpoints existentes.

Se mantuvieron las reglas de `AGENTS.md`:

> Trabajá en tareas pequeñas y verificables.

> Antes de implementar, explicá brevemente el plan y los archivos que pensás modificar.

> Esperá revisión humana antes de avanzar a una tarea importante.

**Acción y resultado**

El trabajo se desarrolló en varias etapas:

- Estructura HTML del modal y estilos.
- Apertura desde los bloques disponibles y precarga de datos.
- Envío del formulario mediante `POST /api/reservations`.
- Manejo de respuestas exitosas y errores, incluidos los conflictos HTTP 409.
- Actualización del calendario después de una creación exitosa.
- Prevención de envíos duplicados.

**Decisión humana**

Se revisó el flujo en el navegador, desde la selección de un bloque disponible hasta el envío del formulario. Se aceptó porque permitió crear reservas, actualizar el calendario sin recargar la página y manejar los conflictos y errores sin cerrar el modal ni perder los datos ingresados. También se comprobó la prevención de envíos duplicados.

Hubo una intervención humana sobre la presentación visual, registrada en el commit `ff7b629`. No se cuenta con evidencia suficiente para atribuir esa intervención a una corrección funcional solicitada al agente.

**Evidencia verificable**

- `75904fd` — `feat: agregar modal de nueva reserva`.
- `7cd78ff` — `feat: implementar apertura del modal de reservas`.
- `b3f5eac` — `feat: implementar envío del formulario de reserva`.
- `f62479d` — `docs: actualizar progreso del sprint 3.4.3`.
- `ff7b629` — `style: rediseñar la interfaz con mejor contraste, componentes`.

La validación manual y el resultado de 110 tests aprobados están registrados en `PROGRESS.md`, con fecha 5 de noviembre de 2026.

---

## 3. Verificación de pruebas y resultados

La suite automatizada está compuesta por 110 tests distribuidos en:

- `tests/test_health.py`
- `tests/test_db.py`
- `tests/test_reservations.py`
- `tests/test_api.py`
- `tests/test_web.py`

El registro de `PROGRESS.md` informa que los 110 tests fueron aprobados el 5 de noviembre de 2026.

Entre las pruebas específicas que respaldan los requisitos funcionales se encuentran:

| Requisito | Prueba |
|---|---|
| Crear y persistir una reserva | `test_create_reservation_persists` |
| Rechazar solapamientos | `test_overlap_same_unit_rejected` |
| Permitir unidades diferentes | `test_overlap_different_unit_allowed` |
| Permitir intervalos consecutivos | `test_consecutive_end_equals_start_allowed` |
| Conservar datos al cancelar | `test_cancel_reservation_updates_status` |
| Liberar el intervalo al cancelar | `test_cancel_reservation_frees_interval` |
| Rechazar conflictos en la API | `test_post_reservation_overlap` |
| Consultar disponibilidad consecutiva | `test_availability_consecutive_allowed` |

La recopilación de pruebas realizada durante la revisión del documento confirmó que pytest encuentra 110 tests. Esa recopilación no equivale a una ejecución: el resultado de aprobación citado corresponde al registro previo de `PROGRESS.md`.

---

## 4. Versión de referencia y trazabilidad

La rama de referencia para la entrega es `main`.

## 5. Limitaciones de la evidencia

- No se conserva la transcripción literal de todos los prompts enviados al agente.
- No hay evidencia suficiente para identificar el modelo exacto utilizado en cada episodio.
- No se dispone de una prueba documentada de reinicio de la aplicación que confirme la recuperación de una reserva previamente creada.
- La recopilación de los 110 tests realizada durante esta revisión no constituye una nueva ejecución de la suite.

Estas limitaciones se explicitan para diferenciar los resultados efectivamente registrados de las comprobaciones que todavía no cuentan con evidencia específica.