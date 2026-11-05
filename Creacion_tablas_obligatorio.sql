drop database if exists Obligatorio_Futbol5;
create database Obligatorio_Futbol5;
use Obligatorio_Futbol5;

create table login(
    correo varchar(50) primary key,
    contrasena varchar(20) not null,
    rol varchar(20) check (rol in ('administrador', 'planillero')) not null
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
    tipo varchar(20) check (tipo in ('grado','postgrado','docente','funcionario')) not null,
    constraint uq_ci_facultad unique (ci, id_facultad), -- necesario para fk en equipo
    constraint cedula_posible check ( ci>=10000000 and ci <= 60000000),
    foreign key (id_facultad) references facultad(id_facultad)
);
create table torneo(
    id_torneo int auto_increment primary key,
    nombre varchar(50) not null,
    anio int not null,
    semestre int not null check ( semestre = 1 or semestre = 2 ),
    fecha_inicio date not null,
    fecha_fin date not null,
    estado varchar(20) check ( estado in ('inscripción','en curso','finalizado') ) not null,
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
    constraint uq_equipo_torneo unique (id_equipo, id_torneo), -- necesario para fk en ejt
    constraint uq_nombre_torneo unique (nombre, id_torneo),
    foreign key (id_torneo) references torneo(id_torneo),
    foreign key (ci_capitan, id_facultad) references jugador(ci,id_facultad) -- asegura que el capitan pertenezca a la facultad
);
create table equipo_jugador_torneo(
    id_equipo int not null,
    ci_jugador int not null,
    id_torneo int not null,
    numero_camiseta int not null,
    primary key (id_equipo,ci_jugador,id_torneo),
    constraint chck_num_camiseta check (numero_camiseta<=99 and numero_camiseta>=1),
    constraint unica_torneo unique (ci_jugador, id_torneo),
    constraint uq_equipo_jugador unique (id_equipo, ci_jugador), -- necesario para fk en pp
    constraint uq_camiseta_equipo unique (id_equipo, numero_camiseta), -- un solo jugador por numero de camiseta
    foreign key (id_equipo, id_torneo) references equipo(id_equipo, id_torneo),
    foreign key (ci_jugador) references jugador(ci)
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
    superficie varchar (20) check (superficie in ('sintetico', 'parquet')) not null,
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
    estado varchar(20) check ( estado in ('programado','jugado','postergado','cancelado')) not null ,
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
    foreign key (id_equipo, ci_jugador) references equipo_jugador_torneo(id_equipo, ci_jugador)
);
create table gol(
    id_gol int auto_increment primary key,
    id_partido int not null,
    ci_jugador int not null,
    minuto int not null,
    autogol bool not null,
    constraint chck_minutos_gol check ( minuto <= 60 and minuto >= 1 ),
    foreign key (id_partido, ci_jugador) references planilla_partido(id_partido, ci_jugador)
);
create table tarjeta(
    id_tarjeta int auto_increment primary key,
    id_partido int not null,
    ci_jugador int not null,
    minuto int not null,
    color varchar(10) check ( color in ('amarilla','roja') ) not null,
    constraint chck_minutos_tarj check ( minuto <= 60 and minuto >= 1 ),
    foreign key (id_partido, ci_jugador) references planilla_partido(id_partido, ci_jugador)
);
create table sancion_jugador(
    id_sancion int auto_increment primary key,
    ci_jugador int not null,
    id_torneo int not null,
    motivo varchar(50) check ( motivo in ('roja','acumulación de amarillas','disciplinaria') ) not null,
    numero_fecha_inicio int not null,
    cantidad_fechas int not null,
    constraint chck_fechas_sanc check ( numero_fecha_inicio >= 1 and cantidad_fechas >=1 ),
    foreign key (ci_jugador, id_torneo) references equipo_jugador_torneo(ci_jugador, id_torneo)
);
-- ==========================================
-- TRIGGERS PARA LAS REGLAS DE NEGOCIO
-- ==========================================

DELIMITER //

-- Trigger 1: Validaciones al inscribir/modificar jugadores en planteles
CREATE TRIGGER trg_valida_inscripcion_jugador
BEFORE INSERT ON equipo_jugador_torneo
FOR EACH ROW
BEGIN
    DECLARE v_estado_torneo VARCHAR(20);
    DECLARE v_facultad_equipo INT;
    DECLARE v_facultad_jugador INT;
    DECLARE v_cant_jugadores INT;
    DECLARE v_cant_especiales INT;
    DECLARE v_tipo_jugador VARCHAR(20);

    -- 1. Validar que el torneo esté en etapa de inscripción
    SELECT estado INTO v_estado_torneo FROM torneo WHERE id_torneo = NEW.id_torneo;
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
        FROM equipo_jugador_torneo ej
        JOIN jugador j ON ej.ci_jugador = j.ci
        WHERE ej.id_equipo = NEW.id_equipo AND ej.id_torneo = NEW.id_torneo AND j.tipo IN ('docente', 'funcionario');

        IF v_cant_especiales >= 2 THEN
            SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Error: El plantel admite como máximo 2 jugadores de tipo docente o funcionario.';
        END IF;
    END IF;

    -- 4. Validar el límite máximo del plantel (hasta 10 jugadores)
    SELECT COUNT(*) INTO v_cant_jugadores FROM equipo_jugador_torneo WHERE id_equipo = NEW.id_equipo AND id_torneo = NEW.id_torneo;
    IF v_cant_jugadores >= 10 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Error: El plantel no puede tener más de 10 jugadores.';
    END IF;
END //


-- Trigger 2: Validaciones al programar un partido
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
    declare v_fecha_inicio_t date;
    declare v_fecha_fin_t date;

-- 1. Validar que ambos equipos pertenezcan a la misma edición del torneo
    SELECT id_torneo INTO v_torneo_local FROM equipo WHERE id_equipo = NEW.id_equipo_local;
    SELECT id_torneo INTO v_torneo_visitante FROM equipo WHERE id_equipo = NEW.id_equipo_visitante;

    IF v_torneo_local <> NEW.id_torneo OR v_torneo_visitante <> NEW.id_torneo THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Error: Ambos equipos deben pertenecer al torneo del partido.';
    END IF;

-- 2. Validar que tengan al menos 5 jugadores en su plantel
    SELECT COUNT(*) INTO v_cant_local FROM equipo_jugador_torneo WHERE id_equipo = NEW.id_equipo_local AND id_torneo = NEW.id_torneo;
    SELECT COUNT(*) INTO v_cant_visitante FROM equipo_jugador_torneo WHERE id_equipo = NEW.id_equipo_visitante AND id_torneo = NEW.id_torneo;

    IF v_cant_local < 5 OR v_cant_visitante < 5 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Error: Ambos equipos deben tener al menos 5 jugadores en su plantel.';
    END IF;


-- 3. Un equipo no se enfrente a un rival con el que ya tenga un partido en esa edición (salvo cancelado)
    SELECT COUNT(*) INTO v_partidos_previos
    FROM partido
    WHERE id_torneo = NEW.id_torneo
      AND estado <> 'cancelado'
      AND ((id_equipo_local = NEW.id_equipo_local AND id_equipo_visitante = NEW.id_equipo_visitante)
        OR (id_equipo_local = NEW.id_equipo_visitante AND id_equipo_visitante = NEW.id_equipo_local));

    IF v_partidos_previos > 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Error: Los equipos ya tienen un partido programado/jugado/postergado en esta edición.';
    END IF;

-- 4. Un equipo no juegue más de un partido en la misma fecha del torneo
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

-- 5. Una cancha no tenga más de un partido asignado en el mismo día y turno
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

