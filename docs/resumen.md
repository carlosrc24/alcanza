# Alcanza — resumen para el equipo

**Alcanza — el empleo que está a tu alcance.** MAD Open Data Challenge 2026 · demo presencial el 20 de octubre.
Repositorio: https://github.com/carlosrc24/alcanza

## El problema en una frase

Una persona en paro no busca empleo en toda la Comunidad de Madrid, sino **donde puede llegar en transporte
público en un tiempo razonable**, y allí **compite con otros parados que también llegan**. Ningún portal de
empleo tiene esto en cuenta.

## Qué hace

**Vista «Busco empleo» (para la persona)**

1. La persona escribe su situación con sus palabras: *«Soy auxiliar administrativa en Parla, no tengo coche,
   tengo un hijo de 2 años y quiero formarme»*. La IA lo convierte en campos (ocupación, municipio, coche,
   hijo, formación), que se pueden corregir a mano.
2. Ajusta el **tiempo máximo de viaje** (15–90 min) y **qué le importa más** (poca competencia, muchos puestos,
   sector que crece, salario, conciliación, evitar formación larga).
3. Recibe:
   - Cuántos puestos de su sector alcanza, cuántos hay por cada parado que compite y si el sector crece.
   - Un **mapa** con los municipios a su alcance, los destinos recomendados, las escuelas infantiles y los
     centros de formación.
   - **Tres caminos**: su mismo empleo, un empleo parecido sin formación (salto corto) y otro con formación.
     Cada uno con puntuación desglosada, el «por qué» en lenguaje claro y dónde buscar.

**Vista «Orientación y planificación» (para orientadores y la Consejería)**

- Mapa de **desiertos de empleo accesible**: municipios con poco acceso al empleo y mucho paro.
- **Simulador «¿y si…?»**: qué pasa si mejora el transporte de un municipio.
- **Ranking de mejoras de transporte**, ordenado por parados que salen de un desierto.
  Ejemplo: con T = 60 min y 10 min de ahorro, mejorar Parla saca de un desierto a sus **7.041 parados**.

**Vista «Datos y método»**: método, validación, fuentes con fecha y descarga de todos los datasets.

## El caso de Lucía (cifras de la app)

Auxiliar administrativa en Parla, sin coche, en transporte público:

| Tiempo máximo | Puestos de su sector | Municipios | Puestos por demandante |
|---|---|---|---|
| 60 min | ~34.700 | 7 | 0,8 |
| 75 min | ~970.700 | 14 | 12,4 |

Al pasar de 60 a 75 min entra Madrid capital (62 min desde Parla). Hay 17 escuelas infantiles en Parla.

## Cómo funciona, en tres pasos

1. **Tiempos reales**: con los horarios oficiales del transporte (GTFS) y la red de calles de OpenStreetMap
   calculamos el tiempo en transporte público entre los 179 municipios, de 7 a 9 de la mañana (mediana).
2. **Puestos y competidores**: cruzamos los puestos de trabajo por municipio y sector (afiliación a la Seguridad
   Social por lugar de trabajo) con el paro registrado por sector.
3. **Índice 2SFCA** (Shen, 1998): los puestos de cada destino se reparten entre todos los parados que pueden
   llegar a él; la persona suma lo que le toca de cada destino a su alcance. Así se mide la competencia real.
   El índice conserva el total de puestos, por eso el simulador **redistribuye**, no infla.

La recomendación pondera esos indicadores con las prioridades de la persona. **La IA nunca puntúa ni
recomienda**: solo entiende el texto libre. Todas las cifras salen de datos abiertos.

## Validación

- Tiempos frente a **2.377 viajes reales** casa→trabajo de la Encuesta Domiciliaria de Movilidad 2018 (80 pares
  de municipios): diferencia mediana **−0,5 min**, error medio 10,7 min, **72 %** de pares a ±15 min.
- **A más acceso, menos paro**: correlación negativa en 103 municipios (también con los puestos alcanzables,
  que no usan el paro, así que no es circular).
- **Robustez**: el índice con umbral frente a una versión con decaimiento gaussiano da Spearman 0,85.

## Datos abiertos usados

Protagonistas los de la **Comunidad de Madrid** (catálogo datos.comunidad.madrid):

- Afiliados a la Seguridad Social por lugar de trabajo y rama (dónde están los puestos).
- Afiliados por lugar de residencia y rama.
- Paro registrado por sector.
- Padrón (población) y ganancia media por ocupación (salario).
- Centros educativos (escuelas infantiles, FP) y registro de centros de atención social.
- Límites municipales.
- Resultados de la Encuesta Domiciliaria de Movilidad 2018 (validación).

Además: GTFS del Consorcio Regional de Transportes (Metro, Metro Ligero, EMT, interurbanos, urbanos), GTFS de
Renfe Cercanías y OpenStreetMap. Cada cifra de la app lleva su fuente y su fecha.

## Herramientas

| Para qué | Herramienta |
|---|---|
| Tratamiento de datos | Python, pandas, numpy |
| Geografía y mapas | geopandas, shapely |
| Tiempos en transporte público | r5py (motor R5, Java) sobre GTFS + OpenStreetMap |
| Estimar tiempos donde faltan horarios | scikit-learn (regresión cuantílica) |
| Validación estadística | scipy (correlación de Spearman) |
| Aplicación y mapas interactivos | Streamlit, pydeck |
| Entender el texto libre | Google Gemini (salida JSON restringida a nuestras listas; respaldo por reglas) |
| Calidad | pytest (16 pruebas), GitHub |

## Límites que declaramos (y cómo los tratamos)

- **Madrid capital es un único destino**, sin desagregar por distritos: por eso el salto entre 60 y 75 min.
- **Horarios incompletos**: el GTFS de interurbanos se publica como «Datos parciales». En 26 municipios se
  estiman los tiempos; no se clasifican como desiertos (borde morado en el mapa) y la app avisa.
- **Paro de 2026 solo en total**: se reparte por sectores con la estructura de 2025 (marcado como estimado).
- **No hay ofertas de empleo abiertas**: la demanda se aproxima con los puestos existentes y su tendencia.

## Datasets elaborados

En `data/processed/`, cada uno documentado en su `README.md` (columnas, unidades, fuente y fecha): municipios,
puestos y parados por municipio y sector, balance de empleo, tiempos en transporte público, indicadores de
accesibilidad, recursos (escuelas infantiles, formación, servicios sociales), validación y fuentes.

## Cómo arrancarla

```bash
pip install -r requirements.txt
python -m streamlit run app/app.py     # abre http://localhost:8501
```
