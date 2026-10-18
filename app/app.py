"""Alcanza — el empleo que está a tu alcance.   streamlit run app/app.py"""
import copy
import html
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pydeck as pdk
import streamlit as st

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src import recomendador as R  # noqa: E402
from src import simulador as S  # noqa: E402
from src.config import PROCESSED, UMBRALES_T  # noqa: E402
from src.texto import interpretar  # noqa: E402

st.set_page_config(page_title="Alcanza · el empleo que está a tu alcance", page_icon="🧭", layout="wide")

# ------------------------------------------------------------------------------- estética
# Paleta: verde azulado (marca, accesibilidad), ámbar (salto corto), violeta (formación),
# rosa (escuelas infantiles), rojo (desiertos). Fondo cálido y tarjetas blancas.
CSS = """
<style>
:root {
  --ink: #14213d; --muted: #5b6577; --line: #e3e6de; --bg: #f6f7f3; --card: #ffffff;
  --teal: #0f766e; --teal-d: #0b4f4a; --teal-l: #e6f4f1; --amber: #c2410c; --amber-l: #fff4e6;
  --violet: #6d28d9; --violet-l: #f3efff; --rose: #db2777; --red: #dc2626; --red-l: #fef2f2;
  --serif: "Fraunces", Georgia, serif;
}
.block-container {padding-top: 1.2rem; padding-bottom: 3rem; max-width: 1380px;}
header[data-testid="stHeader"] {background: transparent;}
.stAppDeployButton, [data-testid="stStatusWidget"] {display: none;}

/* --- barra lateral --- */
.alc-brand {display: flex; align-items: center; gap: 12px; margin: 4px 0 18px 0;}
.alc-brand .nombre {font-family: var(--serif); font-size: 1.7rem; font-weight: 700; color: #fff; line-height: 1;}
.alc-brand .lema {font-size: .82rem; color: #a7d8cf; margin-top: 4px;}
section[data-testid="stSidebar"] div[role="radiogroup"] {gap: 4px;}
section[data-testid="stSidebar"] div[role="radiogroup"] label {
  padding: 9px 12px; border-radius: 12px; width: 100%; transition: background .15s;}
section[data-testid="stSidebar"] div[role="radiogroup"] label:hover {background: rgba(255,255,255,.06);}
section[data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked) {background: rgba(94,234,212,.14);}
.alc-side-note {font-size: .78rem; color: #a7c9c2; line-height: 1.45; border-top: 1px solid #1d5f58;
  padding-top: 14px; margin-top: 8px;}
.alc-side-note b {color: #e7f3ef;}
.alc-fuentes {display: flex; flex-wrap: wrap; gap: 6px; margin-top: 10px;}
.alc-fuentes span {font-size: .7rem; background: rgba(255,255,255,.08); color: #d5ece7; border-radius: 999px;
  padding: 2px 9px;}

/* --- cabecera de cada vista: anillos de isócrona como motivo --- */
.alc-hero {position: relative; overflow: hidden; border-radius: 22px; padding: 30px 34px 28px 34px;
  margin-bottom: 18px; color: #fff;
  background: linear-gradient(118deg, #0b4f4a 0%, #0f766e 55%, #14907f 100%);}
.alc-hero::after {content: ""; position: absolute; right: -90px; top: -120px; width: 460px; height: 460px;
  border-radius: 50%; opacity: .22;
  background: repeating-radial-gradient(circle, transparent 0 34px, rgba(255,255,255,.9) 35px 36px);}
.alc-hero::before {content: ""; position: absolute; right: 140px; top: 96px; width: 12px; height: 12px;
  border-radius: 50%; background: #fbbf24; box-shadow: 0 0 0 6px rgba(251,191,36,.25);}
.alc-hero .kicker {font-size: .75rem; letter-spacing: .14em; text-transform: uppercase; color: #a7f3d0;
  font-weight: 600;}
.alc-hero .titulo {font-family: var(--serif); font-size: 2.35rem; font-weight: 700; line-height: 1.1;
  margin: 6px 0 8px 0; max-width: 780px;}
.alc-hero .sub {font-size: 1.02rem; color: #d7f0ea; max-width: 720px;}

/* --- paneles --- */
div[class*="st-key-panel"] {background: var(--card); border: 1px solid var(--line); border-radius: 18px;
  padding: 18px 20px 8px 20px; box-shadow: 0 1px 2px rgba(20,33,61,.04), 0 8px 24px -18px rgba(20,33,61,.25);}
.alc-paso {display: flex; align-items: center; gap: 10px; margin: 0 0 10px 0;}
.alc-paso .n {width: 26px; height: 26px; border-radius: 50%; background: var(--teal); color: #fff;
  display: grid; place-items: center; font-size: .8rem; font-weight: 700; flex: none;}
.alc-paso .t {font-family: var(--serif); font-size: 1.22rem; font-weight: 600; color: var(--ink);}
.alc-paso .d {font-size: .85rem; color: var(--muted); margin-left: 4px;}

/* --- cifras clave --- */
.alc-stats {display: grid; grid-template-columns: 1.5fr 1fr 1fr 1fr; gap: 12px; margin-bottom: 12px;}
@media (max-width: 900px) {.alc-stats {grid-template-columns: 1fr 1fr;}}
.alc-stat {background: var(--card); border: 1px solid var(--line); border-radius: 16px; padding: 14px 16px;}
.alc-stat .lbl {font-size: .78rem; color: var(--muted); font-weight: 500;}
.alc-stat .val {font-size: 1.75rem; font-weight: 700; color: var(--ink); line-height: 1.15; margin-top: 4px;
  font-variant-numeric: tabular-nums;}
.alc-stat .sub {font-size: .8rem; color: var(--muted); margin-top: 2px;}
.alc-stat.main {background: linear-gradient(135deg, #e6f4f1, #f4fbf9); border-color: #cfe9e3;}
.alc-stat.main .val {font-size: 2.3rem; color: var(--teal-d);}
.alc-pill {display: inline-block; font-size: .74rem; font-weight: 600; border-radius: 999px; padding: 2px 9px;
  margin-top: 6px;}
.alc-pill.up {background: #dcfce7; color: #166534;} .alc-pill.down {background: #fee2e2; color: #991b1b;}
.alc-pill.flat {background: #eef1ec; color: #475569;}

/* --- avisos y leyendas --- */
.alc-aviso {display: flex; gap: 10px; align-items: flex-start; background: #fff8eb; border: 1px solid #fde3b0;
  color: #7c4a03; border-radius: 14px; padding: 10px 14px; font-size: .86rem; margin-bottom: 12px;}
.alc-leyenda {display: flex; flex-wrap: wrap; gap: 6px 14px; font-size: .78rem; color: var(--muted);
  margin: 8px 2px 0 2px;}
.alc-leyenda span {display: inline-flex; align-items: center; gap: 6px;}
.alc-leyenda i {display: inline-block; width: 14px; height: 10px; border-radius: 3px;}
.alc-leyenda i.borde {background: transparent !important; border: 2.5px solid; height: 10px;}
.alc-leyenda i.punto {width: 10px; height: 10px; border-radius: 50%;}
.alc-leyenda i.rampa {width: 46px; background: linear-gradient(90deg, #d5efe9, #0b4f4a);}
iframe, [data-testid="stDeckGlJsonChart"] {border-radius: 16px; overflow: hidden;}

/* --- tarjetas de caminos --- */
.alc-seccion {font-family: var(--serif); font-size: 1.6rem; font-weight: 700; color: var(--ink);
  margin: 26px 0 2px 0;}
.alc-seccion-sub {color: var(--muted); font-size: .92rem; margin-bottom: 14px;}
.alc-card {--c: var(--teal); --cl: var(--teal-l); position: relative; background: var(--card);
  border: 1px solid var(--line); border-radius: 18px; padding: 18px 18px 16px 18px; min-height: 270px;
  box-shadow: 0 1px 2px rgba(20,33,61,.04), 0 12px 28px -22px rgba(20,33,61,.35); overflow: hidden;}
.alc-card::before {content: ""; position: absolute; left: 0; top: 0; right: 0; height: 5px; background: var(--c);}
.alc-card.corto {--c: var(--amber); --cl: var(--amber-l);}
.alc-card.form {--c: var(--violet); --cl: var(--violet-l);}
.alc-card .top {display: flex; justify-content: space-between; gap: 12px; align-items: flex-start;}
.alc-card .tipo {display: inline-flex; align-items: center; gap: 6px; font-size: .72rem; font-weight: 700;
  letter-spacing: .1em; text-transform: uppercase; color: var(--c); background: var(--cl);
  border-radius: 999px; padding: 3px 10px;}
.alc-card .titulo {font-family: var(--serif); font-size: 1.32rem; font-weight: 600; line-height: 1.2;
  margin: 10px 0 4px 0; color: var(--ink);}
.alc-card .lugar {display: flex; align-items: center; gap: 6px; color: var(--muted); font-size: .9rem;}
.alc-card .chips {margin-top: 12px;}
.alc-card .chips span {display: inline-block; background: #f3f5f0; border-radius: 999px; padding: 3px 10px;
  margin: 0 5px 6px 0; font-size: .8rem; color: var(--ink); font-weight: 500;}
.alc-card .porque {font-size: .9rem; color: #334155; margin-top: 6px; line-height: 1.5;}
.alc-ring {width: 58px; height: 58px; border-radius: 50%; flex: none; display: grid; place-items: center;
  background: conic-gradient(var(--c) calc(var(--p) * 1%), #ebeee7 0);}
.alc-ring span {width: 46px; height: 46px; border-radius: 50%; background: #fff; display: grid;
  place-items: center; font-weight: 700; font-size: 1.05rem; color: var(--ink); line-height: 1;}
.alc-ring small {display: block; font-size: .55rem; color: var(--muted); font-weight: 500;}
.alc-card.bloqueada {opacity: .5; filter: grayscale(.6);}

/* --- pie --- */
.alc-pie {font-size: .8rem; color: var(--muted); border-top: 1px solid var(--line); margin-top: 28px;
  padding-top: 14px; line-height: 1.55;}
.alc-est {font-size: .7rem; background: #fef3c7; color: #92400e; border-radius: 6px; padding: 1px 6px;
  font-weight: 600;}

/* --- datos y método --- */
.alc-formula {background: #0e3b37; color: #e7f3ef; border-radius: 14px; padding: 14px 18px;
  font-family: ui-monospace, Consolas, monospace; font-size: .9rem; line-height: 1.7; margin: 8px 0 12px 0;}
.alc-formula b {color: #5eead4; font-weight: 600;}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

LOGO = """<svg viewBox="0 0 44 44" width="40" height="40" aria-hidden="true">
<circle cx="22" cy="22" r="19" fill="none" stroke="#5eead4" stroke-width="3" stroke-linecap="round"
 stroke-dasharray="88 32" transform="rotate(-50 22 22)"/>
