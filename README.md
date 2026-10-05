# Industrial Alarm Gateway & Migrator

Sistema para la migración, limpieza, normalización, almacenamiento y consulta de históricos de alarmas industriales provenientes de sistemas SCADA.

El proyecto recibe un conjunto de datos históricos con inconsistencias intencionales, realiza un proceso ETL para mejorar su calidad, almacena los registros normalizados en una base de datos relacional SQLite y expone una API REST desarrollada con FastAPI para consultar y analizar las alarmas.

---

## 1. Descripción del problema

Un cliente industrial se encuentra modernizando su infraestructura y dispone de históricos de alarmas provenientes de un sistema SCADA.

Los datos históricos presentan diferentes problemas de calidad, entre ellos:

- Registros incompletos.
- Valores nulos.
- Formatos de fecha heterogéneos.
- Tipos de datos inconsistentes.
- Diferencias de mayúsculas, minúsculas y espacios.
- Valores inválidos.
- Registros duplicados.
- Diferentes representaciones para los estados y niveles de severidad.

El objetivo es construir una solución que permita:

1. Generar un dataset representativo de alarmas industriales.
2. Introducir problemas de calidad de datos de forma controlada.
3. Limpiar y normalizar los registros.
4. Separar los registros válidos, rechazados y duplicados.
5. Almacenar los datos normalizados en una base de datos relacional.
6. Exponer la información mediante una API REST.
7. Permitir consultas y agregaciones sobre las alarmas.

---

## 2. Arquitectura de la solución

El flujo general del sistema es:

```text
                 ┌─────────────────────┐
                 │  generate_data.py   │
                 │ Generación de datos │
                 └──────────┬──────────┘
                            │
                            ▼
                 ┌─────────────────────┐
                 │   alarms_raw.csv    │
                 │    Datos crudos     │
                 └──────────┬──────────┘
                            │
                            ▼
                 ┌─────────────────────┐
                 │    clean_data.py    │
                 │ Limpieza y ETL      │
                 └──────────┬──────────┘
                            │
              ┌─────────────┼──────────────────────────┐
              ▼             ▼                          ▼
       alarms_clean.csv  alarms_rejected.csv  alarms_duplicates.csv
              │
              ▼
       ┌─────────────────┐
       │ load_database.py│
       └────────┬────────┘
                │
                ▼
          ┌───────────┐
          │ alarms.db │
          │  SQLite   │
          └─────┬─────┘
                │
                ▼
       ┌─────────────────┐
       │    FastAPI      │
       │     REST API    │
       └────────┬────────┘
                │
                ▼
       Consultas / métricas
```

---

## 3. Estructura del proyecto

```text
SOAP/
│
├── .venv/
│
├── api/
│   ├── main.py
│   └── database.py
│
├── data/
│   ├── raw/
│   │   └── alarms_raw.csv
│   │
│   └── clean/
│       ├── alarms_clean.csv
│       ├── alarms_duplicates.csv
│       ├── alarms_rejected.csv
│       ├── quality_report.txt
│       └── alarms.db
│
├── generate_data.py
├── clean_data.py
├── load_database.py
├── requirements.txt
└── README.md
```

---

## 4. Tecnologías utilizadas

- **Python 3.14**
- **Pandas** — generación, transformación y limpieza de datos.
- **FastAPI** — desarrollo de la API REST.
- **Uvicorn** — servidor ASGI para ejecutar FastAPI.
- **SQLite** — almacenamiento relacional.
- **SQL** — consultas, filtros y agregaciones.
- **PowerShell** — ejecución del proyecto en Windows.

SQLite fue seleccionado como motor relacional debido a que permite implementar la solución sin requerir la instalación de un servidor de base de datos externo. La arquitectura permite migrar posteriormente a otros motores como PostgreSQL o SQL Server.

---

## 5. Instalación

### 5.1. Requisitos

Se requiere:

- Python 3.14 o compatible.
- `uv`.

El proyecto utiliza un entorno virtual ubicado en:

