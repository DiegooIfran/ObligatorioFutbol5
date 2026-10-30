drop database if exists Obligatorio_Futbol5;
create database Obligatorio_Futbol5;
use Obligatorio_Futbol5;

create table login(
    correo varchar(50) primary key,
    contraseña varchar(20) not null,
    rol varchar(20) check (rol in ("administrador", "planillero")) not null
);
create table facultad(
    id_facultad int auto_increment primary key,
    nombre varchar(50) not null
);
create table jugador(
    ci int primary key,
    nombre varchar(20) not null,
    apellido varchar(20) not null,
    email varchar(50) not null,
    fecha_nacimiento date not null,
    id_facultad int not null,
    tipo varchar(20) check (tipo in ("grado","postgrado","docente","funcionario")) not null,
    constraint cedula_posible check ( ci>=10000000 and ci <= 60000000),
    foreign key (id_facultad) references facultad(id_facultad)
);
create table torneo(
    id_torneo int auto_increment primary key,
    nombre varchar(50) not null,
    anio int not null,
    semestre int not null,
    fecha_inicio date not null,
    fecha_fin date not null,
    estado varchar(20) check ( estado in ("inscripción","en curso","finalizado") ) not null,
    constraint chck_fechas check (
        anio >= 2026
        and year(fecha_inicio)=anio
        and year(fecha_fin)= anio
        and fecha_inicio<fecha_fin)
);
create table equipo(
    id_equipo int auto_increment primary key,
    nombre varchar(50)not null,
    id_torneo int not null,
    id_facultad int not null,
    ci_capitan int not null,
    foreign key (id_torneo) references torneo(id_torneo),
    foreign key (id_facultad) references facultad(id_facultad),
    foreign key (ci_capitan) references jugador(ci)
);
create table equipo_jugador_toreno(
    id_equipo int not null,
    ci_jugador int not null,
    id_toreno int not null,
    numero_camiseta int not null,
    primary key (id_equipo,ci_jugador,id_toreno),
    constraint chck_num_camiseta check (numero_camiseta<=99 and numero_camiseta>=1),
    constraint unica_torneo unique (ci_jugador, id_toreno),
    foreign key (id_equipo) references equipo(id_equipo),
    foreign key (ci_jugador) references jugador(ci),
    foreign key (id_toreno) references torneo(id_torneo)
);
create table complejo (
    id_complejo int auto_increment primary key,
    nombre varchar(50) not null,
    direccion varchar(50) not null,
    departamento varchar(50) not null
);
create table cancha (
    nombre_cancha varchar(50),
    id_complejo int not null,
    superficie varchar (20) check (superficie in ("sintetico", "parquet")) not null,
    techada bool not null,
    primary key (nombre_cancha,id_complejo),
    foreign key (id_complejo) references complejo(id_complejo)
);
create table turno(
    id_turno int auto_increment primary key,
    hora_inicio time not null,
    hora_fin time not null,
    constraint chk_turno_rango check (
        hora_inicio >= '18:00:00'
        and hora_fin <= '23:00:00'
        and MINUTE(hora_inicio) = 0 and SECOND(hora_inicio) = 0
        and TIMEDIFF(hora_fin, hora_inicio) = '01:00:00'
        and hora_fin>hora_inicio
));
create table partido(
    id_partido int auto_increment not null primary key,
    id_torneo int not null,
    numero_fecha int not null,
    id_equipo_local int not null,
    id_equipo_visitante int not null,
    dia date not null,
    id_turno int not null,
    nombre_cancha varchar(50) not null,
    id_complejo int not null,
    estado varchar(20) check ( estado in ("programado","jugado","postergado","cancelado")),
    constraint chk_equipos check (id_equipo_local <> id_equipo_visitante),
    constraint chck_fechas_partido check ( numero_fecha>= 1),
    foreign key (id_torneo) references torneo(id_torneo),
    foreign key (id_equipo_local) references equipo(id_equipo),
    foreign key (id_equipo_visitante) references equipo(id_equipo),
    foreign key (id_turno) references turno(id_turno),
    foreign key (nombre_cancha,id_complejo) references cancha(nombre_cancha,id_complejo)
);
create table planilla_partido(
    id_partido int not null,
    ci_jugador int not null,
    id_equipo int not null,
    primary key (id_partido,ci_jugador),
    foreign key (id_partido) references partido(id_partido),
    foreign key (ci_jugador) references jugador(ci)
);
create table gol(
    id_gol int auto_increment primary key,
    id_partido int not null,
    ci_jugador int not null,
    minuto int not null,
    autogol bool not null,
    constraint chck_minutos_gol check ( minuto <= 60 and minuto >= 1 ),
    foreign key (id_partido) references partido(id_partido),
    foreign key (ci_jugador) references jugador(ci)
);
create table tarjeta(
    id_tarjeta int auto_increment primary key,
    id_partido int not null,
    ci_jugador int not null,
    minuto int not null,
    color varchar(10) check ( color in ("amarilla","roja") ),
    constraint chck_minutos_tarj check ( minuto <= 60 and minuto >= 1 ),
    foreign key (id_partido) references partido(id_partido),
    foreign key (ci_jugador) references jugador(ci)
);
create table sancion_jugador(
    id_sancion int auto_increment primary key,
    ci_jugador int not null,
    id_torneo int not null,
    motivo varchar(50) check ( motivo in ("roja","acumulación de amarillas","disciplinaria") ),
    numero_fecha_inicio int not null,
    cantidad_fechas int not null,
    constraint chck_fechas_sanc check ( numero_fecha_inicio >= 1 and cantidad_fechas >=1 ),
    foreign key (ci_jugador) references jugador(ci),
    foreign key (id_torneo) references torneo(id_torneo)
);
-- ==========================================
-- TRIGGERS PARA LAS REGLAS DE NEGOCIO
-- ==========================================

