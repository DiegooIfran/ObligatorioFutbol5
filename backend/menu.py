import mysql.connector
from db import get_db_connection, set_current_role

# ==========================================
# IMPORTACIONES DE ROUTERS
# ==========================================
from routers.torneos import crear_torneo, actualizar_torneo, eliminar_torneo, obtener_torneos, obtener_torneo
from routers.logins import crear_usuario, actualizar_usuario, eliminar_usuario, obtener_usuarios
from routers.canchas import crear_cancha, actualizar_cancha, eliminar_cancha, obtener_canchas
from routers.complejos import crear_complejo, actualizar_complejo, eliminar_complejo, obtener_complejos, obtener_complejo
from routers.equipos import crear_equipo, actualizar_equipo, eliminar_equipo, obtener_equipos, obtener_equipo
from routers.equipo_jugadores import inscribir_jugador_equipo, modificar_camiseta_jugador, eliminar_jugador_equipo, obtener_plantel
from routers.facultades import crear_facultad, actualizar_facultad, eliminar_facultad, obtener_facultades
from routers.goles import registrar_gol, modificar_gol, eliminar_gol, obtener_goles_partido
from routers.jugadores import crear_jugador, actualizar_jugador, eliminar_jugador, obtener_jugadores, obtener_jugador
from routers.partidos import programar_partido, postergar_partido, marcar_jugado, cancelar_partido, eliminar_partido, obtener_partidos
from routers.planillas import registrar_planilla_jugador, borrar_planilla_jugador, obtener_planilla_partido
from routers.sanciones import crear_sancion, actualizar_sancion, eliminar_sancion, obtener_sanciones
from routers.tarjetas import registrar_tarjeta, modificar_tarjeta, eliminar_tarjeta, obtener_tarjetas_partido
from routers.turnos import crear_turno, actualizar_turno, eliminar_turno, obtener_turnos
from routers.reportes import (
    obtener_tabla_posiciones, obtener_tabla_goleadores, obtener_tabla_fair_play,
    obtener_promedio_goles_fecha, obtener_promedio_goles_edicion, obtener_canchas_turnos,
    obtener_jugadores_facultad, obtener_sin_figurar, obtener_sanciones_equipo,
    obtener_porcentaje_jugados, obtener_resultados, obtener_tarjetas_jugador,
    obtener_tarjetas_jugador_torneo, obtener_porcentaje_participacion
)


# ==========================================
# EXCEPCIÓN Y CONTROL DE CANCELACIÓN
# ==========================================
class OperacionCancelada(Exception):
    """Excepción lanzada cuando el usuario cancela una pantalla de ingreso de datos para regresar al menú anterior."""
    pass


PALABRAS_CANCELAR = {"cancelar", "cancel", "salir", "volver", "v", "0"}


# ==========================================
# UTILIDADES DE MENÚ Y ENTRADA DE DATOS
# ==========================================
def mostrar_resultado(resultado):
    """Muestra el resultado de una operación de forma legible."""
    if resultado is None:
        print("\n[i] No se encontraron registros o la entidad no existe.")
        return

    if isinstance(resultado, dict):
        if "error" in resultado:
            print(f"\n[X] Error: {resultado['error']}")
        elif "exito" in resultado:
            print(f"\n[✓] {resultado.get('mensaje', 'Operación exitosa.')}")
            for clave, valor in resultado.items():
                if clave not in ("exito", "mensaje"):
                    print(f"    {clave}: {valor}")
        else:
            for clave, valor in resultado.items():
                print(f"  {clave}: {valor}")
    elif isinstance(resultado, list):
        if not resultado:
            print("\n[i] No se encontraron resultados.")
        else:
            for i, fila in enumerate(resultado, 1):
                print(f"\n--- Registro {i} ---")
                if isinstance(fila, dict):
                    for clave, valor in fila.items():
                        print(f"  {clave}: {valor}")
                else:
                    print(f"  {fila}")
    else:
        print(resultado)


def pedir_input(mensaje, obligatorio=True, permitir_cancelar=True):
    """
    Pide un valor de texto al usuario.
    Si el usuario escribe 'cancelar', 'volver', 'salir' o 'v', lanza OperacionCancelada.
    Retorna None si no es obligatorio y se deja vacío.
    """
    valor = input(mensaje).strip()

    if permitir_cancelar and valor.lower() in PALABRAS_CANCELAR:
        raise OperacionCancelada()

    if not valor:
        if obligatorio:
            print("[!] Este campo es obligatorio (o escriba 'cancelar' para volver).")
            return pedir_input(mensaje, obligatorio, permitir_cancelar)
        return None
    return valor


def pedir_int(mensaje, obligatorio=True, permitir_cero=False):
    """
    Pide un número entero al usuario.
    Si el usuario escribe 'cancelar', 'volver', 'salir' o '0' (cuando permitir_cero es False),
    lanza OperacionCancelada para volver a la pantalla anterior.
    Retorna None si no es obligatorio y se deja vacío.
    """
    valor = input(mensaje).strip()

    if valor.lower() in PALABRAS_CANCELAR or (not permitir_cero and valor == "0"):
        raise OperacionCancelada()

    if not valor:
        if obligatorio:
            print("[!] Este campo es obligatorio (o escriba 'cancelar'/'0' para volver).")
            return pedir_int(mensaje, obligatorio, permitir_cero)
        return None

    try:
        return int(valor)
    except ValueError:
        print("[!] Debe ingresar un número entero válido (o escriba 'cancelar'/'0' para volver).")
        return pedir_int(mensaje, obligatorio, permitir_cero)


def pedir_confirmacion(mensaje="¿Confirma esta operación? (s/n): "):
    """Pide confirmación sí/no al usuario. Si se cancela, lanza OperacionCancelada."""
    resp = input(mensaje).strip().lower()
    if resp in PALABRAS_CANCELAR or resp == "0":
        raise OperacionCancelada()
    return resp in ("s", "si", "sí", "y", "yes")


# ==========================================
# AUTENTICACIÓN
# ==========================================
def autenticar_usuario(correo, contrasena):
    """
    Consulta la tabla 'login' para validar credenciales humanas.
    Se utiliza una conexión con usuario 'login' (solo lectura en tabla login).
    """
    conn = get_db_connection("login")
    if not conn:
        return None

    cursor = conn.cursor(dictionary=True)
    try:
        sql = "SELECT correo, rol FROM login WHERE correo = %s AND contrasena = %s"
        cursor.execute(sql, (correo, contrasena))
        usuario = cursor.fetchone()
        return usuario
    except mysql.connector.Error as err:
        print(f"[ERROR SQL en Login]: {err}")
        return None
    finally:
        cursor.close()
        conn.close()