```text
.venv/
```

### 5.2. Crear el entorno virtual

Desde la carpeta raíz del proyecto:

```powershell
cd "D:\Usuarios\Julio\Documentos\SOAP"
```

Si es necesario crear nuevamente el entorno:

```powershell
uv venv .venv
```

### 5.3. Instalar dependencias

Las dependencias se encuentran en `requirements.txt`:

```text
pandas
fastapi
uvicorn
```

Para instalarlas:

```powershell
uv pip install -r requirements.txt --python .venv\Scripts\python.exe
```

SQLite no aparece en `requirements.txt` porque `sqlite3` forma parte de la biblioteca estándar de Python.

---

## 6. Generación del dataset

El script:

```text
generate_data.py
```

genera un dataset representativo de alarmas industriales.

La generación utiliza una semilla fija:

```python
SEED = 42
```

Esto permite obtener resultados reproducibles.

El dataset contiene inicialmente:

```text
9.900 registros base
```

y se agregan duplicados intencionales, obteniendo finalmente:

```text
9.999 registros
```

### Variables generadas

El dataset contiene los siguientes campos:

| Campo | Descripción |
|---|---|
| `timestamp` | Fecha y hora del evento |
| `tag_name` | Tag o equipo asociado |
| `alarm_type` | Tipo de alarma |
| `severity` | Nivel de severidad |
| `value` | Valor asociado al evento |
| `status` | Estado de la alarma |

### Problemas de calidad introducidos

El dataset fue diseñado para representar condiciones que pueden encontrarse en históricos SCADA reales.

Se incluyen:

- Fechas en diferentes formatos.
- Fechas inválidas.
- Valores nulos.
- Tags con espacios y diferencias de formato.
- Diferencias entre mayúsculas y minúsculas.
- Severidades inválidas.
- Estados inválidos.
- Valores numéricos almacenados como texto.
- Valores como `ERROR` y `N/A`.
- Registros duplicados.

Para generar nuevamente los datos:

```powershell
& ".\.venv\Scripts\python.exe" generate_data.py
```

El archivo generado se almacena automáticamente en:

```text
data/raw/alarms_raw.csv
```

Las rutas se construyen utilizando la ubicación del proyecto, evitando depender de una ruta absoluta específica.

---

## 7. Limpieza y normalización

El proceso de limpieza se encuentra en:

```text
clean_data.py
```

El script lee:

```text
data/raw/alarms_raw.csv
```

y genera los resultados dentro de:

```text
data/clean/
```

Los archivos generados son:

```text
alarms_clean.csv
alarms_rejected.csv
alarms_duplicates.csv
quality_report.txt
```

### Clasificación de registros

Los registros son procesados y clasificados según su calidad:

- **Clean:** registros que cumplen las reglas de validación.
- **Rejected:** registros que contienen errores que impiden su incorporación al dataset limpio.
- **Duplicates:** registros duplicados eliminados durante el proceso.

También se genera un reporte de calidad con información sobre el resultado del proceso ETL.

### Resultado de la ejecución

La ejecución validada produjo:

| Categoría | Registros |
|---|---:|
| Registros crudos | 9.999 |
| Registros limpios | 7.809 |
| Registros rechazados | 2.078 |
| Duplicados eliminados | 112 |

Por lo tanto:

```text
9.999 registros de entrada
        ↓
7.809 registros válidos
2.078 registros rechazados
  112 duplicados
```

Para ejecutar el proceso:

```powershell
& ".\.venv\Scripts\python.exe" clean_data.py
```

---

## 8. Resultados de calidad

### Distribución por severidad

Después de la limpieza:

| Severidad | Registros |
|---|---:|
| LOW | 7.070 |
| HIGH | 333 |
| CRITICAL | 214 |
| MEDIUM | 192 |

Total:

```text
7.809 registros
```

### Distribución por estado

| Estado | Registros |
|---|---:|
| CLEARED | 7.337 |
| ACTIVE | 328 |
| ACKNOWLEDGED | 144 |