DELIMITER //

-- Trigger 1: Validaciones al inscribir/modificar jugadores en planteles
CREATE TRIGGER trg_valida_inscripcion_jugador
BEFORE INSERT ON equipo_jugador_toreno
FOR EACH ROW
BEGIN
    DECLARE v_estado_torneo VARCHAR(20);
    DECLARE v_facultad_equipo INT;
    DECLARE v_facultad_jugador INT;
    DECLARE v_cant_jugadores INT;
    DECLARE v_cant_especiales INT;
    DECLARE v_tipo_jugador VARCHAR(20);

    -- 1. Validar que el torneo esté en etapa de inscripción
    SELECT estado INTO v_estado_torneo FROM torneo WHERE id_torneo = NEW.id_toreno;
    IF v_estado_torneo <> 'inscripción' THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Error: Los planteles solo pueden modificarse mientras el torneo está en inscripción.';
    END IF;

    -- 2. Validar que el jugador pertenezca a la misma facultad que el equipo
    SELECT id_facultad INTO v_facultad_equipo FROM equipo WHERE id_equipo = NEW.id_equipo;
    SELECT id_facultad, tipo INTO v_facultad_jugador, v_tipo_jugador FROM jugador WHERE ci = NEW.ci_jugador;

    IF v_facultad_equipo <> v_facultad_jugador THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Error: El jugador debe pertenecer a la misma facultad que representa el equipo.';
    END IF;

    -- 3. Validar límite máximo de jugadores de tipo docente o funcionario (máximo 2 por equipo)
    IF v_tipo_jugador IN ('docente', 'funcionario') THEN
        SELECT COUNT(*) INTO v_cant_especiales
        FROM equipo_jugador_toreno ej
        JOIN jugador j ON ej.ci_jugador = j.ci
        WHERE ej.id_equipo = NEW.id_equipo AND ej.id_toreno = NEW.id_toreno AND j.tipo IN ('docente', 'funcionario');

        IF v_cant_especiales > 2 THEN
            SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Error: El plantel admite como máximo 2 jugadores de tipo docente o funcionario.';
        END IF;
    END IF;

    -- 4. Validar el límite máximo del plantel (hasta 10 jugadores)
    SELECT COUNT(*) INTO v_cant_jugadores FROM equipo_jugador_toreno WHERE id_equipo = NEW.id_equipo AND id_toreno = NEW.id_toreno;
    IF v_cant_jugadores >= 10 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Error: El plantel no puede tener más de 10 jugadores.';
    END IF;
END //


