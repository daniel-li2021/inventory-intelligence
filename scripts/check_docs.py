"""Check repository Markdown navigation and the single persisted integration mode."""
from collections import Counter
from pathlib import Path
import re
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]


def fragments(text):
    """GitHub-style heading fragments, including repeated heading suffixes."""
    counts = Counter()
    found = set(re.findall(r'<[^>]+\bid=[\'\"]([^\'\"]+)', text))
    for heading in re.findall(r'^#{1,6}\s+(.+?)(?:\s+#+)?$', text, re.MULTILINE):
        heading = re.sub(r'!?\[([^\]]+)\]\([^)]*\)', r'\1', heading)
        slug = re.sub(r'[^\w\- ]', '', heading.lower()).replace(' ', '-')
        found.add(slug if not counts[slug] else f'{slug}-{counts[slug]}')
        counts[slug] += 1
    return found


def check():
    files = sorted({*ROOT.glob('*.md'), *ROOT.glob('docs/**/*.md'),
                    *ROOT.glob('deploy/**/*.md'), *ROOT.glob('.github/**/*.md')})
    errors = []
    local_links = 0
    for source in files:
        content = source.read_text()
        targets = re.findall(r'!?\[[^\]\n]*\]\((<[^>]+>|[^\s)]+)(?:\s+[\'\"][^\n]*?[\'\"])?\)', content)
        targets += re.findall(r'^\s*\[[^\]]+\]:\s*(<[^>]+>|\S+)', content, re.MULTILINE)
        for target in targets:
            parsed = urlsplit(target.strip('<>'))
            if parsed.scheme or parsed.netloc:
                continue  # External/retired Git links are validated by their pinned blobs at retirement.
            local_links += 1
            path = (source.parent / unquote(parsed.path)).resolve() if parsed.path else source
            label = f'{source.relative_to(ROOT)}: {target}'
            if not path.is_relative_to(ROOT) or not path.exists():
                errors.append(f'{label}: missing or outside-repository target')
            elif parsed.fragment and path.suffix == '.md':
                if unquote(parsed.fragment) not in fragments(path.read_text()):
                    errors.append(f'{label}: missing Markdown heading fragment')
    state = ROOT / 'docs/STATE.md'
    if not state.is_file():
        errors.append('docs/STATE.md: missing canonical state')
    else:
        content = state.read_text()
        modes = re.findall(r'^Integration mode:[ \t]*(\S+)[ \t]*$', content, re.MULTILINE)
        if len(modes) != 1 or modes[0] not in ('AUTO', 'REVIEW'):
            errors.append('docs/STATE.md: require exactly one Integration mode: AUTO or REVIEW line')
        if len(content.splitlines()) > 80:
            errors.append('docs/STATE.md: exceeds the 80-line current-state budget')
    for name in ('PLAN.md', 'DECISIONS.md', 'README.md'):
        if not (ROOT / 'docs' / name).is_file():
            errors.append(f'docs/{name}: missing knowledge entry point')
    return errors, len(files), local_links


if __name__ == '__main__':
    errors, files, links = check()
    if errors:
        print('\n'.join(errors))
        raise SystemExit(1)
    print(f'Documentation OK: {files} Markdown files, {links} local links; canonical mode/state valid.')
