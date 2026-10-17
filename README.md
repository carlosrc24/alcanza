# Alcanza — el empleo que está a tu alcance

Prototipo para el MAD Open Data Challenge 2026 (Comunidad de Madrid · UC3M).
Equipo: Carlos Rodríguez Caparrós, Ana Denis Rubio, Jiaxing Zhu, Pedro González Carnero.

- `docs/` — propuesta aceptada (aproximación técnica, fuentes, interfaz)
- `src/` — pipeline de datos (descarga → limpieza → indicadores)
- `data/raw/` — descargas originales (no se suben a git)
- `data/processed/` — **datasets elaborados** (entregable), con diccionario en su README
- `app/` — prototipo (Streamlit)

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m src.pipeline          # genera data/processed/
streamlit run app/app.py        # abre el prototipo
```
