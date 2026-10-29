from datetime import datetime, timedelta
import mysql.connector
from db import get_db_connection

def programar_partido(id_torneo, numero_fecha, id_local, id_visitante, dia, id_turno, nombre_cancha, id_complejo):
    # Programa un partido validando todas las reglas de negocio en Python + SQL directos.
    conn = get_db_connection(user_role="admin")
    if not conn:
        return {"error": "No se pudo conectar a la base de datos"}

    cursor = conn.cursor(dictionary=True)

    try:
        # Ambos equipos deben tener al menos 5 jugadores en el torneo
        cursor.execute(
            "SELECT COUNT(*) as total FROM equipo_jugador_torneo WHERE id_equipo = %s AND id_torneo = %s",
            (id_local, id_torneo)
        )
        if cursor.fetchone()["total"] < 5:
            return {"error": "El equipo local tiene menos de 5 jugadores inscriptos."}

        cursor.execute(
            "SELECT COUNT(*) as total FROM equipo_jugador_torneo WHERE id_equipo = %s AND id_torneo = %s",
            (id_visitante, id_torneo)
        )
        if cursor.fetchone()["total"] < 5:
            return {"error": "El equipo visitante tiene menos de 5 jugadores inscriptos."}

        # Cancha sin partidos asignados en el mismo día y turno (salvo cancelados)
        sql_cancha = """
            SELECT id_partido FROM partido 
            WHERE dia = %s AND id_turno = %s AND nombre_cancha = %s AND id_complejo = %s 
              AND estado != 'cancelado'
        """
        cursor.execute(sql_cancha, (dia, id_turno, nombre_cancha, id_complejo))
        if cursor.fetchone():
            return {"error": "La cancha ya está reservada para ese día y turno."}

        # Ningún equipo juega más de un partido en la misma fecha del torneo
        sql_fecha = """
            SELECT id_partido FROM partido 
            WHERE id_torneo = %s AND numero_fecha = %s 
              AND (id_equipo_local IN (%s, %s) OR id_equipo_visitante IN (%s, %s))
              AND estado != 'cancelado'
        """
        cursor.execute(sql_fecha, (id_torneo, numero_fecha, id_local, id_visitante, id_local, id_visitante))
        if cursor.fetchone():
            return {"error": "Uno de los equipos ya tiene un partido asignado en esta fecha del torneo."}

        # Inserción del partido programado
        sql_insert = """
            INSERT INTO partido (id_torneo, numero_fecha, id_equipo_local, id_equipo_visitante, dia, id_turno, nombre_cancha, id_complejo, estado)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'programado')
        """
        cursor.execute(sql_insert,
                       (id_torneo, numero_fecha, id_local, id_visitante, dia, id_turno, nombre_cancha, id_complejo))
        conn.commit()

        return {"exito": True, "mensaje": "Partido programado correctamente."}

    except mysql.connector.Error as err:
        return {"error": f"Error SQL: {err}"}
    finally:
        cursor.close()
        conn.close()


def editar_resultado_partido(id_partido, fecha_hora_disputa):
    #Valida la regla de las 48 horas posteriores a la disputa para editar el partido.
    ahora = datetime.now()
    limite_horas = fecha_hora_disputa + timedelta(hours=48)

    if ahora > limite_horas:
        return {"error": "Ha expirado el plazo de 48 horas para modificar o corregir el resultado de este partido."}

    # Actualiza
    return {"exito": True, "mensaje": "Dentro del plazo permitido para corrección."}
