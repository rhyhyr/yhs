"""Archive source-only extraction outputs that violate the frozen citation rule."""
import json
from pathlib import Path
from run_translation_e2e import validate_extraction
OUT=Path(__file__).resolve().parent/'results/translation_e2e'
rows={r['id']:r for r in json.loads((OUT/'collection.json').read_text(encoding='utf-8'))}
archive=OUT/'rejected-citation-audits'
archive.mkdir(exist_ok=True)
rejected=[]
for path in sorted(OUT.glob('ready-audit-*.json')):
    i=int(path.stem.split('-')[-1])
    if i not in rows: continue
    cached=json.loads(path.read_text(encoding='utf-8'))
    try: validate_extraction({'items':cached['items']},rows[i]['korean_source_answer'])
    except AssertionError as exc:
        patterns=[f'ready-audit-{i:02d}.json',f'critical-source-{i:02d}.json',f'judge-{i:02d}-*.json']
        archived=[]
        for pattern in patterns:
            for src in OUT.glob(pattern):
                absolute=src.resolve()
                assert absolute.parent==OUT.resolve() and archive.resolve().parent==OUT.resolve()
                target=archive/src.name
                assert not target.exists()
                src.rename(target)
                archived.append(src.name)
        rejected.append({'id':i,'reason':str(exc),'archived':archived})
(archive/'manifest.json').write_text(json.dumps(rejected,ensure_ascii=False,indent=2),encoding='utf-8')
print('Original citation-exclusion rule enforced; archived IDs:',[x['id'] for x in rejected])
