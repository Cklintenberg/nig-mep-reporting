"""Embed editable chart-data snapshots in our generated PowerPoint package.

Only the renderer's single-series category charts are supported. Values are copied
from chart literals; no source-workbook formulas or links are inferred.
"""
from copy import deepcopy
from io import BytesIO
from pathlib import PurePosixPath
import xml.etree.ElementTree as ET
import zipfile
import re
from openpyxl import Workbook

C='http://schemas.openxmlformats.org/drawingml/2006/chart'
R='http://schemas.openxmlformats.org/officeDocument/2006/relationships'
P='http://schemas.openxmlformats.org/package/2006/relationships'
T='http://schemas.openxmlformats.org/package/2006/content-types'
ET.register_namespace('c',C);ET.register_namespace('r',R)


def embed_chart_workbooks(path):
    with zipfile.ZipFile(path) as z:
        parts={n:z.read(n) for n in z.namelist()}
    content=ET.fromstring(parts['[Content_Types].xml'])
    charts=[n for n in parts if '/charts/' in n and n.endswith('.xml') and '/_rels/' not in n]
    for index,name in enumerate(charts,1):
        chart=ET.fromstring(parts[name])
        if chart.find(f'{{{C}}}externalData') is not None:
            continue
        series=chart.findall(f'.//{{{C}}}ser')
        if len(series)!=1:raise ValueError('Unsupported chart series layout in PowerPoint export.')
        ser=series[0];cat=ser.find(f'{{{C}}}cat');val=ser.find(f'{{{C}}}val')
        cats=cat.find(f'{{{C}}}strLit');vals=val.find(f'{{{C}}}numLit')
        if cats is None or vals is None:raise ValueError('Chart data is not a complete literal snapshot.')
        categories=[p.find(f'{{{C}}}v').text for p in cats.findall(f'{{{C}}}pt')]
        exact_numbers=[p.find(f'{{{C}}}v').text for p in vals.findall(f'{{{C}}}pt')]
        numbers=[float(v) for v in exact_numbers]
        if len(categories)!=len(numbers) or not categories:raise ValueError('Chart categories and values differ.')
        title=ser.find(f'{{{C}}}tx/{{{C}}}v').text
        wb=Workbook();ws=wb.active;ws.title='Data';ws.append(['Period',title])
        for label,v in zip(categories,numbers):ws.append([label,v])
        for row in ws:
            for cell in row:
                if isinstance(cell.value,str):cell.data_type='s'
        raw=BytesIO();wb.save(raw)
        # Preserve literal decimal spelling; openpyxl's float formatter can expand 99.9.
        with zipfile.ZipFile(BytesIO(raw.getvalue())) as archive:
            cells={n:archive.read(n) for n in archive.namelist()}
        sheet=cells['xl/worksheets/sheet1.xml'].decode()
        for row,v in enumerate(exact_numbers,2):
            sheet=re.sub(r'(<c r="B'+str(row)+r'"[^>]*><v>)[^<]*(</v>)',lambda m:m[1]+v+m[2],sheet)
        cells['xl/worksheets/sheet1.xml']=sheet.encode()
        exact=BytesIO()
        with zipfile.ZipFile(exact,'w',zipfile.ZIP_DEFLATED) as archive:
            for part,data in cells.items():archive.writestr(part,data)
        workbook=f'ppt/slides/embeddings/mep-chart-{index}.xlsx';parts[workbook]=exact.getvalue()
        for parent,literal,kind,col in [(cat,cats,'str','A'),(val,vals,'num','B')]:
            parent.remove(literal);ref=ET.SubElement(parent,f'{{{C}}}{kind}Ref')
            ET.SubElement(ref,f'{{{C}}}f').text=f"Data!${col}$2:${col}${len(categories)+1}"
            cache=deepcopy(literal);cache.tag=f'{{{C}}}{kind}Cache';ref.append(cache)
        rel_id='rIdMEPWorkbook'
        external=ET.SubElement(chart,f'{{{C}}}externalData',{f'{{{R}}}id':rel_id})
        ET.SubElement(external,f'{{{C}}}autoUpdate',{'val':'0'})
        relpath=str(PurePosixPath(name).parent/'_rels'/(PurePosixPath(name).name+'.rels'))
        relationships=ET.fromstring(parts[relpath]) if relpath in parts else ET.Element(f'{{{P}}}Relationships')
        ET.SubElement(relationships,f'{{{P}}}Relationship',{'Id':rel_id,'Type':R+'/package','Target':'../embeddings/'+PurePosixPath(workbook).name})
        parts[relpath]=ET.tostring(relationships,encoding='utf-8',xml_declaration=True)
        parts[name]=ET.tostring(chart,encoding='utf-8',xml_declaration=True)
    if charts and not any(e.get('Extension')=='xlsx' for e in content):
        ET.SubElement(content,f'{{{T}}}Default',{'Extension':'xlsx','ContentType':'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'})
    ET.register_namespace('',T)
    parts['[Content_Types].xml']=ET.tostring(content,encoding='utf-8',xml_declaration=True)
    with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED) as z:
        for name,data in parts.items():z.writestr(name,data)
