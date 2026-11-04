import mysql.connector
from db import get_db_connection


def crear_equipo(nombre, id_torneo, id_facultad, ci_capitan, user_role=None):
    """
    Crea un nuevo equipo en un torneo.
    Valida pertenencia de facultad del capitán, que el torneo esté en inscripción,
    y que el capitán no pertenezca a otro equipo del torneo.
    (El trigger trg_equipo_inscribe_capitan inscribe automáticamente al capitán con camiseta #1).
    """
    conn = get_db_connection(user_role=user_role)
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
            return {"error": "Solo se pueden registrar equipos mientras el torneo esté en etapa de inscripción."}

        # Validar existencia del jugador y facultad
        cursor.execute("SELECT id_facultad FROM jugador WHERE ci = %s", (ci_capitan,))
        jugador = cursor.fetchone()
        if not jugador:
            return {"error": "El jugador indicado como capitán no existe."}
        if jugador["id_facultad"] != id_facultad:
            return {"error": "El capitán debe pertenecer a la misma facultad que representa el equipo."}

        # Validar nombre único en el torneo
        cursor.execute("SELECT id_equipo FROM equipo WHERE nombre = %s AND id_torneo = %s", (nombre, id_torneo))
        if cursor.fetchone():
            return {"error": f"Ya existe un equipo con el nombre '{nombre}' en esta edición del torneo."}

        # Validar que el capitán no esté inscripto en otro equipo del mismo torneo
        cursor.execute(
            "SELECT id_equipo FROM equipo_jugador_torneo WHERE ci_jugador = %s AND id_torneo = %s",
            (ci_capitan, id_torneo)
        )
        if cursor.fetchone():
            return {"error": "El capitán ya pertenece a un equipo inscripto en este torneo."}

        # Inserción (el trigger trg_equipo_inscribe_capitan se encarga de inscribirlo al plantel con dorsal 1)
        sql_insert = """
            INSERT INTO equipo (nombre, id_torneo, id_facultad, ci_capitan)
            VALUES (%s, %s, %s, %s)
        """
        cursor.execute(sql_insert, (nombre, id_torneo, id_facultad, ci_capitan))
        conn.commit()

        return {"exito": True, "mensaje": "Equipo creado e inscripto exitosamente con su capitán.", "id_equipo": cursor.lastrowid}
    except mysql.connector.Error as err:
        return {"error": f"Error SQL: {err}"}
    finally:
        cursor.close()
        conn.close()


def actualizar_equipo(id_equipo, nombre=None, ci_capitan=None, user_role=None):
    """
    Actualiza el nombre del equipo o su capitán.
    Nota: La facultad y el torneo son inmutables por regla de integridad.
    Si se cambia el capitán, este debe pertenecer al plantel del equipo y a la misma facultad.
    """
    conn = get_db_connection(user_role=user_role)
    if not conn:
        return {"error": "No se pudo conectar a la base de datos"}

    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM equipo WHERE id_equipo = %s", (id_equipo,))
        equipo = cursor.fetchone()
        if not equipo:
            return {"error": "El equipo no existe."}

        nuevo_nombre = nombre if nombre is not None else equipo["nombre"]
        nuevo_capitan = ci_capitan if ci_capitan is not None else equipo["ci_capitan"]

        if ci_capitan is not None and ci_capitan != equipo["ci_capitan"]:
            # Verificar que pertenezca a la misma facultad
            cursor.execute("SELECT id_facultad FROM jugador WHERE ci = %s", (nuevo_capitan,))
            jug = cursor.fetchone()
            if not jug or jug["id_facultad"] != equipo["id_facultad"]:
                return {"error": "El nuevo capitán debe pertenecer a la misma facultad del equipo."}

            # Verificar que pertenezca al plantel de este equipo
            cursor.execute(
                "SELECT * FROM equipo_jugador_torneo WHERE id_equipo = %s AND ci_jugador = %s AND id_torneo = %s",
                (id_equipo, nuevo_capitan, equipo["id_torneo"])
            )
            if not cursor.fetchone():
                return {"error": "El nuevo capitán debe figurar previamente en el plantel del equipo."}

        sql_update = "UPDATE equipo SET nombre = %s, ci_capitan = %s WHERE id_equipo = %s"
        cursor.execute(sql_update, (nuevo_nombre, nuevo_capitan, id_equipo))
        conn.commit()

        return {"exito": True, "mensaje": "Equipo actualizado correctamente."}
    except mysql.connector.Error as err:
        return {"error": f"Error SQL: {err}"}
    finally:
        cursor.close()
        conn.close()


def eliminar_equipo(id_equipo, user_role=None):
    """
    Elimina un equipo si no tiene partidos programados o jugados.
    Elimina también las inscripciones de su plantel asociadas.
    """
    conn = get_db_connection(user_role=user_role)
    if not conn:
        return {"error": "No se pudo conectar a la base de datos"}

    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT id_equipo, id_torneo FROM equipo WHERE id_equipo = %s", (id_equipo,))
        equipo = cursor.fetchone()
        if not equipo:
            return {"error": "El equipo no existe."}

        # Validar si tiene partidos asignados
        sql_partidos = """
            SELECT COUNT(*) AS total FROM partido
            WHERE (id_equipo_local = %s OR id_equipo_visitante = %s)
        """
        cursor.execute(sql_partidos, (id_equipo, id_equipo))
        if cursor.fetchone()["total"] > 0:
            return {"error": "No se puede eliminar el equipo porque ya tiene partidos programados o disputados."}

        # Eliminar inscripciones de jugadores
        cursor.execute("DELETE FROM equipo_jugador_torneo WHERE id_equipo = %s", (id_equipo,))
        # Eliminar equipo
        cursor.execute("DELETE FROM equipo WHERE id_equipo = %s", (id_equipo,))
        conn.commit()

        return {"exito": True, "mensaje": "Equipo y su plantel eliminados correctamente."}
    except mysql.connector.Error as err:
        return {"error": f"Error SQL: {err}"}
    finally:
        cursor.close()
        conn.close()


def obtener_equipos(id_torneo=None, user_role=None):
    """
    Obtiene la lista de equipos, opcionalmente filtrada por torneo.
    """
    conn = get_db_connection(user_role=user_role)
    if not conn:
        return []

    cursor = conn.cursor(dictionary=True)
    try:
        if id_torneo is not None:
            cursor.execute("""
                SELECT e.id_equipo, e.nombre, e.id_torneo, e.id_facultad, f.nombre as facultad, e.ci_capitan
                FROM equipo e
                JOIN facultad f ON e.id_facultad = f.id_facultad
                WHERE e.id_torneo = %s
                ORDER BY e.nombre ASC
            """, (id_torneo,))
        else:
            cursor.execute("""
                SELECT e.id_equipo, e.nombre, e.id_torneo, e.id_facultad, f.nombre as facultad, e.ci_capitan
                FROM equipo e
                JOIN facultad f ON e.id_facultad = f.id_facultad
                ORDER BY e.nombre ASC
            """)
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()


def obtener_equipo(id_equipo, user_role=None):
    """
    Obtiene un equipo por su ID.
    """
    conn = get_db_connection(user_role=user_role)
    if not conn:
        return None

    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM equipo WHERE id_equipo = %s", (id_equipo,))
        return cursor.fetchone()
    finally:
        cursor.close()
        conn.close()
