import sqlite3
from pathlib import Path


# Directorio raíz del proyecto
BASE_DIR = Path(__file__).resolve().parent.parent

# Ruta relativa a la base de datos
DB_FILE = BASE_DIR / "data" / "clean" / "alarms.db"


def get_connection():
    """
    Crea y devuelve una conexión a la base de datos SQLite.
    """
    if not DB_FILE.exists():
        raise FileNotFoundError(
            f"No se encontró la base de datos: {DB_FILE}"
        )

    connection = sqlite3.connect(DB_FILE)
    connection.row_factory = sqlite3.Row

    return connection