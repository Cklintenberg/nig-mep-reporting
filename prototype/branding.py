"""Local SVG assets. NIG is an original concept mark for the fictional case."""
import base64
from pathlib import Path
from html import escape

ROOT=Path(__file__).resolve().parent/'assets'


def logo(name, width=44):
    paths={'SharePoint':'integrations/sharepoint.svg','OneDrive for Business':'integrations/onedrive.svg',
           'Microsoft Teams':'integrations/teams.svg','Google Workspace':'integrations/google.svg',
           'Zoom':'integrations/zoom.svg','Platform analytics':'integrations/analytics.svg',
           'Email':'integrations/email.svg','NIG':'nig.svg'}
    raw=(ROOT/paths[name]).read_bytes()
    src='data:image/svg+xml;base64,'+base64.b64encode(raw).decode()
    return f'<img src="{src}" alt="{escape(name)} logo" style="width:{width}px;max-height:44px;object-fit:contain;flex-shrink:0"/>'
