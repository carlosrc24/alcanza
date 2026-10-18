"""Simulador «¿y si…?» y ranking de mejoras de transporte (2SFCA recalculado en memoria).

Una mejora = restar `ahorro` minutos a los viajes en transporte público entre un municipio y
los demás (o solo con Madrid capital), en los dos sentidos, con un mínimo de 5 min.

El 2SFCA conserva el total (Σ parados · acceso = puestos alcanzados): lo que gana un municipio
lo pierde en parte la competencia en otros. Por eso el ranking ordena por parados que salen de
un «desierto de empleo accesible» (definición fija, la de la situación actual), no por la suma
de accesibilidad.
"""
import numpy as np
import pandas as pd

MADRID = "28079"


def accesibilidad(M: np.ndarray, P: np.ndarray, U: np.ndarray) -> np.ndarray:
    """A_i = Σ_j M_ij · P_j / Σ_k U_k · M_kj  (M booleana: t ≤ T)."""
    return M @ (P / np.maximum(U @ M, 1.0))


def datos_sector(D, sector: str, T: int):
    """Vectores alineados con D['mun']: ids, matriz de tiempos TP, puestos P, parados U, población."""
    ids = list(D["mun"]["ine"])
    tt = D["tt"].pivot(index="origen", columns="destino", values="min_tp").reindex(index=ids, columns=ids).to_numpy()
    P = (D["dest"][(D["dest"]["sector"] == sector) & (D["dest"]["T"] == T) & (D["dest"]["modo"] == "tp")]
         .set_index("ine")["puestos"].reindex(ids).fillna(0).to_numpy())
    par = D["par"].groupby("ine")["parados"].sum() if sector == "TOT" else \
        D["par"][D["par"]["sector"] == sector].set_index("ine")["parados"]
    U = par.reindex(ids).fillna(0).to_numpy()
    pob = D["mun"].set_index("ine")["poblacion"].reindex(ids).to_numpy()
    return ids, tt, P, U, pob


def mejorar(tt: np.ndarray, ids: list, ine: str, ahorro: float, solo_madrid: bool = False) -> np.ndarray:
    k = ids.index(ine)
    cols = [ids.index(MADRID)] if solo_madrid else [j for j in range(len(ids)) if j != k]
    cols = [j for j in cols if j != k]
    t2 = tt.copy()
    t2[k, cols] = np.maximum(tt[k, cols] - ahorro, 5)
    t2[cols, k] = np.maximum(tt[cols, k] - ahorro, 5)
    return t2


def desiertos(rel: np.ndarray, U: np.ndarray, pob: np.ndarray, excluidos: np.ndarray, umbrales=None):
    """Tercio con menos acceso relativo y tercio con más paro por habitante (≥ 50 parados)."""
    tasa = U / pob
    q_acc, q_par = umbrales if umbrales else (np.quantile(rel, 1 / 3), np.quantile(tasa, 2 / 3))
    return (rel <= q_acc) & (tasa >= q_par) & (U >= 50) & ~excluidos, (q_acc, q_par)


def ranking(D, sector: str, T: int, ahorro: float, solo_madrid: bool = False, hueco=frozenset()) -> pd.DataFrame:
    """Para cada municipio candidato: efecto de mejorar su conexión en `ahorro` minutos."""
    ids, tt, P, U, pob = datos_sector(D, sector, T)
    media = P.sum() / max(U.sum(), 1)
    excl = np.isin(ids, list(hueco))
    A0 = accesibilidad(tt <= T, P, U)
    des0, umbrales = desiertos(A0 / media, U, pob, excl)
    nom = D["mun"].set_index("ine")["nombre"]
    filas = []
    for k, ine in enumerate(ids):
        # la capital no es una intervención concreta; los municipios con hueco de GTFS no son fiables
        if ine == MADRID or excl[k] or U[k] < 50:
            continue
        t2 = mejorar(tt, ids, ine, ahorro, solo_madrid)
        A1 = accesibilidad(t2 <= T, P, U)
        des1, _ = desiertos(A1 / media, U, pob, excl, umbrales)
        alc0 = ((tt[k] <= T) * P).sum()
        alc1 = ((t2[k] <= T) * P).sum()
        filas.append({"ine": ine, "municipio": nom[ine], "parados": U[k],
                      "acceso_antes": A0[k] / media, "acceso_despues": A1[k] / media,
                      "puestos_alcanzables_antes": alc0, "puestos_alcanzables_despues": alc1,
                      "parados_salen_desierto": U[des0 & ~des1].sum(), "parados_entran_desierto": U[~des0 & des1].sum()})
    r = pd.DataFrame(filas)
    r["salen_neto"] = r["parados_salen_desierto"] - r["parados_entran_desierto"]
    r["ganancia_local"] = r["parados"] * (r["acceso_despues"] - r["acceso_antes"])
    return r.sort_values(["salen_neto", "ganancia_local"], ascending=False).reset_index(drop=True)
