# Datasets elaborados de Alcanza

Generados con `python -m src.pipeline` a partir de datos abiertos de la Comunidad de Madrid
(catálogo datos.comunidad.madrid), del Consorcio Regional de Transportes de Madrid (GTFS),
de Renfe Cercanías (GTFS) y de OpenStreetMap. Fecha de descarga y última modificación en el
catálogo de cada fuente: `fuentes.json`.

Convenciones comunes:

- **`ine`**: código INE del municipio, 5 dígitos (`28xxx`). Los ficheros del catálogo usan
  3 dígitos + dígito de control (`0796` → `28079`); se convierte así en todos los ficheros.
  Se descarta el código `9999` («Sin municipio asignado»).
- **`sector`**: clasificación común del proyecto (columna `sector` de `sectores.csv`):

  | Código | Sector | Ramas de afiliación | Sector del paro registrado |
  |---|---|---|---|
  | AGR | Agricultura y ganadería | Agricultura y ganadería | Agricultura |
  | IND | Industria y energía | Minería, industria y energía | Industria |
  | CON | Construcción | Construcción | Construcción |
  | DIS | Comercio, transporte y hostelería | Servicios de distribución y hostelería | Servicios (reparto, estimado) |
  | EMP | Servicios a empresas, financieros e inmobiliarios | Servicios a empresas y financieros + Inmobiliarias | Servicios (reparto, estimado) |
  | OTR | Otros servicios | Otros servicios | Servicios (reparto, estimado) |
  | TOT | Todos los sectores | suma | suma |

- **`estimado`**: `True` cuando la cifra no se observa directamente en la fuente.
- CSV con separador `,`, decimal `.`, codificación UTF-8.

---

## `municipios.csv` — 179 filas

| Columna | Unidad | Descripción |
|---|---|---|
| ine | — | código INE |
| nombre | — | nombre oficial (forma del padrón: «Rozas de Madrid (Las)») |
| lat, lon | grados WGS84 | **núcleo** del municipio: mediana de las coordenadas de sus paradas de transporte público (si no tiene, punto representativo del polígono). Es el origen/destino de los tiempos de viaje |
| x, y | m, ETRS89 UTM 30N (EPSG:25830) | mismo punto |
| area_km2 | km² | superficie del polígono |
| poblacion | personas | población empadronada (Total) |
| anio_poblacion | año | año del padrón (1 de enero) |
| n_paradas | — | paradas de los GTFS dentro del municipio |

Fuentes: «Población empadronada por sexo. Municipios»; límites «Municipios y Distritos de
Madrid (2020)» (recurso SHP del conjunto «Covid 19 - TIA por Municipios y Distritos de
Madrid»; los 21 distritos de Madrid se disuelven en 28079); paradas de los GTFS del Consorcio
y de Renfe Cercanías.
`municipios.geojson`: mismos polígonos simplificados (WGS84) para el mapa.

## `puestos_municipio_sector.csv` — 179 × 6 filas

| Columna | Unidad | Descripción |
|---|---|---|
| ine | — | municipio **donde está el centro de trabajo** |
| anio | año | año de referencia |
| sector | — | sector |
| puestos | afiliados en alta laboral | puestos de trabajo localizados en el municipio |
| fecha_referencia | fecha | 31 de diciembre |
| estimado | bool | `False`: dato observado |

Fuente: «Trabajadores afiliados en alta laboral a la Seguridad Social por ubicación del centro
de trabajo y rama de actividad. Municipios». Este conjunto trae el sector por lugar de trabajo,
así que **no hace falta la estimación IPF** prevista. Tratamiento: desde 2021 la fuente redondea
cada rama a múltiplos de 5 (el total no); las ramas se reescalan para que sumen el total
municipal y la rama «No consta» se reparte pro rata. Hasta 2020 los «-» (dato < 5) reciben el
residuo total − conocido a partes iguales.

## `parados_municipio_sector.csv` — 179 × 6 filas

| Columna | Unidad | Descripción |
|---|---|---|
| ine | — | municipio **de residencia** del parado |
| sector | — | sector |
| parados_con_sector | personas | parados cuyo último empleo fue de ese sector |
| parados_sin_empleo_anterior | personas | parte asignada de los parados «Sin sector de actividad» (sin empleo anterior), repartidos pro rata entre sectores |
| parados | personas | suma de las dos anteriores: **competidores** del modelo |
| estimado | bool | `True` (ver abajo) |
| anio | año | año del total de paro (31 de marzo) |
| anio_estructura_sectorial | año | año del desglose sectorial usado |
| fecha_referencia | fecha | 31 de marzo |

