import streamlit as st
from sentence_transformers import SentenceTransformer
import requests as _requests
import csv, os, json, textwrap, time, requests
import numpy as np
from fpdf import FPDF

# =============================================================================
# CONFIGURACIÓN CENTRAL
# =============================================================================
CEREBRAS_MODEL = "qwen-3-235b-a22b-instruct-2507"
CEREBRAS_URL   = "https://api.cerebras.ai/v1/chat/completions"
# Modo coste cero: límites duros para evitar consumo excesivo de free tiers.
MAX_TOKENS_RESPUESTA  = 900
MAX_TOKENS_RAPIDO     = 300
MAX_CHARS_PREGUNTA    = 500
MAX_CHARS_CONTEXTO    = 18000
MAX_PREGUNTAS_SESION  = 10
MATCH_THRESHOLD_ALTO  = 0.40
MATCH_THRESHOLD_BAJO  = 0.25
MATCH_COUNT           = 8      # fragmentos finales enviados al LLM
MATCH_COUNT_RETRIEVAL = 40     # candidatos recuperados antes de reordenar
HISTORIAL_TURNOS      = 2
MAX_HISTORIAL_LOCAL   = 10
COLLECTION_NAME       = "normativa"

# =============================================================================
# CONFIGURACIÓN DE PÁGINA
# =============================================================================
st.set_page_config(page_title="Normativa Educativa CyL", page_icon="📚", layout="centered")

# =============================================================================
# SESSION STATE
# =============================================================================
_DEFAULTS = {
    "historial_completo": [], "ultima_pregunta": None,
    "ultima_respuesta": None, "ultimas_fuentes": [],
    "confirmar_borrar": False,
    "feedback_pendiente": False, "feedback_pregunta": None,
    "feedback_respuesta": None, "pregunta_actual": "",
    "consultas_sesion": 0,
}
for _k, _v in _DEFAULTS.items():
    if _k not in st.session_state:
        st.session_state[_k] = _v

# =============================================================================
# PDF
# =============================================================================
_UNICODE_FIX = {
    "\u2018":"'", "\u2019":"'", "\u201C":'"', "\u201D":'"',
    "\u2013":"-", "\u2014":"-", "\u2022":"-", "\u00B7":"-",
    "\u2026":"...", "\u00A0":" ", "\u00AD":"-",
}

def _limpiar(texto):
    for orig, repl in _UNICODE_FIX.items():
        texto = texto.replace(orig, repl)
    return texto.encode("latin-1", "replace").decode("latin-1")

def generar_pdf(lista_interacciones, titulo="Normativa Educativa"):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, _limpiar(titulo), ln=True, align="C")
    pdf.ln(8)
    for item in lista_interacciones:
        pdf.set_font("Helvetica", "B", 12)
        for linea in textwrap.wrap(f"PREGUNTA: {_limpiar(item['pregunta'])}", 80):
            pdf.cell(0, 6, linea, ln=True)
        corr = item.get("pregunta_corregida", "")
        if corr and corr.strip().lower() != item["pregunta"].strip().lower():
            pdf.set_font("Helvetica", "I", 10)
            pdf.cell(0, 5, _limpiar(f"(Corregida a: {corr})"), ln=True)
        pdf.ln(2)
        pdf.set_font("Helvetica", size=11)
        for linea in textwrap.wrap(_limpiar(item["respuesta"]), 90):
            pdf.cell(0, 6, linea, ln=True)
        pdf.ln(4)
        pdf.set_font("Helvetica", "I", 10)
        pdf.cell(0, 5, "FUENTES CONSULTADAS:", ln=True)
        for fuente in item.get("fuentes", []):
            for linea in textwrap.wrap(f"- {_limpiar(fuente)}", 90):
                pdf.cell(0, 5, linea, ln=True)
        pdf.ln(8)
    return bytes(pdf.output())

# =============================================================================
# CLAVES Y SERVICIOS
# =============================================================================
CEREBRAS_API_KEY = st.secrets["CEREBRAS_API_KEY"]
QDRANT_URL    = st.secrets["QDRANT_URL"]
QDRANT_API_KEY = st.secrets["QDRANT_API_KEY"]

