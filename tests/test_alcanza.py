"""Pruebas de humo y de coherencia:  python -m pytest -q tests"""
import itertools

import numpy as np
import pandas as pd
import pytest

from src import recomendador as R
from src.config import PROCESSED, UMBRALES_T
from src.texto import interpretar


@pytest.fixture(scope="module")
def D():
    return R.cargar()


def test_179_municipios(D):
    assert len(D["mun"]) == 179 and D["mun"]["ine"].is_unique
    assert D["mun"]["ine"].str.match(r"^28\d{3}$").all()


def test_matriz_completa(D):
    assert len(D["tt"]) == 179 * 179
    assert D["tt"][["min_tp", "min_coche"]].notna().all().all()


def test_conservacion_2sfca(D):
    """Σ_i A_i·parados_i = Σ_j puestos_j de los destinos a los que llega algún parado
    (propiedad de conservación del 2SFCA)."""
    par = D["par"]
    dest = D["dest"].set_index(["sector", "T", "modo"])
    for (s, T, modo), g in D["ind"].groupby(["sector", "T", "modo"]):
        u = (par.groupby("ine")["parados"].sum() if s == "TOT"
             else par[par["sector"] == s].set_index("ine")["parados"])
        lhs = g.set_index("ine")["puestos_por_competidor"].mul(u, fill_value=0).sum()
        d = dest.loc[(s, T, modo)]
        rhs = d.loc[d["competidores_que_llegan"] >= 1, "puestos"].sum()
        assert lhs == pytest.approx(rhs, rel=0.01), (s, T, modo)


def test_monotono_en_T(D):
    x = D["ind"].sort_values("T").groupby(["ine", "sector", "modo"])["puestos_alcanzables"]
    assert x.apply(lambda v: (v.diff().dropna() >= -1).all()).all()


def test_recomendador_todos_los_casos(D):
    ocus = list(D["ocu"]["id"])
    ines = list(D["mun"]["ine"])
    for oid, ine in itertools.product(ocus, ines[::7] + ["28106", "28079"]):
        for T, coche, hijo in itertools.product(UMBRALES_T[::2], (False, True), (False, True)):
            r = R.recomendar(D, oid, ine, coche=coche, hijo=hijo, T=T)
            assert 2 <= len(r["tarjetas"]) <= 3
            for t in r["tarjetas"]:
                assert 0 <= t.puntuacion <= 1 and t.resumen and t.por_que
                assert sum(t.contribuciones.values()) == pytest.approx(t.puntuacion)


def test_ocupaciones_referencias_validas(D):
    ocu = D["ocu"].set_index("id")
    for oid, r in ocu.iterrows():
        assert r["sector"] in D["nom_sec"]
        for o in r["saltos_cortos"].split("|"):
            assert o in ocu.index and o != oid, (oid, o)
        assert r["salto_formacion"] in ocu.index


def test_caso_lucia(D):
    m = D["nom"]
    r = interpretar("He trabajado 6 años de auxiliar administrativa. Vivo en Parla, no tengo coche y tengo "
                    "un niño de 2 años. Si merece la pena, volvería a estudiar.", m)
    assert r == {"ocupacion": "aux_admin", "ine": "28106", "coche": False, "hijo": True,
                 "formacion": True, "T": None, "cp": None}
    res = R.recomendar(D, "aux_admin", "28106", hijo=True, T=45)
    assert [t.tipo for t in res["tarjetas"]] == ["directo", "salto_corto", "salto_formacion"]


