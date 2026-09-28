# Extractor de Facturas IA

Convierte facturas en PDF o imagen en datos estructurados listos para contabilidad, con validación automática.

**[▶ Probar la demo en vivo](https://asanjuancere.github.io/herramientas/extractor-facturas/)** — el botón «Probar con facturas de ejemplo» funciona sin clave de API.

## El problema

En administración y contabilidad, cada factura de proveedor se teclea a mano en el ERP o en Excel: proveedor, NIF, número, fechas, base, IVA, retención y total. Son unos 3 minutos por factura y los errores (un total que no cuadra, un CIF mal copiado, una factura duplicada) se descubren tarde.

## La solución

1. Se suben una o varias facturas (PDF, JPG, PNG).
2. Claude lee cada documento y devuelve los datos mediante **tool use con un esquema JSON**, así la salida siempre tiene la misma estructura.
3. Reglas de negocio en JavaScript validan el resultado:
   - Dígito de control de **NIF, NIE y CIF**.
   - Que **base + IVA − IRPF = total**.
   - Que la cuota de IVA corresponda al tipo aplicado y que el tipo sea uno de los vigentes en España.
   - **Facturas duplicadas** (mismo proveedor y número).
   - Fechas ausentes o futuras, y lecturas de baja confianza.
4. Se pueden corregir celdas con doble clic (la validación se recalcula) y exportar a **CSV compatible con Excel en español** o copiar y pegar directamente.

## Impacto

| | Manual | Con la herramienta |
|---|---|---|
| Tiempo por factura | ~3 min | segundos + revisión de las marcadas |
| Detección de errores | al cuadrar el mes | en el momento de la carga |

El panel calcula el tiempo ahorrado en función de los minutos por factura que indique cada empresa.

## Tecnología

- HTML + CSS + JavaScript en un único archivo, sin servidor ni dependencias.
- API de Anthropic (Claude) llamada directamente desde el navegador.
- Salida estructurada con `tool_choice` forzado a la herramienta `registrar_factura`.

## Privacidad

La clave de API solo se envía a `api.anthropic.com`. Las facturas no pasan por ningún servidor propio. Opcionalmente, la clave se puede recordar en el navegador del usuario.

## Posibles mejoras

- Envío automático a Google Sheets o a un ERP.
- Flujo en n8n que procese las facturas que llegan a un buzón de correo.
- Soporte para varios tipos de IVA por factura.
