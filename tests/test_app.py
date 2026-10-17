"""La app arranca y recorre sus tres vistas sin excepciones."""
from streamlit.testing.v1 import AppTest


def _app():
    at = AppTest.from_file("app/app.py", default_timeout=120)
    at.run()
    assert not at.exception, at.exception
    return at


def test_ciudadania_y_controles():
    at = _app()
    assert any("Tus tres caminos" in m.value for m in at.markdown)
    at.toggle(key="coche").set_value(True).run()
    assert not at.exception
    at.toggle(key="hijo").set_value(False).run()
    at.toggle(key="formacion").set_value(False).run()
    assert not at.exception
    at.selectbox(key="ine").set_value("28001").run()   # La Acebeda: pueblo de sierra
    assert not at.exception
    at.select_slider(key="T").set_value(15).run()
    assert not at.exception
    at.button[0].click().run()                        # «Entender mi situación»
    assert not at.exception
    assert at.session_state["ine"] == "28106" and at.session_state["hijo"] is True


def test_planificacion_y_datos():
    at = _app()
    at.sidebar.radio[0].set_value("Orientación y planificación").run()
    assert not at.exception
    at.radio[0].set_value("Balance empleo/residentes").run()
    assert not at.exception
    at.sidebar.radio[0].set_value("Datos y método").run()
    assert not at.exception
