"""Record actual accessibility of the preferred reference-free QE model."""
import json
from datetime import datetime,timezone
from pathlib import Path
from huggingface_hub import hf_hub_download
result={'model':'Unbabel/wmt22-cometkiwi-da','file':'hparams.yaml','checked_utc':datetime.now(timezone.utc).isoformat()}
try:
    path=hf_hub_download(result['model'],result['file'])
    result.update(status='accessible',path=path)
except Exception as exc:
    result.update(status='unavailable',exception_type=type(exc).__name__,message=str(exc),http_status=getattr(getattr(exc,'response',None),'status_code',None))
out=Path(__file__).resolve().parent/'results/translation_e2e'
out.mkdir(parents=True,exist_ok=True)
(out/'qe-preflight.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(result,ensure_ascii=False,indent=2))