Fuentes: «Paro registrado en las oficinas de empleo por nacionalidad, sector de actividad y
sexo CNAE 09. Municipios» (Españoles + Extranjeros, Sexo = Total). Estimaciones: (1) el último
año publicado (2026) solo trae el total municipal; se aplica la estructura sectorial del último
año con desglose (2025) a ese total; (2) el paro solo distingue cuatro sectores: «Servicios» se
reparte entre DIS, EMP y OTR con la estructura de «Afiliados a la Seguridad Social por lugar de
residencia y rama de actividad. Municipios» del propio municipio.

## `balance_empleo.csv` — 179 filas

| Columna | Unidad | Descripción |
|---|---|---|
| ine | — | municipio |
| puestos | afiliados | puestos localizados en el municipio (31-12, `anio_puestos`) |
| residentes_ocupados | afiliados | afiliados que residen en el municipio (1-1, `anio_residencia`) |
| balance | ratio | puestos / residentes ocupados |
| tipo | — | «polo de empleo» (≥ 1,1), «ciudad dormitorio» (≤ 0,6) o «equilibrado» |

## `tiempos_tp.csv` — 179 × 179 filas

| Columna | Unidad | Descripción |
|---|---|---|
| origen, destino | — | municipios (núcleos de `municipios.csv`) |
| min_tp | minutos | transporte público + a pie, **mediana** de las salidas minuto a minuto entre 7:00 y 9:00 de un martes laborable; 181 = no alcanzable en 180 min |
| min_coche | minutos | coche, aproximado: distancia en línea recta × 1,3 a 30 km/h (< 10 km) o 55 km/h, + 5 min |
| accesible_tp | bool | hay conexión en ≤ 180 min |
| metodo_tp | — | por par: `r5py_gtfs_osm_p50_7a9h` (plan A), `estimado_hueco_gtfs` (estimado por hueco de la fuente, ver abajo) o `plan_c_aproximado` (respaldo) |

**Comprobad la columna `metodo_tp`.** Con el plan A los tiempos salen de horarios reales. Con el
plan C (respaldo, sin r5py) se aproximan como 15 min de acceso y espera más la distancia
(× 1,3) a 25 km/h si los dos municipios tienen paradas, o a 15 km/h si no las tienen.

**Hueco de la fuente (`estimado_hueco_gtfs`).** El Consorcio publica el GTFS de autobuses
interurbanos como «Datos parciales» (versión del 16-10-2026). En él, 13 líneas no traen viajes
(522, 635, 720–728, N702, N908: entre ellas toda la concesión de Colmenar Viejo) y 48 traen
horarios «de relleno» (todas las paradas a las 02:00:00); en el GTFS de urbanos del resto de
municipios hay otras 23 líneas así. Un municipio se marca afectado (`huecos_gtfs.csv`) si al menos
el 65 % de sus paradas de autobús no tienen ningún viaje con horario real. En los pares con un
extremo afectado, `min_tp` es el menor entre el valor de r5py y una estimación: regresión cuantílica
(mediana) `t_tp = a + b · t_coche` ajustada por tipo de par sobre los pares no afectados
(coeficientes y error en `estimacion_hueco_gtfs.csv`). La estimación es conservadora en trayectos
cortos entre municipios vecinos.

**Madrid capital es un único destino**, situado en su núcleo (mediana de sus paradas). Cuando el
umbral T supera el tiempo hasta ese punto se suman de golpe unos 2,9 millones de puestos (p. ej.,
desde Parla: 62 min, el salto se ve entre T = 60 y T = 75). Es una simplificación declarada de la
unidad municipal; la desagregación por distritos queda como mejora.

## `huecos_gtfs.csv` — 179 filas

| Columna | Unidad | Descripción |
|---|---|---|
| ine | — | municipio |
| paradas_sin_horario | proporción | paradas de autobús (interurbanos y urbanos) del municipio sin ningún viaje con horario real en la fuente |
| ferrocarril | bool | tiene alguna parada de Cercanías, Metro o Metro Ligero |
| hueco_gtfs | bool | `paradas_sin_horario` ≥ 0,65: sus tiempos se completan con la estimación |

## `estimacion_hueco_gtfs.csv`

Coeficientes de la estimación por tipo de par (`madrid`: un extremo es Madrid capital;
`ferrocarril_ambos`, `ferrocarril_uno`, `autobus`): `a_min`, `b`, número de pares del ajuste y
error absoluto mediano en minutos.

