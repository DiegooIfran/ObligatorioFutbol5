# MANUAL DE USUARIO 


## Requisitos: 

Tener un IDE de python descargado (como PyCharm) 

Tener descargado MySQL Configurator (versión 26.7 o posterior) 

Tener un IDE de bases de datos SQL (como DataGrip) 

Descargar la librería mysql.connector con el siguiente comando: 

pip install mysql-connector-python 

## Pasos para levantar el programa: 

### Paso 1: 

Clonar el repositorio de GitHub:  

https://github.com/DiegooIfran/ObligatorioFutbol5  

### Paso 2: 

Crear y encender un servidor local en MySQL Configurator de la siguiente manera: 

Abre tu herramienta de gestión de MySQL. 

Asegúrate de crear e iniciar un servidor local activo (por defecto suele correr en el puerto 3306 con el usuario root). 

### Paso 3:  

Conectar el servidor local con el IDE de bases de datos: 

Abre tu IDE de base de datos (como DataGrip). 

Añade una nueva fuente de datos conectada a MySQL (Data Sources -> MySQL). 

Rellena los datos de conexión del servidor local (Host: localhost, Port: 3306, credenciales de tu usuario administrador como root y su contraseña como rootpassword o la que haya asignado). 

Prueba la conexión (Test Connection) y guárdala. 

### Paso 4:  

Abrir el documento Creacion_tablas_obligatorio.sql en el IDE de SQL y correrlo por completo 

Advertencia: Si ya existe una base de datos llamada Obligatorio_Futbol5 o usuarios 'usr_admin'@'localhost', 'usr_planillero'@'localhost' o 'usr_login'@'localhost' el código los dará de baja. 

### Paso 5:  

En el IDE de python correr menu.py ubicado en la carpeta "backend" 

 

## Cómo utilizar el programa: 

El programa ya viene con datos de ejemplo cargados y dos usuarios iniciales: 

Los datos forman un torneo con 6 equipos y 3 fechas jugadas hasta el momento, con datos de las facultades, jugadores, los partidos y sus goles, tarjetas y sanciones correspondientes. 

Los usuarios iniciales son: 

"admin@ucu.edu.uy" con contraseña "admin123" cuyo rol es de administrador 

"planillero1@ucu.edu.uy" con contraseña "planillero123" cuyo rol es de planillero 

En este sistema hay dos tipos de usuarios, los administradores y los planilleros. Los administradores pueden manejar toda la información de la base de datos (incluyendo alta y baja de otros usuarios) así que deben ser únicamente personas de confianza, estos serán los encargados de crear los torneos, administrar sus inscripciones, crear los partidos y crear las canchas y complejos. Además, serán los encargados de borrar los casos en los que las planillas sean mal cargadas.  

Los planilleros sólo pueden registrar las planillas de los partidos, registrar los goles y tarjetas (o editar su minuto) y marcar los partidos como "jugados". Las planillas y goles deben ser registradas antes de pasadas 48 horas de la hora disputa del partido marcada en la base de datos. 

## Uso general del programa: 

Para elegir una opción, se escribe su número y se presiona Enter. 

Para cancelar una carga y volver a la pantalla anterior, se escribe “0”, “cancelar”, “volver” o “salir” en cualquier campo. 

Al modificar un registro, los campos que no se quieren cambiar se dejan vacíos y se presiona Enter. 

Las fechas se ingresan en formato AAAA-MM-DD  

(por ejemplo, 2026-11-04). 

Después de cada resultado se muestra “Presione Enter para continuar...”. 

Si una operación no cumple alguna regla del sistema, se muestra un mensaje que empieza con “Error:” y no se guarda nada. 

Para salir del programa, se escribe “0” en la pantalla de inicio de sesión. 

Una vez que el programa esté en funcionamiento aparecerá la pantalla de inicio de sesión. En el primer uso se debe de ingresar con la cuenta "admin@ucu.edu.uy" para poder crear así el usuario de administrador de quién lo vaya a usar (y es recomendado borrar este usuario inicial por temas de seguridad). 

### Al ingresar como administrador se le plantean al usuario las siguientes opciones:  

##### Trabajar en un torneo 

##### ABM de Torneos 

##### ABM de Canchas 

##### ABM de Complejos Deportivos 

##### ABM de Facultades 

##### ABM de Jugadores 

##### ABM de Logins (Usuarios) 

##### Cerrar Sesión 

 

Trabajar en un torneo: 

Despliega el menú para realizar inscripciones de equipos, de jugadores dentro de los equipos y registros de partidos, planillas, goles, tarjetas y sanciones.  

ABM de Torneos:  

Permite registrar, borrar, modificar o ver los torneos 

ABM de Canchas: 

Permite registrar, borrar, modificar o ver las canchas (se debe antes registrar su complejo deportivo) 

ABM de Complejos Deportivos: 

