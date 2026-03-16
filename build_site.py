from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from hashlib import sha1
from html import escape
import json
import posixpath
import re
from pathlib import Path
from urllib.parse import unquote, urljoin, urlparse
from urllib.request import Request, urlopen

from lxml import html

SOURCE_URL = 'https://flash0926.yuque.com/org-wiki-flash0926-kivyu0/gpa1ys'
BASE_HOST = 'https://flash0926.yuque.com'
SITE_DIR = Path('/Users/chenmo/D/codex_agent_workspace/孟德尔随机化修炼手册站')
OUT_INDEX = SITE_DIR / 'index.html'
DOCS_DIR = SITE_DIR / 'docs'
ASSETS_DIR = SITE_DIR / 'assets'
MEDIA_DIR = ASSETS_DIR / 'media'
CACHE_DIR = SITE_DIR / '.cache'
DOC_CACHE_DIR = CACHE_DIR / 'docs'
OVERVIEW_CACHE = CACHE_DIR / 'overview.json'
README_PATH = SITE_DIR / 'README.md'
GITIGNORE_PATH = SITE_DIR / '.gitignore'
NOJEKYLL_PATH = SITE_DIR / '.nojekyll'
CITATION_TEXT = '医工科研-孟德尔随机化'
USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36'
CODE_KEYWORDS = ('代码', '函数', '安装', '更新', 'R包', '绘图', 'plot', 'TwoSample', 'MendelR', 'SMR')

