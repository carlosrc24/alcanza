# Prompt para crear la presentación

Copiar y pegar en Claude, ChatGPT o similar.

```
Eres diseñador de presentaciones. Crea el contenido de una presentación de 6 diapositivas en español para el
MAD Open Data Challenge 2026 (jurado técnico; puntúa: rigor en el tratamiento de datos abiertos, resolución del
reto, sencillez para el usuario e interactividad). Se presenta en ~4,5 minutos de diapositivas; el resto es demo
en directo de la app, así que las diapositivas deben ser muy visuales, con poco texto (máx. 3-4 líneas o una
cifra grande).

Para cada diapositiva dame: título, texto en pantalla, sugerencia visual concreta (gráfico, icono, mapa,
esquema) y notas del ponente (2-4 frases). Estilo: limpio, moderno, colores sobrios (verde azulado oscuro
#14213d / #0f766e con acento ámbar #d97706), una idea por diapositiva.

PROYECTO: «Alcanza — el empleo que está a tu alcance». Equipo: Carlos Rodríguez Caparrós, Ana Denis Rubio,
Jiaxing Zhu, Pedro González Carnero (Máster en Ingeniería Informática, UC3M).

Qué hace: recomienda a una persona en paro de la Comunidad de Madrid qué empleo puede alcanzar de verdad en
transporte público, cuánta gente compite por él, qué empleo parecido puede hacer o al que puede llegar con
formación, y qué escuelas infantiles, formación y servicios sociales tiene cerca. La persona lo cuenta con sus
palabras y ajusta el tiempo máximo de viaje y sus prioridades. Segunda vista para orientadores/Consejería: mapa
de «desiertos de empleo accesible», simulador «¿y si…?» y ranking de mejoras de transporte.

Caso conductor: Lucía, auxiliar administrativa en Parla, sin coche, hijo de 2 años, dispuesta a formarse.
Con 60 min en transporte público alcanza ~34.700 puestos de su sector en 7 municipios, pero hay 0,8 puestos
por cada parado que compite. Con 75 min entra Madrid (62 min desde Parla): ~970.000 puestos en 14 municipios y
12,4 puestos por competidor. 17 escuelas infantiles en Parla.

Datos abiertos (protagonistas los de la Comunidad de Madrid): afiliados a la Seguridad Social por lugar de
trabajo y rama, y por residencia; paro registrado por sector; padrón; salario por ocupación; centros educativos;
centros de atención social; límites municipales; Encuesta Domiciliaria de Movilidad 2018; GTFS del Consorcio
de Transportes y de Renfe Cercanías; OpenStreetMap. 179 municipios unidos por código INE; cada cifra con fuente
y fecha.

Método: tiempos reales en transporte público entre municipios (r5py con GTFS y OpenStreetMap, 7-9 h, mediana);
índice de accesibilidad 2SFCA (Shen 1998) por sector, tiempo y modo: los puestos de cada destino se reparten
entre los parados que pueden llegar a él (mide la competencia). Conserva el total de puestos, así que el
simulador redistribuye y no infla. Desierto = tercio con menos acceso y tercio con más paro por habitante.
Huecos declarados: paro 2026 solo en total (estructura sectorial estimada); GTFS de interurbanos publicado como
datos parciales (26 municipios con tiempos estimados por regresión cuantílica, no se clasifican como
desiertos); Madrid capital como un único destino.

Validación: frente a 2.377 viajes reales casa-trabajo de la EDM 2018 (80 pares), diferencia mediana −0,5 min,
72 % de pares a ±15 min; a más acceso, menos paro (Spearman negativo en 103 municipios); robustez frente a
variante gaussiana del índice: Spearman 0,85.

Impacto: con 10 min de ahorro de transporte, mejorar Parla saca de un desierto a sus 7.041 parados.

Herramientas: Python (pandas, geopandas), r5py (Java), scikit-learn, scipy, Streamlit + pydeck, Google Gemini
(solo interpreta el texto libre; nunca puntúa ni recomienda; respaldo por reglas), pytest (16 pruebas), GitHub
(github.com/carlosrc24/alcanza).

Estructura:
1. Portada: Alcanza + lema + equipo + UC3M.
2. El problema con Lucía: «no es dónde hay empleo, sino a qué empleo llegas».
3. Datos abiertos: fuentes como iconos agrupados (empleo, paro, transporte, recursos) + huecos tratados.
4. Método: esquema en 3 pasos (tiempos reales → puestos y competidores → índice 2SFCA → recomendación).
5. Validación: cifras grandes (−0,5 min, 72 %, 2.377 viajes) + herramientas usadas.
6. Cierre: dos preguntas respondidas (persona / administración), cifra de 7.041 parados, enlace a GitHub.

Ponentes: diapos 1-2 Pedro, diapo 3 Ana, diapos 4-5 Jiaxing, diapo 6 Pedro (la demo la hacen Carlos y Ana).
```
