import mysql.connector
from mysql.connector import Error

# Credenciales según el rol
CREDENTIALS = {
    "admin": {
        "user": "usr_admin",
        "password": "AdminPass123!"
    },
    "planillero": {
        "user": "usr_planillero",
        "password": "PlanilleroPass123!"
    },
    # Solo se usa para validar el login (SELECT sobre la tabla login)
    "login": {
        "user": "usr_login",
        "password": "Contraseña123!"
    }
}

# Variable global que guarda el rol de la sesión actual ('admin' o 'planillero')
CURRENT_ROLE = "admin"


def set_current_role(role):
    """
    Configura el rol global de la sesión tras iniciar sesión.
    Acepta 'admin', 'administrador', 'planillero' o 'login'.
    """
    global CURRENT_ROLE
    if role in ("administrador", "admin"):
        CURRENT_ROLE = "admin"
    elif role == "planillero":
        CURRENT_ROLE = "planillero"
    elif role == "login":
        CURRENT_ROLE = "login"
    else:
        raise ValueError(f"Rol no válido: {role}")


def get_current_role():
    """
    Retorna el rol global configurado para la sesión.
    """
    return CURRENT_ROLE


def get_db_connection(user_role=None):
    """
    Retorna una conexión activa a MySQL con las credenciales del rol solicitado.
    Si no se especifica user_role (o es None), utiliza el rol global CURRENT_ROLE.
    """
    rol = user_role if user_role is not None else CURRENT_ROLE

    # Normalizar 'administrador' a 'admin'
    if rol in ("administrador", "admin"):
        rol = "admin"

    if rol not in CREDENTIALS:
        raise ValueError(f"Rol no válido: {rol}")

    creds = CREDENTIALS[rol]

    try:
        connection = mysql.connector.connect(
            host="localhost",
            database="Obligatorio_Futbol5",
            user=creds["user"],
            password=creds["password"]
        )
        return connection
    except Error as e:
        print(f"Error de conexión a MySQL: {e}")
        return None