SITE_CSS = r'''
:root {
  --bg: #f6f2e8;
  --paper: rgba(255, 252, 246, 0.94);
  --paper-strong: #fffdf8;
  --ink: #1f2937;
  --muted: #5f6b7a;
  --line: rgba(31, 41, 55, 0.12);
  --brand: #0f766e;
  --brand-soft: rgba(15, 118, 110, 0.12);
  --gold: #9a6b2f;
  --gold-soft: rgba(154, 107, 47, 0.1);
  --shadow: 0 18px 44px rgba(61, 48, 29, 0.1);
  --radius: 24px;
  --max: 1240px;
}
* { box-sizing: border-box; }
html { scroll-behavior: smooth; }
body {
  margin: 0;
  color: var(--ink);
  font-family: "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif;
  background:
    radial-gradient(circle at top left, rgba(15,118,110,.16), transparent 24%),
    radial-gradient(circle at top right, rgba(154,107,47,.16), transparent 22%),
    linear-gradient(180deg, #fbf8f2 0%, #f2ebe0 100%);
  min-height: 100vh;
}
a {
  color: var(--brand);
  text-decoration: none;
  border-bottom: 1px solid rgba(15, 118, 110, 0.24);
}
a:hover {
  color: #0b5d56;
  border-bottom-color: rgba(11, 93, 86, 0.46);
}
img {
  display: block;
  max-width: 100%;
  height: auto;
  border-radius: 16px;
}
.wrap {
  width: min(var(--max), calc(100% - 24px));
  margin: 0 auto;
  padding: 24px 0 56px;
}
.hero,
.panel,
.section-block,
.article-card,
.footer-note,
.nav-card,
.mini-card {
  background: var(--paper);
  border: 1px solid var(--line);
  box-shadow: var(--shadow);
  border-radius: 28px;
}
.hero {
  padding: 28px;
  margin-bottom: 18px;
  background: linear-gradient(135deg, rgba(255,255,255,.96), rgba(250,245,236,.92));
}
.eyebrow {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  border-radius: 999px;
  background: var(--brand-soft);
  color: var(--brand);
  font-size: 13px;
  font-weight: 700;
  letter-spacing: .04em;
}
.hero h1,
.page-title {
  margin: 14px 0 10px;
  font-size: clamp(30px, 4.8vw, 50px);
  line-height: 1.08;
  letter-spacing: -.03em;
}
.lead,
.intro,
.muted,
.footer-note p,
.footer-note small,
.section-desc,
.item-snippet,
.article-meta,
.sidebar-note,
.link-card small,
.article-body,
.article-body p,
.article-body li {
  color: var(--muted);
  line-height: 1.85;
}
.hero-links,
.badge-row,
.stats,
.quick-grid,
.doc-nav,
.meta-row {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}
.btn,
.pill,
.section-chip {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 9px 13px;
  border-radius: 999px;
  background: rgba(255,255,255,.9);
  border: 1px solid var(--line);
  color: var(--ink);
  font-size: 13px;
  font-weight: 600;
}
.btn.primary,
.pill.brand {
  color: #fff;
  background: var(--brand);
  border-color: var(--brand);
}
.pill.gold {
  color: var(--gold);
  background: var(--gold-soft);
  border-color: rgba(154,107,47,.2);
}
.stats {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  margin-top: 18px;
}
.stat {
  padding: 16px;
  border-radius: 18px;
  background: rgba(255,255,255,.78);
  border: 1px solid var(--line);
}
.stat span {
  display: block;
  font-size: 13px;
  color: var(--muted);
}
.stat strong {
  display: block;
  margin-top: 8px;
  font-size: 24px;
  color: var(--ink);
}
.layout {
  display: grid;
  grid-template-columns: 320px minmax(0, 1fr);
  gap: 18px;
  align-items: start;
}
.panel {
  position: sticky;
  top: 14px;
  padding: 20px;
}
.panel h2,
.content-head h2,
.section-head h3 {
  margin: 0 0 10px;
}
.search {
  width: 100%;
  padding: 12px 14px;
  border-radius: 14px;
  border: 1px solid var(--line);
  background: rgba(255,255,255,.9);
  outline: none;
  font-size: 14px;
}
.quick-list,
.doc-list,
.section-nav,
.inline-list {
  margin: 14px 0 0;
  padding-left: 18px;
}
.quick-list li,
.doc-list li,
.section-nav li,
.inline-list li {
  margin: 10px 0;
}
.content {
  display: grid;
  gap: 14px;
}
.content-head {
  padding: 22px;
  border-radius: 22px;
  background: rgba(255,255,255,.78);
  border: 1px solid var(--line);
}
.section-block {
  padding: 18px;
}
.section-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  margin-bottom: 10px;
}
.section-head span,
.count {
  color: var(--muted);
  font-size: 13px;
}
.item-link {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}
.item-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 6px;
}
.item-snippet {
  margin-top: 6px;
  font-size: 14px;
}
.badge {
  display: inline-flex;
  align-items: center;
  padding: 3px 8px;
  border-radius: 999px;
  background: rgba(15,118,110,.08);
  color: var(--brand);
  font-size: 12px;
  font-weight: 700;
}
.badge.external {
  color: var(--gold);
  background: rgba(154,107,47,.08);
}
.doc-page {
  display: grid;
  gap: 18px;
}
.article-card {
  padding: 24px;
}
.article-head {
  padding-bottom: 18px;
  margin-bottom: 18px;
  border-bottom: 1px solid var(--line);
}
.breadcrumbs {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  font-size: 14px;
  color: var(--muted);
}
.breadcrumbs a {
  color: var(--muted);
  border-bottom-color: rgba(95,107,122,.22);
}
.article-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  font-size: 14px;
}
.article-body {
  font-size: 16px;
}
.article-body h1,
.article-body h2,
.article-body h3,
.article-body h4 {
  color: var(--ink);
  margin: 1.6em 0 .7em;
  line-height: 1.35;
}
.article-body p,
.article-body ul,
.article-body ol,
.article-body table,
.article-body blockquote,
.article-body pre,
.article-body figure,
.article-body img,
.article-body details {
  margin: 1.05em 0;
}
.article-body ul,
.article-body ol {
  padding-left: 1.5em;
}
.article-body table {
  width: 100%;
  border-collapse: collapse;
  min-width: 620px;
}
.article-body th,
.article-body td {
  padding: 10px 12px;
  border: 1px solid rgba(31,41,55,.12);
  vertical-align: top;
}
.article-body th {
  background: rgba(15,118,110,.08);
  color: var(--ink);
}
.table-scroll {
  overflow-x: auto;
  border: 1px solid rgba(31,41,55,.1);
  border-radius: 18px;
  background: rgba(255,255,255,.86);
}
.article-body blockquote {
  padding: 14px 16px;
  border-left: 4px solid rgba(15,118,110,.32);
  border-radius: 16px;
  background: rgba(15,118,110,.06);
}
.code-block {
  overflow: hidden;
  border-radius: 18px;
  border: 1px solid rgba(31,41,55,.12);
  background: #12212a;
  color: #eff4f8;
}
.code-label {
  padding: 10px 14px;
  border-bottom: 1px solid rgba(255,255,255,.08);
  background: rgba(255,255,255,.04);
  font-size: 12px;
  font-weight: 800;
  letter-spacing: .08em;
  text-transform: uppercase;
  color: rgba(255,255,255,.72);
}
.code-block pre {
  margin: 0;
  padding: 16px;
  overflow-x: auto;
}
.code-block code {
  display: block;
  font-family: "SFMono-Regular", "Consolas", monospace;
  font-size: 14px;
  line-height: 1.75;
  white-space: pre;
}
.link-card {
  display: block;
  padding: 14px 16px;
  border-radius: 18px;
  border: 1px solid rgba(15,118,110,.18);
  background: rgba(15,118,110,.06);
  color: var(--ink);
}
.link-card strong {
  display: block;
  color: var(--ink);
  font-size: 15px;
}
.link-card span {
  display: block;
  margin-top: 5px;
  color: var(--brand);
  font-size: 12px;
  font-weight: 700;
  letter-spacing: .04em;
}
.link-card small {
  display: block;
  margin-top: 6px;
}
.image-card {
  margin: 1.05em 0;
}
.image-card a {
  display: inline-block;
  border-bottom: none;
}
.image-card img {
  box-shadow: var(--shadow);
  background: rgba(255,255,255,.88);
}
.board-tree {
  padding-left: 1.2em;
}
.board-tree > li {
  margin: .55em 0;
}
.card-raw {
  padding: 12px 14px;
  border-radius: 16px;
  background: rgba(154,107,47,.08);
  border: 1px solid rgba(154,107,47,.16);
}
.card-raw summary {
  cursor: pointer;
  color: var(--gold);
  font-weight: 700;
}
.card-raw pre {
  white-space: pre-wrap;
  word-break: break-word;
}
.doc-nav {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}
.nav-card {
  display: block;
  padding: 16px;
}
.nav-card em {
  display: block;
  margin-bottom: 6px;
  color: var(--muted);
  font-style: normal;
  font-size: 13px;
}
.mini-card {
  padding: 16px;
}
.mini-card h3 {
  margin: 0 0 10px;
  font-size: 17px;
}
.filter-item.is-hidden {
  display: none;
}
.footer-note {
  margin-top: 18px;
  padding: 20px;
  border-style: dashed;
}
.footer-note strong {
  color: var(--ink);
}
@media (max-width: 980px) {
  .stats {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
  .layout {
    grid-template-columns: 1fr;
  }
  .panel {
    position: static;
  }
  .doc-nav {
    grid-template-columns: 1fr;
  }
}
@media (max-width: 640px) {
  .wrap {
    width: min(calc(100% - 16px), 1080px);
  }
  .hero,
  .panel,
  .section-block,
  .article-card,
  .footer-note,
  .nav-card,
  .mini-card {
    padding: 18px;
    border-radius: 22px;
  }
  .stats {
    grid-template-columns: 1fr;
  }
}
'''

