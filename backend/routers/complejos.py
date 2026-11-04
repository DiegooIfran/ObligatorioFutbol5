import mysql.connector
from db import get_db_connection


def crear_complejo(nombre, direccion, departamento, user_role=None):
    """
    Crea un nuevo complejo deportivo.
    """
    conn = get_db_connection(user_role=user_role)
    if not conn:
        return {"error": "No se pudo conectar a la base de datos"}

    cursor = conn.cursor(dictionary=True)
    try:
        sql = "INSERT INTO complejo (nombre, direccion, departamento) VALUES (%s, %s, %s)"
        cursor.execute(sql, (nombre, direccion, departamento))
        conn.commit()
        return {"exito": True, "mensaje": "Complejo deportivo creado exitosamente.", "id_complejo": cursor.lastrowid}
    except mysql.connector.Error as err:
        return {"error": f"Error SQL: {err}"}
    finally:
        cursor.close()
        conn.close()


def actualizar_complejo(id_complejo, nombre=None, direccion=None, departamento=None, user_role=None):
    """
    Actualiza los datos de un complejo deportivo existente.
    """
    conn = get_db_connection(user_role=user_role)
    if not conn:
        return {"error": "No se pudo conectar a la base de datos"}

    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM complejo WHERE id_complejo = %s", (id_complejo,))
        complejo = cursor.fetchone()
        if not complejo:
            return {"error": "El complejo no existe."}

        nuevo_nombre = nombre if nombre is not None else complejo["nombre"]
        nueva_direccion = direccion if direccion is not None else complejo["direccion"]
        nuevo_departamento = departamento if departamento is not None else complejo["departamento"]

        sql = "UPDATE complejo SET nombre = %s, direccion = %s, departamento = %s WHERE id_complejo = %s"
        cursor.execute(sql, (nuevo_nombre, nueva_direccion, nuevo_departamento, id_complejo))
        conn.commit()

        return {"exito": True, "mensaje": "Complejo deportivo actualizado correctamente."}
    except mysql.connector.Error as err:
        return {"error": f"Error SQL: {err}"}
    finally:
        cursor.close()
        conn.close()


def eliminar_complejo(id_complejo, user_role=None):
    """
    Elimina un complejo si no tiene canchas asociadas.
    """
    conn = get_db_connection(user_role=user_role)
    if not conn:
        return {"error": "No se pudo conectar a la base de datos"}

    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT id_complejo FROM complejo WHERE id_complejo = %s", (id_complejo,))
        if not cursor.fetchone():
            return {"error": "El complejo no existe."}

        cursor.execute("SELECT COUNT(*) AS total FROM cancha WHERE id_complejo = %s", (id_complejo,))
        if cursor.fetchone()["total"] > 0:
            return {"error": "No se puede eliminar el complejo porque tiene canchas registradas."}

        cursor.execute("DELETE FROM complejo WHERE id_complejo = %s", (id_complejo,))
        conn.commit()
        return {"exito": True, "mensaje": "Complejo eliminado correctamente."}
    except mysql.connector.Error as err:
        return {"error": f"Error SQL: {err}"}
    finally:
        cursor.close()
        conn.close()


def obtener_complejos(user_role=None):
    """
    Retorna la lista de complejos deportivos.
    """
    conn = get_db_connection(user_role=user_role)
    if not conn:
        return []

    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM complejo ORDER BY nombre ASC")
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()


def obtener_complejo(id_complejo, user_role=None):
    """
    Retorna un complejo por su ID.
    """
    conn = get_db_connection(user_role=user_role)
    if not conn:
        return None

    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM complejo WHERE id_complejo = %s", (id_complejo,))
        return cursor.fetchone()
    finally:
        cursor.close()
        conn.close()