def test_texto_libre(D):
    from src.texto import interpretar
    casos = [
        ("Vivo en Alcalá de Henares, era dependienta. Máximo media hora.", "28005", "dependiente", None, None, 30),
        ("conductor de reparto, vivo en torrejon, tengo furgoneta", "28148", "conductor", True, None, None),
        ("Teleoperadora en Valdemoro, dos hijos de 5 y 8 años", "28161", "teleoperador", None, False, None),
        ("vivo en sanse, soy cocinera, tengo un bebé de 10 meses, hora y media", "28134", "cocinero_prof", None, True, 90),
        ("Soy de Rivas, vigilante de seguridad, no conduzco, mi hija tiene tres años", "28123", "vigilante",
         False, True, None),
        ("mozo de almacén en coslada, coche propio, 40 min", "28049", "mozo_almacen", True, None, 40),
    ]
    for texto, ine, ocu, coche, hijo, T in casos:
        r = interpretar(texto, D["nom"])
        assert (r["ine"], r["ocupacion"], r["coche"], r["hijo"], r["T"]) == (ine, ocu, coche, hijo, T), texto


def test_barrios_de_madrid(D):
    """Los barrios con ejemplo por código postal se reconocen y fijan Madrid capital."""
    from src.texto import interpretar
    casos = [("Vivo en Chamberí, soy camarero", "28010"), ("vivo en Villa de Vallecas", "28031"),
             ("soy de Vallecas, sin coche", "28018"), ("vivo en Argüelles", "28008"), ("vivo en el 28013", "28013"),
             ("operario en Parla, quiero un centro de formación", None)]
    for texto, cp in casos:
        r = interpretar(texto, D["nom"])
        assert r["cp"] == cp, texto
        if cp:
            assert r["ine"] == "28079", texto


def test_negaciones_de_los_ejemplos_de_la_demo(D):
    """Plan B sin IA: «No volvería a estudiar» y «ni hijos» se leen como negaciones."""
    from src.texto import interpretar
    r = interpretar("He trabajado 3 años de auxiliar administrativa. Vivo en Chamberí, no tengo coche y tengo un "
                    "niño de 2 años. No volvería a estudiar y lo máximo que estaría dispuesto a viajar es 15 min.",
                    D["nom"])
    assert (r["ine"], r["cp"], r["hijo"], r["formacion"], r["T"]) == ("28079", "28010", True, False, 15)
    r = interpretar("He trabajado 6 años de camarero. Vivo en Parla, no tengo coche ni hijos. Si merece la pena, "
                    "volvería a estudiar y lo máximo que estaría dispuesta a viajar es 45 min.", D["nom"])
    assert (r["ocupacion"], r["ine"], r["coche"], r["hijo"], r["formacion"], r["T"]) ==         ("camarero", "28106", False, False, True, 45)


def test_simulador_y_ranking(D):
    import numpy as np
    from src import simulador as S
    ids, tt, P, U, pob = S.datos_sector(D, "TOT", 60)
    t2 = S.mejorar(tt, ids, "28106", 10)
    A0, A1 = S.accesibilidad(tt <= 60, P, U), S.accesibilidad(t2 <= 60, P, U)
    assert A1[ids.index("28106")] > A0[ids.index("28106")]
    # conservación: el total repartido no cambia, solo su reparto
    alc = lambda M: P[(U @ M) > 0].sum()
    assert np.isclose((U * A0).sum(), alc(tt <= 60), rtol=1e-6)
    assert np.isclose((U * A1).sum(), alc(t2 <= 60), rtol=1e-6)
    r = S.ranking(D, "TOT", 60, 10)
    assert len(r) > 100 and "28079" not in set(r["ine"])
    assert r["salen_neto"].is_monotonic_decreasing
    assert r.iloc[0]["salen_neto"] > 0


def test_validacion():
    import json
    from src.config import PROCESSED
    V = json.loads((PROCESSED / "validacion.json").read_text(encoding="utf-8"))
    vt = V["tiempos_vs_edm2018"]
    assert vt["pares"] >= 50 and abs(vt["sesgo_mediano_min"]) <= 5 and vt["pct_dentro_15min"] >= 0.6
    assert all(d["spearman_puestos_paro"] < 0 for d in V["indicador_vs_tasa_paro"].values())