# ==========================================
# ABM DE TORNEOS
# ==========================================
def menu_abm_torneos():
    while True:
        print("\n" + "-" * 40)
        print("  ABM DE TORNEOS")
        print("-" * 40)
        print("1. Crear torneo")
        print("2. Modificar / Actualizar torneo")
        print("3. Eliminar / Dar de baja torneo")
        print("4. Obtener / Listar torneos")
        print("5. Consultar torneo por ID")
        print("0. Volver")

        opcion = input("\nSeleccione una opción: ").strip()

        if opcion == "0":
            break

        try:
            if opcion == "1":
                print("\n--- CREAR TORNEO ---")
                print("(Escriba '0' o 'cancelar' en cualquier campo para volver)")
                nombre = pedir_input("Nombre del torneo: ")
                anio = pedir_int("Año (>= 2026): ")
                semestre = pedir_int("Semestre (1 o 2): ")
                fecha_inicio = pedir_input("Fecha de inicio (YYYY-MM-DD): ")
                fecha_fin = pedir_input("Fecha de fin (YYYY-MM-DD): ")
                estado = pedir_input("Estado (inscripción/en curso/finalizado) [inscripción]: ", obligatorio=False) or "inscripción"
                resultado = crear_torneo(nombre, anio, semestre, fecha_inicio, fecha_fin, estado)
                mostrar_resultado(resultado)

            elif opcion == "2":
                print("\n--- MODIFICAR / ACTUALIZAR TORNEO ---")
                print("(Escriba '0' o 'cancelar' para volver)")
                id_torneo = pedir_int("ID del torneo a actualizar: ")
                print("(Deje vacío los campos que no desea modificar)")
                nombre = pedir_input("Nuevo nombre: ", obligatorio=False)
                anio = pedir_int("Nuevo año: ", obligatorio=False)
                semestre = pedir_int("Nuevo semestre: ", obligatorio=False)
                fecha_inicio = pedir_input("Nueva fecha de inicio (YYYY-MM-DD): ", obligatorio=False)
                fecha_fin = pedir_input("Nueva fecha de fin (YYYY-MM-DD): ", obligatorio=False)
                estado = pedir_input("Nuevo estado (inscripción/en curso/finalizado): ", obligatorio=False)
                resultado = actualizar_torneo(id_torneo, nombre, anio, semestre, fecha_inicio, fecha_fin, estado)
                mostrar_resultado(resultado)

            elif opcion == "3":
                print("\n--- ELIMINAR / DAR DE BAJA TORNEO ---")
                print("(Escriba '0' o 'cancelar' para volver)")
                id_torneo = pedir_int("ID del torneo a eliminar: ")
                if pedir_confirmacion(f"¿Confirma eliminar el torneo {id_torneo}? (s/n): "):
                    resultado = eliminar_torneo(id_torneo)
                    mostrar_resultado(resultado)
                else:
                    print("\n[i] Operación cancelada.")

            elif opcion == "4":
                print("\n--- LISTAR TORNEOS ---")
                resultado = obtener_torneos()
                mostrar_resultado(resultado)

            elif opcion == "5":
                print("\n--- CONSULTAR TORNEO POR ID ---")
                print("(Escriba '0' o 'cancelar' para volver)")
                id_torneo = pedir_int("ID del torneo a consultar: ")
                resultado = obtener_torneo(id_torneo)
                mostrar_resultado(resultado)

            else:
                print("[!] Opción no válida.")

        except OperacionCancelada:
            print("\n[i] Operación cancelada. Regresando a la pantalla anterior...")
        except ValueError:
            print("\n[X] Error: Fecha inválida. Use el formato YYYY-MM-DD.")


# ==========================================
# ABM DE USUARIOS / LOGINS
# ==========================================
def menu_abm_logins():
    while True:
        print("\n" + "-" * 40)
        print("  ABM DE USUARIOS (LOGINS)")
        print("-" * 40)
        print("1. Crear usuario")
        print("2. Modificar / Actualizar usuario")
        print("3. Eliminar / Dar de baja usuario")
        print("4. Obtener / Listar usuarios")
        print("0. Volver")

        opcion = input("\nSeleccione una opción: ").strip()

        if opcion == "0":
            break

        try:
            if opcion == "1":
                print("\n--- CREAR USUARIO ---")
                print("(Escriba '0' o 'cancelar' en cualquier campo para volver)")
                correo = pedir_input("Correo electrónico: ")
                contrasena = pedir_input("Contraseña: ")
                rol = pedir_input("Rol (administrador/planillero): ").lower()
                resultado = crear_usuario(correo, contrasena, rol)
                mostrar_resultado(resultado)

            elif opcion == "2":
                print("\n--- MODIFICAR / ACTUALIZAR USUARIO ---")
                print("(Escriba '0' o 'cancelar' para volver)")
                correo = pedir_input("Correo del usuario a actualizar: ")
                print("(Deje vacío los campos que no desea modificar)")
                nueva_contrasena = pedir_input("Nueva contraseña: ", obligatorio=False)
                nuevo_rol = pedir_input("Nuevo rol (administrador/planillero): ", obligatorio=False)
                if nuevo_rol:
                    nuevo_rol = nuevo_rol.lower()
                resultado = actualizar_usuario(correo, nueva_contrasena, nuevo_rol)
                mostrar_resultado(resultado)

            elif opcion == "3":
                print("\n--- ELIMINAR / DAR DE BAJA USUARIO ---")
                print("(Escriba '0' o 'cancelar' para volver)")
                correo = pedir_input("Correo del usuario a eliminar: ")
                if pedir_confirmacion(f"¿Confirma eliminar al usuario {correo}? (s/n): "):
                    resultado = eliminar_usuario(correo)
                    mostrar_resultado(resultado)
                else:
                    print("\n[i] Operación cancelada.")

            elif opcion == "4":
                print("\n--- LISTAR USUARIOS ---")
                resultado = obtener_usuarios()
                mostrar_resultado(resultado)

            else:
                print("[!] Opción no válida.")

        except OperacionCancelada:
            print("\n[i] Operación cancelada. Regresando a la pantalla anterior...")


# ==========================================
# ABM DE CANCHAS
# ==========================================
def menu_abm_canchas():
    while True:
        print("\n" + "-" * 40)
        print("  ABM DE CANCHAS")
        print("-" * 40)
        print("1. Crear cancha")
        print("2. Modificar / Actualizar cancha")
        print("3. Eliminar / Dar de baja cancha")
        print("4. Obtener / Listar canchas")
        print("0. Volver")

        opcion = input("\nSeleccione una opción: ").strip()

        if opcion == "0":
            break

        try:
            if opcion == "1":
                print("\n--- CREAR CANCHA ---")
                print("(Escriba '0' o 'cancelar' en cualquier campo para volver)")
                nombre = pedir_input("Nombre de la cancha: ")
                id_complejo = pedir_int("ID del complejo deportivo: ")
                superficie = pedir_input("Superficie (sintetico/parquet): ").lower()
                techada_str = pedir_input("¿Es techada? (s/n): ").lower()
                techada = 1 if techada_str in ("s", "si", "sí", "1") else 0
                resultado = crear_cancha(nombre, id_complejo, superficie, techada)
                mostrar_resultado(resultado)

            elif opcion == "2":
                print("\n--- MODIFICAR / ACTUALIZAR CANCHA ---")
                print("(Escriba '0' o 'cancelar' para volver)")
                nombre = pedir_input("Nombre de la cancha: ")
                id_complejo = pedir_int("ID del complejo deportivo: ")
                print("(Deje vacío los campos que no desea modificar)")
                nueva_superficie = pedir_input("Nueva superficie (sintetico/parquet): ", obligatorio=False)
                if nueva_superficie:
                    nueva_superficie = nueva_superficie.lower()
                nueva_techada_str = pedir_input("¿Es techada? (s/n, vacío=no cambiar): ", obligatorio=False)
                nueva_techada = None
                if nueva_techada_str:
                    nueva_techada = 1 if nueva_techada_str.lower() in ("s", "si", "sí", "1") else 0
                resultado = actualizar_cancha(nombre, id_complejo, nueva_superficie, nueva_techada)
                mostrar_resultado(resultado)

            elif opcion == "3":
                print("\n--- ELIMINAR / DAR DE BAJA CANCHA ---")
                print("(Escriba '0' o 'cancelar' para volver)")
                nombre = pedir_input("Nombre de la cancha: ")
                id_complejo = pedir_int("ID del complejo deportivo: ")
                if pedir_confirmacion(f"¿Confirma eliminar la cancha '{nombre}' del complejo {id_complejo}? (s/n): "):
                    resultado = eliminar_cancha(nombre, id_complejo)
                    mostrar_resultado(resultado)
                else:
                    print("\n[i] Operación cancelada.")

            elif opcion == "4":
                print("\n--- LISTAR CANCHAS ---")
                id_complejo = pedir_int("Filtrar por ID de complejo (vacío=todas): ", obligatorio=False)
                resultado = obtener_canchas(id_complejo)
                mostrar_resultado(resultado)

            else:
                print("[!] Opción no válida.")

        except OperacionCancelada:
            print("\n[i] Operación cancelada. Regresando a la pantalla anterior...")