SITE_JS = r'''
document.querySelectorAll('[data-search-input]').forEach((input) => {
  const selector = input.dataset.searchTarget;
  if (!selector) return;
  const items = Array.from(document.querySelectorAll(selector));
  input.addEventListener('input', () => {
    const query = input.value.trim().toLowerCase();
    items.forEach((item) => {
      const haystack = (item.dataset.searchText || item.textContent || '').toLowerCase();
      const matched = !query || haystack.includes(query);
      item.classList.toggle('is-hidden', !matched);
    });
  });
});
'''

TAG_ALLOWED = {
    'a': {'href', 'target', 'rel', 'class'},
    'article': {'class'},
    'blockquote': {'class'},
    'code': {'class', 'data-lang'},
    'details': {'class'},
    'div': {'class'},
    'figcaption': {'class'},
    'figure': {'class'},
    'h1': {'class'},
    'h2': {'class'},
    'h3': {'class'},
    'h4': {'class'},
    'h5': {'class'},
    'h6': {'class'},
    'iframe': {'src', 'allowfullscreen', 'loading', 'class'},
    'img': {'src', 'alt', 'title', 'width', 'height', 'loading', 'class'},
    'li': {'class'},
    'ol': {'class'},
    'p': {'class'},
    'pre': {'class'},
    'section': {'class'},
    'small': {'class'},
    'source': {'src', 'type'},
    'span': {'class'},
    'strong': {'class'},
    'summary': {'class'},
    'table': {'class'},
    'tbody': {'class'},
    'td': {'colspan', 'rowspan', 'align', 'class'},
    'tfoot': {'class'},
    'th': {'colspan', 'rowspan', 'align', 'class'},
    'thead': {'class'},
    'tr': {'class'},
    'ul': {'class'},
    'video': {'src', 'controls', 'class', 'poster'},
}


def ensure_dirs() -> None:
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    MEDIA_DIR.mkdir(parents=True, exist_ok=True)
    DOC_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    NOJEKYLL_PATH.write_text('', encoding='utf-8')
    GITIGNORE_PATH.write_text('.cache/\n__pycache__/\n', encoding='utf-8')


def fetch_text(url: str, *, binary: bool = False, extra_headers: dict | None = None):
    headers = {'User-Agent': USER_AGENT}
    if extra_headers:
        headers.update(extra_headers)
    error = None
    for _ in range(3):
        try:
            req = Request(url, headers=headers)
            with urlopen(req, timeout=45) as resp:
                data = resp.read()
            return data if binary else data.decode('utf-8', 'ignore')
        except Exception as exc:  # pragma: no cover - network variability
            error = exc
    raise error


def fetch_app_data() -> dict:
    if OVERVIEW_CACHE.exists():
        return json.loads(OVERVIEW_CACHE.read_text(encoding='utf-8'))
    src = fetch_text(SOURCE_URL)
    match = re.search(r'window\.appData = JSON\.parse\(decodeURIComponent\("([\s\S]*?)"\)\)', src)
    if not match:
        raise RuntimeError('无法从语雀首页提取 appData')
    data = json.loads(unquote(match.group(1)))
    OVERVIEW_CACHE.write_text(json.dumps(data, ensure_ascii=False), encoding='utf-8')
    return data


def fetch_doc_payload(slug: str, book_id: int) -> dict:
    cache_path = DOC_CACHE_DIR / f'{slug}.json'
    if cache_path.exists():
        return json.loads(cache_path.read_text(encoding='utf-8'))
    api_url = f'{BASE_HOST}/api/docs/{slug}?book_id={book_id}'
    payload = json.loads(fetch_text(api_url, extra_headers={'x-requested-with': 'XMLHttpRequest'}))['data']
    cache_path.write_text(json.dumps(payload, ensure_ascii=False), encoding='utf-8')
    return payload


def normalize_source_url(item_url: str) -> str:
    if not item_url:
        return SOURCE_URL
    if item_url.startswith('http://') or item_url.startswith('https://'):
        return item_url
    if item_url.startswith('//'):
        return 'https:' + item_url
    if item_url.startswith('/'):
        return urljoin(BASE_HOST, item_url)
    return urljoin(SOURCE_URL.rstrip('/') + '/', item_url)


def absolute_url(url: str) -> str:
    if not url:
        return ''
    if url.startswith(('data:', 'mailto:', 'tel:', '#')):
        return url
    if url.startswith('//'):
        return 'https:' + url
    if re.match(r'^[a-zA-Z][a-zA-Z0-9+.-]*:', url):
        return url
    if url.startswith('/'):
        return urljoin(BASE_HOST, url)
    return urljoin(SOURCE_URL.rstrip('/') + '/', url)


def slug_from_url(url: str | None) -> str | None:
    if not url:
        return None
    parsed = urlparse(absolute_url(url))
    candidate = parsed.path.rstrip('/').split('/')[-1]
    if candidate.endswith('.html'):
        candidate = candidate[:-5]
    return candidate or None


def collapse_ws(text: str) -> str:
    return re.sub(r'\s+', ' ', text or '').strip()


