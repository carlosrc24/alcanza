# Alcanza — resumen para el equipo

**Alcanza — el empleo que está a tu alcance.** MAD Open Data Challenge 2026 · demo presencial el 20 de octubre.
Repositorio: https://github.com/carlosrc24/alcanza

## La idea en tres frases

1. Una persona en paro no busca empleo en toda la Comunidad de Madrid, sino **donde puede llegar en transporte
   público en un tiempo razonable**, y allí **compite con otros parados que también llegan**.
2. Alcanza le dice **qué empleo tiene de verdad a su alcance**, a qué trabajo parecido puede saltar, si le
   compensa formarse y qué escuelas infantiles tiene cerca; y con un clic le abre las ofertas de hoy.
3. A la administración le dice **dónde vive la gente que se queda sin empleo a su alcance** y **qué mejora de
   transporte saca a más personas de esa situación**.

Todas las cifras salen de datos abiertos, sobre todo de la Comunidad de Madrid. La IA solo entiende el texto.

## Qué hace la app (3 vistas)

### 1. «Busco empleo» — para la persona

**Paso 1 · Tu situación.** La persona escribe su situación con sus palabras y pulsa «Entender mi situación».
La IA (Google Gemini) saca de ahí: ocupación, municipio (y barrio, si es uno de los ejemplos de Madrid), si tiene
coche, si tiene un hijo de 0 a 3 años, si quiere formarse y cuánto está dispuesta a viajar. Debajo aparece en
etiquetas lo que se ha entendido. Si la IA falla (sin internet o sin cuota), entran unas reglas fijas.

> Los campos para rellenarlo a mano siguen en el código, comentados para la demo.

**Paso 2 · Ajusta a tu caso.**
- **Tiempo máximo de viaje** (15–90 min): decide a qué municipios llegas. Cambia cifras, mapa y caminos.
- **¿Qué te importa más?** (poca competencia, muchos puestos, sector que crece, salario, conciliación, evitar
  formación larga): cambia la puntuación y **el orden** de los tres caminos, no el mapa.

**Resultados.**
- **Cifras**: puestos de tu sector a tu alcance, **puestos por demandante** (la competencia), comparación con la
  media regional y variación en el último año.
- **Mapa**: municipios a tu alcance coloreados por puestos por demandante, destinos recomendados (borde naranja),
  escuelas infantiles (rosa) y centros de formación (morado).
- **Tus tres caminos**, ordenados por puntuación (el mejor, destacado): **trabajo directo** (lo tuyo),
  **salto corto** (un empleo parecido sin formación) y **salto con formación** (mejor salario tras formarte).
  Cada uno con «Por qué y cómo» (explicación, desglose de la puntuación y dónde buscar) y **botones de ofertas
  de hoy** en LinkedIn (filtrado a «con experiencia»), InfoJobs (provincia de Madrid) e Indeed, ya buscando esa
  ocupación en el mejor destino. Son solo enlaces: las ofertas no entran en el cálculo.

**Ejemplos por código postal en Madrid capital.** Madrid es un solo punto en el modelo. Para 5 barrios
preestablecidos el viaje sale de una estación de Metro del barrio: **28013 Sol, 28010 Chamberí, 28008
Moncloa-Argüelles, 28018 Puente de Vallecas y 28031 Villa de Vallecas**. Se detectan solos al escribir «vivo en
Chamberí» o «vivo en el 28031». A 60 min, por ejemplo, desde Villa de Vallecas se llega a 17 municipios (15,1
puestos por demandante) y desde Sol a 38 (19,0). Con poco tiempo (15–30 min) todos los barrios dan lo mismo,
porque solo alcanzan Madrid.

### 2. «Orientación y planificación» — para orientadores y la Consejería

Es lo mismo que ve cada persona, pero sumado para toda la región, y con la palanca de la administración: el
transporte.

- **Desierto de empleo accesible**: municipio que está a la vez en el tercio con **menos acceso al empleo** y en
  el tercio con **más paro por habitante** (y al menos 50 parados). Borde rojo en el mapa. Los 26 municipios con
  horarios de autobús incompletos en la fuente no se clasifican (borde morado).
- **Cifras**: parados que viven en desiertos, cuántos municipios lo son y la media regional.
- **Dónde actuar primero**: los desiertos ordenados por número de parados.
- **Simulador «¿y si…?»**: eliges un municipio, cuántos minutos se ahorran (más frecuencia, una línea directa) y
  hacia dónde. Se restan esos minutos a sus viajes y se recalcula el índice: cuánto mejora su acceso, cuántos
  parados salen de un desierto (y cuántos entran) y cuántos municipios mejoran. Es un escenario, no una predicción.
- **¿Dónde rinde más esta mejora?**: la misma mejora probada en cada municipio, uno a uno; los 5 que sacan a más
  parados de un desierto. **Con 60 min y 10 min de ahorro, mejorar Parla saca de un desierto a sus 7.041 parados.**
  La cifra va a saltos: cuando un municipio sale del desierto, cuentan todos sus parados.

### 3. «Datos y método» — transparencia

Método explicado en dos pasos (con la fórmula técnica en un desplegable), validación, fuentes con su fecha y
descarga de todos los datasets elaborados.

## Los dos ejemplos de la demo

- **Lucía**, auxiliar administrativa en **Chamberí**, hijo de 2 años, sin coche, no quiere estudiar, 15 min:
  ~915.000 puestos de su sector y **20 puestos por demandante** (1,4 veces la media); 41 escuelas infantiles a
  menos de 2 km.
- **Javier**, camarero en **Parla**, sin coche ni hijos, se formaría, 45 min: ~44.600 puestos en 4 municipios y
  **4,4 por demandante** (un 66 % menos que la media). Con 75 min entra Madrid: ~724.000 puestos y 11,2.