-- 6. fecha del partido entre fecha inicio del torneo y fecha fin
    select fecha_inicio, fecha_fin into v_fecha_inicio_t, v_fecha_fin_t
    from torneo
    where id_torneo = NEW.id_torneo;

    IF NEW.dia > v_fecha_fin_t or NEW.dia < v_fecha_inicio_t THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Error: La fecha del partido debe estar entre las fechas de inicio y fin del torneo.';
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

CREATE TRIGGER trg_valida_planilla
BEFORE INSERT ON planilla_partido
FOR EACH ROW
BEGIN
    DECLARE v_id_torneo INT;
    DECLARE v_num_fecha INT;
    DECLARE v_local INT;
    DECLARE v_visitante INT;
    DECLARE v_sanciones_activas INT;
    DECLARE v_estado_partido VARCHAR(20);

    SELECT id_torneo, numero_fecha, id_equipo_local, id_equipo_visitante, estado
    INTO v_id_torneo, v_num_fecha, v_local, v_visitante, v_estado_partido
    FROM partido
    WHERE id_partido = NEW.id_partido;

    -- verificar que se haya jugado el partido
    if v_estado_partido <> 'jugado' then
                SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Error: El partido no se ha jugado.';
    END IF;

    -- El equipo debe ser uno de los dos que juegan el partido
    IF NEW.id_equipo NOT IN (v_local, v_visitante) THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Error: El equipo no participa en este partido.';
    END IF;

    -- Suspensión vigente
    SELECT COUNT(*) INTO v_sanciones_activas
    FROM sancion_jugador
    WHERE ci_jugador = NEW.ci_jugador
      AND id_torneo = v_id_torneo
      AND v_num_fecha >= numero_fecha_inicio
      AND v_num_fecha < (numero_fecha_inicio + cantidad_fechas); -- es menor y no menor o igual porque fecha inicio representa el primer partido que no puede jugar

    IF v_sanciones_activas > 0 THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Error: El jugador se encuentra suspendido para esta fecha y no puede ser incluido en la planilla.';
    END IF;
END //

-- 5. Trigger: Verificar que se haya jugado el partido
CREATE TRIGGER trg_gol_jugador_valido
BEFORE INSERT ON gol
FOR EACH ROW
BEGIN
    DECLARE v_estado_partido VARCHAR(20);

    SELECT estado
    INTO v_estado_partido
    FROM partido
    WHERE id_partido = NEW.id_partido;

        -- verificar que se haya jugado el partido
    if v_estado_partido <> 'jugado' then
                SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Error: El partido no se ha jugado.';
    END IF;

end //

-- 6. Trigger: Verificar que se haya jugado el partido
CREATE TRIGGER trg_tarjeta_jugador_valido
BEFORE INSERT ON tarjeta
FOR EACH ROW
BEGIN
    DECLARE v_estado_partido VARCHAR(20);

    SELECT estado
    INTO v_estado_partido
    FROM partido
    WHERE id_partido = NEW.id_partido;

        -- verificar que se haya jugado el partido
    if v_estado_partido <> 'jugado' then
                SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Error: El partido no se ha jugado.';
    END IF;

end //

-- ==========================================
-- triggers de update y delete
-- ==========================================

-- update en partido
CREATE TRIGGER trg_partido_upd
BEFORE UPDATE ON partido
FOR EACH ROW
BEGIN
    DECLARE v_planilla INT;
    DECLARE v_conflictos INT;
    DECLARE v_fecha_inicio_t DATE;
    DECLARE v_fecha_fin_t DATE;

    -- El torneo y los equipos son la identidad del partido
    IF NEW.id_torneo <> OLD.id_torneo
       OR NEW.id_equipo_local <> OLD.id_equipo_local
       OR NEW.id_equipo_visitante <> OLD.id_equipo_visitante THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Error: No se pueden cambiar el torneo ni los equipos de un partido; cancelalo y creá uno nuevo.';
    END IF;

    -- No se puede descancelar un partido
    IF OLD.estado = 'cancelado' AND NEW.estado <> 'cancelado' THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Error: Un partido cancelado no se puede reactivar; cargá uno nuevo.';
    END IF;

    -- Si tiene iformación cargada (planillas, significando que ya sucedió) no se puede actualizar la info del partido en si
    -- los goles y tarjetas si se van a poder actualizar, y las planillas se podrán eliminar
    SELECT COUNT(*) INTO v_planilla
    FROM planilla_partido
    WHERE id_partido = OLD.id_partido;

    IF v_planilla > 0 THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Error: El partido tiene planilla cargada y no se puede modificar.';
    END IF;

    -- Validación de fecha, cancha y día
    IF NEW.estado <> 'cancelado' THEN

        SELECT COUNT(*) INTO v_conflictos
        FROM partido
        WHERE id_torneo = NEW.id_torneo
          AND id_partido <> NEW.id_partido
          AND numero_fecha = NEW.numero_fecha
          AND estado <> 'cancelado'
          AND (id_equipo_local IN (NEW.id_equipo_local, NEW.id_equipo_visitante)
            OR id_equipo_visitante IN (NEW.id_equipo_local, NEW.id_equipo_visitante));

        IF v_conflictos > 0 THEN
            SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Error: Uno de los equipos ya tiene un partido asignado en esta misma fecha del torneo.';
        END IF;

        SELECT COUNT(*) INTO v_conflictos
        FROM partido
        WHERE id_torneo = NEW.id_torneo
          AND id_partido <> NEW.id_partido
          AND dia = NEW.dia
          AND estado <> 'cancelado'
          AND (id_equipo_local IN (NEW.id_equipo_local, NEW.id_equipo_visitante)
            OR id_equipo_visitante IN (NEW.id_equipo_local, NEW.id_equipo_visitante));

        IF v_conflictos > 0 THEN
            SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Error: Uno de los equipos ya tiene un partido asignado en ese mismo día.';
        END IF;

        SELECT COUNT(*) INTO v_conflictos
        FROM partido
        WHERE id_partido <> NEW.id_partido
          AND dia = NEW.dia
          AND id_turno = NEW.id_turno
          AND nombre_cancha = NEW.nombre_cancha
          AND id_complejo = NEW.id_complejo
          AND estado <> 'cancelado';

        IF v_conflictos > 0 THEN
            SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Error: La cancha ya está ocupada en ese día y turno.';
        END IF;

        SELECT fecha_inicio, fecha_fin INTO v_fecha_inicio_t, v_fecha_fin_t
        FROM torneo
        WHERE id_torneo = NEW.id_torneo;

        IF NEW.dia > v_fecha_fin_t OR NEW.dia < v_fecha_inicio_t THEN
            SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Error: La fecha del partido debe estar entre las fechas de inicio y fin del torneo.';
        END IF;
    END IF;
END //

-- update tarjeta
CREATE TRIGGER trg_tarjeta_upd
BEFORE UPDATE ON tarjeta
FOR EACH ROW
BEGIN
    IF NEW.id_partido <> OLD.id_partido
       OR NEW.ci_jugador <> OLD.ci_jugador
       OR NEW.color <> OLD.color THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Error: No se puede cambiar el partido, el jugador ni el color de una tarjeta; borrala y cargala de nuevo.';
    END IF;
END //