-- Trigger 2: Validaciones al programar o actualizar un partido
CREATE TRIGGER trg_valida_partido
BEFORE INSERT ON partido
FOR EACH ROW
BEGIN
    DECLARE v_torneo_local INT;
    DECLARE v_torneo_visitante INT;
    DECLARE v_cant_local INT;
    DECLARE v_cant_visitante INT;
    DECLARE v_partidos_previos INT;
    DECLARE v_cancha_ocupada INT;

    -- 1. Validar que ambos equipos pertenezcan a la misma edición del torneo
    SELECT id_torneo INTO v_torneo_local FROM equipo WHERE id_equipo = NEW.id_equipo_local;
    SELECT id_torneo INTO v_torneo_visitante FROM equipo WHERE id_equipo = NEW.id_equipo_visitante;

    IF v_torneo_local <> NEW.id_torneo OR v_torneo_visitante <> NEW.id_torneo THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Error: Ambos equipos deben pertenecer al torneo del partido.';
    END IF;

    -- 2. Validar que tengan al menos 5 jugadores en su plantel
    SELECT COUNT(*) INTO v_cant_local FROM equipo_jugador_toreno WHERE id_equipo = NEW.id_equipo_local AND id_toreno = NEW.id_torneo;
    SELECT COUNT(*) INTO v_cant_visitante FROM equipo_jugador_toreno WHERE id_equipo = NEW.id_equipo_visitante AND id_toreno = NEW.id_torneo;

    IF v_cant_local < 5 OR v_cant_visitante < 5 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Error: Ambos equipos deben tener al menos 5 jugadores en su plantel.';
    END IF;

    -- 3. Un equipo no se enfrente a sí mismo
    IF NEW.id_equipo_local = NEW.id_equipo_visitante THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Error: Un equipo no puede enfrentarse a sí mismo.';
    END IF;

    -- 4. Un equipo no se enfrente a un rival con el que ya tenga un partido en esa edición (salvo cancelado)
    SELECT COUNT(*) INTO v_partidos_previos
    FROM partido
    WHERE id_torneo = NEW.id_torneo
      AND estado <> 'cancelado'
      AND ((id_equipo_local = NEW.id_equipo_local AND id_equipo_visitante = NEW.id_equipo_visitante)
        OR (id_equipo_local = NEW.id_equipo_visitante AND id_equipo_visitante = NEW.id_equipo_local));

    IF v_partidos_previos > 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Error: Los equipos ya tienen un partido programado/jugado/postergado en esta edición.';
    END IF;

    -- 5. Un equipo no juegue más de un partido en la misma fecha del torneo
    SELECT COUNT(*) INTO v_partidos_previos
    FROM partido
    WHERE id_torneo = NEW.id_torneo
      AND numero_fecha = NEW.numero_fecha
      AND estado <> 'cancelado'
      AND (id_equipo_local IN (NEW.id_equipo_local, NEW.id_equipo_visitante)
        OR id_equipo_visitante IN (NEW.id_equipo_local, NEW.id_equipo_visitante));

    IF v_partidos_previos > 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Error: Uno de los equipos ya tiene un partido asignado en esta misma fecha del torneo.';
    END IF;

    -- 6. Una cancha no tenga más de un partido asignado en el mismo día y turno
    SELECT COUNT(*) INTO v_cancha_ocupada
    FROM partido
    WHERE dia = NEW.dia
      AND id_turno = NEW.id_turno
      AND nombre_cancha = NEW.nombre_cancha
      AND id_complejo = NEW.id_complejo
      AND estado <> 'cancelado';

    IF v_cancha_ocupada > 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Error: La cancha ya está ocupada en ese día y turno.';
    END IF;
END //

-- 3. TRIGGER: Generar sanción automática por tarjeta Roja o Acumulación de Amarillas

CREATE TRIGGER trg_auto_sancion_tarjeta
AFTER INSERT ON tarjeta
FOR EACH ROW
BEGIN
    DECLARE v_id_torneo INT;
    DECLARE v_num_fecha INT;
    DECLARE v_cant_amarillas INT;

    -- Obtener el torneo y la fecha del partido donde se sacó la tarjeta
    SELECT id_torneo, numero_fecha INTO v_id_torneo, v_num_fecha
    FROM partido
    WHERE id_partido = NEW.id_partido;

    -- CASO A: Tarjeta Roja directa
    IF NEW.color = 'roja' THEN
        INSERT INTO sancion_jugador (ci_jugador, id_torneo, motivo, numero_fecha_inicio, cantidad_fechas)
        VALUES (NEW.ci_jugador, v_id_torneo, 'roja', v_num_fecha + 1, 1);

    -- CASO B: Tarjeta Amarilla (control de acumulación)
    ELSEIF NEW.color = 'amarilla' THEN
        -- Contar cuántas amarillas acumuladas tiene el jugador en este torneo
        SELECT COUNT(*) INTO v_cant_amarillas
        FROM tarjeta t
        JOIN partido p ON t.id_partido = p.id_partido
        WHERE t.ci_jugador = NEW.ci_jugador
          AND t.color = 'amarilla'
          AND p.id_torneo = v_id_torneo;

        -- Si llega a 3, 6, 9... se sanciona automáticamente por 1 fecha (la siguiente)
        IF v_cant_amarillas % 3 = 0 THEN
            INSERT INTO sancion_jugador (ci_jugador, id_torneo, motivo, numero_fecha_inicio, cantidad_fechas)
            VALUES (NEW.ci_jugador, v_id_torneo, 'acumulación de amarillas', v_num_fecha + 1, 1);
        END IF;
    END IF;
