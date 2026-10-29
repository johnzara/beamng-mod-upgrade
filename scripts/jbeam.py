"""Lenient JBeam (relaxed JSON) parser: comments, missing/trailing commas, bare literals."""
import re, json, sys, os
def _tokens(s):
    i, n = 0, len(s)
    while i < n:
        c = s[i]
        if c in ' \t\r\n': i += 1; continue
        if s.startswith('//', i): i = s.find('\n', i); i = n if i < 0 else i; continue
        if s.startswith('/*', i): j = s.find('*/', i+2); i = n if j < 0 else j+2; continue
        if c in '{}[]:,': yield c; i += 1; continue
        if c == '"':
            j = i+1
            while j < n and s[j] != '"':
                j += 2 if s[j] == '\\' else 1
            yield ('s', s[i+1:j]); i = j+1; continue
        m = re.compile(r'[^\s{}\[\]:,"]+').match(s, i)
        yield ('l', m.group(0)); i = m.end()
def _lit(t):
    v = t[1]
    if v in ('true','false'): return v == 'true'
    if v in ('null','nil'): return None
    try: return int(v)
    except ValueError: pass
    try: return float(v)
    except ValueError: return v
def parse(text):
    toks = list(_tokens(text)); pos = 0
    def val():
        nonlocal pos
        t = toks[pos]; pos += 1
        if t == '{':
            d = {}
            while True:
                while pos < len(toks) and toks[pos] == ',': pos += 1
                if toks[pos] == '}': pos += 1; return d
                k = val(); 
                if toks[pos] == ':': pos += 1
                d[k] = val()
        if t == '[':
            a = []
            while True:
                while pos < len(toks) and toks[pos] == ',': pos += 1
                if toks[pos] == ']': pos += 1; return a
                a.append(val())
        if isinstance(t, tuple): return t[1] if t[0] == 's' else _lit(t)
        raise ValueError('unexpected %r at token %d' % (t, pos))
    return val()
def load_dir(root):
    parts, errors = {}, []
    for dp, _, fs in os.walk(root):
        for f in fs:
            if f.endswith('.jbeam'):
                p = os.path.join(dp, f)
                try:
                    for k, v in parse(open(p, encoding='utf-8', errors='replace').read()).items():
                        if k in parts: errors.append(('duplicate part', k, p, parts[k]['__file']))
                        v['__file'] = os.path.relpath(p, root); parts[k] = v
                except Exception as e: errors.append(('parse', p, str(e)))
    return parts, errors
def rows(section):
    """Yield dict rows of a jbeam table section, applying header and inline modifier dicts."""
    if not isinstance(section, list) or not section: return
    hdr = section[0]; mods = {}
    for r in section[1:]:
        if isinstance(r, dict): mods.update(r); continue
        if not isinstance(r, list): continue
        d = dict(mods)
        for i, v in enumerate(r):
            if isinstance(v, dict): d.update(v)
            elif i < len(hdr): d[hdr[i]] = v
        yield d