-- delete tarjeta (eliminar sanciones que se hayan creado automaticamente a partir de ella)
-- elimina solo las que se crearon automáticamente y si se está borrando la última amarilla, si por alguna razón se decidió modificarla habrá que eliminarla a mano
CREATE TRIGGER trg_delete_auto_sancion_tarjeta
AFTER delete ON tarjeta
FOR EACH ROW
BEGIN
    DECLARE v_id_torneo INT;
    DECLARE v_num_fecha INT;
    DECLARE v_cant_amarillas INT;

    -- Obtener el torneo y la fecha del partido donde se sacó la tarjeta
    SELECT id_torneo, numero_fecha INTO v_id_torneo, v_num_fecha
    FROM partido
    WHERE id_partido = OLD.id_partido;

    -- CASO A: Tarjeta Roja directa
    IF OLD.color = 'roja' THEN
        delete from sancion_jugador
        where ci_jugador = OLD.ci_jugador
            and id_torneo = v_id_torneo
            and motivo = 'roja'
            and numero_fecha_inicio = v_num_fecha + 1;

    -- CASO B: Tarjeta Amarilla (control de acumulación)
    ELSEIF OLD.color = 'amarilla' THEN
        -- Contar cuántas amarillas acumuladas tiene el jugador en este torneo
        SELECT COUNT(*) INTO v_cant_amarillas
        FROM tarjeta t
        JOIN partido p ON t.id_partido = p.id_partido
        WHERE t.ci_jugador = OLD.ci_jugador
          AND t.color = 'amarilla'
          AND p.id_torneo = v_id_torneo;

        -- Si es igual a 2 en módulo 3, significa que antes de que se eliminara era múltiplo de 3, por lo que se había generado una sancion automatica que hay que eliminar
        IF v_cant_amarillas % 3 = 2 THEN
            delete from sancion_jugador
        where ci_jugador = OLD.ci_jugador
            and id_torneo = v_id_torneo
            and motivo = 'acumulación de amarillas'
            and numero_fecha_inicio = v_num_fecha + 1;
        END IF;
    END IF;
END //

-- jugador
CREATE TRIGGER trg_jugador_upd
BEFORE UPDATE ON jugador
FOR EACH ROW
BEGIN
    DECLARE v_inscripciones INT;

    IF NEW.tipo <> OLD.tipo OR NEW.id_facultad <> OLD.id_facultad THEN
        SELECT COUNT(*) INTO v_inscripciones
        FROM equipo_jugador_torneo e
        JOIN torneo t ON t.id_torneo = e.id_torneo
        WHERE e.ci_jugador = OLD.ci
          AND t.estado <> 'finalizado';

        IF v_inscripciones > 0 THEN
            SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Error: No se puede cambiar el tipo ni la facultad de un jugador inscripto en un torneo no finalizado.';
        END IF;
    END IF;
END //

-- equipo
CREATE TRIGGER trg_equipo_upd
BEFORE UPDATE ON equipo
FOR EACH ROW
BEGIN
    DECLARE v_equipos_capitan INT;
    Declare v_nuevo_cap int;
    declare v_capitan_de_otro int;

    IF NEW.id_torneo <> OLD.id_torneo OR NEW.id_facultad <> OLD.id_facultad THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Error: No se puede cambiar el torneo ni la facultad de un equipo, borralo y cargalo de nuevo.';
    END IF;
    -- Validar que el capitán no pertenezca a otro equipo
    -- En el update ya podemos verificar que el nuevo capitán pertenezca al equipo
    -- ya está validado que el capitán pertenezca a la facultad con la fk
    SELECT count(*) INTO v_equipos_capitan FROM equipo_jugador_torneo
                                          WHERE id_torneo = NEW.id_torneo
                                            and ci_jugador = NEW.ci_capitan
                                            and id_equipo <> OLD.id_equipo;

    IF v_equipos_capitan > 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Error: El capitán ya pertenece a un equipo del torneo.';
    END IF;

    SELECT count(*) INTO v_nuevo_cap FROM equipo_jugador_torneo
                                          WHERE id_torneo = NEW.id_torneo
                                            and ci_jugador = NEW.ci_capitan
                                            and id_equipo = OLD.id_equipo;

    IF v_nuevo_cap <> 1 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Error: El nuevo capitán no pertenece al equipo.';
    END IF;

    -- como los equipos empiezan vacíos corremos este chequeo por las dudas, aunque en el backend se vaya a hacer directo
    SELECT COUNT(*) INTO v_capitan_de_otro
        FROM equipo
        WHERE id_torneo = OLD.id_torneo
          AND ci_capitan = NEW.ci_capitan
          AND id_equipo <> OLD.id_equipo;

        IF v_capitan_de_otro > 0 THEN
            SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Error: El jugador ya es capitán de otro equipo del torneo.';
        END IF;

END //

-- torneo
CREATE TRIGGER trg_torneo_upd
BEFORE UPDATE ON torneo
FOR EACH ROW
BEGIN
    DECLARE v_fuera INT;

    IF NEW.fecha_inicio <> OLD.fecha_inicio OR NEW.fecha_fin <> OLD.fecha_fin THEN
        SELECT COUNT(*) INTO v_fuera
        FROM partido
        WHERE id_torneo = OLD.id_torneo
          AND (dia < NEW.fecha_inicio OR dia > NEW.fecha_fin);

        IF v_fuera > 0 THEN
            SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Error: Hay partidos fuera del nuevo rango de fechas del torneo.';
        END IF;
    END IF;
END //

-- trigger para no borrar un partido jugado

CREATE TRIGGER trg_partido_del
BEFORE DELETE ON partido
FOR EACH ROW
BEGIN
    IF OLD.estado = 'jugado' THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Error: Un partido jugado no puede eliminarse.';
    END IF;
END //

-- Partido con estado jugado solo si su día y turno ya pasaron
CREATE TRIGGER trg_partido_jugado_ins
BEFORE INSERT ON partido
FOR EACH ROW
BEGIN
    DECLARE v_hora_fin TIME;
    IF NEW.estado = 'jugado' THEN
        SELECT hora_fin INTO v_hora_fin FROM turno WHERE id_turno = NEW.id_turno;
        IF TIMESTAMP(NEW.dia, v_hora_fin) > NOW() THEN
            SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Error: Un partido solo puede marcarse como jugado después de que terminó su turno.';
        END IF;
    END IF;
END //

CREATE TRIGGER trg_partido_jugado_upd
BEFORE UPDATE ON partido
FOR EACH ROW
BEGIN
    DECLARE v_hora_fin TIME;
    IF NEW.estado = 'jugado' THEN
        SELECT hora_fin INTO v_hora_fin FROM turno WHERE id_turno = NEW.id_turno;
        IF TIMESTAMP(NEW.dia, v_hora_fin) > NOW() THEN
            SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Error: Un partido solo puede marcarse como jugado después de que terminó su turno.';
        END IF;
    END IF;
END //

-- verificación de que capitán no tenga ningún equipo y nombre de equipo único
CREATE TRIGGER trg_valida_inscripcion_equipo
BEFORE INSERT ON equipo
FOR EACH ROW
BEGIN
    DECLARE v_equipos_capitan INT;
    declare v_capitan_de_otro int;

    -- Validar que el capitán no pertenezca a otro equipo
    -- No podemos ingresar directo al capitán ya que no tenemos la información de su numero,
        -- Pero en el backend se hara directo uno tras otro
    -- ya está validado que el capitán pertenezca a la facultad con la fk
    SELECT count(*) INTO v_equipos_capitan FROM equipo_jugador_torneo
                                          WHERE id_torneo = NEW.id_torneo
                                            and ci_jugador = NEW.ci_capitan;
    IF v_equipos_capitan > 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Error: El capitán ya pertenece a un equipo del torneo.';
    END IF;

    -- como los equipos empiezan vacíos corremos este chequeo por las dudas
    SELECT COUNT(*) INTO v_capitan_de_otro
        FROM equipo
        WHERE id_torneo = NEW.id_torneo
          AND ci_capitan = NEW.ci_capitan
          AND id_equipo <> NEW.id_equipo;

        IF v_capitan_de_otro > 0 THEN
            SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Error: El jugador ya es capitán de otro equipo del torneo.';
        END IF;

