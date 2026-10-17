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
                 "formacion": True, "T": None}
    res = R.recomendar(D, "aux_admin", "28106", hijo=True, T=45)
    assert [t.tipo for t in res["tarjetas"]] == ["directo", "salto_corto", "salto_formacion"]
