import mysql.connector
from db import get_db_connection, set_current_role

# Importaciones de routers
from routers.torneos import crear_torneo, actualizar_torneo, eliminar_torneo, obtener_torneos, obtener_torneo
from routers.logins import crear_usuario, actualizar_usuario, eliminar_usuario, obtener_usuarios
from routers.canchas import crear_cancha, actualizar_cancha, eliminar_cancha, obtener_canchas
from routers.complejos import crear_complejo, actualizar_complejo, eliminar_complejo, obtener_complejos
from routers.equipos import crear_equipo, actualizar_equipo, eliminar_equipo, obtener_equipos
from routers.equipo_jugadores import inscribir_jugador_equipo, modificar_camiseta_jugador, eliminar_jugador_equipo, obtener_plantel
from routers.facultades import crear_facultad, actualizar_facultad, eliminar_facultad, obtener_facultades
from routers.goles import registrar_gol, modificar_gol, eliminar_gol, obtener_goles_partido
from routers.jugadores import crear_jugador, actualizar_jugador, eliminar_jugador, obtener_jugadores, obtener_jugador
from routers.partidos import programar_partido, editar_resultado_partido, postergar_partido, marcar_jugado, cancelar_partido, eliminar_partido
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
# UTILIDADES DE MENÚ
# ==========================================
def mostrar_resultado(resultado):
    """Muestra el resultado de una operación de forma legible."""
    if isinstance(resultado, dict):
        if "error" in resultado:
            print(f"\n[X] Error: {resultado['error']}")
        elif "exito" in resultado:
            print(f"\n[✓] {resultado.get('mensaje', 'Operación exitosa.')}")
            # Mostrar campos extra (id_sancion, id_gol, etc.)
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
                for clave, valor in fila.items():
                    print(f"  {clave}: {valor}")
    else:
        print(resultado)


def pedir_input(mensaje, obligatorio=True):
    """Pide input al usuario. Retorna None si no es obligatorio y se deja vacío."""
    valor = input(mensaje).strip()
    if not valor:
        if obligatorio:
            print("[!] Este campo es obligatorio.")
            return pedir_input(mensaje, obligatorio)
        return None
    return valor


def pedir_int(mensaje, obligatorio=True):
    """Pide un entero al usuario."""
    valor = pedir_input(mensaje, obligatorio)
    if valor is None:
        return None
    try:
        return int(valor)
    except ValueError:
        print("[!] Debe ingresar un número entero.")
        return pedir_int(mensaje, obligatorio)


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
        print("2. Actualizar torneo")
        print("3. Eliminar torneo")
        print("4. Listar torneos")
        print("0. Volver")

        opcion = input("\nSeleccione una opción: ").strip()

        if opcion == "1":
            nombre = pedir_input("Nombre del torneo: ")
            anio = pedir_int("Año: ")
            semestre = pedir_int("Semestre (1 o 2): ")
            fecha_inicio = pedir_input("Fecha de inicio (YYYY-MM-DD): ")
            fecha_fin = pedir_input("Fecha de fin (YYYY-MM-DD): ")
            estado = pedir_input("Estado (inscripción/en curso/finalizado) [inscripción]: ", obligatorio=False) or "inscripción"
            resultado = crear_torneo(nombre, anio, semestre, fecha_inicio, fecha_fin, estado)
            mostrar_resultado(resultado)

        elif opcion == "2":
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
            id_torneo = pedir_int("ID del torneo a eliminar: ")
            resultado = eliminar_torneo(id_torneo)
            mostrar_resultado(resultado)

        elif opcion == "4":
            resultado = obtener_torneos()
            mostrar_resultado(resultado)

        elif opcion == "0":
            break
        else:
            print("[!] Opción no válida.")


