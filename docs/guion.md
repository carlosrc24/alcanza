# Guion de la presentación (~9 min)

Mitad diapositivas (~4,5 min) y mitad demo en directo (~4,5 min). Hablan los cuatro; el reparto de nombres es
provisional.

| Tiempo | Quién | Qué | Soporte |
|---|---|---|---|
| 0:00–1:15 | Pedro | El problema: Lucía y Javier | Diapos 1–2 |
| 1:15–2:45 | Ana | Datos abiertos | Diapo 3 |
| 2:45–4:30 | Jiaxing | Método y validación | Diapos 4–5 |
| 4:30–7:30 | Carlos | Demo «Busco empleo»: Lucía (Chamberí) y Javier (Parla) | App |
| 7:30–8:45 | Ana | Demo «Orientación y planificación»: el «¿y si…?» de Parla | App |
| 8:45–9:30 | Pedro | Cierre | Diapo 6 |

La historia que une todo: **dónde vives decide a qué empleo llegas; la persona puede viajar más, pero la
administración puede acercarle el empleo con el transporte.**

Los dos textos de la demo (el primero viene escrito por defecto en la app):

> **Lucía:** He trabajado 3 años de auxiliar administrativa. Vivo en Chamberí, no tengo coche y tengo un niño de
> 2 años. No volvería a estudiar y lo máximo que estaría dispuesto a viajar es 15 min.

> **Javier:** He trabajado 6 años de camarero. Vivo en Parla, no tengo coche ni hijos. Si merece la pena, volvería
> a estudiar y lo máximo que estaría dispuesta a viajar es 45 min.

---

## 0:00–1:15 · Pedro — El problema

> «Lucía es auxiliar administrativa en Chamberí, con un hijo de 2 años. Javier es camarero en Parla. Ninguno
> tiene coche. A los dos les dicen que "en Madrid hay mucho empleo", pero eso no les sirve de nada si no pueden
> llegar en un tiempo razonable.
> La pregunta no es dónde hay empleo, sino **qué empleo está a su alcance**, cuánta gente compite por él y qué
> pueden hacer para mejorar. Y la respuesta depende muchísimo de **dónde viven**. Eso es Alcanza.»

## 1:15–2:45 · Ana — Datos abiertos

> «Todo sale de datos abiertos, y los protagonistas son los de la Comunidad de Madrid.»

- **Dónde están los puestos**: afiliados a la Seguridad Social por lugar de trabajo y sector.
- **Quién compite**: paro registrado por sector.
- **Contexto**: padrón, salarios, centros educativos (escuelas infantiles, FP) y servicios sociales.
- **Transporte**: horarios GTFS del Consorcio y de Renfe Cercanías sobre las calles de OpenStreetMap.
- 179 municipios unidos por su código INE. **Cada cifra lleva su fuente y su fecha** (vista «Datos y método»).

> «También contamos los huecos: no hay datos abiertos de ofertas, así que usamos los puestos que ya existen y su
> tendencia; el paro de 2026 solo viene en total y lo repartimos por sectores; y el GTFS de autobuses
> interurbanos está publicado como datos parciales, así que en 26 municipios estimamos los tiempos y lo avisamos.»

## 2:45–4:30 · Jiaxing — Método y validación

- Con **r5py** calculamos el tiempo real en transporte público entre todos los municipios: horarios oficiales,
  saliendo cada minuto de 7:00 a 9:00, y nos quedamos con la mediana. Para cinco barrios de Madrid, el viaje sale
  de una estación de Metro del barrio.
- Encima, el índice **puestos por demandante** (método 2SFCA): en cada destino, sus puestos se reparten entre
  todos los parados que pueden llegar; y tú sumas lo que te toca en cada destino al que llegas. **Así medimos la
  competencia real**, no solo cuántos puestos hay.
- **Validación**: frente a 2.377 viajes reales de la Encuesta de Movilidad 2018, la diferencia mediana es de
  **−0,5 minutos** y el **72 %** de los pares queda a ±15 min. Y a más acceso, menos paro (103 municipios).
- La IA (Google Gemini) **solo entiende el texto** que escribe la persona. No puntúa ni recomienda.

## 4:30–7:30 · Carlos — Demo «Busco empleo»

**Antes de empezar**: app abierta en «Busco empleo» con el texto de Lucía (viene por defecto) y el de Javier
copiado.

1. **Lucía, Chamberí, 15 min.** Pulsar «Entender mi situación».
   - Etiquetas: *Auxiliar administrativo/a · Madrid · Chamberí (28010) · sin coche · hijo/a de 0 a 3 años · sin
     formarse · hasta 15 min*.
   > «La IA ha entendido hasta el barrio: el viaje sale de su estación de Metro, Iglesia. En solo 15 minutos tiene
   > unos **915.000 puestos** de su sector y **20 puestos por cada parado** que compite, 1,4 veces la media. Y
   > 41 escuelas infantiles a menos de 2 km de casa.»
   - Tarjetas: auxiliar administrativa (92) y teleoperadora (86). La de formación sale en gris y al final porque
     ha dicho que no quiere estudiar.
