import mysql.connector
from db import get_db_connection


def inscribir_jugador_equipo(id_equipo, ci_jugador, id_torneo, numero_camiseta):
    """
    Inscribe un jugador al plantel de un equipo en un torneo.
    Valida:
    - Torneo en etapa de 'inscripción'.
    - Jugador de la misma facultad que el equipo.
    - Máximo 2 docentes o funcionarios en el plantel.
    - Plantel no supere los 10 jugadores.
    - Dorsal entre 1 y 99 no repetido en el equipo.
    """
    if not (1 <= int(numero_camiseta) <= 99):
        return {"error": "El número de camiseta debe estar entre 1 y 99."}

    conn = get_db_connection(user_role="admin")
    if not conn:
        return {"error": "No se pudo conectar a la base de datos"}

    cursor = conn.cursor(dictionary=True)
    try:
        # Validar estado del torneo
        cursor.execute("SELECT estado FROM torneo WHERE id_torneo = %s", (id_torneo,))
        torneo = cursor.fetchone()
        if not torneo:
            return {"error": "El torneo no existe."}
        if torneo["estado"] != "inscripción":
            return {"error": "Solo se pueden inscribir jugadores mientras el torneo esté en etapa de inscripción."}

        # Validar equipo y facultad
        cursor.execute("SELECT id_facultad, id_torneo FROM equipo WHERE id_equipo = %s", (id_equipo,))
        equipo = cursor.fetchone()
        if not equipo:
            return {"error": "El equipo no existe."}
        if equipo["id_torneo"] != id_torneo:
            return {"error": "El equipo no pertenece al torneo especificado."}

        # Validar jugador y facultad
        cursor.execute("SELECT id_facultad, tipo FROM jugador WHERE ci = %s", (ci_jugador,))
        jugador = cursor.fetchone()
        if not jugador:
            return {"error": "El jugador no existe."}
        if jugador["id_facultad"] != equipo["id_facultad"]:
            return {"error": "El jugador debe pertenecer a la misma facultad que el equipo."}

        # Validar si ya está inscripto en este torneo (en cualquier equipo)
        cursor.execute(
            "SELECT id_equipo FROM equipo_jugador_torneo WHERE ci_jugador = %s AND id_torneo = %s",
            (ci_jugador, id_torneo)
        )
        if cursor.fetchone():
            return {"error": "El jugador ya se encuentra inscripto en un equipo para esta edición del torneo."}

        # Validar camiseta no ocupada en el equipo
        cursor.execute(
            "SELECT ci_jugador FROM equipo_jugador_torneo WHERE id_equipo = %s AND numero_camiseta = %s",
            (id_equipo, numero_camiseta)
        )
        if cursor.fetchone():
            return {"error": f"La camiseta #{numero_camiseta} ya está asignada a otro jugador del equipo."}

        # Validar cupo de docentes/funcionarios (máx 2)
        if jugador["tipo"] in ("docente", "funcionario"):
            cursor.execute("""
                SELECT COUNT(*) AS total
                FROM equipo_jugador_torneo ej
                JOIN jugador j ON ej.ci_jugador = j.ci
                WHERE ej.id_equipo = %s AND ej.id_torneo = %s AND j.tipo IN ('docente', 'funcionario')
            """, (id_equipo, id_torneo))
            if cursor.fetchone()["total"] >= 2:
                return {"error": "El plantel ya cuenta con el máximo permitido de 2 docentes/funcionarios."}

        # Validar cupo total del plantel (máx 10)
        cursor.execute(
            "SELECT COUNT(*) AS total FROM equipo_jugador_torneo WHERE id_equipo = %s AND id_torneo = %s",
            (id_equipo, id_torneo)
        )
        if cursor.fetchone()["total"] >= 10:
            return {"error": "El plantel ya alcanzó el límite máximo de 10 jugadores."}

        sql_insert = """
            INSERT INTO equipo_jugador_torneo (id_equipo, ci_jugador, id_torneo, numero_camiseta)
            VALUES (%s, %s, %s, %s)
        """
        cursor.execute(sql_insert, (id_equipo, ci_jugador, id_torneo, numero_camiseta))
        conn.commit()

        return {"exito": True, "mensaje": "Jugador inscripto correctamente en el plantel."}
    except mysql.connector.Error as err:
        return {"error": f"Error SQL: {err}"}
    finally:
        cursor.close()
        conn.close()