# ==========================================
# ABM DE COMPLEJOS DEPORTIVOS
# ==========================================
def menu_abm_complejos():
    while True:
        print("\n" + "-" * 40)
        print("  ABM DE COMPLEJOS DEPORTIVOS")
        print("-" * 40)
        print("1. Crear complejo")
        print("2. Modificar / Actualizar complejo")
        print("3. Eliminar / Dar de baja complejo")
        print("4. Obtener / Listar complejos")
        print("5. Consultar complejo por ID")
        print("0. Volver")

        opcion = input("\nSeleccione una opción: ").strip()

        if opcion == "0":
            break

        try:
            if opcion == "1":
                print("\n--- CREAR COMPLEJO ---")
                print("(Escriba '0' o 'cancelar' en cualquier campo para volver)")
                nombre = pedir_input("Nombre del complejo: ")
                direccion = pedir_input("Dirección: ")
                departamento = pedir_input("Departamento: ")
                resultado = crear_complejo(nombre, direccion, departamento)
                mostrar_resultado(resultado)

            elif opcion == "2":
                print("\n--- MODIFICAR / ACTUALIZAR COMPLEJO ---")
                print("(Escriba '0' o 'cancelar' para volver)")
                id_complejo = pedir_int("ID del complejo a actualizar: ")
                print("(Deje vacío los campos que no desea modificar)")
                nombre = pedir_input("Nuevo nombre: ", obligatorio=False)
                direccion = pedir_input("Nueva dirección: ", obligatorio=False)
                departamento = pedir_input("Nuevo departamento: ", obligatorio=False)
                resultado = actualizar_complejo(id_complejo, nombre, direccion, departamento)
                mostrar_resultado(resultado)

            elif opcion == "3":
                print("\n--- ELIMINAR / DAR DE BAJA COMPLEJO ---")
                print("(Escriba '0' o 'cancelar' para volver)")
                id_complejo = pedir_int("ID del complejo a eliminar: ")
                if pedir_confirmacion(f"¿Confirma eliminar el complejo {id_complejo}? (s/n): "):
                    resultado = eliminar_complejo(id_complejo)
                    mostrar_resultado(resultado)
                else:
                    print("\n[i] Operación cancelada.")

            elif opcion == "4":
                print("\n--- LISTAR COMPLEJOS ---")
                resultado = obtener_complejos()
                mostrar_resultado(resultado)

            elif opcion == "5":
                print("\n--- CONSULTAR COMPLEJO POR ID ---")
                print("(Escriba '0' o 'cancelar' para volver)")
                id_complejo = pedir_int("ID del complejo: ")
                resultado = obtener_complejo(id_complejo)
                mostrar_resultado(resultado)

            else:
                print("[!] Opción no válida.")

        except OperacionCancelada:
            print("\n[i] Operación cancelada. Regresando a la pantalla anterior...")


# ==========================================
# ABM DE EQUIPOS (POR TORNEO)
# ==========================================
def menu_abm_equipos(id_torneo):
    while True:
        print("\n" + "-" * 40)
        print(f"  ABM DE EQUIPOS (Torneo {id_torneo})")
        print("-" * 40)
        print("1. Crear equipo")
        print("2. Modificar / Actualizar equipo")
        print("3. Eliminar / Dar de baja equipo")
        print("4. Obtener / Listar equipos del torneo")
        print("5. Consultar equipo por ID")
        print("0. Volver")

        opcion = input("\nSeleccione una opción: ").strip()

        if opcion == "0":
            break

        try:
            if opcion == "1":
                print("\n--- CREAR EQUIPO ---")
                print("(Escriba '0' o 'cancelar' en cualquier campo para volver)")
                nombre = pedir_input("Nombre del equipo: ")
                id_facultad = pedir_int("ID de la facultad: ")
                ci_capitan = pedir_int("CI del capitán: ")
                resultado = crear_equipo(nombre, id_torneo, id_facultad, ci_capitan)
                mostrar_resultado(resultado)

            elif opcion == "2":
                print("\n--- MODIFICAR / ACTUALIZAR EQUIPO ---")
                print("(Escriba '0' o 'cancelar' para volver)")
                id_equipo = pedir_int("ID del equipo a actualizar: ")
                print("(Deje vacío los campos que no desea modificar)")
                nombre = pedir_input("Nuevo nombre: ", obligatorio=False)
                ci_capitan = pedir_int("Nuevo CI del capitán: ", obligatorio=False)
                resultado = actualizar_equipo(id_equipo, nombre, ci_capitan)
                mostrar_resultado(resultado)

            elif opcion == "3":
                print("\n--- ELIMINAR / DAR DE BAJA EQUIPO ---")
                print("(Escriba '0' o 'cancelar' para volver)")
                id_equipo = pedir_int("ID del equipo a eliminar: ")
                if pedir_confirmacion(f"¿Confirma eliminar el equipo {id_equipo}? (s/n): "):
                    resultado = eliminar_equipo(id_equipo)
                    mostrar_resultado(resultado)
                else:
                    print("\n[i] Operación cancelada.")

            elif opcion == "4":
                print(f"\n--- EQUIPOS DEL TORNEO {id_torneo} ---")
                resultado = obtener_equipos(id_torneo)
                mostrar_resultado(resultado)

            elif opcion == "5":
                print("\n--- CONSULTAR EQUIPO POR ID ---")
                print("(Escriba '0' o 'cancelar' para volver)")
                id_equipo = pedir_int("ID del equipo: ")
                resultado = obtener_equipo(id_equipo)
                mostrar_resultado(resultado)

            else:
                print("[!] Opción no válida.")

        except OperacionCancelada:
            print("\n[i] Operación cancelada. Regresando a la pantalla anterior...")


# ==========================================
# ABM DE INSCRIPCIONES (PLANTELES)
# ==========================================
def menu_abm_inscripciones(id_torneo):
    while True:
        print("\n" + "-" * 40)
        print(f"  ABM DE INSCRIPCIONES / PLANTELES (Torneo {id_torneo})")
        print("-" * 40)
        print("1. Inscribir jugador en equipo")
        print("2. Modificar dorsal / número de camiseta")
        print("3. Eliminar / Dar de baja jugador de equipo")
        print("4. Obtener / Ver plantel de un equipo")
        print("0. Volver")

        opcion = input("\nSeleccione una opción: ").strip()

        if opcion == "0":
            break

        try:
            if opcion == "1":
                print("\n--- INSCRIBIR JUGADOR EN EQUIPO ---")
                print("(Escriba '0' o 'cancelar' en cualquier campo para volver)")
                id_equipo = pedir_int("ID del equipo: ")
                ci_jugador = pedir_int("CI del jugador: ")
                numero_camiseta = pedir_int("Número de camiseta (1-99): ")
                resultado = inscribir_jugador_equipo(id_equipo, ci_jugador, id_torneo, numero_camiseta)
                mostrar_resultado(resultado)

            elif opcion == "2":
                print("\n--- MODIFICAR DORSAL DE JUGADOR ---")
                print("(Escriba '0' o 'cancelar' para volver)")
                id_equipo = pedir_int("ID del equipo: ")
                ci_jugador = pedir_int("CI del jugador: ")
                nuevo_numero = pedir_int("Nuevo número de camiseta (1-99): ")
                resultado = modificar_camiseta_jugador(id_equipo, ci_jugador, id_torneo, nuevo_numero)
                mostrar_resultado(resultado)

            elif opcion == "3":
                print("\n--- ELIMINAR / DAR DE BAJA JUGADOR DE EQUIPO ---")
                print("(Escriba '0' o 'cancelar' para volver)")
                id_equipo = pedir_int("ID del equipo: ")
                ci_jugador = pedir_int("CI del jugador: ")
                if pedir_confirmacion(f"¿Confirma dar de baja al jugador {ci_jugador} del equipo {id_equipo}? (s/n): "):
                    resultado = eliminar_jugador_equipo(id_equipo, ci_jugador, id_torneo)
                    mostrar_resultado(resultado)
                else:
                    print("\n[i] Operación cancelada.")

            elif opcion == "4":
                print("\n--- VER PLANTEL DE UN EQUIPO ---")
                print("(Escriba '0' o 'cancelar' para volver)")
                id_equipo = pedir_int("ID del equipo: ")
                resultado = obtener_plantel(id_equipo, id_torneo)
                mostrar_resultado(resultado)

            else:
                print("[!] Opción no válida.")

        except OperacionCancelada:
            print("\n[i] Operación cancelada. Regresando a la pantalla anterior...")


