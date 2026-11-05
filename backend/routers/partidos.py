from datetime import datetime, timedelta, time, date
import mysql.connector
from db import get_db_connection

def programar_partido(id_torneo, numero_fecha, id_local, id_visitante, dia, id_turno, nombre_cancha, id_complejo, user_role=None):
    # Programa un partido validando todas las reglas de negocio en Python + SQL directos.
    conn = get_db_connection(user_role=user_role)
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
    # Valida la regla de las 48 horas posteriores a la disputa para editar el partido.
    ahora = datetime.now()
    limite_horas = fecha_hora_disputa + timedelta(hours=48)

    if ahora > limite_horas:
        return {"error": "Ha expirado el plazo de 48 horas para modificar o corregir el resultado de este partido."}

    # Actualiza
    return {"exito": True, "mensaje": "Dentro del plazo permitido para corrección."}


def postergar_partido(id_partido, nueva_fecha, nueva_cancha, nuevo_id_turno=None, nuevo_id_complejo=None, user_role=None):
    """
    Pospone un partido actualizando su fecha y cancha (y opcionalmente turno y complejo).
    Cambia el estado del partido a 'postergado'.
    """
    conn = get_db_connection(user_role=user_role)
    if not conn:
        return {"error": "No se pudo conectar a la base de datos"}

    # Permite flexibilidad si se pasan argumentos en orden (id_partido, nueva_fecha, nuevo_id_turno, nueva_cancha)
    if isinstance(nueva_cancha, int) and (nuevo_id_turno is None or isinstance(nuevo_id_turno, str)):
        nuevo_id_turno, nueva_cancha = nueva_cancha, nuevo_id_turno

    cursor = conn.cursor(dictionary=True)
    try:
        # Obtener los datos actuales del partido
        cursor.execute("SELECT * FROM partido WHERE id_partido = %s", (id_partido,))
        partido = cursor.fetchone()
        if not partido:
            return {"error": "El partido no existe."}

        if partido["estado"] == "cancelado":
            return {"error": "No se puede postergar un partido que ha sido cancelado."}

        if partido["estado"] == "jugado":
            return {"error": "No se puede postergar un partido que ya ha sido jugado."}

        # Verificar si ya tiene planilla cargada
        cursor.execute("SELECT COUNT(*) as total FROM planilla_partido WHERE id_partido = %s", (id_partido,))
        if cursor.fetchone()["total"] > 0:
            return {"error": "El partido tiene planilla cargada y no se puede modificar."}

        # Si no se especifican turno o complejo, conservar los que ya tenía asignados
        turno_final = nuevo_id_turno if nuevo_id_turno is not None else partido["id_turno"]
        complejo_final = nuevo_id_complejo if nuevo_id_complejo is not None else partido["id_complejo"]

        # Validar fechas dentro del rango del torneo
        cursor.execute("SELECT fecha_inicio, fecha_fin FROM torneo WHERE id_torneo = %s", (partido["id_torneo"],))
        torneo = cursor.fetchone()
        if torneo:
            fecha_val = datetime.strptime(nueva_fecha, "%Y-%m-%d").date() if isinstance(nueva_fecha, str) else nueva_fecha
            if fecha_val < torneo["fecha_inicio"] or fecha_val > torneo["fecha_fin"]:
                return {"error": "La fecha del partido debe estar entre las fechas de inicio y fin del torneo."}

        # Validar que la cancha esté libre en ese día y turno
        sql_cancha = """
            SELECT id_partido FROM partido 
            WHERE dia = %s AND id_turno = %s AND nombre_cancha = %s AND id_complejo = %s 
              AND id_partido != %s
              AND estado != 'cancelado'
        """
        cursor.execute(sql_cancha, (nueva_fecha, turno_final, nueva_cancha, complejo_final, id_partido))
        if cursor.fetchone():
            return {"error": "La cancha ya está reservada para ese día y turno."}

        # Validar que ninguno de los equipos juegue otro partido en ese mismo día
        sql_mismo_dia = """
            SELECT id_partido FROM partido
            WHERE id_torneo = %s
              AND id_partido != %s
              AND dia = %s
              AND estado != 'cancelado'
              AND (id_equipo_local IN (%s, %s) OR id_equipo_visitante IN (%s, %s))
        """
        cursor.execute(
            sql_mismo_dia,
            (
                partido["id_torneo"],
                id_partido,
                nueva_fecha,
                partido["id_equipo_local"],
                partido["id_equipo_visitante"],
                partido["id_equipo_local"],
                partido["id_equipo_visitante"],
            ),
        )
        if cursor.fetchone():
            return {"error": "Uno de los equipos ya tiene un partido asignado en ese mismo día."}

        # Actualizar partido a postergado con la nueva fecha y cancha
        sql_update = """
            UPDATE partido 
            SET dia = %s, id_turno = %s, nombre_cancha = %s, id_complejo = %s, estado = 'postergado'
            WHERE id_partido = %s
        """
        cursor.execute(sql_update, (nueva_fecha, turno_final, nueva_cancha, complejo_final, id_partido))
        conn.commit()

        return {"exito": True, "mensaje": "Partido postergado y reprogramado correctamente."}

    except mysql.connector.Error as err:
        return {"error": f"Error SQL: {err}"}
    finally:
        cursor.close()
        conn.close()


