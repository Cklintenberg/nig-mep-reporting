"""Navigation for the working report workflow and fictional expansion previews."""
import streamlit as st
from branding import logo


def select_page(page):
    st.session_state['workspace_page']=page


def active(label, icon, preview=False):
    selected=st.session_state['workspace_page']==label
    st.button(label,icon=f':material/{icon}:',key='nav_'+label,type='primary' if selected else 'secondary',
              use_container_width=True,on_click=select_page,args=(label,))


def render_sidebar():
    st.session_state.setdefault('workspace_page','Overview')
    with st.sidebar:
        with st.container(key='sidebar_nav'):
            st.markdown('<div class="sidebar-brand nig-brand">'+logo('NIG',130)+'<span class="brand-context">MEP · Partner workspace</span></div>',unsafe_allow_html=True)
            active('Search workspace','search',preview=True)
            active('Overview','home')
            active('Weekly report','description')
            st.markdown('<div class="nav-group-title">Portfolio</div>',unsafe_allow_html=True)
            active('Applications','apps',preview=True)
            active('Customers','group',preview=True)
            active('Partners','handshake',preview=True)
            st.markdown('<div class="nav-group-title">Operations</div>',unsafe_allow_html=True)
            active('Meetings','calendar_month',preview=True)
            active('Insights & forecasts','monitoring',preview=True)
            active('Report library','folder_open')
            active('Integrations','extension',preview=True)
            st.markdown('<div class="nav-group-title">Workspace</div>',unsafe_allow_html=True)
            active('Model comparison','compare_arrows')
            active('Design & scope','architecture')
            active('Settings','settings',preview=True)
            st.markdown('<div class="sidebar-scope">Mock pages use fictional data.<br>Reporting and the library are working features.</div><div class="sidebar-account"><div class="account-avatar">N</div><div><strong>NIG</strong><span>Business Development</span></div></div><div class="sidebar-fiction">FICTIONAL CASE STUDY · ZURICH</div>',unsafe_allow_html=True)
    return st.session_state['workspace_page']