<circle cx="22" cy="22" r="11" fill="none" stroke="#99f6e4" stroke-width="2.5" opacity=".65"/>
<circle cx="22" cy="22" r="4" fill="#fbbf24"/></svg>"""
PIN = ('<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" '
       'aria-hidden="true"><path d="M12 21s-7-6.2-7-11.5A7 7 0 0 1 19 9.5C19 14.8 12 21 12 21z"/>'
       '<circle cx="12" cy="9.5" r="2.5"/></svg>')


# ------------------------------------------------------------------------------- datos
@st.cache_resource
def datos(version: float):
    D = R.cargar()
    D["geo"] = json.loads((PROCESSED / "municipios.geojson").read_text(encoding="utf-8"))
    D["fuentes"] = json.loads((PROCESSED / "fuentes.json").read_text(encoding="utf-8"))
    tt = D["tt"]
    est = tt["metodo_tp"] == "estimado_hueco_gtfs"
    if (tt["metodo_tp"] == "plan_c_aproximado").all():
        D["metodo_tp"] = "APROXIMADOS por distancia (plan C, provisional)"
    else:
        D["metodo_tp"] = "horarios reales (GTFS) en hora punta, mediana de 7:00 a 9:00"
        if est.any():
            D["metodo_tp"] += (f"; el {est.mean() * 100:.0f} % de los pares, estimados por horarios incompletos "
                               f"en el GTFS de interurbanos")
    # proporción de tiempos estimados desde cada origen (hueco del GTFS de interurbanos)
    D["pct_est"] = est.groupby(tt["origen"]).mean()
    fh = PROCESSED / "huecos_gtfs.csv"
    D["hueco"] = (set(pd.read_csv(fh, dtype={"ine": str}).query("hueco_gtfs")["ine"]) if fh.exists() else set())
    return D


# la caché se invalida sola cuando se regeneran los ficheros de data/processed/
D = datos(max(p.stat().st_mtime for p in PROCESSED.glob("*.csv")))
NOM = {k: R.nombre_municipio(v) for k, v in D["nom"].items()}
INES = sorted(NOM, key=lambda k: NOM[k])
OCU = D["ocu"].set_index("id")


def fmt(x, dec=0):
    if x is None or (isinstance(x, float) and np.isnan(x)):
        return "—"
    return f"{x:,.{dec}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def e(x) -> str:
    return html.escape(str(x))


def rampa(v, lo, hi):
    """Verde azulado secuencial (claro → oscuro)."""
    a = np.array([213, 239, 233])
    b = np.array([11, 79, 74])
    f = 0 if hi <= lo else float(np.clip((v - lo) / (hi - lo), 0, 1))
    return [int(c) for c in a + (b - a) * f]


def hero(kicker, titulo, sub):
    st.markdown(f'<div class="alc-hero"><div class="kicker">{kicker}</div><div class="titulo">{titulo}</div>'
                f'<div class="sub">{sub}</div></div>', unsafe_allow_html=True)


def paso(n, titulo, detalle=""):
    st.markdown(f'<div class="alc-paso"><div class="n">{n}</div><div class="t">{titulo}</div>'
                f'<div class="d">{detalle}</div></div>', unsafe_allow_html=True)


def stat(lbl, val, sub="", pill=None, main=False, ayuda=""):
    p = f'<div class="alc-pill {pill[0]}">{pill[1]}</div>' if pill else ""
    return (f'<div class="alc-stat{" main" if main else ""}" title="{e(ayuda)}"><div class="lbl">{lbl}</div>'
            f'<div class="val">{val}</div>{f"<div class=sub>{sub}</div>" if sub else ""}{p}</div>')


def stats(*bloques, columnas=None):
    estilo = f' style="grid-template-columns:{columnas}"' if columnas else ""
    st.markdown(f'<div class="alc-stats"{estilo}>{"".join(bloques)}</div>', unsafe_allow_html=True)


def leyenda(items):
    """items: (tipo, color css, texto), tipo ∈ {relleno, borde, punto, rampa}."""
    partes = []
    for tipo, color, txt in items:
        cls = "" if tipo == "relleno" else tipo
        partes.append(f'<span><i class="{cls}" style="background:{color};border-color:{color}"></i>{txt}</span>')
    st.markdown(f'<div class="alc-leyenda">{"".join(partes)}</div>', unsafe_allow_html=True)


def mapa(features_props, puntos=None, centro=(40.42, -3.70), zoom=8.3, alto=520):
    geo = copy.deepcopy(D["geo"])
    for f in geo["features"]:
        f["properties"].update(features_props.get(f["properties"]["ine"], {}))
    capas = [pdk.Layer("GeoJsonLayer", geo, pickable=True, stroked=True, filled=True,
                       get_fill_color="properties.fill", get_line_color="properties.line",
                       get_line_width="properties.lw", line_width_units="'pixels'", line_width_min_pixels=0.5,
                       auto_highlight=True, highlight_color=[251, 191, 36, 90])]
    # bordes destacados encima, para que los polígonos vecinos no los tapen
    resaltados = [f for f in geo["features"] if f["properties"].get("lw", 0) >= 2]
    if resaltados:
        capas.append(pdk.Layer("GeoJsonLayer", {"type": "FeatureCollection", "features": resaltados},
                               stroked=True, filled=False, get_line_color="properties.line",
                               get_line_width=3, line_width_units="'pixels'", line_width_min_pixels=3))
    if puntos is not None and len(puntos):
        capas.append(pdk.Layer("ScatterplotLayer", puntos, get_position=["lon", "lat"], get_fill_color="color",
                               get_radius=170, radius_min_pixels=4, stroked=True, get_line_color=[255, 255, 255],
                               line_width_min_pixels=1.5, pickable=True))
    tooltip = {"html": "{tip}", "style": {"backgroundColor": "#14213d", "color": "white", "fontSize": "13px",
                                          "fontFamily": "Inter, sans-serif", "borderRadius": "10px",
                                          "padding": "8px 10px", "lineHeight": "1.45"}}
    st.pydeck_chart(pdk.Deck(layers=capas, initial_view_state=pdk.ViewState(latitude=centro[0], longitude=centro[1],
                                                                           zoom=zoom),
                             map_style=pdk.map_styles.CARTO_LIGHT, tooltip=tooltip), height=alto)


# ------------------------------------------------------------------------------- navegación
VISTAS = {"Busco empleo": ":material/work_outline:", "Orientación y planificación": ":material/map:",
          "Datos y método": ":material/dataset:"}
st.sidebar.markdown(f'<div class="alc-brand">{LOGO}<div><div class="nombre">Alcanza</div>'
                    f'<div class="lema">el empleo que está a tu alcance</div></div></div>', unsafe_allow_html=True)
vista = st.sidebar.radio("Vista", list(VISTAS), label_visibility="collapsed",
                         format_func=lambda v: f"{VISTAS[v]}  {v}")
st.sidebar.markdown(
    '<div class="alc-side-note"><b>MAD Open Data Challenge 2026.</b> Prototipo con datos abiertos de la '
    'Comunidad de Madrid y del Consorcio Regional de Transportes. Las cifras orientan: no son ofertas de empleo.'
    '<div class="alc-fuentes"><span>Afiliación SS</span><span>Paro registrado</span><span>GTFS Consorcio</span>'
    '<span>Renfe Cercanías</span><span>Centros educativos</span><span>Servicios sociales</span>'
    '<span>OpenStreetMap</span></div></div>', unsafe_allow_html=True)


# =============================================================================== CIUDADANÍA
def vista_ciudadania():
    hero("Para quien busca empleo", "¿Qué empleo tienes a tu alcance?",
         "Te decimos cuánto trabajo de lo tuyo puedes alcanzar de verdad en transporte público, con cuánta gente "
         "compites por él y qué caminos parecidos te abren más puertas. No guardamos nada.")

    ss = st.session_state
    ss.setdefault("ocupacion", "aux_admin")
    ss.setdefault("ine", "28106")
    ss.setdefault("coche", False)
    ss.setdefault("hijo", True)
    ss.setdefault("formacion", True)
    ss.setdefault("T", 45)

    with st.container(key="panel_situacion"):
        paso(1, "Tu situación", "cuéntalo con tus palabras o rellena los campos")
        with st.expander("Escríbelo con tus palabras", icon=":material/edit_note:", expanded=False):
            txt = st.text_area("Tu situación", label_visibility="collapsed",
                               value="He trabajado 6 años de auxiliar administrativa. Vivo en Parla, no tengo coche y "
                                     "tengo un niño de 2 años. Si merece la pena, volvería a estudiar.")
            if st.button("Entender mi situación", icon=":material/auto_awesome:", type="primary"):
                r = interpretar(txt, D["nom"])
                for k in ("ocupacion", "ine", "coche", "hijo", "formacion"):
                    if r[k] is not None:
                        ss[k] = r[k]
                if r["T"]:
                    ss["T"] = R.snap_T(r["T"])
                campos = {"ocupacion": "ocupación", "ine": "municipio", "coche": "coche", "hijo": "hijos",
                          "formacion": "formación", "T": "tiempo de viaje"}
                faltan = [v for k, v in campos.items() if r[k] is None]
                st.success("Esto es lo que hemos entendido. Revísalo abajo y corrige lo que haga falta."
                           + (f" No lo has mencionado o no lo hemos reconocido: {', '.join(faltan)}." if faltan else ""))

        c = st.columns([2, 1.7, 1, 1.25, 1.35], vertical_alignment="bottom")
        c[0].selectbox("Ocupación", list(OCU.index), key="ocupacion", format_func=lambda o: OCU.loc[o, "ocupacion"])
        c[1].selectbox("Vivo en", INES, key="ine", format_func=lambda k: NOM[k])
        c[2].toggle("Tengo coche", key="coche")
        c[3].toggle("Hijo/a de 0 a 3 años", key="hijo")
        c[4].toggle("Dispuesta/o a formarme", key="formacion")

    st.markdown("")
    izq, der = st.columns([1, 2.7], gap="large")
    with izq:
        with st.container(key="panel_ajustes"):
            paso(2, "Ajusta a tu caso")
            T = st.select_slider("Tiempo máximo de viaje (solo ida)", options=UMBRALES_T, key="T",
                                 format_func=lambda v: f"{v} min")
            st.caption("¿Qué te importa más?")
            pesos = {
                "competencia": st.slider("Poca competencia (puestos por demandante)", 0, 5, 3),
                "volumen": st.slider("Muchos puestos alcanzables", 0, 5, 2),
                "tendencia": st.slider("Sector que crece", 0, 5, 1),
                "salario": st.slider("Salario", 0, 5, 1),
                "conciliacion": st.slider("Conciliación (escuelas infantiles)", 0, 5, 2 if ss.hijo else 0,
                                          disabled=not ss.hijo),
                "esfuerzo": st.slider("Evitar formación larga", 0, 5, 1 if ss.formacion else 4),
            }

    res = R.recomendar(D, ss.ocupacion, ss.ine, coche=ss.coche, hijo=ss.hijo, formacion=ss.formacion,
                       T=T, pesos=pesos)
    tarjetas = res["tarjetas"]
    directo = tarjetas[0]
    ind = directo.indicadores
    modo_txt = "en coche" if ss.coche else "en transporte público"
    sector_txt = directo.nombre_sector.split(" (")[0].lower()

    with der:
        rel = ind["indice_relativo"]
        pill_rel = (("flat", "en la media") if 0.9 <= rel <= 1.1 else
                    ("up", f"{fmt(rel, 1)} veces la media") if rel > 1.1 else
                    ("down", f"{fmt((1 - rel) * 100)} % menos que la media"))
        v = ind["var_interanual"]
        stats(
            stat("Puestos de tu sector a tu alcance", fmt(ind["puestos_alcanzables"]),
                 f"{e(sector_txt.capitalize())}<br>desde {e(NOM[ss.ine])} · ≤ {T} min {modo_txt}", main=True),
            stat("Puestos por demandante", fmt(ind["puestos_por_competidor"], 1), "método 2SFCA",
                 ayuda="Puestos de cada destino repartidos entre los parados del sector que pueden llegar a él, "
                       "sumados sobre los destinos que tú alcanzas."),
            stat("Frente a la media regional", f"×{fmt(rel, 2)}", pill=pill_rel),
            stat("Variación en un año","—" if pd.isna(v) else f"{'+' if v >= 0 else '−'}{fmt(abs(v) * 100, 1)} %",
                 pill=None if pd.isna(v) else (("up", "sube") if v > 0.02 else ("down", "baja") if v < -0.02
                                                else ("flat", "estable"))),
        )
        p_est = D["pct_est"].get(ss.ine, 0)
        if not ss.coche and ss.ine in D["hueco"] and p_est > 0:
            st.markdown(f'<div class="alc-aviso"><span>⚠</span><div>El {fmt(p_est * 100)} % de los tiempos desde '
                        f'{e(NOM[ss.ine])} son estimados: el GTFS de autobuses del Consorcio está incompleto '
                        f'(«Datos parciales») en esta zona, así que los puestos a tu alcance pueden estar '
                        f'infravalorados.</div></div>', unsafe_allow_html=True)

        # mapa: destinos alcanzables coloreados por puestos por demandante del destino
        t = R.tiempos_desde(D, ss.ine, res["modo"])
        dd = D["dest"][(D["dest"]["sector"] == directo.sector) & (D["dest"]["T"] == res["T"])
                       & (D["dest"]["modo"] == res["modo"])].set_index("ine")
        alc = t[t <= T].index
        vals = dd.loc[dd.index.intersection(alc), "puestos_por_competidor_destino"]
        lo, hi = (vals.quantile(.1), vals.quantile(.9)) if len(vals) else (0, 1)
        top = set(directo.destinos["ine"]) if len(directo.destinos) else set()
        props = {}
        for ine in D["nom"]:
            m = t.get(ine, np.nan)
            r = dd.loc[ine] if ine in dd.index else None
            ok = ine in alc
            fill = rampa(r["puestos_por_competidor_destino"], lo, hi) + [215] if ok and r is not None \
                else [226, 228, 221, 120]
            line = [20, 33, 61] if ine == ss.ine else ([217, 119, 6] if ine in top else [255, 255, 255])
            props[ine] = {"fill": fill, "line": line, "lw": 3 if (ine == ss.ine or ine in top) else 0.5,
                          "tip": f"<b>{NOM[ine]}</b><br>{fmt(m)} min {modo_txt}<br>"
                                 f"{fmt(r['puestos'] if r is not None else 0)} puestos del sector<br>"
                                 f"{fmt(r['puestos_por_competidor_destino'] if r is not None else 0, 2)} puestos por demandante"
                                 + ("" if ok else "<br><i>fuera de tu tiempo máximo</i>")}
        pts = []
        if ss.hijo:
            ei = D["rec"][(D["rec"]["tipo"] == "escuela_infantil") & D["rec"]["ine"].isin(set(top) | {ss.ine})].copy()
            ei["color"] = [[219, 39, 119, 220]] * len(ei)
            ei["tip"] = "👶 " + ei["nombre"] + "<br>" + ei["subtipo"] + " · " + ei["titularidad"]
            pts.append(ei)
        if ss.formacion and len(tarjetas) > 2:
            fp = tarjetas[2].centros_formacion.copy()
            if len(fp):
                fp["color"] = [[109, 40, 217, 235]] * len(fp)
                fp["tip"] = "🎓 " + fp["nombre"] + "<br>" + fp["subtipo"]
                pts.append(fp)
        puntos = pd.concat(pts)[["lon", "lat", "color", "tip"]] if pts else None
        o = D["mun"].set_index("ine").loc[ss.ine]
        mapa(props, puntos, centro=(o["lat"], o["lon"]), zoom=9.3 if T <= 45 else 8.6, alto=440)
        leyenda([("rampa", "", "puestos por demandante en el destino"),
                 ("relleno", "#e2e4dd", "fuera de tu tiempo"),
                 ("borde", "#14213d", "donde vives"),
                 ("borde", "#d97706", "destinos recomendados")]
                + ([("punto", "#db2777", "escuelas infantiles")] if ss.hijo else [])
                + ([("punto", "#6d28d9", "centros de formación")] if ss.formacion else []))

    st.markdown('<div class="alc-seccion">Tus tres caminos</div>'
                '<div class="alc-seccion-sub">Ordenados con tus prioridades. Abre «Por qué y cómo» para ver de dónde '
                'sale cada puntuación y dónde buscar.</div>', unsafe_allow_html=True)
    cols = st.columns(3, gap="medium")
    estilos = {"directo": ("", "Trabajo directo", "◎"), "salto_corto": ("corto", "Salto corto", "↗"),
               "salto_formacion": ("form", "Salto con formación", "✦")}
    for col, tj in zip(cols, tarjetas):
        cls, nombre_tipo, icono = estilos[tj.tipo]
        d0 = tj.destinos.iloc[0] if len(tj.destinos) else None
        lugar = f"{e(d0['nombre'])} · {int(d0['minutos'])} min" if d0 is not None else "Sin destinos en ese tiempo"
        i = tj.indicadores
        sal = R.salario(D, OCU.loc[tj.ocupacion_id, "cno11"])
        chips = [f"{fmt(i['puestos_por_competidor'], 1)} puestos/demandante",
                 {"sube": "↑ sector crece", "baja": "↓ sector cae", "estable": "→ sector estable"}.get(i["tendencia"], ""),
                 f"~{fmt(sal / 1000, 1)} k€/año" if sal else ""]
        bloqueada = tj.tipo == "salto_formacion" and not ss.formacion
        punt = int(round(tj.puntuacion * 100))
        with col:
            st.markdown(f"""<div class="alc-card {cls}{' bloqueada' if bloqueada else ''}">
              <div class="top"><div><span class="tipo">{icono} {nombre_tipo}</span>
                <div class="titulo">{e(tj.ocupacion)}</div>
                <div class="lugar">{PIN}{lugar}</div></div>
                <div class="alc-ring" style="--p:{punt}" title="Puntuación con tus prioridades">
                  <span><div>{punt}<small>/100</small></div></span></div></div>
              <div class="chips">{''.join(f'<span>{c}</span>' for c in chips if c)}</div>
              <div class="porque">{e(tj.resumen)}</div></div>""", unsafe_allow_html=True)
            if bloqueada:
                st.caption("Activa «Dispuesta/o a formarme» para valorar este camino.")
            with st.expander("Por qué y cómo", icon=":material/insights:"):
                st.markdown(tj.por_que)
                contrib = pd.DataFrame({"criterio": [R.ETIQUETAS[k] for k in tj.contribuciones],
                                        "aporte": [v * 100 for v in tj.contribuciones.values()]})
                color = {"directo": "#0f766e", "salto_corto": "#c2410c", "salto_formacion": "#6d28d9"}[tj.tipo]
                st.bar_chart(contrib.set_index("criterio"), horizontal=True, height=210, color=color)
                st.caption("Cada barra es peso × indicador normalizado; la suma es la puntuación.")
                if len(tj.destinos):
                    st.markdown("**Dónde buscar**")
                    st.dataframe(tj.destinos.assign(
                        minutos=tj.destinos["minutos"].round(0).astype(int),
                        puestos=tj.destinos["puestos"].astype(int),
                        ratio=tj.destinos["puestos_por_competidor_destino"].round(2))[
                        ["nombre", "minutos", "puestos", "ratio", "ei"]].rename(columns={
                        "nombre": "Municipio", "minutos": "Min", "puestos": "Puestos del sector",
                        "ratio": "Puestos/demandante", "ei": "Esc. infantiles"}), hide_index=True)
                if tj.tipo == "salto_formacion":
                    st.markdown(f"**Fórmate:** {tj.formacion}")
                    if len(tj.centros_formacion):
                        st.dataframe(tj.centros_formacion.assign(minutos=tj.centros_formacion["minutos"].round(0))[
                            ["nombre", "subtipo", "municipio", "minutos"]].rename(columns={
                            "nombre": "Centro", "subtipo": "Tipo", "municipio": "Municipio", "minutos": "Min"}),
                            hide_index=True)
                if tj.tipo == "salto_corto" and len(res["alternativas_cortas"]) > 1:
                    otras = [a.ocupacion for a in res["alternativas_cortas"] if a.ocupacion_id != tj.ocupacion_id]
                    st.caption("Otros saltos cortos valorados: " + ", ".join(otras))

    st.markdown(
        f'<div class="alc-pie">No existen datos abiertos de ofertas de empleo: la demanda se aproxima con los '
        f'puestos existentes (afiliación por centro de trabajo, 31-12-{int(D["bal"]["anio_puestos"].iloc[0])}), '
        f'su tendencia y el paro registrado (31-03-{int(D["par"]["anio"].iloc[0])}). <span class="alc-est">estimado</span> '
        f'el reparto del paro de «Servicios» entre ramas de servicios. Tiempos: {D["metodo_tp"]}. Detalle en '
        f'«Datos y método».</div>', unsafe_allow_html=True)


# =============================================================================== PLANIFICACIÓN
@st.cache_data(show_spinner="Probando la mejora en los 179 municipios…")
def ranking_mejoras(sec, T, ahorro, solo_madrid):
    return S.ranking(D, sec, T, ahorro, solo_madrid, frozenset(D["hueco"]))


def vista_planificacion():
    hero("Para orientadores y la Consejería", "Desiertos de empleo accesible",
         "Dónde vive la gente parada que tiene poco empleo a su alcance en transporte público, y cuánto cambiaría "
         "con una mejor conexión.")
    with st.container(key="panel_filtros"):
        c = st.columns([2, 1.4, 1.4], vertical_alignment="center")
        sectores = list(D["sec"]["sector"])
        sec = c[0].selectbox("Sector", sectores[::-1] if sectores[-1] == "TOT" else sectores,
                             format_func=lambda s: D["nom_sec"][s])
        T = c[1].select_slider("Tiempo máximo", UMBRALES_T, value=45, format_func=lambda v: f"{v} min")
        capa = c[2].radio("Mapa", ["Accesibilidad", "Balance empleo/residentes"], horizontal=True)

    ind = D["ind"][(D["ind"]["sector"] == sec) & (D["ind"]["T"] == T) & (D["ind"]["modo"] == "tp")].set_index("ine")
    par = (D["par"].groupby("ine")["parados"].sum() if sec == "TOT"
           else D["par"][D["par"]["sector"] == sec].set_index("ine")["parados"])
    mun = D["mun"].set_index("ine")
    df = ind.join(par.rename("parados")).join(mun[["poblacion"]])
    df["tasa_paro_pob"] = df["parados"] / df["poblacion"]
    q_acc = df["indice_relativo"].quantile(1 / 3)
    q_par = df["tasa_paro_pob"].quantile(2 / 3)
    df["desierto"] = (df["indice_relativo"] <= q_acc) & (df["tasa_paro_pob"] >= q_par) & (df["parados"] >= 50)
    # sin horarios fiables en la fuente no se clasifica (su acceso sale infravalorado)
    df["desierto"] &= ~df.index.isin(D["hueco"])

    props = {}
    bal = D["bal"].set_index("ine")
    for ine in df.index:
        r = df.loc[ine]
        if capa == "Accesibilidad":
            fill = rampa(np.log(max(r["indice_relativo"], 0.01)), np.log(0.05), np.log(3)) + [215]
        else:
            b = bal.loc[ine, "balance"] if ine in bal.index else 0
            fill = ([217, 119, 6, 190] if b <= 0.6 else [15, 118, 110, 200] if b >= 1.1 else [214, 218, 208, 200])
        hueco = ine in D["hueco"]
        props[ine] = {"fill": fill,
                      "line": [220, 38, 38] if r["desierto"] else [124, 58, 237] if hueco else [255, 255, 255],
                      "lw": 3 if r["desierto"] else 2 if hueco else 0.5,
                      "tip": f"<b>{NOM[ine]}</b><br>{fmt(r['puestos_por_competidor'], 1)} puestos por demandante "
                             f"(×{fmt(r['indice_relativo'], 2)} media)<br>{fmt(r['parados'])} parados del sector<br>"
                             f"Balance empleo/residentes: {fmt(bal.loc[ine, 'balance'] if ine in bal.index else np.nan, 2)}"
                             + ("<br><b style='color:#fca5a5'>Desierto de empleo accesible</b>" if r["desierto"] else "")
                             + ("<br><i>Tiempos estimados: horarios de autobús incompletos en la fuente</i>"
                                if hueco else "")}
    des = df[df["desierto"]].sort_values("parados", ascending=False)
    st.markdown("")
    stats(
        stat("Parados en desiertos de empleo accesible", fmt(des["parados"].sum()),
             f"{fmt(des['parados'].sum() / max(df['parados'].sum(), 1) * 100, 1)} % de los parados del sector",
             main=True, ayuda="Parados del sector que viven en municipios del tercio con menor accesibilidad y del "
                              "tercio con más paro por habitante."),
        stat("Municipios desierto", fmt(len(des)), f"de {len(df)} municipios"),
        stat("Sin clasificar", fmt(len(D["hueco"])), "horarios de autobús incompletos en la fuente"),
        stat("Media regional", fmt(D["dest"].query("sector == @sec and T == @T and modo == 'tp'")["puestos"].sum()
                                   / max(df["parados"].sum(), 1), 1), "puestos por parado del sector"),
    )
    izq, der = st.columns([2.2, 1], gap="large")
    with izq:
        mapa(props, alto=560)
        leyenda(([("rampa", "", "más oscuro = más puestos por demandante")] if capa == "Accesibilidad" else
                 [("relleno", "#0f766e", "polo de empleo (≥ 1,1)"), ("relleno", "#d97706", "ciudad dormitorio (≤ 0,6)"),
                  ("relleno", "#d6dad0", "equilibrado")])
                + [("borde", "#dc2626", "desierto: tercio con menos acceso y tercio con más paro por habitante"),
                   ("borde", "#7c3aed", "sin clasificar: horarios de autobús incompletos")])
    with der:
        st.markdown('<div class="alc-paso"><div class="t">Dónde actuar primero</div></div>', unsafe_allow_html=True)
        st.dataframe(des.assign(municipio=[NOM[i] for i in des.index], parados=des["parados"].round(0).astype(int))[
                         ["municipio", "parados", "indice_relativo"]].rename(columns={
                         "municipio": "Municipio", "parados": "Parados", "indice_relativo": "Acceso"}),
                     hide_index=True, height=500, column_config={
                         "Municipio": st.column_config.TextColumn(width="medium"),
                         "Acceso": st.column_config.ProgressColumn(format="×%.2f", min_value=0, max_value=1,
                                                                   help="Puestos por demandante frente a la media regional"),
                         "Parados": st.column_config.NumberColumn(format="%d")})

    st.markdown("")
    with st.container(key="panel_simulador"):
        paso("?", "Simulador «¿y si…?»: mejorar el transporte",
             "más frecuencia o una línea directa; se recalcula el 2SFCA completo")
        s1, s2, s3 = st.columns([2, 1, 1])
        ine_sim = s1.selectbox("Municipio que mejora su conexión", INES, index=INES.index("28106"),
                               format_func=lambda k: NOM[k])
        ahorro = s2.slider("Minutos que se ahorran", 0, 30, 10, step=5)
        destino_sim = s3.selectbox("Hacia", ["Todos los municipios", "Madrid"])

        solo_madrid = destino_sim == "Madrid"
        ids, tt, P, U, pob = S.datos_sector(D, sec, T)
        k = ids.index(ine_sim)
        media = P.sum() / max(U.sum(), 1)
        excl = np.isin(ids, list(D["hueco"]))
        A0 = S.accesibilidad(tt <= T, P, U)
        A1 = S.accesibilidad(S.mejorar(tt, ids, ine_sim, ahorro, solo_madrid) <= T, P, U)
        des0, umbrales = S.desiertos(A0 / media, U, pob, excl)
        des1, _ = S.desiertos(A1 / media, U, pob, excl, umbrales)
        cambio = (A1[k] / max(A0[k], 1e-9) - 1) * 100
        stats(
            stat(f"Acceso en {e(NOM[ine_sim])}", f"×{fmt(A1[k] / media, 2)}",
                 f"antes ×{fmt(A0[k] / media, 2)} la media regional",
                 pill=("up", f"+{fmt(cambio)} %") if cambio > 0.5 else ("down", f"{fmt(cambio)} %") if cambio < -0.5
                 else ("flat", "sin cambio"), main=True),
            stat("Parados que salen de un desierto", fmt(U[des0 & ~des1].sum()),
                 f"y {fmt(U[~des0 & des1].sum())} que entran"),
            stat("Municipios que mejoran su acceso", fmt(int((A1 > A0 * 1.01).sum())), "más de un 1 %"),
            columnas="1.4fr 1fr 1fr")
        if cambio < -0.5:
            st.caption("El acceso relativo puede bajar: al conectarse mejor también llega a destinos con mucha más "
                       "competencia (p. ej., Madrid). El indicador mide puestos por demandante, no volumen.")

        st.markdown('<div class="alc-paso" style="margin-top:18px"><div class="t">¿Dónde rinde más esta mejora?'
                    '</div><div class="d">la misma mejora aplicada a cada municipio, uno a uno</div></div>',
                    unsafe_allow_html=True)
        rk = ranking_mejoras(sec, T, ahorro, solo_madrid)
        top = rk.head(10)
        st.dataframe(pd.DataFrame({
            "Municipio": top["municipio"],
            "Parados que salen de desiertos": top["salen_neto"].round(0).astype(int),
            "Parados del municipio": top["parados"].round(0).astype(int),
            "Acceso antes": top["acceso_antes"], "Acceso después": top["acceso_despues"],
            "Puestos alcanzables +": (top["puestos_alcanzables_despues"] - top["puestos_alcanzables_antes"]).astype(int),
        }), hide_index=True, use_container_width=True, column_config={
            "Acceso antes": st.column_config.NumberColumn(format="×%.2f"),
            "Acceso después": st.column_config.NumberColumn(format="×%.2f"),
            "Puestos alcanzables +": st.column_config.NumberColumn(format="+%d")})
        st.caption(f"Ordenado por parados (de toda la región) que dejan de vivir en un desierto de empleo accesible; "
                   f"a igualdad, por la ganancia de acceso de los parados del propio municipio. El 2SFCA reparte: lo "
                   f"que gana un municipio lo pierde en parte la competencia en otros, por eso no se suma el acceso. "
                   f"Se excluyen Madrid capital y los {len(D['hueco'])} municipios con horarios incompletos.")


# =============================================================================== DATOS
def vista_validacion():
    fv = PROCESSED / "validacion.json"
    if not fv.exists():
        st.info("Ejecuta `python -m src.validacion` para generar la validación.")
        return
    V = json.loads(fv.read_text(encoding="utf-8"))
    vt = V["tiempos_vs_edm2018"]
    st.markdown("**¿Los tiempos se parecen a los viajes reales?** Comparamos los tiempos calculados con los viajes "
                "casa → trabajo en transporte público que declararon los encuestados de la **Encuesta Domiciliaria "
                "de Movilidad 2018** (catálogo de la Comunidad de Madrid), saliendo entre las 6:00 y las 10:00.")
    if vt.get("pares", 0) == 0:
        st.info("Los tiempos actuales son del plan C: no hay tiempos de horarios reales que validar.")
        return
    stats(
        stat("Diferencia mediana", f"{fmt(vt['sesgo_mediano_min'], 1)} min", "calculado − declarado", main=True,
             pill=("up", "sin sesgo apreciable") if abs(vt["sesgo_mediano_min"]) <= 5 else ("down", "sesgo")),
        stat("Pares dentro de ±15 min", f"{fmt(vt['pct_dentro_15min'] * 100)} %",
             f"{fmt(vt['pct_dentro_15min_sin_madrid'] * 100)} % sin contar Madrid capital"),
        stat("Error medio", f"{fmt(vt['error_medio_abs_min'], 1)} min", "absoluto"),
        stat("Base de la comparación", fmt(vt["pares"]), f"pares de municipios · {fmt(vt['viajes'])} viajes"))
    pares = pd.read_csv(PROCESSED / "validacion_tiempos_edm.csv", dtype={"origen": str, "destino": str})
    pares = pares[pares["metodo_tp"] == "r5py_gtfs_osm_p50_7a9h"].assign(
        par=lambda d: d["nombre_origen"] + " → " + d["nombre_destino"],
        tipo=lambda d: np.where(d["con_madrid"], "con Madrid capital", "entre otros municipios"))
    import altair as alt
    base = alt.Chart(pares)
    lim = [0, max(pares["min_edm"].max(), pares["min_tp"].max()) + 5]
    diag = alt.Chart(pd.DataFrame({"x": lim, "y": lim})).mark_line(color="#94a3b8", strokeDash=[5, 4]).encode(
        x="x", y="y")
    banda = alt.Chart(pd.DataFrame({"x": lim, "lo": [v - 15 for v in lim], "hi": [v + 15 for v in lim]})).mark_area(
        opacity=.12, color="#0f766e").encode(x="x", y="lo", y2="hi")
    puntos = base.mark_circle(opacity=.8, stroke="white", strokeWidth=.6).encode(
        x=alt.X("min_edm:Q", title="Minutos declarados en la EDM 2018 (mediana ponderada)", scale=alt.Scale(domain=lim)),
        y=alt.Y("min_tp:Q", title="Minutos calculados (r5py, horarios 2026)", scale=alt.Scale(domain=lim)),
        size=alt.Size("viajes_edm:Q", title="Viajes", scale=alt.Scale(range=[30, 500])),
        color=alt.Color("tipo:N", title=None, scale=alt.Scale(range=["#d97706", "#0f766e"]),
                        legend=alt.Legend(orient="top")),
        tooltip=[alt.Tooltip("par:N", title="Par"), alt.Tooltip("min_edm:Q", title="EDM"),
                 alt.Tooltip("min_tp:Q", title="Calculado"), alt.Tooltip("viajes_edm:Q", title="Viajes")])
    st.altair_chart((banda + diag + puntos).properties(height=420), use_container_width=True)
    st.caption("Línea discontinua: coincidencia exacta; banda: ±15 min. Diferencias esperables: la encuesta es de 2018 "
               "y declara horas redondeadas, y mide de puerta a puerta desde cualquier punto del municipio, mientras que "
               "el modelo va de núcleo a núcleo. Los mayores errores son viajes a Madrid capital desde municipios lejanos "
               "a su centro (p. ej., Alcalá de Henares): es el efecto de tratar Madrid como un solo destino.")

    st.markdown("**¿El indicador se relaciona con el paro?** Correlación de Spearman entre el acceso al empleo y la "
                "tasa de paro (parados / población) en los municipios de 2.000 habitantes o más con horarios completos.")
    vi = V["indicador_vs_tasa_paro"]
    st.dataframe(pd.DataFrame([{"Tiempo máximo": f"{T} min", "Municipios": d["municipios"],
                                "Puestos por demandante ↔ paro": d["spearman_indice_paro"],
                                "Puestos alcanzables ↔ paro": d["spearman_puestos_paro"]} for T, d in vi.items()]),
                 hide_index=True, use_container_width=True)
    st.caption("Negativo = donde hay menos empleo a tu alcance hay más paro. Con los puestos por demandante la relación es "
               "en parte mecánica (los parados del municipio cuentan como competidores); con los puestos alcanzables, que "
               "no usan el paro, se mantiene. Es una asociación, no una prueba de causalidad.")

    vr = V["robustez"]
    st.markdown(f"**¿Depende del corte duro en T?** Comparamos el índice con umbral (t ≤ {vr['T_referencia']} min) con "
                f"un 2SFCA de decaimiento gaussiano, en el que los destinos más lejanos pesan menos.")
    st.dataframe(pd.DataFrame([{"Variante": k.replace("gaussiano_d0_", "Gaussiano, d₀ = ") + " min",
                                "Spearman con el índice de la app": v}
                               for k, v in vr["spearman_umbral_vs_decaimiento"].items()]),
                 hide_index=True, use_container_width=True)
    st.caption("Con un alcance comparable (d₀ = 60 min) la ordenación de municipios se mantiene en lo esencial.")


def vista_datos():
    hero("Transparencia", "Datos y método",
         "Cada cifra de Alcanza se puede rastrear hasta su fuente abierta y su fecha. Aquí está cómo se calcula "
         "y qué límites tiene.")
    tab_m, tab_v, tab_f, tab_d = st.tabs([":material/function: Método", ":material/verified: Validación",
                                          ":material/source: Fuentes", ":material/download: Datasets elaborados"])
    with tab_v:
        vista_validacion()
    with tab_m:
        st.markdown("**Pregunta:** ¿cuánto empleo de mi sector puedo alcanzar en transporte público, y con cuánta "
                    "gente compito por él?")
        st.markdown("**Indicador principal — puestos por demandante (2SFCA, Shen 1998).**")
        st.markdown('<div class="alc-formula"><b>1.</b> para cada destino j: &nbsp;R<sub>j</sub> = puestos<sub>j</sub> '
                    '/ Σ<sub>k</sub> parados<sub>k</sub> · [t<sub>kj</sub> ≤ T]<br><b>2.</b> para cada origen i: '
                    '&nbsp;A<sub>i</sub> = Σ<sub>j</sub> R<sub>j</sub> · [t<sub>ij</sub> ≤ T]</div>',
                    unsafe_allow_html=True)
        st.markdown("""