- **La administración**: con 10 min de ahorro en el transporte de Parla (todos los sectores, 60 min), sus **7.041
  parados** salen del desierto.

## Cómo funciona por dentro

1. **Tiempos reales en transporte público** (r5py): horarios oficiales (GTFS) de Metro, Metro Ligero, EMT,
   interurbanos, urbanos y Cercanías, más las calles de OpenStreetMap para los tramos a pie. Se simula un martes
   laborable saliendo cada minuto de 7:00 a 9:00 y se toma la mediana. Origen y destino: el centro de las paradas
   de cada municipio; dentro del propio municipio, 10 min. En coche: aproximación por distancia.
2. **Puestos y competidores**: puestos de trabajo por municipio y sector (afiliación por centro de trabajo) y
   parados registrados por sector.
3. **Puestos por demandante** (método 2SFCA):
   - en cada destino, sus puestos ÷ los parados del sector que pueden llegar a él;
   - para ti, la suma de eso en todos los destinos a los que llegas.

   *Ejemplo: Getafe 10.000 puestos / 5.000 parados que llegan = 2; Pinto 3.000 / 1.000 = 3; si llegas a los dos,
   tienes 5.* Cuantos más parados llegan a un sitio, menos toca a cada uno: así se mide la competencia.
4. **La recomendación** pondera esos indicadores con las prioridades de la persona. **La IA no puntúa ni recomienda.**

**Ofertas.** No hay datos abiertos de ofertas de empleo. La demanda se aproxima con los **puestos que ya existen**
y su tendencia (donde hay más empleo salen más vacantes por rotación). Los botones a los portales cierran el
círculo sin mezclar las ofertas en el cálculo.

## Validación

- Tiempos frente a **2.377 viajes reales** casa→trabajo de la Encuesta Domiciliaria de Movilidad 2018 (80 pares
  de municipios): diferencia mediana **−0,5 min**, error medio 10,7 min, **72 %** de pares a ±15 min.
- **A más acceso, menos paro**: correlación negativa en 103 municipios (también con los puestos alcanzables, que
  no usan el paro, así que no es circular).
- **Robustez**: frente a una versión del índice con decaimiento gaussiano, Spearman 0,85.

## Datos abiertos usados

**Comunidad de Madrid** (datos.comunidad.madrid), protagonistas:

| Dataset | Para qué |
|---|---|
| Afiliados por ubicación del centro de trabajo y rama. Municipios | dónde están los puestos (pieza central) y su tendencia |
| Afiliados por lugar de residencia y rama. Municipios | repartir el paro de «Servicios» y balance empleo/residentes |
| Paro registrado por sector (CNAE 09). Municipios | los competidores y el paro por habitante |
| Población empadronada. Municipios | paro por habitante (desiertos) |
| Ganancia media anual por ocupación | salario de cada camino |
| Centros educativos | escuelas infantiles y centros de FP |
| Registro de centros de atención social | recursos cercanos |
| Límites municipales (Covid 19 - TIA por Municipios y Distritos) | geometría de los mapas |
| Resultados de la EDM 2018 | validación de los tiempos |

**Transporte y calles**: GTFS del Consorcio Regional de Transportes (Metro, Metro Ligero, EMT, interurbanos,
urbanos), GTFS de Renfe Cercanías (el de Cercanías del Consorcio viene vacío) y OpenStreetMap.

**Hecho por nosotros**: `data/ref/ocupaciones.csv` (26 ocupaciones, sus saltos y la formación que piden).

**Valorados y no usados**: contratos registrados por municipio (solo 4 sectores y cuenta varias veces los
contratos cortos), paro mensual por edad, ocupados del censo, ESCO.

## Herramientas

| Para qué | Herramienta |
|---|---|
| Tratamiento de datos | Python, pandas, numpy |
| Geografía y mapas | geopandas, shapely |
| Tiempos en transporte público | r5py (motor R5, Java) sobre GTFS + OpenStreetMap |
| Estimar tiempos donde faltan horarios | scikit-learn (regresión cuantílica) |
| Validación estadística | scipy (Spearman) |
| App y mapas interactivos | Streamlit, pydeck |
| Entender el texto libre | Google Gemini (salida restringida a nuestras listas) con respaldo por reglas |
| Calidad | pytest (18 pruebas), GitHub |

## Límites que declaramos

- **Madrid capital es un único destino** (su centro): al alcanzarlo entran ~2,9 M de puestos de golpe. Los 5
  ejemplos por código postal afinan el origen, no el destino.
- **Horarios incompletos** en el GTFS de interurbanos («Datos parciales»): 26 municipios con tiempos estimados,
  no clasificados como desiertos y avisados en la app.
- **Paro de 2026 solo en total**: se reparte por sectores con la estructura de 2025 (marcado como estimado).
- **No hay ofertas abiertas**: demanda aproximada con puestos existentes y tendencia.

**Mejoras futuras**: origen por código postal o sección censal en toda la región, Madrid por distritos, contratos
registrados para medir rotación y temporalidad, ESCO para los saltos entre ocupaciones.

## Datasets elaborados

En `data/processed/`, documentados en su `README.md` (columnas, unidades, fuente y fecha): municipios, puestos y
parados por sector, balance de empleo, tiempos en transporte público, huecos del GTFS, indicadores de
accesibilidad, oportunidad por destino, recursos, salarios, validación, fuentes y los 3 ficheros de los ejemplos
por código postal.

## Cómo arrancarla

```bash
pip install -r requirements.txt
python -m streamlit run app/app.py     # abre http://localhost:8501
```

Necesita internet para el mapa base y para la IA (sin IA funcionan las reglas).