def short_text(text: str, limit: int = 120) -> str:
    text = collapse_ws(text)
    return text if len(text) <= limit else text[: limit - 1].rstrip() + '…'


def relative_href(target: Path, current_page: Path) -> str:
    start = current_page.parent.as_posix() or '.'
    return posixpath.relpath(target.as_posix(), start=start)


def asset_href(name: str, current_page: Path) -> str:
    return relative_href(Path('assets') / name, current_page)


def is_local_href(url: str) -> bool:
    if not url:
        return False
    return bool(re.match(r'^(?:\./|\.\./|docs/|assets/|[^/#?]+\.html(?:[#?].*)?)', url))


def is_image_href(url: str) -> bool:
    if not url:
        return False
    parsed = urlparse(absolute_url(url))
    return parsed.path.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp', '.svg', '.bmp'))


def rewrite_href(url: str, current_page: Path, doc_paths: dict[str, Path]) -> str:
    if not url:
        return ''
    if url.startswith(('#', 'mailto:', 'tel:')) or is_local_href(url):
        return url
    normalized = absolute_url(url)
    slug = slug_from_url(normalized)
    if slug and slug in doc_paths:
        return relative_href(doc_paths[slug], current_page)
    return normalized


def localize_image(url: str, current_page: Path, image_cache: dict[str, Path]) -> str:
    if is_local_href(url):
        return url
    normalized = absolute_url(url)
    if not normalized or normalized.startswith('data:'):
        return normalized
    if normalized in image_cache:
        return relative_href(image_cache[normalized], current_page)
    parsed = urlparse(normalized)
    ext = Path(parsed.path).suffix.lower()
    if not ext or len(ext) > 6:
        ext = '.bin'
    rel_path = Path('assets') / 'media' / f"{sha1(normalized.encode('utf-8')).hexdigest()[:20]}{ext}"
    target = SITE_DIR / rel_path
    if target.exists():
        image_cache[normalized] = rel_path
        return relative_href(rel_path, current_page)
    return normalized


def build_sections(toc: list[dict]) -> list[dict]:
    sections: list[dict] = []
    current = {'title': '未分组', 'items': []}
    for item in toc:
        item_type = item.get('type')
        title = collapse_ws(item.get('title', ''))
        level = item.get('level', 0)
        if not title:
            continue
        if level == 0 and item_type == 'TITLE':
            if current['items'] or current['title'] != '未分组':
                sections.append(current)
            current = {'title': title, 'items': []}
            continue
        if item_type not in {'DOC', 'LINK'}:
            continue
        source_url = normalize_source_url(item.get('url', ''))
        entry = {
            'title': title,
            'type': item_type,
            'level': level,
            'source_url': source_url,
            'slug': item.get('url', '').split('/')[-1] if item_type == 'DOC' and item.get('url') else slug_from_url(source_url),
        }
        current['items'].append(entry)
    if current['items'] or current['title'] != '未分组':
        sections.append(current)
    for section_index, section in enumerate(sections):
        section['anchor'] = f'section-{section_index + 1}'
        for item_index, item in enumerate(section['items']):
            item['section_index'] = section_index
            item['item_index'] = item_index
            item['section_title'] = section['title']
    return sections


def decode_card_value(value: str | None) -> dict:
    if not value:
        return {}
    raw = value[5:] if value.startswith('data:') else value
    try:
        return json.loads(unquote(raw))
    except Exception:
        return {}


def build_link_card(title: str, href: str, meta: str = '', desc: str = ''):
    meta_map = {'bookmarkinline': '引用链接', 'thirdparty': '外部内容', 'image': '插图'}
    meta = meta_map.get(meta, meta)
    node = html.Element('a', href=href, **{'class': 'link-card'})
    if href.startswith('http://') or href.startswith('https://'):
        node.set('target', '_blank')
        node.set('rel', 'noreferrer')
    strong = html.Element('strong')
    strong.text = title or '引用内容'
    node.append(strong)
    if meta:
        tag = html.Element('span')
        tag.text = meta
        node.append(tag)
    if desc:
        summary = html.Element('small')
        summary.text = short_text(desc, 200)
        node.append(summary)
    return node


def build_raw_card(name: str, payload: dict):
    node = html.Element('details', **{'class': 'card-raw'})
    summary = html.Element('summary')
    summary.text = f'展开查看 {name or "card"} 内容'
    node.append(summary)
    pre = html.Element('pre')
    pre.text = json.dumps(payload, ensure_ascii=False, indent=2)
    node.append(pre)
    return node


def render_card(card, current_page: Path, doc_paths: dict[str, Path]) -> tuple[html.HtmlElement | None, int]:
    name = (card.get('name') or '').strip().lower()
    payload = decode_card_value(card.get('value'))
    if name == 'codeblock' or payload.get('code'):
        language = collapse_ws(payload.get('mode') or payload.get('language') or 'code')
        wrapper = html.Element('figure', **{'class': 'code-block'})
        caption = html.Element('figcaption', **{'class': 'code-label'})
        caption.text = language
        pre = html.Element('pre')
        code = html.Element('code')
        if language:
            code.set('class', f'language-{re.sub(r"[^a-zA-Z0-9_-]+", "-", language.lower())}')
            code.set('data-lang', language)
        code.text = payload.get('code') or ''
        pre.append(code)
        wrapper.extend([caption, pre])
        return wrapper, 1

    detail = payload.get('detail') or {}
    target = payload.get('src') or payload.get('url') or detail.get('url') or ''
    title = collapse_ws(detail.get('title') or payload.get('title') or card.get('name') or '引用内容')
    desc = collapse_ws(detail.get('desc') or payload.get('desc') or '')

    if name == 'yuqueinline':
        meta = '站内引用' if slug_from_url(target) in doc_paths else '引用链接'
        return build_link_card(title, rewrite_href(target, current_page, doc_paths), meta, desc), 0

    if target:
        meta = name or '引用卡片'
        return build_link_card(title, rewrite_href(target, current_page, doc_paths), meta, desc), 0

    return build_raw_card(name, payload), 0




