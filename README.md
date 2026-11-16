# Asistencia Docente - IES N.º 7 Populorum Progressio

Trabajo Final de Cursada. Adaptación del sistema de asistencia por reconocimiento
facial (incrementos 1 a 6, rama `main`) al **Contexto A: docentes del Populorum**.

El reconocimiento facial identifica al docente; el sistema busca qué obligación
horaria le corresponde en ese momento (clase, mesa de examen o jornada
institucional), decide si es una entrada o una salida, la clasifica y le pide
confirmación antes de guardar.

La rama `main` conserva el sistema original de alumnos y jornadas. Esta rama
(`adaptacion-populorum`) usa otro stack de Docker, otra base y otro volumen, así
que las dos versiones pueden convivir en la misma computadora.

## Requisitos

- Python 3.10 o superior
- Docker Desktop
- Una cámara web

## Instalación

1. Clonar el repositorio y pasar a la rama:

   ```
   git clone https://github.com/Rioja-popu/asistencia-facial.git
   cd asistencia-facial
   git checkout adaptacion-populorum
   ```

2. Crear el archivo `.env` a partir de `.env.example` y completar usuario y
   contraseña de PostgreSQL. El puerto sugerido es `5433` para no chocar con la
   base del sistema original (`5432`).

3. Levantar la base de datos:

   ```
   docker compose up -d
   ```

   La primera vez se crea el volumen `asistencia-docentes_pgdata` y se ejecutan
   `database/initdb/01-schema.sql` (tablas) y `02-datos-iniciales.sql` (usuario
   administrativo de demostración).

4. Crear el entorno virtual e instalar las dependencias:

   ```
   python -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt
   ```

5. Ejecutar la aplicación:

   ```
   python src\main.py
   ```

   Usuario de demostración: `admin` / `admin`.

Para volver a crear la base desde cero **de esta rama** (no afecta a la del
sistema original, que pertenece a otro stack): `docker compose down -v` y
`docker compose up -d`.

## Pruebas automáticas

Las reglas de negocio no dependen de la cámara ni de la base, y tienen pruebas:

```
pip install pytest
python -m pytest tests
```

## Pantallas

| Pantalla | Para qué sirve |
|---|---|
| Marcación | Cámara, reconocimiento y confirmación de entrada o salida |
| Docentes | Alta y edición de docentes con sus tres fotos; baja lógica (inactivo) o eliminación definitiva con todo su historial; importación desde un listado en Excel o CSV |
| Carreras y cátedras | Carreras del instituto y cátedras de cada una |
| Horarios | Día y horario en que cada docente dicta cada cátedra; importación desde una planilla de Excel |
| Actividades especiales | Jornadas institucionales y mesas de examen, con sus docentes y roles; listado exportable a Excel y PDF |
| Ausencias | Particulares y ausencias médicas, con seguimiento del certificado |
| Feriados y recesos | Días en que las clases habituales no se dictan |
| Informes | Situación de cada obligación de un docente en un período, resumen general de todos los docentes y corrección manual de marcaciones; Excel y PDF |

## Modelo de datos

El esquema completo está en `database/initdb/01-schema.sql`.

| Tabla | Contenido |
|---|---|
| `usuario` | Personal administrativo que inicia sesión |
| `docente` | Docentes que marcan asistencia; `activo` permite la baja sin borrar historial. DNI y CUIL pueden quedar vacíos en los docentes importados |
| `foto_docente` | Tres fotos por docente (frontal, lateral izquierdo, lateral derecho) |
| `carrera`, `catedra` | Cada cátedra pertenece a una carrera |
| `horario_catedra` | Obligación semanal: docente, cátedra, día, horario y período de vigencia |
| `actividad_especial` | Jornada institucional o mesa de examen, con fecha y horario |
| `actividad_docente` | Docentes de cada actividad; en las mesas, con rol (presidente, vocal, auxiliar) |
| `asistencia` | Una fila por docente, fecha y obligación: entrada, salida, tardanza, salida anticipada. Si se corrigió a mano, guarda quién, cuándo y el motivo |
| `ausencia` | Particular o ausencia médica de un docente en una fecha, con su estado |
| `dia_no_laborable` | Feriado (un día) o receso (de una fecha a otra) |

Cambios respecto del sistema original:

- `alumno` y `foto_alumno` se reemplazan por `docente` y `foto_docente`.
- Desaparece `jornada`: ya no se configura a mano cada día. El horario de cada
  docente está cargado y el sistema resuelve solo a qué obligación corresponde
  cada marcación.
