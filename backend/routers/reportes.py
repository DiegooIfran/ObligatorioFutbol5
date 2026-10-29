from db import get_db_connection

def obtener_tabla_posiciones(id_torneo):
    conn = get_db_connection(user_role="admin")
    cursor = conn.cursor(dictionary=True)

    # Consulta de tabla de posiciones calculada por puntos, diferencia de gol y goles a favor
    query = """
        SELECT 
            e.nombre AS equipo,
            COUNT(p.id_partido) AS PJ,
            SUM(CASE 
                WHEN (p.id_equipo_local = e.id_equipo AND e_loc.goles > e_vis.goles) OR 
                     (p.id_equipo_visitante = e.id_equipo AND e_vis.goles > e_loc.goles) THEN 1 ELSE 0 END) AS PG,
            SUM(CASE WHEN e_loc.goles = e_vis.goles AND p.estado = 'jugado' THEN 1 ELSE 0 END) AS PE,
            SUM(CASE 
                WHEN (p.id_equipo_local = e.id_equipo AND e_loc.goles < e_vis.goles) OR 
                     (p.id_equipo_visitante = e.id_equipo AND e_vis.goles < e_loc.goles) THEN 1 ELSE 0 END) AS PP,
            SUM(CASE WHEN p.id_equipo_local = e.id_equipo THEN COALESCE(e_loc.goles,0) ELSE COALESCE(e_vis.goles,0) END) AS GF,
            SUM(CASE WHEN p.id_equipo_local = e.id_equipo THEN COALESCE(e_vis.goles,0) ELSE COALESCE(e_loc.goles,0) END) AS GC,
            (SUM(CASE WHEN p.id_equipo_local = e.id_equipo THEN COALESCE(e_loc.goles,0) ELSE COALESCE(e_vis.goles,0) END) - 
             SUM(CASE WHEN p.id_equipo_local = e.id_equipo THEN COALESCE(e_vis.goles,0) ELSE COALESCE(e_loc.goles,0) END)) AS DG,
            SUM(CASE 
                WHEN (p.id_equipo_local = e.id_equipo AND e_loc.goles > e_vis.goles) OR 
                     (p.id_equipo_visitante = e.id_equipo AND e_vis.goles > e_loc.goles) THEN 3
                WHEN e_loc.goles = e_vis.goles AND p.estado = 'jugado' THEN 1 ELSE 0 END) AS Puntos
        FROM equipo e
        JOIN partido p ON (e.id_equipo = p.id_equipo_local OR e.id_equipo = p.id_equipo_visitante) AND p.estado = 'jugado'
        LEFT JOIN (
            SELECT id_partido, id_equipo, COUNT(*) as goles 
            FROM gol GROUP BY id_partido, id_equipo
        ) e_loc ON p.id_partido = e_loc.id_partido AND p.id_equipo_local = e_loc.id_equipo
        LEFT JOIN (
            SELECT id_partido, id_equipo, COUNT(*) as goles 
            FROM gol GROUP BY id_partido, id_equipo
        ) e_vis ON p.id_partido = e_vis.id_partido AND p.id_equipo_visitante = e_vis.id_equipo
        WHERE e.id_torneo = %s
        GROUP BY e.id_equipo
        ORDER BY Puntos DESC, DG DESC, GF DESC;
    """
    cursor.execute(query, (id_torneo,))
    posiciones = cursor.fetchall()

    cursor.close()
    conn.close()
    return posiciones


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