END //

-- 4. TRIGGER: Evitar que un jugador suspendido figure en la planilla del partido

CREATE TRIGGER trg_valida_suspension_planilla
BEFORE INSERT ON planilla_partido
FOR EACH ROW
BEGIN
    DECLARE v_id_torneo INT;
    DECLARE v_num_fecha INT;
    DECLARE v_sanciones_activas INT;

    -- Obtener el torneo y número de fecha del partido al que se intenta agregar al jugador
    SELECT id_torneo, numero_fecha INTO v_id_torneo, v_num_fecha
    FROM partido
    WHERE id_partido = NEW.id_partido;

    -- Verificar si la fecha del partido cae dentro del rango de alguna sanción activa del jugador
    SELECT COUNT(*) INTO v_sanciones_activas
    FROM sancion_jugador
    WHERE ci_jugador = NEW.ci_jugador
      AND id_torneo = v_id_torneo
      AND v_num_fecha >= numero_fecha_inicio
      AND v_num_fecha < (numero_fecha_inicio + cantidad_fechas);

    -- Si existe una sanción activa para esta fecha, se bloquea la inserción
    IF v_sanciones_activas > 0 THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Error: El jugador se encuentra suspendido para esta fecha y no puede ser incluido en la planilla.';
    END IF;
END //

DELIMITER ;

-- Usuario para administradores (acceso completo)

CREATE USER IF NOT EXISTS 'usr_admin'@'localhost' IDENTIFIED BY 'AdminPass123!';

GRANT ALL PRIVILEGES ON Obligatorio_Futbol5.* TO 'usr_admin'@'localhost';

-- Usuario para planilleros (permisos limitados para cargar planillas, goles y tarjetas)

CREATE USER IF NOT EXISTS 'usr_planillero'@'localhost' IDENTIFIED BY 'PlanilleroPass123!';

GRANT SELECT ON Obligatorio_Futbol5.* TO 'usr_planillero'@'localhost';

GRANT INSERT, UPDATE ON Obligatorio_Futbol5.planilla_partido TO 'usr_planillero'@'localhost';

GRANT INSERT, UPDATE ON Obligatorio_Futbol5.gol TO 'usr_planillero'@'localhost';

GRANT INSERT, UPDATE ON Obligatorio_Futbol5.tarjeta TO 'usr_planillero'@'localhost';

GRANT UPDATE (estado) ON Obligatorio_Futbol5.partido TO 'usr_planillero'@'localhost';

FLUSH PRIVILEGES;

-- Inserciones de datos base (6 equipos y 3 fehcas)
-- ==========================================
-- 1. USUARIOS
-- ==========================================
INSERT INTO login (correo, contrasena, rol) VALUES
    ('admin@ucu.edu.uy', 'admin123', 'administrador'), -- admin
    ('planillero1@ucu.edu.uy', 'planillero123', 'planillero'); -- planillero

-- ==========================================
-- 2. FACULTADES
-- ==========================================
INSERT INTO facultad (nombre) VALUES
('Facultad de Ingeniería'),
('Facultad de Ciencias Económicas');


-- ==========================================
-- 3. JUGADORES (7 por equipo = 42 jugadores, CI de 8 dígitos)
-- ==========================================
-- Equipo 1: Ingeniería FC (CI: 10001001 al 10001007)
INSERT INTO jugador (ci, nombre, apellido, email, fecha_nacimiento, id_facultad, tipo) VALUES
(10001001, 'Lucas', 'Pérez', 'lucas.p@fing.edu.uy', '2002-05-12', 1, 'grado'),
(10001002, 'Mateo', 'Gómez', 'mateo.g@fing.edu.uy', '2001-08-20', 1, 'grado'),
(10001003, 'Joaquín', 'Rodríguez', 'joaquin.r@fing.edu.uy', '2000-02-15', 1, 'grado'),
(10001004, 'Federico', 'Silva', 'federico.s@fing.edu.uy', '1999-11-03', 1, 'grado'),
(10001005, 'Bruno', 'Martínez', 'bruno.m@fing.edu.uy', '2003-01-25', 1, 'grado'),
(10001006, 'Facundo', 'López', 'facundo.l@fing.edu.uy', '1998-07-30', 1, 'postgrado'),
(10001007, 'Ignacio', 'Díaz', 'ignacio.d@fing.edu.uy', '1985-04-10', 1, 'docente');

