from datetime import datetime
import mysql.connector
from db import get_db_connection


def crear_torneo(nombre, anio, semestre, fecha_inicio, fecha_fin, estado="inscripción"):
    """
    Crea un nuevo torneo con sus validaciones de negocio (fechas, año y semestre).
    """
    if semestre not in (1, 2):
        return {"error": "El semestre debe ser 1 o 2."}

    estados_validos = ("inscripción", "en curso", "finalizado")
    if estado not in estados_validos:
        return {"error": f"Estado no válido. Debe ser uno de: {', '.join(estados_validos)}."}

    if int(anio) < 2026:
        return {"error": "El año del torneo debe ser igual o mayor a 2026."}

    f_inicio = datetime.strptime(fecha_inicio, "%Y-%m-%d").date() if isinstance(fecha_inicio, str) else fecha_inicio
    f_fin = datetime.strptime(fecha_fin, "%Y-%m-%d").date() if isinstance(fecha_fin, str) else fecha_fin

    if f_inicio.year != int(anio) or f_fin.year != int(anio):
        return {"error": "Las fechas de inicio y fin deben corresponder al año del torneo."}

    if f_inicio >= f_fin:
        return {"error": "La fecha de inicio debe ser anterior a la fecha de fin."}

    conn = get_db_connection(user_role="admin")
    if not conn:
        return {"error": "No se pudo conectar a la base de datos"}

    cursor = conn.cursor(dictionary=True)
    try:
        sql = """
            INSERT INTO torneo (nombre, anio, semestre, fecha_inicio, fecha_fin, estado)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        cursor.execute(sql, (nombre, anio, semestre, f_inicio, f_fin, estado))
        conn.commit()
        return {"exito": True, "mensaje": "Torneo creado correctamente.", "id_torneo": cursor.lastrowid}
    except mysql.connector.Error as err:
        return {"error": f"Error SQL: {err}"}
    finally:
        cursor.close()
        conn.close()


def actualizar_torneo(id_torneo, nombre=None, anio=None, semestre=None, fecha_inicio=None, fecha_fin=None, estado=None):
    """
    Actualiza los datos de un torneo.
    Si se modifican las fechas, valida que no queden partidos programados por fuera del nuevo rango.
    """
    conn = get_db_connection(user_role="admin")
    if not conn:
        return {"error": "No se pudo conectar a la base de datos"}

    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM torneo WHERE id_torneo = %s", (id_torneo,))
        torneo = cursor.fetchone()
        if not torneo:
            return {"error": "El torneo no existe."}

        nuevo_nombre = nombre if nombre is not None else torneo["nombre"]
        nuevo_anio = anio if anio is not None else torneo["anio"]
        nuevo_semestre = semestre if semestre is not None else torneo["semestre"]
        nuevo_estado = estado if estado is not None else torneo["estado"]

        nueva_f_inicio = datetime.strptime(fecha_inicio, "%Y-%m-%d").date() if isinstance(fecha_inicio, str) else (fecha_inicio if fecha_inicio is not None else torneo["fecha_inicio"])
        nueva_f_fin = datetime.strptime(fecha_fin, "%Y-%m-%d").date() if isinstance(fecha_fin, str) else (fecha_fin if fecha_fin is not None else torneo["fecha_fin"])

        if nuevo_semestre not in (1, 2):
            return {"error": "El semestre debe ser 1 o 2."}

        if nuevo_estado not in ("inscripción", "en curso", "finalizado"):
            return {"error": "Estado no válido."}

        if nueva_f_inicio >= nueva_f_fin:
            return {"error": "La fecha de inicio debe ser anterior a la fecha de fin."}

        # Validar si hay partidos fuera del nuevo rango
        if nueva_f_inicio != torneo["fecha_inicio"] or nueva_f_fin != torneo["fecha_fin"]:
            sql_fuera = """
                SELECT COUNT(*) AS total
                FROM partido
                WHERE id_torneo = %s AND (dia < %s OR dia > %s)
            """
            cursor.execute(sql_fuera, (id_torneo, nueva_f_inicio, nueva_f_fin))
            if cursor.fetchone()["total"] > 0:
                return {"error": "Hay partidos programados fuera del nuevo rango de fechas del torneo."}

        sql_update = """
            UPDATE torneo
            SET nombre = %s, anio = %s, semestre = %s, fecha_inicio = %s, fecha_fin = %s, estado = %s
            WHERE id_torneo = %s
        """
        cursor.execute(sql_update, (nuevo_nombre, nuevo_anio, nuevo_semestre, nueva_f_inicio, nueva_f_fin, nuevo_estado, id_torneo))
        conn.commit()

        return {"exito": True, "mensaje": "Torneo actualizado correctamente."}
    except mysql.connector.Error as err:
        return {"error": f"Error SQL: {err}"}
    finally:
        cursor.close()
        conn.close()


def eliminar_torneo(id_torneo):
    """
    Elimina un torneo si no tiene equipos ni partidos registrados.
    """
    conn = get_db_connection(user_role="admin")
    if not conn:
        return {"error": "No se pudo conectar a la base de datos"}

    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT id_torneo FROM torneo WHERE id_torneo = %s", (id_torneo,))
        if not cursor.fetchone():
            return {"error": "El torneo no existe."}

        cursor.execute("SELECT COUNT(*) AS total FROM equipo WHERE id_torneo = %s", (id_torneo,))
        if cursor.fetchone()["total"] > 0:
            return {"error": "No se puede eliminar el torneo porque tiene equipos inscriptos."}

        cursor.execute("SELECT COUNT(*) AS total FROM partido WHERE id_torneo = %s", (id_torneo,))
        if cursor.fetchone()["total"] > 0:
            return {"error": "No se puede eliminar el torneo porque tiene partidos programados o jugados."}

        cursor.execute("DELETE FROM torneo WHERE id_torneo = %s", (id_torneo,))
        conn.commit()
        return {"exito": True, "mensaje": "Torneo eliminado correctamente."}
    except mysql.connector.Error as err:
        return {"error": f"Error SQL: {err}"}
    finally:
        cursor.close()
        conn.close()


def obtener_torneos():
    """
    Retorna la lista de torneos.
    """
    conn = get_db_connection(user_role="admin")
    if not conn:
        return []

    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM torneo ORDER BY anio DESC, semestre DESC")
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()


def obtener_torneo(id_torneo):
    """
    Retorna un torneo por su ID.
    """
    conn = get_db_connection(user_role="admin")
    if not conn:
        return None

    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM torneo WHERE id_torneo = %s", (id_torneo,))
        return cursor.fetchone()
    finally:
        cursor.close()
        conn.close()

