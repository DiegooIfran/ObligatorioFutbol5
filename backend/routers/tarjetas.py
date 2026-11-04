import mysql.connector
from db import get_db_connection


def registrar_tarjeta(id_partido, ci_jugador, minuto, color, user_role="planillero"):
    """
    Registra una tarjeta (amarilla o roja) en un partido.
    Valida:
    - Color 'amarilla' o 'roja'.
    - Minuto entre 1 y 60.
    - Que el jugador figure en la planilla del partido.
    - Que el partido esté en estado 'jugado'.
    - Que esté dentro del plazo de 48 horas posteriores al partido.
    (El trigger trg_auto_sancion_tarjeta genera la sanción automática si corresponde).
    """
    if color not in ("amarilla", "roja"):
        return {"error": "Color de tarjeta no válido. Debe ser 'amarilla' o 'roja'."}

    if not (1 <= int(minuto) <= 60):
        return {"error": "El minuto de la tarjeta debe estar comprendido entre 1 y 60."}

    conn = get_db_connection(user_role=user_role)
    if not conn:
        return {"error": "No se pudo conectar a la base de datos"}

    cursor = conn.cursor(dictionary=True)
    try:
        # Validar jugador en planilla
        cursor.execute(
            "SELECT * FROM planilla_partido WHERE id_partido = %s AND ci_jugador = %s",
            (id_partido, ci_jugador)
        )
        if not cursor.fetchone():
            return {"error": "El jugador no figura en la planilla de este partido."}

        # Validar partido jugado
        cursor.execute("SELECT estado FROM partido WHERE id_partido = %s", (id_partido,))
        partido = cursor.fetchone()
        if not partido or partido["estado"] != "jugado":
            return {"error": "Solo se pueden registrar tarjetas en partidos con estado 'jugado'."}

        sql_insert = "INSERT INTO tarjeta (id_partido, ci_jugador, minuto, color) VALUES (%s, %s, %s, %s)"
        cursor.execute(sql_insert, (id_partido, ci_jugador, minuto, color))
        conn.commit()

        return {"exito": True, "mensaje": f"Tarjeta {color} registrada exitosamente.", "id_tarjeta": cursor.lastrowid}
    except mysql.connector.Error as err:
        return {"error": f"Error SQL: {err}"}
    finally:
        cursor.close()
        conn.close()


def modificar_tarjeta(id_tarjeta, nuevo_minuto, user_role="planillero"):
    """
    Modifica el minuto de una tarjeta registrada.
    Nota: Por regla de negocio (trg_tarjeta_upd), no se puede cambiar el partido, jugador ni color;
    para corregir esos datos debe eliminarse y registrarse nuevamente.
    """
    if not (1 <= int(nuevo_minuto) <= 60):
        return {"error": "El minuto debe estar comprendido entre 1 y 60."}

    conn = get_db_connection(user_role=user_role)
    if not conn:
        return {"error": "No se pudo conectar a la base de datos"}

    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT id_tarjeta FROM tarjeta WHERE id_tarjeta = %s", (id_tarjeta,))
        if not cursor.fetchone():
            return {"error": "La tarjeta no existe."}

        sql_update = "UPDATE tarjeta SET minuto = %s WHERE id_tarjeta = %s"
        cursor.execute(sql_update, (nuevo_minuto, id_tarjeta))
        conn.commit()

        return {"exito": True, "mensaje": "Minuto de tarjeta actualizado correctamente."}
    except mysql.connector.Error as err:
        return {"error": f"Error SQL: {err}"}
    finally:
        cursor.close()
        conn.close()


def eliminar_tarjeta(id_tarjeta, user_role="admin"):
    """
    Elimina una tarjeta registrada (y limpia su sanción automática asociada).
    Sujeto al plazo de 48 horas posteriores al partido.
    """
    conn = get_db_connection(user_role=user_role)
    if not conn:
        return {"error": "No se pudo conectar a la base de datos"}

    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT id_tarjeta FROM tarjeta WHERE id_tarjeta = %s", (id_tarjeta,))
        if not cursor.fetchone():
            return {"error": "La tarjeta no existe."}

        cursor.execute("DELETE FROM tarjeta WHERE id_tarjeta = %s", (id_tarjeta,))
        conn.commit()

        return {"exito": True, "mensaje": "Tarjeta eliminada correctamente."}
    except mysql.connector.Error as err:
        return {"error": f"Error SQL: {err}"}
    finally:
        cursor.close()
        conn.close()


def obtener_tarjetas_partido(id_partido):
    """
    Obtiene las tarjetas registradas en un partido.
    """
    conn = get_db_connection(user_role="admin")
    if not conn:
        return []

    cursor = conn.cursor(dictionary=True)
    try:
        sql = """
            SELECT t.id_tarjeta, t.id_partido, t.ci_jugador, j.nombre, j.apellido,
                   pp.id_equipo, e.nombre as equipo, t.minuto, t.color
            FROM tarjeta t
            JOIN jugador j ON t.ci_jugador = j.ci
            JOIN planilla_partido pp ON t.id_partido = pp.id_partido AND t.ci_jugador = pp.ci_jugador
            JOIN equipo e ON pp.id_equipo = e.id_equipo
            WHERE t.id_partido = %s
            ORDER BY t.minuto ASC
        """
        cursor.execute(sql, (id_partido,))
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()