# ==========================================
# ABM DE USUARIOS (LOGINS)
# ==========================================
def menu_abm_logins():
    while True:
        print("\n" + "-" * 40)
        print("  ABM DE USUARIOS")
        print("-" * 40)
        print("1. Crear usuario")
        print("2. Actualizar usuario")
        print("3. Eliminar usuario")
        print("4. Listar usuarios")
        print("0. Volver")

        opcion = input("\nSeleccione una opción: ").strip()

        if opcion == "1":
            correo = pedir_input("Correo del nuevo usuario: ")
            contrasena = pedir_input("Contraseña: ")
            rol = pedir_input("Rol (administrador/planillero): ")
            resultado = crear_usuario(correo, contrasena, rol)
            mostrar_resultado(resultado)

        elif opcion == "2":
            correo = pedir_input("Correo del usuario a actualizar: ")
            print("(Deje vacío los campos que no desea modificar)")
            nueva_contrasena = pedir_input("Nueva contraseña: ", obligatorio=False)
            nuevo_rol = pedir_input("Nuevo rol (administrador/planillero): ", obligatorio=False)
            resultado = actualizar_usuario(correo, nueva_contrasena, nuevo_rol)
            mostrar_resultado(resultado)

        elif opcion == "3":
            correo = pedir_input("Correo del usuario a eliminar: ")
            resultado = eliminar_usuario(correo)
            mostrar_resultado(resultado)

        elif opcion == "4":
            resultado = obtener_usuarios()
            mostrar_resultado(resultado)

        elif opcion == "0":
            break
        else:
            print("[!] Opción no válida.")


# ==========================================
# ABM DE CANCHAS
# ==========================================
def menu_abm_canchas():
    while True:
        print("\n" + "-" * 40)
        print("  ABM DE CANCHAS")
        print("-" * 40)
        print("1. Crear cancha")
        print("2. Actualizar cancha")
        print("3. Eliminar cancha")
        print("4. Listar canchas")
        print("0. Volver")

        opcion = input("\nSeleccione una opción: ").strip()

        if opcion == "1":
            nombre = pedir_input("Nombre de la cancha: ")
            id_complejo = pedir_int("ID del complejo: ")
            superficie = pedir_input("Superficie (cesped natural/cesped sintetico/hormigon): ")
            techada_str = pedir_input("¿Es techada? (s/n): ").lower()
            techada = 1 if techada_str == "s" else 0
            resultado = crear_cancha(nombre, id_complejo, superficie, techada)
            mostrar_resultado(resultado)

        elif opcion == "2":
            nombre = pedir_input("Nombre de la cancha: ")
            id_complejo = pedir_int("ID del complejo: ")
            print("(Deje vacío los campos que no desea modificar)")
            nueva_superficie = pedir_input("Nueva superficie: ", obligatorio=False)
            nueva_techada_str = pedir_input("¿Es techada? (s/n, vacío=no cambiar): ", obligatorio=False)
            nueva_techada = None
            if nueva_techada_str:
                nueva_techada = 1 if nueva_techada_str.lower() == "s" else 0
            resultado = actualizar_cancha(nombre, id_complejo, nueva_superficie, nueva_techada)
            mostrar_resultado(resultado)

        elif opcion == "3":
            nombre = pedir_input("Nombre de la cancha: ")
            id_complejo = pedir_int("ID del complejo: ")
            resultado = eliminar_cancha(nombre, id_complejo)
            mostrar_resultado(resultado)

        elif opcion == "4":
            id_complejo = pedir_int("ID del complejo (vacío=todos): ", obligatorio=False)
            resultado = obtener_canchas(id_complejo)
            mostrar_resultado(resultado)

        elif opcion == "0":
            break
        else:
            print("[!] Opción no válida.")