# ==========================================
# ABM DE FACULTADES
# ==========================================
def menu_abm_facultades():
    while True:
        print("\n" + "-" * 40)
        print("  ABM DE FACULTADES")
        print("-" * 40)
        print("1. Crear facultad")
        print("2. Modificar / Actualizar facultad")
        print("3. Eliminar / Dar de baja facultad")
        print("4. Obtener / Listar facultades")
        print("0. Volver")

        opcion = input("\nSeleccione una opción: ").strip()

        if opcion == "0":
            break

        try:
            if opcion == "1":
                print("\n--- CREAR FACULTAD ---")
                print("(Escriba '0' o 'cancelar' en cualquier campo para volver)")
                nombre = pedir_input("Nombre de la facultad: ")
                resultado = crear_facultad(nombre)
                mostrar_resultado(resultado)

            elif opcion == "2":
                print("\n--- MODIFICAR / ACTUALIZAR FACULTAD ---")
                print("(Escriba '0' o 'cancelar' para volver)")
                id_facultad = pedir_int("ID de la facultad a actualizar: ")
                nombre = pedir_input("Nuevo nombre: ")
                resultado = actualizar_facultad(id_facultad, nombre)
                mostrar_resultado(resultado)

            elif opcion == "3":
                print("\n--- ELIMINAR / DAR DE BAJA FACULTAD ---")
                print("(Escriba '0' o 'cancelar' para volver)")
                id_facultad = pedir_int("ID de la facultad a eliminar: ")
                if pedir_confirmacion(f"¿Confirma eliminar la facultad {id_facultad}? (s/n): "):
                    resultado = eliminar_facultad(id_facultad)
                    mostrar_resultado(resultado)
                else:
                    print("\n[i] Operación cancelada.")

            elif opcion == "4":
                print("\n--- LISTAR FACULTADES ---")
                resultado = obtener_facultades()
                mostrar_resultado(resultado)

            else:
                print("[!] Opción no válida.")

        except OperacionCancelada:
            print("\n[i] Operación cancelada. Regresando a la pantalla anterior...")


# ==========================================
# ABM DE GOLES (POR TORNEO)
# ==========================================
def menu_abm_goles(id_torneo):
    while True:
        print("\n" + "-" * 40)
        print(f"  ABM DE GOLES (Torneo {id_torneo})")
        print("-" * 40)
        print("1. Registrar gol")
        print("2. Modificar / Actualizar gol")
        print("3. Eliminar / Dar de baja gol")
        print("4. Obtener / Ver goles de un partido")
        print("0. Volver")

        opcion = input("\nSeleccione una opción: ").strip()

        if opcion == "0":
            break

        try:
            if opcion == "1":
                print("\n--- REGISTRAR GOL ---")
                print("(Escriba '0' o 'cancelar' en cualquier campo para volver)")
                id_partido = pedir_int("ID del partido: ")
                ci_jugador = pedir_int("CI del jugador: ")
                minuto = pedir_int("Minuto del gol (1-60): ")
                autogol_str = pedir_input("¿Es autogol? (s/n): ").lower()
                autogol = autogol_str in ("s", "si", "sí", "1")
                resultado = registrar_gol(id_partido, ci_jugador, minuto, autogol)
                mostrar_resultado(resultado)

            elif opcion == "2":
                print("\n--- MODIFICAR / ACTUALIZAR GOL ---")
                print("(Escriba '0' o 'cancelar' para volver)")
                id_gol = pedir_int("ID del gol a modificar: ")
                print("(Deje vacío los campos que no desea modificar)")
                nuevo_minuto = pedir_int("Nuevo minuto (1-60): ", obligatorio=False)
                nuevo_autogol_str = pedir_input("¿Es autogol? (s/n, vacío=no cambiar): ", obligatorio=False)
                nuevo_autogol = None
                if nuevo_autogol_str:
                    nuevo_autogol = nuevo_autogol_str.lower() in ("s", "si", "sí", "1")
                nueva_ci = pedir_int("Nuevo CI del jugador: ", obligatorio=False)
                resultado = modificar_gol(id_gol, nuevo_minuto, nuevo_autogol, nueva_ci)
                mostrar_resultado(resultado)

            elif opcion == "3":
                print("\n--- ELIMINAR / DAR DE BAJA GOL ---")
                print("(Escriba '0' o 'cancelar' para volver)")
                id_gol = pedir_int("ID del gol a eliminar: ")
                if pedir_confirmacion(f"¿Confirma eliminar el gol {id_gol}? (s/n): "):
                    resultado = eliminar_gol(id_gol)
                    mostrar_resultado(resultado)
                else:
                    print("\n[i] Operación cancelada.")

            elif opcion == "4":
                print("\n--- VER GOLES DE UN PARTIDO ---")
                print("(Escriba '0' o 'cancelar' para volver)")
                id_partido = pedir_int("ID del partido: ")
                resultado = obtener_goles_partido(id_partido)
                mostrar_resultado(resultado)

            else:
                print("[!] Opción no válida.")

        except OperacionCancelada:
            print("\n[i] Operación cancelada. Regresando a la pantalla anterior...")


# ==========================================
# ABM DE JUGADORES
# ==========================================
def menu_abm_jugadores():
    while True:
        print("\n" + "-" * 40)
        print("  ABM DE JUGADORES")
        print("-" * 40)
        print("1. Crear jugador")
        print("2. Modificar / Actualizar jugador")
        print("3. Eliminar / Dar de baja jugador")
        print("4. Obtener / Listar jugadores")
        print("5. Consultar jugador por CI")
        print("0. Volver")

        opcion = input("\nSeleccione una opción: ").strip()

        if opcion == "0":
            break

        try:
            if opcion == "1":
                print("\n--- CREAR JUGADOR ---")
                print("(Escriba '0' o 'cancelar' en cualquier campo para volver)")
                ci = pedir_int("CI del jugador (10000000-60000000): ")
                nombre = pedir_input("Nombre: ")
                apellido = pedir_input("Apellido: ")
                email = pedir_input("Email: ")
                fecha_nacimiento = pedir_input("Fecha de nacimiento (YYYY-MM-DD): ")
                id_facultad = pedir_int("ID de la facultad: ")
                tipo = pedir_input("Tipo (grado/postgrado/docente/funcionario): ").lower()
                resultado = crear_jugador(ci, nombre, apellido, email, fecha_nacimiento, id_facultad, tipo)
                mostrar_resultado(resultado)

            elif opcion == "2":
                print("\n--- MODIFICAR / ACTUALIZAR JUGADOR ---")
                print("(Escriba '0' o 'cancelar' para volver)")
                ci = pedir_int("CI del jugador a actualizar: ")
                print("(Deje vacío los campos que no desea modificar)")
                nombre = pedir_input("Nuevo nombre: ", obligatorio=False)
                apellido = pedir_input("Nuevo apellido: ", obligatorio=False)
                email = pedir_input("Nuevo email: ", obligatorio=False)
                fecha_nacimiento = pedir_input("Nueva fecha de nacimiento (YYYY-MM-DD): ", obligatorio=False)
                id_facultad = pedir_int("Nuevo ID de facultad: ", obligatorio=False)
                tipo = pedir_input("Nuevo tipo (grado/postgrado/docente/funcionario): ", obligatorio=False)
                if tipo:
                    tipo = tipo.lower()
                resultado = actualizar_jugador(ci, nombre, apellido, email, fecha_nacimiento, id_facultad, tipo)
                mostrar_resultado(resultado)

            elif opcion == "3":
                print("\n--- ELIMINAR / DAR DE BAJA JUGADOR ---")
                print("(Escriba '0' o 'cancelar' para volver)")
                ci = pedir_int("CI del jugador a eliminar: ")
                if pedir_confirmacion(f"¿Confirma eliminar al jugador con CI {ci}? (s/n): "):
                    resultado = eliminar_jugador(ci)
                    mostrar_resultado(resultado)
                else:
                    print("\n[i] Operación cancelada.")

            elif opcion == "4":
                print("\n--- LISTAR JUGADORES ---")
                id_facultad = pedir_int("ID de facultad (vacío=todos): ", obligatorio=False)
                resultado = obtener_jugadores(id_facultad)
                mostrar_resultado(resultado)

            elif opcion == "5":
                print("\n--- CONSULTAR JUGADOR POR CI ---")
                print("(Escriba '0' o 'cancelar' para volver)")
                ci = pedir_int("CI del jugador: ")
                resultado = obtener_jugador(ci)
                mostrar_resultado(resultado)

            else:
                print("[!] Opción no válida.")

        except OperacionCancelada:
            print("\n[i] Operación cancelada. Regresando a la pantalla anterior...")