def build_image_figure(href: str, current_page: Path, image_cache: dict[str, Path], alt_text: str = '插图'):
    local_src = localize_image(href, current_page, image_cache)
    cleaned_alt = collapse_ws(alt_text).replace(' ', '')
    if not cleaned_alt or cleaned_alt.lower() in {'image', 'imageimage'}:
        cleaned_alt = '插图'
    figure = html.Element('figure', **{'class': 'image-card'})
    link = html.Element('a', href=local_src)
    if local_src.startswith('http://') or local_src.startswith('https://'):
        link.set('target', '_blank')
        link.set('rel', 'noreferrer')
    image = html.Element('img', src=local_src, alt=cleaned_alt, loading='lazy')
    link.append(image)
    figure.append(link)
    return figure


def render_inline_html(fragment: str, current_page: Path, doc_paths: dict[str, Path], image_cache: dict[str, Path]):
    if not fragment:
        span = html.Element('span')
        span.text = ''
        return span
    wrapper = html.fromstring(f'<span>{fragment}</span>')
    for anchor in list(wrapper.xpath('.//a[@href]')):
        href = anchor.get('href')
        if href and is_image_href(href) and not anchor.xpath('.//img'):
            figure = build_image_figure(href, current_page, image_cache, collapse_ws(anchor.text_content()) or '插图')
            parent = anchor.getparent()
            if parent is not None:
                parent.replace(anchor, figure)
                continue
        if href:
            resolved = rewrite_href(href, current_page, doc_paths)
            anchor.set('href', resolved)
            if resolved.startswith('http://') or resolved.startswith('https://'):
                anchor.set('target', '_blank')
                anchor.set('rel', 'noreferrer')
            else:
                anchor.attrib.pop('target', None)
                anchor.attrib.pop('rel', None)
    for node in wrapper.iter():
        cleanup_attributes(node)
    return wrapper


def render_board_branch(nodes: list[dict], current_page: Path, doc_paths: dict[str, Path], image_cache: dict[str, Path]):
    ul = html.Element('ul', **{'class': 'board-tree'})
    for entry in nodes or []:
        label_html = entry.get('html') or entry.get('text') or ''
        label = collapse_ws(re.sub(r'<[^>]+>', ' ', label_html))
        if not label and not entry.get('children'):
            continue
        li = html.Element('li')
        inline = render_inline_html(label_html, current_page, doc_paths, image_cache)
        li.append(inline)
        children = entry.get('children') or []
        if children:
            li.append(render_board_branch(children, current_page, doc_paths, image_cache))
        ul.append(li)
    return ul


def render_board_content(raw: str, current_page: Path, doc_paths: dict[str, Path], image_cache: dict[str, Path]):
    payload = json.loads(raw)
    wrapper = html.Element('div', **{'class': 'article-body'})
    intro = html.Element('div', **{'class': 'link-card'})
    title = html.Element('strong')
    title.text = '白板 / 思维导图文字版'
    tag = html.Element('span')
    tag.text = '已整理为站内可读结构'
    desc = html.Element('small')
    desc.text = '原页面是语雀白板内容，这里优先按层级结构整理为列表，便于直接阅读和分享。'
    intro.extend([title, tag, desc])
    wrapper.append(intro)
    body = payload.get('diagramData', {}).get('body') or []
    if body:
        wrapper.append(render_board_branch(body, current_page, doc_paths, image_cache))
    if payload.get('text'):
        details = html.Element('details', **{'class': 'card-raw'})
        summary = html.Element('summary')
        summary.text = '展开查看白板原始文本'
        pre = html.Element('pre')
        pre.text = payload.get('text')
        details.extend([summary, pre])
        wrapper.append(details)
    html_string = html.tostring(wrapper, encoding='unicode', method='html')
    return html_string, short_text(payload.get('text') or '白板内容', 180), 0


def cleanup_attributes(node) -> None:
    if not isinstance(node.tag, str):
        return
    allowed = TAG_ALLOWED.get(node.tag, {'class'})
    for attr in list(node.attrib):
        if attr == 'class':
            classes = [part for part in node.get('class', '').split() if not part.startswith('lake-')]
            if classes:
                node.set('class', ' '.join(classes))
            else:
                del node.attrib['class']
            continue
        if attr.startswith('data-lake') or attr in {'id', 'style'}:
            del node.attrib[attr]
            continue
        if attr not in allowed:
            del node.attrib[attr]