-- Equipo 2: Algoritmos United (CI: 10001008 al 10001014)
INSERT INTO jugador (ci, nombre, apellido, email, fecha_nacimiento, id_facultad, tipo) VALUES
(10001008, 'Santiago', 'Fernández', 'santi.f@fing.edu.uy', '2001-03-14', 1, 'grado'),
(10001009, 'Agustín', 'Ruiz', 'agustin.r@fing.edu.uy', '2002-09-09', 1, 'grado'),
(10001010, 'Gonzalo', 'Suárez', 'gonzalo.s@fing.edu.uy', '2000-12-01', 1, 'grado'),
(10001011, 'Martín', 'Acosta', 'martin.a@fing.edu.uy', '2001-06-18', 1, 'grado'),
(10001012, 'Tomás', 'Castro', 'tomas.c@fing.edu.uy', '1997-10-05', 1, 'funcionario'),
(10001013, 'Nicolás', 'Mendoza', 'nicolas.m@fing.edu.uy', '2002-04-22', 1, 'grado'),
(10001014, 'Valeria', 'Pintos', 'valeria.p@fing.edu.uy', '2001-12-12', 1, 'grado');

-- Equipo 3: Redes F.C. (CI: 10001015 al 10001021)
INSERT INTO jugador (ci, nombre, apellido, email, fecha_nacimiento, id_facultad, tipo) VALUES
(10001015, 'Camila', 'Sosa', 'camila.s@fing.edu.uy', '2002-07-07', 1, 'grado'),
(10001016, 'Sofía', 'Pereyra', 'sofia.p@fing.edu.uy', '2001-01-15', 1, 'grado'),
(10001017, 'Valentina', 'Ramírez', 'valentina.r@fing.edu.uy', '2000-09-19', 1, 'grado'),
(10001018, 'Lucía', 'Medina', 'lucia.m@fing.edu.uy', '1999-05-28', 1, 'grado'),
(10001019, 'Renzo', 'Bica', 'renzo.b@fing.edu.uy', '2002-11-11', 1, 'grado'),
(10001020, 'Damián', 'Viera', 'damian.v@fing.edu.uy', '1996-03-04', 1, 'docente'),
(10001021, 'Emiliano', 'Braga', 'emiliano.b@fing.edu.uy', '2001-08-30', 1, 'grado');

-- Equipo 4: Economía Juniors (CI: 20002001 al 20002007)
INSERT INTO jugador (ci, nombre, apellido, email, fecha_nacimiento, id_facultad, tipo) VALUES
(20002001, 'Carlos', 'Giménez', 'carlos.g@fcea.edu.uy', '2001-02-10', 2, 'grado'),
(20002002, 'Andrés', 'Blanco', 'andres.b@fcea.edu.uy', '2000-06-15', 2, 'grado'),
(20002003, 'Diego', 'Ferreira', 'diego.f@fcea.edu.uy', '1999-12-20', 2, 'grado'),
(20002004, 'Manuel', 'Machado', 'manuel.m@fcea.edu.uy', '2002-04-05', 2, 'grado'),
(20002005, 'Esteban', 'Correa', 'esteban.c@fcea.edu.uy', '2001-09-17', 2, 'grado'),
(20002006, 'Mariana', 'Núñez', 'mariana.n@fcea.edu.uy', '1997-03-25', 2, 'funcionario'),
(20002007, 'Pablo', 'Iglesias', 'pablo.i@fcea.edu.uy', '1988-08-14', 2, 'docente');

-- Equipo 5: Finanzas City (CI: 20002008 al 20002014)
INSERT INTO jugador (ci, nombre, apellido, email, fecha_nacimiento, id_facultad, tipo) VALUES
(20002008, 'Rodrigo', 'Pintos', 'rodrigo.p@fcea.edu.uy', '2002-01-05', 2, 'grado'),
(20002009, 'Mauricio', 'Cardozo', 'mauricio.c@fcea.edu.uy', '2000-05-11', 2, 'grado'),
(20002010, 'Gastón', 'Larrosa', 'gaston.l@fcea.edu.uy', '2001-10-30', 2, 'grado'),
(20002011, 'Maximiliano', 'Montero', 'maxi.m@fcea.edu.uy', '1999-07-19', 2, 'grado'),
(20002012, 'Florencia', 'Acosta', 'florencia.a@fcea.edu.uy', '2002-03-12', 2, 'grado'),
(20002013, 'Bruno', 'Tabárez', 'bruno.t@fcea.edu.uy', '2001-11-21', 2, 'grado'),
(20002014, 'Lucas', 'Olivera', 'lucas.o@fcea.edu.uy', '2000-08-08', 2, 'grado');

