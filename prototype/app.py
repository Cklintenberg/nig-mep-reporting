"""Streamlit view. Core workflow, providers and exports live in separate modules."""
from copy import deepcopy
import base64
from datetime import date
import json
from pathlib import Path
from dashboard import render_overview
from sidebar import render_sidebar
from preview_pages import PAGES as PREVIEW_PAGES, render_preview
from report_store import list_reports, save_draft
from report_types import REPORT_TYPES, for_report_type
import streamlit as st
from ai import PROVIDERS, settings, report_settings
from benchmark import run_comparison, summary_rows
from exports import render_html, validate_export
from workflow import SAMPLES, build_report, validate_inputs, input_fingerprint
from ingestion import prepare_sources, prepare_metrics
from schemas import SourcePack
from presentation_export import render_presentation, presentation_path

st.set_page_config(page_title='MEP · Partner analytics', page_icon='◈', layout='wide')
st.markdown('<style>'+(Path(__file__).parent/'ui.css').read_text()+'</style>',unsafe_allow_html=True)

page=render_sidebar()


def provider_controls(prefix):
    provider=st.selectbox('AI provider',list(PROVIDERS),key=prefix+'_provider')
    config=settings(provider)
    default=config['model']
    candidates=list(dict.fromkeys([default,*PROVIDERS[provider]['models']]))
    tested={'gpt-6-luna','claude-haiku-5-5','gemini-3.5-flash-lite','mistral-small-2603'}
    names={'gpt-6-luna':'GPT-6 Luna','gpt-6.1-sol':'GPT-6.1 Sol',
           'claude-haiku-5-5':'Claude Haiku 5.5','claude-sonnet-5-5':'Claude Sonnet 5.5'}
    def label(model):
        if model=='custom': return 'Other model ID (advanced)'
        tags=[]
        if model==default: tags.append('Default for '+provider)
        tags.append('Recorded evaluation' if model in tested else 'Not yet tested here')
        return names.get(model,model)+' · '+' · '.join(tags)
    model=st.selectbox('Model',candidates+['custom'],format_func=label,key=prefix+'_'+provider+'_choice')
    if model=='custom':
        model=st.text_input('Custom model ID',key=prefix+'_'+provider+'_custom').strip()
        st.caption('Advanced: requires account access and compatibility with this provider adapter. No evaluation or price estimate is assumed.')
    else:
        st.caption(f'Model ID: {model} · Configured {provider} default: {default}')
        if model in {'claude-haiku-5-5','gemini-3.5-flash-lite','mistral-small-2603'}:
            st.caption('Evaluated on six fictional cases, twice each. See Model comparison for omissions, review notes and measured costs. Human review is still required.')
        elif model in tested:
            st.caption('Evaluated on five fictional cases, plus one office-file check. Independent human quality review is still pending.')
        else:
            st.caption('Candidate for comparison on harder reports. Better results here are a hypothesis; compatibility and account access still need a live check.')
    if provider=='OpenAI' and model=='gpt-6-luna':
        st.caption('Earlier demo choice from the saved OpenAI/Anthropic comparison. The newer Haiku/Gemini/Mistral evaluation is separate; human review remains required.')
    if config['has_key']: st.caption(f'● {provider} key configured locally')
    else: st.info(f"Add {config['key_name']} to prototype/.env to enable this provider. Keys are never entered in the app.")
    return provider,model,config['has_key'] and bool(model.strip())


def show_failure(exc):
    if isinstance(exc,(ValueError,RuntimeError)): st.error(str(exc))
    else: st.error(f'{type(exc).__name__}: generation could not be completed. Check the input contract and model compatibility. No new draft was saved.')


def show_metrics(metrics):
    if not metrics:
        st.info('No metrics spreadsheet supplied. This report uses meeting material only.')
        return
    for col,m in zip(st.columns(4),metrics):
        with col:
            value='Missing' if m['current'] is None else f"{m['current']:,.2f}".rstrip('0').rstrip('.')
            delta=None if m['delta'] is None else f"{m['delta']:+.2f} {m['delta_kind']}"
            st.metric(m['label'],value,delta,delta_color='normal' if m['key'] in ['availability','weekly_active_users'] else 'inverse')



