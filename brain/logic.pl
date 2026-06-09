% brain/logic.pl - ATHENEA Core Lógico (V3 - Scoring y Recomendaciones)
:- dynamic estado_envio/2.
:- dynamic limite_entrega/2.
:- dynamic costo_flete/2.
:- dynamic destino_envio/2.
:- dynamic origen_envio/2.
:- dynamic fecha_despacho/2.

% ---------------------------------------------------------
% 1. UTILIDADES BÁSICAS
% ---------------------------------------------------------
fecha_mayor(fecha(_, _, A1), fecha(_, _, A2)) :- A1 > A2.
fecha_mayor(fecha(_, M1, A), fecha(_, M2, A)) :- M1 > M2.
fecha_mayor(fecha(D1, M, A), fecha(D2, M, A)) :- D1 > D2.

% Reglas auxiliares para separar listas compuestas
extraer_datos([], [], [], []).
extraer_datos([[A, P, R]|Resto], [A|Alertas], [P|Penalizaciones], [R|Recomendaciones]) :-
    extraer_datos(Resto, Alertas, Penalizaciones, Recomendaciones).

sumar_puntos([], 0).
sumar_puntos([P|Resto], Total) :- sumar_puntos(Resto, SubTotal), Total is P + SubTotal.

% ---------------------------------------------------------
% 2. REGLAS PURAS DE AUDITORÍA
% ---------------------------------------------------------
alerta_critica(Guia) :- estado_envio(Guia, en_novedad), costo_flete(Guia, Costo), Costo > 30000.
alerta_tarifa_excesiva(Guia) :- estado_envio(Guia, en_transito), costo_flete(Guia, Costo), Costo > 2500.
retraso_por_despacho(Guia, FechaActual) :- estado_envio(Guia, Estado), (Estado = en_bodega ; Estado = preparacion), fecha_despacho(Guia, FechaProgDespacho), fecha_mayor(FechaActual, FechaProgDespacho).
retraso_por_transporte(Guia, FechaActual) :- estado_envio(Guia, Estado), (Estado = en_transito ; Estado = en_novedad), limite_entrega(Guia, FechaLimite), fecha_mayor(FechaActual, FechaLimite).
alerta_riesgo_perdida(Guia) :- estado_envio(Guia, en_novedad), costo_flete(Guia, Costo), Costo > 10000.
flete_sospechoso(Guia) :- estado_envio(Guia, en_novedad), costo_flete(Guia, Costo), Costo > 4500.

% ---------------------------------------------------------
% 3. MOTOR DE SCORING Y RECOMENDACIONES (La Inteligencia)
% Estructura: detectar_infraccion(Guia, Fecha, Mensaje, PuntosRestados, AccionSugerida)
% ---------------------------------------------------------
detectar_infraccion(Guia, FechaActual, '❌ Retraso Crítico en Despacho', 15, 'Llamar a bodega origen urgente.') :- retraso_por_despacho(Guia, FechaActual).
detectar_infraccion(Guia, FechaActual, '🚛 Vehículo Retrasado en Ruta', 20, 'Contactar al conductor/transportista.') :- retraso_por_transporte(Guia, FechaActual).
detectar_infraccion(Guia, _, '📉 Tarifa Excesiva en Tránsito', 25, 'Renegociar tarifa con el proveedor.') :- alerta_tarifa_excesiva(Guia).
detectar_infraccion(Guia, _, '💰 Riesgo Financiero Alto (>30k)', 40, 'Bloquear pago de factura preventivamente.') :- alerta_critica(Guia).
detectar_infraccion(Guia, _, '🚨 Novedad con Riesgo de Pérdida', 50, 'Preparar activación de póliza de seguro.') :- alerta_riesgo_perdida(Guia).
detectar_infraccion(Guia, _, '⚠️ Posible Fraude / Flete Sospechoso', 60, 'Auditoría interna inmediata requerida.') :- flete_sospechoso(Guia).

% Clasificación del Índice de Salud
clasificar_salud(Salud, excelente) :- Salud >= 90.
clasificar_salud(Salud, atencion_requerida) :- Salud >= 60, Salud < 90.
clasificar_salud(Salud, critico) :- Salud < 60.