Permite registrar, borrar, modificar o ver los complejos deportivos 

ABM de Facultades: 

Permite registrar, borrar, modificar o ver las facultades 

ABM de Jugadores: 

Permite registrar, borrar, modificar o ver los jugadores (esto se debe realizar previo a su inscripción a un torneo) 

ABM de Logins (Usuarios): 

Permite registrar, borrar, modificar o ver los usuarios (sin mostrar sus contraseñas) 

Cerrar Sesión: 

Cierra sesión y devuelve a la pantalla de inicio de sesión 

 

Al elegir "Trabajar en un torneo" se le pregunta al usuario el id del torneo en el que trabajará y al ingresar un id correcto se despliega el siguiente menú: 

 

ABM de Equipos 

ABM de Inscripciones (Planteles) 

ABM de Goles 

ABM de Partidos 

ABM de Planillas 

ABM de Sanciones 

ABM de Tarjetas 

Ver Reportes 

Volver al Menú Principal 



ABM de Equipos: 

Permite registrar, borrar, modificar o ver los equipos (cuando se crea un equipo, se asigna un jugador como capitán y se lo inscribe automáticamente) 

ABM de Inscripciones (Planteles): 

Permite inscribir, dar de baja, modificar dorsales de jugadores o ver plantel de un equipo 

ABM de Goles: 

Permite registrar, borrar, modificar o ver los goles de un partido 

ABM de Partidos: 

Permite programar, borrar, modificar, cancelar, marcar como jugado o listar partidos 

ABM de Planillas:  

Permite registrar, borrar o ver las planillas (jugadores que participaron del partido) 

ABM de Sanciones:  

Permite crear, dar de baja, modificar o listar sanciones (se pueden marcar sanciones disciplinarias y marcar su duración. 

ABM de Tarjetas:  

Permite registrar, dar de baja, modificar o listar tarjetas de un partido (estas tarjetas aplican sanciones automáticamente cada tres tarjetas amarillas o una roja) 
Si en un partido a un jugador se le saca doble amarilla, por lo que recibe una roja indirecta, en la planilla se debe marcar únicamente la roja 

Ver Reportes:  

Permite ver: 

Tabla de posiciones: Obtiene la tabla de posiciones de los equipos en el torneo. 

Tabla de goleadores: Obtiene los goleadores del torneo. 

Tabla de fair play: Obtiene los puntos y estadísticas de Fair Play por equipo en un torneo (el equipo con menor puntaje es el que menos sanciones tiene) 

Promedio de goles por fecha: Obtiene el promedio de goles por fecha disputada en un torneo. 

Promedio de goles por edición: Obtiene el promedio de goles por edición (general de todos los torneos). 

Canchas y turnos: Obtiene la cantidad de usos de canchas y turnos (general de todos los torneos). 

Jugadores por facultad: Obtiene la distribución de jugadores por facultad y grado para un torneo. 

Jugadores sin figurar: Obtiene los jugadores inscriptos que no figuraron en ninguna planilla del torneo. 

Sanciones por equipo: Obtiene el resumen de sanciones por equipo y por motivo en un torneo. 

Porcentaje de partidos jugados: Obtiene el porcentaje de partidos jugados vs cancelados/postergados de un torneo. 

Resultados: Obtiene el detalle de resultados de los partidos disputados, filtrando por torneo si se especifica. 

Tarjetas por jugador (todos los torneos): Obtiene el consolidado de sanciones y tarjetas por jugador (general de todos los torneos). 

Tarjetas por jugador en el torneo: Obtiene el consolidado de sanciones y tarjetas por jugador en un torneo específico. 

Porcentaje de participación: Obtiene el porcentaje de participación de cada jugador según los partidos de su equipo en el torneo. 

Volver al Menú Principal:  

Te devuelve al menú principal. 

 


Al ingresar como planillero primero se le preguntará en qué torneo decide trabajar y posteriormente se le plantean al usuario las siguientes opciones: 

Registrar o consultar Planillas 

Registrar o modificar Goles 

Registrar o modificar Tarjetas 

Marcar partido como 'jugado' 

Ver Reportes 

Consultar partidos del torneo 

Cambiar de Torneo / Volver 

 

Registrar o consultar Planillas: 

Permite registrar o ver las planillas (jugadores que participaron del partido) 

Registrar o modificar Goles: 

Permite registrar, modificar o ver los goles de un partido 

Registrar o modificar Tarjetas: 

Permite registrar, modificar o ver las tarjetas de un partido 

Marcar partido como 'jugado': 

Permite marcar un partido como "jugado" 

Ver Reportes: 

Permite ver los reportes (los mismos que para el administrador) 

Consultar partidos del torneo:  

Permite ver los partidos del torneo, filtrando por fecha o estado 

Cambiar de Torneo / Volver 

Vuelve a la selección de torneo, desde donde se puede cerrar sesión 