def transform_content(raw: str, current_page: Path, doc_paths: dict[str, Path], image_cache: dict[str, Path]):
    cleaned = re.sub(r'<!doctype lake>', '', raw, flags=re.I)
    cleaned = re.sub(r'<meta[^>]+/?>', '', cleaned, flags=re.I)
    stripped = cleaned.strip()
    if stripped.startswith('{') and '"format":"lakeboard"' in stripped:
        return render_board_content(stripped, current_page, doc_paths, image_cache)

    root = html.fromstring(f'<div class="article-body">{cleaned}</div>')

    code_count = 0
    for card in list(root.xpath('.//card')):
        replacement, added = render_card(card, current_page, doc_paths)
        code_count += added
        parent = card.getparent()
        if parent is None:
            continue
        if replacement is None:
            parent.remove(card)
        else:
            parent.replace(card, replacement)

    for anchor in list(root.xpath('.//a[@href]')):
        href = anchor.get('href')
        if href and is_image_href(href) and not anchor.xpath('.//img'):
            figure = build_image_figure(href, current_page, image_cache, collapse_ws(anchor.text_content()) or '插图')
            parent = anchor.getparent()
            if parent is not None:
                parent.replace(anchor, figure)

    for table in list(root.xpath('.//table')):
        parent = table.getparent()
        if parent is None:
            continue
        if parent.tag == 'div' and parent.get('class') == 'table-scroll':
            continue
        wrapper = html.Element('div', **{'class': 'table-scroll'})
        parent.replace(table, wrapper)
        wrapper.append(table)

    for node in root.iter():
        if not isinstance(node.tag, str):
            continue
        if node.tag == 'a' and node.get('href'):
            href = rewrite_href(node.get('href'), current_page, doc_paths)
            node.set('href', href)
            if href.startswith('http://') or href.startswith('https://'):
                node.set('target', '_blank')
                node.set('rel', 'noreferrer')
            else:
                node.attrib.pop('target', None)
                node.attrib.pop('rel', None)
        elif node.tag == 'img' and node.get('src'):
            node.set('src', localize_image(node.get('src'), current_page, image_cache))
            node.set('loading', 'lazy')
        elif node.tag == 'iframe' and node.get('src'):
            node.set('src', absolute_url(node.get('src')))
            node.set('loading', 'lazy')
        cleanup_attributes(node)

    html_string = html.tostring(root, encoding='unicode', method='html')
    text = short_text(root.text_content(), 180)
    return html_string, text, code_count


def page_shell(current_page: Path, title: str, description: str, hero: str, sidebar: str, content: str, footer: str) -> str:
    return f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{escape(title)}</title>
  <meta name="description" content="{escape(description)}">
  <link rel="stylesheet" href="{escape(asset_href('site.css', current_page))}">
</head>
<body>
  <div class="wrap">
    {hero}
    <div class="layout">
      {sidebar}
      {content}
    </div>
    {footer}
  </div>
  <script src="{escape(asset_href('site.js', current_page))}"></script>
</body>
</html>'''


def render_item(item: dict, current_page: Path, docs_by_slug: dict[str, dict], doc_paths: dict[str, Path]) -> str:
    if item.get('slug') in docs_by_slug:
        doc = docs_by_slug[item['slug']]
        href = relative_href(doc_paths[item['slug']], current_page)
        badges = ['<span class="badge">正文</span>' if item['type'] == 'DOC' else '<span class="badge">站内页</span>']
        if doc['code_count']:
            badges.append(f'<span class="badge">代码 {doc["code_count"]}</span>')
        meta_bits = [f'<span class="count">{doc["word_count"]} 字</span>']
        if doc['updated_at']:
            meta_bits.append(f'<span class="count">更新 {escape(doc["updated_at"][:10])}</span>')
        snippet = f'<div class="item-snippet">{escape(doc["excerpt"])}</div>' if doc['excerpt'] else ''
        return f'''<li class="filter-item" data-search-text="{escape(item['section_title'] + ' ' + item['title'] + ' ' + doc['excerpt'])}">
  <a class="item-link" href="{escape(href)}">{escape(item['title'])}</a>
  {' '.join(badges)}
  <div class="item-meta">{''.join(meta_bits)}</div>
  {snippet}
</li>'''

    href = item['source_url']
    return f'''<li class="filter-item" data-search-text="{escape(item['section_title'] + ' ' + item['title'])}">
  <a class="item-link" href="{escape(href)}" target="_blank" rel="noreferrer">{escape(item['title'])}</a>
  <span class="badge external">外链</span>
</li>'''


def pick_quick_docs(sections: list[dict], docs_by_slug: dict[str, dict]) -> list[dict]:
    picks: list[dict] = []
    for section in sections:
        for item in section['items']:
            if item['type'] != 'DOC' or item['slug'] not in docs_by_slug:
                continue
            doc = docs_by_slug[item['slug']]
            if doc['code_count'] or any(keyword.lower() in item['title'].lower() for keyword in CODE_KEYWORDS):
                picks.append(doc)
    seen = set()
    unique = []
    for doc in picks:
        if doc['slug'] in seen:
            continue
        seen.add(doc['slug'])
        unique.append(doc)
    return unique[:24]


def render_index(book: dict, sections: list[dict], docs: list[dict], docs_by_slug: dict[str, dict], doc_paths: dict[str, Path]) -> None:
    quick_docs = pick_quick_docs(sections, docs_by_slug)
    section_items = []
    for section in sections:
        items_html = '\n'.join(render_item(item, Path('index.html'), docs_by_slug, doc_paths) for item in section['items'])
        section_items.append(f'''<section class="section-block" id="{section['anchor']}">
  <div class="section-head">
    <h3>{escape(section['title'])}</h3>
    <span>{len(section['items'])} 条</span>
  </div>
  <ul class="doc-list">{items_html}</ul>