# ==========================================
# ABM DE COMPLEJOS
# ==========================================
def menu_abm_complejos():
    while True:
        print("\n" + "-" * 40)
        print("  ABM DE COMPLEJOS DEPORTIVOS")
        print("-" * 40)
        print("1. Crear complejo")
        print("2. Actualizar complejo")
        print("3. Eliminar complejo")
        print("4. Listar complejos")
        print("0. Volver")

        opcion = input("\nSeleccione una opción: ").strip()

        if opcion == "1":
            nombre = pedir_input("Nombre del complejo: ")
            direccion = pedir_input("Dirección: ")
            departamento = pedir_input("Departamento: ")
            resultado = crear_complejo(nombre, direccion, departamento)
            mostrar_resultado(resultado)

        elif opcion == "2":
            id_complejo = pedir_int("ID del complejo a actualizar: ")
            print("(Deje vacío los campos que no desea modificar)")
            nombre = pedir_input("Nuevo nombre: ", obligatorio=False)
            direccion = pedir_input("Nueva dirección: ", obligatorio=False)
            departamento = pedir_input("Nuevo departamento: ", obligatorio=False)
            resultado = actualizar_complejo(id_complejo, nombre, direccion, departamento)
            mostrar_resultado(resultado)

        elif opcion == "3":
            id_complejo = pedir_int("ID del complejo a eliminar: ")
            resultado = eliminar_complejo(id_complejo)
            mostrar_resultado(resultado)

        elif opcion == "4":
            resultado = obtener_complejos()
            mostrar_resultado(resultado)

        elif opcion == "0":
            break
        else:
            print("[!] Opción no válida.")


# ==========================================
# ABM DE EQUIPOS
# ==========================================
def menu_abm_equipos(id_torneo):
    while True:
        print("\n" + "-" * 40)
        print(f"  ABM DE EQUIPOS (Torneo {id_torneo})")
        print("-" * 40)
        print("1. Crear equipo")
        print("2. Actualizar equipo")
        print("3. Eliminar equipo")
        print("4. Listar equipos del torneo")
        print("0. Volver")

        opcion = input("\nSeleccione una opción: ").strip()

        if opcion == "1":
            nombre = pedir_input("Nombre del equipo: ")
            id_facultad = pedir_int("ID de la facultad: ")
            ci_capitan = pedir_input("CI del capitán: ")
            resultado = crear_equipo(nombre, id_torneo, id_facultad, ci_capitan)
            mostrar_resultado(resultado)

        elif opcion == "2":
            id_equipo = pedir_int("ID del equipo a actualizar: ")
            print("(Deje vacío los campos que no desea modificar)")
            nombre = pedir_input("Nuevo nombre: ", obligatorio=False)
            ci_capitan = pedir_input("Nuevo CI del capitán: ", obligatorio=False)
            resultado = actualizar_equipo(id_equipo, nombre, ci_capitan)
            mostrar_resultado(resultado)

        elif opcion == "3":
            id_equipo = pedir_int("ID del equipo a eliminar: ")
            resultado = eliminar_equipo(id_equipo)
            mostrar_resultado(resultado)

        elif opcion == "4":
            resultado = obtener_equipos(id_torneo)
            mostrar_resultado(resultado)

        elif opcion == "0":
            break
        else:
            print("[!] Opción no válida.")


# ==========================================
# ABM DE INSCRIPCIONES (equipo_jugador_torneo)
# ==========================================
def menu_abm_inscripciones(id_torneo):
    while True:
        print("\n" + "-" * 40)
        print(f"  ABM DE INSCRIPCIONES (Torneo {id_torneo})")
        print("-" * 40)
        print("1. Inscribir jugador en equipo")
        print("2. Modificar número de camiseta")
        print("3. Eliminar jugador de equipo")
        print("4. Ver plantel de un equipo")
        print("0. Volver")

        opcion = input("\nSeleccione una opción: ").strip()

        if opcion == "1":
            id_equipo = pedir_int("ID del equipo: ")
            ci_jugador = pedir_input("CI del jugador: ")
            numero_camiseta = pedir_int("Número de camiseta: ")
            resultado = inscribir_jugador_equipo(id_equipo, ci_jugador, id_torneo, numero_camiseta)
            mostrar_resultado(resultado)

        elif opcion == "2":
            id_equipo = pedir_int("ID del equipo: ")
            ci_jugador = pedir_input("CI del jugador: ")
            nuevo_numero = pedir_int("Nuevo número de camiseta: ")
            resultado = modificar_camiseta_jugador(id_equipo, ci_jugador, id_torneo, nuevo_numero)
            mostrar_resultado(resultado)

        elif opcion == "3":
            id_equipo = pedir_int("ID del equipo: ")
            ci_jugador = pedir_input("CI del jugador: ")
            resultado = eliminar_jugador_equipo(id_equipo, ci_jugador, id_torneo)
            mostrar_resultado(resultado)

        elif opcion == "4":
            id_equipo = pedir_int("ID del equipo: ")
            resultado = obtener_plantel(id_equipo, id_torneo)
            mostrar_resultado(resultado)

        elif opcion == "0":
            break
        else:
            print("[!] Opción no válida.")