def modificar_camiseta_jugador(id_equipo, ci_jugador, id_torneo, nuevo_numero_camiseta):
    """
    Modifica el dorsal/número de camiseta de un jugador en un equipo.
    """
    if not (1 <= int(nuevo_numero_camiseta) <= 99):
        return {"error": "El número de camiseta debe estar entre 1 y 99."}

    conn = get_db_connection(user_role="admin")
    if not conn:
        return {"error": "No se pudo conectar a la base de datos"}

    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            "SELECT * FROM equipo_jugador_torneo WHERE id_equipo = %s AND ci_jugador = %s AND id_torneo = %s",
            (id_equipo, ci_jugador, id_torneo)
        )
        if not cursor.fetchone():
            return {"error": "El jugador no figura en el plantel de este equipo para el torneo."}

        # Verificar que la nueva camiseta no esté ocupada
        cursor.execute(
            "SELECT ci_jugador FROM equipo_jugador_torneo WHERE id_equipo = %s AND numero_camiseta = %s AND ci_jugador != %s",
            (id_equipo, nuevo_numero_camiseta, ci_jugador)
        )
        if cursor.fetchone():
            return {"error": f"La camiseta #{nuevo_numero_camiseta} ya está ocupada por otro jugador."}

        sql_update = """
            UPDATE equipo_jugador_torneo
            SET numero_camiseta = %s
            WHERE id_equipo = %s AND ci_jugador = %s AND id_torneo = %s
        """
        cursor.execute(sql_update, (nuevo_numero_camiseta, id_equipo, ci_jugador, id_torneo))
        conn.commit()

        return {"exito": True, "mensaje": "Número de camiseta actualizado correctamente."}
    except mysql.connector.Error as err:
        return {"error": f"Error SQL: {err}"}
    finally:
        cursor.close()
        conn.close()


def eliminar_jugador_equipo(id_equipo, ci_jugador, id_torneo):
    """
    Elimina a un jugador del plantel de un equipo.
    Valida que no sea el capitán del equipo ni tenga planillas disputadas.
    """
    conn = get_db_connection(user_role="admin")
    if not conn:
        return {"error": "No se pudo conectar a la base de datos"}

    cursor = conn.cursor(dictionary=True)
    try:
        # Verificar estado del torneo
        cursor.execute("SELECT estado FROM torneo WHERE id_torneo = %s", (id_torneo,))
        torneo = cursor.fetchone()
        if torneo and torneo["estado"] != "inscripción":
            return {"error": "Solo se pueden dar de baja jugadores mientras el torneo esté en etapa de inscripción."}

        # Verificar si es el capitán
        cursor.execute("SELECT ci_capitan FROM equipo WHERE id_equipo = %s", (id_equipo,))
        equipo = cursor.fetchone()
        if equipo and equipo["ci_capitan"] == ci_jugador:
            return {"error": "No se puede eliminar al capitán del plantel. Asigne primero un nuevo capitán al equipo."}

        # Verificar si tiene planillas asociadas
        cursor.execute(
            "SELECT COUNT(*) AS total FROM planilla_partido WHERE id_equipo = %s AND ci_jugador = %s",
            (id_equipo, ci_jugador)
        )
        if cursor.fetchone()["total"] > 0:
            return {"error": "No se puede eliminar el jugador porque tiene planillas de partidos registradas."}

        cursor.execute(
            "DELETE FROM equipo_jugador_torneo WHERE id_equipo = %s AND ci_jugador = %s AND id_torneo = %s",
            (id_equipo, ci_jugador, id_torneo)
        )
        conn.commit()

        return {"exito": True, "mensaje": "Jugador dado de baja del plantel correctamente."}
    except mysql.connector.Error as err:
        return {"error": f"Error SQL: {err}"}
    finally:
        cursor.close()
        conn.close()


def obtener_plantel(id_equipo, id_torneo):
    """
    Obtiene la lista de jugadores inscriptos en el plantel de un equipo para un torneo.
    """
    conn = get_db_connection(user_role="admin")
    if not conn:
        return []

    cursor = conn.cursor(dictionary=True)
    try:
        sql = """
            SELECT ej.ci_jugador, j.nombre, j.apellido, j.tipo, ej.numero_camiseta,
                   (CASE WHEN e.ci_capitan = ej.ci_jugador THEN TRUE ELSE FALSE END) AS es_capitan
            FROM equipo_jugador_torneo ej
            JOIN jugador j ON ej.ci_jugador = j.ci
            JOIN equipo e ON ej.id_equipo = e.id_equipo
            WHERE ej.id_equipo = %s AND ej.id_torneo = %s
            ORDER BY ej.numero_camiseta ASC
        """
        cursor.execute(sql, (id_equipo, id_torneo))
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()

