"""El cerebro: Claude puntúa cada oferta según MI rúbrica y MI perfil.

Decisiones de diseño (explicadas en el README):
- Filtro previo por reglas: lo obvio (p. ej. "riesgo de crédito") se descarta
  sin llamar a la IA. Más barato y más rápido.
- Tool use con esquema JSON: Claude está obligado a responder con los mismos
  campos siempre, así el resultado se puede ordenar, medir y comparar.
- Prompt caching: la rúbrica y el perfil son iguales en todas las llamadas;
  se marcan como caché y las siguientes llamadas cuestan ~10 % de esa parte.
- Temperatura 0: la misma oferta debe recibir la misma nota (reproducible).
"""
from __future__ import annotations

import re
from pathlib import Path

from .modelo import Oferta

RAIZ = Path(__file__).resolve().parent.parent
MODELO = "claude-sonnet-5"

# Reglas baratas antes de gastar en IA: (patrón, nota, motivo)
REGLAS_DESCARTE = [
    (r"riesgo[s]? de cr[eé]dito|credit risk|analista de riesgos|risk analyst", 0,
     "Riesgo de crédito: es justo lo que quiero dejar."),
    (r"\b(senior|sr\.?|lead|principal|staff|head of|director)\b", 2,
     "Puesto senior/lead: requiere años de experiencia que aún no tengo en el área."),
]

HERRAMIENTA = {
    "name": "evaluar_oferta",
    "description": "Registra la evaluación de una oferta de empleo para el candidato.",
    "input_schema": {
        "type": "object",
        "properties": {
            "puntuacion": {"type": "integer", "minimum": 0, "maximum": 10,
                           "description": "Nota según la rúbrica del candidato."},
            "veredicto": {"type": "string", "enum": ["aplicar hoy", "aplicar", "dudosa", "descartar"]},
            "motivo": {"type": "string", "description": "Una frase: por qué esta nota."},
            "encaje": {"type": "array", "items": {"type": "string"},
                       "description": "Qué de su experiencia encaja (máx. 3)."},
            "carencias": {"type": "array", "items": {"type": "string"},
                          "description": "Qué le falta o puede frenar la candidatura (máx. 3)."},
            "probabilidad_entrevista": {"type": "string", "enum": ["alta", "media", "baja"]},
            "argumento_carta": {"type": "string",
                                "description": "Un argumento concreto y específico para el mensaje al reclutador."},
            "info_suficiente": {"type": "boolean",
                                "description": "false si solo hay título y la nota es orientativa."},
        },
        "required": ["puntuacion", "veredicto", "motivo", "probabilidad_entrevista", "info_suficiente"],
    },
}


def _sistema() -> list[dict]:
    rubrica = (RAIZ / "rubrica.md").read_text(encoding="utf-8")
    perfil = (RAIZ / "perfil.md").read_text(encoding="utf-8")
    texto = (
        "Eres un headhunter especializado en perfiles de IA y automatización en España. "
        "Evalúas ofertas para un candidato concreto con honestidad: ni inflas ni hundes notas. "
        "Aplica SOLO la rúbrica del candidato. Si la oferta solo trae título y empresa, puntúa "
        "de forma orientativa y marca info_suficiente=false.\n\n"
        f"<rubrica>\n{rubrica}\n</rubrica>\n\n<perfil_candidato>\n{perfil}\n</perfil_candidato>"
    )
    # cache_control: esta parte se reutiliza en todas las llamadas del día
    return [{"type": "text", "text": texto, "cache_control": {"type": "ephemeral"}}]


def filtro_reglas(o: Oferta) -> dict | None:
    texto = f"{o.titulo} {o.descripcion[:300]}"
    for patron, nota, motivo in REGLAS_DESCARTE:
        if re.search(patron, texto, re.I):
            return {"puntuacion": nota, "veredicto": "descartar", "motivo": motivo,
                    "probabilidad_entrevista": "baja", "info_suficiente": True, "por_reglas": True}
    return None


def evaluar(cliente, o: Oferta, modelo: str = MODELO) -> dict:
    """Devuelve la evaluación y el uso de tokens. `cliente` es anthropic.Anthropic()."""
    previa = filtro_reglas(o)
    if previa:
        return previa
    oferta_txt = (
        f"Título: {o.titulo}\nEmpresa: {o.empresa}\nUbicación: {o.ubicacion}\n"
        f"Salario: {o.salario or 'no indicado'}\nFuente: {o.fuente}\n\nDescripción:\n{o.descripcion[:4000]}"
    )
    r = cliente.messages.create(
        model=modelo,
        max_tokens=800,
        temperature=0,
        system=_sistema(),
        tools=[HERRAMIENTA],
        tool_choice={"type": "tool", "name": "evaluar_oferta"},
        messages=[{"role": "user", "content": f"<oferta>\n{oferta_txt}\n</oferta>"}],
    )
    bloque = next(b for b in r.content if b.type == "tool_use")
    ev = dict(bloque.input)
    u = r.usage
    ev["_uso"] = {
        "entrada": u.input_tokens,
        "salida": u.output_tokens,
        "cache_leida": getattr(u, "cache_read_input_tokens", 0) or 0,
        "cache_escrita": getattr(u, "cache_creation_input_tokens", 0) or 0,
    }
    return ev


# Precios por millón de tokens (USD) para estimar el coste de cada ejecución
PRECIOS = {"claude-sonnet-5": (2.0, 10.0), "claude-haiku-4-5-20251001": (1.0, 5.0), "claude-opus-5-5": (4.0, 20.0)}


def coste(evs: list[dict], modelo: str = MODELO) -> float:
    pin, pout = PRECIOS.get(modelo, (2.0, 10.0))
    total = 0.0
    for ev in evs:
        u = ev.get("_uso")
        if not u:
            continue
        total += (u["entrada"] * pin + u["cache_escrita"] * pin * 1.25
                  + u["cache_leida"] * pin * 0.1 + u["salida"] * pout) / 1e6
    return round(total, 4)
