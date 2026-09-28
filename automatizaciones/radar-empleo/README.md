# Radar de empleo con IA

Cada mañana revisa las ofertas nuevas, las puntúa con IA según **mi propia rúbrica** y me envía por email solo las que merecen la pena, con el porqué y un argumento para la candidatura.

Lo uso a diario en mi búsqueda de empleo. Las métricas de uso real están en [`datos/metricas.csv`](datos/metricas.csv).

## Cómo funciona

```
 Alertas de LinkedIn ─┐   (email, vía IMAP)
                      ├──► Quitar ya vistas ──► Filtro por reglas ──► Claude + rúbrica ──► Email diario
 API de Adzuna ───────┘                          (gratis, obvio)      (tool use, JSON)     + métricas
                                  ▲
                    GitHub Actions: lunes a viernes a las 08:15
```

| Archivo | Qué hace |
|---|---|
| `radar/linkedin_email.py` | Lee las alertas de LinkedIn de mi buzón y extrae título, empresa y ubicación |
| `radar/adzuna.py` | Consulta la API oficial de Adzuna (incluye extracto de la descripción) |
| `radar/puntuar.py` | Filtro por reglas + evaluación con Claude y salida estructurada |
| `radar/informe.py` | Email diario y métricas agregadas |
| `rubrica.md` · `perfil.md` | Mi criterio y mi perfil: lo que la IA usa para decidir |
| `evals/` | Conjunto etiquetado a mano y script que mide si la IA acierta |
| `tests/` | Pruebas que se ejecutan antes de cada ejecución |

## Decisiones de diseño

- **LinkedIn por email, no scraping.** LinkedIn prohíbe el acceso automatizado y puede bloquear la cuenta. Las alertas por email son el canal oficial; el programa solo lee mi propio correo, en modo solo lectura.
- **Reglas antes que IA.** Lo obvio (riesgo de crédito, puestos senior) se descarta sin llamar al modelo. Más barato y más predecible.
- **Tool use con esquema JSON.** Claude devuelve siempre los mismos campos (nota, veredicto, encaje, carencias, probabilidad de entrevista), así las notas se pueden ordenar, medir y comparar.
- **Prompt caching.** La rúbrica y el perfil se repiten en cada llamada; se cachean y esa parte cuesta ~10 % a partir de la segunda oferta.
- **Temperatura 0.** La misma oferta debe recibir la misma nota.
- **Honestidad sobre la información.** Si una oferta solo trae título, la IA lo marca (`info_suficiente=false`) y la nota se presenta como orientativa.
- **Privacidad.** El repo es público: no se publican ofertas ni notas, solo métricas agregadas. Los ids ya vistos se guardan como huella (hash). El dataset de evals está anonimizado.

## Evals: ¿puntúa como yo?

Puntúo a mano un conjunto de ofertas y `evals/evaluar.py` compara mis notas con las de la IA:

- error medio en puntos,
- acierto a ±2 puntos,
- acierto en la decisión *aplicar / no aplicar*,
- **falsos negativos**: ofertas buenas que la IA descartaría. Es la métrica que más vigilo, porque son oportunidades perdidas.

Cualquier cambio de prompt o de modelo se valida con el eval antes de darlo por bueno. Resultados en [`evals/resultados.md`](evals/resultados.md).

## Probarlo

```bash
pip install -r requirements.txt
python main.py --demo        # sin claves: datos de ejemplo y evaluador simulado
python -m pytest -q tests
```

Para uso real, estas variables (en GitHub: *Settings → Secrets → Actions*): `ANTHROPIC_API_KEY`, `GMAIL_USUARIO`, `GMAIL_CLAVE_APP` (contraseña de aplicación de Google), `ADZUNA_APP_ID`, `ADZUNA_APP_KEY`.

## Próximas mejoras

- Juez calibrado: comparar varios modelos (Haiku vs Sonnet) en coste y precisión con el mismo eval.
- Borrador de mensaje al reclutador para las ofertas con nota ≥ 8.
- Aprender de mis decisiones: si aplico o descarto, ajustar la rúbrica.