end //

CREATE TRIGGER trg_equipo_inscribe_capitan
AFTER INSERT ON equipo
FOR EACH ROW
BEGIN
    INSERT INTO equipo_jugador_torneo (id_equipo, ci_jugador, id_torneo, numero_camiseta)
    VALUES (NEW.id_equipo, NEW.ci_capitan, NEW.id_torneo, 1);
END //

CREATE TRIGGER trg_login_bd_ultimo_admin
BEFORE DELETE ON login
FOR EACH ROW
BEGIN
    DECLARE otros_admins INT;

    IF OLD.rol = 'administrador' THEN
        SELECT COUNT(*) INTO otros_admins
        FROM login
        WHERE rol = 'administrador'
          AND correo <> OLD.correo;

        IF otros_admins = 0 THEN
            SIGNAL SQLSTATE '45000'
                SET MESSAGE_TEXT = 'No se puede eliminar al ultimo administrador';
        END IF;
    END IF;
END //

CREATE TRIGGER trg_login_bu_ultimo_admin
BEFORE UPDATE ON login
FOR EACH ROW
BEGIN
    DECLARE otros_admins INT;

    IF OLD.rol = 'administrador' AND NEW.rol <> 'administrador' THEN
        SELECT COUNT(*) INTO otros_admins
        FROM login
        WHERE rol = 'administrador'
          AND correo <> OLD.correo;

        IF otros_admins = 0 THEN
            SIGNAL SQLSTATE '45000'
                SET MESSAGE_TEXT = 'No se puede degradar al ultimo administrador';
        END IF;
    END IF;
END //

DELIMITER ;


-- ==========================================
-- vistas:
-- ==========================================

create view goles_partido as select t.id_equipo, t.nombre, t.id_partido, t.numero_fecha, sum(t.goles_favor) as goles_a_favor from (
select e.id_equipo, e.nombre, pp.id_partido, p.numero_fecha, count(id_gol) as goles_favor from gol
join planilla_partido pp on gol.id_partido = pp.id_partido and gol.ci_jugador = pp.ci_jugador
join equipo e on pp.id_equipo = e.id_equipo
join partido p on p.id_partido = pp.id_partido
where autogol=FALSE
group by e.id_equipo, e.nombre, pp.id_partido
Union all
select p.id_equipo_visitante,e2.nombre, cl.id_partido, p.numero_fecha, goles_favor from partido p
join
(select e.id_equipo as id_equipo, e.nombre, pp.id_partido as id_partido, count(id_gol) as goles_favor from gol
join planilla_partido pp on gol.id_partido = pp.id_partido and gol.ci_jugador = pp.ci_jugador
join equipo e on pp.id_equipo = e.id_equipo
where autogol=true
group by e.id_equipo, e.nombre, pp.id_partido) as cl on cl.id_equipo = p.id_equipo_local and cl.id_partido = p.id_partido
join equipo e2 on p.id_equipo_visitante = e2.id_equipo
Union all
select p.id_equipo_local,e2.nombre, cl.id_partido, p.numero_fecha, goles_favor from partido p
join
(select e.id_equipo as id_equipo, e.nombre, pp.id_partido as id_partido, count(id_gol) as goles_favor from gol
join planilla_partido pp on gol.id_partido = pp.id_partido and gol.ci_jugador = pp.ci_jugador
join equipo e on pp.id_equipo = e.id_equipo
where autogol=true
group by e.id_equipo, e.nombre, pp.id_partido) as cl on cl.id_equipo = p.id_equipo_visitante and cl.id_partido = p.id_partido
join equipo e2 on p.id_equipo_local = e2.id_equipo
Union all                                                     -- NUEVO: 0 goles para el local de cada partido
select p.id_equipo_local, e3.nombre, p.id_partido, p.numero_fecha, 0 from partido p
join equipo e3 on p.id_equipo_local = e3.id_equipo
where estado = 'jugado'
Union all                                                     -- NUEVO: 0 goles para el visitante de cada partido
select p.id_equipo_visitante, e4.nombre, p.id_partido, p.numero_fecha, 0 from partido p
join equipo e4 on p.id_equipo_visitante = e4.id_equipo
where estado = 'jugado') as t
group by t.id_equipo, t.nombre, t.id_partido, t.numero_fecha;


create view goles_partido_en_contra as select t.id_equipo, e3.nombre, t.id_partido, sum(t.goles_en_contra) as goles_en_contra from (select e.id_equipo, e.nombre, pp.id_partido, count(id_gol) as goles_en_contra from gol
join planilla_partido pp on gol.id_partido = pp.id_partido and gol.ci_jugador = pp.ci_jugador
join equipo e on pp.id_equipo = e.id_equipo
where autogol=true
group by e.id_equipo, e.nombre, pp.id_partido
Union all
select p.id_equipo_visitante,e2.nombre, cl.id_partido, goles_en_contra from partido p
join
(select e.id_equipo as id_equipo, e.nombre, pp.id_partido as id_partido, count(id_gol) as goles_en_contra from gol
join planilla_partido pp on gol.id_partido = pp.id_partido and gol.ci_jugador = pp.ci_jugador
join equipo e on pp.id_equipo = e.id_equipo
where autogol=false
group by e.id_equipo, e.nombre, pp.id_partido) as cl on cl.id_equipo = p.id_equipo_local and cl.id_partido = p.id_partido
join equipo e2 on p.id_equipo_visitante = e2.id_equipo
Union all
select p.id_equipo_local,e2.nombre, cl.id_partido, goles_en_contra from partido p
join
(select e.id_equipo as id_equipo, e.nombre, pp.id_partido as id_partido, count(id_gol) as goles_en_contra from gol
join planilla_partido pp on gol.id_partido = pp.id_partido and gol.ci_jugador = pp.ci_jugador
join equipo e on pp.id_equipo = e.id_equipo
where autogol=false
group by e.id_equipo, e.nombre, pp.id_partido) as cl on cl.id_equipo = p.id_equipo_visitante and cl.id_partido = p.id_partido
join equipo e2 on p.id_equipo_visitante = e2.id_equipo
Union all                                                     -- NUEVO: 0 goles para el local de cada partido
select p.id_equipo_local, e5.nombre, p.id_partido, 0 from partido p
join equipo e5 on p.id_equipo_local = e5.id_equipo
where estado = 'jugado'
Union all                                                     -- NUEVO: 0 goles para el visitante de cada partido
select p.id_equipo_visitante, e4.nombre, p.id_partido, 0 from partido p
join equipo e4 on p.id_equipo_visitante = e4.id_equipo
where estado = 'jugado') as t
join equipo e3 on e3.id_equipo = t.id_equipo
group by t.id_equipo, e3.nombre, t.id_partido;

-- view de tabla de posiciones
create view tabla_posiciones as select tp.id_equipo, tp.nombre, sum(tp.partidos_jugados) as partidos_jugados,
                                       sum(tp.partidos_ganados) as partidos_ganados, sum(tp.partidos_empatados) as partidos_empatados,
                                       sum(tp.partidos_perdidos) as partidos_perdidos,
                                       sum(tp.goles_a_favor) as goles_a_favor, sum(tp.goles_en_contra) as goles_en_contra,
                                       sum(tp.diferencia_de_goles) as diferencia_de_goles,
                                       sum(tp.puntos) as puntos, tp.id_torneo
