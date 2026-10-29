import mysql.connector
from db import get_db_connection


# Importamos las funciones desarrolladas previamente en tus módulos
# from routers.partidos import programar_partido
# from routers.planillas import registrar_planilla_jugador
# from routers.reportes import obtener_tabla_posiciones, obtener_goleadores


def autenticar_usuario(correo, contrasena):
    """
    Paso 1: Consulta la tabla 'login' para validar credenciales humanas.
    Se utiliza una conexión temporal o de lectura para verificar la cuenta.
    """
    # Conectamos con usuario básico o admin para validar el login
    conn = get_db_connection("administrador")
    if not conn:
        return None

    cursor = conn.cursor(dictionary=True)
    try:
        # Prevenimos inyección SQL usando tupla de parámetros (%s)
        sql = "SELECT correo, rol FROM login WHERE correo = %s AND contrasena = %s"
        cursor.execute(sql, (correo, contrasena))
        usuario = cursor.fetchone()
        return usuario  # Retorna None si las credenciales son incorrectas
    except mysql.connector.Error as err:
        print(f"[ERROR SQL en Login]: {err}")
        return None
    finally:
        cursor.close()
        conn.close()


# ==========================================
# MENÚ PARA ADMINISTRADORES
# ==========================================
def mostrar_menu_administrador(correo_usuario):
    # Paso 2: Instanciamos la conexión persistente con 'usr_admin'
    conn = get_db_connection("administrador")
    if not conn:
        return

    while True:
        print("\n" + "=" * 50)
        print(f"   PANEL DE ADMINISTRACIÓN (Sesión: {correo_usuario})")
        print("=" * 50)
        print("1. ABM de Jugadores y Equipos")
        print("2. ABM de Complejos Deportivos y Canchas")
        print("3. Programar/Editar Partidos (Control de Reglas)")
        print("4. Gestionar Sanciones a Jugadores")
        print("5. Ver Reportes Analíticos (Posiciones, Goleadores, Fair Play)")
        print("0. Cerrar Sesión / Salir")

        opcion = input("\nSeleccione una opción: ").strip()

        if opcion == "1":
            print("\n[Módulo]: Gestión de Jugadores y Equipos (ABM)")
            # Lógica / llamadas a funciones ABM...
        elif opcion == "2":
            print("\n[Módulo]: Gestión de Complejos y Canchas (ABM)")
        elif opcion == "3":
            print("\n[Módulo]: Programación de Partidos")
            # Ejemplo: programar_partido(...)
        elif opcion == "4":
            print("\n[Módulo]: Sanciones Disciplinarias")
        elif opcion == "5":
            print("\n[Módulo]: Reportes y Métricas del Torneo")
            # Ejemplo: obtener_tabla_posiciones(id_torneo=1)
        elif opcion == "0":
            print("\nCerrando sesión de Administrador...")
            conn.close()
            break
        else:
            print("\n[!] Opción no válida. Intente nuevamente.")


# ==========================================
# MENÚ PARA PLANILLEROS
# ==========================================
def mostrar_menu_planillero(correo_usuario):
    # Paso 2: Instanciamos la conexión persistente con 'usr_planillero' (permisos restringidos)
    conn = get_db_connection("planillero")
    if not conn:
        return

    while True:
        print("\n" + "=" * 50)
        print(f"   PANEL DE PLANILLERO (Sesión: {correo_usuario})")
        print("=" * 50)
        print("1. Cargar Planilla de Partido (Jugadores Presentes)")
        print("2. Registrar Gol")
        print("3. Registrar Tarjeta (Amarilla / Roja)")
        print("4. Consultar Partidos Programados del Día")
        print("0. Cerrar Sesión / Salir")

        opcion = input("\nSeleccione una opción: ").strip()

        if opcion == "1":
            print("\n[Módulo Planillero]: Cargar Planilla de Partido")
            # Si el planillero intentara hacer algo fuera de su rol, MySQL arrojará un error de permisos
        elif opcion == "2":
            print("\n[Módulo Planillero]: Registrar Gol")
        elif opcion == "3":
            print("\n[Módulo Planillero]: Registrar Tarjetas")
        elif opcion == "4":
            print("\n[Módulo Planillero]: Partidos del día")
        elif opcion == "0":
            print("\nCerrando sesión de Planillero...")
            conn.close()
            break
        else:
            print("\n[!] Opción no válida. Intente nuevamente.")


# ==========================================
# PUNTO DE ENTRADA PRINCIPAL (LOGIN)
# ==========================================
def main():
    print("=" * 50)
    print(" SISTEMA DE GESTIÓN DE FÚTBOL 5 - UCU 2026")
    print("=" * 50)

    # Captura de credenciales por terminal
    correo = input("Correo electrónico: ").strip()
    contrasena = input("Contraseña: ").strip()

    print("\nVerificando credenciales...")
    usuario = autenticar_usuario(correo, contrasena)

    if not usuario:
        print("\n[X] Error: Correo o contraseña incorrectos. Acceso denegado.")
        return

    print(f"\n[✓] Autenticación exitosa. Rol detectado: {usuario['rol'].upper()}")

    # Redirección dinámica según el rol retornado por la tabla 'login'
    if usuario["rol"] == "administrador":
        mostrar_menu_administrador(usuario["correo"])
    elif usuario["rol"] == "planillero":
        mostrar_menu_planillero(usuario["correo"])
    else:
        print(f"\n[X] Error: El rol '{usuario['rol']}' no tiene un menú asignado.")


if __name__ == "__main__":
    main()
