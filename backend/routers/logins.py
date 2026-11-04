import mysql.connector
from db import get_db_connection


def crear_usuario(correo, contrasena, rol, user_role=None):
    """
    Registra un nuevo usuario en la tabla login.
    Roles válidos: 'administrador', 'planillero'.
    """
    roles_validos = ("administrador", "planillero")
    if rol not in roles_validos:
        return {"error": f"Rol no válido. Debe ser uno de: {', '.join(roles_validos)}."}

    conn = get_db_connection(user_role=user_role)
    if not conn:
        return {"error": "No se pudo conectar a la base de datos"}

    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT correo FROM login WHERE correo = %s", (correo,))
        if cursor.fetchone():
            return {"error": f"Ya existe un usuario con el correo '{correo}'."}

        sql = "INSERT INTO login (correo, contrasena, rol) VALUES (%s, %s, %s)"
        cursor.execute(sql, (correo, contrasena, rol))
        conn.commit()

        return {"exito": True, "mensaje": "Usuario creado correctamente."}
    except mysql.connector.Error as err:
        return {"error": f"Error SQL: {err}"}
    finally:
        cursor.close()
        conn.close()


def actualizar_usuario(correo, nueva_contrasena=None, nuevo_rol=None, user_role=None):
    """
    Actualiza la contraseña o rol de un usuario.
    (El trigger trg_login_bu_ultimo_admin protege de degradar al último administrador).
    """
    conn = get_db_connection(user_role=user_role)
    if not conn:
        return {"error": "No se pudo conectar a la base de datos"}

    cursor = conn.cursor(dictionary=True)
    try:
        # usr_admin solo puede leer correo y rol, no la contraseña
        cursor.execute("SELECT correo, rol FROM login WHERE correo = %s", (correo,))
        usuario = cursor.fetchone()
        if not usuario:
            return {"error": "El usuario no existe."}

        rol_final = nuevo_rol if nuevo_rol is not None else usuario["rol"]

        if rol_final not in ("administrador", "planillero"):
            return {"error": "Rol no válido. Debe ser 'administrador' o 'planillero'."}

        # Si no hay contraseña nueva, se actualiza solo el rol
        if nueva_contrasena is not None:
            sql = "UPDATE login SET contrasena = %s, rol = %s WHERE correo = %s"
            cursor.execute(sql, (nueva_contrasena, rol_final, correo))
        else:
            sql = "UPDATE login SET rol = %s WHERE correo = %s"
            cursor.execute(sql, (rol_final, correo))
        conn.commit()

        return {"exito": True, "mensaje": "Usuario actualizado correctamente."}
    except mysql.connector.Error as err:
        return {"error": f"Error SQL: {err}"}
    finally:
        cursor.close()
        conn.close()


def eliminar_usuario(correo, user_role=None):
    """
    Elimina un usuario.
    (El trigger trg_login_bd_ultimo_admin impide eliminar al último administrador).
    """
    conn = get_db_connection(user_role=user_role)
    if not conn:
        return {"error": "No se pudo conectar a la base de datos"}

    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT correo FROM login WHERE correo = %s", (correo,))
        if not cursor.fetchone():
            return {"error": "El usuario no existe."}

        sql = "DELETE FROM login WHERE correo = %s"
        cursor.execute(sql, (correo,))
        conn.commit()

        return {"exito": True, "mensaje": "Usuario eliminado correctamente."}
    except mysql.connector.Error as err:
        return {"error": f"Error SQL: {err}"}
    finally:
        cursor.close()
        conn.close()


def obtener_usuarios(user_role=None):
    """
    Obtiene la lista de usuarios registrados (sin exponer contraseñas).
    """
    conn = get_db_connection(user_role=user_role)
    if not conn:
        return []

    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT correo, rol FROM login ORDER BY rol ASC, correo ASC")
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()
