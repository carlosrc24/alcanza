"""Alcanza — el empleo que está a tu alcance.   streamlit run app/app.py"""
import copy
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
from src.config import PROCESSED, UMBRALES_T  # noqa: E402
from src.texto import interpretar  # noqa: E402

st.set_page_config(page_title="Alcanza", page_icon="🧭", layout="wide")

CSS = """
<style>
.block-container {padding-top: 1.6rem; max-width: 1400px;}
h1, h2, h3 {letter-spacing: -0.01em;}
.alc-hero {font-size: 2.0rem; font-weight: 700; margin: 0 0 .2rem 0;}
.alc-sub {color: #4b5563; margin-bottom: 1rem;}
.alc-card {border: 1px solid #e5e7eb; border-radius: 14px; padding: 16px 18px; background: #ffffff;
           height: 100%; box-shadow: 0 1px 2px rgba(0,0,0,.04);}
.alc-card .tipo {font-size: .75rem; font-weight: 700; letter-spacing: .08em; color: #0f766e; text-transform: uppercase;}
.alc-card.corto .tipo {color: #b45309;}
.alc-card.form .tipo {color: #6d28d9;}
.alc-card .titulo {font-size: 1.15rem; font-weight: 700; margin: 4px 0 2px 0; color: #111827;}
.alc-card .lugar {color: #374151; margin-bottom: 8px;}
.alc-card .chips span {display: inline-block; background: #f3f4f6; border-radius: 999px; padding: 2px 10px;
           margin: 2px 4px 2px 0; font-size: .82rem; color: #111827;}
.alc-card .porque {font-size: .9rem; color: #374151; margin-top: 8px;}
.alc-big {font-size: 2.2rem; font-weight: 700; color: #0f766e; line-height: 1.1;}
.alc-note {font-size: .8rem; color: #6b7280;}
.alc-est {font-size: .72rem; background: #fef3c7; color: #92400e; border-radius: 6px; padding: 1px 6px;}
@media (prefers-color-scheme: dark) {
  .alc-card {background: #111827; border-color: #374151;}
  .alc-card .titulo {color: #f9fafb;} .alc-card .lugar, .alc-card .porque {color: #d1d5db;}
  .alc-card .chips span {background: #1f2937; color: #e5e7eb;} .alc-sub {color: #9ca3af;}
}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)


# ------------------------------------------------------------------------------- datos
@st.cache_resource
def datos():
    D = R.cargar()
    D["geo"] = json.loads((PROCESSED / "municipios.geojson").read_text(encoding="utf-8"))
    D["fuentes"] = json.loads((PROCESSED / "fuentes.json").read_text(encoding="utf-8"))
    D["metodo_tp"] = D["tt"]["metodo_tp"].iloc[0]
    return D


D = datos()
NOM = {k: R.nombre_municipio(v) for k, v in D["nom"].items()}
INES = sorted(NOM, key=lambda k: NOM[k])
OCU = D["ocu"].set_index("id")


def fmt(x, dec=0):
    if x is None or (isinstance(x, float) and np.isnan(x)):
        return "—"
    return f"{x:,.{dec}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def rampa(v, lo, hi):
    """Verde azulado secuencial (claro → oscuro)."""
    a = np.array([204, 236, 230])
    b = np.array([1, 102, 94])
    f = 0 if hi <= lo else float(np.clip((v - lo) / (hi - lo), 0, 1))
    return [int(c) for c in a + (b - a) * f]


def mapa(features_props, puntos=None, centro=(40.42, -3.70), zoom=8.3, alto=520):
    geo = copy.deepcopy(D["geo"])
    for f in geo["features"]:
        f["properties"].update(features_props.get(f["properties"]["ine"], {}))
    capas = [pdk.Layer("GeoJsonLayer", geo, pickable=True, stroked=True, filled=True,
                       get_fill_color="properties.fill", get_line_color="properties.line",
                       get_line_width="properties.lw", line_width_units="pixels")]
    if puntos is not None and len(puntos):
        capas.append(pdk.Layer("ScatterplotLayer", puntos, get_position=["lon", "lat"], get_fill_color="color",
                               get_radius=170, radius_min_pixels=3, pickable=True))
    tooltip = {"html": "{tip}", "style": {"backgroundColor": "#111827", "color": "white", "fontSize": "13px"}}
    st.pydeck_chart(pdk.Deck(layers=capas, initial_view_state=pdk.ViewState(latitude=centro[0], longitude=centro[1],
                                                                           zoom=zoom),
                             map_style=pdk.map_styles.CARTO_LIGHT, tooltip=tooltip), height=alto)


# ------------------------------------------------------------------------------- navegación
st.sidebar.markdown("## 🧭 Alcanza")
st.sidebar.caption("El empleo que está a tu alcance")
vista = st.sidebar.radio("Vista", ["Busco empleo", "Orientación y planificación", "Datos y método"],
                         label_visibility="collapsed")
st.sidebar.markdown("---")
st.sidebar.caption(
    "MAD Open Data Challenge 2026 · Datos abiertos de la Comunidad de Madrid y del Consorcio Regional de "
    "Transportes. Prototipo: las cifras son estimaciones para orientar, no ofertas de empleo.")


# =============================================================================== CIUDADANÍA
def vista_ciudadania():
    st.markdown('<div class="alc-hero">¿Qué empleo tienes a tu alcance?</div>', unsafe_allow_html=True)
    st.markdown('<div class="alc-sub">Cuéntanos tu situación con tus palabras o rellena los campos. '
                'No guardamos nada.</div>', unsafe_allow_html=True)

    ss = st.session_state
    ss.setdefault("ocupacion", "aux_admin")
    ss.setdefault("ine", "28106")
    ss.setdefault("coche", False)
    ss.setdefault("hijo", True)
    ss.setdefault("formacion", True)
    ss.setdefault("T", 45)

    with st.expander("✍️ Escríbelo con tus palabras", expanded=False):
        txt = st.text_area("Tu situación", label_visibility="collapsed",
                           value="He trabajado 6 años de auxiliar administrativa. Vivo en Parla, no tengo coche y "
                                 "tengo un niño de 2 años. Si merece la pena, volvería a estudiar.")
        if st.button("Entender mi situación"):
            r = interpretar(txt, D["nom"])
            for k in ("ocupacion", "ine", "coche", "hijo", "formacion"):
                if r[k] is not None:
                    ss[k] = r[k]
            if r["T"]:
                ss["T"] = R.snap_T(r["T"])
            st.success("Esto es lo que hemos entendido. Revísalo abajo y corrige lo que haga falta.")

    c = st.columns([2.2, 2, 1, 1.1, 1.1])
    c[0].selectbox("Ocupación", list(OCU.index), key="ocupacion", format_func=lambda o: OCU.loc[o, "ocupacion"])
    c[1].selectbox("Vivo en", INES, key="ine", format_func=lambda k: NOM[k])
    c[2].toggle("Tengo coche", key="coche")
    c[3].toggle("Hijo/a de 0 a 3 años", key="hijo")
    c[4].toggle("Dispuesta/o a formarme", key="formacion")

    izq, der = st.columns([1, 2.6], gap="large")
    with izq:
        st.markdown("##### Ajusta a tu caso")
        T = st.select_slider("Tiempo máximo de viaje (solo ida)", options=UMBRALES_T, key="T",
                             format_func=lambda v: f"{v} min")
        st.caption("Importancia de cada criterio")
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

    with der:
        a, b, c2 = st.columns([1.3, 1, 1])
        a.markdown(f"Desde **{NOM[ss.ine]}**, {modo_txt}, en **{T} min**")
        a.markdown(f'<div class="alc-big">{fmt(ind["puestos_alcanzables"])}</div>'
                   f'puestos de tu sector ({directo.nombre_sector.split(" (")[0].lower()})', unsafe_allow_html=True)
        b.metric("Puestos por demandante", fmt(ind["puestos_por_competidor"], 1),
                 help="Método 2SFCA: puestos de cada destino repartidos entre los parados del sector que pueden "
                      "llegar a él, sumados sobre los destinos que tú alcanzas.")
        c2.metric("Frente a la media regional", f"×{fmt(ind['indice_relativo'], 2)}",
                  delta=f"{fmt(ind['var_interanual'] * 100, 1)} % empleo en un año"
                  if not pd.isna(ind["var_interanual"]) else None)

        # mapa: destinos alcanzables coloreados por puestos por demandante del destino
        t = R.tiempos_desde(D, ss.ine, res["modo"])
        dd = D["dest"][(D["dest"]["sector"] == directo.sector) & (D["dest"]["T"] == res["T"])].set_index("ine")
        alc = t[t <= T].index
        vals = dd.loc[dd.index.intersection(alc), "puestos_por_competidor_destino"]
        lo, hi = (vals.quantile(.1), vals.quantile(.9)) if len(vals) else (0, 1)
        top = set(directo.destinos["ine"]) if len(directo.destinos) else set()
        props = {}
        for ine in D["nom"]:
            m = t.get(ine, np.nan)
            r = dd.loc[ine] if ine in dd.index else None
            ok = ine in alc
            fill = rampa(r["puestos_por_competidor_destino"], lo, hi) + [200] if ok and r is not None else [229, 231, 235, 110]
            line = [17, 24, 39] if ine == ss.ine else ([234, 88, 12] if ine in top else [255, 255, 255])
            props[ine] = {"fill": fill, "line": line, "lw": 3 if (ine == ss.ine or ine in top) else 0.5,
                          "tip": f"<b>{NOM[ine]}</b><br>{fmt(m)} min {modo_txt}<br>"
                                 f"{fmt(r['puestos'] if r is not None else 0)} puestos del sector<br>"
                                 f"{fmt(r['puestos_por_competidor_destino'] if r is not None else 0, 2)} puestos por demandante"
                                 + ("" if ok else "<br><i>fuera de tu tiempo máximo</i>")}
        pts = []
        if ss.hijo:
            ei = D["rec"][(D["rec"]["tipo"] == "escuela_infantil") & D["rec"]["ine"].isin(set(top) | {ss.ine})].copy()
            ei["color"] = [[219, 39, 119, 200]] * len(ei)
            ei["tip"] = "👶 " + ei["nombre"] + "<br>" + ei["subtipo"] + " · " + ei["titularidad"]
            pts.append(ei)
        if ss.formacion and len(tarjetas) > 2:
            fp = tarjetas[2].centros_formacion.copy()
            if len(fp):
                fp["color"] = [[109, 40, 217, 230]] * len(fp)
                fp["tip"] = "🎓 " + fp["nombre"] + "<br>" + fp["subtipo"]
                pts.append(fp)
        puntos = pd.concat(pts)[["lon", "lat", "color", "tip"]] if pts else None
        o = D["mun"].set_index("ine").loc[ss.ine]
        mapa(props, puntos, centro=(o["lat"], o["lon"]), zoom=9.3 if T <= 45 else 8.6, alto=430)
        st.markdown('<span class="alc-note">Más oscuro = más puestos por demandante en ese municipio · '
                    'gris = fuera de tu tiempo · borde naranja = destinos recomendados'
                    + (' · rosa = escuelas infantiles' if ss.hijo else '')
                    + (' · morado = centros de formación' if ss.formacion else '') + '</span>',
                    unsafe_allow_html=True)

    st.markdown("### Tus tres caminos")
    cols = st.columns(3, gap="medium")
    estilos = {"directo": ("", "Trabajo directo"), "salto_corto": ("corto", "Salto corto"),
               "salto_formacion": ("form", "Salto con formación")}
    for col, tj in zip(cols, tarjetas):
        cls, nombre_tipo = estilos[tj.tipo]
        d0 = tj.destinos.iloc[0] if len(tj.destinos) else None
        lugar = f"{d0['nombre']} · {int(d0['minutos'])} min" if d0 is not None else "Sin destinos en ese tiempo"
        i = tj.indicadores
        sal = R.salario(D, OCU.loc[tj.ocupacion_id, "cno11"])
        chips = [f"{fmt(i['puestos_por_competidor'], 1)} puestos/demandante",
                 {"sube": "↑ sector crece", "baja": "↓ sector cae", "estable": "→ sector estable"}.get(i["tendencia"], ""),
                 f"~{fmt(sal / 1000, 1)} k€/año" if sal else ""]
        bloqueada = tj.tipo == "salto_formacion" and not ss.formacion
        with col:
            st.markdown(f"""<div class="alc-card {cls}" style="opacity:{.45 if bloqueada else 1}">
              <div class="tipo">{nombre_tipo} · {fmt(tj.puntuacion * 100)} / 100</div>
              <div class="titulo">{tj.ocupacion}</div>
              <div class="lugar">{lugar}</div>
              <div class="chips">{''.join(f'<span>{c}</span>' for c in chips if c)}</div>
              <div class="porque">{tj.por_que}</div></div>""", unsafe_allow_html=True)
            if bloqueada:
                st.caption("Activa «Dispuesta/o a formarme» para valorar este camino.")
            with st.expander("Por qué y cómo"):
                contrib = pd.DataFrame({"criterio": [R.ETIQUETAS[k] for k in tj.contribuciones],
                                        "aporte": [v * 100 for v in tj.contribuciones.values()]})
                st.bar_chart(contrib.set_index("criterio"), horizontal=True, height=210, color="#0f766e")
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

    st.markdown("")
    st.markdown(
        f'<span class="alc-note">No existen datos abiertos de ofertas de empleo: la demanda se aproxima con los '
        f'puestos existentes (afiliación por centro de trabajo, 31-12-{int(D["dest"]["T"].iloc[0] * 0 + 2025)}), '
        f'su tendencia y el paro registrado (31-03-2026). <span class="alc-est">estimado</span> el reparto del paro '
        f'de «Servicios» entre ramas de servicios. Tiempos: {D["metodo_tp"]}. Detalle en «Datos y método».</span>',
        unsafe_allow_html=True)


# =============================================================================== PLANIFICACIÓN
def accesibilidad(Mtp, Muser, P, U):
    D_ = U @ Mtp
    Rj = P / np.maximum(D_, 1.0)
    return Muser @ Rj


def vista_planificacion():
    st.markdown('<div class="alc-hero">Desiertos de empleo accesible</div>', unsafe_allow_html=True)
    st.markdown('<div class="alc-sub">Dónde vive la gente parada que tiene poco empleo a su alcance en transporte '
                'público. Para orientadores y para la Consejería.</div>', unsafe_allow_html=True)
    c = st.columns([2, 1, 1])
    sectores = list(D["sec"]["sector"])
    sec = c[0].selectbox("Sector", sectores[::-1] if sectores[-1] == "TOT" else sectores,
                         format_func=lambda s: D["nom_sec"][s])
    T = c[1].select_slider("Tiempo máximo", UMBRALES_T, value=45, format_func=lambda v: f"{v} min")
    capa = c[2].radio("Mapa", ["Accesibilidad", "Balance empleo/residentes"], horizontal=False)

    ind = D["ind"][(D["ind"]["sector"] == sec) & (D["ind"]["T"] == T) & (D["ind"]["modo"] == "tp")].set_index("ine")
    par = (D["par"].groupby("ine")["parados"].sum() if sec == "TOT"
           else D["par"][D["par"]["sector"] == sec].set_index("ine")["parados"])
    mun = D["mun"].set_index("ine")
    df = ind.join(par.rename("parados")).join(mun[["poblacion"]])
    df["tasa_paro_pob"] = df["parados"] / df["poblacion"]
    q_acc = df["indice_relativo"].quantile(1 / 3)
    q_par = df["tasa_paro_pob"].quantile(2 / 3)
    df["desierto"] = (df["indice_relativo"] <= q_acc) & (df["tasa_paro_pob"] >= q_par) & (df["parados"] >= 50)

    props = {}
    bal = D["bal"].set_index("ine")
    for ine in df.index:
        r = df.loc[ine]
        if capa == "Accesibilidad":
            fill = rampa(np.log(max(r["indice_relativo"], 0.01)), np.log(0.05), np.log(3)) + [210]
        else:
            b = bal.loc[ine, "balance"] if ine in bal.index else 0
            fill = ([180, 83, 9, 200] if b <= 0.6 else [15, 118, 110, 200] if b >= 1.1 else [209, 213, 219, 200])
        props[ine] = {"fill": fill, "line": [220, 38, 38] if r["desierto"] else [255, 255, 255],
                      "lw": 3 if r["desierto"] else 0.5,
                      "tip": f"<b>{NOM[ine]}</b><br>{fmt(r['puestos_por_competidor'], 1)} puestos por demandante "
                             f"(×{fmt(r['indice_relativo'], 2)} media)<br>{fmt(r['parados'])} parados del sector<br>"
                             f"Balance empleo/residentes: {fmt(bal.loc[ine, 'balance'] if ine in bal.index else np.nan, 2)}"
                             + ("<br><b style='color:#fca5a5'>Desierto de empleo accesible</b>" if r["desierto"] else "")}
    izq, der = st.columns([2.2, 1], gap="large")
    with izq:
        mapa(props, alto=560)
        st.markdown('<span class="alc-note">' + (
            "Más oscuro = más puestos por demandante en transporte público · borde rojo = desierto (tercio con "
            "menos acceso y tercio con más paro por habitante)" if capa == "Accesibilidad" else
            "Verde = polo de empleo (más puestos que residentes ocupados) · ocre = ciudad dormitorio (≤0,6) · "
            "borde rojo = desierto") + "</span>", unsafe_allow_html=True)
    with der:
        des = df[df["desierto"]].sort_values("parados", ascending=False)
        st.metric("Parados en desiertos de empleo accesible", fmt(des["parados"].sum()),
                  help="Parados del sector que viven en municipios del tercio con menor accesibilidad y del tercio "
                       "con más paro por habitante.")
        st.dataframe(des.assign(municipio=[NOM[i] for i in des.index])[
                         ["municipio", "parados", "indice_relativo"]].rename(columns={
                         "municipio": "Municipio", "parados": "Parados", "indice_relativo": "Acceso (×media)"}).round(2),
                     hide_index=True, height=300)

    st.markdown("### Simulador «¿y si…?»: mejorar el transporte")
    st.caption("Reduce el tiempo de viaje en transporte público entre un municipio y los demás (p. ej., más "
               "frecuencia o una línea directa) y mira cuánta gente parada gana acceso. Se recalcula el 2SFCA completo.")
    s1, s2, s3 = st.columns([2, 1, 1])
    ine_sim = s1.selectbox("Municipio que mejora su conexión", INES, index=INES.index("28106"),
                           format_func=lambda k: NOM[k])
    ahorro = s2.slider("Minutos que se ahorran", 0, 30, 10, step=5)
    destino_sim = s3.selectbox("Hacia", ["Todos los municipios", "Madrid"])

    ids = list(D["mun"]["ine"])
    tt = D["tt"].pivot(index="origen", columns="destino", values="min_tp").reindex(index=ids, columns=ids).to_numpy()
    tt2 = tt.copy()
    k = ids.index(ine_sim)
    cols_ = [ids.index("28079")] if destino_sim == "Madrid" else list(range(len(ids)))
    for j in cols_:
        if j != k:
            tt2[k, j] = max(tt[k, j] - ahorro, 5)
            tt2[j, k] = max(tt[j, k] - ahorro, 5)
    if sec == "TOT":
        P = D["dest"][(D["dest"]["sector"] == "TOT") & (D["dest"]["T"] == T)].set_index("ine")["puestos"].reindex(ids).fillna(0).to_numpy()
        U = D["par"].groupby("ine")["parados"].sum().reindex(ids).fillna(0).to_numpy()
    else:
        P = D["dest"][(D["dest"]["sector"] == sec) & (D["dest"]["T"] == T)].set_index("ine")["puestos"].reindex(ids).fillna(0).to_numpy()
        U = D["par"][D["par"]["sector"] == sec].set_index("ine")["parados"].reindex(ids).fillna(0).to_numpy()
    A0 = accesibilidad(tt <= T, tt <= T, P, U)
    A1 = accesibilidad(tt2 <= T, tt2 <= T, P, U)
    umbral = P.sum() / U.sum()
    gana = (A0 < umbral) & (A1 >= umbral)
    r1, r2, r3 = st.columns(3)
    r1.metric(f"Accesibilidad en {NOM[ine_sim]}", fmt(A1[k], 1), delta=f"{fmt((A1[k] / max(A0[k], 1e-9) - 1) * 100, 0)} %")
    r2.metric("Parados que pasan a superar la media regional", fmt(U[gana].sum()),
              help=f"Media regional: {fmt(umbral, 1)} puestos por parado en el sector.")
    r3.metric("Municipios que mejoran", int((A1 > A0 * 1.01).sum()))


# =============================================================================== DATOS
def vista_datos():
    st.markdown('<div class="alc-hero">Datos y método</div>', unsafe_allow_html=True)
    st.markdown("""