# ==========================================
# ABM DE FACULTADES
# ==========================================
def menu_abm_facultades():
    while True:
        print("\n" + "-" * 40)
        print("  ABM DE FACULTADES")
        print("-" * 40)
        print("1. Crear facultad")
        print("2. Actualizar facultad")
        print("3. Eliminar facultad")
        print("4. Listar facultades")
        print("0. Volver")

        opcion = input("\nSeleccione una opción: ").strip()

        if opcion == "1":
            nombre = pedir_input("Nombre de la facultad: ")
            resultado = crear_facultad(nombre)
            mostrar_resultado(resultado)

        elif opcion == "2":
            id_facultad = pedir_int("ID de la facultad a actualizar: ")
            nombre = pedir_input("Nuevo nombre: ")
            resultado = actualizar_facultad(id_facultad, nombre)
            mostrar_resultado(resultado)

        elif opcion == "3":
            id_facultad = pedir_int("ID de la facultad a eliminar: ")
            resultado = eliminar_facultad(id_facultad)
            mostrar_resultado(resultado)

        elif opcion == "4":
            resultado = obtener_facultades()
            mostrar_resultado(resultado)

        elif opcion == "0":
            break
        else:
            print("[!] Opción no válida.")


# ==========================================
# ABM DE GOLES
# ==========================================
def menu_abm_goles(id_torneo):
    while True:
        print("\n" + "-" * 40)
        print(f"  ABM DE GOLES (Torneo {id_torneo})")
        print("-" * 40)
        print("1. Registrar gol")
        print("2. Modificar gol")
        print("3. Eliminar gol")
        print("4. Ver goles de un partido")
        print("0. Volver")

        opcion = input("\nSeleccione una opción: ").strip()

        if opcion == "1":
            id_partido = pedir_int("ID del partido: ")
            ci_jugador = pedir_input("CI del jugador: ")
            minuto = pedir_int("Minuto del gol: ")
            autogol_str = pedir_input("¿Es autogol? (s/n): ").lower()
            autogol = True if autogol_str == "s" else False
            resultado = registrar_gol(id_partido, ci_jugador, minuto, autogol)
            mostrar_resultado(resultado)

        elif opcion == "2":
            id_gol = pedir_int("ID del gol a modificar: ")
            print("(Deje vacío los campos que no desea modificar)")
            nuevo_minuto = pedir_int("Nuevo minuto: ", obligatorio=False)
            nuevo_autogol_str = pedir_input("¿Es autogol? (s/n, vacío=no cambiar): ", obligatorio=False)
            nuevo_autogol = None
            if nuevo_autogol_str:
                nuevo_autogol = True if nuevo_autogol_str.lower() == "s" else False
            nueva_ci = pedir_input("Nuevo CI del jugador: ", obligatorio=False)
            resultado = modificar_gol(id_gol, nuevo_minuto, nuevo_autogol, nueva_ci)
            mostrar_resultado(resultado)

        elif opcion == "3":
            id_gol = pedir_int("ID del gol a eliminar: ")
            resultado = eliminar_gol(id_gol)
            mostrar_resultado(resultado)

        elif opcion == "4":
            id_partido = pedir_int("ID del partido: ")
            resultado = obtener_goles_partido(id_partido)
            mostrar_resultado(resultado)

        elif opcion == "0":
            break
        else:
            print("[!] Opción no válida.")


