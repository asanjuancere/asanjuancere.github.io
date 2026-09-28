"""Pruebas automáticas: se ejecutan en cada cambio (GitHub Actions) con `python -m pytest`."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from evals.evaluar import metricas  # noqa: E402
from radar import puntuar  # noqa: E402
from radar.linkedin_email import extraer_ofertas_html  # noqa: E402
from radar.modelo import Oferta  # noqa: E402

# Estructura simplificada de un email de alerta de LinkedIn.
# TODO: sustituir por un email real anonimizado en cuanto llegue la primera alerta.
EMAIL = """
<html><body>
<a href="https://www.linkedin.com/comm/jobs/view/4470880613/?trackingId=abc">Junior AI Operations Specialist</a>
<p>WEEWOO · Madrid, Comunidad de Madrid, España</p>
<p>Contratando activamente</p>
<a href="https://www.linkedin.com/comm/jobs/view/4470880613/?trackingId=abc">Ver empleo</a>
<table><tr><td><a href="https://www.linkedin.com/comm/jobs/view/4472492940/">Automation &amp; Analytics Specialist</a></td></tr>
<tr><td>Mercedes-Benz Group Services Madrid</td></tr><tr><td>San Sebastián de los Reyes</td></tr></table>
<a href="https://www.linkedin.com/comm/jobs/search/?keywords=ia">Ver todos los empleos</a>
</body></html>
"""


def test_extrae_ofertas_del_email():
    ofs = {o.id: o for o in extraer_ofertas_html(EMAIL)}
    assert set(ofs) == {"linkedin:4470880613", "linkedin:4472492940"}
    w = ofs["linkedin:4470880613"]
    assert w.titulo == "Junior AI Operations Specialist"
    assert w.empresa == "WEEWOO" and w.ubicacion.startswith("Madrid")
    m = ofs["linkedin:4472492940"]
    assert m.titulo == "Automation & Analytics Specialist"
    assert m.empresa == "Mercedes-Benz Group Services Madrid"
    assert m.ubicacion == "San Sebastián de los Reyes"


def test_reglas_descartan_riesgo_de_credito_sin_llamar_a_la_ia():
    ev = puntuar.filtro_reglas(Oferta(id="x", fuente="manual", titulo="Analista de Riesgos de Crédito"))
    assert ev["puntuacion"] == 0 and ev["por_reglas"]


def test_reglas_no_tocan_ofertas_normales():
    assert puntuar.filtro_reglas(Oferta(id="x", fuente="manual", titulo="Junior AI Operations Specialist")) is None


def test_metricas_eval():
    m = metricas([(9, 8), (8, 4), (2, 3), (1, 7)])
    assert m["mae"] == 3.0  # (1+4+1+6)/4
    assert m["falsos_negativos"] == 1 and m["falsos_positivos"] == 1
    assert m["acierto_decision"] == 0.5