**Pregunta:** ¿cuánto empleo de mi sector puedo alcanzar en transporte público, y con cuánta gente compito por él?

**Indicador principal — puestos por demandante (2SFCA, Shen 1998).** Para cada municipio de destino *j*:
`R_j = puestos_j / Σ_k parados_k · [t_kj ≤ T]`; para cada municipio de origen *i*: `A_i = Σ_j R_j · [t_ij ≤ T]`.
Los parados compiten desplazándose en transporte público. *Índice relativo* = `A_i` dividido entre la media regional
(puestos del sector / parados del sector).

**Unidad territorial:** los 179 municipios; origen y destino = punto central de las paradas de transporte
del municipio. Dentro del propio municipio se supone un viaje de 10 min (simplificación declarada; afecta sobre todo a
Madrid capital).

**Tiempos:** r5py (motor R5) con los GTFS del Consorcio (Metro, Metro Ligero, EMT, interurbanos, urbanos) y de
Renfe Cercanías (el GTFS de Cercanías del Consorcio no trae horarios) sobre la red peatonal de OpenStreetMap.
Mediana de las salidas entre 7:00 y 9:00 de un martes laborable. Coche: distancia × 1,3 a 30–55 km/h (aproximado).

**Sectores:** el paro registrado por municipio solo distingue agricultura, industria, construcción y servicios.
Servicios se reparte entre tres ramas con la estructura de afiliados residentes del propio municipio
(*estimado*). Los parados sin empleo anterior se reparten entre sectores pro rata.

**Límites declarados:** no hay ofertas de empleo abiertas por municipio; la afiliación está redondeada a múltiplos
de 5; el salario es regional por gran grupo de ocupación (Encuesta de Estructura Salarial, cuatrienal); la tabla de
ocupaciones y sus saltos es una correspondencia hecha a mano.
""")
    st.markdown("#### Fuentes descargadas")
    f = pd.DataFrame(D["fuentes"])[["titulo", "descargado", "modificado_catalogo", "url"]]
    st.dataframe(f, hide_index=True, column_config={"url": st.column_config.LinkColumn("Enlace")})
    st.markdown("#### Datasets elaborados (descargables)")
    for p in sorted(PROCESSED.glob("*.csv")):
        st.download_button(f"⬇ {p.name}", p.read_bytes(), file_name=p.name, mime="text/csv", key=p.name)


{"Busco empleo": vista_ciudadania, "Orientación y planificación": vista_planificacion,
 "Datos y método": vista_datos}[vista]()