-- Equipo 6: Contadores F.C. (CI: 20002015 al 20002021)
INSERT INTO jugador (ci, nombre, apellido, email, fecha_nacimiento, id_facultad, tipo) VALUES
(20002015, 'Agustina', 'Pérez', 'agustina.p@fcea.edu.uy', '2002-06-14', 2, 'grado'),
(20002016, 'Victoria', 'García', 'victoria.g@fcea.edu.uy', '2001-09-02', 2, 'grado'),
(20002017, 'Natalia', 'Benítez', 'natalia.b@fcea.edu.uy', '2000-04-18', 2, 'grado'),
(20002018, 'Lorena', 'Silva', 'lorena.s@fcea.edu.uy', '1999-12-05', 2, 'grado'),
(20002019, 'Javier', 'Rivas', 'javier.r@fcea.edu.uy', '1995-02-28', 2, 'docente'),
(20002020, 'Gabriel', 'Domínguez', 'gabriel.d@fcea.edu.uy', '2001-07-22', 2, 'grado'),
(20002021, 'Enzo', 'Peralta', 'enzo.p@fcea.edu.uy', '2002-10-10', 2, 'grado');


-- ==========================================
-- 4. TORNEO
-- ==========================================
INSERT INTO torneo (nombre, anio, semestre, fecha_inicio, fecha_fin, estado) VALUES
('Torneo Apertura Futsal 2026', 2026, 1, '2026-03-01', '2026-07-01', 'inscripción');


-- ==========================================
-- 5. EQUIPOS
-- ==========================================
INSERT INTO equipo (nombre, id_torneo, id_facultad, ci_capitan) VALUES
('Ingeniería FC', 1, 1, 10001001),
('Algoritmos United', 1, 1, 10001008),
('Redes F.C.', 1, 1, 10001015),
('Economía Juniors', 1, 2, 20002001),
('Finanzas City', 1, 2, 20002008),
('Contadores F.C.', 1, 2, 20002015);


-- ==========================================
-- 6. INSCRIPCIÓN DE JUGADORES A EQUIPO Y TORNEO
-- ==========================================
-- Ingeniería FC (id_equipo = 1)
INSERT INTO equipo_jugador_toreno (id_equipo, ci_jugador, id_toreno, numero_camiseta) VALUES
(1, 10001001, 1, 10), (1, 10001002, 1, 5), (1, 10001003, 1, 8), (1, 10001004, 1, 9), (1, 10001005, 1, 4), (1, 10001006, 1, 7), (1, 10001007, 1, 1);

-- Algoritmos United (id_equipo = 2)
INSERT INTO equipo_jugador_toreno (id_equipo, ci_jugador, id_toreno, numero_camiseta) VALUES
(2, 10001008, 1, 10), (2, 10001009, 1, 2), (2, 10001010, 1, 3), (2, 10001011, 1, 6), (2, 10001012, 1, 7), (2, 10001013, 1, 9), (2, 10001014, 1, 11);

-- Redes F.C. (id_equipo = 3)
INSERT INTO equipo_jugador_toreno (id_equipo, ci_jugador, id_toreno, numero_camiseta) VALUES
(3, 10001015, 1, 1), (3, 10001016, 1, 4), (3, 10001017, 1, 5), (3, 10001018, 1, 8), (3, 10001019, 1, 10), (3, 10001020, 1, 14), (3, 10001021, 1, 9);

-- Economía Juniors (id_equipo = 4)
INSERT INTO equipo_jugador_toreno (id_equipo, ci_jugador, id_toreno, numero_camiseta) VALUES
(4, 20002001, 1, 10), (4, 20002002, 1, 2), (4, 20002003, 1, 3), (4, 20002004, 1, 4), (4, 20002005, 1, 7), (4, 20002006, 1, 9), (4, 20002007, 1, 12);

-- Finanzas City (id_equipo = 5)
INSERT INTO equipo_jugador_toreno (id_equipo, ci_jugador, id_toreno, numero_camiseta) VALUES
(5, 20002008, 1, 1), (5, 20002009, 1, 5), (5, 20002010, 1, 6), (5, 20002011, 1, 8), (5, 20002012, 1, 10), (5, 20002013, 1, 11), (5, 20002014, 1, 7);

