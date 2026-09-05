from html import escape
from xml.etree.ElementTree import Element, SubElement, tostring

from fastapi import Depends, FastAPI, Form, HTTPException, Query
from fastapi.responses import HTMLResponse, Response
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from . import __version__
from .config import settings
from .db import Base, SessionLocal, engine, get_db
from .models import ApiKey, NNTPProvider, Release, UsenetArticle, UsenetGroup
from .nzb import build_nzb
from .scanner import scan_group
from .search import search_releases
from .seed import seed_default_groups

app = FastAPI(title="Narra", version=__version__)


@app.on_event("startup")
def startup() -> None:
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        seed_default_groups(db)


def page(title: str, body: str) -> HTMLResponse:
    html = f"""<!doctype html>
<html><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>
<title>{escape(title)} · Narra</title>
<style>
body{{margin:0;font-family:Inter,system-ui,-apple-system,sans-serif;background:#f7f7fb;color:#1f2230}}
header{{background:#fff;border-bottom:1px solid #e5e7ef;padding:16px 28px;display:flex;align-items:center;gap:28px;position:sticky;top:0}}
.brand{{font-size:24px;font-weight:800;letter-spacing:-.04em}} nav a{{margin-right:18px;color:#555b70;text-decoration:none;font-weight:600}}
main{{max-width:1180px;margin:28px auto;padding:0 22px}} .card{{background:#fff;border:1px solid #e6e8ef;border-radius:14px;padding:20px;margin-bottom:18px;box-shadow:0 4px 20px rgba(30,34,50,.04)}}
.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:14px}} .metric{{font-size:30px;font-weight:800}} .muted{{color:#73798e}} input,button{{font:inherit;padding:10px 12px;border-radius:9px;border:1px solid #cfd3df}} button{{background:#2d3559;color:#fff;border:0;font-weight:700;cursor:pointer}} table{{width:100%;border-collapse:collapse}} th,td{{padding:12px 8px;border-bottom:1px solid #edf0f5;text-align:left}} .ok{{color:#18794e;font-weight:700}} .bad{{color:#b42318;font-weight:700}} code{{background:#f1f3f7;padding:2px 5px;border-radius:5px}}
</style></head><body>
<header><div class='brand'>Narra</div><nav><a href='/'>Dashboard</a><a href='/search'>Search</a><a href='/settings'>Settings</a></nav><div class='muted' style='margin-left:auto'>{escape(__version__)}</div></header>
<main>{body}</main></body></html>"""
    return HTMLResponse(html)


def valid_api_key(db: Session, supplied: str | None) -> bool:
    if supplied and supplied == settings.api_key:
        return True
    if not supplied:
        return False
    return db.scalar(select(ApiKey.id).where(ApiKey.key == supplied, ApiKey.enabled.is_(True))) is not None


@app.get("/", response_class=HTMLResponse)
def dashboard(db: Session = Depends(get_db)):
    releases = db.scalar(select(func.count(Release.id))) or 0
    accepted = db.scalar(select(func.count(Release.id)).where(Release.accepted.is_(True))) or 0
    groups = db.scalar(select(func.count(UsenetGroup.id)).where(UsenetGroup.enabled.is_(True))) or 0
    providers = db.scalar(select(func.count(NNTPProvider.id)).where(NNTPProvider.enabled.is_(True))) or 0
    latest = db.scalars(select(Release).order_by(Release.id.desc()).limit(12)).all()
    rows = ''.join(
        f"<tr><td><a href='/release/{r.id}'>{escape(r.title)}</a></td><td>{escape(r.group_name)}</td><td>{r.completion:.0%}</td><td class='{'ok' if r.accepted else 'bad'}'>{'Accepted' if r.accepted else 'Rejected'}</td><td>{r.classification_score}</td></tr>"
        for r in latest
    ) or "<tr><td colspan='5' class='muted'>No indexed releases yet.</td></tr>"
    return page("Dashboard", f"""
<div class='grid'><div class='card'><div class='metric'>{releases}</div><div class='muted'>Discovered releases</div></div><div class='card'><div class='metric'>{accepted}</div><div class='muted'>Audiobooks accepted</div></div><div class='card'><div class='metric'>{groups}</div><div class='muted'>Enabled groups</div></div><div class='card'><div class='metric'>{providers}</div><div class='muted'>NNTP providers</div></div></div>
<div class='card'><h2>Latest discoveries</h2><table><tr><th>Release</th><th>Group</th><th>Complete</th><th>Decision</th><th>Score</th></tr>{rows}</table></div>""")


