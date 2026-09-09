"""Diagnostico puntual de solo lectura: imprime el valor crudo de un
campo especifico en Kobo para submissions cuyo item_name coincida.
Solo se usa para campos no sensibles (numeros), nunca para datos de
contacto."""
import sys
from kobo_client import get_new_submissions
from transform import flatten_submission, build_item_name

nombres_buscados = sys.argv[1:]
campo = "personas_actuales"

submissions = get_new_submissions(since_id=0)
for raw in submissions:
    flat = flatten_submission(raw)
    nombre = build_item_name(flat)
    if any(n.lower() in nombre.lower() for n in nombres_buscados):
        crudo = raw.get(campo, "<clave no encontrada en la submission>")
        aplanado = flat.get(campo, "<clave no encontrada tras aplanar>")
        print(f"{nombre} (_id={raw.get('_id')}):")
        print(f"  Valor crudo de Kobo ('{campo}'): {crudo!r}")
        print(f"  Valor tras aplanar/traducir: {aplanado!r}")