# ==========================================
# ABM DE JUGADORES
# ==========================================
def menu_abm_jugadores():
    while True:
        print("\n" + "-" * 40)
        print("  ABM DE JUGADORES")
        print("-" * 40)
        print("1. Crear jugador")
        print("2. Actualizar jugador")
        print("3. Eliminar jugador")
        print("4. Listar jugadores")
        print("5. Buscar jugador por CI")
        print("0. Volver")

        opcion = input("\nSeleccione una opción: ").strip()

        if opcion == "1":
            ci = pedir_input("CI del jugador: ")
            nombre = pedir_input("Nombre: ")
            apellido = pedir_input("Apellido: ")
            email = pedir_input("Email: ")
            fecha_nacimiento = pedir_input("Fecha de nacimiento (YYYY-MM-DD): ")
            id_facultad = pedir_int("ID de la facultad: ")
            tipo = pedir_input("Tipo (estudiante/funcionario/egresado): ")
            resultado = crear_jugador(ci, nombre, apellido, email, fecha_nacimiento, id_facultad, tipo)
            mostrar_resultado(resultado)

        elif opcion == "2":
            ci = pedir_input("CI del jugador a actualizar: ")
            print("(Deje vacío los campos que no desea modificar)")
            nombre = pedir_input("Nuevo nombre: ", obligatorio=False)
            apellido = pedir_input("Nuevo apellido: ", obligatorio=False)
            email = pedir_input("Nuevo email: ", obligatorio=False)
            fecha_nacimiento = pedir_input("Nueva fecha de nacimiento (YYYY-MM-DD): ", obligatorio=False)
            id_facultad = pedir_int("Nuevo ID de facultad: ", obligatorio=False)
            tipo = pedir_input("Nuevo tipo (estudiante/funcionario/egresado): ", obligatorio=False)
            resultado = actualizar_jugador(ci, nombre, apellido, email, fecha_nacimiento, id_facultad, tipo)
            mostrar_resultado(resultado)

        elif opcion == "3":
            ci = pedir_input("CI del jugador a eliminar: ")
            resultado = eliminar_jugador(ci)
            mostrar_resultado(resultado)

        elif opcion == "4":
            id_facultad = pedir_int("ID de facultad (vacío=todos): ", obligatorio=False)
            resultado = obtener_jugadores(id_facultad)
            mostrar_resultado(resultado)

        elif opcion == "5":
            ci = pedir_input("CI del jugador: ")
            resultado = obtener_jugador(ci)
            mostrar_resultado(resultado)

        elif opcion == "0":
            break
        else:
            print("[!] Opción no válida.")


