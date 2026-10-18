# CLAUDE.md — Alcanza

Contexto para Claude Code. Léelo entero antes de escribir código.

## Qué es

**Alcanza — el empleo que está a tu alcance.** Proyecto del equipo (Carlos Rodríguez Caparrós,
Ana Denis Rubio, Jiaxing Zhu, Pedro González Carnero; Máster en Ingeniería Informática, UC3M)
para el **MAD Open Data Challenge 2026**. La idea ya fue aceptada; la propuesta completa está en
`docs/` (tres PDF: aproximación técnica, fuentes de datos, propuesta de interfaz). Si algo de este
fichero contradice los PDF, manda este fichero.

Alcanza recomienda a una persona que busca empleo en la Comunidad de Madrid **qué empleo puede
alcanzar de verdad en transporte público**, cuánta gente compite por él, qué trabajo parecido
puede hacer y qué formación y recursos (escuelas infantiles, servicios sociales) tiene cerca.
Tiene una segunda vista para orientadores/Consejería con el mapa de «desiertos de empleo
accesible», un simulador «¿y si…?» y un ranking de mejoras de transporte.

Repositorio público: https://github.com/carlosrc24/alcanza (la app **no** se publica en internet:
decisión del equipo; se ejecuta en local).

## Qué hay que entregar (demo presencial el 20 de octubre de 2026)

1. **Prototipo funcional** que el jurado pueda usar en directo (demo de 10 minutos).
2. **Datasets elaborados** que use el prototipo: CSV en `data/processed/`, cada uno con su
   diccionario de datos en `data/processed/README.md` (columnas, unidades, fuentes, fecha).

Cómo puntúa el jurado (100 puntos):
- 25 · corrección del planteamiento teórico en el tratamiento de los datos abiertos
- 25 · grado de resolución del reto
- 25 · sencillez para que el destinatario obtenga y entienda los resultados
- 25 · interactividad/flexibilidad para que el usuario lo adapte a su caso

Requisito de las bases: los **datos de la Comunidad de Madrid deben ser protagonistas**. No
sustituirlos por otras fuentes.

## Estado (18-10-2026): todo el MVP y casi todos los extras están hechos

A dos días de la demo: **no añadir funcionalidades nuevas**; solo arreglos que salgan al ensayar.

| Pieza | Estado | Dónde |
|---|---|---|
| 179 municipios, puestos y parados por sector | hecho | `src/datos.py` |
| Tiempos TP reales (r5py, 7–9 h, mediana) + coche aproximado | hecho | `src/gtfs.py`, `src/tiempos.py` |
| 2SFCA por sector × T (15–90) × modo (tp/coche), tendencia | hecho | `src/indicadores.py` |
| Recomendador: 3 tarjetas con puntuación desglosada y «por qué» | hecho | `src/recomendador.py` |
| Escuelas infantiles, FP, formación para el empleo, servicios sociales | hecho | `src/recursos.py` |
| Texto libre → campos: IA (Gemini) con respaldo por reglas | hecho | `src/ia.py`, `src/texto.py` |
| Simulador «¿y si…?» y ranking de mejoras de transporte | hecho | `src/simulador.py` |
| Validación externa (EDM 2018, paro, robustez) | hecho | `src/validacion.py` |
| App: 3 vistas, diseño propio (tema en `.streamlit/config.toml`) | hecho | `app/app.py` |
| Pruebas (16): datos, conservación 2SFCA, recomendador, texto, IA, app, validación | hecho | `tests/` |
| Afinidad entre ocupaciones con ESCO | **no** (tabla hecha a mano de 26 ocupaciones) | `data/ref/ocupaciones.csv` |
| Madrid capital desagregada por distritos | **no** (declarado como límite) | — |

## Cómo se ejecuta

```bash
pip install -r requirements.txt
streamlit run app/app.py                    # la app solo lee data/processed/ (ya en el repo)
python -m pytest -q                         # ~5 min (más si hay otra app abierta)
python -m src.pipeline                      # regenera todo reutilizando los tiempos
python -m src.pipeline --tiempos            # recalcula tiempos con r5py (Java 21+, ~30 min, 16 GB)
python -m src.validacion                    # solo la validación
```

