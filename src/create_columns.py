"""
Crea automáticamente en Monday las 66 columnas del tablero
"Diagnóstico terreno — Terremoto 2026", con el tipo correcto para cada una
(Estado, Menú desplegable, Números o Texto largo).

Este script se corre UNA SOLA VEZ, para poblar el tablero. Después de eso,
el pipeline diario (sync.py) solo llena datos en las columnas ya creadas.

Requiere las variables de entorno MONDAY_API_TOKEN y MONDAY_BOARD_ID
(ya guardadas como GitHub Secrets).
"""
import json
import os
import time
import requests

MONDAY_API_TOKEN = os.environ["MONDAY_API_TOKEN"]
MONDAY_BOARD_ID = os.environ["MONDAY_BOARD_ID"]
MONDAY_API_URL = "https://api.monday.com/v2"

TYPE_MAP = {
    "Estado": "status",
    "Menú desplegable": "dropdown",
    "Números": "numbers",
    "Texto largo": "long_text",
}

KPI_COLUMNS = [
    ("Tipo de área", "Estado"), ("Estado", "Estado"), ("Municipio", "Estado"), ("Parroquia", "Estado"),
    ("Comunidad / Sector", "Texto largo"), ("Campamento", "Texto largo"), ("Tipo de campamento", "Estado"),
    ("Ubicación (mapa)", "Texto largo"), ("Clasificación de comunidad", "Estado"),
    ("Necesidades principales", "Menú desplegable"), ("Prioridad 1", "Estado"), ("Asistencia recibida", "Estado"),
    ("Brechas sin atender", "Menú desplegable"), ("Actores apoyando actualmente", "Menú desplegable"),
    ("Riesgo de duplicación", "Estado"), ("Familias (total)", "Números"), ("Personas (total)", "Números"),
    ("Familias afectadas", "Números"), ("Familias que no permanecen", "Números"),
    ("Edificaciones destruidas", "Menú desplegable"), ("Edificaciones dañadas", "Menú desplegable"),
    ("Viviendas dañadas (n.º)", "Números"), ("Apartamentos dañados (n.º)", "Números"),
    ("Servicios afectados", "Menú desplegable"), ("Riesgos terremoto/réplicas", "Menú desplegable"),
    ("Atención médica primaria activa", "Estado"), ("Principal necesidad de salud", "Menú desplegable"),
    ("Agua suficiente (comunidad)", "Estado"), ("Fuente de agua (comunidad)", "Estado"),
    ("Frecuencia de agua (comunidad)", "Estado"), ("Calidad de agua (comunidad)", "Estado"),
    ("Aguas negras / fugas", "Estado"), ("Vectores/enfermedades (comunidad)", "Menú desplegable"),
    ("Dificultad para obtener agua (comunidad)", "Estado"), ("Fuente de agua (campamento)", "Estado"),
    ("Agua suficiente (campamento)", "Estado"), ("Vectores/enfermedades (campamento)", "Menú desplegable"),
    ("Enfermedades reportadas (campamento)", "Menú desplegable"), ("Puntos de lavado de manos (campamento)", "Estado"),
    ("Estado de sanitarios (campamento)", "Estado"), ("Suficiencia de sanitarios (campamento)", "Estado"),
    ("Necesidades de alojamiento", "Menú desplegable"), ("Riesgo que impide el retorno", "Estado"),
    ("Familias que requieren alojamiento", "Números"), ("Intención de permanencia (campamento)", "Estado"),
    ("Acceso a mercados", "Estado"), ("Apoyo para reactivación económica", "Menú desplegable"),
    ("Riesgos de protección", "Menú desplegable"), ("Malestar emocional relevante",