@app.get("/search", response_class=HTMLResponse)
def search_ui(q: str = "", db: Session = Depends(get_db)):
    results = search_releases(db, q, accepted_only=True, limit=100)
    rows = ''.join(f"<tr><td><a href='/release/{r.id}'>{escape(r.title)}</a></td><td>{escape(r.group_name)}</td><td>{r.size_bytes}</td><td>{r.completion:.0%}</td></tr>" for r in results)
    if not rows:
        rows = "<tr><td colspan='4' class='muted'>No matching audiobooks.</td></tr>"
    return page("Search", f"<div class='card'><h1>Audiobook search</h1><form><input name='q' value='{escape(q)}' placeholder='Title, author, narrator, series, ISBN or ASIN' style='width:min(650px,70vw)'><button>Search</button></form></div><div class='card'><table><tr><th>Title</th><th>Group</th><th>Bytes</th><th>Complete</th></tr>{rows}</table></div>")


@app.get("/release/{release_id}", response_class=HTMLResponse)
def release_detail(release_id: int, db: Session = Depends(get_db)):
    release = db.get(Release, release_id)
    if not release:
        raise HTTPException(404)
    articles = db.scalars(select(UsenetArticle).where(UsenetArticle.release_id == release_id).order_by(UsenetArticle.article_number)).all()
    article_rows = ''.join(f"<tr><td>{a.article_number}</td><td>{escape(a.message_id)}</td><td>{a.bytes}</td></tr>" for a in articles)
    return page(release.title, f"<div class='card'><h1>{escape(release.title)}</h1><p><b>Classification:</b> {'Accepted' if release.accepted else 'Rejected'} ({release.classification_score})</p><p><b>Reasons:</b> {escape(release.reasons)}</p><p><b>Completeness:</b> {release.completion:.1%}</p><p><a href='/nzb/{release.id}'>Download NZB</a></p></div><div class='card'><h2>Articles</h2><table><tr><th>#</th><th>Message ID</th><th>Bytes</th></tr>{article_rows}</table></div>")


@app.get("/settings", response_class=HTMLResponse)
def settings_ui(db: Session = Depends(get_db)):
    providers = db.scalars(select(NNTPProvider).order_by(NNTPProvider.id)).all()
    groups = db.scalars(select(UsenetGroup).order_by(UsenetGroup.name)).all()
    p_rows = ''.join(f"<tr><td>{escape(p.name)}</td><td>{escape(p.host)}:{p.port}</td><td>{'SSL' if p.use_ssl else 'Plain'}</td><td>{p.max_connections}</td></tr>" for p in providers) or "<tr><td colspan='4' class='muted'>No providers.</td></tr>"
    g_rows = ''.join(f"<tr><td>{escape(g.name)}</td><td>{g.high_water}</td><td><form method='post' action='/scan/{g.id}'><button>Scan now</button></form></td></tr>" for g in groups) or "<tr><td colspan='3' class='muted'>No groups.</td></tr>"
    return page("Settings", f"""
<div class='card'><h2>Add NNTP provider</h2><form method='post' action='/providers'><input name='name' placeholder='Name' required> <input name='host' placeholder='news.example.com' required> <input name='port' type='number' value='563'> <input name='username' placeholder='Username'> <input name='password' type='password' placeholder='Password'> <button>Add provider</button></form><table><tr><th>Name</th><th>Server</th><th>Transport</th><th>Connections</th></tr>{p_rows}</table></div>
<div class='card'><h2>Add Usenet group</h2><form method='post' action='/groups'><input name='name' placeholder='alt.binaries.audiobooks' required style='width:340px'> <button>Add group</button></form><table><tr><th>Group</th><th>High-water</th><th>Action</th></tr>{g_rows}</table></div>
<div class='card'><h2>Newznab</h2><p>Development API key: <code>{escape(settings.api_key)}</code></p><p>Endpoint: <code>/api?t=search&amp;q=book&amp;apikey=...</code></p></div>""")


