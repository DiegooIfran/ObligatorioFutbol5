import mysql.connector
from db import get_db_connection


def crear_cancha(nombre_cancha, id_complejo, superficie, techada):
    """
    Crea una cancha asociada a un complejo deportivo.
    Superficie debe ser 'sintetico' o 'parquet'.
    """
    if superficie not in ("sintetico", "parquet"):
        return {"error": "Superficie no válida. Debe ser 'sintetico' o 'parquet'."}

    conn = get_db_connection(user_role="admin")
    if not conn:
        return {"error": "No se pudo conectar a la base de datos"}

    cursor = conn.cursor(dictionary=True)
    try:
        # Verificar que el complejo exista
        cursor.execute("SELECT id_complejo FROM complejo WHERE id_complejo = %s", (id_complejo,))
        if not cursor.fetchone():
            return {"error": "El complejo deportivo indicado no existe."}

        # Verificar si ya existe cancha con ese nombre en el complejo
        cursor.execute(
            "SELECT nombre_cancha FROM cancha WHERE nombre_cancha = %s AND id_complejo = %s",
            (nombre_cancha, id_complejo)
        )
        if cursor.fetchone():
            return {"error": f"Ya existe una cancha con el nombre '{nombre_cancha}' en este complejo."}

        sql = "INSERT INTO cancha (nombre_cancha, id_complejo, superficie, techada) VALUES (%s, %s, %s, %s)"
        cursor.execute(sql, (nombre_cancha, id_complejo, superficie, bool(techada)))
        conn.commit()

        return {"exito": True, "mensaje": "Cancha registrada correctamente."}
    except mysql.connector.Error as err:
        return {"error": f"Error SQL: {err}"}
    finally:
        cursor.close()
        conn.close()


def actualizar_cancha(nombre_cancha, id_complejo, nueva_superficie=None, nueva_techada=None):
    """
    Actualiza la superficie o condición de techada de una cancha.
    """
    conn = get_db_connection(user_role="admin")
    if not conn:
        return {"error": "No se pudo conectar a la base de datos"}

    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            "SELECT * FROM cancha WHERE nombre_cancha = %s AND id_complejo = %s",
            (nombre_cancha, id_complejo)
        )
        cancha = cursor.fetchone()
        if not cancha:
            return {"error": "La cancha no existe."}

        sup = nueva_superficie if nueva_superficie is not None else cancha["superficie"]
        if sup not in ("sintetico", "parquet"):
            return {"error": "Superficie no válida. Debe ser 'sintetico' o 'parquet'."}

        tech = bool(nueva_techada) if nueva_techada is not None else cancha["techada"]

        sql = "UPDATE cancha SET superficie = %s, techada = %s WHERE nombre_cancha = %s AND id_complejo = %s"
        cursor.execute(sql, (sup, tech, nombre_cancha, id_complejo))
        conn.commit()

        return {"exito": True, "mensaje": "Cancha actualizada correctamente."}
    except mysql.connector.Error as err:
        return {"error": f"Error SQL: {err}"}
    finally:
        cursor.close()
        conn.close()


def eliminar_cancha(nombre_cancha, id_complejo):
    """
    Elimina una cancha si no está asignada a ningún partido programado o jugado.
    """
    conn = get_db_connection(user_role="admin")
    if not conn:
        return {"error": "No se pudo conectar a la base de datos"}

    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            "SELECT * FROM cancha WHERE nombre_cancha = %s AND id_complejo = %s",
            (nombre_cancha, id_complejo)
        )
        if not cursor.fetchone():
            return {"error": "La cancha no existe."}

        # Verificar si tiene partidos asociados
        cursor.execute(
            "SELECT COUNT(*) AS total FROM partido WHERE nombre_cancha = %s AND id_complejo = %s",
            (nombre_cancha, id_complejo)
        )
        if cursor.fetchone()["total"] > 0:
            return {"error": "No se puede eliminar la cancha porque tiene partidos asociados."}

        cursor.execute("DELETE FROM cancha WHERE nombre_cancha = %s AND id_complejo = %s", (nombre_cancha, id_complejo))
        conn.commit()
        return {"exito": True, "mensaje": "Cancha eliminada correctamente."}
    except mysql.connector.Error as err:
        return {"error": f"Error SQL: {err}"}
    finally:
        cursor.close()
        conn.close()


def obtener_canchas(id_complejo=None):
    """
    Retorna la lista de canchas, opcionalmente filtrada por complejo.
    """
    conn = get_db_connection(user_role="admin")
    if not conn:
        return []

    cursor = conn.cursor(dictionary=True)
    try:
        if id_complejo is not None:
            sql = """
                SELECT c.nombre_cancha, c.id_complejo, comp.nombre as complejo, c.superficie, c.techada
                FROM cancha c
                JOIN complejo comp ON c.id_complejo = comp.id_complejo
                WHERE c.id_complejo = %s
                ORDER BY c.nombre_cancha ASC
            """
            cursor.execute(sql, (id_complejo,))
        else:
            sql = """
                SELECT c.nombre_cancha, c.id_complejo, comp.nombre as complejo, c.superficie, c.techada
                FROM cancha c
                JOIN complejo comp ON c.id_complejo = comp.id_complejo
                ORDER BY comp.nombre ASC, c.nombre_cancha ASC
            """
            cursor.execute(sql)
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()

