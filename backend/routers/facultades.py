import mysql.connector
from db import get_db_connection


def crear_facultad(nombre, user_role=None):
    """
    Registra una nueva facultad.
    """
    conn = get_db_connection(user_role=user_role)
    if not conn:
        return {"error": "No se pudo conectar a la base de datos"}

    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT id_facultad FROM facultad WHERE nombre = %s", (nombre,))
        if cursor.fetchone():
            return {"error": f"Ya existe una facultad con el nombre '{nombre}'."}

        cursor.execute("INSERT INTO facultad (nombre) VALUES (%s)", (nombre,))
        conn.commit()
        return {"exito": True, "mensaje": "Facultad creada exitosamente.", "id_facultad": cursor.lastrowid}
    except mysql.connector.Error as err:
        return {"error": f"Error SQL: {err}"}
    finally:
        cursor.close()
        conn.close()


def actualizar_facultad(id_facultad, nombre, user_role=None):
    """
    Modifica el nombre de una facultad existente.
    """
    conn = get_db_connection(user_role=user_role)
    if not conn:
        return {"error": "No se pudo conectar a la base de datos"}

    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT id_facultad FROM facultad WHERE id_facultad = %s", (id_facultad,))
        if not cursor.fetchone():
            return {"error": "La facultad no existe."}

        cursor.execute("UPDATE facultad SET nombre = %s WHERE id_facultad = %s", (nombre, id_facultad))
        conn.commit()
        return {"exito": True, "mensaje": "Facultad actualizada exitosamente."}
    except mysql.connector.Error as err:
        return {"error": f"Error SQL: {err}"}
    finally:
        cursor.close()
        conn.close()


def eliminar_facultad(id_facultad, user_role=None):
    """
    Elimina una facultad si no tiene jugadores o equipos asociados.
    """
    conn = get_db_connection(user_role=user_role)
    if not conn:
        return {"error": "No se pudo conectar a la base de datos"}

    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT id_facultad FROM facultad WHERE id_facultad = %s", (id_facultad,))
        if not cursor.fetchone():
            return {"error": "La facultad no existe."}

        cursor.execute("SELECT COUNT(*) AS total FROM jugador WHERE id_facultad = %s", (id_facultad,))
        if cursor.fetchone()["total"] > 0:
            return {"error": "No se puede eliminar la facultad porque tiene jugadores asociados."}

        cursor.execute("SELECT COUNT(*) AS total FROM equipo WHERE id_facultad = %s", (id_facultad,))
        if cursor.fetchone()["total"] > 0:
            return {"error": "No se puede eliminar la facultad porque tiene equipos asociados."}

        cursor.execute("DELETE FROM facultad WHERE id_facultad = %s", (id_facultad,))
        conn.commit()
        return {"exito": True, "mensaje": "Facultad eliminada exitosamente."}
    except mysql.connector.Error as err:
        return {"error": f"Error SQL: {err}"}
    finally:
        cursor.close()
        conn.close()


def obtener_facultades(user_role=None):
    """
    Obtiene la lista completa de facultades.
    """
    conn = get_db_connection(user_role=user_role)
    if not conn:
        return []

    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT id_facultad, nombre FROM facultad ORDER BY nombre ASC")
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()