- `asistencia` apunta a un horario de cátedra **o** a una participación en una
  actividad especial (nunca a las dos; lo controla un `CHECK`), y guarda el
  horario previsto de ese día para que el informe no cambie si después se
  modifica el horario.

## Importación de horarios

En **Horarios**, "Descargar planilla modelo" genera un Excel con el mismo cuadro
que usa el instituto: una hoja por curso, con la carrera y el curso arriba y una
grilla de módulos por día. Cada celda se completa como
`MATERIA - APELLIDO, NOMBRE`. "Importar desde Excel" lee la planilla y muestra una
vista previa antes de guardar.

- Los módulos seguidos de la misma cátedra y docente se unen en un solo horario.
- Las carreras, cátedras y docentes que ya existen se reutilizan (se comparan sin
  distinguir mayúsculas ni tildes); los que faltan se crean.
- Un horario que ya estaba cargado se omite, así que importar dos veces la misma
  planilla no duplica nada.
- No se importan los horarios que duran menos de una clase, los que se superponen
  con otro del mismo docente ni las celdas mal escritas: se listan con el motivo.
- Todo se guarda en una sola transacción: si algo falla, no queda nada a medias.
- Los docentes creados por la importación quedan sin DNI, CUIL ni fotos, y hay que
  completarlos en **Docentes** para que puedan marcar.

La lógica está en `src/services/importacion_service.py`. Una base creada antes de
esta función necesita aplicar una vez `database/migraciones/01-importacion-horarios.sql`.

## Importación de docentes

En Docentes, "Descargar listado modelo" genera un Excel con las columnas
APELLIDO, NOMBRE, DNI, CUIL, CELULAR y CORREO ELECTRONICO, e "Importar docentes"
lee ese listado en Excel o CSV (separado por coma o punto y coma).

- Apellido, nombre y DNI son obligatorios. DNI de 7 u 8 números y CUIL de 11; los
  puntos y guiones se ignoran.
- Antes de guardar se muestra una vista previa con lo que pasa con cada fila.
- **No duplica**: si ya hay un docente con ese DNI, o con el mismo apellido y
  nombre y sin DNI (por ejemplo, creado al importar horarios), no se crea otro:
  se le completan los datos vacíos. Nunca se pisa un dato ya cargado.
- Se rechazan las filas con datos inválidos, DNI o CUIL repetidos, o con el nombre
  de un docente que ya tiene otro DNI. Si un docente nuevo se parece a uno ya
  cargado (mismo apellido y nombre que empieza igual), se crea con un aviso.
- Se guarda todo o nada. Los docentes importados quedan sin fotos y no pueden
  marcar hasta que se las tomen.

Conviene importar primero los docentes y después los horarios: así los horarios
quedan asociados a docentes que ya tienen DNI y CUIL.

## Reglas de negocio

Están en `src/services/marcacion_service.py` (qué registrar) y
`src/services/situacion_service.py` (cómo se informa).

- **Duración de la clase**: 1 h 20 min, que es el mínimo de un horario. El cuadro
  de horarios del instituto se arma en módulos de 40 minutos y hay cátedras de tres
  módulos seguidos, así que un horario dura 80 minutos y crece de a 40 (80, 120,
  160...). Los módulos seguidos de la misma cátedra se cargan como un bloque. Lo
  valida la pantalla y también un `CHECK` de la base.
- **Tardanza**: entrada registrada pasados 5 minutos del inicio previsto. A los 5
  minutos exactos todavía es "en horario".
- **Salida anticipada**: salida registrada antes del fin previsto.
- **Salida sin registrar**: hay entrada, no hay salida y el horario ya terminó.
  No se guarda: se calcula al consultar.
- **Particulares**: 6 por docente y por año calendario. El séptimo se rechaza.
- **Ausencia médica**: nace como "certificado pendiente". Después se marca
  "justificada" (con la fecha en que se presentó el certificado) o "no justificada".
- **Ausente con aviso**: toda obligación de un día con un particular o una
  ausencia médica cargada figura así en el informe, con el detalle (particular,
  médica con certificado pendiente, médica justificada). Si la médica quedó no
  justificada pasa a "Ausencia médica no justificada".
- **Ausente sin aviso**: obligación ya finalizada, sin marcación y sin ausencia cargada.
- **Feriados y recesos**: las clases habituales de esos días no se pueden marcar,
  figuran como "Sin clases" y no cuentan como obligación ni como ausencia. Las
  mesas y jornadas cargadas para esos días se mantienen, porque tienen fecha propia.
