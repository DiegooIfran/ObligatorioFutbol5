import mysql.connector
from db import get_db_connection


def obtener_tabla_posiciones(id_torneo, user_role=None):
    """
    Obtiene la tabla de posiciones filtrada por edición del torneo.
    """
    conn = get_db_connection(user_role=user_role)
    if not conn:
        return []
    cursor = conn.cursor(dictionary=True)
    try:
        query = """
            SELECT nombre               AS equipo,
                   partidos_jugados     AS PJ,
                   partidos_ganados     AS PG,
                   partidos_empatados   AS PE,
                   partidos_perdidos    AS PP,
                   goles_a_favor        AS GF,
                   goles_en_contra      AS GC,
                   diferencia_de_goles  AS DG,
                   puntos               AS Puntos
            FROM tabla_posiciones
            WHERE id_torneo = %s
            ORDER BY puntos DESC, diferencia_de_goles DESC, goles_a_favor DESC
        """
        cursor.execute(query, (id_torneo,))
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()


def obtener_tabla_goleadores(id_torneo, user_role=None):
    """
    Obtiene los goleadores del torneo desde la vista 'tabla_goleadores'.
    """
    conn = get_db_connection(user_role=user_role)
    if not conn:
        return []
    cursor = conn.cursor(dictionary=True)
    try:
        query = """
            SELECT ci, nombre, apellido, equipo, goles
            FROM tabla_goleadores
            WHERE id_torneo = %s
            ORDER BY goles DESC, apellido ASC, nombre ASC
            LIMIT 10
        """
        cursor.execute(query, (id_torneo,))
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()


# Alias para compatibilidad con código existente
obtener_goleadores = obtener_tabla_goleadores


def obtener_tabla_fair_play(id_torneo, user_role=None):
    """
    Obtiene los puntos y estadísticas de Fair Play por equipo en un torneo.
    """
    conn = get_db_connection(user_role=user_role)
    if not conn:
        return []
    cursor = conn.cursor(dictionary=True)
    try:
        query = """
            SELECT id_equipo, equipo, puntos_fair_play
            FROM tabla_fair_play
            WHERE id_torneo = %s
            ORDER BY puntos_fair_play ASC
        """
        cursor.execute(query, (id_torneo,))
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()


def obtener_promedio_goles_fecha(id_torneo, user_role=None):
    """
    Obtiene el promedio de goles por fecha disputada en un torneo.
    """
    conn = get_db_connection(user_role=user_role)
    if not conn:
        return []
    cursor = conn.cursor(dictionary=True)
    try:
        query = """
            SELECT numero_fecha, promedio_goles
            FROM promedio_goles_fecha
            WHERE id_torneo = %s
            ORDER BY numero_fecha ASC
        """
        cursor.execute(query, (id_torneo,))
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()


def obtener_promedio_goles_edicion(user_role=None):
    """
    Obtiene el promedio de goles por edición (general de todos los torneos).
    """
    conn = get_db_connection(user_role=user_role)
    if not conn:
        return []
    cursor = conn.cursor(dictionary=True)
    try:
        query = """
            SELECT id_torneo, torneo, promedio_goles
            FROM promedio_goles_edicion
            ORDER BY id_torneo ASC
        """
        cursor.execute(query)
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()


def obtener_canchas_turnos(user_role=None):
    """
    Obtiene la cantidad de usos de canchas y turnos (general de todos los torneos).
    """
    conn = get_db_connection(user_role=user_role)
    if not conn:
        return []
    cursor = conn.cursor(dictionary=True)
    try:
        query = """
            SELECT id_complejo, complejo, nombre_cancha, id_turno, hora_inicio, hora_fin, cantidad_usos
            FROM canchas_turnos
            ORDER BY cantidad_usos DESC
        """
        cursor.execute(query)
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()


def obtener_jugadores_facultad(id_torneo, user_role=None):
    """
    Obtiene la distribución de jugadores por facultad y grado para un torneo.
    """
    conn = get_db_connection(user_role=user_role)
    if not conn:
        return []
    cursor = conn.cursor(dictionary=True)
    try:
        query = """
            SELECT id_facultad, facultad, cantidad_de_jugadores,
                   jugadores_grado, jugadores_postgrado, jugadores_docentes, jugadores_funcionarios
            FROM jugadores_facultad
            WHERE id_torneo = %s
            ORDER BY cantidad_de_jugadores DESC
        """
        cursor.execute(query, (id_torneo,))
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()


