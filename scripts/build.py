"""Build only the orthogonal-slider drawing stage; no 3D/story engine."""
from pathlib import Path
import argparse,json
from star_motion import solve_star
from heart_solver import solve_heart

ROOT=Path(__file__).resolve().parents[1]
def validate(c):
    if not isinstance(c,dict) or set(c)-{'shape','color'}:raise ValueError('只支持shape和color设置')
    if c.get('shape') not in ('circle','heart','star'):raise ValueError('当前只支持圆、心形、五角星')
    if c.get('color','auto') not in ('auto','ice','rose','gold','violet'):raise ValueError('不支持的配色')
def build(c,out,export=False):
    validate(c);out=Path(out)
    if out.exists():raise FileExistsError('请另存新文件，保留已有作品')
    a=ROOT/'assets';lic=(ROOT/'LICENSE.txt').read_text('utf-8')
    code='/* 免费非商业试用许可：\n'+lic+'\n*/\n'
    code+='const CONFIG='+json.dumps(c,ensure_ascii=False).replace('<','\\u003c')+';\nconst EXPORT_ENABLED='+str(export).lower()+';\n'
    if c['shape']=='heart':code+='const HEART_DATA='+json.dumps({'rows':solve_heart()['rows']},separators=(',',':'))+';\n'
    if c['shape']=='star':code+='const STAR_DATA='+json.dumps({'rows':solve_star()['rows']},separators=(',',':'))+';\n'
    for f in ['light.js','mechanism.js','player.js']:code+=(a/f).read_text('utf-8')+'\n'
    html=(a/'player.html').read_text('utf-8').replace('__SCRIPT__',code.replace('</script','<\\/script'))
    out.parent.mkdir(parents=True,exist_ok=True);out.write_text(html,'utf-8');print(out.resolve())
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('config');p.add_argument('--out',required=True);p.add_argument('--export-mode',action='store_true');a=p.parse_args();build(json.loads(Path(a.config).read_text('utf-8-sig')),a.out,a.export_mode)
