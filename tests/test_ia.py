"""Entrada en lenguaje natural con IA: validación de la salida, respaldo y prueba real opcional."""
import pytest

from src import ia, recomendador as R


@pytest.fixture(scope="module")
def listas():
    D = R.cargar()
    return D["ocu"].set_index("id")["ocupacion"].to_dict(), D["nom"]


def test_valida_y_descarta_lo_que_no_esta_en_las_listas(listas, monkeypatch):
    ocu, nom = listas
    monkeypatch.setattr(ia, "clave", lambda: "falsa")
    monkeypatch.setattr(ia, "_llamar", lambda *a, **k: {
        "ocupacion_id": "astronauta", "ocupacion_dicha": "astronauta", "ocupacion_aproximada": True,
        "municipio": "Rozas de Madrid (Las)", "coche": "sí", "hijo_0_3": True, "formacion": False,
        "tiempo_max_min": 9999})
    r = ia.interpretar("soy dependienta", ocu, nom)
    assert r.metodo == "ia"
    assert r.campos["ocupacion"] == "dependiente"      # inválida → se completa con las reglas
    assert r.campos["ine"] == "28127" and r.campos["coche"] is None and r.campos["T"] is None
    assert r.ocupacion_aproximada


def test_respaldo_si_todos_los_modelos_fallan(listas, monkeypatch):
    ocu, nom = listas
    monkeypatch.setattr(ia, "clave", lambda: "falsa")

    def falla(*a, **k):
        raise RuntimeError("HTTP 429: cuota agotada")
    monkeypatch.setattr(ia, "_llamar", falla)
    r = ia.interpretar("camarero en móstoles, tengo coche", ocu, nom)
    assert r.metodo == "reglas" and len(r.intentos) == len(ia.MODELOS)
    assert r.campos["ocupacion"] == "camarero" and r.campos["ine"] == "28092" and r.campos["coche"] is True


@pytest.mark.skipif(ia.clave() is None, reason="sin clave de Gemini")
def test_gemini_real(listas):
    ocu, nom = listas
    r = ia.interpretar("Vivo en Sanse, era enfermera, no conduzco, tengo un bebé, tres cuartos de hora", ocu, nom)
    assert r.metodo == "ia", r.intentos
    assert r.campos["ine"] == "28134" and r.campos["coche"] is False and r.campos["hijo"] is True
    assert r.campos["T"] == 45 and r.campos["ocupacion"] == "aux_enfermeria"
