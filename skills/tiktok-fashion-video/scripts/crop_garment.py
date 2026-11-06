import argparse
import hashlib
import json
from pathlib import Path
from PIL import Image, ImageOps

def main():
    parser=argparse.ArgumentParser(description='Crop a genuine product image without redraw; visually review before use.')
    parser.add_argument('--source',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--bounds',nargs=4,type=float,required=True,metavar=('LEFT','TOP','RIGHT','BOTTOM'))
    parser.add_argument('--metadata',type=Path,required=True)
    args=parser.parse_args()
    assert args.source.resolve()!=args.output.resolve(),'Do not overwrite original'
    left,top,right,bottom=args.bounds
    assert 0<=left<right<=1 and 0<=top<bottom<=1
    im=ImageOps.exif_transpose(Image.open(args.source)).convert('RGB')
    px=[round(left*im.width),round(top*im.height),round(right*im.width),round(bottom*im.height)]
    im.crop(px).save(args.output,quality=95)
    result={'source':str(args.source),'source_sha256':hashlib.sha256(args.source.read_bytes()).hexdigest(),'source_size':list(im.size),'bounds_normalized':args.bounds,'bounds_px':px,'crop':str(args.output),'visual_review_required':True}
    args.metadata.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False))

if __name__=='__main__': main()
