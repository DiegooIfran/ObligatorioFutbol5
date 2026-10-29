import mysql.connector
from db import get_db_connection


def registrar_planilla_jugador(id_partido, ci_jugador, id_equipo):
    # Inserta un jugador a la planilla. Utiliza el usuario 'usr_planillero'.

    conn = get_db_connection(user_role="planillero")
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
        return {"error": f"Error en operacion de planillero: {err}"}
    finally:
        cursor.close()
        conn.close()
