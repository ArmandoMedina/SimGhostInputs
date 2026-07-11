# 05 — Instrumentación: cómo sabes que funciona ANTES del choque

Hilo conductor: **contar fallos es demasiado tarde.** Un gate humano que se pudre no produce un
accidente de inmediato; produce primero una firma de comportamiento medible (aprobaciones más
rápidas, tasa de detección que cae, drift). Esto es cómo se instrumenta esa firma.

> TIP verificado contra fuente primaria (ver `citas-verificadas.md` frente 3, ítem 8).
> LOSA/CCPS: mecanismos estándar bien documentados; cifras no re-verificadas aquí.

## Las seis piezas

| Pieza | Qué da para el gate humano-IA |
|---|---|
| **Leading vs lagging** (CCPS, process safety) | No midas solo fallos. Instrumenta Tier 3 (demandas a la barrera: cuántas veces el gate interceptó algo) y Tier 4 (disciplina del proceso). "Cero incidentes" es el patrón que *precede* al fallo, no evidencia de salud. |
| **LOSA** (aviación, Helmreich/UT, OACI Doc 9803) | Audita una muestra de revisiones humano-IA NORMALES (no solo las que explotaron): codifica amenazas capturadas vs no capturadas. Gate sano = el humano intercepta; gate podrido = amenazas pasando en operación rutinaria. |
| **SPC / CUSUM / EWMA** (Shewhart/Deming) | Control charts sobre las métricas del gate. CUSUM/EWMA detectan drift <1σ — la caída lenta del tiempo de revisión o la subida lenta de la tasa de aprobación aparecen semanas antes del fallo. |
| **Safety-II** (Hollnagel) | Mide los ajustes/rescates que el humano SÍ hace (work-as-done). Si los ajustes desaparecen — si work-as-done colapsa a "aprobar lo que dice la IA" — perdiste la fuente de resiliencia aunque el tablero siga verde. |
| **Just Culture / near-miss** (Reason, Dekker) | Reporte de desacuerdos humano-IA sin castigo. Bandera contraintuitiva: una CAÍDA en reportes de desacuerdo es alarma, no éxito — el sistema se quedó ciego. |
| **TIP — Threat Image Projection** (seguridad aeroportuaria) | El mecanismo estrella, ver abajo. |

## TIP: el canario inyectado

Los aeropuertos inyectan imágenes ficticias de amenazas a baja prevalencia en el flujo REAL de
rayos-X, indistinguibles del tráfico. Doble propósito: (a) mantener despierto al screener (sube
la prevalencia artificial de un evento rarísimo), (b) **medir su tasa de detección en vivo** y
disparar reentrenamiento cuando cae bajo el mínimo [VERIFICADO: "screeners who miss a minimum
TIP hit rate must undergo remedial training", Sensors 2022 — Riz à Porta, Sterchi & Schwaninger;
hit rates reportados ~80-90%, el estudio midió 88%]. Lección de diseño del propio TIP: si la
trampa se nota falsa, deja de medir (34% de imágenes TIP calificadas como poco realistas).
[La cifra de prevalencia exacta (~2%) circula en la literatura TIP pero no quedó verificada
contra fuente primaria — no citarla como dato duro.]

**Traslado a humano-IA:** inyectar periódicamente casos-trampa sintéticos (outputs de IA con un
defecto conocido plantado, indistinguibles de casos reales) en el flujo de revisión humana, a
baja prevalencia. Medir el hit rate del revisor de forma continua; feedback inmediato;
reentrenamiento al caer. Es el canario que mide *y* previene la putrefacción del gate.

**Estado del arte (honesto):** no existe, a 2026, ningún sistema en producción ni framework
consolidado de "TIP para revisores de IA" — solo la analogía madura en aeropuertos, un piloto de
radiología que inyectó errores en borradores simulados (arXiv 2412.12042, exploratorio), y
heurísticas de auditoría de tasas de override. **Construirlo es frontera** (ver `06-fronteras.md`).

## El tablero mínimo del gate humano-IA

En control chart (EWMA/CUSUM), con drift como alarma:

1. **Tiempo de revisión** por ítem — drift descendente = skim-and-approve.
2. **Tasa de aprobación** — acercándose a 100% = bandera roja (un revisor que aprueba todo no
   filtra; el humano-in-the-loop se volvió ficción para distribuir responsabilidad).
3. **Hit rate sobre casos-trampa inyectados** (TIP) — la medida directa de vigilancia.
4. **Tasa de reporte de desacuerdo humano-IA** — su caída es alarma, no éxito.
5. **Demandas a la barrera** (Tier 3): cuántas veces el gate atrapó algo real.

## La bandera roja maestra

> **Una métrica perfecta (cero fallos, 100% aprobación, cero reportes, cero rechazos) es
> sospechosa por defecto.** Un gate sano genera fricción visible; un gate podrido genera silencio.
