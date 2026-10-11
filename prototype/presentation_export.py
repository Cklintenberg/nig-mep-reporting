"""Local, deterministic PowerPoint export of the exact approved snapshot."""
from copy import deepcopy
from hashlib import sha256
import json
import os
import shutil
from pathlib import Path
import subprocess
import tempfile
import zipfile
from exports import content_hash, validate_export
from chart_workbooks import embed_chart_workbooks

ROOT=Path(__file__).resolve().parent
TEMPLATE_VERSION='business-review-v2'


def renderer_config():
    """Keep the rehearsal renderer locally; fresh checkouts use public dependencies."""
    config_file=ROOT/'presentation/runtime.local.json'
    runtime=json.loads(config_file.read_text()) if config_file.exists() else {}
    mode=os.getenv('MEP_EXPORT_RENDERER', 'auto')
    if mode not in {'auto','artifact','portable'}:
        raise RuntimeError('MEP_EXPORT_RENDERER must be auto, portable or artifact.')
    module=os.getenv('MEP_ARTIFACT_MODULE') or runtime.get('artifactModule','')
    use_artifact=mode=='artifact' or (mode=='auto' and bool(module) and Path(module).is_file())
    node=os.getenv('MEP_EXPORT_NODE') or (runtime.get('node') if use_artifact else None) or shutil.which('node')
    return ('artifact' if use_artifact else 'portable'),node,module


def verify_approval(report):
    if not report.get('approval'):
        raise ValueError('Approve this report before exporting a presentation.')
    original=deepcopy(report)
    approval=original.pop('approval')
    if approval.get('content_hash')!=content_hash(original):
        raise ValueError('This report changed after approval. Review and approve it again.')


def presentation_path(report):
    validate_export(report)
    # Include snapshot metadata and renderer content to avoid stale decks after edits or template changes.
    mode,_,_=renderer_config()
    script='build.mjs' if mode=='artifact' else 'build-portable.mjs'
    signature=sha256((content_hash(report)+TEMPLATE_VERSION+mode).encode()+(ROOT/'presentation'/script).read_bytes()+(ROOT/'chart_workbooks.py').read_bytes()+(ROOT/'presentation/package-lock.json').read_bytes()).hexdigest()
    return ROOT/'runs'/'presentations'/f'{signature}.pptx'


def render_presentation(report):
    destination=presentation_path(report)
    if destination.exists():
        return destination
    mode,node,module=renderer_config()
    if not node or not Path(node).is_file() or (mode=='artifact' and not Path(module).is_file()):
        raise RuntimeError('PowerPoint renderer is not configured on this computer. Written reports remain available. See presentation/README.md.')
    destination.parent.mkdir(parents=True,exist_ok=True)
    # Temporary content remains local. No report content or API keys go on the command line.
    with tempfile.TemporaryDirectory(prefix='render-',dir=destination.parent) as tmp:
        source=Path(tmp)/'report.json';candidate=Path(tmp)/'report.pptx'
        source.write_text(json.dumps(report,ensure_ascii=False))
        env={k:os.environ[k] for k in ['PATH','HOME','TMPDIR','LANG'] if k in os.environ}
        if mode=='artifact': env['MEP_ARTIFACT_MODULE']=module
        script='build.mjs' if mode=='artifact' else 'build-portable.mjs'
        try:
            result=subprocess.run([node,str(ROOT/'presentation'/script),str(source),str(candidate)],
                capture_output=True,text=True,timeout=120,env=env,cwd=ROOT)
        except subprocess.TimeoutExpired:
            raise RuntimeError('PowerPoint export timed out. Your report is saved; retry or download the written report.') from None
        if result.returncode or not candidate.exists():
            raise RuntimeError('PowerPoint export could not finish. Your report is saved; download the written report or check the local renderer.')
        if mode=='artifact': embed_chart_workbooks(candidate)
        with zipfile.ZipFile(candidate) as z:
            if z.testzip() or 'ppt/presentation.xml' not in z.namelist():
                raise RuntimeError('PowerPoint export failed its file integrity check.')
        candidate.replace(destination)
    return destination