@st.cache_resource
def load_model():
    # ⚠️ NO cambiar sin re-vectorizar los documentos en Qdrant.
    return SentenceTransformer("intfloat/multilingual-e5-base")

@st.cache_data
def cargar_enlaces():
    """Carga el diccionario nombre_archivo → URL desde enlaces.csv.
    Usa utf-8-sig para manejar el BOM que tiene el fichero.
    Busca el fichero en varias ubicaciones posibles.
    """
    enlaces = {}
    rutas_posibles = ["enlaces.csv", "normativa_educativa/enlaces.csv", "/app/enlaces.csv"]
    ruta_encontrada = None
    for ruta in rutas_posibles:
        if os.path.exists(ruta):
            ruta_encontrada = ruta
            break
    if ruta_encontrada is None:
        return enlaces
    try:
        with open(ruta_encontrada, encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for fila in reader:
                nombre = (fila.get("nombre_archivo") or "").strip()
                url    = (fila.get("url_oficial_verificada") or "").strip()
                if nombre and url:
                    enlaces[nombre] = url
    except Exception:
        # Fallback: lectura posicional
        try:
            with open(ruta_encontrada, encoding="utf-8-sig") as f:
                for i, fila in enumerate(csv.reader(f)):
                    if i == 0:
                        continue
                    if len(fila) >= 2 and fila[0].strip() and fila[1].strip():
                        enlaces[fila[0].strip()] = fila[1].strip()
        except Exception:
            pass
    return enlaces

model        = load_model()
# Cerebras usa requests directamente — sin cliente especial
enlaces      = cargar_enlaces()
if not enlaces:
    st.sidebar.warning("⚠️ enlaces.csv no encontrado — las fuentes no tendrán enlace.")

# =============================================================================
# FUNCIONES AUXILIARES
# =============================================================================

def _parse_json(text, default):
    text = text.strip()
    if "```" in text:
        partes = text.split("```")
        text = partes[1] if len(partes) > 1 else partes[0]
        if text.startswith("json"):
            text = text[4:]
    try:
        return json.loads(text.strip())
    except Exception:
        return default

def validar_input(pregunta):
    if not pregunta or not pregunta.strip():
        return False, "La pregunta no puede estar vacía."
    if len(pregunta) > MAX_CHARS_PREGUNTA:
        return False, f"Pregunta demasiado larga (máximo {MAX_CHARS_PREGUNTA} caracteres)."
    patrones = ["ignore previous", "ignora las instrucciones", "system:", "</s>", "[inst]", "###"]
    if any(p in pregunta.lower() for p in patrones):
        return False, "La pregunta contiene contenido no válido."
    return True, ""

def expandir_y_corregir(pregunta):
    """Sin LLM para ahorrar tokens de Cerebras.
    La búsqueda semántica + reordenación local mantiene el coste en cero.
    """
    import re
    corregida = pregunta.strip()
    # Limpiar signos de interrogación y espacios extra
    base = re.sub(r"[¿?¡!]", "", corregida).strip()
    return corregida, [base]


# Stopwords españolas para extracción de términos clave
_STOPWORDS = {
    "qué","cuál","cuáles","cómo","cuándo","cuánto","cuántos","cuántas",
    "dónde","quién","quiénes","por","para","con","sin","sobre","entre",
    "desde","hasta","hacia","ante","bajo","según","durante","mediante",
    "un","una","unos","unas","el","la","los","las","del","al",
    "es","son","está","están","ser","tener","tiene","tienen","haber",
    "hay","puede","pueden","debe","deben","se","me","te","le","nos",
    "de","en","a","y","o","e","u","que","si","no","más","pero",
    "yo","tú","él","ella","usted","nosotros","ellos","su","sus",
    "mi","mis","tu","tus","un","una","lo","le","les",
    "docente","docentes","alumno","alumna","alumnos","alumnas",
    "derecho","derechos","tiene","tendrá","podrá","podrán",
    "favor","hacer","realizar","solicitar","pedir",
}

def extraer_terminos_clave(pregunta: str) -> list[str]:
    """Extrae 4-6 términos clave de la pregunta eliminando stopwords.
    Devuelve también bigramas de términos legales relevantes.
    """
    import re
    # Normalizar
    texto = pregunta.lower().strip("¿?.,;:")
    texto = re.sub(r"[¿?.,;:()\.\[\]{}!]", " ", texto)
    palabras = [p for p in texto.split() if len(p) > 2 and p not in _STOPWORDS]

    terminos = []
    # Añadir palabras individuales relevantes
    for p in palabras:
        if p not in terminos:
            terminos.append(p)

    # Añadir bigramas de palabras consecutivas
    for i in range(len(palabras) - 1):
        bigrama = f"{palabras[i]} {palabras[i+1]}"
        if bigrama not in terminos:
            terminos.append(bigrama)

    return terminos[:8]  # máx 8 términos/bigramas

def _qdrant_search_rest(embedding, bloque=None, threshold=None, limit=MATCH_COUNT_RETRIEVAL):
    """Búsqueda semántica via REST API directa.

    En modo coste cero y con los bloques actuales pendientes de depuración,
    NO usamos filtro duro por nivel educativo. Recuperamos candidatos de toda
    la colección y después los reordenamos localmente, dando bonus al bloque
    elegido cuando coincide.
    """
    url = f"{QDRANT_URL}/collections/{COLLECTION_NAME}/points/search"
    headers = {"api-key": QDRANT_API_KEY, "Content-Type": "application/json"}
    if hasattr(embedding, 'tolist'):
        embedding = embedding.tolist()
    embedding = [float(x) for x in embedding]
    payload = {
        "vector": embedding,
        "limit": limit,
        "with_payload": True,
    }
    # Importante: no aplicar filtro por bloque aquí. El bloque actual se usa
    # como preferencia en el reranking local, no como exclusión.
    if threshold is not None:
        payload["score_threshold"] = threshold
    try:
        r = requests.post(url, json=payload, headers=headers, timeout=30)
        r.raise_for_status()
        return r.json().get("result", [])
    except Exception:
        return []

def _qdrant_text_search_rest(pregunta_texto, bloque=None, terminos=None):
    """Búsqueda textual desactivada como consulta remota.

    La colección actual no tiene indexado el campo `contenido` para búsqueda
    textual. Para mantener coste cero y evitar consultas lentas o frágiles,
    hacemos la parte léxica en Python sobre los candidatos vectoriales.
    """
    return []

def _normalizar_score(score):
    try:
        return float(score or 0.0)
    except Exception:
        return 0.0


def _score_lexico(contenido: str, terminos: list[str]) -> float:
    """Puntuación léxica local, sin APIs ni coste.

    Da un pequeño bonus cuando los términos de la pregunta aparecen literalmente
    en el fragmento. Está acotada para que no eclipse la similitud vectorial.
    """
    if not contenido or not terminos:
        return 0.0
    texto = contenido.lower()
    score = 0.0
    for termino in terminos:
        t = termino.lower().strip()
        if not t:
            continue
        if " " in t and t in texto:
            score += 0.08
        elif t in texto:
            score += 0.035
    return min(score, 0.25)


def _bonus_bloque(payload: dict, bloque: str) -> float:
    """Usa el nivel educativo como preferencia, no como filtro excluyente."""
    if not bloque or bloque == "general":
        return 0.0
    return 0.06 if payload.get("bloque") == bloque else 0.0


def buscar_normativa_hibrida(embedding, pregunta_texto, bloque):
    """Búsqueda semántica + reordenación local de coste cero.

    Cambio clave: el nivel educativo ya no excluye documentos. Primero se
    recuperan candidatos de toda la colección y después se da prioridad a los
    fragmentos cuyo `bloque` coincide. Esto evita perder normativa relevante
    mientras se corrigen los metadatos de Qdrant.
    """
    terminos_clave = extraer_terminos_clave(pregunta_texto)

    resultados_v = []
    for threshold in [MATCH_THRESHOLD_ALTO, MATCH_THRESHOLD_BAJO, None]:
        hits = _qdrant_search_rest(
            embedding,
            bloque=None,
            threshold=threshold,
            limit=MATCH_COUNT_RETRIEVAL,
        )
        resultados_v = hits
        if len(resultados_v) >= MATCH_COUNT:
            break

    vistos_contenido = set()
    ids_vistos = set()
    combinados = []

    for hit in resultados_v:
        rid = str(hit.get("id", ""))
        payload = hit.get("payload", {}) or {}
        contenido = payload.get("contenido", "")
        clave = contenido[:160].strip()
        if rid in ids_vistos or (clave and clave in vistos_contenido):
            continue
        ids_vistos.add(rid)
        if clave:
            vistos_contenido.add(clave)

        base = _normalizar_score(hit.get("score", 0.0))
        lexical = _score_lexico(contenido, terminos_clave)
        bloque_bonus = _bonus_bloque(payload, bloque)
        score_final = base + lexical + bloque_bonus

        combinados.append({
            "id": rid,
            "contenido": contenido,
            "nombre_archivo": payload.get("nombre_archivo", ""),
            "pagina_num": payload.get("pagina_num", 0),
            "bloque": payload.get("bloque", ""),
            "similarity": score_final,
            "score_vectorial": base,
            "score_lexico": lexical,
            "bonus_bloque": bloque_bonus,
        })

    combinados = sorted(combinados, key=lambda x: x.get("similarity", 0), reverse=True)
    return combinados[:MATCH_COUNT]


def reranquear(pregunta, fragmentos):
    """Reordenación final local. No usa APIs externas ni genera coste."""
    return sorted(fragmentos, key=lambda x: x.get("similarity", 0), reverse=True)


def recortar_contexto_xml(contexto_xml: str, max_chars: int = MAX_CHARS_CONTEXTO) -> str:
    """Límite duro de contexto para proteger el free tier de Cerebras."""
    if len(contexto_xml) <= max_chars:
        return contexto_xml
    return contexto_xml[:max_chars] + "\n\n[CONTEXTO RECORTADO POR LÍMITE GRATUITO DE LA APP]"

def construir_contexto_xml(fragmentos, enlaces_dict):
    contexto_xml = ""
    links_screen = []
    fuentes_pdf  = []
    for i, res in enumerate(fragmentos, 1):
        nombre   = res.get("nombre_archivo", "")
        pagina   = res.get("pagina_num", "")
        score    = res.get("similarity", "")
        nombre_l = nombre.replace(".pdf", "").replace("_", " ")
        score_s  = f"{score:.2f}" if isinstance(score, float) else ""
        contexto_xml += (
            f'<fragmento id="{i}" documento="{nombre_l}" '
            f'pagina="{pagina}" relevancia="{score_s}">\n'
            f'{res.get("contenido", "")}\n</fragmento>\n\n'
        )
        url = enlaces_dict.get(nombre)
        if url:
            # #page=N abre el PDF directamente en la página indicada en la mayoría de navegadores
            link = f"{url}#page={pagina}"
            links_screen.append(f"[{nombre_l} — pág. {pagina}]({link})")
            fuentes_pdf.append(f"{nombre_l} (Pág. {pagina}) — {url}")
        else:
            links_screen.append(f"**{nombre_l}** — pág. {pagina} *(enlace no disponible)*")
            fuentes_pdf.append(f"{nombre_l} (Pág. {pagina})")
    return contexto_xml, links_screen, fuentes_pdf

def construir_mensajes(pregunta, contexto_xml):
    PROMPT_SISTEMA = """\
Eres un asesor jurídico experto en normativa educativa española \
(legislación estatal y de Castilla y León).

FUENTES DE INFORMACIÓN:
Dispones de dos fuentes:
1. FRAGMENTOS NORMATIVOS: los <fragmento> proporcionados con el contexto.
2. CONOCIMIENTO JURÍDICO PROPIO: tu formación en derecho educativo español.

REGLAS:
- Usa SIEMPRE los fragmentos como fuente principal.
- Si los fragmentos contienen la respuesta, cítala con documento y página exactos.
- Si los fragmentos son parciales o insuficientes, COMPLETA con tu conocimiento jurídico general pero indícalo claramente con: *(información general — verifica en la normativa oficial)*
- NUNCA inventes artículos concretos ni números específicos que no estén en los fragmentos.
- Cita el documento y la página de cada afirmación que extraigas de los fragmentos.

REGLAS DE FORMATO OBLIGATORIAS:
- Usa ## y ### para estructurar secciones.
- Cuando haya varios casos (distintos días según parentesco, distintos plazos...) usa SIEMPRE una tabla Markdown.
- Para listas de requisitos o pasos usa viñetas con guion (-).
- Lenguaje claro y accesible para docentes, sin jerga innecesaria.
- Respuestas completas y detalladas — nunca cortes por brevedad.

ESTRUCTURA OBLIGATORIA:

## Respuesta
[respuesta directa, clara y completa — mínimo 4-5 frases con todo el detalle relevante]

## Normativa aplicable
[tabla o lista con artículos, documentos y páginas — todos los casos relevantes]

## Qué debes hacer
[pasos concretos y prácticos para el docente, familia o equipo directivo]

---
EJEMPLO:

Pregunta: ¿Cuántos días de permiso tiene un docente por fallecimiento de familiar?

## Respuesta
Los docentes funcionarios tienen derecho a permiso retribuido por fallecimiento,
accidente o enfermedad grave de un familiar. La duración varía según el grado
de parentesco y si se requiere desplazamiento fuera de la localidad.
Este derecho está reconocido tanto en la normativa estatal (EBEP) como en los
acuerdos de función pública de Castilla y León.

## Normativa aplicable

| Parentesco | Sin desplazamiento | Con desplazamiento |
|---|---|---|
| 1er grado: cónyuge, hijos, padres | 3 días hábiles | 5 días hábiles |
| 2º grado: hermanos, abuelos, nietos, suegros | 2 días hábiles | 4 días hábiles |

Fuente: EBEP, RD Legislativo 5/2015, artículo 48.a) — pág. 14

## Qué debes hacer
- Comunica el permiso a la dirección del centro lo antes posible.
- Aporta el certificado de defunción o el parte médico al reincorporarte.
- Los días cuentan como **hábiles**: no se incluyen fines de semana ni festivos.
- Si hay desplazamiento, guarda los justificantes de viaje por si se requieren."""

    mensajes = [{"role": "system", "content": PROMPT_SISTEMA}]
    ultimos = st.session_state.historial_completo[-HISTORIAL_TURNOS:]
    for turno in ultimos:
        resp_prev = turno["respuesta"]
        if len(resp_prev) > 1200:
            resp_prev = resp_prev[:1200] + "..."
        mensajes.append({"role": "user",      "content": turno["pregunta"]})
        mensajes.append({"role": "assistant", "content": resp_prev})
    mensajes.append({
        "role": "user",
        "content": f"CONTEXTO NORMATIVO:\n{contexto_xml}\n\nPREGUNTA: {pregunta}",
    })
    return mensajes

def guardar_log(bloque, preg_orig, preg_corr, num_res, tiempo_ms, tiene_resp):
    """Logging desactivado para mantener coste 0 y minimizar riesgos RGPD.

    No se guardan preguntas, respuestas ni metadatos en bases de datos externas.
    """
    return None


def guardar_feedback(pregunta, respuesta, util):
    """Feedback no persistente: no se envía a bases de datos externas ni a terceros."""
    return None

# =============================================================================
# INTERFAZ — BARRA LATERAL
# =============================================================================
with st.sidebar:
    st.markdown("### 📊 Sesión actual")
    st.caption(f"Consultas usadas: {st.session_state.consultas_sesion}/{MAX_PREGUNTAS_SESION}")
    if st.session_state.historial_completo:
        st.caption(f"Consultas en historial local: {len(st.session_state.historial_completo)}")
    st.info("Modo coste 0: no se guardan preguntas ni respuestas en bases de datos externas.")

# =============================================================================
# INTERFAZ — CUERPO PRINCIPAL
# =============================================================================
st.title("📚 Buscador Inteligente de Normativa Educativa")

st.warning(
    "No introduzcas nombres, DNI, expedientes, datos médicos, sanciones ni "
    "información que permita identificar a alumnos, familias, docentes u otras personas. "
    "La app no guarda tus preguntas en bases de datos externas, pero la consulta se envía "
    "al proveedor gratuito del modelo de IA para generar la respuesta."
)

bloque_elegido = st.selectbox(
    "Nivel educativo:",
    ["ninguno", "general", "infantil_primaria", "secundaria_bachillerato", "fp"],
    format_func=lambda x: {
        "ninguno":                 "— Selecciona un nivel educativo —",
        "general":                 "📋 General (permisos, bajas, vacaciones, EBEP...)",
        "infantil_primaria":       "🧒 Infantil y Primaria",
        "secundaria_bachillerato": "🎓 Secundaria y Bachillerato",
        "fp":                      "🔧 Formación Profesional",
    }[x],
)


with st.form(key="form_busqueda"):
    pregunta_input = st.text_area(
        "Haz tu pregunta sobre la normativa:",
        value=st.session_state.get("pregunta_actual", ""),
        height=100, max_chars=MAX_CHARS_PREGUNTA,
        placeholder="Escribe tu consulta sobre normativa educativa...",
    )
    submit = st.form_submit_button("🔍 Buscar", use_container_width=True)

# =============================================================================
# PROCESAMIENTO
# =============================================================================
if submit and pregunta_input:

    if bloque_elegido == "ninguno":
        st.warning("⚠️ Selecciona un nivel educativo antes de buscar.")

    elif st.session_state.consultas_sesion >= MAX_PREGUNTAS_SESION:
        st.error(
            "Se ha alcanzado el límite gratuito de consultas de esta sesión. "
            "Vuelve más tarde para seguir usando la app sin coste."
        )

    else:
        valido, msg_error = validar_input(pregunta_input)
        if not valido:
            st.warning(f"⚠️ {msg_error}")
        else:
            try:
                t0 = time.time()

                with st.spinner("✏️ Analizando la consulta..."):
                    pregunta_corregida, reformulaciones = expandir_y_corregir(pregunta_input)

                if pregunta_corregida.strip().lower() != pregunta_input.strip().lower():
                    st.info(f"✏️ He corregido tu consulta a: **{pregunta_corregida}**")

                with st.spinner("🔎 Buscando en la normativa..."):
                    # e5 requiere prefijo "query: " en las consultas
                    todas = [pregunta_corregida] + reformulaciones[:2]
                    embedding_avg = np.mean(
                        [model.encode('query: ' + q, normalize_embeddings=True)
                         for q in todas], axis=0
                    ).tolist()
                    resultados = buscar_normativa_hibrida(
                        embedding_avg, pregunta_corregida, bloque_elegido
                    )

                if not resultados:
                    st.warning("No encontré normativa relacionada. Prueba a reformular la pregunta.")
                    guardar_log(bloque_elegido, pregunta_input, pregunta_corregida,
                                0, (time.time()-t0)*1000, False)
                else:
                    with st.spinner("📊 Ordenando por relevancia..."):
                        resultados = reranquear(pregunta_corregida, resultados)
                        resultados = resultados[:MATCH_COUNT]

                    contexto_xml, links_screen, fuentes_pdf = construir_contexto_xml(
                        resultados, enlaces
                    )
                    contexto_xml = recortar_contexto_xml(contexto_xml)
                    mensajes = construir_mensajes(pregunta_corregida, contexto_xml)

                    st.write("---")
                    st.markdown("### 📝 Respuesta:")

                    _resp = _requests.post(
                        CEREBRAS_URL,
                        headers={"Authorization": f"Bearer {CEREBRAS_API_KEY}",
                                 "Content-Type": "application/json"},
                        json={"model": CEREBRAS_MODEL,
                              "messages": mensajes,
                              "temperature": 0.1,
                              "max_tokens": MAX_TOKENS_RESPUESTA},
                        timeout=60
                    )
                    _resp.raise_for_status()
                    texto_final = _resp.json()["choices"][0]["message"]["content"]
                    st.markdown(texto_final)

                    fuentes_u  = list(dict.fromkeys(links_screen))
                    fuentes_up = list(dict.fromkeys(fuentes_pdf))
                    st.markdown("### 📚 Fuentes consultadas:")
                    for f in fuentes_u:
                        st.markdown(f"- 📄 {f}", unsafe_allow_html=False)

                    st.session_state.consultas_sesion += 1
                    st.session_state.ultima_pregunta   = pregunta_input
                    st.session_state.pregunta_actual   = pregunta_input
                    st.session_state.ultima_respuesta  = texto_final
                    st.session_state.ultimas_fuentes   = fuentes_u
                    st.session_state.historial_completo.append({
                        "pregunta":           pregunta_input,
                        "pregunta_corregida": pregunta_corregida,
                        "respuesta":          texto_final,
                        "fuentes":            fuentes_up,
                    })
                    if len(st.session_state.historial_completo) > MAX_HISTORIAL_LOCAL:
                        st.session_state.historial_completo =                             st.session_state.historial_completo[-MAX_HISTORIAL_LOCAL:]

                    st.session_state.feedback_pendiente = True
                    st.session_state.feedback_pregunta  = pregunta_input
                    st.session_state.feedback_respuesta = texto_final

                    guardar_log(bloque_elegido, pregunta_input, pregunta_corregida,
                                len(resultados), (time.time()-t0)*1000, True)

            except Exception as e:
                err = str(e).lower()
                if "429" in err or "quota" in err or "exhausted" in err or "rate" in err:
                    st.error("⏳ Límite gratuito diario de Cerebras alcanzado. Inténtalo mañana.")
                elif "api_key" in err or "invalid" in err:
                    st.error("❌ Error en la API de Cerebras. Revisa tu API key en los Secrets de Streamlit.")
                else:
                    st.error(f"Error técnico: {e}")

elif st.session_state.ultima_respuesta:
    st.write("---")
    st.markdown(st.session_state.ultima_respuesta)
    st.markdown("### 📚 Fuentes consultadas:")
    for f in st.session_state.ultimas_fuentes:
        st.markdown(f"- 📄 {f}", unsafe_allow_html=False)

# =============================================================================
# FEEDBACK
# =============================================================================
if st.session_state.feedback_pendiente:
    st.markdown("---")
    st.markdown("**¿Te ha resultado útil esta respuesta?**")
    c1, c2, c3 = st.columns([1, 1, 5])
    with c1:
        if st.button("👍 Sí"):
            guardar_feedback(st.session_state.feedback_pregunta,
                             st.session_state.feedback_respuesta, True)
            st.session_state.feedback_pendiente = False
            st.success("¡Gracias! Feedback recibido solo en esta sesión; no se guarda en base de datos.")
            st.rerun()
    with c2:
        if st.button("👎 No"):
            guardar_feedback(st.session_state.feedback_pregunta,
                             st.session_state.feedback_respuesta, False)
            st.session_state.feedback_pendiente = False
            st.info("Gracias. Feedback recibido solo en esta sesión; no se guarda en base de datos.")
            st.rerun()

# =============================================================================
# HISTORIAL EN PANTALLA
# =============================================================================
historial = st.session_state.historial_completo
if len(historial) > 1:
    st.write("---")
    with st.expander(f"📋 Historial ({len(historial)} consultas)", expanded=False):
        for item in reversed(historial[:-1]):
            st.markdown(f"**Pregunta:** {item['pregunta']}")
            prev = item["respuesta"]
            st.markdown(prev[:400] + "..." if len(prev) > 400 else prev)
            st.divider()

# =============================================================================
# BOTONES DE ACCIÓN
# =============================================================================
if historial:
    st.write("---")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.download_button("📄 Descargar esta consulta",
            data=generar_pdf([historial[-1]], "Consulta de Normativa Educativa"),
            file_name="consulta_normativa.pdf", mime="application/pdf",
            use_container_width=True)
    with c2:
        st.download_button("📚 Descargar historial",
            data=generar_pdf(historial, "Historial Completo"),
            file_name="historial_normativa.pdf", mime="application/pdf",
            use_container_width=True)
    with c3:
        if not st.session_state.confirmar_borrar:
            if st.button("🔄 Reiniciar chat", use_container_width=True):
                st.session_state.confirmar_borrar = True
                st.rerun()
        else:
            st.warning("⚠️ ¿Seguro? Se borrará todo el historial.")
            ca, cb = st.columns(2)
            with ca:
                if st.button("✅ Sí, borrar", use_container_width=True):
                    consultas_usadas = st.session_state.get("consultas_sesion", 0)
                    for k, v in _DEFAULTS.items():
                        st.session_state[k] = ([] if isinstance(v, list) else v)
                    # Reiniciar el chat no reinicia el contador de uso del free tier.
                    st.session_state.consultas_sesion = consultas_usadas
                    st.rerun()
            with cb:
                if st.button("❌ Cancelar", use_container_width=True):
                    st.session_state.confirmar_borrar = False
                    st.rerun()
