# Primer mensaje para Claude Code

Copia y pega esto en la primera sesión (mejor en modo plan: Shift+Tab hasta "plan mode"):

---
Lee CLAUDE.md y los tres PDF de docs/. Tenemos hasta el 20 de octubre para entregar un
prototipo funcional y los datasets elaborados.

Primero, sin escribir código todavía:
1. Usa la API CKAN de datos.comunidad.madrid para localizar cada conjunto de la sección
   «Datos — fuentes» de CLAUDE.md por su título y dime su id, formato, columnas reales
   (diccionario) y rango de fechas. Señala en especial si el de afiliados según cuentas de
   cotización trae sector.
2. Con eso, propón el plan de implementación por días (17, 18, 19 y mañana del 20) y un
   reparto en cuatro frentes para cuatro personas: datos, tiempos de viaje, indicadores
   y recomendador, app.

Después empieza por src/download.py y src/config.py.
---

Prompts útiles después:
- «Implementa el cálculo de tiempos con r5py; si en una hora no funciona, pasa al plan B».
- «Genera data/processed/README.md con el diccionario de todos los datasets elaborados».
- «Abre la app y recorre el caso de Lucía (Parla, auxiliar administrativa, sin coche, hijo de
   2 años). Dime qué falla o no se entiende».