r5py va por tandas reanudables en `data/interim/tiempos_r5py_<firma>/`. La firma depende de los
GTFS en bruto, del **código de `src/gtfs.py`**, del OSM y de los puntos: tocar `gtfs.py` invalida
la caché y obliga a recalcular (~25 min). La vez que se calculó entero hubo que cerrar Chrome y
Streamlit por memoria.

## Datos usados (ids reales en `src/config.py`)

Catálogo de la Comunidad (CKAN): https://datos.comunidad.madrid/catalogo. Todo se descarga a
`data/raw/<clave>__<fecha>.*` con un `.meta.json` (título, url, fecha) → `data/processed/fuentes.json`.

- Puestos por **lugar de trabajo y rama**: «Trabajadores afiliados en alta laboral a la Seguridad
  Social por ubicación del centro de trabajo y rama de actividad. Municipios» → trae sector, así
  que **no hizo falta IPF**.
- Afiliados por residencia y rama (estructura para repartir «Servicios» del paro y balance).
- Paro registrado por nacionalidad, sector y sexo (CNAE 09), municipios, 31 de marzo.
- Padrón por sexo (población); ganancia media por ocupación (salario, regional); centros
  educativos; registro de centros de atención social; límites municipales (SHP «Covid 19 - TIA por
  Municipios y Distritos de Madrid», distritos disueltos en 28079).
- GTFS del Consorcio (Metro, Metro Ligero, EMT, interurbanos, urbanos del resto) desde
  crtm.maps.arcgis.com; **GTFS de Renfe Cercanías** (el de Cercanías del Consorcio viene vacío).
- OpenStreetMap (Geofabrik «madrid») para la red peatonal de r5py.
- **«Resultados de la EDM 2018»** (catálogo de la Comunidad; Excel EDM2018VIAJES del Consorcio)
  para validar tiempos. Zonas ZT1259: los 3 primeros dígitos son el código INE del municipio.
- Clave común: código INE de 5 dígitos (`"28" + 3 primeros dígitos` del código de 4 del catálogo;
  se descarta 9999).

No usados (por tiempo): contratos de trabajo, paro por sexo/edad mensual, ocupados por ocupación
del censo, ESCO.

## Huecos de los datos encontrados y cómo se han tratado

- **Paro solo con 4 sectores** y el último año (2026) **solo con el total**: estructura sectorial
  del último año con desglose (2025) escalada al total 2026; «Servicios» repartido entre DIS/EMP/OTR
  con la estructura de afiliados residentes (`estimado = True`). Parados sin empleo anterior,
  pro rata.
- Afiliación por rama redondeada a 5 desde 2021: se reescala al total municipal.
- **GTFS**: los feeds no comparten calendario (Metro caducó en mayo de 2026); `src/gtfs.py` congela
  cada uno en un martes laborable propio y los reasigna al 27-10-2026.
- **GTFS de interurbanos publicado como «Datos parciales»**: 13 líneas sin viajes (522, 635,
  720–728 de Colmenar Viejo, N702, N908) y 48 con horarios de relleno (todo a las 02:00); en
  urbanos del resto, 23 más. En 26 municipios (≥ 65 % de paradas de bus sin horario,
  `huecos_gtfs.csv`) cada par usa min(r5py, regresión cuantílica t_tp = a + b·t_coche por tipo de
  par) → `metodo_tp = estimado_hueco_gtfs`. Como solo añade destinos a partir de ~75–90 min, su
  acceso es una cota inferior: **no se clasifican como desiertos** (borde morado en el mapa) y la
  app avisa.
- **Madrid capital es un único destino** en su núcleo: al superar T el tiempo hasta él se suman
  ~2,9 M de puestos de golpe (desde Parla, 62 min: el salto está entre T = 60 y 75). Declarado.
- No hay ofertas de empleo abiertas: la demanda se aproxima con puestos existentes y tendencia.

## Método (resumen)

- Origen/destino = núcleo del municipio (mediana de sus paradas); dentro del municipio, 10 min.
- 2SFCA (Shen 1998) **por modo**: en `tp` se compite con parados que llegan en TP; en `coche`, con
  los que llegan en coche. Propiedad de conservación (Σ parados·A = puestos alcanzados) verificada
  en `tests/`. Por eso el simulador **reparte, no suma**: el ranking de mejoras ordena por parados
  que salen de un desierto, no por acceso total.
