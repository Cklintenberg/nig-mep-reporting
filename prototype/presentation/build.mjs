/** Approved report -> editable business presentation. No model calls, no network requests. */
import fs from 'node:fs/promises';
import path from 'node:path';
import {pathToFileURL} from 'node:url';
const [input,output,previewDir]=process.argv.slice(2);
if(!input||!output) throw new Error('Usage: build.mjs approved.json output.pptx [preview-dir]');
const runtime=JSON.parse(await fs.readFile(new URL('./runtime.local.json',import.meta.url),'utf8'));
const {Presentation,PresentationFile}=await import(pathToFileURL(process.env.MEP_ARTIFACT_MODULE||runtime.artifactModule).href);
const r=JSON.parse(await fs.readFile(input,'utf8'));

const pres=Presentation.create({slideSize:{width:1280,height:720}});
const C={navy:'#0F1743',ink:'#18213D',soft:'#59647C',purple:'#7962D7',teal:'#079C93',orange:'#D27928',blue:'#3676DB',lime:'#A3E635',pale:'#F5F6FA'};
const font='Arial';const chartOwners=[],tableOwners=[];
const number=v=>v===null||v===undefined?'Not supplied':Number(v).toLocaleString('en-US',{maximumFractionDigits:4});
const value=m=>number(m.current)+(m.current!==null&&m.unit==='%'?'%':'');
const delta=m=>m.delta===null?'Change unavailable':`${m.delta>0?'+':''}${number(m.delta)}${m.delta_kind==='relative %'?'% vs previous week':' '+m.delta_kind}`;
function text(sl,t,x,y,w,h,size=24,color=C.ink,bold=false){const sh=sl.shapes.add({geometry:'textbox',position:{left:x,top:y,width:w,height:h},fill:'none',line:{fill:'none',width:0}});sh.text=String(t);sh.text.style={fontFamily:font,typeface:font,fontSize:size,color,bold,insets:0,verticalAlignment:'top',wrap:'word'};return sh;}
function slide(title,subtitle='',dark=false){const sl=pres.slides.add();sl.background.fill=dark?C.navy:'#FFFFFF';text(sl,title,64,68,1152,104,title.length>70?36:42,dark?'#FFFFFF':C.ink,true);if(subtitle)text(sl,subtitle,64,177,1152,55,21,dark?'#B6C3E0':C.soft);text(sl,`NIG / MEP   •   Internal preparation   •   ${r.pack.week_start}`,64,674,1050,24,13,dark?'#B6C3E0':C.soft);text(sl,String(pres.slides.items.length).padStart(2,'0'),1160,674,55,24,13,dark?'#B6C3E0':C.soft);return sl;}
function table(sl,values,widths,y=246,rowHeight=64){const t=sl.tables.add({rows:values.length,columns:values[0].length,left:64,top:y,width:1152,height:rowHeight*values.length,columnWidths:widths,values});t.borders.assign({fill:'#DFE4ED',width:1,style:'solid'});for(let i=0;i<values.length;i++){t.rows[i].height=rowHeight;for(let j=0;j<values[i].length;j++){const c=t.getCell(i,j);c.fill=i===0?C.navy:i%2?'#F3F5FA':'#FFFFFF';c.text.style={fontFamily:font,typeface:font,fontSize:21,color:i===0?'#FFFFFF':C.ink,bold:i===0,insets:12};}}tableOwners.push(pres.slides.items.length);return t;}
function notes(sl,content){sl.speakerNotes.text=content+'\n\nInternal preparation. Read and edit before use or sharing. Downloading does not record approval. No automatic publishing or task creation.';}
function split(s,limit=180){const out=[];while(s.length>limit){let n=s.lastIndexOf(' ',limit);if(n<limit/2)n=limit;out.push(s.slice(0,n));s=s.slice(n).trimStart();}if(s)out.push(s);return out;}
let sl=slide(`Weekly ${r.pack.report_type||'Engineering'} review`,`Week of ${r.pack.week_start}`,true);
text(sl,'A shared view for the next conversation',64,290,1050,115,54,'#FFFFFF',true);
text(sl,`${r.metrics.length?'Platform figures':''}${r.metrics.length&&r.pack.sources.length?' and ':''}${r.pack.sources.length?'meeting evidence':''}`,64,444,1100,46,28,C.lime);
text(sl,'Prepared for your meeting',64,539,1100,40,23,'#FFFFFF');
text(sl,'Internal BD preparation. Review the recipient and sensitive content before sharing.',64,592,1100,44,20,'#B6C3E0');
notes(sl,`Source: the generated ${r.pack.report_type} report, reporting week ${r.pack.week_start}. All figures and statements are reused from that snapshot. No additional AI interpretation. Input fingerprint: ${r.input_hash}.`);
if(r.metrics.length){
 sl=slide('Platform signals','Current reporting week. Changes compare the same cohort with the previous week.');
 const colors=[C.purple,C.teal,C.orange,C.blue];
 for(let i=0;i<r.metrics.length;i++){const m=r.metrics[i],x=64+(i%2)*584,y=267+Math.floor(i/2)*177;
 text(sl,m.label,x,y,535,35,24,C.soft);text(sl,value(m),x,y+41,530,64,54,colors[i%4],true);text(sl,(m.unit==='%'?'':m.unit+'   ·   ')+delta(m),x,y+111,535,37,22,C.ink);}
 notes(sl,JSON.stringify(r.metrics,null,2)+'\nSpreadsheet origin: '+JSON.stringify(r.intake?.metrics||{})+'\nNo cause is inferred from a metric movement.');
 for(let start=0;start<r.metrics.length;start+=2){const ms=r.metrics.slice(start,start+2);sl=slide('Changes in platform performance','Each chart uses its own units. Missing values stay missing.');for(let i=0;i<ms.length;i++){const m=ms[i],x=64+i*584;
 text(sl,m.label,x,247,540,37,27,colors[(start+i)%4],true);
 const present=[['Previous week',m.previous],['Reporting week',m.current]].filter(p=>p[1]!==null);
 if(present.length){const fmt=m.unit==='%'?'0.0"%"':m.unit==='users'?'#,##0':'0.0';const ch=sl.charts.add('bar',{position:{left:x,top:300,width:538,height:274},categories:present.map(p=>p[0]),series:[{name:m.label,values:present.map(p=>p[1]),fill:colors[(start+i)%4],valuesFormatCode:fmt}],hasLegend:false,barOptions:{direction:'column',grouping:'clustered',gapWidth:110},xAxis:{textStyle:{fontSize:18,typeface:font,fill:C.soft}},yAxis:{min:0,...(m.key==='availability'?{max:100}:{}),numberFormatCode:fmt,textStyle:{fontSize:16,typeface:font,fill:C.soft},majorGridlines:{fill:'#E1E6EF',width:1}},dataLabels:{showValue:true,position:'outEnd',numberFormatCode:fmt,textStyle:{fontSize:21,typeface:font,fill:C.ink,bold:true}},chartFill:'#FFFFFF',plotAreaFill:'#FFFFFF'});chartOwners.push(pres.slides.items.length);}
 else text(sl,'No values supplied',x,374,530,55,30,C.soft);
 text(sl,`${m.unit} · ${delta(m)}`,x,600,540,42,21,C.soft);}
 notes(sl,JSON.stringify(ms,null,2)+'\nChart values come directly from the validated calculation results. Missing periods are omitted, never displayed as zero. All axes start at zero; availability uses 0–100%. Each chart has its own units and scale.');}
 sl=slide('Figures for the meeting',`Cohort: ${r.metrics[0].cohort}`);
 table(sl,[['Metric','Previous','Current','Change'],...r.metrics.map(m=>[`${m.label} (${m.unit})`,number(m.previous),number(m.current),delta(m)])],[365,190,190,407],246,69);
 notes(sl,JSON.stringify(r.metrics,null,2));
}
for(const [i,f] of r.narrative.findings.entries()){
 const chunks=split(f.summary,360);
 for(const [part,summary] of chunks.entries()){
 sl=slide(f.title,`Discussion point ${i+1} · ${f.category}${chunks.length>1?' · Part '+(part+1)+' of '+chunks.length:''}`);
 text(sl,summary,64,260,1152,275,26,C.ink);
 if(f.needs_review){text(sl,'Review context',64,538,220,30,20,C.orange,true);text(sl,f.review_reason,64,574,1152,72,20,C.soft);}
 else text(sl,'Source references: '+[...new Set(f.evidence.map(e=>e.source_id))].join(', '),64,579,1152,50,20,C.soft);
 notes(sl,f.summary+(f.needs_review?'\n\nReview context: '+f.review_reason:''));
}
}
const questions=r.narrative.discussion_questions.flatMap((q,i)=>split(q,205).map((part,j)=>[`${i+1}${j?' (continued)':''}`,part,'Discuss / confirm']));
for(let start=0;start<questions.length;start+=3){sl=slide('Questions for the meeting','These are discussion prompts, not assigned tasks or agreed commitments.');table(sl,[['#','Question','Status'],...questions.slice(start,start+3)],[90,832,230],246,102);notes(sl,r.narrative.discussion_questions.join('\n\n'));}
const issues=r.issues.flatMap(i=>split(i.message,225).map(t=>[i.severity==='error'?'Blocked':'Data gap',t]));
for(let start=0;start<issues.length;start+=3){sl=slide('What remains uncertain','Keep these limitations visible when interpreting the report.');table(sl,[['Type','Review note'],...issues.slice(start,start+3)],[180,972],246,105);notes(sl,JSON.stringify(r.issues,null,2));}
await fs.mkdir(path.dirname(output),{recursive:true});
await (await PresentationFile.exportPptx(pres)).save(output);
if(previewDir){await fs.mkdir(previewDir,{recursive:true});for(const [i,s] of pres.slides.items.entries()){const png=await pres.export({slide:s,format:'png',scale:1});await fs.writeFile(path.join(previewDir,`slide-${String(i+1).padStart(2,'0')}.png`),new Uint8Array(await png.arrayBuffer()));}await fs.writeFile(path.join(previewDir,'requirements.json'),JSON.stringify({requiredNativeChartOwnerSlides:[...new Set(chartOwners)],requiredNativeTableOwnerSlides:tableOwners,fontPolicy:{basis:'design',families:[font]},slideCount:pres.slides.items.length}));}
console.log(JSON.stringify({slides:pres.slides.items.length}));
