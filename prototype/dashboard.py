"""A business overview using explicitly fictional portfolio snapshots."""
from html import escape
import json
from pathlib import Path
import altair as alt
import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parent


def go_to_report():
    st.session_state['workspace_page'] = 'Weekly report'


def sparkline(values, color):
    low, high = min(values), max(values)
    spread = high - low or 1
    points = [(6 + i * 288 / max(len(values)-1, 1), 45 - (v-low)/spread*33) for i,v in enumerate(values)]
    line = ' '.join(f'{x:.1f},{y:.1f}' for x,y in points)
    x,y = points[-1]
    return f'<svg viewBox="0 0 300 52" role="img" aria-label="Weekly trend" preserveAspectRatio="none"><polyline points="{line}" fill="none" stroke="{color}" stroke-width="2.5" stroke-linejoin="round"/><circle cx="{x}" cy="{y}" r="3.5" fill="white" stroke="{color}" stroke-width="2"/></svg>'


def render_overview():
    data=json.loads((ROOT/'sample_data/portfolio.json').read_text())
    snapshots=data['snapshots']; current,previous=snapshots[-1],snapshots[-2]
    st.markdown('<div class="eyebrow">MOBILE EXPERIENCE PLATFORM</div>',unsafe_allow_html=True)
    st.title('Business overview')
    st.caption('Partner ecosystem · Illustrative data · Week of 28 September 2026')
    st.caption('Overview tracks portfolio health. Meeting reports combine these figures with source-backed feedback, updates and questions for Engineering, Vendor or Partner conversations.')
    with st.container(key='overview_banner'):
        text,action=st.columns([2.5,1],vertical_alignment='center')
        with text:
            st.markdown('<div class="banner-kicker">PARTNERSHIP OPERATIONS</div><h2>Your ecosystem. A clearer view.</h2><p>Follow adoption, spot what needs attention, and bring the right evidence to your next engineering meeting.</p>',unsafe_allow_html=True)
        with action:
            st.button('Prepare weekly report →',type='primary',on_click=go_to_report,use_container_width=True)
            st.caption('Upload → Generate → Download → Review')
    heading,period=st.columns([3,1])
    with heading:
        st.subheader('Portfolio at a glance')
        st.caption('Latest week totals · Changes compare with the previous week')
    with period:
        window=st.selectbox('Trend window',['Last 8 weeks','Last 4 weeks'],label_visibility='collapsed')
    history=snapshots[-(8 if window=='Last 8 weeks' else 4):]
    metrics=[
        ('Applications','applications',f"{current['applications']}",f"+{current['applications']-previous['applications']} vs previous week",'Published across the platform','#7161d6','positive'),
        ('Business customers','customers',f"{current['customers']:,}",f"+{current['customers']-previous['customers']} vs previous week",'Distinct customer organisations','#0d9d88','positive'),
        ('Distribution partners','partners',str(current['partners']),'No change vs previous week','4 of 10 in the three-year ambition','#72819b','neutral'),
        ('Weekly active users','weekly_active_users',f"{current['weekly_active_users']:,}",f"+{(current['weekly_active_users']/previous['weekly_active_users']-1)*100:.0f}% vs previous week",'Users in the matched application cohort','#7161d6','positive'),
        ('Platform availability','availability',f"{current['availability']}%",f"+{current['availability']-previous['availability']:.1f} pp vs previous week",'Share of scheduled observation time','#0d9d88','positive'),
        ('Analytics delay','analytics_delay',f"{current['analytics_delay']} hours",f"+{current['analytics_delay']-previous['analytics_delay']} hours vs previous week",'Data is arriving later than last week','#e89449','attention'),
    ]
    cards=[]
    for label,key,value,change,description,color,tone in metrics:
        cards.append(f'<section class="portfolio-card"><div class="card-label">{escape(label)}</div><div class="card-value">{escape(value)}</div><div class="card-change {tone}">{escape(change)}</div>{sparkline([s[key] for s in history],color)}<div class="card-note">{escape(description)}</div></section>')
    st.markdown('<div class="portfolio-grid">'+''.join(cards)+'</div>',unsafe_allow_html=True)
    chart_col,attention_col=st.columns([1.65,1],gap='large')
    with chart_col:
        with st.container(border=True):
            title,choice=st.columns([1,1])
            with title: st.subheader('Adoption trend')
            with choice: series=st.selectbox('Trend metric',['Business customers','Applications'],label_visibility='collapsed')
            field='customers' if series=='Business customers' else 'applications'
            df=pd.DataFrame(history)
            df['Week']=pd.to_datetime(df['week'])
            chart=(alt.Chart(df).mark_area(line={'color':'#7964dc','strokeWidth':2.5},color=alt.Gradient(gradient='linear',stops=[alt.GradientStop(color='#e5defa',offset=0),alt.GradientStop(color='#ffffff',offset=1)],x1=0,x2=0,y1=0,y2=1),point={'filled':True,'fill':'#7964dc','size':42})
                .encode(x=alt.X('Week:T',axis=alt.Axis(format='%d %b',title=None,grid=False)),
                        y=alt.Y(f'{field}:Q',axis=alt.Axis(title=None),scale=alt.Scale(zero=True)),
                        tooltip=[alt.Tooltip('Week:T',format='%d %b %Y'),alt.Tooltip(f'{field}:Q',title=series)])
                .properties(height=218).configure_view(strokeWidth=0).configure_axis(labelColor='#777782',gridColor='#f1f1f4',domain=False,tickSize=0))
            st.altair_chart(chart,use_container_width=True)
            st.caption(f'{series} at each week’s reporting snapshot. All values are fictional.')
    with attention_col:
        with st.container(border=True):
            st.subheader('For the next conversation')
            st.markdown('''<div class="attention-item"><span class="attention-dot amber"></span><div><strong>Analytics are arriving later</strong><p>Delay increased from 24 to 36 hours. Engineering is investigating; no fix date is agreed.</p><small>PLATFORM METRICS · ENG-042</small></div></div><div class="attention-item"><span class="attention-dot violet"></span><div><strong>Partners need onboarding visibility</strong><p>Vodafone requested a clearer checklist. Partner validation is still pending.</p><small>P-015 · ENG-043</small></div></div>''',unsafe_allow_html=True)
            st.button('Review the source notes →',on_click=go_to_report,use_container_width=True)
    st.subheader('Partner portfolio')
    st.caption('Four fictional distribution accounts across EMEA and APAC')
    a,b=st.columns([2,1])
    with a: search=st.text_input('Search partners',placeholder='Search partner name…',label_visibility='collapsed')
    with b: region=st.selectbox('Region',['All regions','EMEA','APAC'],label_visibility='collapsed')
    partners=pd.DataFrame(data['partners'])
    if search: partners=partners[partners['Partner'].str.contains(search,case=False,regex=False)]
    if region!='All regions': partners=partners[partners['Region']==region]
    if partners.empty: st.info('No partners match this search.')
    else: st.dataframe(partners,hide_index=True,use_container_width=True)
    st.caption(f'{len(partners)} of 4 partners shown · An application can be listed by several partners, so application listings are not summed.')
    with st.expander('About these numbers'):
        st.write('This overview is a fictional portfolio snapshot, not a live connection. Applications means distinct published apps; customers means distinct business organisations, assigned to one primary distribution partner for this example. Weekly active users are people and are a separate measure from customer organisations.')
        st.write('The last two weeks of users, availability and analytics delay match the normal weekly-report sample. Other portfolio totals and the earlier trend history provide illustrative business context. Uploading report files does not update this portfolio view.')
        st.write('The trend window changes the plotted history. Headline totals always show the latest week, and headline changes always compare the latest two weeks. The 10-partner ambition is a scenario assumption, not a forecast.')