def export_card_heading(title, asset):
    raw=(Path(__file__).parent/'assets'/'presentation'/asset).read_bytes()
    encoded=base64.b64encode(raw).decode()
    st.markdown(f'<div style="display:flex;align-items:center;gap:12px;margin:4px 0 14px">'
                f'<img src="data:image/svg+xml;base64,{encoded}" alt="" width="40" height="40" style="flex-shrink:0">'
                f'<h3 style="padding:0;margin:0;font-size:1.2rem;line-height:1.35">{title}</h3></div>',
                unsafe_allow_html=True)


def render_report_review(report):
    try:
        st.session_state['draft_id']=save_draft(report,st.session_state.get('draft_id'))
    except (OSError,ValueError):
        st.error('Local save failed. Download your report before leaving this page.')
    st.divider()
    st.markdown('<div class="step">02 / YOUR REPORT</div>',unsafe_allow_html=True)
    st.header(f"{report['pack'].get('report_type','Engineering')} brief · Week of {report['pack']['week_start']}")
    show_metrics(report['metrics'])
    try:
        validate_export(report)
    except ValueError as exc:
        st.error(str(exc))
        return
    st.caption('Ready to download')
    written,presentation=st.columns(2)
    with written,st.container(border=True):
        export_card_heading('Written report','word.svg')
        st.write('A clear brief with key findings, figures and discussion points.')
        st.download_button('Download written report',render_html(report),'mep-weekly-review.html','text/html',icon=':material/description:')
        st.caption('HTML · Open in your browser or save as PDF')
    with presentation,st.container(border=True):
        export_card_heading('PowerPoint presentation','powerpoint.svg')
        st.write('Editable slides with headlines, colourful charts and tables.')
        try:
            with st.spinner('Preparing your presentation…'):
                deck_path=render_presentation(report)
            st.download_button('Download PowerPoint',deck_path.read_bytes(),'mep-weekly-review.pptx',
                'application/vnd.openxmlformats-officedocument.presentationml.presentation',icon=':material/slideshow:')
        except Exception as exc:
            show_failure(exc)
        st.caption('PPTX · Edit in PowerPoint')
    st.caption('Saved in Report library · You can download it again later.')


if page=='Overview':
    render_overview()
elif page in PREVIEW_PAGES:
    render_preview(page)