### Distribución por tag

| Tag | Registros |
|---|---:|
| LT-101 | 1.725 |
| PT-101 | 1.715 |
| FT-101 | 1.448 |
| TT-101 | 1.418 |
| M-101 | 684 |
| V-101 | 682 |
| P-101 | 80 |
| P-102 | 57 |

---

## 9. Base de datos

La base de datos se genera mediante:

```text
load_database.py
```

El archivo SQLite resultante es:

```text
data/clean/alarms.db
```

Para generarla:

```powershell
& ".\.venv\Scripts\python.exe" load_database.py
```

La base de datos contiene los 7.809 registros limpios.

### Tabla `alarms`

La estructura principal contiene:

| Campo | Descripción |
|---|---|
| `id` | Identificador único |
| `timestamp` | Fecha y hora de la alarma |
| `tag_name` | Tag asociado |
| `alarm_type` | Tipo de alarma |
| `severity` | Severidad |
| `value` | Valor del evento |
| `status` | Estado |

### Índices

Se crearon índices para optimizar las consultas más importantes:

```text
idx_alarms_timestamp
idx_alarms_tag
idx_alarms_severity
idx_alarms_status
```

Estos índices permiten mejorar el rendimiento de consultas filtradas por fecha, tag, severidad y estado.

---

## 10. API REST

La API se encuentra dentro de:

```text
api/
├── main.py
└── database.py
```

La aplicación utiliza:

```text
FastAPI
```

y se ejecuta mediante:

```text
Uvicorn
```

### Ejecutar la API

Desde la raíz del proyecto:

```powershell
cd "D:\Usuarios\Julio\Documentos\SOAP"
& ".\.venv\Scripts\python.exe" -m uvicorn api.main:app --reload
```

La API estará disponible en:

```text
http://127.0.0.1:8000
```

La documentación interactiva de Swagger está disponible en:

```text
http://127.0.0.1:8000/docs
```

---

## 11. Endpoints

### `GET /`

Verifica que la API se encuentra activa.

Respuesta:

```json
{
  "message": "Industrial Alarm API",
  "status": "running"
}
```

---

### `GET /alarms`

Consulta las alarmas almacenadas.

Permite filtrar por:

- Fecha inicial.
- Fecha final.
- Severidad.
- Tag.
- Estado.
- Paginación.

Parámetros:

```text
start_time
end_time
severity
tag_name
status
limit
offset
```

Ejemplo:

```text
GET /alarms?severity=CRITICAL&tag_name=PT-101&limit=100
```

También se pueden combinar filtros:

```text
GET /alarms?start_time=2026-01-01T00:00:00&end_time=2026-12-01T23:59:59&severity=CRITICAL&tag_name=PT-101&limit=100
```

La respuesta incluye:

- Cantidad total de registros que cumplen los filtros.
- Cantidad retornada.
- Límite utilizado.
- Offset.
- Datos de las alarmas.

---

### `GET /alarms/{alarm_id}`

Consulta una alarma específica mediante su identificador.

Ejemplo:

```text
GET /alarms/23496
```

Respuesta de ejemplo:

```json
{
  "id": 177,
  "timestamp": "2026-09-01 16:33:25",
  "tag_name": "PT-101",
  "alarm_type": "HIGH_PRESSURE",
  "severity": "CRITICAL",
  "value": "9.59",
  "status": "ACTIVE"
}
```

Si el identificador no existe, la API devuelve:

```text
HTTP 404
```

---

### `GET /alarms/summary/top-tags`

Obtiene los tags con mayor cantidad de eventos.

Ejemplo:

```text
GET /alarms/summary/top-tags
```

Resultado validado:

```json
{
  "count": 8,
  "data": [
    {
      "tag_name": "LT-101",
      "alarm_count": 1725
    },
    {
      "tag_name": "PT-101",
      "alarm_count": 1715
    }
  ]
}
```

