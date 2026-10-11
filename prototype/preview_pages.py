"""Interactive fictional workspace previews, isolated from the reporting workflow."""
import json
from pathlib import Path
import pandas as pd
import streamlit as st
from html import escape
from branding import logo
from meeting_calendar import render_calendar

ROOT=Path(__file__).resolve().parent
PAGES={'Search workspace','Applications','Customers','Partners','Meetings','Insights & forecasts','Integrations','Settings'}


def navigate(page):
    st.session_state['workspace_page']=page


def kpis(items):
    for col,(label,value) in zip(st.columns(len(items)),items):
        col.metric(label,value)


def table(rows):
    st.dataframe(pd.DataFrame(rows),hide_index=True,use_container_width=True)


def render_preview(page):
    data=json.loads((ROOT/'sample_data/workspace_preview.json').read_text())
    portfolio=json.loads((ROOT/'sample_data/portfolio.json').read_text())
    st.markdown('<div class="eyebrow">MEP / WORKSPACE PREVIEW</div>',unsafe_allow_html=True)
    st.title(page)
    st.caption('MOCK UI · Fictional data · Snapshot: week of 28 September 2026. Preview controls affect this demo only; they do not change reports or connect external services.')
    if page=='Applications':
        apps=data['applications']
        kpis([('Published applications',len(apps)),('Categories',6),('Partner listings',sum(len(a['Partners']) for a in apps)),('Review items',3)])
        st.subheader('Application directory')
        a,b=st.columns([2,1]);q=a.text_input('Find an application',placeholder='Search name or provider…')
        category=b.selectbox('Category',['All categories']+sorted({x['Category'] for x in apps}))
        shown=[x for x in apps if q.casefold() in (x['Application']+' '+x['Provider']).casefold() and (category=='All categories' or category==x['Category'])]
        if not shown: st.info('No applications match these filters.');return
        table([{**x,'Partners':', '.join(x['Partners'])} for x in shown])
        selected=st.selectbox('Application details',[x['Application'] for x in shown])
        item=next(x for x in shown if x['Application']==selected)
        with st.container(border=True):
            st.subheader(selected);st.write(f"{item['Provider']} · {item['Category']} · {item['Status']}")
            st.write('Distributed through '+', '.join(item['Partners']))
            count=sum(c['Primary application']==selected for c in data['customers'])
            st.metric('Customers with this as primary app',count)
            st.caption('Primary application is an illustrative customer assignment, not total installations or active users.')
            st.write('Next conversation: '+item['Review'])
        st.caption(f'{len(shown)} of 48 applications shown. Partner listings overlap; they are not distinct applications.')
    elif page=='Customers':
        customers=data['customers'];active=sum(c['Stage']=='Active' for c in customers)
        kpis([('Business customers',len(customers)),('Active accounts',active),('Onboarding',len(customers)-active),('Regions',2)])
        a,b=st.columns([2,1]);q=a.text_input('Find a customer',placeholder='Search company name…')
        partner=b.selectbox('Distribution partner',['All partners']+[p['Partner'] for p in portfolio['partners']])
        shown=[c for c in customers if q.casefold() in c['Customer'].casefold() and (partner=='All partners' or partner==c['Partner'])]
        st.subheader('Customer directory')
        if not shown: st.info('No customers match these filters.');return
        table(shown)
        chosen=st.selectbox('Customer details',[c['Customer'] for c in shown]);c=next(c for c in shown if c['Customer']==chosen)
        with st.container(border=True):
            st.subheader(chosen);st.write(f"{c['Sector']} · {c['Region']} · {c['Stage']}")
            st.write(f"Partner: {c['Partner']} · BD owner: {c['Owner']}")
            st.write('Primary application: '+c['Primary application'])
            st.caption('Fictional organisation. Contact details, contracts and personal information are not included.')
    elif page=='Partners':
        kpis([('Current partners',4),('Three-year ambition',10),('Business customers',312),('Regions',2)])
        st.subheader('Distribution network');table(portfolio['partners'])
        chosen=st.selectbox('Partner profile',[p['Partner'] for p in portfolio['partners']]);p=next(p for p in portfolio['partners'] if p['Partner']==chosen)
        left,right=st.columns([1.4,1])
        with left,st.container(border=True):
            st.subheader(chosen);st.write(p['Region']+' · '+p['Owner'])
            st.write('Current discussion: '+p['Follow-up'])
            st.write('Next step: validate partner needs, gather evidence and agree follow-up ownership.')
            st.caption('Real partner names are used only as fictional scenario labels. These are not actual account records.')
        with right,st.container(border=True):
            st.subheader('Partner reach');st.metric('Business customers',p['Business customers']);st.metric('Application listings',p['Applications listed'])
        st.subheader('Expansion opportunities · illustrative')
        table([{'Market':m,'Stage':stage,'Next step':step} for m,stage,step in [('DACH','Discovery','Validate demand'),('Nordics','Research','Map distribution channels'),('Southeast Asia','Research','Assess support coverage')]])
        st.caption('These opportunities are assumptions, not confirmed leads or a forecast.')
    elif page=='Meetings':
        meetings=data['meetings'];kpis([('Logged demo meetings',6),('Notes available',4),('Partner conversations',3),('Engineering reviews',2)])
        m=render_calendar(meetings)
        selected=m['Title']
        with st.container(border=True):
            st.subheader(selected);st.caption(f"{m['Date']} · {m['Time']} Europe/Zurich · {m['Owner']}")
            st.write(m['Notes']);st.caption('Illustrative summary, not an automatically synced transcript.')
            st.button('Open weekly report',on_click=navigate,args=('Weekly report',))
        st.caption('Calendar sync, recording capture and automatic report inclusion are future scope. Upload meeting files in Weekly report to run the real workflow.')
    elif page=='Insights & forecasts':
        kpis([('Weekly active users','1,200'),('Change vs prior week','+20%'),('Analytics delay','36 hours'),('Confirmed fix date','Not agreed')])
        left,right=st.columns([1.5,1])
        with left:
            st.subheader('Customer growth · fictional history')
            st.line_chart(pd.DataFrame(portfolio['snapshots']).set_index('week')[['customers']],color='#7964dc')
        with right,st.container(border=True):
            st.subheader('Signals for BD');st.write('Analytics freshness needs a partner discussion. Delay rose from 24 to 36 hours.')
            st.write('Onboarding validation remains open. Do not communicate a delivery commitment without engineering confirmation.')
            st.caption('Curated mock signals, not generated predictions.')
        st.subheader('What-if planning · assumptions, not a forecast')
        a,b=st.columns(2);growth=a.slider('Assumed quarterly customer growth (%)',0,20,5);quarters=b.slider('Quarters ahead',1,8,4)
        values=[{'Quarter':f'Q+{q}','Illustrative customers':round(312*(1+growth/100)**q)} for q in range(quarters+1)]
        st.line_chart(pd.DataFrame(values).set_index('Quarter'),color='#0d9d88')
        st.caption('Scenario = 312 × (1 + assumed growth rate) ^ quarters. No fitted model, seasonality, churn or uncertainty estimates; not a revenue prediction.')
    elif page=='Integrations':
        kpis([('Live external connections',0),('Local file intake','Available'),('Planned connectors',7)])
        connectors=[('SharePoint','Approved team libraries · proposed automatic collection','Manual upload today'),('OneDrive for Business','Selected organisational files · proposed change detection','Manual upload today'),('Microsoft Teams','Meeting transcripts','TXT / VTT export'),('Google Workspace','Docs and Meet notes','DOCX / TXT export or paste'),('Zoom','Meeting transcripts','VTT / TXT export'),('Platform analytics','Usage and quality data','CSV / XLSX upload'),('Email','Partner feedback','Paste the relevant text')]
        st.info('Future-scope assumption: NIG can approve read access to selected enterprise document sources. No tenant is connected in this prototype.')
        st.write('Proposed: approved SharePoint / OneDrive files → detect changes → collect the weekly evidence → existing validation and review. This could remove laptop staging and repeated uploads; incremental savings remain unmeasured.')
        st.caption('Tenant membership is not document access. Administrators and data owners must approve sources and permissions; other storage systems need their own adapters.')
        st.subheader('Sources for the weekly review')
        for i,(name,purpose,fallback) in enumerate(connectors):
            with st.container(border=True):
                left,right=st.columns([3,1]);left.markdown('<div class="integration-heading">'+logo(name,110 if name in ['Google Workspace','Zoom'] else 44)+'<h3>'+escape(name)+'</h3></div>',unsafe_allow_html=True);left.write(purpose);left.caption('Not connected · Current path: '+fallback)
                if right.button('Preview setup',key=f'connector_{i}'):
                    st.session_state['preview_connector']=name
        if st.session_state.get('preview_connector'):
            st.info(st.session_state['preview_connector']+' — proposed setup: administrator approves access → choose sources and reporting period → check extracted evidence → enable scheduled intake. This preview creates no connection.')
        st.caption('OpenAI and Anthropic credentials are configured separately for the working report workflow. This page does not expose or change them.')
    elif page=='Settings':
        st.subheader('Workspace preferences · demo only')
        saved=st.session_state.get('mock_preferences',{'workspace':'NIG · MEP','timezone':'Europe/Zurich','cadence':'Weekly','review':True,'reminder':False})
        with st.form('mock_preferences_form'):
            name=st.text_input('Workspace name',value=saved['workspace'])
            zones=['Europe/Zurich','Asia/Tokyo','UTC'];zone=st.selectbox('Reporting time zone',zones,index=zones.index(saved['timezone']))
            cadences=['Weekly','Monthly','Quarterly'];cadence=st.selectbox('Default cadence',cadences,index=cadences.index(saved['cadence']))
            st.checkbox('Require human approval',value=True,disabled=True)
            reminder=st.checkbox('Show a review reminder (preview)',value=saved['reminder'])
            if st.form_submit_button('Save preview preferences'):
                st.session_state['mock_preferences']={'workspace':name,'timezone':zone,'cadence':cadence,'review':True,'reminder':reminder}
                st.success('Preview preferences saved for this browser session. Actual report settings and schedules are unchanged.')
        st.subheader('Access roles · illustrative')
        table([{'Role':'BD reviewer','Proposed access':'Prepare, review and approve reports'},{'Role':'Engineering reader','Proposed access':'Read approved evidence and discussion points'},{'Role':'Workspace administrator','Proposed access':'Manage source permissions and retention'}])
        st.caption('SSO, role enforcement, scheduling and retention controls are future scope. API keys stay in the local .env file.')
    else:
        st.subheader('Find something in the fictional workspace')
        q=st.text_input('Search the demo',placeholder='Try Swisscom, Atlas, onboarding…')
        kind=st.selectbox('Search within',['Everything','Applications','Customers','Partners','Meetings'])
        records=[]
        for group,items,label,detail in [('Applications',data['applications'],'Application','Category'),('Customers',data['customers'],'Customer','Partner'),('Partners',portfolio['partners'],'Partner','Follow-up'),('Meetings',data['meetings'],'Title','Notes')]:
            if kind not in ('Everything',group): continue
            for item in items:
                if q.casefold() in (item[label]+' '+item[detail]).casefold(): records.append({'Name':item[label],'Section':group,'Context':item[detail]})
        st.caption(f'{len(records)} matches · Showing up to 20. Search covers fictional directory records only, not uploaded reports.')
        if records:
            table(records[:20]);target=st.selectbox('Open section',list(dict.fromkeys(r['Section'] for r in records)))
            st.button('Go to section',on_click=navigate,args=(target,))
        else: st.info('No matches. Try another name or a different section.')