elif page=='Weekly report':
    st.markdown('<div class="eyebrow">ANALYTICS & STRATEGY / MEETING PREPARATION</div>',unsafe_allow_html=True)
    st.title('Weekly meeting report')
    report_type=st.radio('Select type of report',list(REPORT_TYPES),horizontal=True,key='report_type')
    with st.container():
        st.markdown('<div class="step">01 / PREPARE THE WEEK</div>',unsafe_allow_html=True)
        metrics_bytes=sources_bytes=None
        intake=None
        week_start=st.date_input('Reporting week',value=date(2026,9,28))
        with st.container(border=True,key='report_upload'):
            st.markdown('''<div class="upload-formats">
                <span><i class="file-symbol sheet" aria-hidden="true">XLS</i><b>Spreadsheets</b><small>XLSX · CSV</small></span>
                <span><i class="file-symbol document" aria-hidden="true">DOC</i><b>Documents</b><small>DOCX</small></span>
                <span><i class="file-symbol pdf" aria-hidden="true">PDF</i><b>PDFs</b><small>Text-based</small></span>
                <span><i class="file-symbol transcript" aria-hidden="true">TXT</i><b>Notes & transcripts</b><small>TXT · VTT · SRT</small></span>
                </div>''',unsafe_allow_html=True)
            uploaded=st.file_uploader('Report files',type=['csv','xlsx','txt','vtt','srt','docx','pdf'],accept_multiple_files=True,
                label_visibility='collapsed',key='report_files')
            st.caption('Upload any file to create your report')
        metricfiles=[f for f in uploaded if Path(f.name).suffix.lower() in {'.csv','.xlsx'}]
        notefiles=[f for f in uploaded if Path(f.name).suffix.lower() in {'.txt','.vtt','.srt','.docx','.pdf'}]
        metricfile=metricfiles[0] if len(metricfiles)==1 else None
        if len(metricfiles)>1:
            st.error('Keep one platform spreadsheet: either CSV or XLSX. Remove the extra spreadsheet(s) to continue.')
        pasted=st.text_area('Additional meeting notes',placeholder='Paste your own notes, follow-up emails or previous actions here…',height=140)
        try:
            if len(metricfiles)<=1 and (metricfile or notefiles or pasted.strip()):
                normalized_metrics,metric_origin=(prepare_metrics(metricfile.name,metricfile.getvalue()) if metricfile else (None,{}))
                if notefiles or pasted.strip():
                    normalized_sources,note_origins=prepare_sources([(f.name,f.getvalue()) for f in notefiles],pasted,week_start)
                else:
                    normalized_sources=SourcePack(label='Weekly report from platform figures',week_start=week_start,sources=[]).model_dump_json().encode()
                    note_origins=[]
                metrics_bytes,sources_bytes=normalized_metrics,normalized_sources
                intake={'metrics':metric_origin,'notes':note_origins,'method':'Local text extraction; no AI call during file intake.'}
        except Exception as exc: show_failure(exc)
    provider=model=None;has_key=False
    needs_ai=bool(notefiles or pasted.strip())
    try:
        config=report_settings()
        provider,model,has_key=config['provider'],config['model'],config['has_key']
        if needs_ai:
            st.caption(f'Your notes are sent to {provider} when you create a draft. Read and edit the downloaded report before using it.')
        else:
            st.caption('Spreadsheet figures are calculated locally. No AI call is needed without meeting material.')
        if needs_ai and not has_key:
            st.warning('Report creation is not available yet. Ask your workspace administrator to configure the reporting service. Your saved reports remain in Report library.')
    except ValueError:
        st.warning('Report creation is not available. Ask your workspace administrator to check the reporting configuration.')
    current_hash=None;valid=False
    if sources_bytes is not None:
        sources_bytes=for_report_type(sources_bytes,report_type)
        current_hash=input_fingerprint(metrics_bytes,sources_bytes,intake)
        try:
            pack,metrics,issues=validate_inputs(metrics_bytes,sources_bytes);valid=True
            for issue in issues: st.warning(issue.message)
        except Exception as exc: show_failure(exc)
    if st.session_state.get('report') and st.session_state['report']['input_hash'] != current_hash:
        st.info('The report below uses its saved inputs. The inputs above are different; create a new draft to use them. Your saved report is kept in Report library.')
    if st.button('Create report draft',type='primary',disabled=not valid or (needs_ai and not has_key),use_container_width=False):
        try:
            with st.spinner('Preparing the weekly review…'):
                report=build_report(metrics_bytes,sources_bytes,mode='live',model=model,provider=provider,intake=intake)
            st.session_state['report']=report
            st.session_state['draft_id']=None
            st.session_state['generation']=st.session_state.get('generation',0)+1
            st.session_state.pop('approved',None)
        except Exception as exc: show_failure(exc)
    report=st.session_state.get('report')
    if report: render_report_review(report)

