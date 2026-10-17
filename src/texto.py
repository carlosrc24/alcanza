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


def _norm(s: str) -> str:
    s = unicodedata.normalize("NFD", s.lower())
    return "".join(c for c in s if unicodedata.category(c) != "Mn")


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


def interpretar(texto: str, municipios: dict[str, str]) -> dict:
    """Devuelve los campos que se han podido entender (los demás quedan en None)."""
    t = " " + _norm(texto) + " "
    out = {"ocupacion": None, "ine": None, "coche": None, "hijo": None, "formacion": None, "T": None}

    mejor = (0, None)
    for ine, vs in _variantes(municipios).items():
        for v in vs:
            if len(v) >= 4 and re.search(rf"\b{re.escape(v)}\b", t) and len(v) > mejor[0]:
                mejor = (len(v), ine)
    out["ine"] = mejor[1]

    pos = {}
    for oid, claves in SINONIMOS.items():
        for k in claves:
            i = t.find(k)
            if i >= 0:
                # coincidencia más larga (más específica) gana; a igualdad, la primera en el texto
                if oid not in pos or len(k) > pos[oid][0]:
                    pos[oid] = (len(k), i)
    if pos:
        out["ocupacion"] = max(pos, key=lambda o: (pos[o][0], -pos[o][1]))

    if re.search(r"(no tengo|sin) (coche|carne|vehiculo)", t):
        out["coche"] = False
    elif re.search(r"(tengo|con) (coche|vehiculo)", t):
        out["coche"] = True

    if re.search(r"\b(hij[oa]s?|nin[oa]s?|bebe|guarderia|peque)\b", t):
        edad = re.search(r"(hij[oa]s?|nin[oa]s?|bebe|peque\w*)\s+(de\s+)?(\d+)\s*(anos|ano|meses)", t)
        edad = re.match(r"(\d+)\s*(\w+)", f"{edad.group(3)} {edad.group(4)}") if edad else None
        out["hijo"] = True if not edad or edad.group(2) == "meses" or int(edad.group(1)) <= 3 else False

    if re.search(r"(estudiar|formarme|formacion|curso|fp\b|reciclarme|aprender)", t):
        out["formacion"] = not re.search(r"no (quiero|puedo) (estudiar|formarme)", t)

    m = re.search(r"(\d+)\s*(min|minutos)", t)
    if m:
        out["T"] = int(m.group(1))
    elif re.search(r"(\d+|una)\s*hora", t):
        out["T"] = 60
    return out