Plan A — viajes dentro del propio municipio: 10 min por convención (simplificación declarada, afecta
sobre todo a Madrid capital). Cálculo con r5py (motor R5 de Conveyal) sobre OpenStreetMap
(extracto Geofabrik «madrid») y los GTFS del Consorcio: Metro, Metro Ligero, EMT, autobuses
interurbanos y urbanos del resto de municipios. El GTFS de Cercanías publicado por el Consorcio
no contiene horarios, por lo que se usa el GTFS de Renfe Cercanías (rutas del núcleo de Madrid).
Los feeds no comparten periodo de validez (el de Metro termina en mayo de 2026): cada uno se
fija en un martes laborable propio dentro de su calendario y todos se reasignan a una fecha común
(`src/gtfs.py`).

## `indicadores_municipio_sector.csv` — 179 × 7 sectores × 6 umbrales × 2 modos

| Columna | Unidad | Descripción |
|---|---|---|
| ine | — | municipio de **origen** (residencia de la persona) |
| sector | — | sector (incluye TOT) |
| T | minutos | tiempo máximo de viaje: 15, 30, 45, 60, 75, 90 |
| modo | — | `tp` (transporte público) o `coche` (modo de la persona) |
| puestos_alcanzables | puestos | Σ_j puestos_j · [t_ij ≤ T] |
| competidores | personas | competidores efectivos = puestos_alcanzables / puestos_por_competidor |
| puestos_por_competidor | puestos/parado | **indicador principal** (2SFCA, Shen 1998): A_i = Σ_j R_j · [t_ij ≤ T], con R_j = puestos_j / Σ_k parados_k · [t_kj ≤ T] |
| indice_relativo | ratio | A_i / (puestos del sector / parados del sector en la región); 1 = media regional. Su media ponderada por parados es 1 en cada sector, T y modo (propiedad de conservación del 2SFCA, verificada en `tests/`) |
| var_interanual | proporción | variación de puestos_alcanzables entre los dos últimos años |
| tendencia | — | «sube» (> +2 %), «baja» (< −2 %), «estable» o «sin datos» (sin puestos alcanzables el año anterior) |
| municipios_alcanzables | — | nº de municipios a ≤ T |

Cada modo tiene su propio 2SFCA. En `tp` se compite con los parados que llegan al destino en
transporte público, y en `coche` con los que llegan en coche. Así el índice compara a cada
persona con quienes se desplazan como ella, y la ventaja del coche se ve en
`puestos_alcanzables` y `municipios_alcanzables`.

## `oportunidad_destino.csv` — 179 × 7 sectores × 6 umbrales × 2 modos

| Columna | Unidad | Descripción |
|---|---|---|
| ine | — | municipio de **destino** |
| sector, T, modo | — | sector, umbral y modo (`tp` o `coche`) |
| puestos | puestos | puestos del sector en el destino |
| competidores_que_llegan | personas | Σ_k parados_k · [t_kj ≤ T] con los tiempos del modo |
| puestos_por_competidor_destino | ratio | R_j (primer paso del 2SFCA) |

## `recursos.csv`

| Columna | Descripción |
|---|---|
| tipo | `escuela_infantil` (EEI, EIPR, Casa de niños, CPR infantil), `fp` (CIFP, centros privados de FP), `fp_ies` (IES: pueden ofrecer FP), `formacion_empleo` (centros de formación para el empleo, UFIL), `adultos` (CEPA), `servicio_social` |
| subtipo, nombre, titularidad, direccion, telefono, web | datos del registro |
| ine | municipio |
| lat, lon | WGS84, convertidas desde UTM ETRS89 (EPSG:25830) |
| fuente | conjunto de origen |

Fuentes: «Centros educativos de la comunidad de Madrid» (solo `SITUACIÓN = ALTA`) y «Registro
de centros de atención social» (sectores Mujer, Familia, Infancia, inmigración, sin hogar y
centros de rehabilitación laboral; se excluyen los residenciales).

## `salario_ocupacion.csv`

Ganancia media anual por trabajador por gran grupo de ocupación CNO-11 (ambos sexos, Comunidad
de Madrid). Fuente: «Recursos económicos de los hogares. Estructura salarial cuatrienal. Ganancia
media anual por trabajador por ocupación y sexo». `poco_fiable = True` cuando la fuente marca el
dato con «-» (100 a 500 observaciones). El gran grupo 6 no tiene dato publicable.

## `sectores.csv`

Códigos y nombres de los sectores.

## Tabla de referencia hecha a mano: `data/ref/ocupaciones.csv`

26 ocupaciones con su sector, código CNO-11 (4 dígitos, orientativo), tres «saltos cortos»
(ocupaciones con competencias muy compartidas) y un «salto con formación» con la formación
requerida y su duración típica. Correspondencia elaborada por el equipo.
