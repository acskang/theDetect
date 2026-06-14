import json
import logging
import re
from urllib import error, request

from django.conf import settings

from . import manual_services

logger = logging.getLogger(__name__)

USER_ERROR_MESSAGE = '지금은 AI 챗봇 응답이 지연되고 있습니다. 잠시 후 다시 시도해 주세요.'
ALLOWED_HISTORY_ROLES = {'user', 'assistant'}


class LlamaChatValidationError(Exception):
    pass


class LlamaChatServiceError(Exception):
    pass


PAGE_DOC_HINTS = {
    '/': ['landing', 'login', 'manual', 'overview'],
    '/dashboard/': ['dashboard', 'overview', 'project settings', 'implementation result'],
    '/project-settings/': ['project settings', 'system checks', 'settings overview'],
    '/datasets/build/': ['dataset build', 'dataset defaults'],
    '/datasets/build/augmented/': ['augmented dataset build', 'augmentation', 'color-safe'],
    '/datasets/versions/': ['dataset versions', 'dataset build'],
    '/training/jobs/': ['training jobs', 'training defaults', 'yolo'],
    '/models/registry/': ['model registry', 'active server model'],
    '/models/android/export/': ['android model export', 'tflite', 'deployment'],
    '/models/android/packages/': ['android model package', 'model deployment', 'set deployed'],
    '/server-detection/': ['server detection', 'server mode', 'inference'],
    '/detection-logs/': ['detection logs', 'history'],
    '/manual/': ['manual', 'docs', 'guide'],
}


def build_chat_response(message, history=None, page=None):
    clean_message = validate_message(message)
    clean_history = normalize_history(history)
    page_context = normalize_page_context(page)
    model = getattr(settings, 'CHAT_OLLAMA_MODEL', 'llama3.2-vision:11b')
    payload = {
        'model': model,
        'messages': [
            {'role': 'system', 'content': build_system_prompt(clean_message, page_context)},
            *clean_history,
            {'role': 'user', 'content': clean_message},
        ],
        'stream': False,
    }
    raw_response = call_ollama_chat(payload)
    return {
        'ok': True,
        'reply': extract_reply(raw_response),
        'model': model,
    }


def build_system_prompt(message, page_context=None):
    base_prompt = getattr(settings, 'CHAT_SYSTEM_PROMPT', '')
    page_context = page_context or {}
    manual_context = build_manual_context(message, page_context)
    page_prompt = build_page_prompt(page_context)
    parts = [base_prompt]
    if page_prompt:
        parts.append(f'[Current page context]\n{page_prompt}')
    if not manual_context:
        return '\n\n'.join(parts)
    parts.append(f'[theDetect manual context]\n{manual_context}')
    return '\n\n'.join(parts)


def build_manual_context(message, page_context=None):
    page_context = page_context or {}
    query_text = ' '.join([
        message or '',
        page_context.get('path', ''),
        page_context.get('title', ''),
        ' '.join(page_context.get('headings', [])),
        ' '.join(page_hints_for_path(page_context.get('path', ''))),
    ])
    query_terms = _terms(query_text)
    candidates = []
    for relative_path in manual_services.iter_doc_paths():
        try:
            raw_content = (manual_services.docs_root() / relative_path).read_text(encoding='utf-8')
        except OSError:
            continue
        haystack = f'{relative_path}\n{manual_services.title_for_path(relative_path)}\n{raw_content}'.lower()
        score = sum(haystack.count(term) for term in query_terms)
        if score <= 0:
            score = 1 if relative_path in {'README.md', 'implementation_result.md', 'next_steps.md'} else 0
        if score <= 0:
            continue
        candidates.append((score, relative_path, raw_content))

    max_docs = int(getattr(settings, 'CHAT_MANUAL_CONTEXT_DOCS', 5))
    max_chars = int(getattr(settings, 'CHAT_MANUAL_CONTEXT_CHARS', 9000))
    context_parts = []
    used_chars = 0
    for _, relative_path, raw_content in sorted(candidates, key=lambda item: (-item[0], item[1].lower()))[:max_docs]:
        excerpt = _best_excerpt(raw_content, query_terms, max_chars=1800)
        part = f'## {manual_services.title_for_path(relative_path)} ({relative_path})\n{excerpt}'
        if used_chars + len(part) > max_chars:
            remaining = max_chars - used_chars
            if remaining <= 200:
                break
            part = part[:remaining]
        context_parts.append(part)
        used_chars += len(part)
    return '\n\n'.join(context_parts)


def build_page_prompt(page_context):
    if not page_context:
        return ''
    headings = page_context.get('headings', [])
    lines = [
        f"현재 URL path: {page_context.get('path') or '-'}",
        f"문서 title: {page_context.get('title') or '-'}",
    ]
    if headings:
        lines.append(f"화면 headings: {', '.join(headings)}")
    visible_text = page_context.get('visible_text', '')
    if visible_text:
        lines.append(f"화면 visible text excerpt: {visible_text}")
    lines.append('사용자가 "이 페이지", "현재 화면", "여기"라고 말하면 위 현재 페이지 기준으로 답하라.')
    return '\n'.join(lines)


