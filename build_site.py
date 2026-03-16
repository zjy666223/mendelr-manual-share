from urllib.request import Request, urlopen
from urllib.parse import unquote
import json
import re
from html import escape
from collections import defaultdict
from pathlib import Path

SOURCE_URL = 'https://flash0926.yuque.com/org-wiki-flash0926-kivyu0/gpa1ys'
BASE_DOC_URL = 'https://flash0926.yuque.com/org-wiki-flash0926-kivyu0/gpa1ys/'
OUT = Path('/Users/chenmo/D/codex_agent_workspace/孟德尔随机化修炼手册站/index.html')


def fetch_app_data(url: str):
    req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    src = urlopen(req, timeout=20).read().decode('utf-8', 'ignore')
    m = re.search(r'window\.appData = JSON\.parse\(decodeURIComponent\("([\s\S]*?)"\)\)', src)
    if not m:
        raise RuntimeError('无法从页面中提取 appData')
    return json.loads(unquote(m.group(1)))


def normalize_url(item_url: str) -> str:
    if not item_url:
        return '#'
    if item_url.startswith('http://') or item_url.startswith('https://'):
        return item_url
    if item_url.startswith('/'):
        return 'https://flash0926.yuque.com' + item_url
    return BASE_DOC_URL + item_url


def build_sections(toc):
    sections = []
    current = {'title': '未分组', 'items': []}
    for item in toc:
        level = item.get('level', 0)
        item_type = item.get('type')
        title = item.get('title', '').strip()
        if not title:
            continue
        if level == 0 and item_type == 'TITLE':
            if current['items'] or current['title'] != '未分组':
                sections.append(current)
            current = {'title': title, 'items': []}
            continue
        if item_type in {'DOC', 'LINK'}:
            current['items'].append({
                'title': title,
                'url': normalize_url(item.get('url', '')),
                'level': level,
                'type': item_type,
            })
    if current['items'] or current['title'] != '未分组':
        sections.append(current)
    return sections


def pick_code_items(sections):
    section_priorities = {'安装与更新', '数据准备与处理', '代码分析', '图表呈现'}
    keywords = ['代码', '函数', '安装', '更新', '绘图', 'R包', 'MendelR', 'SMR', 'TwoSample', 'forest', 'plot']
    picks = []
    for section in sections:
        for item in section['items']:
            if section['title'] in section_priorities or any(k.lower() in item['title'].lower() for k in keywords):
                picks.append((section['title'], item))
    # 去重并保持顺序
    seen = set()
    unique = []
    for sec, item in picks:
        key = item['url']
        if key in seen:
            continue
        seen.add(key)
        unique.append((sec, item))
    return unique[:36]


def render_item(item, section_title):
    indent = '&nbsp;' * max(item['level'] - 1, 0) * 2
    item_type = '正文' if item['type'] == 'DOC' else '外链'
    return f'''<li class="doc-item" data-title="{escape(item['title'])}" data-section="{escape(section_title)}">
      <a href="{escape(item['url'])}" target="_blank" rel="noreferrer">{indent}{escape(item['title'])}</a>
      <span class="meta-tag">{item_type}</span>
    </li>'''


