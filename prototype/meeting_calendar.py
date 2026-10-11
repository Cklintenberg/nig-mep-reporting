"""Graphical calendar over fictional meeting records; no external calendar sync."""
import calendar
from datetime import date, timedelta
import streamlit as st

DEMO_WEEK=date(2026,9,28)


def shift_period(amount,view):
    current=st.session_state['calendar_anchor']
    if view=='Week': current+=timedelta(days=7*amount)
    else:
        month=current.year*12+current.month-1+amount
        current=date(month//12,month%12+1,1)
    st.session_state['calendar_anchor']=current


def choose_event(title):
    st.session_state['calendar_meeting']=title


def render_calendar(meetings):
    st.session_state.setdefault('calendar_anchor',DEMO_WEEK)
    a,b,c=st.columns([1,1,2])
    view=a.radio('Calendar view',['Week','Month'],horizontal=True)
    kind=b.selectbox('Meeting type',['All meetings','Partner','Engineering','Vendor'])
    c.caption('Fictional meeting log · Europe/Zurich · Click an event to read its notes below.')
    previous,heading,next_,reset=st.columns([.45,4,.45,1])
    previous.button('‹',key='calendar_previous',on_click=shift_period,args=(-1,view),use_container_width=True)
    next_.button('›',key='calendar_next',on_click=shift_period,args=(1,view),use_container_width=True)
    reset.button('Demo week',on_click=lambda:st.session_state.update(calendar_anchor=DEMO_WEEK),use_container_width=True)
    anchor=st.session_state['calendar_anchor']
    start=anchor-timedelta(days=anchor.weekday())
    heading.subheader(f"{start:%d %b} – {start+timedelta(days=6):%d %b %Y}" if view=='Week' else anchor.strftime('%B %Y'))
    filtered=[m for m in meetings if kind=='All meetings' or m['Type']==kind]
    days=[start+timedelta(days=i) for i in range(7)] if view=='Week' else list(calendar.Calendar().itermonthdates(anchor.year,anchor.month))
    st.caption('● Partner · ● Engineering · ● Vendor — categories are written on each event.')

    def event(m):
        with st.container(key='event_'+m['Type'].lower()+'_'+m['Date']+'_'+m['Time'].replace(':','')):
            st.button(f"{m['Time']} · {m['Type']}\n\n{m['Title']}",key='event_'+m['Title'],
                      type='primary' if st.session_state.get('calendar_meeting')==m['Title'] else 'secondary',
                      on_click=choose_event,args=(m['Title'],),use_container_width=True)

    with st.container(key='calendar_grid'):
        if view=='Week':
            cols=st.columns([.4]+[1]*7,gap='small')
            cols[0].markdown('**Time**')
            for col,day in zip(cols[1:],days): col.markdown(f"**{day:%a}**  \n{day:%d %b}")
            for hour in range(9,17):
                cols=st.columns([.4]+[1]*7,gap='small')
                cols[0].caption(f'{hour:02}:00')
                for col,day in zip(cols[1:],days):
                    with col,st.container(key=f'calendar_slot_{day}_{hour}'):
                        matches=[m for m in filtered if m['Date']==day.isoformat() and int(m['Time'][:2])==hour]
                        if matches:
                            for m in matches:event(m)
                        else: st.markdown('<div class="calendar-empty"></div>',unsafe_allow_html=True)
        else:
            for col,name in zip(st.columns(7,gap='small'),calendar.day_abbr):col.markdown('**'+name+'**')
            for offset in range(0,len(days),7):
                for col,day in zip(st.columns(7,gap='small'),days[offset:offset+7]):
                    with col,st.container(border=True,key=f'calendar_day_{day}'):
                        st.caption(day.strftime('%d %b') if day.month!=anchor.month else str(day.day))
                        for m in filtered:
                            if m['Date']==day.isoformat():event(m)
    count=sum(m['Date'] in {d.isoformat() for d in days} for m in filtered)
    if not count:st.info('No demo meetings in this period. Choose Demo week to return to the fictional meeting log.')
    st.subheader('Meeting details')
    selected=st.session_state.get('calendar_meeting',meetings[0]['Title'])
    return next(m for m in meetings if m['Title']==selected)
