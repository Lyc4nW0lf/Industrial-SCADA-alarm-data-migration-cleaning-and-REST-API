import sqlite3
from pathlib import Path
import csv


# ============================================================
# CONFIGURACIÓN
# ============================================================

# Carpeta donde está este script
BASE_DIR = Path(__file__).resolve().parent

# Directorio de datos limpios
CLEAN_DIR = BASE_DIR / "data" / "clean"

# Archivo CSV limpio
CSV_FILE = CLEAN_DIR / "alarms_clean.csv"

# Base de datos SQLite que se creará
DB_FILE = CLEAN_DIR / "alarms.db"

# ============================================================
# VALIDACIÓN DEL ARCHIVO DE ENTRADA
# ============================================================

if not CSV_FILE.exists():
    raise FileNotFoundError(
        f"No se encontró el archivo:\n{CSV_FILE}\n\n"
        "Asegúrate de que alarms_clean.csv esté en la misma carpeta "
        "que load_database.py."
    )


# ============================================================
# CONEXIÓN A SQLITE
# ============================================================

connection = sqlite3.connect(DB_FILE)
cursor = connection.cursor()


# ============================================================
# CREACIÓN DE LA TABLA
# ============================================================

cursor.execute("""
CREATE TABLE IF NOT EXISTS alarms (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    tag_name TEXT NOT NULL,
    alarm_type TEXT NOT NULL,
    severity TEXT NOT NULL,
    value TEXT,
    status TEXT NOT NULL
)
""")


# ============================================================
# LIMPIAR TABLA ANTES DE CARGAR
# ============================================================

# Esto permite ejecutar el script varias veces sin
# duplicar los registros.

cursor.execute("DELETE FROM alarms")


# ============================================================
# CARGA DEL CSV
# ============================================================

records = []

with open(CSV_FILE, "r", encoding="utf-8-sig", newline="") as file:

    reader = csv.DictReader(file)

    expected_columns = {
        "timestamp",
        "tag_name",
        "alarm_type",
        "severity",
        "value",
        "status",
    }

    if not expected_columns.issubset(reader.fieldnames or []):
        raise ValueError(
            "El archivo alarms_clean.csv no contiene las columnas esperadas.\n"
            f"Columnas encontradas: {reader.fieldnames}\n"
            f"Columnas requeridas: {sorted(expected_columns)}"
        )

    for row_number, row in enumerate(reader, start=2):

        timestamp = (row.get("timestamp") or "").strip()
        tag_name = (row.get("tag_name") or "").strip()
        alarm_type = (row.get("alarm_type") or "").strip()
        severity = (row.get("severity") or "").strip()
        value = (row.get("value") or "").strip()
        status = (row.get("status") or "").strip()

        # Validación mínima
        if not timestamp:
            raise ValueError(
                f"timestamp vacío en la fila {row_number}"
            )

        if not tag_name:
            raise ValueError(
                f"tag_name vacío en la fila {row_number}"
            )

        if not alarm_type:
            raise ValueError(
                f"alarm_type vacío en la fila {row_number}"
            )

        if not severity:
            raise ValueError(
                f"severity vacío en la fila {row_number}"
            )

        if not status:
            raise ValueError(
                f"status vacío en la fila {row_number}"
            )

        records.append(
            (
                timestamp,
                tag_name,
                alarm_type,
                severity,
                value if value != "" else None,
                status,
            )
        )


# ============================================================
# INSERTAR REGISTROS
# ============================================================

cursor.executemany("""
INSERT INTO alarms (
    timestamp,
    tag_name,
    alarm_type,
    severity,
    value,
    status
)
VALUES (?, ?, ?, ?, ?, ?)
""", records)


# ============================================================
# ÍNDICES
# ============================================================

cursor.execute("""
CREATE INDEX IF NOT EXISTS idx_alarms_timestamp
ON alarms(timestamp)
""")

cursor.execute("""
CREATE INDEX IF NOT EXISTS idx_alarms_tag
ON alarms(tag_name)
""")

cursor.execute("""
CREATE INDEX IF NOT EXISTS idx_alarms_severity
ON alarms(severity)
""")

cursor.execute("""
CREATE INDEX IF NOT EXISTS idx_alarms_status
ON alarms(status)
""")


# ============================================================
# GUARDAR CAMBIOS
# ============================================================

connection.commit()


# ============================================================
# AUDITORÍA DE LA BASE DE DATOS
# ============================================================

cursor.execute("SELECT COUNT(*) FROM alarms")
total_records = cursor.fetchone()[0]

cursor.execute("""
SELECT MIN(timestamp), MAX(timestamp)
FROM alarms
""")

min_timestamp, max_timestamp = cursor.fetchone()


cursor.execute("""
SELECT severity, COUNT(*)
FROM alarms
GROUP BY severity
ORDER BY severity
""")

severity_distribution = cursor.fetchall()


cursor.execute("""
SELECT status, COUNT(*)
FROM alarms
GROUP BY status
ORDER BY status
""")

status_distribution = cursor.fetchall()


# ============================================================
# CERRAR CONEXIÓN
# ============================================================

connection.close()


# ============================================================
# RESULTADOS
# ============================================================

print("\n" + "=" * 60)
print("BASE DE DATOS CREADA CORRECTAMENTE")
print("=" * 60)

print(f"\nArchivo:")
print(DB_FILE)

print(f"\nRegistros cargados: {total_records}")

print("\nRango temporal:")
print(f"  Desde: {min_timestamp}")
print(f"  Hasta: {max_timestamp}")

print("\nDistribución por severidad:")

for severity, count in severity_distribution:
    print(f"  {severity}: {count}")

print("\nDistribución por estado:")

for status, count in status_distribution:
    print(f"  {status}: {count}")

print("\nÍndices creados:")
print("  - idx_alarms_timestamp")
print("  - idx_alarms_tag")
print("  - idx_alarms_severity")
print("  - idx_alarms_status")

print("\nProceso terminado.")
print("=" * 60)