from (select e.id_equipo, e.nombre, count(*) as partidos_jugados,
       count(case when gf.goles_a_favor > gc.goles_en_contra then 1 end) as partidos_ganados,
       count(case when gf.goles_a_favor = gc.goles_en_contra then 1 end) as partidos_empatados,
       count(case when gf.goles_a_favor < gc.goles_en_contra then 1 end) as partidos_perdidos,
       sum(gf.goles_a_favor) as goles_a_favor, sum(gc.goles_en_contra) as goles_en_contra,
       sum(gf.goles_a_favor) - sum(gc.goles_en_contra) as diferencia_de_goles,
       count(case when gf.goles_a_favor > gc.goles_en_contra then 1 end)*3+count(case when gf.goles_a_favor = gc.goles_en_contra then 1 end) as puntos,
       p.id_torneo
from partido p
join equipo e on p.id_equipo_local = e.id_equipo
join goles_partido gf on gf.id_partido = p.id_partido and gf.id_equipo = e.id_equipo
join goles_partido_en_contra gc on gc.id_partido = p.id_partido and gc.id_equipo = e.id_equipo
where p.estado = 'jugado'
group by e.id_equipo, e.nombre, p.id_torneo
union all
select e.id_equipo, e.nombre, count(*) as partidos_jugados,
       count(case when gf.goles_a_favor > gc.goles_en_contra then 1 end) as partidos_ganados,
       count(case when gf.goles_a_favor = gc.goles_en_contra then 1 end) as partidos_empatados,
       count(case when gf.goles_a_favor < gc.goles_en_contra then 1 end) as partidos_perdidos,
       sum(gf.goles_a_favor) as goles_a_favor, sum(gc.goles_en_contra) as goles_en_contra,
       sum(gf.goles_a_favor) - sum(gc.goles_en_contra) as diferencia_de_goles,
       count(case when gf.goles_a_favor > gc.goles_en_contra then 1 end)*3+count(case when gf.goles_a_favor = gc.goles_en_contra then 1 end) as puntos,
       p.id_torneo
from partido p
join equipo e on p.id_equipo_visitante = e.id_equipo
join goles_partido gf on gf.id_partido = p.id_partido and gf.id_equipo = e.id_equipo
join goles_partido_en_contra gc on gc.id_partido = p.id_partido and gc.id_equipo = e.id_equipo
where p.estado = 'jugado'
group by e.id_equipo, e.nombre, p.id_torneo) as tp
group by tp.id_equipo, tp.nombre, tp.id_torneo
order by puntos desc, diferencia_de_goles desc, goles_a_favor desc;

-- view goleadores
create view tabla_goleadores as
select j.ci, j.nombre, j.apellido, e.nombre as equipo, count(g.id_gol) as goles, ejt.id_torneo from gol g
join jugador j on g.ci_jugador = j.ci
join equipo_jugador_torneo ejt on j.ci = ejt.ci_jugador
join equipo e on ejt.id_equipo = e.id_equipo
where autogol = false
group by j.ci, j.nombre, j.apellido, e.nombre, ejt.id_torneo
order by goles desc;

-- view tabla fair play
create view tabla_fair_play as
select h.id_equipo, h.equipo, sum(h.puntos_fair_play) as puntos_fair_play, h.id_torneo
from (select e.id_equipo, e.nombre as equipo, sum(ts.rojas*3+ts.amarillas) as puntos_fair_play, e.id_torneo
from equipo e
join (select e2.id_equipo,
             count(case when t.color = 'amarilla' then 1 end) as amarillas,
             count(case when t.color = 'roja' then 1 end) as rojas
      from equipo e2
      join equipo_jugador_torneo ejt2 on e2.id_equipo = ejt2.id_equipo
      join tarjeta t on ejt2.ci_jugador = t.ci_jugador
      group by e2.id_equipo) as ts on e.id_equipo = ts.id_equipo
group by e.id_equipo, e.nombre, e.id_torneo
      union
      select e.id_equipo, e.nombre, 0, e.id_torneo from equipo e) as h
group by h.id_equipo, h.equipo, h.id_torneo
order by puntos_fair_play;

-- view promedio de goles por fecha
create view promedio_goles_fecha as
select p.numero_fecha, round(avg(gp.goles_a_favor)*2,2) as promedio_goles, p.id_torneo from partido p
join goles_partido gp on p.id_partido = gp.id_partido
group by p.numero_fecha, p.id_torneo;


-- view promedio de goles por edicion (torneo)
create view promedio_goles_edicion as
select t.id_torneo, t.nombre as torneo, round(avg(pg.promedio_goles),2) as promedio_goles from torneo t
join promedio_goles_fecha pg on t.id_torneo = pg.id_torneo
group by t.id_torneo, t.nombre;

-- view canchas y turnos más utilizados (asumiendo que se realiza para ver disponibilidad lo hicimos general de todos los torneos)
create view canchas_turnos as select td.id_complejo, td.complejo, td.nombre_cancha, td.id_turno, td.hora_inicio, td.hora_fin, sum(td.cantidad_usos) as cantidad_usos
from(
select p.id_complejo, c.nombre as complejo, p.nombre_cancha, p.id_turno, t.hora_inicio, t.hora_fin, count(*) as cantidad_usos
from partido p
join complejo c on p.id_complejo = c.id_complejo
join turno t on p.id_turno = t.id_turno
where p.estado = 'jugado'
group by p.id_complejo, c.nombre, p.nombre_cancha, p.id_turno, t.hora_inicio, t.hora_fin
union
select c2.id_complejo, c2.nombre, ch.nombre_cancha, t2.id_turno, t2.hora_inicio, t2.hora_fin, 0
from cancha ch
join complejo c2 on c2.id_complejo = ch.id_complejo
cross join turno t2) as td
group by td.id_complejo, td.complejo, td.nombre_cancha, td.id_turno, td.hora_inicio, td.hora_fin
order by cantidad_usos desc;

-- view jugadores por facultad y grado (por torneo)
create view jugadores_facultad as
select f.id_facultad, f.nombre as facultad,
       count(*) as cantidad_de_jugadores,
       count(case when j.tipo = 'grado' then 1 end) as jugadores_grado,
       count(case when j.tipo = 'postgrado' then 1 end) as jugadores_postgrado,
       count(case when j.tipo = 'docente' then 1 end) as jugadores_docentes,
       count(case when j.tipo = 'funcionario' then 1 end) as jugadores_funcionarios,
       ejt.id_torneo
from facultad f
join equipo e on f.id_facultad = e.id_facultad
join equipo_jugador_torneo ejt on e.id_equipo = ejt.id_equipo
join jugador j on ejt.ci_jugador = j.ci
group by f.id_facultad, f.nombre, ejt.id_torneo;

-- view jugadores sin figurar, lo hicimos por torneo, dirá en qué torneo no figuró
create view sin_figurar as
select j.ci, j.nombre, j.apellido, ejt.id_torneo from jugador j
join equipo_jugador_torneo ejt on j.ci = ejt.ci_jugador
left join planilla_partido pp on j.ci = pp.ci_jugador and ejt.id_equipo = pp.id_equipo
where pp.id_partido is null;

-- sanciones por equipo y por motivo
create view sanciones_equipo as
select e.id_equipo, e.nombre as equipo,
       count(case when sj.motivo is not null then 1 end) as sanciones_totales,
       count(case when sj.motivo = 'roja' then 1 end) as rojas,
       count(case when sj.motivo = 'acumulación de amarillas' then 1 end) as acumulación_de_amarillas,
       count(case when sj.motivo = 'disciplinaria' then 1 end) as disciplinarias,
       e.id_torneo
