"""Interpretación de la descripción en texto libre → campos del formulario.

Determinista (palabras clave); el usuario revisa y corrige los campos antes de calcular.
Ni este módulo ni ninguna IA puntúan o recomiendan.
"""
import re
import unicodedata

SINONIMOS = {
    "aux_admin": ["auxiliar administrativ", "administrativ", "oficina", "secretari"],
    "administrativo_contable": ["contable", "contabilidad", "facturacion"],
    "dependiente": ["dependient", "tienda", "vendedor", "comercio"],
    "cajero": ["cajer", "reponedor", "supermercado"],
    "camarero": ["camarer", "hosteleria", "bar ", "restaurante"],
    "cocinero": ["cocina", "pinche"],
    "cocinero_prof": ["cociner"],
    "recepcionista": ["recepcion", "atencion al cliente"],
    "recepcionista_hotel": ["hotel"],
    "mozo_almacen": ["almacen", "mozo", "logistica", "preparador de pedidos"],
    "carretillero": ["carretiller"],
    "repartidor": ["repartid", "reparto", "mensajer"],
    "conductor": ["conductor", "chofer", "camioner", "autobus"],
    "mecanico": ["mecanic", "taller"],
    "teleoperador": ["teleoperador", "call center", "telefonic"],
    "limpieza": ["limpieza", "limpiador", "limpiadora"],
    "vigilante": ["vigilante", "seguridad privada", "guarda"],
    "programador": ["programador", "informatic", "desarrollador", "software"],
    "cuidador": ["cuidador", "ayuda a domicilio", "dependientes", "geriatri", "mayores"],
    "aux_enfermeria": ["enfermeria", "tcae", "sanitari"],
    "educador_infantil": ["educador", "educacion infantil", "guarderia como"],
    "peluquero": ["peluquer", "estetic"],
    "operario_industria": ["operari", "fabrica", "produccion", "cadena de montaje"],
    "electricista": ["electricista", "mantenimiento"],
    "albanil": ["albanil", "obra", "construccion", "peon"],
    "jardinero": ["jardiner", "agricol", "campo"],
}

# Formas cortas habituales que comparten varios municipios: se resuelven al más poblado
ALIAS = {
    "torrejon": "28148", "alcala": "28005", "sanse": "28134", "san sebastian": "28134", "rivas": "28123",
    "villaviciosa": "28181", "san fernando": "28130", "villalba": "28047", "pozuelo": "28115",
    "colmenar": "28045", "boadilla": "28022", "arganda": "28014", "el escorial": "28131",
    "humanes": "28073", "paracuellos": "28104", "mejorada": "28084", "velilla": "28167",
    "madrid capital": "28079",
}
NUMEROS = {"un": 1, "una": 1, "uno": 1, "dos": 2, "tres": 3, "cuatro": 4, "cinco": 5, "seis": 6, "siete": 7,
           "ocho": 8, "nueve": 9, "diez": 10, "once": 11, "doce": 12}
_NUM = r"(\d+|" + "|".join(NUMEROS) + r")"


def _norm(s: str) -> str:
    s = unicodedata.normalize("NFD", s.lower())
    return "".join(c for c in s if unicodedata.category(c) != "Mn").replace("-", " ")


def _num(x: str) -> int:
    return int(x) if x.isdigit() else NUMEROS[x]


def _variantes_municipio(nombre: str) -> list[str]:
    n = _norm(nombre)
    v = [n]
    m = re.match(r"(.+) \((el|la|los|las)\)$", n)
    if m:
        v += [f"{m.group(2)} {m.group(1)}", m.group(1)]
    # forma corta sin el complemento («Las Rozas de Madrid» → «las rozas»)
    v += [x.split(" de ")[0] for x in list(v) if " de " in x]
    return v


def _variantes(municipios: dict[str, str]) -> dict[str, list[str]]:
    """Variantes de nombre de cada municipio, descartando las formas cortas ambiguas."""
    todas = {ine: _variantes_municipio(n) for ine, n in municipios.items()}
    cuenta = {}
    for vs in todas.values():
        for x in set(vs):
            cuenta[x] = cuenta.get(x, 0) + 1
    return {ine: [x for x in vs if cuenta[x] == 1 or x == vs[0]] for ine, vs in todas.items()}


def _municipio(t: str, municipios: dict[str, str]):
    mejor = (0, None)
    candidatos = [(v, ine) for ine, vs in _variantes(municipios).items() for v in vs]
    candidatos += [(a, ine) for a, ine in ALIAS.items() if ine in municipios]
    for v, ine in candidatos:
        if len(v) >= 4 and len(v) > mejor[0] and re.search(rf"\b{re.escape(v)}\b", t):
            mejor = (len(v), ine)
    return mejor[1]


def _ocupacion(t: str):
    pos = {}
    for oid, claves in SINONIMOS.items():
        for k in claves:
            i = t.find(k)
            if i >= 0:
                # coincidencia más larga (más específica) gana; a igualdad, la primera en el texto
                if oid not in pos or len(k) > pos[oid][0]:
                    pos[oid] = (len(k), i)
    return max(pos, key=lambda o: (pos[o][0], -pos[o][1])) if pos else None


def _coche(t: str):
    veh = r"(coche|carne|carnet|vehiculo|furgoneta|moto|auto)"
    if re.search(rf"(no tengo|no dispongo de|sin)( ni)?( de)?( un| una)? {veh}\b|no conduzco|no se conducir", t):
        return False
    if re.search(rf"(tengo|con|dispongo de|uso)( un| una| mi)? {veh}\b|\b{veh} propi[oa]|\bconduzco", t):
        return True
    return None


def _hijo(t: str):
    m = re.search(r"\b(hij[oa]s?|nin[oa]s?|bebes?|guarderia|peque\w*|criaturas?)\b", t)
    if not m:
        return None
    # edades que siguen a la palabra («dos hijos de 5 y 8 años», «un niño de 18 meses»)
    ventana = t[m.end():m.end() + 45]
    u = re.search(r"\b(anos?|meses|mes)\b", ventana)
    if not u:
        return True
    if u.group(1).startswith("mes"):
        return True
    edades = [n for n in (_num(x) for x in re.findall(rf"\b{_NUM}\b", ventana[:u.start()])) if n <= 25]
    return True if not edades else any(n <= 3 for n in edades)


def _tiempo(t: str):
    m = re.search(r"(\d+)\s*(min|minutos)\b", t)
    if m:
        return int(m.group(1))
    for patron, minutos in ((r"hora y media", 90), (r"media hora", 30), (r"tres cuartos", 45),
                            (r"cuarto de hora", 15)):
        if re.search(patron, t):
            return minutos
    m = re.search(r"\b(\d+|una|un|dos)\s*horas?\b", t)
    return 60 * _num(m.group(1)) if m else None


def interpretar(texto: str, municipios: dict[str, str]) -> dict:
    """Devuelve los campos que se han podido entender (los demás quedan en None)."""
    t = " " + _norm(texto) + " "
    out = {"ocupacion": _ocupacion(t), "ine": _municipio(t, municipios), "coche": _coche(t), "hijo": _hijo(t),
           "formacion": None, "T": _tiempo(t)}
    if re.search(r"(estudiar|formarme|formacion|curso|fp\b|reciclarme|aprender)", t):
        out["formacion"] = not re.search(r"no (quiero|puedo|me interesa) (estudiar|formarme)", t)
    return out