</section>''')

    quick_html = '\n'.join(
        f'''<li><a href="{escape(relative_href(doc_paths[doc['slug']], Path('index.html')))}">{escape(doc['title'])}</a><span class="badge">{escape(doc['section_title'])}</span></li>'''
        for doc in quick_docs
    )
    section_nav = '\n'.join(
        f'''<li><a href="#{section['anchor']}">{escape(section['title'])}</a><span class="count">{len(section['items'])} 条</span></li>'''
        for section in sections
    )

    hero = f'''<header class="hero">
  <div class="eyebrow">授权整理完整版</div>
  <h1>{escape(book['name'])}</h1>
  <p class="lead">这次不再只是目录导航，而是把语雀公开手册的正文页完整抓取成站内多页面版本。手册内链已经改成站内跳转，代码块也按更适合阅读的形式做了整理。</p>
  <div class="badge-row">
    <span class="pill brand">正文镜像 {len(docs)} 篇</span>
    <span class="pill gold">代码页 {sum(1 for doc in docs if doc['code_count'])} 篇</span>
    <span class="pill">章节 {len(sections)} 个</span>
  </div>
  <div class="stats">
    <div class="stat"><span>手册标题</span><strong>{escape(book['name'])}</strong></div>
    <div class="stat"><span>正文页数</span><strong>{len(docs)}</strong></div>
    <div class="stat"><span>含代码页面</span><strong>{sum(1 for doc in docs if doc['code_count'])}</strong></div>
    <div class="stat"><span>更新时间</span><strong>{escape(book.get('updated_at', '')[:10])}</strong></div>
  </div>
</header>'''

    sidebar = f'''<aside class="panel">
  <h2>快速浏览</h2>
  <p class="sidebar-note">左侧优先放了代码、安装、数据处理和图表相关页面。下面的搜索可以直接按章节名或文档标题过滤整站目录。</p>
  <input class="search" type="search" placeholder="搜索章节或文档标题..." data-search-input data-search-target=".filter-item">
  <div class="mini-card" style="margin-top:14px;">
    <h3>代码与实战入口</h3>
    <ul class="quick-list">{quick_html}</ul>
  </div>
  <div class="mini-card" style="margin-top:14px;">
    <h3>章节一览</h3>
    <ul class="section-nav">{section_nav}</ul>
  </div>
</aside>'''

    content = f'''<main class="content">
  <section class="content-head">
    <h2>整站目录</h2>
    <p class="intro">正文页都已经整理到站内。目录中的外链资源仍然保留，方便继续查看作者原本放在手册里的补充材料。</p>
  </section>
  {''.join(section_items)}
</main>'''

    footer = f'''<section class="footer-note">
  <p><strong>引用：</strong>{escape(CITATION_TEXT)}</p>
  <small>说明：该站点依据你提供的授权，将语雀公开手册整理为站内多页面阅读版。正文内容、代码示例和手册内链都已转为本地页面形式，便于直接分享。</small>
</section>'''

    OUT_INDEX.write_text(page_shell(Path('index.html'), f"{book['name']} · 分享整理站", short_text(book.get('description', '') or '孟德尔随机化修炼手册完整版分享站'), hero, sidebar, content, footer), encoding='utf-8')


def render_doc_sidebar(current_doc: dict, current_page: Path, current_section: dict, sections: list[dict], docs_by_slug: dict[str, dict], doc_paths: dict[str, Path]) -> str:
    current_section_items = []
    for item in current_section['items']:
        classes = ['filter-item']
        if item['type'] == 'DOC' and item.get('slug') == current_doc['slug']:
            classes.append('current')
        is_internal = item.get('slug') in doc_paths
        href = relative_href(doc_paths[item['slug']], current_page) if is_internal else item['source_url']
        attrs = '' if is_internal else ' target="_blank" rel="noreferrer"'
        badge = '<span class="badge">当前</span>' if is_internal and item.get('slug') == current_doc['slug'] else ''
        kind = '' if is_internal else '<span class="badge external">外链</span>'
        current_section_items.append(
            f'''<li class="{' '.join(classes)}" data-search-text="{escape(item['title'])}">
  <a href="{escape(href)}"{attrs}>{escape(item['title'])}</a>{badge}{kind}
</li>'''
        )

    section_nav = '\n'.join(
        f'''<li><a href="{escape(relative_href(Path('index.html'), current_page))}#{section['anchor']}">{escape(section['title'])}</a><span class="count">{len(section['items'])} 条</span></li>'''
        for section in sections
    )

    return f'''<aside class="panel">
  <h2>本节目录</h2>
  <p class="sidebar-note">当前页面所在章节会完整展开，方便继续顺着手册读下去。下面的搜索只过滤这一节的条目。</p>
  <input class="search" type="search" placeholder="筛选本节条目..." data-search-input data-search-target=".filter-item">
  <div class="mini-card" style="margin-top:14px;">
    <h3>{escape(current_section['title'])}</h3>
    <ul class="section-nav">{''.join(current_section_items)}</ul>
  </div>
  <div class="mini-card" style="margin-top:14px;">
    <h3>章节一览</h3>
    <ul class="section-nav">{section_nav}</ul>
  </div>
</aside>'''


def render_doc_page(book: dict, doc: dict, sections: list[dict], docs: list[dict], docs_by_slug: dict[str, dict], doc_paths: dict[str, Path]) -> None:
    current_page = doc_paths[doc['slug']]
    current_index = doc['order_index']
    prev_doc = docs[current_index - 1] if current_index > 0 else None
    next_doc = docs[current_index + 1] if current_index + 1 < len(docs) else None
    current_section = sections[doc['section_index']]

    hero = f'''<header class="hero">
  <div class="eyebrow">正文页</div>
  <div class="breadcrumbs">
    <a href="{escape(relative_href(Path('index.html'), current_page))}">手册首页</a>
    <span>/</span>
    <span>{escape(doc['section_title'])}</span>
  </div>
  <h1 class="page-title">{escape(doc['title'])}</h1>
  <div class="article-meta">
    <span>所属章节：{escape(doc['section_title'])}</span>
    <span>字数：{doc['word_count']}</span>
    <span>代码块：{doc['code_count']}</span>
    <span>更新时间：{escape(doc['updated_at'][:10]) if doc['updated_at'] else '未知'}</span>
  </div>