def marcar_jugado(id_partido, user_role=None):
    """
    Marca un partido como 'jugado'.
    Valida que el partido exista y que ya haya finalizado según su día y hora de turno.
    """
    conn = get_db_connection(user_role=user_role)
    if not conn:
        return {"error": "No se pudo conectar a la base de datos"}

    cursor = conn.cursor(dictionary=True)
    try:
        # Obtener partido y horario de turno
        sql_partido = """
            SELECT p.id_partido, p.dia, p.id_turno, p.estado, t.hora_inicio, t.hora_fin
            FROM partido p
            JOIN turno t ON p.id_turno = t.id_turno
            WHERE p.id_partido = %s
        """
        cursor.execute(sql_partido, (id_partido,))
        partido = cursor.fetchone()
        if not partido:
            return {"error": "El partido no existe."}

        if partido["estado"] == "jugado":
            return {"error": "El partido ya fue marcado como jugado."}

        if partido["estado"] == "cancelado":
            return {"error": "No se puede marcar como jugado un partido cancelado."}

        # Validar que el partido ya haya sucedido
        dia_partido = partido["dia"]
        if isinstance(dia_partido, str):
            dia_partido = datetime.strptime(dia_partido, "%Y-%m-%d").date()

        hora_fin = partido["hora_fin"]
        if isinstance(hora_fin, timedelta):
            dt_fin_partido = datetime.combine(dia_partido, datetime.min.time()) + hora_fin
        elif isinstance(hora_fin, time):
            dt_fin_partido = datetime.combine(dia_partido, hora_fin)
        else:
            t = datetime.strptime(str(hora_fin), "%H:%M:%S").time()
            dt_fin_partido = datetime.combine(dia_partido, t)

        if datetime.now() < dt_fin_partido:
            return {"error": "El partido aún no ha finalizado. Solo se puede marcar como jugado después de que haya sucedido."}

        # Actualizar estado a 'jugado'
        sql_update = "UPDATE partido SET estado = 'jugado' WHERE id_partido = %s"
        cursor.execute(sql_update, (id_partido,))
        conn.commit()

        return {"exito": True, "mensaje": "Partido marcado como jugado correctamente."}

    except mysql.connector.Error as err:
        return {"error": f"Error SQL: {err}"}
    finally:
        cursor.close()
        conn.close()


