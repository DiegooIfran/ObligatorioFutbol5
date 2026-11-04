import mysql.connector
from db import get_db_connection


def registrar_planilla_jugador(id_partido, ci_jugador, id_equipo, user_role=None):
    """
    Inserta un jugador a la planilla.
    """
    conn = get_db_connection(user_role=user_role)
    if not conn:
        return {"error": "No se pudo conectar a la base de datos"}

    cursor = conn.cursor(dictionary=True)

    try:
        # Verificar que el jugador no esté sancionado para la fecha actual del partido
        sql_sancion = """
            SELECT s.id_sancion 
            FROM sancion_jugador s
            JOIN partido p ON p.id_partido = %s
            WHERE s.ci_jugador = %s 
              AND s.id_torneo = p.id_torneo
              AND p.numero_fecha BETWEEN s.numero_fecha_inicio AND (s.numero_fecha_inicio + s.cantidad_fechas - 1)
        """
        cursor.execute(sql_sancion, (id_partido, ci_jugador))
        if cursor.fetchone():
            return {"error": "El jugador se encuentra sancionado y no puede figurar en la planilla."}

        # Registrar en la planilla del partido
        sql_insert = "INSERT INTO planilla_partido (id_partido, ci_jugador, id_equipo) VALUES (%s, %s, %s)"
        cursor.execute(sql_insert, (id_partido, ci_jugador, id_equipo))
        conn.commit()

        return {"exito": True, "mensaje": "Jugador agregado a la planilla con éxito."}

    except mysql.connector.Error as err:
        return {"error": f"Error en operacion de planilla: {err}"}
    finally:
        cursor.close()
        conn.close()


def borrar_planilla_jugador(id_partido, ci_jugador, user_role=None):
    """
    Elimina a un jugador de la planilla de un partido.
    Valida que el jugador figure en la planilla y que no tenga goles ni tarjetas asociadas.
    """
    conn = get_db_connection(user_role=user_role)
    if not conn:
        return {"error": "No se pudo conectar a la base de datos"}

    cursor = conn.cursor(dictionary=True)

    try:
        # 1. Verificar que el jugador figure en la planilla del partido
        cursor.execute(
            "SELECT * FROM planilla_partido WHERE id_partido = %s AND ci_jugador = %s",
            (id_partido, ci_jugador)
        )
        if not cursor.fetchone():
            return {"error": "El jugador no figura en la planilla de este partido."}

        # 2. Verificar que no tenga goles asociados en el partido
        cursor.execute(
            "SELECT COUNT(*) as total FROM gol WHERE id_partido = %s AND ci_jugador = %s",
            (id_partido, ci_jugador)
        )
        cant_goles = cursor.fetchone()["total"]
        if cant_goles > 0:
            return {"error": f"No se puede eliminar de la planilla: el jugador tiene {cant_goles} gol(es) registrado(s) en este partido."}

        # 3. Verificar que no tenga tarjetas asociadas en el partido
        cursor.execute(
            "SELECT COUNT(*) as total FROM tarjeta WHERE id_partido = %s AND ci_jugador = %s",
            (id_partido, ci_jugador)
        )
        cant_tarjetas = cursor.fetchone()["total"]
        if cant_tarjetas > 0:
            return {"error": f"No se puede eliminar de la planilla: el jugador tiene {cant_tarjetas} tarjeta(s) registrada(s) en este partido."}

        # 4. Eliminar el registro de la planilla
        sql_delete = "DELETE FROM planilla_partido WHERE id_partido = %s AND ci_jugador = %s"
        cursor.execute(sql_delete, (id_partido, ci_jugador))
        conn.commit()

        return {"exito": True, "mensaje": "Jugador eliminado de la planilla con éxito."}

    except mysql.connector.Error as err:
        return {"error": f"Error SQL: {err}"}
    finally:
        cursor.close()
        conn.close()


def obtener_planilla_partido(id_partido, user_role=None):
    """
    Obtiene los jugadores que figuran en la planilla de un partido.
    """
    conn = get_db_connection(user_role=user_role)
    if not conn:
        return []

    cursor = conn.cursor(dictionary=True)
    try:
        sql = """
            SELECT pp.id_partido, pp.ci_jugador, j.nombre, j.apellido,
                   pp.id_equipo, e.nombre as equipo, ejt.numero_camiseta
            FROM planilla_partido pp
            JOIN jugador j ON pp.ci_jugador = j.ci
            JOIN equipo e ON pp.id_equipo = e.id_equipo
            JOIN partido p ON pp.id_partido = p.id_partido
            LEFT JOIN equipo_jugador_torneo ejt ON pp.ci_jugador = ejt.ci_jugador AND pp.id_equipo = ejt.id_equipo AND p.id_torneo = ejt.id_torneo
            WHERE pp.id_partido = %s
            ORDER BY pp.id_equipo ASC, ejt.numero_camiseta ASC
        """
        cursor.execute(sql, (id_partido,))
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()