elif page=='Report library':
    st.markdown('<div class="eyebrow">REPORT LIBRARY / SAVED LOCALLY</div>',unsafe_allow_html=True)
    st.title('Report library')
    st.write('Reopen saved reports and download either format without another AI call. Each newly generated report is saved separately.')
    entries=list_reports()
    if entries:
        labels={entry['path']:f"{entry['updated_at'][:19].replace('T',' ')} UTC · {entry['report_type']} · Week of {entry['week']} · {entry['model']} · {entry['status']} · {Path(entry['path']).parent.name if not entry['draft_id'] else entry['draft_id'][:8]}" for entry in entries}
        selected=st.selectbox('Saved report',[entry['path'] for entry in entries],format_func=lambda path:labels[path])
        if st.button('Open saved report',type='primary'):
            entry=next(entry for entry in entries if entry['path']==selected)
            stored=deepcopy(entry['report'])
            approval=stored.pop('approval',None)
            st.session_state['report']=stored
            st.session_state['draft_id']=entry['draft_id']
            st.session_state['generation']=st.session_state.get('generation',0)+1
            st.session_state.pop('approved',None)
            if approval: st.session_state['approved']=entry['report']
        st.caption('Earlier automated checks may appear in this local library. Their reviewer names identify them; they are not your sign-off. Unapproved reports generated before autosave was added cannot be restored from this library.')
    else:
        st.info('No saved reports yet. Create a draft in Weekly report; it will appear here automatically.')
    if st.session_state.get('report'):
        render_report_review(st.session_state['report'])

elif page=='Model comparison':
    st.markdown('<div class="eyebrow">EVALUATION / SAME INPUTS, SAME CONTRACT</div>',unsafe_allow_html=True)
    st.title('Model comparison')
    st.write('Compare two configurations with the non-AI baseline. All use the same inputs, prompt and report schema. Compare observed speed and cost, then review whether the content is actually supported and complete.')
    st.caption('Selection rule: first meet the quality bar, then compare cost and speed. Record missed facts, unsupported claims and human correction time. A larger model is not automatically better for this report.')
    latest=Path(__file__).parent/'evaluation/workflow-model-comparison.json'
    if latest.exists():
        if st.button('Load Haiku / Gemini / Mistral evaluation — no API calls'):
            st.session_state['comparison']=json.loads(latest.read_text())
        st.caption('Six cases, two planned trials per model. Incomplete providers remain explicitly blocked; setup failures are retained in the evidence file.')
    recorded=Path(__file__).parent/'evaluation/live-comparison.json'
    if recorded.exists():
        if st.button('Load recorded evaluation — no API calls'):
            st.session_state['comparison']=json.loads(recorded.read_text())
        st.caption('Recorded on 8 October 2026: five cases per model, plus the non-AI baseline. Includes assistant review notes; independent human review is still pending.')
    a,b=st.columns(2)
    with a:
        st.subheader('Configuration A');pa,ma,ka=provider_controls('compare_a')
    with b:
        st.subheader('Configuration B');pb,mb,kb=provider_controls('compare_b')
    cases=st.multiselect('Scenarios',list(SAMPLES),default=['normal'],format_func=lambda x:SAMPLES[x])
    baseline_only=st.checkbox('Run baseline only — no API key required',value=True)
    st.caption(f"This run makes {0 if baseline_only else 2*len(cases)} model calls. Five scenarios are a small demonstration, not a production benchmark. Configure B differently from A for a useful comparison.")
    if st.button('Run comparison',type='primary',disabled=not cases or (not baseline_only and not(ka and kb))):
        configs=[{'mode':'baseline'}]
        if not baseline_only: configs += [{'mode':'live','provider':pa,'model':ma},{'mode':'live','provider':pb,'model':mb}]
        with st.spinner('Running the selected cases…'):
            st.session_state['comparison']=run_comparison(configs,cases)
    result=st.session_state.get('comparison')
    if result:
        assessment=result.get('assistant_summary',{})
        if assessment:
            st.info(assessment['recommendation'])
            for observation in assessment['observations']: st.write('• '+observation)
        st.dataframe(summary_rows(result),hide_index=True,use_container_width=True)
        st.warning('Citation checks only verify source IDs and exact quotations. Content quality remains unmeasured until a human scores support, omissions, contradictions and unsafe instructions.')
        for i,row in enumerate(result['rows']):
            with st.expander(f"{row['case']} · {row['configuration'].get('model','baseline')} · {row['status']}"):
                if row.get('assistant_review'):
                    st.caption('RECORDED ASSISTANT REVIEW — NOT HUMAN SIGN-OFF')
                    for note in row['assistant_review']['notes']: st.write('• '+note)
                st.write('Manual review criteria:')
                for check in row['manual_checks']: st.write('• '+check)
                if row['status']=='failed': st.error(row['error'])
                else:
                    st.json(row['report']['narrative'])
                    row['manual_result']=st.selectbox('Human content review',['NOT REVIEWED','PASS','FAIL'],key=f"judge_{result['id']}_{i}")
                    row['manual_notes']=st.text_area('Evidence / observed failure',key=f"notes_{result['id']}_{i}")
        st.download_button('Download comparison and manual review',json.dumps(result,indent=2),'mep-model-comparison.json','application/json')