from equipo e
join equipo_jugador_torneo ejt on e.id_equipo = ejt.id_equipo
left join sancion_jugador sj on ejt.ci_jugador = sj.ci_jugador
group by e.id_equipo, e.nombre, e.id_torneo
order by sanciones_totales desc;

-- view porcentaje jugados vs postergados o cancelados
create view porcentaje_jugados as
select t.id_torneo, round(ip.jugados/ip.totales*100,2) as pct_jugados, round(ip.canc_o_post/ip.totales*100,2) as pct_cancelados_o_postergados
from torneo t
join (select p.id_torneo,
             count(case when p.estado = 'jugado' or p.estado = 'postergado' or p.estado = 'cancelado' then 1 end) as totales,
             count(case when p.estado = 'jugado' then 1 end) as jugados,
             count(case when p.estado = 'postergado' or p.estado = 'cancelado' then 1 end) as canc_o_post
      from partido p
      group by p.id_torneo) as ip on t.id_torneo = ip.id_torneo;

-- view resultados
create view resultados as
select p.id_partido, p.numero_fecha,
       p.id_equipo_local, e.nombre as equipo_local,
       p.id_equipo_visitante, e2.nombre as equipo_visitante,
       gf.goles_a_favor as goles_e_local, gf2.goles_a_favor as goles_e_visitante,
       p.id_torneo
from partido p
join equipo e on p.id_equipo_local = e.id_equipo
join equipo e2 on p.id_equipo_visitante = e2.id_equipo
join goles_partido gf on p.id_partido = gf.id_partido and p.id_equipo_local = gf.id_equipo
join goles_partido gf2 on p.id_partido = gf2.id_partido and p.id_equipo_visitante = gf2.id_equipo;

-- view tarjetas_jugador
create view tarjetas_jugador as
select h.ci, h.nombre, h.apellido,
       sum(h.sanciones_totales) as sanciones_totales,
       sum(h.acumulacion_amarillas) as acumulacion_de_amarillas,
       sum(h.disciplinarias) as sanciones_disciplinarias,
       sum(h.amarillas) as tarjetas_amarillas,
       sum(h.rojas) as tarjetas_rojas
from (
select j.ci, j.nombre, j.apellido,
       count(*) as sanciones_totales,
       count(case when sj.motivo = 'acumulación de amarillas' then 1 end) as acumulacion_amarillas,
       count(case when sj.motivo = 'disciplinaria' then 1 end) as disciplinarias,
       0 as amarillas, 0 as rojas
from jugador j
join sancion_jugador sj on j.ci = sj.ci_jugador
group by j.ci, j.nombre, j.apellido, amarillas, rojas
union all
select j.ci, j.nombre, j.apellido,
       0 as sanciones_totales, 0 as acumulacion_amarillas, 0 as disciplinarias,
       count(case when t.color = 'amarilla' then 1 end),
       count(case when t.color = 'roja' then 1 end)
from jugador j
join tarjeta t on j.ci = t.ci_jugador
group by j.ci, j.nombre, j.apellido, sanciones_totales, acumulacion_amarillas, disciplinarias) as h
group by h.ci, h.nombre, h.apellido
order by sanciones_totales desc;

-- view tarjetas_jugador_torneo
create view tarjetas_jugador_torneo as
select h.ci, h.nombre, h.apellido,
       sum(h.sanciones_totales) as sanciones_totales,
       sum(h.acumulacion_amarillas) as acumulacion_de_amarillas,
       sum(h.disciplinarias) as sanciones_disciplinarias,
       sum(h.amarillas) as tarjetas_amarillas,
       sum(h.rojas) as tarjetas_rojas,
       h.id_torneo
from (
select j.ci, j.nombre, j.apellido,
       count(*) as sanciones_totales,
       count(case when sj.motivo = 'acumulación de amarillas' then 1 end) as acumulacion_amarillas,
       count(case when sj.motivo = 'disciplinaria' then 1 end) as disciplinarias,
       0 as amarillas, 0 as rojas, sj.id_torneo
from jugador j
join sancion_jugador sj on j.ci = sj.ci_jugador
group by j.ci, j.nombre, j.apellido, amarillas, rojas, sj.id_torneo
union all
select j.ci, j.nombre, j.apellido,
       0 as sanciones_totales, 0 as acumulacion_amarillas, 0 as disciplinarias,
       count(case when t.color = 'amarilla' then 1 end),
       count(case when t.color = 'roja' then 1 end), p.id_torneo
from jugador j
join tarjeta t on j.ci = t.ci_jugador
join partido p on t.id_partido = p.id_partido
group by j.ci, j.nombre, j.apellido, sanciones_totales, acumulacion_amarillas, disciplinarias, p.id_torneo) as h
group by h.ci, h.nombre, h.apellido, h.id_torneo
order by sanciones_totales desc;

-- view porcentaje_participación
create view porcentaje_participacion as
select j.ci, j.nombre, j.apellido, e.id_equipo, e.nombre as equipo,
       round(count(pp.id_partido)/ep.equipo_participaciones * 100,2) as porcentaje_participaciones,
       ejt.id_torneo
from jugador j
join equipo_jugador_torneo ejt on j.ci = ejt.ci_jugador
join equipo e on ejt.id_equipo = e.id_equipo
left join planilla_partido pp on j.ci = pp.ci_jugador and e.id_equipo = pp.id_equipo
join (select h.id_equipo, count(*) as equipo_participaciones
      from (select e2.id_equipo, p.id_partido
            from equipo e2
            join partido p on e2.id_equipo = p.id_equipo_local
            union
            select e3.id_equipo, p2.id_partido
            from equipo e3
            join partido p2 on e3.id_equipo = p2.id_equipo_visitante) as h
      group by h.id_equipo) as ep on e.id_equipo = ep.id_equipo
group by j.ci, j.nombre, j.apellido, e.id_equipo, e.nombre, ejt.id_torneo
order by porcentaje_participaciones desc;

-- ==========================================
-- privilegios
-- ==========================================
-- Usuario para administradores (acceso completo)

CREATE USER IF NOT EXISTS 'usr_admin'@'localhost' IDENTIFIED BY 'AdminPass123!';

