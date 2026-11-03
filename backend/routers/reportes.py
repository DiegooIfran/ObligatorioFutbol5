from db import get_db_connection

def obtener_tabla_posiciones(id_torneo):
    conn = get_db_connection(user_role="admin")
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


def obtener_goleadores(id_torneo):
    conn = get_db_connection(user_role="admin")
    cursor = conn.cursor(dictionary=True)

    query = """
        SELECT j.ci, j.nombre, j.apellido, COUNT(g.id_gol) AS total_goles
        FROM gol g
        JOIN jugador j ON g.ci_jugador = j.ci
        JOIN partido p ON g.id_partido = p.id_partido
        WHERE g.autogol = FALSE AND p.id_torneo = %s
        GROUP BY j.ci
        ORDER BY total_goles DESC
        LIMIT 10;
    """
    cursor.execute(query, (id_torneo,))
    goleadores = cursor.fetchall()

    cursor.close()
    conn.close()
    return goleadores
