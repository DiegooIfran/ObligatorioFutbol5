import mysql.connector
from db import get_db_connection


def crear_sancion(ci_jugador, id_torneo, motivo, numero_fecha_inicio, cantidad_fechas=1, user_role=None):
    """
    Registra una sanción disciplinaria para un jugador en un torneo.
    Motivos válidos: 'roja', 'acumulación de amarillas', 'disciplinaria'.
    """
    motivos_validos = ("roja", "acumulación de amarillas", "disciplinaria")
    if motivo not in motivos_validos:
        return {"error": f"Motivo no válido. Debe ser uno de: {', '.join(motivos_validos)}."}

    if int(numero_fecha_inicio) < 1 or int(cantidad_fechas) < 1:
        return {"error": "El número de fecha de inicio y la cantidad de fechas deben ser mayores o iguales a 1."}

    conn = get_db_connection(user_role=user_role)
    if not conn:
        return {"error": "No se pudo conectar a la base de datos"}

    cursor = conn.cursor(dictionary=True)
    try:
        # Verificar que el jugador esté inscripto en el torneo
        cursor.execute(
            "SELECT ci_jugador FROM equipo_jugador_torneo WHERE ci_jugador = %s AND id_torneo = %s",
            (ci_jugador, id_torneo)
        )
        if not cursor.fetchone():
            return {"error": "El jugador no figura inscripto en ningún equipo de este torneo."}

        sql_insert = """
            INSERT INTO sancion_jugador (ci_jugador, id_torneo, motivo, numero_fecha_inicio, cantidad_fechas)
            VALUES (%s, %s, %s, %s, %s)
        """
        cursor.execute(sql_insert, (ci_jugador, id_torneo, motivo, numero_fecha_inicio, cantidad_fechas))
        conn.commit()

        return {"exito": True, "mensaje": "Sanción registrada correctamente.", "id_sancion": cursor.lastrowid}
    except mysql.connector.Error as err:
        return {"error": f"Error SQL: {err}"}
    finally:
        cursor.close()
        conn.close()


def actualizar_sancion(id_sancion, motivo=None, numero_fecha_inicio=None, cantidad_fechas=None, user_role=None):
    """
    Actualiza el motivo o la duración de una sanción.
    """
    conn = get_db_connection(user_role=user_role)
    if not conn:
        return {"error": "No se pudo conectar a la base de datos"}

    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM sancion_jugador WHERE id_sancion = %s", (id_sancion,))
        sancion = cursor.fetchone()
        if not sancion:
            return {"error": "La sanción no existe."}

        nuevo_motivo = motivo if motivo is not None else sancion["motivo"]
        if nuevo_motivo not in ("roja", "acumulación de amarillas", "disciplinaria"):
            return {"error": "Motivo no válido."}

        nueva_fecha_inicio = numero_fecha_inicio if numero_fecha_inicio is not None else sancion["numero_fecha_inicio"]
        nueva_cantidad = cantidad_fechas if cantidad_fechas is not None else sancion["cantidad_fechas"]

        if int(nueva_fecha_inicio) < 1 or int(nueva_cantidad) < 1:
            return {"error": "Los valores de fechas deben ser mayores o iguales a 1."}

        sql_update = """
            UPDATE sancion_jugador
            SET motivo = %s, numero_fecha_inicio = %s, cantidad_fechas = %s
            WHERE id_sancion = %s
        """
        cursor.execute(sql_update, (nuevo_motivo, nueva_fecha_inicio, nueva_cantidad, id_sancion))
        conn.commit()

        return {"exito": True, "mensaje": "Sanción actualizada correctamente."}
    except mysql.connector.Error as err:
        return {"error": f"Error SQL: {err}"}
    finally:
        cursor.close()
        conn.close()


def eliminar_sancion(id_sancion, user_role=None):
    """
    Elimina una sanción disciplinaria.
    """
    conn = get_db_connection(user_role=user_role)
    if not conn:
        return {"error": "No se pudo conectar a la base de datos"}

    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT id_sancion FROM sancion_jugador WHERE id_sancion = %s", (id_sancion,))
        if not cursor.fetchone():
            return {"error": "La sanción no existe."}

        cursor.execute("DELETE FROM sancion_jugador WHERE id_sancion = %s", (id_sancion,))
        conn.commit()

        return {"exito": True, "mensaje": "Sanción eliminada correctamente."}
    except mysql.connector.Error as err:
        return {"error": f"Error SQL: {err}"}
    finally:
        cursor.close()
        conn.close()


def obtener_sanciones(id_torneo=None, ci_jugador=None, user_role=None):
    """
    Obtiene las sanciones registradas, opcionalmente filtradas por torneo o jugador.
    """
    conn = get_db_connection(user_role=user_role)
    if not conn:
        return []

    cursor = conn.cursor(dictionary=True)
    try:
        condiciones = []
        valores = []

        if id_torneo is not None:
            condiciones.append("s.id_torneo = %s")
            valores.append(id_torneo)
        if ci_jugador is not None:
            condiciones.append("s.ci_jugador = %s")
            valores.append(ci_jugador)

        where_clause = f"WHERE {' AND '.join(condiciones)}" if condiciones else ""

        sql = f"""
            SELECT s.id_sancion, s.ci_jugador, j.nombre, j.apellido,
                   s.id_torneo, s.motivo, s.numero_fecha_inicio, s.cantidad_fechas
            FROM sancion_jugador s
            JOIN jugador j ON s.ci_jugador = j.ci
            {where_clause}
            ORDER BY s.id_torneo DESC, s.numero_fecha_inicio DESC
        """
        cursor.execute(sql, tuple(valores))
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()
