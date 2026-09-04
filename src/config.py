"""
Configuración del pipeline Kobo -> Monday.

Nada de esto contiene credenciales reales. Todo se lee de variables de entorno
(en producción: GitHub Secrets). En modo de prueba (DRY_RUN=true) el script
nunca llama a la API real de Kobo ni de Monday.
"""
import os

DRY_RUN = os.getenv("DRY_RUN", "true").lower() == "true"

KOBO_API_TOKEN = os.getenv("KOBO_API_TOKEN", "")
KOBO_ASSET_UID = os.getenv("KOBO_ASSET_UID", "")
KOBO_BASE_URL = os.getenv("KOBO_BASE_URL", "https://kobo.ifrc.org")

MONDAY_API_TOKEN = os.getenv("MONDAY_API_TOKEN", "")
MONDAY_BOARD_ID = os.getenv("MONDAY_BOARD_ID", "")
MONDAY_API_URL = "https://api.monday.com/v2"

MONDAY_COLUMN_MAP = {
    "tipo_area": "color_mm6r3ja7",
    "estado": "color_mm6rjg61",
    "municipio": "color_mm6rcbv4",
    "parroquia": "color_mm6r6yre",
    "sector_comunidad": "long_text_mm6r1nky",
    "nombre_campamento": "long_text_mm6r5k8r",
    "tipo_campamento": "color_mm6rvkj1",
    "ubicacion": "long_text_mm6rwcs",
    "clasificacion_comunidad": "color_mm6rtwv",
    "necesidades_principales": "dropdown_mm6r93b3",
    "prioridad_1": "color_mm6rbzgz",
    "asistencia_recibida": "color_mm6rrkav",
    "brechas_necesidades": "dropdown_mm6rztw",
    "actores_actuales": "dropdown_mm6rr9zk",
    "riesgo_duplicacion": "color_mm6rwr42",
    "familias_actuales": "numeric_mm6r640v",
    "personas_actuales": "numeric_mm6rst2h",
    "familias_afectadas": "numeric_mm6rrfkn",
    "familias_no_permanecen": "numeric_mm6r9t48",
    "destruidas": "dropdown_mm6rdnka",
    "danadas": "dropdown_mm6r4n2t",
    "danadas_vivienda_n": "numeric_mm6rqpsg",
    "danadas_multifamiliar_n": "numeric_mm6rdxse",
    "servicios_afectados": "dropdown_mm6r9z18",
    "riesgos_terremoto": "dropdown_mm6r6sq9",
    "salud_primaria": "color_mm6r1exd",
    "necesidad_salud": "dropdown_mm6rcmhm",
    "agua_suficiente_com": "color_mm6rmsp6",
    "fuente_agua_com": "color_mm6rf2qw",
    "frecuencia_agua_com": "color_mm6rwnpe",
    "calidad_agua_com": "color_mm6rdcz6",
    "aguas_negras": "color_mm6rd2kg",
    "vectores_com": "dropdown_mm6r3d3r",
    "dificultad_agua_com": "color_mm6re15r",
    "fuente_agua_camp": "color_mm6rsgjm",
    "agua_suficiente_camp": "color_mm6rkw0b",
    "vectores_camp": "dropdown_mm6r3vhy",
    "enfermedades_camp": "dropdown_mm6r5p0t",
    "lavado_manos_camp": "color_mm6rc6yn",
    "estado_sanitarios_camp": "color_mm6r1wdz",
    "suficiencia_sanitarios_camp": "color_mm6r1daw",
    "necesidades_alojamiento": "dropdown_mm6rrj99",
    "riesgo_retorno": "color_mm6ret12",
    "familias_alojamiento": "numeric_mm6rsrj2",
    "intencion_permanencia_campamento": "color_mm6r3nzf",
    "acceso_mercados": "color_mm6rjyan",
    "apoyo_reactivacion": "dropdown_mm6rbghf",
    "riesgos_proteccion": "dropdown_mm6rywsd",
    "malestar_emocional": "color_mm6rw2nv",
    "servicios_smaps": "dropdown_mm6rf0e5",
    "grupos_smaps": "dropdown_mm6rb721",
    "sectores_prioritarios": "dropdown_mm6rw0wh",
    "evaluacion_tecnica": "dropdown_mm6rme59",
    "situacion_critica": "color_mm6rcjds",
    "prioridad_preliminar": "color_mm6rvvfn",
    "puntos_urgencia": "numeric_mm6rzmct",
    "nivel_urgencia": "color_mm6rr2g5",
    "puntos_factibilidad": "numeric_mm6rfwcg",
    "nivel_factibilidad": "color_mm6rkghg",
    "cuadrante": "color_mm6rzjwx",
    "condiciones_distribucion": "dropdown_mm6s4s4x",
    "referente": "text_mm6v9jk7",
    "telefono_referente": "text_mm6vaxs",
    "acciones_siguientes": "text_mm6vfd10",
    "fecha_eval": "date_mm6v1zxa",
    "En_el_marco_del_diagn_stico_te": "color_mm6vwnfn",  # Evaluación de seguridad
    "Nombre_de_la_persona_ionario_de_seguridad": "text_mm6vmk98",  # Persona
    "progreso": "color_mm6vybqh",  # Progreso (no viene de Kobo, se fija en monday_client.py)
}

# Grupos antiguos, basados en Cuadrante. Ya no se usan para ubicar items
# nuevos (ver PROGRESO_GROUP_MAP más abajo); se conservan solo por si
# reorganizar_grupos.py necesita consultarlos para migraciones históricas.
CUADRANTE_GROUP_MAP = {
    "Intervenir ya": "topics",
    "Intervenir con gestión de riesgo": "group_mm6t643r",
    "Resolver acceso primero": "group_mm6t643r",
    "Oportunidad": "group_mm6tg4cs",
    "Programar con preparación": "group_mm6t72tj",
    "Monitorear": "group_mm6t72tj",
}

# El tablero usa un solo grupo para todos los items (ya no se separa en
# 3 tablas por Progreso). El estado real de avance se maneja a mano en la
# columna Progreso (status), no moviendo items entre grupos.
MONDAY_DEFAULT_GROUP_ID = "group_mm6w12kt"  # "Comunidades" (antes "Evaluada")

# Toda evaluación nueva sincronizada desde Kobo entra con este valor en la
# columna Progreso, porque recién fue diagnosticada y aún no ha sido
# contactada ni intervenida. El equipo cambia la etiqueta manualmente
# conforme avanza el trabajo real.
PROGRESO_DEFAULT = "Evaluada"