-- Contadores F.C. (id_equipo = 6)
INSERT INTO equipo_jugador_toreno (id_equipo, ci_jugador, id_toreno, numero_camiseta) VALUES
(6, 20002015, 1, 9), (6, 20002016, 1, 2), (6, 20002017, 1, 3), (6, 20002018, 1, 4), (6, 20002019, 1, 10), (6, 20002020, 1, 7), (6, 20002021, 1, 11);


-- ==========================================
-- 7. COMPLEJO Y CANCHAS
-- ==========================================
INSERT INTO complejo (nombre, direccion, departamento) VALUES
('Complejo Universitario Campus 5', 'Av. R. Italia 2300', 'Montevideo');

INSERT INTO cancha (nombre_cancha, id_complejo, superficie, techada) VALUES
('Cancha Principal', 1, 'sintetico', true),
('Cancha Anexa', 1, 'parquet', false);


-- ==========================================
-- 8. TURNOS
-- ==========================================
INSERT INTO turno (hora_inicio, hora_fin) VALUES
('18:00:00', '19:00:00'),
('19:00:00', '20:00:00'),
('20:00:00', '21:00:00'),
('21:00:00', '22:00:00'),
('22:00:00', '23:00:00');


-- ==========================================
-- 9. PARTIDOS (3 Fechas - Todos Jugados)
-- ==========================================
-- FECHA 1
INSERT INTO partido (id_torneo, numero_fecha, id_equipo_local, id_equipo_visitante, dia, id_turno, nombre_cancha, id_complejo, estado) VALUES
(1, 1, 1, 2, '2026-03-10', 1, 'Cancha Principal', 1, 'jugado'),
(1, 1, 3, 4, '2026-03-10', 2, 'Cancha Principal', 1, 'jugado'),
(1, 1, 5, 6, '2026-03-10', 3, 'Cancha Anexa', 1, 'jugado');

-- FECHA 2
INSERT INTO partido (id_torneo, numero_fecha, id_equipo_local, id_equipo_visitante, dia, id_turno, nombre_cancha, id_complejo, estado) VALUES
(1, 2, 1, 3, '2026-03-17', 1, 'Cancha Principal', 1, 'jugado'),
(1, 2, 2, 5, '2026-03-17', 2, 'Cancha Principal', 1, 'jugado'),
(1, 2, 4, 6, '2026-03-17', 3, 'Cancha Anexa', 1, 'jugado');

-- FECHA 3
INSERT INTO partido (id_torneo, numero_fecha, id_equipo_local, id_equipo_visitante, dia, id_turno, nombre_cancha, id_complejo, estado) VALUES
(1, 3, 1, 6, '2026-03-24', 1, 'Cancha Principal', 1, 'jugado'),
(1, 3, 2, 4, '2026-03-24', 2, 'Cancha Principal', 1, 'jugado'),
(1, 3, 3, 5, '2026-03-24', 3, 'Cancha Anexa', 1, 'jugado');


-- ==========================================
-- 10. PLANILLAS DE PARTIDOS
-- ==========================================
-- Partido 1 (Ingeniería vs Algoritmos)
INSERT INTO planilla_partido (id_partido, ci_jugador, id_equipo) VALUES
(1, 10001001, 1), (1, 10001002, 1), (1, 10001003, 1), (1, 10001004, 1), (1, 10001005, 1),
(1, 10001008, 2), (1, 10001009, 2), (1, 10001010, 2), (1, 10001011, 2), (1, 10001012, 2);

-- Partido 2 (Redes vs Economía)
INSERT INTO planilla_partido (id_partido, ci_jugador, id_equipo) VALUES
(2, 10001015, 3), (2, 10001016, 3), (2, 10001017, 3), (2, 10001018, 3), (2, 10001019, 3),
(2, 20002001, 4), (2, 20002002, 4), (2, 20002003, 4), (2, 20002004, 4), (2, 20002005, 4);

-- Partido 3 (Finanzas vs Contadores)
INSERT INTO planilla_partido (id_partido, ci_jugador, id_equipo) VALUES
(3, 20002008, 5), (3, 20002009, 5), (3, 20002010, 5), (3, 20002011, 5), (3, 20002012, 5),
(3, 20002015, 6), (3, 20002016, 6), (3, 20002017, 6), (3, 20002018, 6), (3, 20002020, 6);

-- Partido 4 (Ingeniería vs Redes)
INSERT INTO planilla_partido (id_partido, ci_jugador, id_equipo) VALUES
(4, 10001001, 1), (4, 10001002, 1), (4, 10001003, 1), (4, 10001004, 1), (4, 10001006, 1),
(4, 10001015, 3), (4, 10001016, 3), (4, 10001017, 3), (4, 10001018, 3), (4, 10001020, 3);