- Desierto = tercio con menos acceso relativo y tercio con más paro por habitante (≥ 50 parados),
  excluidos los municipios con hueco de GTFS.

## Validación (`data/processed/validacion.json`, pestaña «Validación»)

- Tiempos frente a 2.377 viajes casa→trabajo en TP de la EDM 2018 (80 pares): diferencia mediana
  **−0,5 min**, error medio 10,7 min, **72 %** de pares a ±15 min (79 % sin Madrid capital).
- Acceso frente a tasa de paro (Spearman, 103 municipios): negativo con el índice y con los puestos
  alcanzables (este no usa el paro, así que no es circular).
- Robustez: índice con umbral (T = 60) frente a 2SFCA gaussiano d₀ = 60 → Spearman 0,85.

## IA (Google Gemini) — solo para entender el texto libre

- `src/ia.py`: llamada REST a la API de Gemini con **salida JSON restringida por esquema**
  (ocupación y municipio solo pueden ser valores de nuestras listas), validada en Python. Si la
  ocupación no está, elige la más parecida y la app lo dice. Lo que la IA deja vacío se completa
  con las reglas de `src/texto.py`.
- Modelos en cascada (`MODELOS`): `gemini-3.5-flash-lite` (~1 s) → `gemini-3.1-flash-lite` →
  `gemini-flash-lite-latest` → `gemini-3.5-flash`; si fallan todos (cuota, red), reglas fijas. Los
  2.5 ya no están disponibles para claves nuevas.
- Clave: `GOOGLE_AI` en `.env` (**nunca se sube**; plantilla en `.env.example`), o variable de
  entorno, o `.streamlit/secrets.toml`. `ALCANZA_SIN_IA=1` la desactiva (lo usan las pruebas de la
  app). La app avisa de que, con IA, el texto se envía a Google.
- **La IA nunca puntúa ni recomienda**: todas las cifras salen de los datos abiertos.

## Demo (10 min)

Caso conductor (propuesta, `docs/`): **Lucía, auxiliar administrativa en Parla**, sin coche, hijo
de 2 años, dispuesta a formarse — es el texto de ejemplo que trae la app. Puntos clave:
deslizador de tiempo de **60 a 75 min** (entra Madrid), tarjetas y «por qué», escuelas infantiles
en el mapa; en planificación, mapa de desiertos y ranking de mejoras (con T = 60 y 10 min de
ahorro, mejorar Parla saca de un desierto a sus 7.041 parados); cerrar con la validación (EDM 2018).
Llevar plan B: el mapa base necesita internet, y la IA también (sin ella funcionan las reglas).
Probado a 1280×720 (proyector) sin desbordes.

## Datasets elaborados (`data/processed/`, documentados en su `README.md`)

`municipios.csv` (+ `.geojson`), `puestos_municipio_sector.csv`, `parados_municipio_sector.csv`,
`balance_empleo.csv`, `sectores.csv`, `salario_ocupacion.csv`, `tiempos_tp.csv`,
`huecos_gtfs.csv`, `estimacion_hueco_gtfs.csv`, `indicadores_municipio_sector.csv`,
`oportunidad_destino.csv`, `recursos.csv`, `validacion_tiempos_edm.csv`, `validacion.json`,
`fuentes.json`. Tabla hecha a mano: `data/ref/ocupaciones.csv` (26 ocupaciones, saltos).

## Reglas de trabajo

- No subir a git datos en bruto (`data/raw/`, `data/interim/`) ni el `.env`; sí `data/processed/`.
- Cada cifra que vea el usuario debe poder rastrearse a su fuente y fecha.
- Escribir en español la interfaz y la documentación.
- Antes de dar algo por hecho: ejecutar el pipeline, `python -m pytest -q` y abrir la app.
- Si se toca un CSV o una columna, actualizar `data/processed/README.md` en el mismo cambio.
- La app debe responder al instante: solo lee `data/processed/`; nunca recalcula la matriz de
  tiempos (el simulador recalcula el 2SFCA en memoria, que es inmediato).