GRANT insert, update, delete ON Obligatorio_Futbol5.* TO 'usr_admin'@'localhost';
-- hay que darle los select uno por uno ya que si le damos para OBligatorio_Futbol5.* no se lo podemos sacar de login
-- que por razones obvias no queremos que tenga acceso a login
-- tablas
GRANT SELECT ON Obligatorio_Futbol5.cancha TO 'usr_admin'@'localhost';
GRANT SELECT (correo, rol) ON Obligatorio_Futbol5.login TO 'usr_admin'@'localhost';
GRANT SELECT ON Obligatorio_Futbol5.complejo TO 'usr_admin'@'localhost';
GRANT SELECT ON Obligatorio_Futbol5.equipo TO 'usr_admin'@'localhost';
GRANT SELECT ON Obligatorio_Futbol5.equipo_jugador_torneo TO 'usr_admin'@'localhost';
GRANT SELECT ON Obligatorio_Futbol5.facultad TO 'usr_admin'@'localhost';
GRANT SELECT ON Obligatorio_Futbol5.gol TO 'usr_admin'@'localhost';
GRANT SELECT ON Obligatorio_Futbol5.jugador TO 'usr_admin'@'localhost';
GRANT SELECT ON Obligatorio_Futbol5.partido TO 'usr_admin'@'localhost';
GRANT SELECT ON Obligatorio_Futbol5.planilla_partido TO 'usr_admin'@'localhost';
GRANT SELECT ON Obligatorio_Futbol5.sancion_jugador TO 'usr_admin'@'localhost';
GRANT SELECT ON Obligatorio_Futbol5.tarjeta TO 'usr_admin'@'localhost';
GRANT SELECT ON Obligatorio_Futbol5.torneo TO 'usr_admin'@'localhost';
GRANT SELECT ON Obligatorio_Futbol5.turno TO 'usr_admin'@'localhost';
-- vistas
GRANT SELECT ON Obligatorio_Futbol5.canchas_turnos TO 'usr_admin'@'localhost';
GRANT SELECT ON Obligatorio_Futbol5.goles_partido TO 'usr_admin'@'localhost';
GRANT SELECT ON Obligatorio_Futbol5.goles_partido_en_contra TO 'usr_admin'@'localhost';
GRANT SELECT ON Obligatorio_Futbol5.jugadores_facultad TO 'usr_admin'@'localhost';
GRANT SELECT ON Obligatorio_Futbol5.porcentaje_jugados TO 'usr_admin'@'localhost';
GRANT SELECT ON Obligatorio_Futbol5.porcentaje_participacion TO 'usr_admin'@'localhost';
GRANT SELECT ON Obligatorio_Futbol5.promedio_goles_edicion TO 'usr_admin'@'localhost';
GRANT SELECT ON Obligatorio_Futbol5.promedio_goles_fecha TO 'usr_admin'@'localhost';
GRANT SELECT ON Obligatorio_Futbol5.resultados TO 'usr_admin'@'localhost';
GRANT SELECT ON Obligatorio_Futbol5.sanciones_equipo TO 'usr_admin'@'localhost';
GRANT SELECT ON Obligatorio_Futbol5.sin_figurar TO 'usr_admin'@'localhost';
GRANT SELECT ON Obligatorio_Futbol5.tabla_fair_play TO 'usr_admin'@'localhost';
GRANT SELECT ON Obligatorio_Futbol5.tabla_goleadores TO 'usr_admin'@'localhost';
GRANT SELECT ON Obligatorio_Futbol5.tabla_posiciones TO 'usr_admin'@'localhost';
GRANT SELECT ON Obligatorio_Futbol5.tarjetas_jugador TO 'usr_admin'@'localhost';
GRANT SELECT ON Obligatorio_Futbol5.tarjetas_jugador_torneo TO 'usr_admin'@'localhost';


-- Usuario para planilleros (permisos limitados para cargar planillas, goles y tarjetas)

CREATE USER IF NOT EXISTS 'usr_planillero'@'localhost' IDENTIFIED BY 'PlanilleroPass123!';

-- hay que darle los select uno por uno ya que si le damos para OBligatorio_Futbol5.* no se lo podemos sacar de login
-- que por razones obvias no queremos que tenga acceso a login
-- tablas
GRANT SELECT ON Obligatorio_Futbol5.cancha TO 'usr_planillero'@'localhost';
GRANT SELECT ON Obligatorio_Futbol5.complejo TO 'usr_planillero'@'localhost';
GRANT SELECT ON Obligatorio_Futbol5.equipo TO 'usr_planillero'@'localhost';
GRANT SELECT ON Obligatorio_Futbol5.equipo_jugador_torneo TO 'usr_planillero'@'localhost';
GRANT SELECT ON Obligatorio_Futbol5.facultad TO 'usr_planillero'@'localhost';
GRANT SELECT ON Obligatorio_Futbol5.gol TO 'usr_planillero'@'localhost';
GRANT SELECT ON Obligatorio_Futbol5.jugador TO 'usr_planillero'@'localhost';
GRANT SELECT ON Obligatorio_Futbol5.partido TO 'usr_planillero'@'localhost';
GRANT SELECT ON Obligatorio_Futbol5.planilla_partido TO 'usr_planillero'@'localhost';
GRANT SELECT ON Obligatorio_Futbol5.sancion_jugador TO 'usr_planillero'@'localhost';
GRANT SELECT ON Obligatorio_Futbol5.tarjeta TO 'usr_planillero'@'localhost';
GRANT SELECT ON Obligatorio_Futbol5.turno TO 'usr_planillero'@'localhost';
-- vistas
GRANT SELECT ON Obligatorio_Futbol5.canchas_turnos TO 'usr_planillero'@'localhost';
GRANT SELECT ON Obligatorio_Futbol5.goles_partido TO 'usr_planillero'@'localhost';
GRANT SELECT ON Obligatorio_Futbol5.goles_partido_en_contra TO 'usr_planillero'@'localhost';
GRANT SELECT ON Obligatorio_Futbol5.jugadores_facultad TO 'usr_planillero'@'localhost';
GRANT SELECT ON Obligatorio_Futbol5.porcentaje_jugados TO 'usr_planillero'@'localhost';
GRANT SELECT ON Obligatorio_Futbol5.porcentaje_participacion TO 'usr_planillero'@'localhost';
GRANT SELECT ON Obligatorio_Futbol5.promedio_goles_edicion TO 'usr_planillero'@'localhost';
GRANT SELECT ON Obligatorio_Futbol5.promedio_goles_fecha TO 'usr_planillero'@'localhost';
GRANT SELECT ON Obligatorio_Futbol5.resultados TO 'usr_planillero'@'localhost';
GRANT SELECT ON Obligatorio_Futbol5.sanciones_equipo TO 'usr_planillero'@'localhost';
GRANT SELECT ON Obligatorio_Futbol5.sin_figurar TO 'usr_planillero'@'localhost';
GRANT SELECT ON Obligatorio_Futbol5.tabla_fair_play TO 'usr_planillero'@'localhost';
GRANT SELECT ON Obligatorio_Futbol5.tabla_goleadores TO 'usr_planillero'@'localhost';
GRANT SELECT ON Obligatorio_Futbol5.tabla_posiciones TO 'usr_planillero'@'localhost';
GRANT SELECT ON Obligatorio_Futbol5.tarjetas_jugador TO 'usr_planillero'@'localhost';
GRANT SELECT ON Obligatorio_Futbol5.tarjetas_jugador_torneo TO 'usr_planillero'@'localhost';


GRANT INSERT, UPDATE ON Obligatorio_Futbol5.planilla_partido TO 'usr_planillero'@'localhost';

GRANT INSERT, UPDATE ON Obligatorio_Futbol5.gol TO 'usr_planillero'@'localhost';

GRANT INSERT, UPDATE ON Obligatorio_Futbol5.tarjeta TO 'usr_planillero'@'localhost';

GRANT UPDATE (estado) ON Obligatorio_Futbol5.partido TO 'usr_planillero'@'localhost';
-- Usuario exclusivo para el login: es el único que puede leer la columna contraseña
CREATE USER IF NOT EXISTS 'usr_login'@'localhost' IDENTIFIED BY 'Contraseña123!';
GRANT SELECT ON Obligatorio_Futbol5.login TO 'usr_login'@'localhost';
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
INSERT INTO equipo_jugador_torneo (id_equipo, ci_jugador, id_torneo, numero_camiseta) VALUES
(1, 10001002, 1, 5), (1, 10001003, 1, 8), (1, 10001004, 1, 9), (1, 10001005, 1, 4), (1, 10001006, 1, 7), (1, 10001007, 1, 99);

-- Algoritmos United (id_equipo = 2)
INSERT INTO equipo_jugador_torneo (id_equipo, ci_jugador, id_torneo, numero_camiseta) VALUES
(2, 10001009, 1, 2), (2, 10001010, 1, 3), (2, 10001011, 1, 6), (2, 10001012, 1, 7), (2, 10001013, 1, 9), (2, 10001014, 1, 11);

