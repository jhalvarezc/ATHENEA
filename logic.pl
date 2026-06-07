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