def main():
    data = fetch_app_data(SOURCE_URL)
    book = data['book']
    sections = build_sections(book['toc'])
    quick_items = pick_code_items(sections)
    total_items = sum(len(s['items']) for s in sections)
    section_cards = []
    for section in sections:
        items_html = '\n'.join(render_item(item, section['title']) for item in section['items'])
        section_cards.append(f'''<section class="section-block" data-section="{escape(section['title'])}">
  <div class="section-head">
    <h3>{escape(section['title'])}</h3>
    <span>{len(section['items'])} 条</span>
  </div>
  <ul class="doc-list">{items_html}</ul>
</section>''')

    quick_html = '\n'.join(
        f'''<li><a href="{escape(item['url'])}" target="_blank" rel="noreferrer">{escape(item['title'])}</a><span>{escape(section)}</span></li>'''
        for section, item in quick_items
    )

    html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{escape(book['name'])} · 分享整理站</title>
  <style>
    :root {{
      --bg: #f5f1e9;
      --paper: rgba(255, 252, 247, 0.92);
      --ink: #1f2937;
      --muted: #5f6b7a;
      --line: rgba(31, 41, 55, 0.12);
      --brand: #0f766e;
      --brand-soft: rgba(15, 118, 110, 0.1);
      --gold: #9a6b2f;
      --gold-soft: rgba(154, 107, 47, 0.1);
      --shadow: 0 18px 46px rgba(72, 54, 28, 0.1);
      --radius: 22px;
      --max: 1180px;
    }}
    * {{ box-sizing: border-box; }}
    html {{ scroll-behavior: smooth; }}
    body {{
      margin: 0;
      color: var(--ink);
      font-family: "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif;
      background:
        radial-gradient(circle at top left, rgba(15,118,110,.16), transparent 26%),
        radial-gradient(circle at top right, rgba(154,107,47,.14), transparent 24%),
        linear-gradient(180deg, #fbf8f1 0%, #f4eee4 100%);
      min-height: 100vh;
    }}
    a {{ color: var(--brand); text-decoration: none; border-bottom: 1px solid rgba(15,118,110,.26); }}
    a:hover {{ color: #0b5d56; border-bottom-color: rgba(11,93,86,.45); }}
    .wrap {{ width: min(var(--max), calc(100% - 26px)); margin: 0 auto; padding: 28px 0 58px; }}
    .hero, .panel, .section-block, .footer-note {{
      background: var(--paper);
      border: 1px solid var(--line);
      box-shadow: var(--shadow);
      border-radius: 28px;
    }}
    .hero {{ padding: 30px; margin-bottom: 18px; background: linear-gradient(135deg, rgba(255,255,255,.96), rgba(250,245,235,.9)); }}
    .eyebrow {{ display: inline-block; padding: 8px 12px; border-radius: 999px; background: var(--brand-soft); color: var(--brand); font-size: 13px; font-weight: 700; letter-spacing: .04em; }}
    h1 {{ margin: 16px 0 10px; font-size: clamp(30px, 4.8vw, 50px); line-height: 1.06; letter-spacing: -.03em; }}
    .lead, .intro, .footer-note p, .footer-note small, .doc-item, .quick-list li {{ color: var(--muted); line-height: 1.8; }}
    .hero-links {{ display: flex; flex-wrap: wrap; gap: 10px; margin-top: 16px; }}
    .btn {{ display: inline-flex; align-items: center; gap: 8px; padding: 10px 14px; border-radius: 999px; background: rgba(255,255,255,.92); border: 1px solid var(--line); font-size: 14px; color: var(--ink); border-bottom: 1px solid var(--line); }}
    .btn.primary {{ color: #fff; background: var(--brand); border-color: var(--brand); }}
    .stats {{ display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 12px; margin-top: 18px; }}
    .stat {{ padding: 16px; border-radius: 18px; background: rgba(255,255,255,.78); border: 1px solid var(--line); }}
    .stat span {{ display: block; font-size: 13px; color: var(--muted); }}
    .stat strong {{ display: block; margin-top: 8px; font-size: 24px; }}
    .layout {{ display: grid; grid-template-columns: 320px minmax(0,1fr); gap: 18px; margin-top: 18px; }}
    .panel {{ padding: 20px; position: sticky; top: 14px; height: fit-content; }}
    .panel h2 {{ margin: 0 0 12px; font-size: 22px; }}
    .search {{ width: 100%; padding: 12px 14px; border-radius: 14px; border: 1px solid var(--line); outline: none; font-size: 14px; background: rgba(255,255,255,.88); }}
    .chip-row {{ display: flex; flex-wrap: wrap; gap: 8px; margin-top: 12px; }}
    .chip {{ padding: 8px 10px; border-radius: 999px; background: var(--gold-soft); color: var(--gold); font-size: 12px; font-weight: 700; }}
    .quick-list {{ margin: 14px 0 0; padding-left: 18px; }}
    .quick-list li {{ margin: 10px 0; }}
    .quick-list span {{ display: inline-block; margin-left: 8px; padding: 3px 8px; border-radius: 999px; background: rgba(15,118,110,.08); color: var(--brand); font-size: 12px; }}
    .content {{ display: grid; gap: 14px; }}
    .content-head {{ padding: 22px; border-radius: 22px; background: rgba(255,255,255,.76); border: 1px solid var(--line); }}
    .content-head h2 {{ margin: 0 0 8px; font-size: 28px; }}
    .section-block {{ padding: 18px; }}
    .section-head {{ display: flex; justify-content: space-between; align-items: center; gap: 12px; margin-bottom: 12px; }}
    .section-head h3 {{ margin: 0; font-size: 22px; }}
    .section-head span {{ color: var(--muted); font-size: 13px; }}
    .doc-list {{ margin: 0; padding-left: 18px; }}
    .doc-item {{ margin: 10px 0; }}
    .meta-tag {{ display: inline-block; margin-left: 8px; padding: 3px 8px; border-radius: 999px; background: rgba(154,107,47,.08); color: var(--gold); font-size: 12px; }}
    .footer-note {{ margin-top: 18px; padding: 20px; border-style: dashed; }}
    @media (max-width: 980px) {{
      .stats {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
      .layout {{ grid-template-columns: 1fr; }}
      .panel {{ position: static; }}
    }}
    @media (max-width: 640px) {{
      .wrap {{ width: min(calc(100% - 16px), 1000px); }}
      .hero, .panel, .section-block, .footer-note {{ padding: 18px; border-radius: 22px; }}
      .stats {{ grid-template-columns: 1fr; }}
    }}
  </style>
</head>
<body>
  <div class="wrap">
    <header class="hero">
      <div class="eyebrow">语雀目录整理版</div>
      <h1>{escape(book['name'])}</h1>
      <p class="lead">这个页面不是把语雀内容整页照搬，而是把这本公开手册的目录、章节层级和代码相关入口重新整理成一个更好浏览的导航式站点。你可以把它当作知识库首页来分享，点进去继续看原始文档。</p>
      <div class="hero-links">
        <a class="btn primary" href="{escape(SOURCE_URL)}" target="_blank" rel="noreferrer">打开原始语雀页</a>
        <a class="btn" href="{escape(book.get('cover', ''))}" target="_blank" rel="noreferrer">封面图</a>
        <a class="btn" href="https://flash0926.yuque.com/org-wiki-flash0926-kivyu0" target="_blank" rel="noreferrer">知识库空间</a>
      </div>
      <div class="stats">
        <div class="stat"><span>手册标题</span><strong>{escape(book['name'])}</strong></div>
        <div class="stat"><span>目录总条目</span><strong>{total_items}</strong></div>
        <div class="stat"><span>顶层分区</span><strong>{len(sections)}</strong></div>
        <div class="stat"><span>最近更新时间</span><strong>{escape(book.get('updated_at','')[:10])}</strong></div>
      </div>
    </header>

    <div class="layout">
      <aside class="panel">
        <h2>代码与实战快捷入口</h2>
        <p class="intro">原链接本身是一本公开手册的目录首页，不直接展开正文代码。我把“安装、更新、数据处理、代码分析、图表呈现”等条目单独抽出来，方便先跳到更像代码 / 函数 / 实操的部分。</p>
        <input class="search" id="searchInput" type="search" placeholder="搜索章节或文档标题...">
        <div class="chip-row">
          <span class="chip">安装与更新</span>
          <span class="chip">代码分析</span>
          <span class="chip">图表呈现</span>
          <span class="chip">数据处理</span>
        </div>
        <ul class="quick-list">{quick_html}</ul>
      </aside>

      <main class="content">
        <section class="content-head">
          <h2>目录总览</h2>
          <p class="intro">我保留了原始目录层级与所有主要文档链接。你可以直接在这里筛选标题、跳转到原始语雀文档，或者先从左侧的代码快捷入口开始。</p>
        </section>
        {''.join(section_cards)}
      </main>
    </div>

    <section class="footer-note">
      <p><strong>来源说明：</strong>本页根据语雀公开页 <a href="{escape(SOURCE_URL)}" target="_blank" rel="noreferrer">{escape(SOURCE_URL)}</a> 的目录结构和公开链接整理而成。因为原链接是整本手册首页，而不是单篇正文页，所以这次更适合做成“知识库导航站”。</p>
      <small>补充说明：你提到“代码也需要整理”，我已把代码 / 函数 / 安装 / 绘图相关条目单独抽出做快捷区，方便优先浏览。如果你之后想把整本手册里的每篇正文和代码块再进一步整理成多页面站点，我可以继续做第二轮全量抓取与重构。</small>
    </section>
  </div>

  <script>
    const input = document.getElementById('searchInput');
    const items = Array.from(document.querySelectorAll('.doc-item'));
    input.addEventListener('input', () => {{
      const q = input.value.trim().toLowerCase();
      items.forEach((item) => {{
        const hay = (item.dataset.title + ' ' + item.dataset.section).toLowerCase();
        item.style.display = hay.includes(q) ? '' : 'none';
      }});
    }});
  </script>
</body>
</html>'''
    OUT.write_text(html, encoding='utf-8')
    print(f'generated: {OUT}')
    print(f'sections: {len(sections)}')
    print(f'items: {total_items}')
    print(f'quick_items: {len(quick_items)}')


if __name__ == '__main__':
    main()