-- Partido 5 (Algoritmos vs Finanzas)
INSERT INTO planilla_partido (id_partido, ci_jugador, id_equipo) VALUES
(5, 10001008, 2), (5, 10001009, 2), (5, 10001010, 2), (5, 10001013, 2), (5, 10001014, 2),
(5, 20002008, 5), (5, 20002009, 5), (5, 20002010, 5), (5, 20002013, 5), (5, 20002014, 5);

-- Partido 6 (Economía vs Contadores)
INSERT INTO planilla_partido (id_partido, ci_jugador, id_equipo) VALUES
(6, 20002001, 4), (6, 20002002, 4), (6, 20002003, 4), (6, 20002006, 4), (6, 20002007, 4),
(6, 20002015, 6), (6, 20002016, 6), (6, 20002017, 6), (6, 20002019, 6), (6, 20002021, 6);

-- Partido 7 (Ingeniería vs Contadores)
INSERT INTO planilla_partido (id_partido, ci_jugador, id_equipo) VALUES
(7, 10001001, 1), (7, 10001002, 1), (7, 10001003, 1), (7, 10001004, 1), (7, 10001005, 1),
(7, 20002015, 6), (7, 20002016, 6), (7, 20002017, 6), (7, 20002018, 6), (7, 20002020, 6);

-- Partido 8 (Algoritmos vs Economía)
INSERT INTO planilla_partido (id_partido, ci_jugador, id_equipo) VALUES
(8, 10001008, 2), (8, 10001009, 2), (8, 10001010, 2), (8, 10001011, 2), (8, 10001012, 2),
(8, 20002001, 4), (8, 20002002, 4), (8, 20002003, 4), (8, 20002004, 4), (8, 20002005, 4);

-- Partido 9 (Redes vs Finanzas)
INSERT INTO planilla_partido (id_partido, ci_jugador, id_equipo) VALUES
(9, 10001015, 3), (9, 10001016, 3), (9, 10001017, 3), (9, 10001018, 3), (9, 10001019, 3),
(9, 20002008, 5), (9, 20002009, 5), (9, 20002010, 5), (9, 20002011, 5), (9, 20002012, 5);


-- ==========================================
-- 11. GOLES
-- ==========================================
INSERT INTO gol (id_partido, ci_jugador, minuto, autogol) VALUES
-- Partido 1 (Ingeniería 3 - 1 Algoritmos)
(1, 10001001, 12, false),
(1, 10001002, 25, false),
(1, 10001001, 44, false),
(1, 10001008, 50, false),

-- Partido 2 (Redes 2 - 2 Economía)
(2, 10001015, 10, false),
(2, 10001018, 30, false),
(2, 20002001, 18, false),
(2, 20002003, 42, false),

-- Partido 3 (Finanzas 4 - 0 Contadores)
(3, 20002008, 5, false),
(3, 20002008, 22, false),
(3, 20002009, 37, false),
(3, 20002011, 55, false),

-- Partido 4 (Ingeniería 1 - 3 Redes)
(4, 10001003, 20, false),
(4, 10001016, 14, false),
(4, 10001017, 33, false),
(4, 10001015, 48, false),

-- Partido 5 (Algoritmos 2 - 1 Finanzas)
(5, 10001008, 15, false),
(5, 10001010, 40, false),
(5, 20002010, 28, false),

-- Partido 6 (Economía 0 - 1 Contadores)
(6, 20002015, 35, false),

-- Partido 7 (Ingeniería 2 - 2 Contadores)
(7, 10001001, 8, false),
(7, 10001004, 52, false),
(7, 20002016, 19, false),
(7, 20002017, 41, false),

-- Partido 8 (Algoritmos 3 - 2 Economía)
(8, 10001009, 11, true), -- gol en contra
(8, 10001011, 26, false),
(8, 10001012, 54, false),
(8, 20002001, 30, false),
(8, 20002002, 49, false),

-- Partido 9 (Redes 1 - 1 Finanzas)
(9, 10001018, 22, false),
(9, 20002008, 38, false);


-- ==========================================
-- 12. TARJETAS
-- ==========================================
INSERT INTO tarjeta (id_partido, ci_jugador, minuto, color) VALUES
(1, 10001011, 58, 'roja'),
(2, 20002002, 30, 'amarilla'),
(4, 10001006, 50, 'roja'),
(5, 20002014, 25, 'amarilla'),
(7, 20002016, 45, 'roja');


