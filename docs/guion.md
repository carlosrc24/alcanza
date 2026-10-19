# Guion de la presentación (~9 min)

Mitad diapositivas (~4,5 min) y mitad demo en directo (~4,5 min). Hablan los cuatro. El reparto de nombres es
provisional: cambiadlo como queráis.

| Tiempo | Quién | Qué | Soporte |
|---|---|---|---|
| 0:00–1:15 | Pedro | El problema y Lucía | Diapos 1–2 |
| 1:15–2:45 | Ana | Datos abiertos | Diapo 3 |
| 2:45–4:30 | Jiaxing | Método y validación | Diapos 4–5 |
| 4:30–7:30 | Carlos | Demo: vista «Busco empleo» | App |
| 7:30–8:45 | Ana | Demo: vista «Orientación y planificación» | App |
| 8:45–9:30 | Pedro | Cierre | Diapo 6 |

---

## 0:00–1:15 · Pedro — El problema

> «Lucía vive en Parla. Es auxiliar administrativa, no tiene coche y tiene un hijo de 2 años.
> Para ella, "hay mucho empleo en Madrid" no sirve de nada si no puede llegar en un tiempo razonable y volver
> a recoger a su hijo.
> La pregunta no es dónde hay empleo, sino **qué empleo está a su alcance**, cuánta gente compite por él y qué
> puede hacer para mejorar sus opciones. Eso es Alcanza.»

## 1:15–2:45 · Ana — Datos abiertos

> «Todo sale de datos abiertos, y los protagonistas son los de la Comunidad de Madrid.»

- **Dónde están los puestos**: afiliados a la Seguridad Social por lugar de trabajo y sector.
- **Quién compite**: paro registrado por sector.
- **Contexto**: padrón, salarios, centros educativos y servicios sociales.
- **Transporte**: horarios GTFS del Consorcio y de Renfe Cercanías sobre OpenStreetMap.
- Unimos los 179 municipios por su código INE. **Cada cifra de la app lleva su fuente y su fecha.**

> «Contamos también los huecos de los datos, porque es parte de hacerlo bien: el paro de 2026 solo viene en
> total y lo repartimos por sectores de forma estimada; y el GTFS de interurbanos está publicado como datos
> parciales, así que en 26 municipios estimamos los tiempos y la app lo avisa.»

## 2:45–4:30 · Jiaxing — Método y validación

- Con **r5py** calculamos el tiempo real en transporte público entre todos los municipios, de 7 a 9 de la mañana.
- Encima aplicamos el **2SFCA**, un índice de accesibilidad que no solo cuenta los puestos a tu alcance: los
  reparte entre todos los parados que también llegan a ellos. **Así medimos la competencia real.**
- El índice reparte el total de puestos, no lo multiplica: por eso el simulador redistribuye el acceso entre
  municipios en lugar de inflarlo.
- **Validación**: frente a 2.377 viajes reales de la Encuesta de Movilidad 2018, la diferencia mediana es de
  **−0,5 minutos** y el **72 %** de los pares queda a ±15 min. Y a más acceso, menos paro (103 municipios).
- La IA (Google Gemini) **solo traduce el texto libre** a campos. No puntúa ni recomienda: todas las cifras
  salen de los datos.

## 4:30–7:30 · Carlos — Demo «Busco empleo»

1. Abrir «Escríbelo con tus palabras», usar el texto de Lucía y pulsar el botón. Enseñar que la IA ha rellenado
   ocupación, Parla, sin coche, con hijo y con formación.
2. Poner el tiempo en **60 min**:
   > «Unos 34.700 puestos de su sector en 7 municipios, pero hay menos de un puesto (0,8) por cada parado que
   > compite.»
3. Subir a **75 min**:
   > «Entra Madrid, a 62 minutos de Parla: unos 970.000 puestos en 14 municipios y 12,4 puestos por
   > competidor. Un cuarto de hora más de viaje cambia por completo sus opciones.»
4. **Los tres caminos**: auxiliar administrativa, el salto corto (teleoperadora a 75 min) y administrativa
   contable con formación. Abrir «Por qué y cómo» de una tarjeta: leer el «por qué» y enseñar el desglose de
   la puntuación.
5. Subir la prioridad **«Salario»** a 5: el camino con formación (administrativa contable, ~35,7 k€/año) pasa
   al primer puesto y se marca como «el que mejor encaja con tus prioridades».
   > «Cada persona decide qué le importa: la app reordena sus caminos al instante.»
6. En el mapa: **escuelas infantiles** (17 en Parla) y centros de formación cerca.

## 7:30–8:45 · Ana — Demo «Orientación y planificación»

1. Mapa de **desiertos de empleo accesible**:
   > «En rojo, municipios con poco acceso al empleo y mucho paro. Los de borde morado tienen horarios
   > incompletos en la fuente y no los clasificamos: preferimos no afirmar lo que los datos no sostienen.»
2. **Ranking de mejoras** con T = 60 min y 10 min de ahorro:
   > «Mejorar el transporte de Parla saca de un desierto a sus 7.041 parados. Esto es lo que debería mirar la
   > Consejería al priorizar inversiones.»

## 8:45–9:30 · Pedro — Cierre

> «Alcanza responde con datos abiertos de la Comunidad a dos preguntas. A la persona: qué empleo está de verdad
> a su alcance. A la administración: dónde mejorar el transporte cambia más vidas.
> Está validado con viajes reales y es reproducible: el código y los datasets están en GitHub. Gracias.»

---

## Preguntas probables del jurado

- **¿Por qué el simulador no suma acceso?** El 2SFCA conserva el total (Σ parados × acceso = puestos
  alcanzados): mejorar un municipio redistribuye el acceso. Por eso el ranking ordena por parados que salen de
  un desierto.
- **¿Por qué el salto tan grande entre 60 y 75 min?** Madrid capital es un único destino (su núcleo): al
  alcanzarlo entran todos sus puestos de golpe. Es un límite declarado; desagregar por distritos es la mejora
  natural.
- **¿Hay ofertas reales?** No existen datos abiertos de ofertas. Aproximamos la demanda con los puestos
  existentes y su tendencia en el último año.
- **¿Qué hace la IA exactamente?** Convierte el texto en campos con una salida JSON restringida a nuestras listas
  (ocupación y municipio solo pueden ser valores válidos). Si falla, entran las reglas. Nunca puntúa.
- **¿Qué datos faltan?** GTFS de interurbanos parcial (26 municipios estimados, no clasificados como desiertos)
  y paro de 2026 solo en total (reparto sectorial estimado). Todo marcado en la app.

## Antes de empezar (checklist)

- [ ] App arrancada antes de salir: `python -m streamlit run app/app.py` → http://localhost:8501
- [ ] Pantalla a 1280×720 y Chrome sin otras pestañas pesadas.
- [ ] Internet comprobado (el mapa base y la IA lo necesitan).
- [ ] **Plan B**: capturas de cada paso de la demo. Sin IA, la app usa reglas y la demo sigue igual.
- [ ] Cargador del portátil.