def validate_message(message):
    if not isinstance(message, str):
        raise LlamaChatValidationError('message is required.')
    clean_message = message.strip()
    if not clean_message:
        raise LlamaChatValidationError('message is required.')
    max_length = int(getattr(settings, 'CHAT_MESSAGE_MAX_LENGTH', 1000))
    if len(clean_message) > max_length:
        raise LlamaChatValidationError(f'message must be {max_length} characters or fewer.')
    return clean_message


def normalize_history(history):
    if history in (None, ''):
        return []
    if not isinstance(history, list):
        raise LlamaChatValidationError('history must be a list.')
    clean_history = []
    for item in history:
        if not isinstance(item, dict):
            continue
        role = item.get('role')
        content = item.get('content')
        if role not in ALLOWED_HISTORY_ROLES or not isinstance(content, str):
            continue
        clean_content = content.strip()
        if clean_content:
            clean_history.append({'role': role, 'content': clean_content})
    max_messages = int(getattr(settings, 'CHAT_HISTORY_MAX_MESSAGES', 6))
    return clean_history[-max_messages:]


def normalize_page_context(page):
    if not isinstance(page, dict):
        return {}
    return {
        'url': _clean_string(page.get('url'), 300),
        'path': _clean_path(page.get('path')),
        'title': _clean_string(page.get('title'), 160),
        'headings': _clean_string_list(page.get('headings'), max_items=8, max_length=120),
        'visible_text': _clean_string(page.get('visible_text'), 2000),
    }


def page_hints_for_path(path):
    clean_path = _clean_path(path)
    hints = []
    for prefix, values in PAGE_DOC_HINTS.items():
        if clean_path == prefix or (prefix != '/' and clean_path.startswith(prefix)):
            hints.extend(values)
    return hints


def call_ollama_chat(payload):
    base_url = getattr(settings, 'CHAT_OLLAMA_BASE_URL', 'http://127.0.0.1:11434').rstrip('/')
    timeout = int(getattr(settings, 'CHAT_OLLAMA_TIMEOUT_SECONDS', 30))
    req = request.Request(
        f'{base_url}/api/chat',
        data=json.dumps(payload).encode('utf-8'),
        headers={'Content-Type': 'application/json'},
        method='POST',
    )
    try:
        with request.urlopen(req, timeout=timeout) as response:
            return json.loads(response.read().decode('utf-8'))
    except TimeoutError as exc:
        logger.warning('Ollama MDetect chat timed out after %ss.', timeout)
        raise LlamaChatServiceError(USER_ERROR_MESSAGE) from exc
    except error.URLError as exc:
        logger.warning('Ollama MDetect chat connection failed: %s', exc.reason)
        raise LlamaChatServiceError(USER_ERROR_MESSAGE) from exc
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning('Ollama MDetect chat response failed: %s', exc)
        raise LlamaChatServiceError(USER_ERROR_MESSAGE) from exc


def extract_reply(raw_response):
    if not isinstance(raw_response, dict):
        raise LlamaChatServiceError(USER_ERROR_MESSAGE)
    message = raw_response.get('message')
    if not isinstance(message, dict):
        raise LlamaChatServiceError(USER_ERROR_MESSAGE)
    content = message.get('content')
    if not isinstance(content, str) or not content.strip():
        raise LlamaChatServiceError(USER_ERROR_MESSAGE)
    return content.strip()


def _terms(message):
    terms = [term.lower() for term in re.findall(r'[\w가-힣]{2,}', message or '')]
    synonyms = {
        '앱': ['android', 'apk', 'mobile'],
        '안드로이드': ['android', 'apk', 'mobile'],
        '모델': ['model', 'training', 'export', 'deployment'],
        '학습': ['training', 'dataset', 'yolo'],
        '로그인': ['auth', 'login', 'signup', 'session'],
        '회원가입': ['auth', 'signup', 'approval'],
        '탐지': ['detection', 'inference', 'yolo'],
        '매뉴얼': ['manual', 'guide', 'docs'],
    }
    expanded = set(terms)
    for term in terms:
        expanded.update(synonyms.get(term, []))
    return sorted(expanded) or ['mdetect']


def _clean_string(value, max_length):
    if not isinstance(value, str):
        return ''
    clean = re.sub(r'\s+', ' ', value).strip()
    return clean[:max_length]


def _clean_path(value):
    clean = _clean_string(value, 200)
    if not clean.startswith('/'):
        return ''
    return clean.split('?', 1)[0].split('#', 1)[0]


def _clean_string_list(value, max_items, max_length):
    if not isinstance(value, list):
        return []
    clean_values = []
    for item in value:
        clean = _clean_string(item, max_length)
        if clean:
            clean_values.append(clean)
        if len(clean_values) >= max_items:
            break
    return clean_values


def _best_excerpt(content, terms, max_chars):
    normalized = content.strip()
    if len(normalized) <= max_chars:
        return normalized
    lower_content = normalized.lower()
    first_match = min((lower_content.find(term) for term in terms if lower_content.find(term) >= 0), default=-1)
    if first_match < 0:
        return normalized[:max_chars]
    start = max(0, first_match - max_chars // 3)
    end = min(len(normalized), start + max_chars)
    return normalized[start:end]