Cada modo tiene su propio cálculo: en transporte público se compite con parados que se mueven en transporte
público; con coche, con parados que también tienen coche. *Índice relativo* = `A_i` dividido entre la ratio regional
(puestos del sector / parados del sector); su media ponderada por parados es exactamente 1 (comprobado).

**Unidad territorial:** los 179 municipios; origen y destino = punto central de las paradas de transporte
del municipio. Dentro del propio municipio se supone un viaje de 10 min (simplificación declarada; afecta sobre todo a
Madrid capital).

**Tiempos en transporte público (versión actual: {metodo}).** Plan A: r5py (motor R5) con los GTFS del
Consorcio (Metro, Metro Ligero, EMT, interurbanos, urbanos) y de Renfe Cercanías (el GTFS de Cercanías del
Consorcio no trae horarios) sobre la red peatonal de OpenStreetMap; mediana de las salidas entre 7:00 y 9:00 de un
martes laborable. Plan C (respaldo): 15 min de acceso y espera + distancia × 1,3 a 25 km/h. Coche: distancia × 1,3
a 30–55 km/h + 5 min (aproximado).

**Hueco en la fuente de autobuses interurbanos.** El Consorcio publica el GTFS de interurbanos como «Datos
parciales»: 13 líneas no traen viajes (entre ellas la concesión de Colmenar Viejo, 720–728) y 48 traen horarios de
relleno (todas las paradas a las 02:00). En los municipios donde al menos el 65 % de las paradas de autobús no tienen
horario utilizable (Sierra Norte, Colmenar Viejo, Las Vegas…, borde morado en el mapa), el tiempo de cada par es el
menor entre r5py y una estimación: mediana condicionada al tiempo en coche, ajustada sobre los pares bien cubiertos
por tipo de par (con Madrid, con ferrocarril o solo autobús; error absoluto mediano 11–19 min). La estimación
solo añade destinos a partir de unos 75–90 min, así que para estos municipios el acceso es una **cota inferior**: no se
clasifican como desiertos y la app lo avisa. Esos pares figuran como `estimado_hueco_gtfs` en `tiempos_tp.csv`.

