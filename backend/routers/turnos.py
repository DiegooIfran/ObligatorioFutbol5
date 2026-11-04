import mysql.connector
from db import get_db_connection


def crear_turno(hora_inicio, hora_fin, user_role=None):
    """
    Crea un turno horario.
    Reglas de negocio:
    - hora_inicio >= '18:00:00'
    - hora_fin <= '23:00:00'
    - Duración exacta de 1 hora
    - Minutos y segundos en 0 (:00:00)
    """
    conn = get_db_connection(user_role=user_role)
    if not conn:
        return {"error": "No se pudo conectar a la base de datos"}

    cursor = conn.cursor(dictionary=True)
    try:
        sql = "INSERT INTO turno (hora_inicio, hora_fin) VALUES (%s, %s)"
        cursor.execute(sql, (str(hora_inicio), str(hora_fin)))
        conn.commit()
        return {"exito": True, "mensaje": "Turno creado correctamente.", "id_turno": cursor.lastrowid}
    except mysql.connector.Error as err:
        return {"error": f"Error SQL: {err}"}
    finally:
        cursor.close()
        conn.close()


def actualizar_turno(id_turno, hora_inicio, hora_fin, user_role=None):
    """
    Actualiza el rango horario de un turno.
    """
    conn = get_db_connection(user_role=user_role)
    if not conn:
        return {"error": "No se pudo conectar a la base de datos"}

    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT id_turno FROM turno WHERE id_turno = %s", (id_turno,))
        if not cursor.fetchone():
            return {"error": "El turno no existe."}

        sql = "UPDATE turno SET hora_inicio = %s, hora_fin = %s WHERE id_turno = %s"
        cursor.execute(sql, (str(hora_inicio), str(hora_fin), id_turno))
        conn.commit()
        return {"exito": True, "mensaje": "Turno actualizado correctamente."}
    except mysql.connector.Error as err:
        return {"error": f"Error SQL: {err}"}
    finally:
        cursor.close()
        conn.close()


def eliminar_turno(id_turno, user_role=None):
    """
    Elimina un turno si no está asignado a ningún partido.
    """
    conn = get_db_connection(user_role=user_role)
    if not conn:
        return {"error": "No se pudo conectar a la base de datos"}

    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT id_turno FROM turno WHERE id_turno = %s", (id_turno,))
        if not cursor.fetchone():
            return {"error": "El turno no existe."}

        cursor.execute("SELECT COUNT(*) AS total FROM partido WHERE id_turno = %s", (id_turno,))
        if cursor.fetchone()["total"] > 0:
            return {"error": "No se puede eliminar el turno porque está asignado a partidos."}

        cursor.execute("DELETE FROM turno WHERE id_turno = %s", (id_turno,))
        conn.commit()
        return {"exito": True, "mensaje": "Turno eliminado correctamente."}
    except mysql.connector.Error as err:
        return {"error": f"Error SQL: {err}"}
    finally:
        cursor.close()
        conn.close()


def obtener_turnos(user_role=None):
    """
    Obtiene la lista de todos los turnos disponibles.
    """
    conn = get_db_connection(user_role=user_role)
    if not conn:
        return []

    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT id_turno, hora_inicio, hora_fin FROM turno ORDER BY hora_inicio ASC")
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()