- **Corrección manual**: desde Informes, el personal administrativo puede cargar o
  corregir la entrada y la salida de una obligación ya iniciada. El motivo es
  obligatorio y quedan guardados el usuario y el momento de la corrección. La
  tardanza y la salida anticipada se recalculan con las mismas reglas que una
  marcación hecha con la cámara, y el informe la señala como "corregida a mano".
- **Jornadas institucionales y mesas de examen**: usan las mismas reglas de
  entrada, tardanza, salida y salida anticipada que una clase.

## Flujo de marcación y modal de confirmación

1. La cámara detecta un rostro y lo compara con las fotos de los docentes activos.
2. Si reconoce a un docente, el hilo de la cámara **pausa el reconocimiento** antes
   de avisar a la pantalla. El video sigue viéndose.
3. El sistema busca las obligaciones del día y decide qué proponer.
4. Si hay algo para registrar, muestra un modal con el docente, la operación
   (entrada o salida), la cátedra o actividad, el horario previsto y los avisos
   (tardanza, salida anticipada), con los botones **OK** y **Cancelar**.
5. Con **OK** se guarda. Con **Cancelar** no se ejecuta ningún `INSERT` ni `UPDATE`.
6. En los dos casos, al cerrarse el modal el reconocimiento se reanuda.

Si no hay nada para registrar (sin actividad, demasiado temprano, asistencia
completa), no hay modal: se muestra el motivo debajo de la cámara.

## Casos especiales y decisiones

| Caso | Decisión |
|---|---|
| Ventana de entrada | Desde 30 minutos antes del inicio hasta el fin previsto. Antes se informa desde qué hora se puede marcar; después, ya no se admite la entrada |
| Clases pegadas (una termina cuando empieza la otra) | Forman un bloque: una sola entrada y una sola salida para todas. La tardanza y la salida anticipada se calculan para cada clase |
| Clases separadas por un intervalo | Se marcan por separado, cada una con su entrada y su salida |
| Entrada con el bloque ya empezado | Sólo cubre las clases que todavía no terminaron; las anteriores quedan como ausente |
| Segunda pasada apenas marcada la entrada | Durante 5 minutos no se propone la salida, para no generar una salida anticipada por error |
| Salida olvidada y nueva clase más tarde | Primero se propone cerrar la salida pendiente; en la pasada siguiente, la nueva entrada |
| Asistencia ya completa | No se registra nada y se informa |
| Sin actividad ese día | No se registra nada y se informa |
| Clase que coincide con una mesa o jornada | Manda la actividad especial; la clase figura como "Reemplazada por actividad especial" |
| Docente con ausencia cargada que igual se presenta | Puede marcar; el modal lo avisa y el informe lo señala para revisión |
| Docente inactivo | No se lo compara al reconocer y no puede marcar |
| Rostro no reconocido | No se registra nada |
| Cambio de horario durante el año | El horario anterior se da de baja con fecha (`vigente_hasta`) y se carga el nuevo; los informes anteriores no cambian |
| Clase en un feriado o receso | Figura como "Sin clases" y no cuenta en los totales. Si el feriado se carga después de que alguien marcó, esa marcación se conserva y se informa normalmente |
| Mesa o jornada en un feriado o receso | Se mantiene: se puede marcar y cuenta como obligación |
| Docente que olvidó marcar la salida | Queda "Salida sin registrar" hasta que el personal administrativo la corrige desde Informes |
| Corrección de una clase en feriado o de una obligación futura | No se admite |

## Informes

Se elige un docente y un período. Cada fila es una obligación con fecha, día,
cátedra o actividad, horario previsto, entrada, salida y situación. Al pie se
muestran los totales por situación. El Excel y el PDF agregan los datos del
docente, los particulares usados en el año y el usuario que generó el informe.

Con "Todos los docentes (resumen general)" se obtiene una fila por docente con
obligaciones en el período: cantidad de obligaciones, en horario, tardanzas,
salidas anticipadas, salidas sin registrar, ausencias con y sin aviso, médicas no
justificadas y particulares usados en el año, más una fila de totales. También se
exporta a Excel y PDF.

"Corregir marcación" actúa sobre la obligación seleccionada del informe de un docente.

Las bases creadas antes de estas funciones necesitan, una sola vez,
`database/migraciones/02-feriados-y-correcciones.sql`.

## Estructura del proyecto

```
assets/                 Escudo del instituto
database/initdb/        Esquema y datos iniciales
src/config/             Conexión a PostgreSQL
src/repositories/       Consultas SQL
src/services/           Cámara, reconocimiento, reglas de negocio e informes
src/ui/                 Pantallas (PySide6)
tests/                  Pruebas automáticas de las reglas y los informes
```
