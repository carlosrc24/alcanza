# CLAUDE.md — Alcanza

Contexto para Claude Code. Léelo entero antes de escribir código.

## Qué es

**Alcanza — el empleo que está a tu alcance.** Proyecto del equipo (Carlos Rodríguez Caparrós,
Ana Denis Rubio, Jiaxing Zhu, Pedro González Carnero; Máster en Ingeniería Informática, UC3M)
para el **MAD Open Data Challenge 2026**. La idea ya fue aceptada; la propuesta completa está en
`docs/` (tres PDF: aproximación técnica, fuentes de datos, propuesta de interfaz). Si algo de este
fichero contradice los PDF, manda este fichero: es la versión recortada para llegar a tiempo.

Alcanza recomienda a una persona que busca empleo en la Comunidad de Madrid **qué empleo puede
alcanzar de verdad en transporte público**, cuánta gente compite por él, qué trabajo parecido
puede hacer y qué formación y recursos (escuelas infantiles, servicios sociales) tiene cerca.
Tiene una segunda vista para orientadores/Consejería con el mapa de «desiertos de empleo
accesible».

## Qué hay que entregar (fecha límite: demo presencial el 20 de octubre de 2026)

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

## Alcance mínimo (MVP) — priorizar en este orden

Hay muy poco tiempo. Antes de añadir nada, que funcione esto de punta a punta:

1. **Unidad territorial: los 179 municipios.** (La desagregación de Madrid capital en zonas de
   transporte de la EDM es un extra, solo si sobra tiempo.)
2. **Tiempos de viaje en transporte público** entre municipios (matriz 179×179, hora punta
   laborable 7:00–9:00, mediana). Ver «Tiempos de viaje» abajo.
3. **Indicadores por municipio y sector**:
   - `puestos_alcanzables`: suma de puestos (afiliados por cuenta de cotización) de los
     municipios a ≤ T minutos.
   - `competidores`: parados del sector que pueden llegar a esos mismos destinos.
   - `puestos_por_competidor` (indicador principal, método 2SFCA / Shen 1998):
     para cada destino j: `R_j = puestos_j / Σ_k parados_k · [t_kj ≤ T]`;
     para cada origen i: `A_i = Σ_j R_j · [t_ij ≤ T]`.
   - `balance_empleo`: afiliados por cuenta de cotización / afiliados por residencia.
   - `tendencia`: variación interanual de afiliación (sube / estable / baja).
4. **Recomendador**: entrada (ocupación o sector, municipio, coche sí/no, hijo 0–3 sí/no,
   formación sí/no, tiempo máximo) → tres tarjetas: *trabajo directo*, *salto corto*,
   *salto con formación*, cada una con su explicación («por qué»).
   Puntuación = suma ponderada de indicadores normalizados; los pesos los mueve el usuario.
5. **App** con mapa + deslizadores + tarjetas + vista «planificación» (mapa coroplético).
6. Extras, por este orden: escuelas infantiles en ruta (conciliación), centros de FP cercanos,
   afinidad entre ocupaciones con ESCO, entrada en lenguaje natural con un LLM, simulador
   «¿y si…?».

Si un paso se atasca más de medio día, usar el plan B indicado y seguir.

## Datos — fuentes (títulos exactos del catálogo de la Comunidad)

Catálogo: https://datos.comunidad.madrid/catalogo — API CKAN estándar:
`https://datos.comunidad.madrid/api/3/action/package_search?q=<texto>` y
`.../package_show?id=<id>`. Los ids no los sabemos: **buscar por título** con `package_search`
y guardar el id encontrado en `src/config.py`. Guardar siempre lo descargado en `data/raw/`
con la fecha.

Empleo (núcleo):
- «Afiliados a la Seguridad Social en alta laboral a último día de mes según cuentas de
  cotización, por municipio. Comunidad de Madrid» → **puestos por municipio de trabajo**
  (mensual). Comprobar si trae rama/sector; si no, ver «Huecos».
- «Afiliados a la Seguridad Social en alta laboral a último día de mes, por municipio.
  Comunidad de Madrid» (mensual).
- «Afiliados a la Seguridad Social por lugar de residencia y rama de actividad. Municipios»
  (anual, 1 enero) → estructura sectorial por residencia.
- «Paro registrado en las oficinas de empleo por nacionalidad, sector de actividad y sexo
  CNAE 09. Municipios» (anual, 31 marzo) → **parados por sector y municipio de residencia**.
- «Movimiento Laboral Registrado. Paro registrado, por sexo y municipio. Comunidad de Madrid»
  y «… por edad y municipio …» (mensual).
- «Movimiento Laboral Registrado. Contratos de trabajo, por municipio. Comunidad de Madrid».
- «Población ocupada de 16 y más años por ocupación y sexo. Censo anual. Municipios».
- «Ganancia media anual por trabajador por ocupación y antigüedad» y «… por actividad, tipo de
  contrato y sexo» (salario, regional).
- «Accidentes de trabajo con baja en jornada de trabajo según grandes grupos de ocupación».