</header>'''

    sidebar = render_doc_sidebar(doc, current_page, current_section, sections, docs_by_slug, doc_paths)

    nav_cards = []
    if prev_doc:
        nav_cards.append(
            f'''<a class="nav-card" href="{escape(relative_href(doc_paths[prev_doc['slug']], current_page))}"><em>上一篇</em><strong>{escape(prev_doc['title'])}</strong></a>'''
        )
    if next_doc:
        nav_cards.append(
            f'''<a class="nav-card" href="{escape(relative_href(doc_paths[next_doc['slug']], current_page))}"><em>下一篇</em><strong>{escape(next_doc['title'])}</strong></a>'''
        )

    content = f'''<main class="doc-page">
  <article class="article-card">
    <div class="article-head">
      <div class="badge-row">
        <span class="pill">章节：{escape(doc['section_title'])}</span>
        <span class="pill gold">代码块 {doc['code_count']}</span>
      </div>
      <p class="intro">正文已经整理为站内页面，语雀内部引用也会直接跳转到本站对应页面。代码卡片已转换为便于阅读的代码块展示。</p>
    </div>
    {doc['content_html']}
  </article>
  <div class="doc-nav">{''.join(nav_cards)}</div>
</main>'''

    footer = f'''<section class="footer-note">
  <p><strong>引用：</strong>{escape(CITATION_TEXT)}</p>
  <small>该页面依据授权整理为站内阅读版，保留原手册内容结构、链接关系与代码示例，便于持续分享和检索。</small>
</section>'''

    page = page_shell(current_page, f"{doc['title']} · {book['name']}", short_text(doc['excerpt'], 150), hero, sidebar, content, footer)
    (SITE_DIR / current_page).write_text(page, encoding='utf-8')


def write_assets() -> None:
    (ASSETS_DIR / 'site.css').write_text(SITE_CSS.strip() + '\n', encoding='utf-8')
    (ASSETS_DIR / 'site.js').write_text(SITE_JS.strip() + '\n', encoding='utf-8')


def write_readme(book: dict, docs: list[dict]) -> None:
    README_PATH.write_text(
        '\n'.join([
            f'# {book["name"]} 分享站',
            '',
            f'- 页面入口：{OUT_INDEX.name}',
            f'- 正文页数：{len(docs)}',
            f'- 引用：{CITATION_TEXT}',
            '- 生成方式：运行 `python3 build_site.py` 会重新抓取语雀公开正文并生成多页面静态站点。',
        ]) + '\n',
        encoding='utf-8',
    )


def fetch_all_docs(doc_items: list[dict], book_id: int) -> tuple[dict[str, dict], dict[str, str]]:
    results: dict[str, dict] = {}
    errors: dict[str, str] = {}
    with ThreadPoolExecutor(max_workers=8) as pool:
        future_map = {pool.submit(fetch_doc_payload, item['slug'], book_id): item for item in doc_items}
        total = len(future_map)
        for index, future in enumerate(as_completed(future_map), start=1):
            item = future_map[future]
            try:
                results[item['slug']] = future.result()
            except Exception as exc:  # pragma: no cover - network variability
                errors[item['slug']] = str(exc)
            if index % 25 == 0 or index == total:
                print(f'fetched docs: {index}/{total}')
    return results, errors


def main() -> None:
    ensure_dirs()
    app_data = fetch_app_data()
    book = app_data['book']
    sections = build_sections(book['toc'])

    doc_items = [item for section in sections for item in section['items'] if item['type'] == 'DOC' and item.get('slug')]
    doc_paths = {item['slug']: Path('docs') / f"{item['slug']}.html" for item in doc_items}

    payloads, errors = fetch_all_docs(doc_items, book['id'])
    image_cache: dict[str, Path] = {}
    docs: list[dict] = []

    for order_index, item in enumerate(doc_items):
        payload = payloads.get(item['slug'])
        if not payload:
            continue
        content_html, excerpt, code_count = transform_content(payload.get('content') or '', doc_paths[item['slug']], doc_paths, image_cache)
        docs.append({
            'slug': item['slug'],
            'title': collapse_ws(payload.get('title') or item['title']),
            'section_title': item['section_title'],
            'section_index': item['section_index'],
            'order_index': order_index,
            'word_count': payload.get('word_count') or 0,
            'updated_at': payload.get('content_updated_at') or payload.get('updated_at') or '',
            'description': collapse_ws(payload.get('description') or ''),
            'excerpt': excerpt,
            'content_html': content_html,
            'code_count': code_count,
            'source_url': item['source_url'],
        })

    docs_by_slug = {doc['slug']: doc for doc in docs}
    write_assets()
    render_index(book, sections, docs, docs_by_slug, doc_paths)
    for doc in docs:
        render_doc_page(book, doc, sections, docs, docs_by_slug, doc_paths)
    write_readme(book, docs)

    print(f'generated docs: {len(docs)}')
    print(f'sections: {len(sections)}')
    print(f'code pages: {sum(1 for doc in docs if doc["code_count"])}')
    print(f'errors: {len(errors)}')
    if errors:
        for slug, message in list(errors.items())[:12]:
            print(f'failed {slug}: {message}')


if __name__ == '__main__':
    main()