# ==========================================
# ABM DE PARTIDOS
# ==========================================
def menu_abm_partidos(id_torneo):
    while True:
        print("\n" + "-" * 40)
        print(f"  ABM DE PARTIDOS (Torneo {id_torneo})")
        print("-" * 40)
        print("1. Programar partido")
        print("2. Editar resultado de partido")
        print("3. Postergar partido")
        print("4. Marcar partido como jugado")
        print("5. Cancelar partido")
        print("6. Eliminar partido")
        print("0. Volver")

        opcion = input("\nSeleccione una opción: ").strip()

        if opcion == "1":
            id_equipo_local = pedir_int("ID equipo local: ")
            id_equipo_visitante = pedir_int("ID equipo visitante: ")
            numero_fecha = pedir_int("Número de fecha: ")
            fecha = pedir_input("Fecha del partido (YYYY-MM-DD): ")
            hora = pedir_input("Hora (HH:MM): ")
            nombre_cancha = pedir_input("Nombre de la cancha: ")
            id_complejo = pedir_int("ID del complejo: ")
            id_turno = pedir_int("ID del turno: ")
            resultado = programar_partido(id_equipo_local, id_equipo_visitante, id_torneo,
                                          numero_fecha, fecha, hora, nombre_cancha, id_complejo, id_turno)
            mostrar_resultado(resultado)

        elif opcion == "2":
            id_partido = pedir_int("ID del partido: ")
            goles_local = pedir_int("Goles del equipo local: ")
            goles_visitante = pedir_int("Goles del equipo visitante: ")
            resultado = editar_resultado_partido(id_partido, goles_local, goles_visitante)
            mostrar_resultado(resultado)

        elif opcion == "3":
            id_partido = pedir_int("ID del partido a postergar: ")
            nueva_fecha = pedir_input("Nueva fecha (YYYY-MM-DD): ")
            nueva_cancha = pedir_input("Nuevo nombre de cancha: ")
            nuevo_id_complejo = pedir_int("Nuevo ID de complejo: ")
            resultado = postergar_partido(id_partido, nueva_fecha, nueva_cancha, nuevo_id_complejo)
            mostrar_resultado(resultado)

        elif opcion == "4":
            id_partido = pedir_int("ID del partido a marcar como jugado: ")
            resultado = marcar_jugado(id_partido)
            mostrar_resultado(resultado)

        elif opcion == "5":
            id_partido = pedir_int("ID del partido a cancelar: ")
            resultado = cancelar_partido(id_partido)
            mostrar_resultado(resultado)

        elif opcion == "6":
            id_partido = pedir_int("ID del partido a eliminar: ")
            resultado = eliminar_partido(id_partido)
            mostrar_resultado(resultado)

        elif opcion == "0":
            break
        else:
            print("[!] Opción no válida.")


# ==========================================
# ABM DE PLANILLAS
# ==========================================
def menu_abm_planillas(id_torneo):
    while True:
        print("\n" + "-" * 40)
        print(f"  ABM DE PLANILLAS (Torneo {id_torneo})")
        print("-" * 40)
        print("1. Registrar jugador en planilla")
        print("2. Borrar jugador de planilla")
        print("3. Ver planilla de un partido")
        print("0. Volver")

        opcion = input("\nSeleccione una opción: ").strip()

        if opcion == "1":
            id_partido = pedir_int("ID del partido: ")
            ci_jugador = pedir_input("CI del jugador: ")
            id_equipo = pedir_int("ID del equipo: ")
            resultado = registrar_planilla_jugador(id_partido, ci_jugador, id_equipo)
            mostrar_resultado(resultado)

        elif opcion == "2":
            id_partido = pedir_int("ID del partido: ")
            ci_jugador = pedir_input("CI del jugador: ")
            resultado = borrar_planilla_jugador(id_partido, ci_jugador)
            mostrar_resultado(resultado)

        elif opcion == "3":
            id_partido = pedir_int("ID del partido: ")
            resultado = obtener_planilla_partido(id_partido)
            mostrar_resultado(resultado)

        elif opcion == "0":
            break
        else:
            print("[!] Opción no válida.")


