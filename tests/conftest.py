import sys
import types

if 'streamlit' not in sys.modules:
    st = types.ModuleType('streamlit')
    st.session_state = {}
    st.error = lambda *a, **k: None
    st.info = lambda *a, **k: None
    st.caption = lambda *a, **k: None
    sys.modules['streamlit'] = st
