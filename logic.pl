% logic.pl - ATHENEA Core Lógico (Arquitectura Desacoplada)

% 1. PERMISOS DE INYECCIÓN EN TIEMPO REAL
% Permite a Python inyectar y borrar estos datos en tiempo de ejecución
:- dynamic estado_envio/2.
:- dynamic limite_entrega/2.
:- dynamic costo_flete/2.

% ==========================================
% 2. REGLAS DE NEGOCIO (El Cerebro)
% ==========================================

% Regla A: Alerta de Retraso (Ineficiencia de Tiempo)
alerta_retraso(Guia, FechaActual) :-
    estado_envio(Guia, Estado),
    Estado \= entregado,
    limite_entrega(Guia, FechaLimite),
    FechaActual > FechaLimite.

% Regla B: Alerta Crítica (Para probar escalabilidad futura)
% "Si un envío está en novedad y su flete es mayor a 30,000, es un riesgo grave"
alerta_critica(Guia) :-
    estado_envio(Guia, en_novedad),
    costo_flete(Guia, Costo),
    Costo > 30000.
% =================================================================
% NUEVAS REGLAS DE NEGOCIO AVANZADAS
% =================================================================

% Regla C: Alerta de Ruta Crítica (Alta prioridad con Latencia Operativa)
% Un envío es considerado "Ruta Crítica" si está 'en_novedad' y su costo de flete 
% supera los $3,000, lo que exige atención prioritaria e inmediata de la gerencia.
alerta_ruta_critica(Guia) :-
    estado_envio(Guia, en_novedad),
    costo_flete(Guia, Costo),
    Costo > 3000.

% Regla D: Alerta de Desviación de Tarifas Estándar
% El negocio establece que ningún envío en tránsito ordinario debería superar 
% un costo de flete de $2,500. Si lo supera, se dispara una alerta de auditoría por tarifa excesiva.
alerta_tarifa_excesiva(Guia) :-
    estado_envio(Guia, en_transito),
    costo_flete(Guia, Costo),
    Costo > 2500.   