% ---------------------------------------------------------
% 4. DIAGNÓSTICO MAESTRO (Devuelve Calificación del 0 al 100)
% ---------------------------------------------------------
auditoria_integral(Guia, FechaActual, ListaAlertas, SaludFinal, Categoria, ListaRecomendaciones) :-
    ( estado_envio(Guia, entregado) -> 
        ListaAlertas = ['✅ Entregado Correctamente'],
        SaludFinal = 100, Categoria = excelente, 
        ListaRecomendaciones = ['Ninguna. Archivar registro.']
    ; 
        % Buscar todas las infracciones con sus detalles
        findall([Alerta, Penalizacion, Recomendacion], detectar_infraccion(Guia, FechaActual, Alerta, Penalizacion, Recomendacion), InfraccionesEncontradas),
        
        ( InfraccionesEncontradas = [] -> 
            ListaAlertas = ['✅ Operación Normal'], SaludFinal = 100, Categoria = excelente, ListaRecomendaciones = ['Continuar monitoreo estándar.']
        ; 
            % Separar la información
            extraer_datos(InfraccionesEncontradas, AlertasBrutas, Penalizaciones, RecomendacionesBrutas),
            
            % Limpiar duplicados
            sort(AlertasBrutas, ListaAlertas),
            sort(RecomendacionesBrutas, ListaRecomendaciones),
            
            % Calcular Score Final (100 puntos menos las penalizaciones)
            sumar_puntos(Penalizaciones, TotalPenalizacion),
            SaludCalculada is 100 - TotalPenalizacion,
            
            % Evitar puntajes negativos
            (SaludCalculada < 0 -> SaludFinal = 0 ; SaludFinal = SaludCalculada),
            
            % Categorizar
            clasificar_salud(SaludFinal, Categoria)
        )
    ).

% ---------------------------------------------------------
% 5. MATRIZ DE CONTROL DE ACCESO (ROLES Y PERMISOS)
% ---------------------------------------------------------
% Definición de los roles del sistema ATHENEA
rol(admin).
rol(basico).

% Permisos del Administrador (Nivel Dios: Ve finanzas y auditorías completas)
puede_ver(admin, guia_id).
puede_ver(admin, origen).
puede_ver(admin, destino).
puede_ver(admin, costo_flete).
puede_ver(admin, estado_auditoria).
puede_ver(admin, nivel_salud).
puede_ver(admin, recomendaciones_internas).

% Permisos del Usuario Básico (Nivel Operativo: Solo ve el tránsito, NUNCA el dinero)
puede_ver(basico, guia_id).
puede_ver(basico, origen).
puede_ver(basico, destino).
puede_ver(basico, estado_auditoria).
puede_ver(basico, nivel_salud).
% Nota: Ocultamos intencionalmente 'costo_flete' y 'recomendaciones_internas'

% Regla para filtrar una lista de columnas solicitadas contra los permisos del rol
columnas_permitidas(_, [], []).
columnas_permitidas(Rol, [Columna|Resto], [Columna|Permitidas]) :-
    puede_ver(Rol, Columna),
    columnas_permitidas(Rol, Resto, Permitidas).
columnas_permitidas(Rol, [_|Resto], Permitidas) :-
    columnas_permitidas(Rol, Resto, Permitidas).

% =================================================================
% 6. COMPATIBILIDAD CON REPORTES Y KPIS DE CONTROL
% =================================================================
flete_alto(Guia, Costo) :-
    costo_flete(Guia, Costo),
    Costo > 2500.

entrega_urgente(Guia) :-
    estado_envio(Guia, Estado),
    (Estado = en_novedad ; Estado = en_revision_doc).    

% ---------------------------------------------------------
% 7. PUENTE DE COMPATIBILIDAD (Para el Dashboard del Admin)
% ---------------------------------------------------------
analisis_ruta_completa(Guia, Origen, Destino, Diagnostico, FechaActual) :-
    origen_envio(Guia, Origen),
    destino_envio(Guia, Destino),
    (
        retraso_por_despacho(Guia, FechaActual) -> Diagnostico = retraso_critico ;
        retraso_por_transporte(Guia, FechaActual) -> Diagnostico = retraso_ruta ;
        alerta_critica(Guia) -> Diagnostico = critico_financiero ;
        estado_envio(Guia, entregado) -> Diagnostico = entregado_ok ;
        Diagnostico = en_transito_optimo
    ).

% ---------------------------------------------------------
% 8. MOTOR DE PREDICCIONES Y PROYECCIONES
% ---------------------------------------------------------
:- dynamic datos_fiscales/3.        % datos_fiscales(MesActual, CostoAcumulado, TotalEnvios)
:- dynamic estadisticas_hub/3.      % estadisticas_hub(Ciudad, EnviosConNovedad, TotalEnvios)
:- dynamic estadisticas_sla/2.      % estadisticas_sla(UrgentesNoEntregados, TotalUrgentes)

