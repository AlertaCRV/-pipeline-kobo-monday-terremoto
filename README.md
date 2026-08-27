# Pipeline Kobo → Monday — CRV, diagnóstico terremoto 2026

Sincroniza automáticamente las evaluaciones de terreno (KoboToolbox) hacia el
tablero de Monday.com, calculando en el camino el score de **Urgencia ×
Factibilidad operativa** que se calibró y confirmó en
`Matriz_Urgencia_Factibilidad_v2_definitivo.xlsx`.

**Este código no requiere ninguna IA para ejecutarse.** Es lógica fija (las
mismas fórmulas del Excel, traducidas a Python) que corre sola, en un
horario programado, sin intervención humana ni de ningún modelo de lenguaje.

## Qué hace cada archivo

| Archivo | Función |
|---|---|
| `src/config.py` | Lee credenciales desde variables de entorno / GitHub Secrets. Nunca contiene claves reales. |
| `src/kobo_client.py` | Obtiene submissions nuevas de Kobo (o del fixture ficticio si `DRY_RUN=true`). |
| `src/transform.py` | Aplana la submission y se queda solo con los 61 campos confirmados como KPI. |
| `src/scoring.py` | Calcula Urgencia, Factibilidad y Cuadrante, usando los pesos de `scoring_config.json`. |
| `src/monday_client.py` | Crea/actualiza el ítem correspondiente en el tablero de Monday. |
| `src/sync.py` | Orquesta todo lo anterior. Es el script que se ejecuta cada corrida. |
| `src/kpi_fields.json` | Los 61 campos confirmados, extraídos directamente de `Mapeo_Kobo_Monday_v9.xlsx`. |
| `src/scoring_config.json` | Pesos y umbrales, extraídos directamente del Excel de calibración ya bloqueado. |
| `tests/fixtures/sample_submissions.json` | 5 evaluaciones ficticias (marcadas `FICTICIO`), usadas para probar sin datos reales. |
| `.github/workflows/sync-kobo-monday.yml` | Corre `sync.py` automáticamente todos los días a las 6:00 a.m. (hora Venezuela). |

## Cómo probarlo ahora mismo (sin credenciales)

```bash
cd src
python sync.py
```

Por defecto `DRY_RUN=true`, así que usa los 5 registros ficticios y solo
**imprime** lo que enviaría a Monday — no llama a ninguna API real.

## Qué falta para pasar a producción

1. **Crear el tablero real en Monday** con las 61 columnas de
   `Especificacion_Columnas_Monday_v1.xlsx` (más las 4 columnas del score:
   Puntos/Nivel Urgencia, Puntos/Nivel Factibilidad, Cuadrante).
2. **Completar `MONDAY_COLUMN_MAP`** en `src/config.py` con los IDs reales de
   esas columnas (se obtienen desde la interfaz de Monday o vía su API).
3. **Completar la traducción código → etiqueta** en `transform.py`: Kobo
   real devuelve códigos (`"alta"`) en vez de las etiquetas que usa
   `scoring.py` (`"Alta"`). El diccionario de equivalencias sale de la hoja
   `choices` del formulario Kobo (ya la tenemos mapeada en este chat).
4. **Configurar los 4 GitHub Secrets**: `KOBO_API_TOKEN`, `KOBO_ASSET_UID`,
   `MONDAY_API_TOKEN`, `MONDAY_BOARD_ID`.
5. Cambiar `DRY_RUN` a `false` (ya está así por defecto en el workflow de
   GitHub Actions — solo afecta si lo corres localmente).

Ninguno de estos pasos requiere volver a usar Claude — son configuración
estándar de Kobo, Monday y GitHub.
