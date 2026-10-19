# Prompt para crear la presentación

Copiar y pegar en Claude, ChatGPT o similar.

```
Eres diseñador de presentaciones. Crea el contenido de una presentación de 6 diapositivas en español para el
MAD Open Data Challenge 2026 (jurado técnico; puntúa: rigor en el tratamiento de datos abiertos, resolución del
reto, sencillez para el usuario e interactividad). Se presenta en ~4,5 minutos de diapositivas; el resto es demo
en directo de la app, así que las diapositivas deben ser muy visuales, con poco texto (máx. 3-4 líneas o una
cifra grande).

Para cada diapositiva dame: título, texto en pantalla, sugerencia visual concreta (gráfico, icono, mapa,
esquema) y notas del ponente (2-4 frases). Estilo: limpio, moderno, colores sobrios (azul noche #14213d y verde
azulado #0f766e, con acento ámbar #d97706), una idea por diapositiva.

PROYECTO: «Alcanza — el empleo que está a tu alcance». Equipo: Carlos Rodríguez Caparrós, Ana Denis Rubio,
Jiaxing Zhu, Pedro González Carnero (Máster en Ingeniería Informática, UC3M).

LA IDEA: una persona en paro no busca empleo en toda la Comunidad de Madrid, sino donde puede llegar en
transporte público en un tiempo razonable, y allí compite con otros parados que también llegan. Alcanza le dice
qué empleo tiene de verdad a su alcance, a qué trabajo parecido puede saltar, si le compensa formarse y qué
escuelas infantiles tiene cerca, y con un clic le abre las ofertas de hoy. A la administración le dice dónde
vive la gente que se queda sin empleo a su alcance y qué mejora de transporte saca a más personas de esa
situación.

CÓMO SE USA: la persona escribe su situación con sus palabras; la IA (Google Gemini) la entiende (ocupación,
municipio y hasta el barrio, coche, hijos, formación, tiempo de viaje). Ajusta el tiempo máximo y sus
prioridades; ve sus cifras, un mapa y tres caminos (su mismo empleo, un salto corto sin formación y un salto con
formación), ordenados por sus prioridades, con el porqué y botones a LinkedIn, InfoJobs e Indeed. La IA nunca
puntúa ni recomienda: todas las cifras salen de datos abiertos.

CASO CONDUCTOR (dos personas sin coche, dos lugares):
- Lucía, auxiliar administrativa en Chamberí (Madrid), hijo de 2 años, 15 min de viaje como máximo: ~915.000
  puestos de su sector y 20 puestos por cada parado que compite (1,4 veces la media); 41 escuelas infantiles a
  menos de 2 km.
- Javier, camarero en Parla, 45 min como máximo: ~44.600 puestos de hostelería y comercio en 4 municipios y 4,4
  puestos por demandante (un 66 % menos que la media). Si acepta 75 min entra Madrid (62 min): ~724.000 puestos y
  11,2 por demandante, pero con dos horas y media de viaje al día.
- La administración: si el transporte desde Parla ahorrara 10 minutos, sus 7.041 parados saldrían de un
  «desierto de empleo accesible»; es la mejora de la región que más gente saca.
Frase: «Lo que Javier consigue viajando más, la administración se lo puede dar a 7.041 personas.»

DATOS ABIERTOS (protagonistas los de la Comunidad de Madrid): afiliados a la Seguridad Social por lugar de
trabajo y rama, y por residencia; paro registrado por sector; padrón; salario por ocupación; centros educativos;
centros de atención social; límites municipales; Encuesta Domiciliaria de Movilidad 2018. Además, GTFS del
Consorcio de Transportes y de Renfe Cercanías, y OpenStreetMap. 179 municipios unidos por código INE; cada cifra
con fuente y fecha. No hay datos abiertos de ofertas: la demanda se aproxima con los puestos existentes y su
tendencia.

MÉTODO: tiempos reales en transporte público entre municipios con r5py (horarios oficiales, salidas cada minuto
de 7 a 9 h, mediana). Índice «puestos por demandante» (2SFCA, Shen 1998): en cada destino, sus puestos ÷ los
parados que pueden llegar; para la persona, la suma en los destinos a los que llega. Desierto = tercio con menos
acceso y tercio con más paro por habitante. Cinco ejemplos por código postal en Madrid capital (Sol, Chamberí,
Moncloa-Argüelles, Puente de Vallecas, Villa de Vallecas): el viaje sale de una estación de Metro del barrio.
Límites declarados: Madrid capital como un único destino; GTFS de interurbanos publicado como datos parciales
(26 municipios estimados, no clasificados como desiertos); paro de 2026 solo en total.

VALIDACIÓN: frente a 2.377 viajes reales casa-trabajo de la EDM 2018 (80 pares), diferencia mediana −0,5 min,
72 % de pares a ±15 min; a más acceso, menos paro (Spearman negativo en 103 municipios); robustez frente a una
variante gaussiana del índice: Spearman 0,85.

HERRAMIENTAS: Python (pandas, geopandas), r5py (Java), scikit-learn, scipy, Streamlit + pydeck, Google Gemini,
pytest (18 pruebas), GitHub (github.com/carlosrc24/alcanza).

ESTRUCTURA:
1. Portada: Alcanza + lema + equipo + UC3M.
2. El problema: «no es dónde hay empleo, sino a qué empleo llegas». Dos personas, dos lugares: Lucía en
   Chamberí, 20 puestos por demandante en 15 min, frente a Javier en Parla, 4,4 en 45 min (cifras grandes
   enfrentadas).
3. Datos abiertos: fuentes como iconos agrupados (empleo, paro, transporte, recursos) + huecos tratados.
4. Método: esquema en 3 pasos (tiempos reales → puestos y competidores → puestos por demandante → tres caminos
   y ofertas).
5. Validación: cifras grandes (−0,5 min, 72 %, 2.377 viajes) + herramientas usadas.
6. Cierre: dos preguntas respondidas (persona / administración), cifra de 7.041 parados, enlace a GitHub.

PONENTES: diapos 1-2 Pedro, diapo 3 Ana, diapos 4-5 Jiaxing, diapo 6 Pedro (la demo la hacen Carlos y Ana).
```