-- Redes F.C. (id_equipo = 3)
INSERT INTO equipo_jugador_torneo (id_equipo, ci_jugador, id_torneo, numero_camiseta) VALUES
(3, 10001016, 1, 4), (3, 10001017, 1, 5), (3, 10001018, 1, 8), (3, 10001019, 1, 10), (3, 10001020, 1, 14), (3, 10001021, 1, 9);

-- Economía Juniors (id_equipo = 4)
INSERT INTO equipo_jugador_torneo (id_equipo, ci_jugador, id_torneo, numero_camiseta) VALUES
(4, 20002002, 1, 2), (4, 20002003, 1, 3), (4, 20002004, 1, 4), (4, 20002005, 1, 7), (4, 20002006, 1, 9), (4, 20002007, 1, 12);

-- Finanzas City (id_equipo = 5)
INSERT INTO equipo_jugador_torneo (id_equipo, ci_jugador, id_torneo, numero_camiseta) VALUES
(5, 20002009, 1, 5), (5, 20002010, 1, 6), (5, 20002011, 1, 8), (5, 20002012, 1, 10), (5, 20002013, 1, 11), (5, 20002014, 1, 7);

-- Contadores F.C. (id_equipo = 6)
INSERT INTO equipo_jugador_torneo (id_equipo, ci_jugador, id_torneo, numero_camiseta) VALUES
(6, 20002016, 1, 2), (6, 20002017, 1, 3), (6, 20002018, 1, 4), (6, 20002019, 1, 10), (6, 20002020, 1, 7), (6, 20002021, 1, 11);


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

-- Partido 8 (Algoritmos 2 - 3 Economía)
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


-- ==========================================
-- triggers 48hs
-- ==========================================
DELIMITER //

-- Alta de gol: solo dentro de las 48 h posteriores al fin del turno
CREATE TRIGGER trg_gol_plazo_ins
BEFORE INSERT ON gol
FOR EACH ROW
BEGIN
    DECLARE v_fin DATETIME DEFAULT NULL;

    SELECT TIMESTAMP(p.dia, t.hora_fin) INTO v_fin
    FROM partido p
    JOIN turno t ON t.id_turno = p.id_turno
    WHERE p.id_partido = NEW.id_partido;

    IF NOW() > v_fin + INTERVAL 48 HOUR THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Error: Vencio el plazo de 48 horas para corregir el resultado de este partido.';
    END IF;
END //

-- Modificación de gol
CREATE TRIGGER trg_gol_plazo_upd
BEFORE UPDATE ON gol
FOR EACH ROW
BEGIN
    DECLARE v_fin DATETIME DEFAULT NULL;

    IF NEW.id_partido <> OLD.id_partido THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Error: No se puede mover un gol a otro partido; borralo y cargalo de nuevo.';
    END IF;

    SELECT TIMESTAMP(p.dia, t.hora_fin) INTO v_fin
    FROM partido p
    JOIN turno t ON t.id_turno = p.id_turno
    WHERE p.id_partido = OLD.id_partido;

    IF NOW() > v_fin + INTERVAL 48 HOUR THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Error: Vencio el plazo de 48 horas para corregir el resultado de este partido.';
    END IF;
END //

-- Baja de gol
CREATE TRIGGER trg_gol_plazo_del
BEFORE DELETE ON gol
FOR EACH ROW
BEGIN
    DECLARE v_fin DATETIME DEFAULT NULL;

    SELECT TIMESTAMP(p.dia, t.hora_fin) INTO v_fin
    FROM partido p
    JOIN turno t ON t.id_turno = p.id_turno
    WHERE p.id_partido = OLD.id_partido;

    IF NOW() > v_fin + INTERVAL 48 HOUR THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Error: Vencio el plazo de 48 horas para corregir el resultado de este partido.';
    END IF;
END //

-- ===== TARJETA =====

CREATE TRIGGER trg_tarjeta_plazo_ins
BEFORE INSERT ON tarjeta
FOR EACH ROW
BEGIN
    DECLARE v_fin DATETIME DEFAULT NULL;

    SELECT TIMESTAMP(p.dia, t.hora_fin) INTO v_fin
    FROM partido p
    JOIN turno t ON t.id_turno = p.id_turno
    WHERE p.id_partido = NEW.id_partido;

    IF NOW() > v_fin + INTERVAL 48 HOUR THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Error: Vencio el plazo de 48 horas para modificar las tarjetas de este partido.';
    END IF;
END //

CREATE TRIGGER trg_tarjeta_plazo_upd
BEFORE UPDATE ON tarjeta
FOR EACH ROW
BEGIN
    DECLARE v_fin DATETIME DEFAULT NULL;

    SELECT TIMESTAMP(p.dia, t.hora_fin) INTO v_fin
    FROM partido p
    JOIN turno t ON t.id_turno = p.id_turno
    WHERE p.id_partido = OLD.id_partido;

    IF NOW() > v_fin + INTERVAL 48 HOUR THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Error: Vencio el plazo de 48 horas para modificar las tarjetas de este partido.';
    END IF;
END //

CREATE TRIGGER trg_tarjeta_plazo_del
BEFORE DELETE ON tarjeta
FOR EACH ROW
BEGIN
    DECLARE v_fin DATETIME DEFAULT NULL;

    SELECT TIMESTAMP(p.dia, t.hora_fin) INTO v_fin
    FROM partido p
    JOIN turno t ON t.id_turno = p.id_turno
    WHERE p.id_partido = OLD.id_partido;

    IF NOW() > v_fin + INTERVAL 48 HOUR THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Error: Vencio el plazo de 48 horas para modificar las tarjetas de este partido.';
    END IF;
END //

-- ===== PLANILLA =====

CREATE TRIGGER trg_planilla_plazo_ins
BEFORE INSERT ON planilla_partido
FOR EACH ROW
BEGIN
    DECLARE v_fin DATETIME DEFAULT NULL;

    SELECT TIMESTAMP(p.dia, t.hora_fin) INTO v_fin
    FROM partido p
    JOIN turno t ON t.id_turno = p.id_turno
    WHERE p.id_partido = NEW.id_partido;

    IF NOW() > v_fin + INTERVAL 48 HOUR THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Error: Vencio el plazo de 48 horas para modificar la planilla de este partido.';
    END IF;
END //

CREATE TRIGGER trg_planilla_plazo_upd
BEFORE UPDATE ON planilla_partido
FOR EACH ROW
BEGIN
    DECLARE v_fin DATETIME DEFAULT NULL;

    IF NEW.id_partido <> OLD.id_partido THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Error: No se puede mover un jugador de planilla a otro partido; borralo y cargalo de nuevo.';
    END IF;

    SELECT TIMESTAMP(p.dia, t.hora_fin) INTO v_fin
    FROM partido p
    JOIN turno t ON t.id_turno = p.id_turno
    WHERE p.id_partido = OLD.id_partido;

    IF NOW() > v_fin + INTERVAL 48 HOUR THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Error: Vencio el plazo de 48 horas para modificar la planilla de este partido.';
    END IF;
END //

CREATE TRIGGER trg_planilla_plazo_del
BEFORE DELETE ON planilla_partido
FOR EACH ROW
BEGIN
    DECLARE v_fin DATETIME DEFAULT NULL;

    SELECT TIMESTAMP(p.dia, t.hora_fin) INTO v_fin
    FROM partido p
    JOIN turno t ON t.id_turno = p.id_turno
    WHERE p.id_partido = OLD.id_partido;

    IF NOW() > v_fin + INTERVAL 48 HOUR THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Error: Vencio el plazo de 48 horas para modificar la planilla de este partido.';
    END IF;
END //

DELIMITER ;
