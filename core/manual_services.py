from dataclasses import dataclass
from html import escape
import re

from django.conf import settings
from django.core.exceptions import SuspiciousFileOperation
from django.utils.safestring import mark_safe


ALLOWED_SUFFIXES = {'.md', '.txt', '.yml', '.yaml'}
STAGE_PATTERN = re.compile(r'^(\d{2})[_-](.+)$')


@dataclass(frozen=True)
class ManualDocument:
    relative_path: str
    title: str
    stage: str
    stage_label: str
    raw_content: str
    html_content: str


@dataclass(frozen=True)
class ManualSearchResult:
    relative_path: str
    title: str
    stage_label: str
    excerpt: str


def docs_root():
    return settings.BASE_DIR / 'docs'


def normalize_doc_path(raw_path):
    if not raw_path:
        raise SuspiciousFileOperation('Document path is empty.')
    path = raw_path.replace('\\', '/').strip('/')
    if path.startswith('.') or '/..' in path or path.startswith('../'):
        raise SuspiciousFileOperation('Unsafe document path.')
    root = docs_root().resolve()
    candidate = (docs_root() / path).resolve()
    if root not in candidate.parents and candidate != root:
        raise SuspiciousFileOperation('Document path escapes docs directory.')
    if candidate.suffix.lower() not in ALLOWED_SUFFIXES:
        raise SuspiciousFileOperation('Unsupported document type.')
    if not candidate.exists() or not candidate.is_file():
        raise SuspiciousFileOperation('Document not found.')
    return candidate.relative_to(root).as_posix()


def iter_doc_paths():
    root = docs_root()
    if not root.exists():
        return []
    paths = [
        path.relative_to(root).as_posix()
        for path in root.rglob('*')
        if path.is_file() and path.suffix.lower() in ALLOWED_SUFFIXES
    ]
    return sorted(paths, key=lambda value: value.lower())


def stage_for_path(relative_path):
    name = relative_path.rsplit('/', 1)[-1]
    match = STAGE_PATTERN.match(name)
    if match:
        return match.group(1)
    if '/' in relative_path:
        return relative_path.split('/', 1)[0]
    return 'docs'


def title_for_path(relative_path):
    name = relative_path.rsplit('/', 1)[-1]
    stem = name.rsplit('.', 1)[0]
    match = STAGE_PATTERN.match(stem)
    if match:
        stem = match.group(2)
    return stem.replace('_', ' ').replace('-', ' ').strip() or relative_path


def stage_label(stage):
    if stage == 'docs':
        return 'Docs'
    if stage.isdigit():
        return f'Step {stage}'
    return stage.replace('_', ' ').replace('-', ' ').title()


def build_stage_options():
    seen = set()
    stages = []
    for relative_path in iter_doc_paths():
        stage = stage_for_path(relative_path)
        if stage in seen:
            continue
        seen.add(stage)
        stages.append({'value': stage, 'label': stage_label(stage)})
    return stages


def build_stage_file_map():
    file_map = {}
    for relative_path in iter_doc_paths():
        stage = stage_for_path(relative_path)
        file_map.setdefault(stage, []).append({
            'value': relative_path,
            'label': title_for_path(relative_path),
        })
    return file_map


def first_doc_path(stage=None):
    for relative_path in iter_doc_paths():
        if not stage or stage_for_path(relative_path) == stage:
            return relative_path
    return None


def render_markdown_like(content):
    html = []
    in_code = False
    list_open = False
    for line in content.splitlines():
        stripped = line.strip()
        if stripped.startswith('```'):
            if list_open:
                html.append('</ul>')
                list_open = False
            if in_code:
                html.append('</code></pre>')
            else:
                html.append('<pre class="manual-pre"><code>')
            in_code = not in_code
            continue
        if in_code:
            html.append(escape(line) + '\n')
            continue
        if not stripped:
            if list_open:
                html.append('</ul>')
                list_open = False
            continue
        if stripped.startswith('### '):
            if list_open:
                html.append('</ul>')
                list_open = False
            html.append(f'<h3>{escape(stripped[4:])}</h3>')
        elif stripped.startswith('## '):
            if list_open:
                html.append('</ul>')
                list_open = False
            html.append(f'<h2>{escape(stripped[3:])}</h2>')
        elif stripped.startswith('# '):
            if list_open:
                html.append('</ul>')
                list_open = False
            html.append(f'<h1>{escape(stripped[2:])}</h1>')
        elif stripped.startswith(('- ', '* ')):
            if not list_open:
                html.append('<ul>')
                list_open = True
            html.append(f'<li>{escape(stripped[2:])}</li>')
        else:
            if list_open:
                html.append('</ul>')
                list_open = False
            html.append(f'<p>{escape(stripped)}</p>')
    if in_code:
        html.append('</code></pre>')
    if list_open:
        html.append('</ul>')
    return mark_safe('\n'.join(html))


def load_document(relative_path):
    normalized_path = normalize_doc_path(relative_path)
    path = docs_root() / normalized_path
    raw_content = path.read_text(encoding='utf-8')
    stage = stage_for_path(normalized_path)
    return ManualDocument(
        relative_path=normalized_path,
        title=title_for_path(normalized_path),
        stage=stage,
        stage_label=stage_label(stage),
        raw_content=raw_content,
        html_content=render_markdown_like(raw_content),
    )


def search_documents(query, stage=None, limit=20):
    normalized_query = (query or '').strip()
    if not normalized_query:
        return []
    lower_query = normalized_query.lower()
    results = []
    for relative_path in iter_doc_paths():
        if stage and stage_for_path(relative_path) != stage:
            continue
        raw_content = (docs_root() / relative_path).read_text(encoding='utf-8')
        lower_content = raw_content.lower()
        index = lower_content.find(lower_query)
        if index < 0 and lower_query not in title_for_path(relative_path).lower():
            continue
        start = max(index - 80, 0) if index >= 0 else 0
        end = min(index + len(normalized_query) + 160, len(raw_content)) if index >= 0 else 160
        excerpt = escape(raw_content[start:end].replace('\n', ' '))
        excerpt = re.sub(
            re.escape(escape(normalized_query)),
            lambda match: f'<mark>{match.group(0)}</mark>',
            excerpt,
            flags=re.IGNORECASE,
        )
        current_stage = stage_for_path(relative_path)
        results.append(ManualSearchResult(
            relative_path=relative_path,
            title=title_for_path(relative_path),
            stage_label=stage_label(current_stage),
            excerpt=mark_safe(excerpt),
        ))
        if len(results) >= limit:
            break
    return results


def manual_stats():
    paths = iter_doc_paths()
    return {
        'document_count': len(paths),
        'stage_count': len({stage_for_path(path) for path in paths}),
    }
