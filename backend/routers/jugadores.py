import mysql.connector
from db import get_db_connection


def crear_jugador(ci, nombre, apellido, email, fecha_nacimiento, id_facultad, tipo, user_role=None):
    """
    Crea un nuevo jugador validando rango de CI, tipo de jugador y existencia de la facultad.
    """
    if not (10000000 <= int(ci) <= 60000000):
        return {"error": "La cédula debe estar comprendida entre 10000000 y 60000000."}

    tipos_validos = ("grado", "postgrado", "docente", "funcionario")
    if tipo not in tipos_validos:
        return {"error": f"Tipo de jugador no válido. Debe ser uno de: {', '.join(tipos_validos)}."}

    conn = get_db_connection(user_role=user_role)
    if not conn:
        return {"error": "No se pudo conectar a la base de datos"}

    cursor = conn.cursor(dictionary=True)
    try:
        # Validar existencia de la facultad
        cursor.execute("SELECT id_facultad FROM facultad WHERE id_facultad = %s", (id_facultad,))
        if not cursor.fetchone():
            return {"error": "La facultad indicada no existe."}

        # Validar cédula duplicada
        cursor.execute("SELECT ci FROM jugador WHERE ci = %s", (ci,))
        if cursor.fetchone():
            return {"error": f"Ya existe un jugador con la cédula {ci}."}

        sql_insert = """
            INSERT INTO jugador (ci, nombre, apellido, email, fecha_nacimiento, id_facultad, tipo)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(sql_insert, (ci, nombre, apellido, email, fecha_nacimiento, id_facultad, tipo))
        conn.commit()

        return {"exito": True, "mensaje": "Jugador registrado correctamente."}
    except mysql.connector.Error as err:
        return {"error": f"Error SQL: {err}"}
    finally:
        cursor.close()
        conn.close()


def actualizar_jugador(ci, nombre=None, apellido=None, email=None, fecha_nacimiento=None, id_facultad=None, tipo=None, user_role=None):
    """
    Actualiza la información de un jugador.
    Si se cambia tipo o facultad, valida que el jugador no esté inscripto en torneos no finalizados.
    """
    conn = get_db_connection(user_role=user_role)
    if not conn:
        return {"error": "No se pudo conectar a la base de datos"}

    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM jugador WHERE ci = %s", (ci,))
        jugador = cursor.fetchone()
        if not jugador:
            return {"error": "El jugador no existe."}

        nuevo_nombre = nombre if nombre is not None else jugador["nombre"]
        nuevo_apellido = apellido if apellido is not None else jugador["apellido"]
        nuevo_email = email if email is not None else jugador["email"]
        nueva_fecha = fecha_nacimiento if fecha_nacimiento is not None else jugador["fecha_nacimiento"]
        nuevo_id_facultad = id_facultad if id_facultad is not None else jugador["id_facultad"]
        nuevo_tipo = tipo if tipo is not None else jugador["tipo"]

        if nuevo_tipo not in ("grado", "postgrado", "docente", "funcionario"):
            return {"error": "Tipo de jugador no válido."}

        # Validar cambio de tipo o facultad
        if nuevo_tipo != jugador["tipo"] or nuevo_id_facultad != jugador["id_facultad"]:
            sql_check = """
                SELECT COUNT(*) AS total
                FROM equipo_jugador_torneo e
                JOIN torneo t ON t.id_torneo = e.id_torneo
                WHERE e.ci_jugador = %s AND t.estado <> 'finalizado'
            """
            cursor.execute(sql_check, (ci,))
            if cursor.fetchone()["total"] > 0:
                return {"error": "No se puede cambiar el tipo ni la facultad de un jugador inscripto en un torneo no finalizado."}

        sql_update = """
            UPDATE jugador
            SET nombre = %s, apellido = %s, email = %s, fecha_nacimiento = %s, id_facultad = %s, tipo = %s
            WHERE ci = %s
        """
        cursor.execute(sql_update, (nuevo_nombre, nuevo_apellido, nuevo_email, nueva_fecha, nuevo_id_facultad, nuevo_tipo, ci))
        conn.commit()

        return {"exito": True, "mensaje": "Jugador actualizado correctamente."}
    except mysql.connector.Error as err:
        return {"error": f"Error SQL: {err}"}
    finally:
        cursor.close()
        conn.close()


def eliminar_jugador(ci, user_role=None):
    """
    Elimina a un jugador si no tiene dependencias (inscripciones, capitanías, planillas, etc.).
    """
    conn = get_db_connection(user_role=user_role)
    if not conn:
        return {"error": "No se pudo conectar a la base de datos"}

    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT ci FROM jugador WHERE ci = %s", (ci,))
        if not cursor.fetchone():
            return {"error": "El jugador no existe."}

        # Validar si es capitán
        cursor.execute("SELECT COUNT(*) AS total FROM equipo WHERE ci_capitan = %s", (ci,))
        if cursor.fetchone()["total"] > 0:
            return {"error": "No se puede eliminar el jugador porque es capitán de uno o más equipos."}

        # Validar inscripciones
        cursor.execute("SELECT COUNT(*) AS total FROM equipo_jugador_torneo WHERE ci_jugador = %s", (ci,))
        if cursor.fetchone()["total"] > 0:
            return {"error": "No se puede eliminar el jugador porque está inscripto en un equipo."}

        cursor.execute("DELETE FROM jugador WHERE ci = %s", (ci,))
        conn.commit()
        return {"exito": True, "mensaje": "Jugador eliminado correctamente."}
    except mysql.connector.Error as err:
        return {"error": f"Error SQL: {err}"}
    finally:
        cursor.close()
        conn.close()


def obtener_jugadores(id_facultad=None, user_role=None):
    """
    Obtiene la lista de jugadores, opcionalmente filtrada por facultad.
    """
    conn = get_db_connection(user_role=user_role)
    if not conn:
        return []

    cursor = conn.cursor(dictionary=True)
    try:
        if id_facultad is not None:
            cursor.execute("SELECT * FROM jugador WHERE id_facultad = %s ORDER BY apellido, nombre", (id_facultad,))
        else:
            cursor.execute("SELECT * FROM jugador ORDER BY apellido, nombre")
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()


def obtener_jugador(ci, user_role=None):
    """
    Obtiene un jugador por su cédula.
    """
    conn = get_db_connection(user_role=user_role)
    if not conn:
        return None

    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM jugador WHERE ci = %s", (ci,))
        return cursor.fetchone()
    finally:
        cursor.close()
        conn.close()
