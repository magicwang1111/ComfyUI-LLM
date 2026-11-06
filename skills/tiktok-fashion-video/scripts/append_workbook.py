import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import zipfile
from xml.sax.saxutils import escape, quoteattr
from lxml import etree as E
from PIL import Image

NS = {'s':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
REL = 'http://schemas.openxmlformats.org/package/2006/relationships'
DOCREL = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    p=argparse.ArgumentParser(description='Limited byte-preserving append for the verified BC workbook layout.')
    p.add_argument('--workbook',type=Path,required=True)
    p.add_argument('--run-dir',type=Path,required=True)
    p.add_argument('--photo',type=Path,required=True)
    p.add_argument('--sheet',default='bnmb')
    p.add_argument('--commit',action='store_true')
    args=p.parse_args()
    run=args.run_dir
    receipt=run/'excel-append.json'
    if receipt.exists() and json.loads(receipt.read_text(encoding='utf-8')).get('committed'):
        raise SystemExit('Append already committed. Do not append another row.')
    product=json.loads((run/'analysis.json').read_text(encoding='utf-8'))
    qc=json.loads((run/'qc.json').read_text(encoding='utf-8'))
    publication=json.loads((run/'publication.json').read_text(encoding='utf-8'))
    probe=json.loads((run/'ffprobe.json').read_text(encoding='utf-8'))
    assert any(s['codec_type']=='video' for s in probe['streams'])
    assert any(s['codec_type']=='audio' for s in probe['streams'])
    assert publication['public_unauthenticated_get_verified'] and (run/'final.mp4').is_file()
    assert re.fullmatch(r'\d{19}',product['pid'])
    assert qc['transcript_english'] and qc['translation_chinese']
    original_hash=sha(args.workbook)
    z=zipfile.ZipFile(args.workbook)
    content={name:z.read(name) for name in z.namelist()}
    wb=E.fromstring(content['xl/workbook.xml'])
    sheet=next(s for s in wb.findall('s:sheets/s:sheet',NS) if s.get('name')==args.sheet)
    rid=sheet.get('{'+DOCREL+'}id')
    target=next(r.get('Target') for r in E.fromstring(content['xl/_rels/workbook.xml.rels']) if r.get('Id')==rid)
    sheet_name='xl/'+target
    root=E.fromstring(content[sheet_name])
    strings=[''.join(x.itertext()) for x in E.fromstring(content['xl/sharedStrings.xml'])]
    def value(cell):
        v=cell.find('s:v',NS)
        if cell.get('t')=='s' and v is not None: return strings[int(v.text)]
        return ''.join(cell.itertext())
    rows=root.findall('s:sheetData/s:row',NS)
    populated=[r for r in rows if any(value(c) for c in r)]
    last=populated[-1]
    number=int(last.get('r'))+1
    previous_code=value(last.find(f's:c[@r="A{number-1}"]',NS))
    match=re.fullmatch(r'([A-Za-z]+)(\d+)',previous_code)
    assert match, 'Unexpected sequence convention'
    code=match[1]+str(int(match[2])+1)
    for r in rows:
        cells={re.sub(r'\d','',c.get('r')):value(c) for c in r}
        assert not (cells.get('B')==product['pid'] and cells.get('I')==publication['url']), 'Already appended'
    target_row=next((r for r in rows if int(r.get('r'))==number),None)
    assert target_row is None or not any(value(c) for c in target_row), 'Append target contains data'
    values={'A':code,'B':product['pid'],'C':product['title'],'D':'','E':'','F':'','G':qc['translation_chinese'],'H':qc['transcript_english'],'I':publication['url'],'J':qc['caption_english'],'K':' '.join(qc['hashtags']),'L':'','M':'','N':''}
    styles={'A':2,'B':20,'C':14,'D':25,'E':42,'F':20,'G':4,'H':4,'I':4,'J':4,'K':4,'L':43,'M':4,'N':4}
    # This fallback deliberately supports the inspected BC styles, not arbitrary templates.
    xfs=E.fromstring(content['xl/styles.xml']).find('s:cellXfs',NS)
    assert len(xfs)>max(styles.values()), 'Workbook style layout differs'
    styles_xml=content['xl/styles.xml'].decode('utf-8')
    xfs_block=re.search(r'<cellXfs\b[^>]*>(.*?)</cellXfs>',styles_xml,re.S)
    raw_styles=re.findall(r'<xf\b[^>]*(?:/>|>.*?</xf>)',xfs_block[1],re.S)
    assert len(raw_styles)==len(xfs)
    text_style=re.sub(r'numFmtId="\d+"','numFmtId="49"',raw_styles[20])
    text_style=re.sub(r'applyNumberFormat="[^"]+"','applyNumberFormat="true"',text_style)
    styles['B']=len(xfs)
    styles_xml=styles_xml.replace('</cellXfs>',text_style+'</cellXfs>')
    styles_xml=re.sub(r'(<cellXfs\b[^>]*count=")\d+("[^>]*>)',rf'\g<1>{len(xfs)+1}\g<2>',styles_xml,count=1)
    new_row=f'<row r="{number}" customHeight="true" ht="240">'
    for col,text in values.items():
        new_row+=f'<c r="{col}{number}" s="{styles[col]}" t="inlineStr"><is><t xml:space="preserve">{escape(text)}</t></is></c>'
    new_row+='</row>'
    sheet_xml=content[sheet_name].decode('utf-8')
    row_pattern=rf'<row\b(?=[^>]*\br="{number}")[^>]*>.*?</row>'
    if target_row is not None:
        sheet_xml,count=re.subn(row_pattern,lambda _:new_row,sheet_xml,count=1,flags=re.S)
        assert count==1
    else:
        sheet_xml=sheet_xml.replace('</sheetData>',new_row+'</sheetData>')
    sheet_rel_name=str(Path(sheet_name).parent/'_rels'/(Path(sheet_name).name+'.rels')).replace('\\','/')
    sheet_rels=content[sheet_rel_name].decode('utf-8')
    relationships=E.fromstring(content[sheet_rel_name])
    draw_rel=next(r for r in relationships if r.get('Type').endswith('/drawing'))
    draw_name=os.path.normpath(str(Path(sheet_name).parent/draw_rel.get('Target'))).replace('\\','/')
    draw_rel_name=str(Path(draw_name).parent/'_rels'/(Path(draw_name).name+'.rels')).replace('\\','/')
    draw_xml=content[draw_name].decode('utf-8')
    draw_rels=content[draw_rel_name].decode('utf-8')
    next_id=max(int(x) for x in re.findall(r'Id="rId(\d+)"',draw_rels))+1
    pic_id=max(int(x) for x in re.findall(r'cNvPr id="(\d+)"',draw_xml))+1
    anchors=re.findall(r'<xdr:twoCellAnchor\b.*?</xdr:twoCellAnchor>',draw_xml,re.S)
    anchor=anchors[-1]
    anchor=re.sub(r'(<xdr:from>.*?<xdr:row>)\d+(</xdr:row>)',rf'\g<1>{number-1}\g<2>',anchor,flags=re.S)
    anchor=re.sub(r'(<xdr:to>.*?<xdr:row>)\d+(</xdr:row>)',rf'\g<1>{number}\g<2>',anchor,flags=re.S)
    # Fit the original photo proportionally inside the existing narrow style column.
    with Image.open(args.photo) as im:
        photo_width=56
        photo_height=photo_width*im.height/im.width
    anchor=re.sub(r'<xdr:from>.*?</xdr:from>',f'<xdr:from><xdr:col>5</xdr:col><xdr:colOff>38100</xdr:colOff><xdr:row>{number-1}</xdr:row><xdr:rowOff>38100</xdr:rowOff></xdr:from>',anchor,flags=re.S)
    anchor=re.sub(r'<xdr:to>.*?</xdr:to>',f'<xdr:to><xdr:col>5</xdr:col><xdr:colOff>{round((4+photo_width)*9525)}</xdr:colOff><xdr:row>{number-1}</xdr:row><xdr:rowOff>{round((4+photo_height)*9525)}</xdr:rowOff></xdr:to>',anchor,flags=re.S)
    anchor=re.sub(r'<xdr:cNvPr\b[^>]*>',f'<xdr:cNvPr id="{pic_id}" name="Picture {pic_id}" descr="Original product 01 PID {product["pid"]}">',anchor)
    anchor=re.sub(r'r:embed="rId\d+"',f'r:embed="rId{next_id}"',anchor)
    draw_xml=draw_xml.replace('</xdr:wsDr>',anchor+'</xdr:wsDr>')
    photo_name=f'tiktok-{product["pid"]}-{number}.jpg'
    media_name='xl/media/'+photo_name
    assert media_name not in content
    draw_rels=draw_rels.replace('</Relationships>',f'<Relationship Id="rId{next_id}" Target="../media/{photo_name}" Type="{DOCREL}/image"/></Relationships>')
    link_id=max(int(x) for x in re.findall(r'Id="rId(\d+)"',sheet_rels))+1
    sheet_rels=sheet_rels.replace('</Relationships>',f'<Relationship Id="rId{link_id}" Target={quoteattr(publication["url"])} Type="{DOCREL}/hyperlink" TargetMode="External"/></Relationships>')
    hyperlink=f'<hyperlink ref="I{number}" r:id="rId{link_id}"/>'
    assert '</hyperlinks>' in sheet_xml, 'Unexpected workbook without hyperlink section'
    sheet_xml=sheet_xml.replace('</hyperlinks>',hyperlink+'</hyperlinks>')
    updates={sheet_name:sheet_xml.encode(),sheet_rel_name:sheet_rels.encode(),draw_name:draw_xml.encode(),draw_rel_name:draw_rels.encode(),media_name:args.photo.read_bytes(),'xl/styles.xml':styles_xml.encode()}
    types=content['[Content_Types].xml'].decode('utf-8')
    if not re.search(r'<Default\b[^>]*Extension="jpg"',types):
        updates['[Content_Types].xml']=types.replace('</Types>','<Default Extension="jpg" ContentType="image/jpeg"/></Types>').encode()
    # Every pre-existing row except the blank destination must remain byte-for-byte identical.
    old_rows=re.findall(r'<row\b.*?</row>',content[sheet_name].decode(),re.S)
    new_rows=re.findall(r'<row\b.*?</row>',sheet_xml,re.S)
    old_other=[r for r in old_rows if not re.match(row_pattern,r,re.S)]
    new_other=[r for r in new_rows if not re.match(row_pattern,r,re.S)]
    assert old_other==new_other
    backup=run/(args.workbook.stem+'.before-append.xlsx')
    if backup.exists():
        assert sha(backup)==original_hash, 'Existing backup differs from current source'
    else:
        shutil.copy2(args.workbook,backup)
    staged=run/(args.workbook.stem+'.staged.xlsx')
    with zipfile.ZipFile(staged,'w',zipfile.ZIP_DEFLATED) as out:
        for info in z.infolist():
            out.writestr(info,updates.get(info.filename,content[info.filename]))
        for name,data in updates.items():
            if name not in content: out.writestr(name,data)
    z.close()
    with zipfile.ZipFile(staged) as check:
        assert check.testzip() is None
        assert all(check.read(name)==data for name,data in content.items() if name not in updates)
        assert all(check.read(name)==data for name,data in content.items() if name.startswith('xl/media/'))
        read_row=E.fromstring(check.read(sheet_name)).find(f's:sheetData/s:row[@r="{number}"]',NS)
        actual={re.sub(r'\d','',c.get('r')):''.join(c.itertext()) for c in read_row}
        assert actual==values
        assert read_row.find(f's:c[@r="B{number}"]',NS).get('t')=='inlineStr'
        assert check.read(media_name)==args.photo.read_bytes()
    result={'workbook':str(args.workbook.resolve()),'sheet':args.sheet,'row':number,'sequence':code,'pid':product['pid'],'backup':str(backup.resolve()),'staged':str(staged.resolve()),'original_sha256':original_hash,'staged_sha256':sha(staged),'committed':False,'fallback_reason':'Artifact Tool export failed with Arg_OutOfMemoryException; scoped ZIP/XML append preserves native parts.','verification':{'old_rows_unchanged':True,'all_other_zip_parts_identical':True,'existing_media_preserved':len([n for n in content if n.startswith('xl/media/')]),'new_photo_sha256':sha(args.photo),'readback_exact':True,'pid_is_text':True,'changed_existing_parts':[n for n in updates if n in content]},'values':values}
    if args.commit:
        assert sha(args.workbook)==original_hash,'Workbook changed during preparation'
        commit_tmp=run/'workbook-commit.tmp'
        shutil.copy2(staged,commit_tmp)
        try:
            os.replace(commit_tmp,args.workbook)
            assert sha(args.workbook)==sha(staged)
            result['committed']=True
        except PermissionError:
            result['error']='Original workbook is locked; staged result and backup preserved.'
    receipt.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({k:result[k] for k in ['sheet','row','sequence','committed','backup','verification']},ensure_ascii=False))

if __name__=='__main__':
    main()
