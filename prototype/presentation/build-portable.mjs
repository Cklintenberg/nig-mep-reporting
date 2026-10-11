/** Portable deterministic renderer. Public npm dependencies only; no AI/network calls. */
import fs from 'node:fs/promises';
import path from 'node:path';
import pptxgen from 'pptxgenjs';
const [input,output]=process.argv.slice(2);
if(!input||!output) throw new Error('Usage: build-portable.mjs report.json output.pptx');
const r=JSON.parse(await fs.readFile(input,'utf8'));
const pptx=new pptxgen();
pptx.layout='LAYOUT_WIDE';
pptx.author='NIG case study'; pptx.subject='Synthetic MEP reporting prototype';
pptx.title=`Weekly ${r.pack.report_type||'Engineering'} review`;
pptx.lang='en-GB';
pptx.theme={headFontFace:'Arial',bodyFontFace:'Arial',lang:'en-GB'};
const C={navy:'0F1743',ink:'18213D',soft:'59647C',purple:'7962D7',teal:'079C93',orange:'D27928',blue:'3676DB',lime:'A3E635'};
let count=0;
const num=v=>v==null?'Not supplied':Number(v).toLocaleString('en-US',{maximumFractionDigits:4});
const delta=m=>m.delta==null?'Change unavailable':`${m.delta>0?'+':''}${num(m.delta)}${m.delta_kind==='relative %'?'% vs previous week':' '+m.delta_kind}`;
function text(sl,value,x,y,w,h,size=22,color=C.ink,bold=false){sl.addText(String(value),{x,y,w,h,fontFace:'Arial',fontSize:size,color,bold,margin:0,breakLine:false,valign:'top',fit:'shrink'});}
function slide(title,subtitle='',dark=false){const sl=pptx.addSlide();count++;sl.background={color:dark?C.navy:'FFFFFF'};
 text(sl,title,.65,.55,12.0,1.0,title.length>70?28:34,dark?'FFFFFF':C.ink,true);
 if(subtitle)text(sl,subtitle,.65,1.65,12.0,.7,17,dark?'B6C3E0':C.soft);
 text(sl,`NIG / MEP · Internal preparation · ${r.pack.week_start}`,.65,7.05,11.3,.23,10,dark?'B6C3E0':C.soft);
 text(sl,String(count).padStart(2,'0'),12.1,7.05,.55,.23,10,dark?'B6C3E0':C.soft);
 return sl;
}
function notes(sl,body){sl.addNotes(body+'\n\nReview before use or sharing. Downloading is not approval. No automatic sending or task creation.');}
function split(value,limit){let s=String(value),out=[];while(s.length>limit){let n=s.lastIndexOf(' ',limit);if(n<limit/2)n=limit;out.push(s.slice(0,n));s=s.slice(n).trimStart();}if(s)out.push(s);return out;}
function table(sl,rows,widths,y=2.5){sl.addTable(rows.map((row,i)=>row.map(value=>({text:String(value),options:{fill:i===0?C.navy:i%2?'F3F5FA':'FFFFFF',color:i===0?'FFFFFF':C.ink,bold:i===0}}))),{x:.65,y,w:12.0,colW:widths,fontFace:'Arial',fontSize:17,margin:10,border:{type:'solid',pt:.5,color:'DFE4ED'},rowH:.72,autoPage:false,valign:'top'});}
let sl=slide(pptx.title,`Week of ${r.pack.week_start}`,true);
text(sl,'A shared view for the next conversation',.65,2.8,11.8,1.3,42,'FFFFFF',true);
text(sl,[r.metrics.length?'Platform figures':'',r.pack.sources.length?'Meeting evidence':''].filter(Boolean).join(' and '),.65,4.5,12,.5,24,C.lime);
text(sl,'Prepared for your meeting',.65,5.5,12,.5,22,'FFFFFF');
text(sl,'Internal BD preparation. Check the recipient and sensitive content before sharing.',.65,6.15,12,.6,17,'B6C3E0');
notes(sl,`Generated ${r.pack.report_type} report. Input fingerprint: ${r.input_hash}. Content reused without additional AI interpretation.`);
if(r.metrics.length){
 const colors=[C.purple,C.teal,C.orange,C.blue];
 sl=slide('Platform signals','Current reporting week. Changes compare the same cohort with the previous week.');
 r.metrics.forEach((m,i)=>{const x=.65+(i%2)*6.1,y=2.7+Math.floor(i/2)*1.85;
 text(sl,m.label,x,y,5.5,.4,20,C.soft);text(sl,num(m.current)+(m.current!=null&&m.unit==='%'?'%':''),x,y+.45,5.5,.7,42,colors[i%4],true);
 text(sl,(m.unit==='%'?'':m.unit+' · ')+delta(m),x,y+1.2,5.5,.5,17);
 });notes(sl,JSON.stringify(r.metrics,null,2));
 for(let start=0;start<r.metrics.length;start+=2){sl=slide('Changes in platform performance','Each chart uses its own units. Missing values stay missing.');
 r.metrics.slice(start,start+2).forEach((m,i)=>{const x=.65+i*6.1;
 text(sl,m.label,x,2.5,5.5,.45,23,colors[(start+i)%4],true);
 const present=[['Previous week',m.previous],['Reporting week',m.current]].filter(p=>p[1]!=null);
 if(present.length)sl.addChart(pptx.ChartType.bar,[{name:m.label,labels:present.map(p=>p[0]),values:present.map(p=>p[1])}],{x,y:3.1,w:5.5,h:2.95,barDir:'col',catAxisLabelFontSize:13,valAxisLabelFontSize:12,chartColors:[colors[(start+i)%4]],showLegend:false,showValue:true,dataLabelPosition:'outEnd',dataLabelFormatCode:m.unit==='%'?'0.0"%"':m.unit==='users'?'#,##0':'0.0',valAxisMinVal:0,...(m.key==='availability'?{valAxisMaxVal:100}:{}),showBorder:false,showCatName:false});
 else text(sl,'No values supplied',x,4,5.5,.5,24,C.soft);
 text(sl,`${m.unit} · ${delta(m)}`,x,6.3,5.5,.5,17,C.soft);
 });notes(sl,'Charts reuse validated values. Missing periods are omitted, never replaced with zero. All axes start at zero.');}
 sl=slide('Figures for the meeting',`Cohort: ${r.metrics[0].cohort}`);
 table(sl,[['Metric','Previous','Current','Change'],...r.metrics.map(m=>[`${m.label} (${m.unit})`,num(m.previous),num(m.current),delta(m)])],[3.8,2,2,4.2]);
 notes(sl,JSON.stringify(r.metrics,null,2));
}
for(const [i,f] of r.narrative.findings.entries()){
 const parts=split(f.summary,350);
 for(const [j,part] of parts.entries()){
 sl=slide(f.title,`Discussion point ${i+1} · ${f.category}${parts.length>1?' · Part '+(j+1)+' of '+parts.length:''}`);
 text(sl,part,.65,2.7,12,2.75,24);
 if(f.needs_review){text(sl,'Review context',.65,5.65,12,.35,17,C.orange,true);text(sl,f.review_reason,.65,6.05,12,.8,16,C.soft);}
 else text(sl,'Source references: '+[...new Set(f.evidence.map(e=>e.source_id))].join(', '),.65,6.1,12,.7,17,C.soft);
 notes(sl,f.summary+(f.needs_review?'\nReview context: '+f.review_reason:''));
 }
}
// Split long questions/warnings instead of silently dropping text.
const questions=r.narrative.discussion_questions.flatMap((q,i)=>split(q,190).map((part,j)=>[`${i+1}${j?' (continued)':''}`,part,'Discuss / confirm']));
for(let i=0;i<questions.length;i+=3){sl=slide('Questions for the meeting','Discussion prompts, not assigned tasks or agreed commitments.');table(sl,[['#','Question','Status'],...questions.slice(i,i+3)],[.9,8.7,2.4]);notes(sl,r.narrative.discussion_questions.join('\n\n'));}
const warnings=r.issues.flatMap(i=>split(i.message,220).map(part=>[i.severity==='error'?'Blocked':'Data gap',part]));
for(let i=0;i<warnings.length;i+=3){sl=slide('What remains uncertain','Keep these limitations visible when interpreting the report.');table(sl,[['Type','Review note'],...warnings.slice(i,i+3)],[1.9,10.1]);notes(sl,JSON.stringify(r.issues,null,2));}
await fs.mkdir(path.dirname(output),{recursive:true});
await pptx.writeFile({fileName:output});
console.log(JSON.stringify({slides:count,renderer:'pptxgenjs'}));
