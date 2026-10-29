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
    }
}

# Retorna una conexión activa a MySQL con las credenciales del rol solicitado.
def get_db_connection(user_role="admin"):
    if user_role not in CREDENTIALS:
        raise ValueError("Rol no válido")

    creds = CREDENTIALS[user_role]

    try:
        connection = mysql.connector.connect(
            host="localhost",
            database="ObligatorioFutbol5",
            user=creds["user"],
            password=creds["password"]
        )
        return connection
    except Error as e:
        print(f"Error de conexión a MySQL: {e}")
        return None