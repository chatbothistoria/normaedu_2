import streamlit as st
import hmac

st.set_page_config(page_title="Administración - NormaEdu 2", page_icon="🔐")

def _ocultar_navegacion_multipagina():
    st.markdown(
        """
        <style>
        [data-testid="stSidebarNav"] {
            display: none !important;
        }
        section[data-testid="stSidebar"] nav {
            display: none !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

_ocultar_navegacion_multipagina()


def _leer_secreto(nombre: str, default=None):
    try:
        return st.secrets[nombre]
    except Exception:
        return default

ADMIN_DIAGNOSTIC_KEY = _leer_secreto("ADMIN_DIAGNOSTIC_KEY")

st.title("🔐 Administración")
st.caption("Acceso privado para activar herramientas de diagnóstico en esta sesión.")

if not ADMIN_DIAGNOSTIC_KEY:
    st.warning("El acceso de administración no está configurado. Añade ADMIN_DIAGNOSTIC_KEY en los Secrets.")
else:
    clave = st.text_input("Clave de administrador", type="password")

    if clave:
        if hmac.compare_digest(str(clave), str(ADMIN_DIAGNOSTIC_KEY)):
            st.session_state.admin_diagnostico_ok = True
            st.session_state.modo_diagnostico = True
            st.success("Acceso administrador activo. Vuelve a la app principal y activa/consulta el modo diagnóstico.")
            st.page_link("app.py", label="Volver a NormaEdu 2", icon="🏠")
        else:
            st.session_state.admin_diagnostico_ok = False
            st.session_state.modo_diagnostico = False
            st.error("Clave de administrador incorrecta.")

st.divider()
st.info("Los usuarios normales no ven el botón de diagnóstico en la app principal. Esta página solo sirve para activar el diagnóstico en tu sesión.")