% Proyección del costo total para el final del año (12 meses)
prediccion_costo_anual(CostoProyectado, CategoriaAlerta, Recomendacion) :-
    datos_fiscales(MesActual, CostoAcumulado, _),
    MesActual > 0,
    MesActual =< 12,
    CostoProyectado is (CostoAcumulado / MesActual) * 12,
    ( CostoProyectado > 1500000 ->
        CategoriaAlerta = 'Peligro (Sobrepresupuesto)',
        Recomendacion = 'Alerta: El costo anual proyectado supera el presupuesto establecido. Se recomienda renegociar contratos de fletes y limitar envios urgentes.'
    ; CostoProyectado > 1000000 ->
        CategoriaAlerta = 'Precaucion (Moderado)',
        Recomendacion = 'Advertencia: El costo proyectado se acerca al limite presupuestario. Monitorear los sobrecostos de fletes reportados por el motor de inferencia.'
    ;
        CategoriaAlerta = 'Seguro (Bajo Riesgo)',
        Recomendacion = 'Normal: El ritmo de gasto anual actual se mantiene dentro de los margenes optimos presupuestados.'
    ).

% Predicción de embotellamientos en hubs
prediccion_embotellamiento(Ciudad, TasaNovedades, NivelRiesgo, Recomendacion) :-
    estadisticas_hub(Ciudad, ConNovedad, Total),
    Total > 0,
    TasaNovedades is (ConNovedad / Total) * 100,
    ( TasaNovedades > 30 ->
        NivelRiesgo = 'Alto Riesgo',
        Recomendacion = 'Prediccion de Bloqueo: Alta tasa de novedades. Desviar despachos no criticos a otros hubs y realizar auditoria fisica de bodega.'
    ; TasaNovedades > 15 ->
        NivelRiesgo = 'Riesgo Moderado',
        Recomendacion = 'Alerta Operativa: Tasa de novedades en aumento. Revisar capacidad de transportadoras asignadas en la zona.'
    ;
        NivelRiesgo = 'Operacion Estable',
        Recomendacion = 'Flujo normal: Hub operativo estable y dentro de la capacidad nominal de red.'
    ).

% Predicción de fallos de SLA
prediccion_sla(TasaFallo, Categoria, Recomendacion) :-
    estadisticas_sla(NoEntregados, Total),
    Total > 0,
    TasaFallo is (NoEntregados / Total) * 100,
    ( TasaFallo > 40 ->
        Categoria = 'Incumplimiento Critico',
        Recomendacion = 'Alerta SLA: Alta tasa de fallos de entrega urgentes. Se recomienda cambiar de proveedor de transporte en rutas criticas.'
    ; TasaFallo > 20 ->
        Categoria = 'Riesgo Moderado',
        Recomendacion = 'Atencion SLA: Retrasos en despacho detectados. Agilizar procesos internos de cargue.'
    ;
        Categoria = 'SLA Cumplido',
        Recomendacion = 'Excelente: Las entregas criticas se encuentran dentro del rango operativo aceptable.'
    ).

% Obtiene el hub con la tasa más alta de novedades (cuello de botella principal)
mayor_cuello_botella(Ciudad, TasaMax, Recomendacion) :-
    estadisticas_hub(Ciudad, Novedades, Total),
    Total > 0,
    TasaMax is (Novedades / Total) * 100,
    TasaMax > 0,
    % Asegurar que no hay otra ciudad con tasa estrictamente mayor
    not((
        estadisticas_hub(OtraCiudad, OtraNov, OtraTot),
        OtraTot > 0,
        OtraCiudad \= Ciudad,
        OtraTasa is (OtraNov / OtraTot) * 100,
        OtraTasa > TasaMax
    )),
    Recomendacion = 'PUNTO CRITICO DE CUELLO DE BOTELLA: Este Hub presenta la mayor concentracion de novedades. Desviar despachos no urgentes de inmediato.'.

% Determina si una guía es urgente (prioridad alta, retrasos de despacho/transporte o costo muy alto)
guia_urgente(Guia, Origen, Destino, Estado, Costo, Diagnostico) :-
    estado_envio(Guia, Estado),
    origen_envio(Guia, Origen),
    destino_envio(Guia, Destino),
    costo_flete(Guia, Costo),
    (
        alerta_critica(Guia) -> Diagnostico = 'Sobrecosto Financiero Extremo' ;
        flete_sospechoso(Guia) -> Diagnostico = 'Posible Fraude Interno' ;
        retraso_por_despacho(Guia, fecha(7, 6, 2026)) -> Diagnostico = 'Retraso Critico en Bodega' ;
        retraso_por_transporte(Guia, fecha(7, 6, 2026)) -> Diagnostico = 'Retraso de Ruta' ;
        entrega_urgente(Guia) -> Diagnostico = 'Margen de SLA Critico'
    ).    