Transporte (Consorcio Regional de Transportes, etiqueta `CRTM` en el catálogo:
https://datos.comunidad.madrid/catalogo/dataset?tags=CRTM). Los recursos son enlaces HTML a
datos.crtm.es; el ZIP GTFS se descarga desde allí:
- «Oferta planificada de la Red de Metro», «… de la Red de Cercanías Madrid», «… de la Red de
  Autobuses Interurbanos», «… de la Red de Autobuses Urbanos de Madrid - EMT», «… de la Red
  de Autobuses Urbanos del resto de municipios» (GTFS) y GTFS de Metro Ligero.
- «Aparcamientos de disuasión ligados al transporte público…» (extra).

Educación y social:
- «Centros educativos de la comunidad de Madrid»
  (https://datos.comunidad.madrid/catalogo/dataset/centros_educativos) → escuelas infantiles
  y centros de FP (filtrar por tipo/etapa; geocodificar si no hay coordenadas).
- «Estadísticas de alumnos de centros educativos de la Comunidad de Madrid» → ciclos de FP.
- «Registro de centros de atención social» y «Registro de servicios de atención social».

Territorio:
- Límites municipales: Geoportal de la Comunidad de Madrid (o IGN/CNIG como respaldo).
  Clave común: **código INE de municipio de 5 dígitos** (28xxx).

Complementarias: ESCO (Comisión Europea, CSV descargable), correspondencia CNO-11 ↔ CIUO-08
(INE), OpenStreetMap (red peatonal para r5py; extracto `madrid` de Geofabrik).

## Huecos conocidos de los datos y cómo tratarlos

- **Afiliación y contratos redondeados a múltiplos de 5**: usar medias de 12 meses.
- **Paro por residencia, puestos por lugar de trabajo**: es lo que se necesita (competidores en
  origen, puestos en destino). No mezclar.
- **Si los puestos por municipio de trabajo no traen sector**: estimar `puestos_j,s` con IPF
  (ajuste proporcional iterativo): margen de filas = total de puestos por municipio de trabajo;
  margen de columnas = total regional por sector; semilla = estructura sectorial por residencia.
  Marcar la columna como `estimado = True`.
- **No hay paro por ocupación y municipio**: trabajar por sector (CNAE-09, secciones A–U). La
  ocupación del usuario se traduce a sector(es) con una tabla de correspondencia sencilla
  (`data/ref/ocupacion_sector.csv`, hecha a mano para las ~20 ocupaciones de la demo si no da
  tiempo a más).
- **No hay ofertas de empleo abiertas**: la demanda se aproxima con puestos existentes +
  contratación + tendencia. Decirlo en la app.

## Tiempos de viaje

Plan A: **r5py** (necesita Java 21) con todos los GTFS + el `.osm.pbf` de la Comunidad. Origen
y destino = centroide de cada municipio (mejor: centroide del núcleo urbano principal). Salidas
cada 10 min entre 7:00 y 9:00 de un martes dentro del calendario de los GTFS; tomar la mediana.

Plan B (si r5py no funciona en medio día): tiempo = acceso a pie a la parada más cercana +
trayecto por la red GTFS con un grafo de paradas (networkx; tiempos de viaje de `stop_times`,
transbordo penalizado 5 min) + egreso a pie. Plan C: distancia × velocidad media por tipo de
municipio, marcado como aproximado.

Validación (si da tiempo): comparar con viajes por motivo trabajo de la «Resultados de la EDM
2018».

## Stack

- Python 3.11+. `pandas`, `geopandas`, `pyarrow`, `requests`; `r5py` para tiempos.
- Pipeline reproducible: `python -m src.pipeline` descarga → limpia → calcula → escribe
  `data/processed/*.csv` (+ copia `.parquet` si conviene).
- App: **Streamlit** (`streamlit run app/app.py`) con mapa (`pydeck` o `folium`), deslizadores
  y tarjetas. Debe responder al instante: la app solo lee `data/processed/`, nunca recalcula
  la matriz de tiempos.
- LLM (extra): solo para convertir texto libre a los campos de entrada; el usuario los
  confirma. La IA nunca puntúa ni recomienda.

## Datasets elaborados que debe generar el pipeline (`data/processed/`)

| Fichero | Contenido |
|---|---|
| `municipios.csv` | código INE, nombre, centroide, población |
| `tiempos_tp.csv` | origen, destino, minutos (transporte público, hora punta) |
| `puestos_municipio_sector.csv` | municipio de trabajo, sector, puestos, estimado (bool) |
| `parados_municipio_sector.csv` | municipio de residencia, sector, parados |
| `indicadores_municipio_sector.csv` | municipio, sector, T, puestos_alcanzables, competidores, puestos_por_competidor, tendencia |
| `balance_empleo.csv` | municipio, puestos, residentes ocupados, balance |
| `recursos.csv` | tipo (escuela_infantil / fp / servicio_social), nombre, municipio, lat, lon |
| `afinidad_ocupaciones.csv` (extra) | ocupación A, ocupación B, similitud ESCO |

Cada fichero documentado en `data/processed/README.md` (columnas, unidades, fuente, fecha,
qué es estimado). Esto es el entregable 2: debe estar limpio.

## Reglas de trabajo

- Cuatro personas en paralelo: no tocar a la vez el mismo fichero. Ramas cortas, PR pequeños.
- No subir a git datos en bruto grandes (`data/raw/` en `.gitignore`); sí `data/processed/`.
- Cada cifra que vea el usuario debe poder rastrearse a su fuente y fecha.
- Escribir en español la interfaz y la documentación.
- Antes de dar algo por hecho: ejecutar el pipeline y abrir la app.