El endpoint permite definir la cantidad máxima de tags:

```text
GET /alarms/summary/top-tags?limit=5
```

---

## 12. Validación y manejo de errores

La API implementa validaciones para evitar consultas incorrectas.

### Rango de fechas

No se permite que la fecha inicial sea posterior a la fecha final.

Ejemplo:

```text
start_time > end_time
```

produce:

```text
HTTP 400
```

con un mensaje indicando el problema.

### Severidad

Los valores permitidos son:

```text
LOW
MEDIUM
HIGH
CRITICAL
```

Los valores enviados en minúsculas son normalizados a mayúsculas.

### Estado

Los estados permitidos son:

```text
ACTIVE
ACKNOWLEDGED
CLEARED
```

También se normalizan a mayúsculas.

### Paginación

El parámetro `limit` acepta:

```text
1 - 1000
```

mientras que `offset` debe ser mayor o igual a cero.

Esto evita solicitudes excesivamente grandes o valores inválidos.

---

## 13. Pruebas realizadas

Durante la validación de la solución se realizaron pruebas de:

### Consulta filtrada

Se verificó una consulta utilizando:

```text
severity = CRITICAL
```

El resultado obtenido fue:

```text
214 registros
```

### Consulta por ID

Se verificó:

```text
GET /alarms/23496
```

obteniendo correctamente el registro correspondiente.

### Agregación

Se verificó:

```text
GET /alarms/summary/top-tags
```

y la suma de los eventos de los tags correspondió a:

```text
7.809
```

### Filtro por severidad

Se verificó:

```text
severity = CRITICAL
```

obteniendo:

```text
214 registros
```

### Filtro combinado

Se verificó:

```text
severity = CRITICAL
status = ACTIVE
```

obteniendo:

```text
106 registros
```

### Validación de fechas

Se probó un rango donde la fecha inicial era posterior a la final.

Resultado:

```text
HTTP 400
```

### Validación de estado

Se probó un estado no permitido.

Resultado:

```text
HTTP 400
```

### Consulta sin filtros

Se verificó que la API devuelve:

```text
Total: 7.809
```

con paginación de 100 registros por defecto.

---

## 14. Decisiones técnicas

### Uso de Pandas

Pandas fue utilizado para facilitar:

- Lectura del CSV.
- Conversión de fechas.
- Normalización de strings.
- Tratamiento de valores nulos.
- Validación de datos.
- Generación de reportes.
- Exportación de los datasets resultantes.

### Uso de SQLite

SQLite fue seleccionado como solución relacional para mantener el proyecto autocontenido y fácil de ejecutar.

No requiere:

- Servidor de base de datos.
- Configuración de credenciales.
- Instalación de servicios adicionales.

Para un entorno industrial productivo con múltiples usuarios y grandes volúmenes de información, se recomienda migrar posteriormente a un motor como PostgreSQL o SQL Server.

### Uso de FastAPI

FastAPI fue seleccionado por:

- Validación automática de parámetros.
- Documentación OpenAPI/Swagger.
- Buen rendimiento.
- Facilidad de desarrollo.
- Integración sencilla con Python.

### Separación de responsabilidades

El proyecto separa las principales responsabilidades:

```text
generate_data.py
    ↓
Generación de datos

clean_data.py
    ↓
Limpieza y normalización

load_database.py
    ↓
Persistencia

api/database.py
    ↓
Conexión a la base de datos

api/main.py
    ↓
API REST
```

Esto facilita el mantenimiento y permite modificar una etapa sin afectar directamente las demás.

---

## 15. Supuestos del dataset

Para representar un escenario industrial se utilizaron tags y tipos de alarma representativos de instrumentación y equipos de proceso.

Ejemplos:

```text
PT-101 → Presión
TT-101 → Temperatura
FT-101 → Flujo
LT-101 → Nivel
M-101  → Motor
V-101  → Válvula
P-101  → Bomba
P-102  → Bomba
```

Los datos fueron generados artificialmente y no representan mediciones provenientes de una instalación industrial real.