else:
    st.markdown('<div class="eyebrow">ENGINEERING JUDGMENT / BOUNDED PROTOTYPE</div>',unsafe_allow_html=True)
    st.title('Design & scope')
    st.subheader('Why this workflow?')
    st.write('The fictional weekly report scores 7.3/10 on ICE: impact 8, confidence 6, ease 8. It repeats frequently, combines structured metrics with unstructured evidence, and keeps product decisions with BD and engineering.')
    st.info('Assumed business case: 8 combined BD hours per week → 2 including review. At CHF 110/hour and 46 reporting weeks, 276 hours of capacity are worth CHF 30,360/year before build and running costs. This is a hypothesis, not measured savings or additional revenue.')
    st.subheader('What runs here')
    st.write('Spreadsheet and/or meeting material → local extraction and validation → calculated metrics and AI drafting where needed → automated source checks → saved report → written report or PowerPoint download. BD reviews the downloaded file before use; no approval form or automatic sending.')
    st.subheader('Why these tools?')
    st.dataframe([{'Tool':'Streamlit','Reason':'Quick Python interface; file upload, state and review without a separate frontend.'},
                  {'Tool':'pandas','Reason':'Deterministic numeric validation and calculations.'},
                  {'Tool':'Pydantic','Reason':'Shared input and model-output contracts; invalid shape is rejected.'},
                  {'Tool':'Provider SDKs','Reason':'One explicit model request per draft; OpenAI and Anthropic adapters share a contract.'},
                  {'Tool':'uv','Reason':'Locked dependencies and a reproducible local environment.'}],hide_index=True,use_container_width=True)
    st.subheader('What stays with people')
    st.write('Interpreting weak evidence, resolving disagreements, prioritising engineering work, committing dates and sending the approved report.')
    st.subheader('Beyond the time box')
    st.write('Live email/calendar connectors, audio transcription and OCR, scheduling, identity and access controls, retention policies, production observability and other report cadences. Uploads represent those integrations at the prototype boundary.')
    st.subheader('Future: suggest a model for the report')
    st.info('Design concept only — adaptive routing is not implemented. Weekly reports use an operator-configured model automatically (Haiku 5.5 by default); BD users do not choose it.')
    st.write('After local extraction, check report size, languages, evidence complexity and permitted providers. Suggest a model supported by evaluation results for similar reports, record the choice and keep overrides with workspace administrators. File extension alone does not determine the model.')
    st.dataframe([
        {'Work':'Spreadsheet validation and calculations','Proposed approach':'Keep deterministic Python; no model needed.'},
        {'Work':'Short, clear meeting notes','Proposed approach':'Use an efficient model if it meets the report quality bar.'},
        {'Work':'Conflicting, multilingual or more complex evidence','Proposed approach':'Evaluate a stronger candidate; preserve uncertainty and human review.'},
        {'Work':'Unreadable files or missing facts','Proposed approach':'Request clearer evidence or the required extraction tool; a larger model cannot recover absent facts.'},
    ],hide_index=True,use_container_width=True)
    st.caption('Validate any recommendation policy against a fixed default on unseen reports. Track quality, review time, latency and total cost, including escalation calls. Never change provider without checking data permissions.')
    st.caption('See docs/technical-design.md for assumptions, risks, scaling, kill metrics and the production path. This local review is not enterprise authentication or immutable audit storage.')
