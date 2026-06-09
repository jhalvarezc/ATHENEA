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