La semilla utilizada durante la generación es:

```text
42
```

Esto permite reproducir el dataset bajo las mismas condiciones.

---

## 16. Reproducir el proyecto desde cero

Una ejecución completa puede realizarse siguiendo estos pasos.

### Paso 1 — Instalar dependencias

```powershell
uv pip install -r requirements.txt --python .venv\Scripts\python.exe
```

### Paso 2 — Generar datos

```powershell
& ".\.venv\Scripts\python.exe" generate_data.py
```

### Paso 3 — Limpiar y normalizar

```powershell
& ".\.venv\Scripts\python.exe" clean_data.py
```

### Paso 4 — Crear la base de datos

```powershell
& ".\.venv\Scripts\python.exe" load_database.py
```

### Paso 5 — Ejecutar la API

```powershell
cd "D:\Usuarios\Julio\Documentos\SOAP"
& ".\.venv\Scripts\python.exe" -m uvicorn api.main:app --reload
```

### Paso 6 — Abrir Swagger

Abrir en el navegador:

```text
http://127.0.0.1:8000/docs
```

Desde Swagger se pueden probar los endpoints de consulta y agregación.

---

## 17. Flujo completo de ejecución

```text
1. generate_data.py
        ↓
   alarms_raw.csv
        ↓
2. clean_data.py
        ↓
   ├── alarms_clean.csv
   ├── alarms_rejected.csv
   ├── alarms_duplicates.csv
   └── quality_report.txt
        ↓
3. load_database.py
        ↓
   alarms.db
        ↓
4. FastAPI
        ↓
   Consultas y métricas
```

---

## 18. Posibles mejoras futuras

Para una versión productiva podrían incorporarse:

- Migración de SQLite a PostgreSQL o SQL Server.
- Docker y Docker Compose.
- Autenticación y autorización de usuarios.
- Tests automatizados con Pytest.
- Logging estructurado.
- Monitoreo de la API.
- Procesamiento incremental de nuevos históricos.
- Paginación avanzada.
- Exportación de reportes.
- Frontend para visualización de alarmas.
- Métricas adicionales, como frecuencia de alarmas por hora, día o equipo.
- Análisis de alarmas críticas y tiempos de permanencia en estado activo.
- Índices y estrategias de particionamiento adicionales para grandes volúmenes de datos.

---

## 19. Estado actual del proyecto

La solución implementada actualmente cubre:

- [x] Generación de dataset industrial representativo.
- [x] Introducción controlada de problemas de calidad.
- [x] Limpieza y normalización.
- [x] Separación de registros rechazados.
- [x] Detección y separación de duplicados.
- [x] Reporte de calidad.
- [x] Base de datos relacional SQLite.
- [x] Índices para consultas frecuentes.
- [x] API REST con FastAPI.
- [x] Consulta de alarmas.
- [x] Filtros por rango de fechas.
- [x] Filtro por severidad.
- [x] Filtro por tag.
- [x] Filtro por estado.
- [x] Consulta individual por ID.
- [x] Endpoint de agregación de tags.
- [x] Validación de parámetros.
- [x] Manejo de errores HTTP.
- [x] Paginación.
- [x] Documentación automática mediante Swagger.
- [x] Dependencias declaradas en `requirements.txt`.
- [x] Rutas de archivos independientes de una ruta absoluta específica.

---

## 20. Conclusión

La solución permite transformar un histórico SCADA con problemas de calidad en un conjunto de datos estructurado, validado y disponible para consulta mediante una API REST.

El flujo implementado separa claramente la generación, transformación, persistencia y exposición de los datos, facilitando el mantenimiento y futuras ampliaciones.

La arquitectura propuesta constituye una base funcional para una plataforma de gestión de históricos de alarmas industriales y puede evolucionar posteriormente hacia una arquitectura productiva utilizando un motor de base de datos empresarial, contenedores, autenticación, monitoreo y procesamiento de mayores volúmenes de información.