**Madrid capital es un solo destino** situado en su núcleo (mediana de sus paradas). Al subir el tiempo máximo por
encima del que se tarda en llegar a él, se suman de golpe unos 2,9 millones de puestos: es un salto real del modelo
municipal, no un error. Desagregar Madrid por distritos queda como mejora futura.

**Sectores:** el paro registrado por municipio solo distingue agricultura, industria, construcción y servicios.
Servicios se reparte entre tres ramas con la estructura de afiliados residentes del propio municipio
(*estimado*). Los parados sin empleo anterior se reparten entre sectores pro rata.

**Límites declarados:** no hay ofertas de empleo abiertas por municipio; la afiliación está redondeada a múltiplos
de 5; el salario es regional por gran grupo de ocupación (Encuesta de Estructura Salarial, cuatrienal); la tabla de
ocupaciones y sus saltos es una correspondencia hecha a mano.
""".replace("{metodo}", D["metodo_tp"]))
    with tab_f:
        f = pd.DataFrame(D["fuentes"])[["titulo", "descargado", "modificado_catalogo", "url"]]
        st.dataframe(f, hide_index=True, use_container_width=True, column_config={
            "titulo": "Conjunto de datos", "descargado": "Descargado", "modificado_catalogo": "Modificado en catálogo",
            "url": st.column_config.LinkColumn("Enlace")})
    with tab_d:
        st.caption("CSV en UTF-8 con separador «,». Diccionario de datos completo en `data/processed/README.md`.")
        ficheros = sorted(PROCESSED.glob("*.csv"))
        cols = st.columns(3)
        for n, p in enumerate(ficheros):
            cols[n % 3].download_button(f"{p.name}", p.read_bytes(), file_name=p.name, mime="text/csv", key=p.name,
                                        icon=":material/download:", use_container_width=True)


{"Busco empleo": vista_ciudadania, "Orientación y planificación": vista_planificacion,
 "Datos y método": vista_datos}[vista]()