# ==========================================
# ABM DE PARTIDOS (POR TORNEO)
# ==========================================
def menu_abm_partidos(id_torneo):
    while True:
        print("\n" + "-" * 40)
        print(f"  ABM DE PARTIDOS (Torneo {id_torneo})")
        print("-" * 40)
        print("1. Programar partido")
        print("2. Modificar / Postergar partido")
        print("3. Marcar partido como jugado")
        print("4. Cancelar partido")
        print("5. Eliminar / Dar de baja partido")
        print("6. Obtener / Listar partidos del torneo")
        print("0. Volver")

        opcion = input("\nSeleccione una opción: ").strip()

        if opcion == "0":
            break

        try:
            if opcion == "1":
                print("\n--- PROGRAMAR PARTIDO ---")
                print("(Escriba '0' o 'cancelar' en cualquier campo para volver)")
                numero_fecha = pedir_int("Número de fecha: ")
                id_equipo_local = pedir_int("ID equipo local: ")
                id_equipo_visitante = pedir_int("ID equipo visitante: ")
                dia = pedir_input("Fecha del partido (YYYY-MM-DD): ")
                id_turno = pedir_int("ID del turno: ")
                nombre_cancha = pedir_input("Nombre de la cancha: ")
                id_complejo = pedir_int("ID del complejo deportivo: ")
                resultado = programar_partido(
                    id_torneo, numero_fecha, id_equipo_local, id_equipo_visitante,
                    dia, id_turno, nombre_cancha, id_complejo
                )
                mostrar_resultado(resultado)

            elif opcion == "2":
                print("\n--- MODIFICAR / POSTERGAR PARTIDO ---")
                print("(Escriba '0' o 'cancelar' para volver)")
                id_partido = pedir_int("ID del partido a postergar/reprogramar: ")
                nueva_fecha = pedir_input("Nueva fecha (YYYY-MM-DD): ")
                nueva_cancha = pedir_input("Nuevo nombre de cancha: ")
                nuevo_id_turno = pedir_int("Nuevo ID de turno (vacío=mantener actual): ", obligatorio=False)
                nuevo_id_complejo = pedir_int("Nuevo ID de complejo (vacío=mantener actual): ", obligatorio=False)
                resultado = postergar_partido(id_partido, nueva_fecha, nueva_cancha, nuevo_id_turno, nuevo_id_complejo)
                mostrar_resultado(resultado)

            elif opcion == "3":
                print("\n--- MARCAR PARTIDO COMO JUGADO ---")
                print("(Escriba '0' o 'cancelar' para volver)")
                id_partido = pedir_int("ID del partido a marcar como jugado: ")
                resultado = marcar_jugado(id_partido)
                mostrar_resultado(resultado)

            elif opcion == "4":
                print("\n--- CANCELAR PARTIDO ---")
                print("(Escriba '0' o 'cancelar' para volver)")
                id_partido = pedir_int("ID del partido a cancelar: ")
                if pedir_confirmacion(f"¿Confirma cancelar el partido {id_partido}? (s/n): "):
                    resultado = cancelar_partido(id_partido)
                    mostrar_resultado(resultado)
                else:
                    print("\n[i] Operación cancelada.")

            elif opcion == "5":
                print("\n--- ELIMINAR / DAR DE BAJA PARTIDO ---")
                print("(Escriba '0' o 'cancelar' para volver)")
                id_partido = pedir_int("ID del partido a eliminar: ")
                if pedir_confirmacion(f"¿Confirma eliminar permanentemente el partido {id_partido}? (s/n): "):
                    resultado = eliminar_partido(id_partido)
                    mostrar_resultado(resultado)
                else:
                    print("\n[i] Operación cancelada.")

            elif opcion == "6":
                print(f"\n--- PARTIDOS DEL TORNEO {id_torneo} ---")
                dia_filtro = pedir_input("Filtrar por fecha (YYYY-MM-DD, vacío=todas): ", obligatorio=False)
                estado_filtro = pedir_input("Filtrar por estado (programado/jugado/postergado/cancelado, vacío=todos): ", obligatorio=False)
                resultado = obtener_partidos(id_torneo=id_torneo, dia=dia_filtro, estado=estado_filtro)
                mostrar_resultado(resultado)

            else:
                print("[!] Opción no válida.")

        except OperacionCancelada:
            print("\n[i] Operación cancelada. Regresando a la pantalla anterior...")


# ==========================================
# ABM DE PLANILLAS DE PARTIDO
# ==========================================
def menu_abm_planillas(id_torneo):
    while True:
        print("\n" + "-" * 40)
        print(f"  ABM DE PLANILLAS (Torneo {id_torneo})")
        print("-" * 40)
        print("1. Registrar jugador en planilla")
        print("2. Borrar / Dar de baja jugador de planilla")
        print("3. Obtener / Ver planilla de un partido")
        print("0. Volver")

        opcion = input("\nSeleccione una opción: ").strip()

        if opcion == "0":
            break

        try:
            if opcion == "1":
                print("\n--- REGISTRAR JUGADOR EN PLANILLA ---")
                print("(Escriba '0' o 'cancelar' en cualquier campo para volver)")
                id_partido = pedir_int("ID del partido: ")
                ci_jugador = pedir_int("CI del jugador: ")
                id_equipo = pedir_int("ID del equipo: ")
                resultado = registrar_planilla_jugador(id_partido, ci_jugador, id_equipo)
                mostrar_resultado(resultado)

            elif opcion == "2":
                print("\n--- BORRAR JUGADOR DE PLANILLA ---")
                print("(Escriba '0' o 'cancelar' para volver)")
                id_partido = pedir_int("ID del partido: ")
                ci_jugador = pedir_int("CI del jugador: ")
                if pedir_confirmacion(f"¿Confirma eliminar al jugador {ci_jugador} de la planilla del partido {id_partido}? (s/n): "):
                    resultado = borrar_planilla_jugador(id_partido, ci_jugador)
                    mostrar_resultado(resultado)
                else:
                    print("\n[i] Operación cancelada.")

            elif opcion == "3":
                print("\n--- VER PLANILLA DE UN PARTIDO ---")
                print("(Escriba '0' o 'cancelar' para volver)")
                id_partido = pedir_int("ID del partido: ")
                resultado = obtener_planilla_partido(id_partido)
                mostrar_resultado(resultado)

            else:
                print("[!] Opción no válida.")

        except OperacionCancelada:
            print("\n[i] Operación cancelada. Regresando a la pantalla anterior...")


# ==========================================
# ABM DE SANCIONES (POR TORNEO)
# ==========================================
def menu_abm_sanciones(id_torneo):
    while True:
        print("\n" + "-" * 40)
        print(f"  ABM DE SANCIONES (Torneo {id_torneo})")
        print("-" * 40)
        print("1. Crear sanción")
        print("2. Modificar / Actualizar sanción")
        print("3. Eliminar / Dar de baja sanción")
        print("4. Obtener / Listar sanciones del torneo")
        print("0. Volver")

        opcion = input("\nSeleccione una opción: ").strip()

        if opcion == "0":
            break

        try:
            if opcion == "1":
                print("\n--- CREAR SANCIÓN ---")
                print("(Escriba '0' o 'cancelar' en cualquier campo para volver)")
                ci_jugador = pedir_int("CI del jugador: ")
                motivo = pedir_input("Motivo (roja/acumulación de amarillas/disciplinaria): ").lower()
                numero_fecha_inicio = pedir_int("Número de fecha de inicio de sanción: ")
                cantidad_fechas = pedir_int("Cantidad de fechas de sanción [1]: ", obligatorio=False) or 1
                resultado = crear_sancion(ci_jugador, id_torneo, motivo, numero_fecha_inicio, cantidad_fechas)
                mostrar_resultado(resultado)

            elif opcion == "2":
                print("\n--- MODIFICAR / ACTUALIZAR SANCIÓN ---")
                print("(Escriba '0' o 'cancelar' para volver)")
                id_sancion = pedir_int("ID de la sanción a actualizar: ")
                print("(Deje vacío los campos que no desea modificar)")
                motivo = pedir_input("Nuevo motivo (roja/acumulación de amarillas/disciplinaria): ", obligatorio=False)
                if motivo:
                    motivo = motivo.lower()
                numero_fecha_inicio = pedir_int("Nuevo número de fecha inicio: ", obligatorio=False)
                cantidad_fechas = pedir_int("Nueva cantidad de fechas: ", obligatorio=False)
                resultado = actualizar_sancion(id_sancion, motivo, numero_fecha_inicio, cantidad_fechas)
                mostrar_resultado(resultado)

            elif opcion == "3":
                print("\n--- ELIMINAR / DAR DE BAJA SANCIÓN ---")
                print("(Escriba '0' o 'cancelar' para volver)")
                id_sancion = pedir_int("ID de la sanción a eliminar: ")
                if pedir_confirmacion(f"¿Confirma eliminar la sanción {id_sancion}? (s/n): "):
                    resultado = eliminar_sancion(id_sancion)
                    mostrar_resultado(resultado)
                else:
                    print("\n[i] Operación cancelada.")

            elif opcion == "4":
                print(f"\n--- SANCIONES DEL TORNEO {id_torneo} ---")
                ci_jugador = pedir_int("Filtrar por CI de jugador (vacío=todas): ", obligatorio=False)
                resultado = obtener_sanciones(id_torneo, ci_jugador)
                mostrar_resultado(resultado)

            else:
                print("[!] Opción no válida.")

        except OperacionCancelada:
            print("\n[i] Operación cancelada. Regresando a la pantalla anterior...")


