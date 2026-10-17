"""Indicadores de accesibilidad al empleo por municipio de origen, sector, umbral T y modo.

Método 2SFCA (Shen 1998; Luo y Wang 2003):
  1) para cada destino j:  R_j = puestos_j / Σ_k parados_k · [t_kj ≤ T]
  2) para cada origen i:   A_i = Σ_j R_j · [t_ij ≤ T]          (puestos por competidor)
Los competidores (parados) se desplazan siempre en transporte público; el modo del usuario
(transporte público o coche) solo cambia su propio conjunto de destinos alcanzables.
"""
import numpy as np
import pandas as pd

from .config import SECTORES, UMBRALES_T

MODOS = {"tp": "min_tp", "coche": "min_coche"}


def _matriz(tiempos: pd.DataFrame, ids, col) -> np.ndarray:
    m = tiempos.pivot(index="origen", columns="destino", values=col).reindex(index=ids, columns=ids)
    return m.to_numpy(dtype=float)


def _vector(df, ids, sector, col):
    return df[df["sector"] == sector].set_index("ine")[col].reindex(ids).fillna(0).to_numpy(float)


def calcular(tiempos, puestos, parados, serie_puestos, municipios):
    ids = municipios["ine"].tolist()
    T_mat = {m: _matriz(tiempos, ids, c) for m, c in MODOS.items()}
    anio = int(serie_puestos["anio"].max())
    prev = serie_puestos[serie_puestos["anio"] == anio - 1]
    filas_o, filas_d = [], []
    def total(df, col):
        return df.groupby("ine")[col].sum().reindex(ids).fillna(0).to_numpy(float)

    for s in list(SECTORES) + ["TOT"]:
        if s == "TOT":  # todos los sectores
            P, P0, U = total(puestos, "puestos"), total(prev, "puestos"), total(parados, "parados")
        else:
            P = _vector(puestos, ids, s, "puestos")
            P0 = _vector(prev, ids, s, "puestos")
            U = _vector(parados, ids, s, "parados")
        ratio_regional = P.sum() / U.sum()
        for T in UMBRALES_T:
            Mtp = T_mat["tp"] <= T
            D = U @ Mtp                         # competidores que llegan a cada destino j
            R = P / np.maximum(D, 1.0)
            for j, ine in enumerate(ids):
                filas_d.append((ine, s, T, P[j], D[j], R[j]))
            for modo, tm in T_mat.items():
                M = tm <= T
                alc = M @ P
                A = M @ R
                alc0 = M @ P0
                var = np.where(alc0 > 0, alc / np.where(alc0 > 0, alc0, 1) - 1, np.nan)
                for i, ine in enumerate(ids):
                    filas_o.append((ine, s, T, modo, alc[i], alc[i] / A[i] if A[i] > 0 else 0.0, A[i],
                                    A[i] / ratio_regional, var[i], int(M[i].sum())))
    ind = pd.DataFrame(filas_o, columns=["ine", "sector", "T", "modo", "puestos_alcanzables", "competidores",
                                         "puestos_por_competidor", "indice_relativo", "var_interanual",
                                         "municipios_alcanzables"])
    ind["tendencia"] = np.select([ind["var_interanual"] > 0.02, ind["var_interanual"] < -0.02],
                                 ["sube", "baja"], "estable")
    ind = ind.round({"puestos_alcanzables": 0, "competidores": 0, "puestos_por_competidor": 3,
                     "indice_relativo": 3, "var_interanual": 4})
    dest = pd.DataFrame(filas_d, columns=["ine", "sector", "T", "puestos", "competidores_que_llegan",
                                          "puestos_por_competidor_destino"])
    dest = dest.round({"puestos": 0, "competidores_que_llegan": 0, "puestos_por_competidor_destino": 3})
    return ind, dest
