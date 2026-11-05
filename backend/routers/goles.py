import mysql.connector
from db import get_db_connection


def registrar_gol(id_partido, ci_jugador, minuto, autogol=False, user_role=None):
    """
    Registra un gol en un partido.
    Valida:
    - Minuto entre 1 y 60.
    - Que el jugador figure en la planilla del partido.
    - Que el partido esté en estado 'jugado'.
    - El plazo de 48 horas y la regla de la roja los controlan los triggers
    trg_gol_plazo_ins y trg_gol_post_roja_ins en la base de datos.
    """
    if not (1 <= int(minuto) <= 60):
        return {"error": "El minuto del gol debe estar comprendido entre 1 y 60."}

    conn = get_db_connection(user_role=user_role)
    if not conn:
        return {"error": "No se pudo conectar a la base de datos"}

    cursor = conn.cursor(dictionary=True)
    try:
        # Verificar que el jugador figure en la planilla
        cursor.execute(
            "SELECT * FROM planilla_partido WHERE id_partido = %s AND ci_jugador = %s",
            (id_partido, ci_jugador)
        )
        if not cursor.fetchone():
            return {"error": "El jugador no figura en la planilla de este partido."}

        # Verificar que el partido esté jugado
        cursor.execute("SELECT estado FROM partido WHERE id_partido = %s", (id_partido,))
        partido = cursor.fetchone()
        if not partido or partido["estado"] != "jugado":
            return {"error": "Solo se pueden registrar goles en partidos con estado 'jugado'."}

        sql_insert = "INSERT INTO gol (id_partido, ci_jugador, minuto, autogol) VALUES (%s, %s, %s, %s)"
        cursor.execute(sql_insert, (id_partido, ci_jugador, minuto, bool(autogol)))
        conn.commit()

        return {"exito": True, "mensaje": "Gol registrado exitosamente.", "id_gol": cursor.lastrowid}
    except mysql.connector.Error as err:
        return {"error": f"Error SQL: {err}"}
    finally:
        cursor.close()
        conn.close()


def modificar_gol(id_gol, nuevo_minuto=None, nuevo_autogol=None, nueva_ci_jugador=None, user_role=None):
    """
    Modifica los datos de un gol (minuto, autogol o jugador asignado de la misma planilla).
    El plazo de 48 horas y la regla de la roja los controlan los triggers
    trg_gol_plazo_upd y trg_gol_post_roja_upd en la base de datos.
    """
    conn = get_db_connection(user_role=user_role)
    if not conn:
        return {"error": "No se pudo conectar a la base de datos"}

    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM gol WHERE id_gol = %s", (id_gol,))
        gol = cursor.fetchone()
        if not gol:
            return {"error": "El gol no existe."}

        minuto_final = nuevo_minuto if nuevo_minuto is not None else gol["minuto"]
        if not (1 <= int(minuto_final) <= 60):
            return {"error": "El minuto del gol debe estar comprendido entre 1 y 60."}

        autogol_final = bool(nuevo_autogol) if nuevo_autogol is not None else gol["autogol"]
        ci_final = nueva_ci_jugador if nueva_ci_jugador is not None else gol["ci_jugador"]

        if nueva_ci_jugador is not None and nueva_ci_jugador != gol["ci_jugador"]:
            cursor.execute(
                "SELECT * FROM planilla_partido WHERE id_partido = %s AND ci_jugador = %s",
                (gol["id_partido"], ci_final)
            )
            if not cursor.fetchone():
                return {"error": "El nuevo jugador indicado no figura en la planilla de este partido."}

        sql_update = "UPDATE gol SET minuto = %s, autogol = %s, ci_jugador = %s WHERE id_gol = %s"
        cursor.execute(sql_update, (minuto_final, autogol_final, ci_final, id_gol))
        conn.commit()

        return {"exito": True, "mensaje": "Gol actualizado correctamente."}
    except mysql.connector.Error as err:
        return {"error": f"Error SQL: {err}"}
    finally:
        cursor.close()
        conn.close()


def eliminar_gol(id_gol, user_role=None):
    """
    Elimina un gol registrado.
    El plazo de 48 horas lo controla el trigger trg_gol_plazo_del en la base de datos.
    """
    conn = get_db_connection(user_role=user_role)
    if not conn:
        return {"error": "No se pudo conectar a la base de datos"}

    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT id_gol FROM gol WHERE id_gol = %s", (id_gol,))
        if not cursor.fetchone():
            return {"error": "El gol no existe."}

        cursor.execute("DELETE FROM gol WHERE id_gol = %s", (id_gol,))
        conn.commit()
        return {"exito": True, "mensaje": "Gol eliminado correctamente."}
    except mysql.connector.Error as err:
        return {"error": f"Error SQL: {err}"}
    finally:
        cursor.close()
        conn.close()


def obtener_goles_partido(id_partido, user_role=None):
    """
    Obtiene todos los goles anotados en un partido.
    """
    conn = get_db_connection(user_role=user_role)
    if not conn:
        return []

    cursor = conn.cursor(dictionary=True)
    try:
        sql = """
            SELECT g.id_gol, g.id_partido, g.ci_jugador, j.nombre, j.apellido,
                   pp.id_equipo, e.nombre as equipo, g.minuto, g.autogol
            FROM gol g
            JOIN jugador j ON g.ci_jugador = j.ci
            JOIN planilla_partido pp ON g.id_partido = pp.id_partido AND g.ci_jugador = pp.ci_jugador
            JOIN equipo e ON pp.id_equipo = e.id_equipo
            WHERE g.id_partido = %s
            ORDER BY g.minuto ASC
        """
        cursor.execute(sql, (id_partido,))
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()