# ==========================================
# ABM DE TARJETAS (POR TORNEO)
# ==========================================
def menu_abm_tarjetas(id_torneo):
    while True:
        print("\n" + "-" * 40)
        print(f"  ABM DE TARJETAS (Torneo {id_torneo})")
        print("-" * 40)
        print("1. Registrar tarjeta")
        print("2. Modificar / Actualizar tarjeta (minuto)")
        print("3. Eliminar / Dar de baja tarjeta")
        print("4. Obtener / Ver tarjetas de un partido")
        print("0. Volver")

        opcion = input("\nSeleccione una opción: ").strip()

        if opcion == "0":
            break

        try:
            if opcion == "1":
                print("\n--- REGISTRAR TARJETA ---")
                print("(Escriba '0' o 'cancelar' en cualquier campo para volver)")
                id_partido = pedir_int("ID del partido: ")
                ci_jugador = pedir_int("CI del jugador: ")
                minuto = pedir_int("Minuto (1-60): ")
                color = pedir_input("Color (amarilla/roja): ").lower()
                resultado = registrar_tarjeta(id_partido, ci_jugador, minuto, color)
                mostrar_resultado(resultado)

            elif opcion == "2":
                print("\n--- MODIFICAR TARJETA ---")
                print("(Escriba '0' o 'cancelar' para volver)")
                id_tarjeta = pedir_int("ID de la tarjeta a modificar: ")
                nuevo_minuto = pedir_int("Nuevo minuto (1-60): ")
                resultado = modificar_tarjeta(id_tarjeta, nuevo_minuto)
                mostrar_resultado(resultado)

            elif opcion == "3":
                print("\n--- ELIMINAR / DAR DE BAJA TARJETA ---")
                print("(Escriba '0' o 'cancelar' para volver)")
                id_tarjeta = pedir_int("ID de la tarjeta a eliminar: ")
                if pedir_confirmacion(f"¿Confirma eliminar la tarjeta {id_tarjeta}? (s/n): "):
                    resultado = eliminar_tarjeta(id_tarjeta)
                    mostrar_resultado(resultado)
                else:
                    print("\n[i] Operación cancelada.")

            elif opcion == "4":
                print("\n--- VER TARJETAS DE UN PARTIDO ---")
                print("(Escriba '0' o 'cancelar' para volver)")
                id_partido = pedir_int("ID del partido: ")
                resultado = obtener_tarjetas_partido(id_partido)
                mostrar_resultado(resultado)

            else:
                print("[!] Opción no válida.")

        except OperacionCancelada:
            print("\n[i] Operación cancelada. Regresando a la pantalla anterior...")


# ==========================================
# ABM DE TURNOS
# ==========================================
def menu_abm_turnos():
    while True:
        print("\n" + "-" * 40)
        print("  ABM DE TURNOS")
        print("-" * 40)
        print("1. Crear turno")
        print("2. Modificar / Actualizar turno")
        print("3. Eliminar / Dar de baja turno")
        print("4. Obtener / Listar turnos")
        print("0. Volver")

        opcion = input("\nSeleccione una opción: ").strip()

        if opcion == "0":
            break

        try:
            if opcion == "1":
                print("\n--- CREAR TURNO ---")
                print("(Escriba '0' o 'cancelar' en cualquier campo para volver)")
                hora_inicio = pedir_input("Hora de inicio (HH:MM o HH:MM:SS): ")
                hora_fin = pedir_input("Hora de fin (HH:MM o HH:MM:SS): ")
                resultado = crear_turno(hora_inicio, hora_fin)
                mostrar_resultado(resultado)

            elif opcion == "2":
                print("\n--- MODIFICAR / ACTUALIZAR TURNO ---")
                print("(Escriba '0' o 'cancelar' para volver)")
                id_turno = pedir_int("ID del turno a actualizar: ")
                hora_inicio = pedir_input("Nueva hora de inicio (HH:MM o HH:MM:SS): ")
                hora_fin = pedir_input("Nueva hora de fin (HH:MM o HH:MM:SS): ")
                resultado = actualizar_turno(id_turno, hora_inicio, hora_fin)
                mostrar_resultado(resultado)

            elif opcion == "3":
                print("\n--- ELIMINAR / DAR DE BAJA TURNO ---")
                print("(Escriba '0' o 'cancelar' para volver)")
                id_turno = pedir_int("ID del turno a eliminar: ")
                if pedir_confirmacion(f"¿Confirma eliminar el turno {id_turno}? (s/n): "):
                    resultado = eliminar_turno(id_turno)
                    mostrar_resultado(resultado)
                else:
                    print("\n[i] Operación cancelada.")

            elif opcion == "4":
                print("\n--- LISTAR TURNOS ---")
                resultado = obtener_turnos()
                mostrar_resultado(resultado)

            else:
                print("[!] Opción no válida.")

        except OperacionCancelada:
            print("\n[i] Operación cancelada. Regresando a la pantalla anterior...")


# ==========================================
# MENÚ DE REPORTES (POR TORNEO)
# ==========================================
def menu_reportes(id_torneo):
    while True:
        print("\n" + "-" * 40)
        print(f"  REPORTES (Torneo {id_torneo})")
        print("-" * 40)
        print("1.  Tabla de posiciones")
        print("2.  Tabla de goleadores")
        print("3.  Tabla de fair play")
        print("4.  Promedio de goles por fecha")
        print("5.  Promedio de goles por edición (todos los torneos)")
        print("6.  Canchas y turnos")
        print("7.  Jugadores por facultad")
        print("8.  Jugadores sin figurar")
        print("9.  Sanciones por equipo")
        print("10. Porcentaje de partidos jugados")
        print("11. Resultados")
        print("12. Tarjetas por jugador (todos los torneos)")
        print("13. Tarjetas por jugador en el torneo")
        print("14. Porcentaje de participación")
        print("0.  Volver")

        opcion = input("\nSeleccione una opción: ").strip()

        if opcion == "1":
            mostrar_resultado(obtener_tabla_posiciones(id_torneo))
        elif opcion == "2":
            mostrar_resultado(obtener_tabla_goleadores(id_torneo))
        elif opcion == "3":
            mostrar_resultado(obtener_tabla_fair_play(id_torneo))
        elif opcion == "4":
            mostrar_resultado(obtener_promedio_goles_fecha(id_torneo))
        elif opcion == "5":
            mostrar_resultado(obtener_promedio_goles_edicion())
        elif opcion == "6":
            mostrar_resultado(obtener_canchas_turnos())
        elif opcion == "7":
            mostrar_resultado(obtener_jugadores_facultad(id_torneo))
        elif opcion == "8":
            mostrar_resultado(obtener_sin_figurar(id_torneo))
        elif opcion == "9":
            mostrar_resultado(obtener_sanciones_equipo(id_torneo))
        elif opcion == "10":
            mostrar_resultado(obtener_porcentaje_jugados(id_torneo))
        elif opcion == "11":
            mostrar_resultado(obtener_resultados(id_torneo))
        elif opcion == "12":
            mostrar_resultado(obtener_tarjetas_jugador())
        elif opcion == "13":
            mostrar_resultado(obtener_tarjetas_jugador_torneo(id_torneo))
        elif opcion == "14":
            mostrar_resultado(obtener_porcentaje_participacion(id_torneo))
        elif opcion == "0":
            break
        else:
            print("[!] Opción no válida.")