def cancelar_partido(id_partido, user_role=None):
    """
    Cancela un partido cambiando su estado a 'cancelado'.
    Valida que no esté previamente cancelado ni jugado ni con planilla registrada.
    """
    conn = get_db_connection(user_role=user_role)
    if not conn:
        return {"error": "No se pudo conectar a la base de datos"}

    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT id_partido, estado FROM partido WHERE id_partido = %s", (id_partido,))
        partido = cursor.fetchone()
        if not partido:
            return {"error": "El partido no existe."}

        if partido["estado"] == "cancelado":
            return {"error": "El partido ya se encuentra cancelado."}

        if partido["estado"] == "jugado":
            return {"error": "No se puede cancelar un partido que ya fue jugado."}

        # Validar si tiene planilla cargada
        cursor.execute("SELECT COUNT(*) as total FROM planilla_partido WHERE id_partido = %s", (id_partido,))
        if cursor.fetchone()["total"] > 0:
            return {"error": "No se puede cancelar un partido que ya tiene planilla cargada."}

        # Actualizar estado a 'cancelado'
        sql_update = "UPDATE partido SET estado = 'cancelado' WHERE id_partido = %s"
        cursor.execute(sql_update, (id_partido,))
        conn.commit()

        return {"exito": True, "mensaje": "Partido cancelado correctamente."}

    except mysql.connector.Error as err:
        return {"error": f"Error SQL: {err}"}
    finally:
        cursor.close()
        conn.close()


def eliminar_partido(id_partido, user_role=None):
    """
    Elimina físicamente un partido.
    El trigger trg_partido_del impide eliminar partidos que ya tengan estado 'jugado'.
    """
    conn = get_db_connection(user_role=user_role)
    if not conn:
        return {"error": "No se pudo conectar a la base de datos"}

    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT id_partido, estado FROM partido WHERE id_partido = %s", (id_partido,))
        partido = cursor.fetchone()
        if not partido:
            return {"error": "El partido no existe."}

        if partido["estado"] == "jugado":
            return {"error": "No se puede borrar un partido jugado."}

        cursor.execute("DELETE FROM partido WHERE id_partido = %s", (id_partido,))
        conn.commit()

        return {"exito": True, "mensaje": "Partido eliminado correctamente."}
    except mysql.connector.Error as err:
        return {"error": f"Error SQL: {err}"}
    finally:
        cursor.close()
        conn.close()

def obtener_partidos(id_torneo=None, dia=None, estado=None, user_role=None):
    """
    Lista los partidos con los nombres de los equipos, el horario y la cancha.
    """
    conn = get_db_connection(user_role=user_role)
    if not conn:
        return []

    cursor = conn.cursor(dictionary=True)
    try:
        sql = """
            SELECT p.id_partido, p.id_torneo, p.numero_fecha,
                   p.id_equipo_local, el.nombre AS equipo_local,
                   p.id_equipo_visitante, ev.nombre AS equipo_visitante,
                   p.dia, t.hora_inicio, t.hora_fin,
                   p.nombre_cancha, p.id_complejo, c.nombre AS complejo,
                   p.estado
            FROM partido p
            JOIN equipo el ON p.id_equipo_local = el.id_equipo
            JOIN equipo ev ON p.id_equipo_visitante = ev.id_equipo
            JOIN turno t ON p.id_turno = t.id_turno
            JOIN complejo c ON p.id_complejo = c.id_complejo
            WHERE 1 = 1
        """
        params = []

        # Cada filtro se agrega solo si se pasó, y su valor va siempre con %s
        # estos filtros se appendean al where 1=1, por eso en necesario. Sin el where no se puede usar el and.
        if id_torneo is not None:
            sql += " AND p.id_torneo = %s"
            params.append(id_torneo)
        if dia is not None:
            sql += " AND p.dia = %s"
            params.append(dia)
        if estado is not None:
            sql += " AND p.estado = %s"
            params.append(estado)

        sql += " ORDER BY p.dia, t.hora_inicio, p.id_partido"

        cursor.execute(sql, tuple(params))
        return cursor.fetchall()
    except mysql.connector.Error as err:
        print(f"[ERROR SQL]: {err}")
        return []
    finally:
        cursor.close()
        conn.close()