@app.post("/providers")
def add_provider(name: str = Form(...), host: str = Form(...), port: int = Form(563), username: str = Form(""), password: str = Form(""), db: Session = Depends(get_db)):
    db.add(NNTPProvider(name=name, host=host, port=port, username=username or None, password=password or None, use_ssl=True))
    db.commit()
    return Response(status_code=303, headers={'Location': '/settings'})


@app.post("/groups")
def add_group(name: str = Form(...), db: Session = Depends(get_db)):
    existing = db.scalar(select(UsenetGroup).where(UsenetGroup.name == name))
    if not existing:
        db.add(UsenetGroup(name=name, enabled=True, high_water=0))
        db.commit()
    return Response(status_code=303, headers={'Location': '/settings'})


@app.post("/scan/{group_id}")
def run_scan(group_id: int, db: Session = Depends(get_db)):
    provider = db.scalar(select(NNTPProvider).where(NNTPProvider.enabled.is_(True)).order_by(NNTPProvider.id))
    group = db.get(UsenetGroup, group_id)
    if not provider or not group:
        raise HTTPException(400, "Configure an enabled provider and group first")
    scan_group(db, provider, group)
    return Response(status_code=303, headers={'Location': '/'})


@app.get("/nzb/{release_id}")
def nzb_download(release_id: int, db: Session = Depends(get_db)):
    release = db.get(Release, release_id)
    if not release:
        raise HTTPException(404)
    articles = db.scalars(select(UsenetArticle).where(UsenetArticle.release_id == release_id)).all()
    payload = build_nzb(subject=release.subject, poster=release.poster or 'unknown', group=release.group_name, segments=[{'number': a.segment or a.article_number, 'bytes': a.bytes, 'message_id': a.message_id} for a in articles])
    filename = ''.join(c if c.isalnum() or c in ' ._-' else '_' for c in release.title).strip() or f'narra-{release_id}'
    return Response(payload, media_type='application/x-nzb', headers={'Content-Disposition': f'attachment; filename="{filename}.nzb"'})


def newznab_xml(releases: list[Release]) -> bytes:
    rss = Element('rss', {'version': '2.0', 'xmlns:newznab': 'http://www.newznab.com/DTD/2010/feeds/attributes/'})
    channel = SubElement(rss, 'channel')
    SubElement(channel, 'title').text = 'Narra'
    for r in releases:
        item = SubElement(channel, 'item')
        SubElement(item, 'title').text = r.title
        SubElement(item, 'guid', {'isPermaLink': 'false'}).text = f'narra:{r.id}'
        SubElement(item, 'link').text = f'/nzb/{r.id}'
        SubElement(item, 'category').text = 'Audio/Audiobook'
        SubElement(item, '{http://www.newznab.com/DTD/2010/feeds/attributes/}attr', {'name': 'size', 'value': str(r.size_bytes)})
        SubElement(item, '{http://www.newznab.com/DTD/2010/feeds/attributes/}attr', {'name': 'category', 'value': '3030'})
    return b'<?xml version="1.0" encoding="UTF-8"?>\n' + tostring(rss, encoding='utf-8')


@app.get("/api")
def newznab_api(t: str = Query("search"), q: str = Query(""), apikey: str | None = Query(None), db: Session = Depends(get_db)):
    if t == 'caps':
        root = Element('caps')
        SubElement(root, 'server', {'version': __version__, 'title': 'Narra'})
        searches = SubElement(root, 'searching')
        SubElement(searches, 'search', {'available': 'yes', 'supportedParams': 'q'})
        SubElement(searches, 'book-search', {'available': 'yes', 'supportedParams': 'q,author,title'})
        categories = SubElement(root, 'categories')
        audio = SubElement(categories, 'category', {'id': '3000', 'name': 'Audio'})
        SubElement(audio, 'subcat', {'id': '3030', 'name': 'Audiobook'})
        return Response(b'<?xml version="1.0" encoding="UTF-8"?>\n' + tostring(root, encoding='utf-8'), media_type='application/xml')
    if not valid_api_key(db, apikey):
        root = Element('error', {'code': '100', 'description': 'Incorrect user credentials'})
        return Response(tostring(root, encoding='utf-8'), status_code=401, media_type='application/xml')
    releases = search_releases(db, q, accepted_only=True, limit=100)
    return Response(newznab_xml(releases), media_type='application/xml')
