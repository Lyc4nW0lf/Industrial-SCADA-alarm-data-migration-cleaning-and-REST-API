from datetime import datetime
from typing import Optional

from fastapi import FastAPI, HTTPException, Query

from api.database import get_connection


app = FastAPI(
    title="Industrial Alarm API",
    description="API para consulta y análisis de alarmas industriales",
    version="1.0.0",
)


@app.get("/")
def root():
    return {
        "message": "Industrial Alarm API",
        "status": "running"
    }


@app.get("/alarms")
def get_alarms(
    start_time: Optional[datetime] = Query(
        default=None,
        description="Fecha/hora inicial del rango"
    ),
    end_time: Optional[datetime] = Query(
        default=None,
        description="Fecha/hora final del rango"
    ),
    severity: Optional[str] = Query(
        default=None,
        description="Nivel de severidad"
    ),
    tag_name: Optional[str] = Query(
        default=None,
        description="Tag de la alarma"
    ),
    status: Optional[str] = Query(
        default=None,
        description="Estado de la alarma"
    ),
    limit: int = Query(
        default=100,
        ge=1,
        le=1000,
        description="Cantidad máxima de registros"
    ),
    offset: int = Query(
        default=0,
        ge=0,
        description="Cantidad de registros a saltar"
    )
):
    # ---------------------------------------------------------
    # VALIDACIÓN DE FECHAS
    # ---------------------------------------------------------

    if start_time is not None and end_time is not None:
        if start_time > end_time:
            raise HTTPException(
                status_code=400,
                detail="start_time no puede ser posterior a end_time"
            )

    # ---------------------------------------------------------
    # VALIDACIÓN DE SEVERIDAD
    # ---------------------------------------------------------

    if severity is not None:
        valid_severities = {
            "LOW",
            "MEDIUM",
            "HIGH",
            "CRITICAL"
        }

        severity = severity.upper()

        if severity not in valid_severities:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Severidad inválida. "
                    "Valores permitidos: LOW, MEDIUM, HIGH, CRITICAL"
                )
            )

    # ---------------------------------------------------------
    # VALIDACIÓN DE ESTADO
    # ---------------------------------------------------------

    if status is not None:
        valid_statuses = {
            "ACTIVE",
            "ACKNOWLEDGED",
            "CLEARED"
        }

        status = status.upper()

        if status not in valid_statuses:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Estado inválido. "
                    "Valores permitidos: ACTIVE, ACKNOWLEDGED, CLEARED"
                )
            )

    # ---------------------------------------------------------
    # CONSTRUCCIÓN DE LA CONSULTA
    # ---------------------------------------------------------

    base_query = """
        FROM alarms
        WHERE 1 = 1
    """

    parameters = []

    if start_time is not None:
        base_query += " AND timestamp >= ?"
        parameters.append(
            start_time.strftime("%Y-%m-%d %H:%M:%S")
        )

    if end_time is not None:
        base_query += " AND timestamp <= ?"
        parameters.append(
            end_time.strftime("%Y-%m-%d %H:%M:%S")
        )

    if severity is not None:
        base_query += " AND severity = ?"
        parameters.append(severity)

    if tag_name is not None:
        base_query += " AND tag_name = ?"
        parameters.append(tag_name.upper())

    if status is not None:
        base_query += " AND status = ?"
        parameters.append(status)

    connection = get_connection()

    try:
        # -----------------------------------------------------
        # TOTAL DE REGISTROS QUE CUMPLEN LOS FILTROS
        # -----------------------------------------------------

        count_query = "SELECT COUNT(*) " + base_query

        total = connection.execute(
            count_query,
            parameters
        ).fetchone()[0]

        # -----------------------------------------------------
        # CONSULTA DE DATOS
        # -----------------------------------------------------

        query = """
            SELECT
                id,
                timestamp,
                tag_name,
                alarm_type,
                severity,
                value,
                status
        """ + base_query + """
            ORDER BY timestamp ASC
            LIMIT ? OFFSET ?
        """

        data_parameters = parameters + [limit, offset]

        rows = connection.execute(
            query,
            data_parameters
        ).fetchall()

        alarms = [dict(row) for row in rows]

        return {
            "total": total,
            "count": len(alarms),
            "limit": limit,
            "offset": offset,
            "data": alarms
        }

    finally:
        connection.close()


@app.get("/alarms/{alarm_id}")
def get_alarm(alarm_id: int):
    connection = get_connection()

    try:
        cursor = connection.execute(
            """
            SELECT
                id,
                timestamp,
                tag_name,
                alarm_type,
                severity,
                value,
                status
            FROM alarms
            WHERE id = ?
            """,
            (alarm_id,)
        )

        row = cursor.fetchone()

        if row is None:
            raise HTTPException(
                status_code=404,
                detail=f"No se encontró la alarma con ID {alarm_id}"
            )

        return dict(row)

    finally:
        connection.close()


@app.get("/alarms/summary/top-tags")
def top_tags(
    limit: int = Query(
        default=10,
        ge=1,
        le=100,
        description="Cantidad de tags a retornar"
    )
):
    connection = get_connection()

    try:
        cursor = connection.execute(
            """
            SELECT
                tag_name,
                COUNT(*) AS alarm_count
            FROM alarms
            GROUP BY tag_name
            ORDER BY alarm_count DESC
            LIMIT ?
            """,
            (limit,)
        )

        rows = cursor.fetchall()

        return {
            "count": len(rows),
            "data": [dict(row) for row in rows]
        }

    finally:
        connection.close()