# ==========================================
# ABM DE SANCIONES
# ==========================================
def menu_abm_sanciones(id_torneo):
    while True:
        print("\n" + "-" * 40)
        print(f"  ABM DE SANCIONES (Torneo {id_torneo})")
        print("-" * 40)
        print("1. Crear sanción")
        print("2. Actualizar sanción")
        print("3. Eliminar sanción")
        print("4. Listar sanciones del torneo")
        print("0. Volver")

        opcion = input("\nSeleccione una opción: ").strip()

        if opcion == "1":
            ci_jugador = pedir_input("CI del jugador: ")
            motivo = pedir_input("Motivo (roja/acumulación de amarillas/disciplinaria): ")
            numero_fecha_inicio = pedir_int("Número de fecha de inicio: ")
            cantidad_fechas = pedir_int("Cantidad de fechas (default=1): ", obligatorio=False) or 1
            resultado = crear_sancion(ci_jugador, id_torneo, motivo, numero_fecha_inicio, cantidad_fechas)
            mostrar_resultado(resultado)

        elif opcion == "2":
            id_sancion = pedir_int("ID de la sanción a actualizar: ")
            print("(Deje vacío los campos que no desea modificar)")
            motivo = pedir_input("Nuevo motivo: ", obligatorio=False)
            numero_fecha_inicio = pedir_int("Nuevo número de fecha inicio: ", obligatorio=False)
            cantidad_fechas = pedir_int("Nueva cantidad de fechas: ", obligatorio=False)
            resultado = actualizar_sancion(id_sancion, motivo, numero_fecha_inicio, cantidad_fechas)
            mostrar_resultado(resultado)

        elif opcion == "3":
            id_sancion = pedir_int("ID de la sanción a eliminar: ")
            resultado = eliminar_sancion(id_sancion)
            mostrar_resultado(resultado)

        elif opcion == "4":
            ci_jugador = pedir_input("Filtrar por CI de jugador (vacío=todos): ", obligatorio=False)
            resultado = obtener_sanciones(id_torneo, ci_jugador)
            mostrar_resultado(resultado)

        elif opcion == "0":
            break
        else:
            print("[!] Opción no válida.")


# ==========================================
# ABM DE TARJETAS
# ==========================================
def menu_abm_tarjetas(id_torneo):
    while True:
        print("\n" + "-" * 40)
        print(f"  ABM DE TARJETAS (Torneo {id_torneo})")
        print("-" * 40)
        print("1. Registrar tarjeta")
        print("2. Modificar tarjeta")
        print("3. Eliminar tarjeta")
        print("4. Ver tarjetas de un partido")
        print("0. Volver")

        opcion = input("\nSeleccione una opción: ").strip()

        if opcion == "1":
            id_partido = pedir_int("ID del partido: ")
            ci_jugador = pedir_input("CI del jugador: ")
            minuto = pedir_int("Minuto: ")
            color = pedir_input("Color (amarilla/roja): ")
            resultado = registrar_tarjeta(id_partido, ci_jugador, minuto, color)
            mostrar_resultado(resultado)

        elif opcion == "2":
            id_tarjeta = pedir_int("ID de la tarjeta a modificar: ")
            nuevo_minuto = pedir_int("Nuevo minuto: ")
            resultado = modificar_tarjeta(id_tarjeta, nuevo_minuto)
            mostrar_resultado(resultado)

        elif opcion == "3":
            id_tarjeta = pedir_int("ID de la tarjeta a eliminar: ")
            resultado = eliminar_tarjeta(id_tarjeta)
            mostrar_resultado(resultado)

        elif opcion == "4":
            id_partido = pedir_int("ID del partido: ")
            resultado = obtener_tarjetas_partido(id_partido)
            mostrar_resultado(resultado)

        elif opcion == "0":
            break
        else:
            print("[!] Opción no válida.")


# ==========================================
# ABM DE TURNOS
# ==========================================
def menu_abm_turnos():
    while True:
        print("\n" + "-" * 40)
        print("  ABM DE TURNOS")
        print("-" * 40)
        print("1. Crear turno")
        print("2. Actualizar turno")
        print("3. Eliminar turno")
        print("4. Listar turnos")
        print("0. Volver")

        opcion = input("\nSeleccione una opción: ").strip()

        if opcion == "1":
            hora_inicio = pedir_input("Hora de inicio (HH:MM): ")
            hora_fin = pedir_input("Hora de fin (HH:MM): ")
            resultado = crear_turno(hora_inicio, hora_fin)
            mostrar_resultado(resultado)

        elif opcion == "2":
            id_turno = pedir_int("ID del turno a actualizar: ")
            hora_inicio = pedir_input("Nueva hora de inicio (HH:MM): ")
            hora_fin = pedir_input("Nueva hora de fin (HH:MM): ")
            resultado = actualizar_turno(id_turno, hora_inicio, hora_fin)
            mostrar_resultado(resultado)

        elif opcion == "3":
            id_turno = pedir_int("ID del turno a eliminar: ")
            resultado = eliminar_turno(id_turno)
            mostrar_resultado(resultado)

        elif opcion == "4":
            resultado = obtener_turnos()
            mostrar_resultado(resultado)

        elif opcion == "0":
            break
        else:
            print("[!] Opción no válida.")