def obtener_sin_figurar(id_torneo, user_role=None):
    """
    Obtiene los jugadores inscriptos que no figuraron en ninguna planilla del torneo.
    """
    conn = get_db_connection(user_role=user_role)
    if not conn:
        return []
    cursor = conn.cursor(dictionary=True)
    try:
        query = """
            SELECT ci, nombre, apellido
            FROM sin_figurar
            WHERE id_torneo = %s
            ORDER BY apellido ASC, nombre ASC
        """
        cursor.execute(query, (id_torneo,))
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()


# Alias descriptivo
obtener_jugadores_sin_figurar = obtener_sin_figurar


def obtener_sanciones_equipo(id_torneo, user_role=None):
    """
    Obtiene el resumen de sanciones por equipo y por motivo en un torneo.
    """
    conn = get_db_connection(user_role=user_role)
    if not conn:
        return []
    cursor = conn.cursor(dictionary=True)
    try:
        query = """
            SELECT id_equipo, equipo, sanciones_totales, rojas,
                   acumulación_de_amarillas, disciplinarias
            FROM sanciones_equipo
            WHERE id_torneo = %s
            ORDER BY sanciones_totales DESC
        """
        cursor.execute(query, (id_torneo,))
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()


def obtener_porcentaje_jugados(id_torneo, user_role=None):
    """
    Obtiene el porcentaje de partidos jugados vs cancelados/postergados de un torneo.
    """
    conn = get_db_connection(user_role=user_role)
    if not conn:
        return []
    cursor = conn.cursor(dictionary=True)
    try:
        query = """
            SELECT id_torneo, pct_jugados, pct_cancelados_o_postergados
            FROM porcentaje_jugados
            WHERE id_torneo = %s
        """
        cursor.execute(query, (id_torneo,))
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()


def obtener_resultados(id_torneo=None, user_role=None):
    """
    Obtiene el detalle de resultados de los partidos disputados, filtrando por torneo si se especifica.
    """
    conn = get_db_connection(user_role=user_role)
    if not conn:
        return []
    cursor = conn.cursor(dictionary=True)
    try:
        if id_torneo is not None:
            query = """
                SELECT id_partido, numero_fecha,
                       id_equipo_local, equipo_local,
                       id_equipo_visitante, equipo_visitante,
                       goles_e_local, goles_e_visitante
                FROM resultados
                WHERE id_torneo = %s
                ORDER BY numero_fecha ASC, id_partido ASC
            """
            cursor.execute(query, (id_torneo,))
        else:
            query = """
                SELECT id_partido, numero_fecha,
                       id_equipo_local, equipo_local,
                       id_equipo_visitante, equipo_visitante,
                       goles_e_local, goles_e_visitante
                FROM resultados
                ORDER BY numero_fecha ASC, id_partido ASC
            """
            cursor.execute(query)
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()


def obtener_tarjetas_jugador(user_role=None):
    """
    Obtiene el consolidado de sanciones y tarjetas por jugador (general de todos los torneos).
    """
    conn = get_db_connection(user_role=user_role)
    if not conn:
        return []
    cursor = conn.cursor(dictionary=True)
    try:
        query = """
            SELECT ci, nombre, apellido,
                   sanciones_totales, acumulacion_de_amarillas,
                   sanciones_disciplinarias, tarjetas_amarillas, tarjetas_rojas
            FROM tarjetas_jugador
            ORDER BY sanciones_totales DESC, tarjetas_rojas DESC, tarjetas_amarillas DESC
        """
        cursor.execute(query)
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()


def obtener_tarjetas_jugador_torneo(id_torneo, user_role=None):
    """
    Obtiene el consolidado de sanciones y tarjetas por jugador en un torneo específico.
    """
    conn = get_db_connection(user_role=user_role)
    if not conn:
        return []
    cursor = conn.cursor(dictionary=True)
    try:
        query = """
            SELECT ci, nombre, apellido,
                   sanciones_totales, acumulacion_de_amarillas,
                   sanciones_disciplinarias, tarjetas_amarillas, tarjetas_rojas
            FROM tarjetas_jugador_torneo
            WHERE id_torneo = %s
            ORDER BY sanciones_totales DESC, tarjetas_rojas DESC, tarjetas_amarillas DESC
        """
        cursor.execute(query, (id_torneo,))
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()


def obtener_porcentaje_participacion(id_torneo, user_role=None):
    """
    Obtiene el porcentaje de participación de cada jugador según los partidos de su equipo en el torneo.
    """
    conn = get_db_connection(user_role=user_role)
    if not conn:
        return []
    cursor = conn.cursor(dictionary=True)
    try:
        query = """
            SELECT ci, nombre, apellido, id_equipo, equipo, porcentaje_participaciones
            FROM porcentaje_participacion
            WHERE id_torneo = %s
            ORDER BY porcentaje_participaciones DESC
        """
        cursor.execute(query, (id_torneo,))
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()
