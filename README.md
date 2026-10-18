# Alcanza — el empleo que está a tu alcance

Prototipo para el MAD Open Data Challenge 2026 (Comunidad de Madrid · UC3M).
Equipo: Carlos Rodríguez Caparrós, Ana Denis Rubio, Jiaxing Zhu, Pedro González Carnero.

Alcanza dice a una persona que busca empleo en la Comunidad de Madrid **qué empleo puede
alcanzar de verdad en transporte público**, con cuánta gente compite por él, qué trabajo
parecido o con algo de formación le abre más puertas, y qué escuelas infantiles y centros de
formación tiene cerca. Una segunda vista muestra a orientadores y a la Consejería los
**desiertos de empleo accesible** y simula mejoras de transporte.

## Ejecutar

```bash
python -m venv .venv && .venv\Scripts\activate      # Windows (en Linux/Mac: source .venv/bin/activate)
pip install -r requirements.txt
streamlit run app/app.py          # abre el prototipo (lee data/processed/, ya incluido en el repo)
```

**Entrada con IA (opcional).** Para que «Escríbelo con tus palabras» use Google Gemini, copia
`.env.example` como `.env` y pon tu clave de Google AI Studio en `GOOGLE_AI`. El `.env` no se
sube a git. Sin clave, o si Gemini no responde, la app entiende el texto con reglas fijas. La IA
solo rellena los campos del formulario para que la persona los revise: no puntúa ni recomienda.

Regenerar los datos desde cero (descarga ~250 MB a `data/raw/`):

```bash
python -m src.pipeline                      # reutiliza data/processed/tiempos_tp.csv
python -m src.pipeline --tiempos            # recalcula tiempos con r5py (Java 21+, 16 GB RAM, ~30 min;
                                            # por tandas reanudables en data/interim/)
python -m src.pipeline --tiempos --plan-c   # tiempos aproximados sin r5py
```

## Estructura

| Ruta | Qué hace |
|---|---|
| `src/config.py` | ids del catálogo, sectores, parámetros |
| `src/download.py` | descarga con fecha a `data/raw/` + metadatos de trazabilidad |
| `src/datos.py` | municipios, puestos por lugar de trabajo, parados por residencia, balance, salario |
| `src/gtfs.py` | normaliza los GTFS a un martes común (los feeds tienen calendarios distintos) |
| `src/tiempos.py` | matriz 179×179 con r5py (plan A) y plan C aproximado; coche aproximado |
| `src/indicadores.py` | 2SFCA (puestos por demandante) para 6 umbrales × 2 modos × 7 sectores |
| `src/recomendador.py` | perfil → tres tarjetas con puntuación desglosada y «por qué» |
| `src/ia.py` | texto libre → campos con Google Gemini (salida restringida a nuestras listas, varios modelos de respaldo) |
| `src/texto.py` | texto libre → campos con reglas fijas (respaldo sin IA; completa lo que la IA deja vacío) |
| `src/recursos.py` | escuelas infantiles, FP, formación para el empleo, servicios sociales |
| `src/simulador.py` | simulador «¿y si…?» y ranking de mejoras de transporte (parados que salen de desiertos) |
| `src/validacion.py` | validación: tiempos frente a la EDM 2018, acceso frente a paro, robustez del 2SFCA |
| `app/app.py` | prototipo Streamlit: ciudadanía, planificación, datos y método |
| `data/processed/` | **datasets elaborados** (entregable) — diccionario en su `README.md` |
| `data/ref/ocupaciones.csv` | ocupaciones, sector, saltos cortos y salto con formación (hecha a mano) |
