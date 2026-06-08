% logic.pl - ATHENEA Core Lógico (Arquitectura Desacoplada)

% ==========================================================
% 1. PERMISOS DE INYECCIÓN EN TIEMPO REAL (DATOS DINÁMICOS)
% ==========================================================
:- dynamic estado_envio/2.      % estado_envio(Guia, Estado) 
:- dynamic limite_entrega/2.    % limite_entrega(Guia, fecha(D, M, A)) <-- Formato: Día, Mes, Año
:- dynamic costo_flete/2.       % costo_flete(Guia, Costo)
:- dynamic destino_envio/2.     % destino_envio(Guia, CiudadDestino)
:- dynamic origen_envio/2.      % origen_envio(Guia, CiudadOrigen)
:- dynamic fecha_despacho/2.    % fecha_despacho(Guia, fecha(D, M, A)) <-- Formato: Día, Mes, Año

% ==========================================================
% 2. MÓDULO DE TIEMPO (COMPARACIÓN DÍA, MES, AÑO)
% ==========================================================
% Regla para determinar si Fecha1 es posterior a Fecha2
fecha_mayor(fecha(_, _, A1), fecha(_, _, A2)) :- A1 > A2.
fecha_mayor(fecha(_, M1, A), fecha(_, M2, A)) :- M1 > M2.
fecha_mayor(fecha(D1, M, A), fecha(D2, M, A)) :- D1 > D2.

% ==========================================================
% 3. REGLAS CORE (Tiempo y Costo Base)
% ==========================================================

% Regla A: Alerta de Retraso General
alerta_retraso(Guia, FechaActual) :-
    estado_envio(Guia, Estado),
    Estado \= entregado,
    limite_entrega(Guia, FechaLimite),
    fecha_mayor(FechaActual, FechaLimite).

% Regla B: Alerta Crítica Nivel 1
alerta_critica(Guia) :-
    estado_envio(Guia, en_novedad),
    costo_flete(Guia, Costo),
    Costo > 30000.

% Regla C: Alerta de Ruta Crítica
alerta_ruta_critica(Guia) :-
    estado_envio(Guia, en_novedad),
    costo_flete(Guia, Costo),
    Costo > 3000.

% Regla D: Alerta de Desviación de Tarifas Estándar
alerta_tarifa_excesiva(Guia) :-
    estado_envio(Guia, en_transito),
    costo_flete(Guia, Costo),
    Costo > 2500.

% ==========================================================
% 4. 🛣️ DETECCIÓN ESPECÍFICA DE CUELLOS DE BOTELLA
% ==========================================================

% Regla E: Retraso por Despacho (Atrapado en Origen)
retraso_por_despacho(Guia, FechaActual) :-
    estado_envio(Guia, Estado),
    (Estado = en_bodega ; Estado = preparacion),
    fecha_despacho(Guia, FechaProgDespacho),
    fecha_mayor(FechaActual, FechaProgDespacho).

% Regla F: Retraso por Transporte (Problema en Carretera)
retraso_por_transporte(Guia, FechaActual) :-
    estado_envio(Guia, Estado),
    (Estado = en_transito ; Estado = en_novedad),
    limite_entrega(Guia, FechaLimite),
    fecha_mayor(FechaActual, FechaLimite).

% Regla G: Alerta de Riesgo de Pérdida Total
alerta_riesgo_perdida_total(Guia) :-
    estado_envio(Guia, en_novedad),
    costo_flete(Guia, Costo),
    Costo > 10000.

% Regla H: Flete Sospechoso / Posible Fraude Interno
flete_sospechoso(Guia) :-
    estado_envio(Guia, en_novedad),
    costo_flete(Guia, Costo),
    Costo > 4500.

% ==========================================================
% 5. 🎯 REGLA MAESTRA DE OPTIMIZACIÓN Y TRAZABILIDAD
% ==========================================================
analisis_ruta_completa(Guia, Origen, Destino, Diagnostico, FechaActual) :-
    origen_envio(Guia, Origen),
    destino_envio(Guia, Destino),
    (
        retraso_por_despacho(Guia, FechaActual) -> Diagnostico = retraso_despacho ;
        retraso_por_transporte(Guia, FechaActual) -> Diagnostico = retraso_transporte ;
        alerta_critica(Guia) -> Diagnostico = critico_financiero ;
        estado_envio(Guia, entregado) -> Diagnostico = entregado_ok ;
        Diagnostico = en_transito_optimo
    ).

% =================================================================
% FUNCIONES AVANZADAS DE AUDITORÍA LOGÍSTICA - ATHENEA
% =================================================================

% 1. Alerta de Fletes Excesivos (Tarifas sospechosas)
% Alerta si el costo del flete supera un umbral maximo aceptable para la ruta.
flete_excesivo(Guia, Costo) :-
    costo_flete(Guia, Costo),
    Costo > 150000. % Umbral base personalizable corporativo

% 2. Evaluación de Eficiencia Operativa (Días Límite Restantes)
% Calcula cuántos días calendario otorgó la operación para entregar el despacho.
dias_entrega_permitidos(Guia, Dias) :-
    fecha_despacho(Guia, fecha(DiaD, MesD, AnoD)),
    limite_entrega(Guia, fecha(DiaL, MesL, AnoL)),
    AnoD == AnoL, MesD == MesL, % Simplificado para el mismo mes
    Dias is DiaL - DiaD.

% 3. Identificación de Rutas Críticas por Estado
% Clasifica envíos prioritarios estancados en revisión documental o procesos iniciales
ruta_critica_prioritaria(Guia, Origen, Destino) :-
    estado_envio(Guia, en_revision_doc),
    origen_envio(Guia, Origen),
    destino_envio(Guia, Destino).