2. **Javier, Parla, 45 min.** Borrar el texto, pegar el de Javier y pulsar «Entender mi situación».
   > «Ahora Javier, camarero en Parla. Con 45 minutos: unos **44.600 puestos** de hostelería y comercio en 4
   > municipios y **4,4 por demandante**, un 66 % menos que la media. Lucía tenía 20 en un cuarto de hora.»
   - Tarjetas: camarero (68, mejor destino Pinto a 42 min), recepcionista (68) y recepcionista de hotel con
     formación (60).
3. **Subir el tiempo a 75 min.**
   > «Si acepta 75 minutos entra Madrid, a 62 de Parla: unos **724.000 puestos** en 14 municipios y **11,2 por
   > demandante**. Pero son dos horas y media al día de viaje.»
4. **Subir la prioridad «Salario» a 5**: recepcionista (~25,9 k€/año) pasa por delante de camarero (~20,8 k€).
   > «Cada persona decide qué le importa y los caminos se reordenan al instante.»
5. **Abrir «Por qué y cómo»** de la primera tarjeta: leer el «por qué» y señalar el desglose de la puntuación.
6. **Pulsar Indeed** (o LinkedIn / InfoJobs) en esa tarjeta: se abre la búsqueda real de hoy.
   > «Alcanza te dice dónde buscar; con un clic ves las ofertas que hay ahí hoy.»

## 7:30–8:45 · Ana — Demo «Orientación y planificación»

**Ajustes**: sector «Todos los sectores», tiempo máximo **60 min**; en el simulador, **Parla**, **10 min**,
«Todos los municipios».

1. **Mapa de desiertos.**
   > «Lo que le pasa a Javier le pasa a mucha gente. En rojo, los desiertos de empleo accesible: municipios con
   > poco empleo a su alcance y mucho paro. Los de borde morado tienen horarios incompletos en la fuente y no los
   > clasificamos: no afirmamos lo que los datos no sostienen.»
2. **El «¿y si…?».**
   > «Javier podía viajar más. La Consejería tiene otra opción: acercarle el empleo. Si el transporte desde Parla
   > ahorrara 10 minutos, su acceso pasaría de 0,15 a 1,01 veces la media regional…»
3. **La tabla «¿Dónde rinde más esta mejora?»**:
   > «…y **los 7.041 parados de Parla saldrían del desierto**. Probada la misma mejora en cada municipio, es la que
   > más gente saca. Lo que Javier consigue viajando más, la administración se lo puede dar a 7.041 personas.»

## 8:45–9:30 · Pedro — Cierre

> «Alcanza responde con datos abiertos de la Comunidad a dos preguntas. A la persona: qué empleo está de verdad a
> su alcance, desde su barrio, y dónde buscarlo hoy. A la administración: dónde mejorar el transporte cambia más
> vidas. Está validado con viajes reales y es reproducible: el código y los datos están en GitHub. Gracias.»

---

## Preguntas probables del jurado

- **¿Por qué Lucía, con 15 min, ya alcanza todo Madrid?** Madrid es un único destino y dentro del propio
  municipio se supone un viaje de 10 min, así que con poco tiempo cualquier barrio de Madrid alcanza Madrid
  entero. El código postal se nota con más tiempo: a 60 min, Villa de Vallecas llega a 17 municipios y Sol a 38.
  Desagregar Madrid por distritos es la mejora natural.
- **¿Cómo tratáis el código postal?** Son 5 ejemplos preestablecidos (Sol, Chamberí, Moncloa-Argüelles, Puente
  de Vallecas, Villa de Vallecas). El viaje sale de una estación de Metro del barrio, con r5py como el resto. Si
  el barrio llega a un destino al que no llega el centro de Madrid, contamos también a los parados de Madrid como
  competidores, para no inflar el resultado.
- **¿Hay ofertas reales?** No hay datos abiertos de ofertas. Aproximamos la demanda con los puestos existentes y
  su tendencia; los botones abren los portales, pero las ofertas no entran en el cálculo. Si la Comunidad
  publicara ofertas por municipio, sustituirían a los puestos sin cambiar el método.
- **¿Por qué el simulador no suma acceso?** El índice reparte un total fijo de puestos: lo que gana un municipio
  lo pierde en parte la competencia en otros. Por eso el ranking ordena por parados que salen de un desierto.
- **¿Por qué esas cifras redondas en la tabla (7.041, 234…)?** Un municipio está o no en un desierto: cuando sale,
  cuentan todos sus parados.
- **¿Qué hace la IA exactamente?** Convierte el texto en campos con una salida restringida a nuestras listas. Si
  falla, entran las reglas, que entienden igual los dos textos de la demo. Nunca puntúa.
- **¿Qué datos faltan?** GTFS de interurbanos parcial (26 municipios estimados) y paro de 2026 solo en total. Todo
  marcado en la app y documentado.

## Antes de empezar (checklist)

- [ ] Portátil con Chrome recién abierto y sin otras apps pesadas.
- [ ] App arrancada: `python -m streamlit run app/app.py` → http://localhost:8501.
- [ ] Probado el recorrido entero una vez (Lucía → Javier → 75 min → Salario → Indeed → planificación).
- [ ] Texto de Javier copiado en el portapapeles o en un bloc de notas.
- [ ] Internet comprobado (mapa base, IA y botones de ofertas).
- [ ] **Plan B**: capturas de cada paso. Sin IA, la app usa las reglas y entiende los dos textos igual.
- [ ] Pantalla a 1280×720 y cargador.