# ==========================================
# MENÚ DENTRO DE UN TORNEO (ADMIN)
# ==========================================
def menu_torneo_admin(id_torneo, torneo_info=None):
    """
    Submenú de gestión completa de un torneo seleccionado.
    Ofrece ABMs de: canchas, complejos, equipos, inscripciones, facultades,
    goles, jugadores, partidos, planillas, sanciones, tarjetas, turnos y reportes.
    """
    if torneo_info and isinstance(torneo_info, dict):
        nombre_torneo = torneo_info.get("nombre", f"ID {id_torneo}")
    else:
        torneo = obtener_torneo(id_torneo)
        if not torneo or (isinstance(torneo, dict) and "error" in torneo):
            print(f"\n[X] Error: No existe un torneo con el ID {id_torneo}.")
            return
        nombre_torneo = torneo.get("nombre", f"ID {id_torneo}")

    while True:
        print("\n" + "=" * 55)
        print(f"  GESTIÓN DE TORNEO: {nombre_torneo} (ID: {id_torneo})")
        print("=" * 55)
        print("1.  ABM de Canchas")
        print("2.  ABM de Complejos Deportivos")
        print("3.  ABM de Equipos")
        print("4.  ABM de Inscripciones (Planteles)")
        print("5.  ABM de Facultades")
        print("6.  ABM de Goles")
        print("7.  ABM de Jugadores")
        print("8.  ABM de Partidos")
        print("9.  ABM de Planillas")
        print("10. ABM de Sanciones")
        print("11. ABM de Tarjetas")
        print("12. ABM de Turnos")
        print("13. Ver Reportes")
        print("0.  Volver al Menú Principal")

        opcion = input("\nSeleccione una opción: ").strip()

        if opcion == "1":
            menu_abm_canchas()
        elif opcion == "2":
            menu_abm_complejos()
        elif opcion == "3":
            menu_abm_equipos(id_torneo)
        elif opcion == "4":
            menu_abm_inscripciones(id_torneo)
        elif opcion == "5":
            menu_abm_facultades()
        elif opcion == "6":
            menu_abm_goles(id_torneo)
        elif opcion == "7":
            menu_abm_jugadores()
        elif opcion == "8":
            menu_abm_partidos(id_torneo)
        elif opcion == "9":
            menu_abm_planillas(id_torneo)
        elif opcion == "10":
            menu_abm_sanciones(id_torneo)
        elif opcion == "11":
            menu_abm_tarjetas(id_torneo)
        elif opcion == "12":
            menu_abm_turnos()
        elif opcion == "13":
            menu_reportes(id_torneo)
        elif opcion == "0":
            break
        else:
            print("[!] Opción no válida.")


# ==========================================
# SELECCIONAR TORNEO PARA TRABAJAR
# ==========================================
def seleccionar_y_trabajar_torneo():
    """
    Pregunta al administrador el ID del torneo en el que desea trabajar.
    Permite salir/volver al menú anterior escribiendo '0' o 'cancelar',
    o listar los torneos disponibles escribiendo '?' o 'listar'.
    """
    while True:
        print("\n" + "=" * 55)
        print("  SELECCIONAR TORNEO PARA TRABAJAR")
        print("  (Ingrese '0' o 'cancelar' para volver)")
        print("  (Ingrese '?' o 'listar' para ver torneos disponibles)")
        print("=" * 55)

        entrada = input("Ingrese el ID del torneo: ").strip()

        if entrada.lower() in PALABRAS_CANCELAR or entrada == "0":
            print("\n[i] Regresando al menú principal...")
            break

        if entrada in ("?", "listar", "ver"):
            print("\n--- TORNEOS DISPONIBLES ---")
            torneos = obtener_torneos()
            mostrar_resultado(torneos)
            continue

        try:
            id_torneo = int(entrada)
        except ValueError:
            print("[!] Debe ingresar un número de ID válido (o '?' para listar, '0' para volver).")
            continue

        torneo = obtener_torneo(id_torneo)
        if not torneo or (isinstance(torneo, dict) and "error" in torneo):
            print(f"\n[X] Error: No se encontró ningún torneo con el ID {id_torneo}.")
            continue

        menu_torneo_admin(id_torneo, torneo)
        break


# ==========================================
# MENÚ PRINCIPAL PARA ADMINISTRADORES
# ==========================================
def mostrar_menu_administrador(correo_usuario):
    """
    Menú principal del rol Administrador.
    Permite:
    1. Trabajar en un torneo (solicita el ID)
    2. ABM de Torneos
    3. ABM de Logins / Usuarios
    0. Cerrar Sesión
    """
    while True:
        print("\n" + "=" * 55)
        print(f"   PANEL DE ADMINISTRACIÓN (Sesión: {correo_usuario})")
        print("=" * 55)
        print("1. Trabajar en un torneo")
        print("2. ABM de Torneos")
        print("3. ABM de Logins (Usuarios)")
        print("0. Cerrar Sesión")

        opcion = input("\nSeleccione una opción: ").strip()

        if opcion == "1":
            seleccionar_y_trabajar_torneo()

        elif opcion == "2":
            menu_abm_torneos()

        elif opcion == "3":
            menu_abm_logins()

        elif opcion == "0":
            print("\nCerrando sesión de Administrador...")
            break
        else:
            print("[!] Opción no válida.")


# ==========================================
# MENÚ PARA PLANILLEROS (SIN OPCIONES DE ELIMINACIÓN)
# ==========================================
def menu_planillas_planillero(id_torneo):
    while True:
        print("\n" + "-" * 40)
        print(f"  PLANILLAS (Torneo {id_torneo})")
        print("-" * 40)
        print("1. Registrar jugador en planilla")
        print("2. Obtener / Ver planilla de un partido")
        print("0. Volver")

        opcion = input("\nSeleccione una opción: ").strip()

        if opcion == "0":
            break

        try:
            if opcion == "1":
                print("\n--- REGISTRAR JUGADOR EN PLANILLA ---")
                print("(Escriba '0' o 'cancelar' en cualquier campo para volver)")
                id_partido = pedir_int("ID del partido: ")
                ci_jugador = pedir_int("CI del jugador: ")
                id_equipo = pedir_int("ID del equipo: ")
                resultado = registrar_planilla_jugador(id_partido, ci_jugador, id_equipo)
                mostrar_resultado(resultado)

            elif opcion == "2":
                print("\n--- VER PLANILLA DE UN PARTIDO ---")
                print("(Escriba '0' o 'cancelar' para volver)")
                id_partido = pedir_int("ID del partido: ")
                resultado = obtener_planilla_partido(id_partido)
                mostrar_resultado(resultado)

            else:
                print("[!] Opción no válida.")

        except OperacionCancelada:
            print("\n[i] Operación cancelada. Regresando a la pantalla anterior...")


def menu_goles_planillero(id_torneo):
    while True:
        print("\n" + "-" * 40)
        print(f"  GOLES (Torneo {id_torneo})")
        print("-" * 40)
        print("1. Registrar gol")
        print("2. Modificar / Actualizar gol")
        print("3. Obtener / Ver goles de un partido")
        print("0. Volver")

        opcion = input("\nSeleccione una opción: ").strip()

        if opcion == "0":
            break

        try:
            if opcion == "1":
                print("\n--- REGISTRAR GOL ---")
                print("(Escriba '0' o 'cancelar' en cualquier campo para volver)")
                id_partido = pedir_int("ID del partido: ")
                ci_jugador = pedir_int("CI del jugador: ")
                minuto = pedir_int("Minuto del gol (1-60): ")
                autogol_str = pedir_input("¿Es autogol? (s/n): ").lower()
                autogol = autogol_str in ("s", "si", "sí", "1")
                resultado = registrar_gol(id_partido, ci_jugador, minuto, autogol)
                mostrar_resultado(resultado)

            elif opcion == "2":
                print("\n--- MODIFICAR / ACTUALIZAR GOL ---")
                print("(Escriba '0' o 'cancelar' para volver)")
                id_gol = pedir_int("ID del gol a modificar: ")
                print("(Deje vacío los campos que no desea modificar)")
                nuevo_minuto = pedir_int("Nuevo minuto (1-60): ", obligatorio=False)
                nuevo_autogol_str = pedir_input("¿Es autogol? (s/n, vacío=no cambiar): ", obligatorio=False)
                nuevo_autogol = None
                if nuevo_autogol_str:
                    nuevo_autogol = nuevo_autogol_str.lower() in ("s", "si", "sí", "1")
                nueva_ci = pedir_int("Nuevo CI del jugador: ", obligatorio=False)
                resultado = modificar_gol(id_gol, nuevo_minuto, nuevo_autogol, nueva_ci)
                mostrar_resultado(resultado)

            elif opcion == "3":
                print("\n--- VER GOLES DE UN PARTIDO ---")
                print("(Escriba '0' o 'cancelar' para volver)")
                id_partido = pedir_int("ID del partido: ")
                resultado = obtener_goles_partido(id_partido)
                mostrar_resultado(resultado)

            else:
                print("[!] Opción no válida.")

        except OperacionCancelada:
            print("\n[i] Operación cancelada. Regresando a la pantalla anterior...")


