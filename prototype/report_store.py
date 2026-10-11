"""Local report history. Drafts include source evidence, never environment credentials."""
from datetime import datetime, timezone
import json
from pathlib import Path
from uuid import UUID, uuid4

ROOT = Path(__file__).resolve().parent


def save_draft(report, draft_id=None):
    draft_id = str(UUID(draft_id)) if draft_id else str(uuid4())
    folder = ROOT / 'runs' / 'drafts'
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f'{draft_id}.json'
    now = datetime.now(timezone.utc).isoformat()
    previous = json.loads(path.read_text()) if path.exists() else {}
    if previous.get('report') != report:
        record = {'id': draft_id, 'created_at': previous.get('created_at', now),
                  'updated_at': now, 'report': report}
        temporary = path.with_suffix('.tmp')
        temporary.write_text(json.dumps(record, indent=2, ensure_ascii=False))
        temporary.replace(path)
    return draft_id


def list_reports():
    entries = []
    paths = list((ROOT / 'runs' / 'drafts').glob('*.json'))
    paths += list((ROOT / 'runs').glob('*/report.json'))
    for path in paths:
        try:
            data = json.loads(path.read_text())
            draft = path.parent.name == 'drafts'
            report = data['report'] if draft else data
            entries.append({'path': str(path), 'draft_id': data['id'] if draft else None,
                            'week': report['pack']['week_start'],
                            'report_type': report['pack'].get('report_type','Engineering'),
                            'model': report['usage']['model'],
                            'status': 'Approved' if report.get('approval') else 'Draft',
                            'updated_at': data['updated_at'] if draft else report['approval']['approved_at'],
                            'report': report})
        except (OSError, ValueError, KeyError, TypeError):
            # An incomplete/corrupt local record must not hide the rest of the library.
            continue
    return sorted(entries, key=lambda entry: entry['updated_at'], reverse=True)
