"""La app arranca y recorre sus tres vistas sin excepciones."""
import os

from streamlit.testing.v1 import AppTest

os.environ["ALCANZA_SIN_IA"] = "1"   # pruebas deterministas y sin red; la IA se prueba en test_ia.py


def _app():
    at = AppTest.from_file("app/app.py", default_timeout=120)
    at.run()
    assert not at.exception, at.exception
    return at


def test_ciudadania_y_controles():
    at = _app()
    assert any("Tus tres caminos" in m.value for m in at.markdown)
    # ejemplo de la demo (Chamberí) con reglas: Madrid, código postal 28010, 15 min
    at.button[0].click().run()                        # «Entender mi situación»
    assert not at.exception
    assert (at.session_state["ine"], at.session_state["cp"], at.session_state["T"]) == ("28079", "28010", 15)
    assert any("Chamberí (28010)" in m.value for m in at.markdown)
    # los campos manuales están comentados: se cambia la situación escribiendo
    at.text_area[0].input("Vivo en La Acebeda, soy camarero, tengo coche, sin hijos, máximo 15 min").run()
    at.button[0].click().run()
    assert not at.exception
    assert at.session_state["ine"] == "28001" and at.session_state["coche"] is True and at.session_state["T"] == 15
    at.select_slider(key="T").set_value(90).run()
    assert not at.exception


def test_planificacion_y_datos():
    at = _app()
    at.sidebar.radio[0].set_value("Orientación y planificación").run()
    assert not at.exception
    at.radio[0].set_value("Balance empleo/residentes").run()
    assert not at.exception
    at.sidebar.radio[0].set_value("Datos y método").run()
    assert not at.exception


def test_entrada_con_ia_simulada(monkeypatch):
    from src import ia
    monkeypatch.setenv("ALCANZA_SIN_IA", "0")
    monkeypatch.setattr(ia, "clave", lambda: "falsa")
    monkeypatch.setattr(ia, "_llamar", lambda *a, **k: {
        "ocupacion_id": "aux_enfermeria", "ocupacion_dicha": "enfermera", "ocupacion_aproximada": True,
        "municipio": "Getafe", "coche": True, "hijo_0_3": False, "formacion": None, "tiempo_max_min": 30})
    at = _app()
    at.button[0].click().run()
    assert not at.exception
    assert at.session_state["ine"] == "28065" and at.session_state["ocupacion"] == "aux_enfermeria"
    assert at.session_state["coche"] is True and at.session_state["T"] == 30
    assert any("enfermera" in s.value for s in at.success)