def menu_tarjetas_planillero(id_torneo):
    while True:
        print("\n" + "-" * 40)
        print(f"  TARJETAS (Torneo {id_torneo})")
        print("-" * 40)
        print("1. Registrar tarjeta")
        print("2. Modificar / Actualizar tarjeta (minuto)")
        print("3. Obtener / Ver tarjetas de un partido")
        print("0. Volver")

        opcion = input("\nSeleccione una opción: ").strip()

        if opcion == "0":
            break

        try:
            if opcion == "1":
                print("\n--- REGISTRAR TARJETA ---")
                print("(Escriba '0' o 'cancelar' en cualquier campo para volver)")
                id_partido = pedir_int("ID del partido: ")
                ci_jugador = pedir_int("CI del jugador: ")
                minuto = pedir_int("Minuto (1-60): ")
                color = pedir_input("Color (amarilla/roja): ").lower()
                resultado = registrar_tarjeta(id_partido, ci_jugador, minuto, color)
                mostrar_resultado(resultado)

            elif opcion == "2":
                print("\n--- MODIFICAR TARJETA ---")
                print("(Escriba '0' o 'cancelar' para volver)")
                id_tarjeta = pedir_int("ID de la tarjeta a modificar: ")
                nuevo_minuto = pedir_int("Nuevo minuto (1-60): ")
                resultado = modificar_tarjeta(id_tarjeta, nuevo_minuto)
                mostrar_resultado(resultado)

            elif opcion == "3":
                print("\n--- VER TARJETAS DE UN PARTIDO ---")
                print("(Escriba '0' o 'cancelar' para volver)")
                id_partido = pedir_int("ID del partido: ")
                resultado = obtener_tarjetas_partido(id_partido)
                mostrar_resultado(resultado)

            else:
                print("[!] Opción no válida.")

        except OperacionCancelada:
            print("\n[i] Operación cancelada. Regresando a la pantalla anterior...")


def menu_torneo_planillero(id_torneo, torneo_info, correo_usuario):
    """
    Submenú de operaciones del Planillero dentro de un torneo seleccionado:
    - Registrar o consultar planillas (sin eliminar)
    - Registrar, modificar o consultar goles (sin eliminar)
    - Registrar, modificar o consultar tarjetas (sin eliminar)
    - Marcar partido como 'jugado'
    - Ver reportes
    - Consultar partidos del torneo
    """
    nombre_torneo = torneo_info.get("nombre", f"ID {id_torneo}") if isinstance(torneo_info, dict) else f"ID {id_torneo}"

    while True:
        print("\n" + "=" * 55)
        print(f"  PLANILLERO - TORNEO: {nombre_torneo} (ID: {id_torneo})")
        print(f"  Sesión: {correo_usuario}")
        print("=" * 55)
        print("1. Registrar o consultar Planillas")
        print("2. Registrar o modificar Goles")
        print("3. Registrar o modificar Tarjetas")
        print("4. Marcar partido como 'jugado'")
        print("5. Ver Reportes")
        print("6. Consultar partidos del torneo")
        print("0. Cambiar de Torneo / Volver")

        opcion = input("\nSeleccione una opción: ").strip()

        if opcion == "1":
            menu_planillas_planillero(id_torneo)
        elif opcion == "2":
            menu_goles_planillero(id_torneo)
        elif opcion == "3":
            menu_tarjetas_planillero(id_torneo)
        elif opcion == "4":
            print("\n--- MARCAR PARTIDO COMO JUGADO ---")
            print("(Escriba '0' o 'cancelar' para volver)")
            try:
                id_partido = pedir_int("ID del partido a marcar como jugado: ")
                resultado = marcar_jugado(id_partido)
                mostrar_resultado(resultado)
            except OperacionCancelada:
                print("\n[i] Operación cancelada. Regresando a la pantalla anterior...")
        elif opcion == "5":
            menu_reportes(id_torneo)
        elif opcion == "6":
            print(f"\n--- PARTIDOS DEL TORNEO {id_torneo} ---")
            try:
                dia_filtro = pedir_input("Filtrar por fecha (YYYY-MM-DD, vacío=todas): ", obligatorio=False)
                estado_filtro = pedir_input("Filtrar por estado (programado/jugado/postergado/cancelado, vacío=todos): ", obligatorio=False)
                resultado = obtener_partidos(id_torneo=id_torneo, dia=dia_filtro, estado=estado_filtro)
                mostrar_resultado(resultado)
            except OperacionCancelada:
                print("\n[i] Operación cancelada. Regresando a la pantalla anterior...")
        elif opcion == "0":
            break
        else:
            print("[!] Opción no válida.")


def mostrar_menu_planillero(correo_usuario):
    """
    Flujo de entrada para el rol Planillero.
    Al loguearse se le pregunta en qué torneo va a trabajar.
    """
    while True:
        print("\n" + "=" * 55)
        print(f"   PANEL DE PLANILLERO (Sesión: {correo_usuario})")
        print("   SELECCIONAR TORNEO PARA TRABAJAR")
        print("   (Ingrese '0' o 'cancelar' para cerrar sesión)")
        print("   (Ingrese '?' o 'listar' para ver torneos disponibles)")
        print("=" * 55)

        entrada = input("Ingrese el ID del torneo en el que va a trabajar: ").strip()

        if entrada.lower() in PALABRAS_CANCELAR or entrada == "0":
            print("\nCerrando sesión de Planillero...")
            break

        if entrada in ("?", "listar", "ver"):
            print("\n--- TORNEOS DISPONIBLES ---")
            torneos = obtener_torneos()
            mostrar_resultado(torneos)
            continue

        try:
            id_torneo = int(entrada)
        except ValueError:
            print("[!] Debe ingresar un número de ID válido (o '?' para listar, '0' para salir).")
            continue

        torneo = obtener_torneo(id_torneo)
        if not torneo or (isinstance(torneo, dict) and "error" in torneo):
            print(f"\n[X] Error: No se encontró ningún torneo con el ID {id_torneo}.")
            continue

        menu_torneo_planillero(id_torneo, torneo, correo_usuario)


# ==========================================
# PUNTO DE ENTRADA PRINCIPAL (LOGIN)
# ==========================================
def main():
    while True:
        print("\n" + "=" * 55)
        print(" SISTEMA DE GESTIÓN DE FÚTBOL 5 - UCU 2026")
        print(" (Escriba '0', 'salir' o 'cancelar' para salir del sistema)")
        print("=" * 55)

        try:
            correo = pedir_input("Correo electrónico: ")
            contrasena = pedir_input("Contraseña: ")
        except OperacionCancelada:
            print("\nSaliendo del sistema. ¡Hasta luego!")
            break

        print("\nVerificando credenciales...")
        usuario = autenticar_usuario(correo, contrasena)

        if not usuario:
            print("\n[X] Error: Correo o contraseña incorrectos. Acceso denegado.")
            continue

        print(f"\n[✓] Autenticación exitosa. Rol detectado: {usuario['rol'].upper()}")

        # Configurar rol de sesión global para todas las funciones del backend
        set_current_role(usuario["rol"])

        # Redirección dinámica según el rol retornado por la tabla 'login'
        if usuario["rol"] in ("administrador", "admin"):
            mostrar_menu_administrador(usuario["correo"])
        elif usuario["rol"] == "planillero":
            mostrar_menu_planillero(usuario["correo"])
        else:
            print(f"\n[X] Error: El rol '{usuario['rol']}' no tiene un menú asignado.")


if __name__ == "__main__":
    main()