# ==========================================
# MENÚ DE REPORTES
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
def menu_torneo_admin(id_torneo):
    # Verificar que el torneo exista
    torneo = obtener_torneo(id_torneo)
    if isinstance(torneo, dict) and "error" in torneo:
        mostrar_resultado(torneo)
        return

    nombre_torneo = torneo.get("nombre", f"ID {id_torneo}") if isinstance(torneo, dict) else f"ID {id_torneo}"

    while True:
        print("\n" + "=" * 50)
        print(f"  TORNEO: {nombre_torneo} (ID: {id_torneo})")
        print("=" * 50)
        print("1.  ABM de Canchas")
        print("2.  ABM de Complejos Deportivos")
        print("3.  ABM de Equipos")
        print("4.  ABM de Inscripciones")
        print("5.  ABM de Facultades")
        print("6.  ABM de Goles")
        print("7.  ABM de Jugadores")
        print("8.  ABM de Partidos")
        print("9.  ABM de Planillas")
        print("10. ABM de Sanciones")
        print("11. ABM de Tarjetas")
        print("12. ABM de Turnos")
        print("13. Ver Reportes")
        print("0.  Volver")

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
# MENÚ PRINCIPAL PARA ADMINISTRADORES
# ==========================================
def mostrar_menu_administrador(correo_usuario):
    while True:
        print("\n" + "=" * 50)
        print(f"   PANEL DE ADMINISTRACIÓN (Sesión: {correo_usuario})")
        print("=" * 50)
        print("1. Trabajar en un torneo")
        print("2. ABM de Torneos")
        print("3. ABM de Usuarios")
        print("0. Cerrar Sesión")

        opcion = input("\nSeleccione una opción: ").strip()

        if opcion == "1":
            id_torneo = pedir_int("Ingrese el ID del torneo: ")
            menu_torneo_admin(id_torneo)

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
# MENÚ PARA PLANILLEROS
# ==========================================
def mostrar_menu_planillero(correo_usuario):
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
        elif opcion == "2":
            print("\n[Módulo Planillero]: Registrar Gol")
        elif opcion == "3":
            print("\n[Módulo Planillero]: Registrar Tarjetas")
        elif opcion == "4":
            print("\n[Módulo Planillero]: Partidos del día")
        elif opcion == "0":
            print("\nCerrando sesión de Planillero...")
            break
        else:
            print("[!] Opción no válida.")


# ==========================================
# PUNTO DE ENTRADA PRINCIPAL (LOGIN)
# ==========================================
def main():
    print("=" * 50)
    print(" SISTEMA DE GESTIÓN DE FÚTBOL 5 - UCU 2026")
    print("=" * 50)

    correo = input("Correo electrónico: ").strip()
    contrasena = input("Contraseña: ").strip()

    print("\nVerificando credenciales...")
    usuario = autenticar_usuario(correo, contrasena)

    if not usuario:
        print("\n[X] Error: Correo o contraseña incorrectos. Acceso denegado.")
        return

    print(f"\n[✓] Autenticación exitosa. Rol detectado: {usuario['rol'].upper()}")

    # Configurar rol de sesión global para todas las funciones
    set_current_role(usuario["rol"])

    # Redirección dinámica según el rol retornado por la tabla 'login'
    if usuario["rol"] == "administrador":
        mostrar_menu_administrador(usuario["correo"])
    elif usuario["rol"] == "planillero":
        mostrar_menu_planillero(usuario["correo"])
    else:
        print(f"\n[X] Error: El rol '{usuario['rol']}' no tiene un menú asignado.")


if __name__ == "__main__":
    main()
