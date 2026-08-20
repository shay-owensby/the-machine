"""A small Markdown renderer for report documents.

Deliberately not a general Markdown implementation. It covers exactly the
constructs the report templates use, and it understands a few things about
*reports* that a general renderer does not:

* the masthead block under the title, which becomes a metadata rail rather
  than a paragraph of bold labels;
* ``## Section`` boundaries, which become real ``<section>`` elements so the
  stylesheet can put a hairline and a lot of air above each one;
* which table cells hold numbers, so they can be right-aligned and set in
  tabular figures without the author having to mark them up;
* which cells say "not available", so an absence is styled as an absence and
  can never be mistaken for a zero.

Standard library only, in keeping with the rest of the plugin: matplotlib
remains the single optional dependency.
"""

import re

__all__ = ["render", "render_body"]

_COMMENT = re.compile(r"<!--.*?-->", re.S)
_NUMERIC = re.compile(r"""^[^\w]*[-+(]?\s*        # currency symbol / sign
                          [\d,]+(?:\.\d+)?        # the number
                          \s*[%)]?                # percent or closing paren
                          (?:\s*[A-Za-z$€£¥]{0,4})?$""", re.X)
_NA_TEXT = re.compile(r"^\s*(?:n/?a|not available|not applicable|—|–|-{1,2})\s*"
                      r"(?:\(.*\))?\s*$", re.I)


def _esc(text):
    return (text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


# --------------------------------------------------------------------------
# Inline
# --------------------------------------------------------------------------

_PRIORITY = re.compile(r"^<strong>(High|Medium|Low)</strong>\s*", re.I)


def _priority_chip(html):
    """Turn a leading **High** / **Medium** / **Low** into a bordered marker.

    Recommendations arrive from the analysis already sorted by priority, and
    the priority is the first thing a reader triages on. As bold body text it
    disappears into the sentence; as a chip it can be scanned down the margin.
    """
    m = _PRIORITY.match(html)
    if not m:
        return html
    level = m.group(1).lower()
    return ('<span class="pri pri-%s">%s</span>%s'
            % (level, m.group(1), html[m.end():]))


def _inline(text):
    """Inline markup. Code spans are protected before anything else runs."""
    spans = []

    def stash(m):
        spans.append(m.group(1))
        return "\x00%d\x00" % (len(spans) - 1)

    text = re.sub(r"`([^`]+)`", stash, text)
    text = _esc(text)

    # Links. Images are handled at block level; any that survive here are
    # inline decoration and get the same treatment.
    text = re.sub(r"!\[([^\]]*)\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)",
                  lambda m: '<img src="%s" alt="%s">' % (m.group(2), m.group(1)),
                  text)
    text = re.sub(r"\[([^\]]+)\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)",
                  lambda m: '<a href="%s">%s</a>' % (m.group(2), m.group(1)), text)

    text = re.sub(r"\*\*(?=\S)(.+?)(?<=\S)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"(?<![\w*])\*(?=\S)([^*]+?)(?<=\S)\*(?![\w*])", r"<em>\1</em>", text)
    text = re.sub(r"(?<![\w_])_(?=\S)([^_]+?)(?<=\S)_(?![\w_])", r"<em>\1</em>", text)

    def unstash(m):
        return "<code>%s</code>" % _esc(spans[int(m.group(1))])

    return re.sub(r"\x00(\d+)\x00", unstash, text)


# --------------------------------------------------------------------------
# Tables
# --------------------------------------------------------------------------

def _split_row(line):
    line = line.strip()
    if line.startswith("|"):
        line = line[1:]
    if line.endswith("|"):
        line = line[:-1]
    return [c.strip() for c in line.split("|")]


def _is_delimiter(line):
    cells = _split_row(line)
    if not cells:
        return False
    return all(re.match(r"^:?-{2,}:?$", c) for c in cells)


def _alignments(line):
    out = []
    for c in _split_row(line):
        if c.endswith(":") and c.startswith(":"):
            out.append("center")
        elif c.endswith(":"):
            out.append("right")
        else:
            out.append(None)
    return out


def _cell_class(text, align):
    """Right-align and tabular-set anything that is a number.

    Inferred rather than declared: the report templates are written by an agent
    reading an analysis file, and requiring it to also mark up alignment is one
    more thing that can be got wrong in a way the reader sees.
    """
    plain = re.sub(r"[*`]", "", text).strip()
    if _NA_TEXT.match(plain):
        return "na"
    if align == "right" or (align is None and plain and _NUMERIC.match(plain)):
        return "num"
    if align == "center":
        return "center"
    return ""


def _table(header, delim, rows):
    aligns = _alignments(delim)
    head_cells = _split_row(header)

    def klass(i, text):
        align = aligns[i] if i < len(aligns) else None
        return _cell_class(text, align)

    out = ['<div class="table-wrap"><table>', "<thead><tr>"]
    for i, c in enumerate(head_cells):
        cls = "num" if (i < len(aligns) and aligns[i] == "right") else ""
        # A header over a numeric column aligns with the column beneath it.
        if not cls and rows:
            body_cls = [klass(i, _split_row(r)[i])
                        for r in rows if len(_split_row(r)) > i]
            if body_cls and all(b == "num" for b in body_cls):
                cls = "num"
        out.append('<th%s>%s</th>' % (' class="%s"' % cls if cls else "", _inline(c)))
    out.append("</tr></thead><tbody>")

    for r in rows:
        cells = _split_row(r)
        out.append("<tr>")
        for i, c in enumerate(cells):
            cls = klass(i, c)
            out.append("<td%s>%s</td>"
                       % (' class="%s"' % cls if cls else "", _inline(c)))
        out.append("</tr>")
    out.append("</tbody></table></div>")
    return "".join(out)


# --------------------------------------------------------------------------
# Blocks
# --------------------------------------------------------------------------

_META_LINE = re.compile(r"^\*\*([^*]+):\*\*\s*(.*)$")


def _masthead(title, meta_lines):
    parts = []
    for line in meta_lines:
        # A meta line may carry several fields separated by a middle dot.
        for chunk in re.split(r"\s+·\s+", line):
            m = _META_LINE.match(chunk.strip())
            if m:
                parts.append("<span><b>%s</b> %s</span>"
                             % (_inline(m.group(1)), _inline(m.group(2))))
            elif chunk.strip():
                parts.append("<span>%s</span>" % _inline(chunk.strip()))
    meta = '<div class="meta">%s</div>' % "".join(parts) if parts else ""
    return '<header class="masthead"><h1>%s</h1>%s</header>' % (_inline(title), meta)


def render_body(text, figure_resolver=None):
    """Markdown to an HTML fragment.

    ``figure_resolver(src, alt)`` may return finished HTML for an image — used
    to inline an SVG chart or to state, in the chart's place, that it was not
    drawn. Returning ``None`` falls back to a plain ``<img>``.
    """
    text = _COMMENT.sub("", text)
    lines = text.replace("\r\n", "\n").split("\n")

    out = []
    section_open = False
    i = 0
    n = len(lines)
    seen_title = False

    def close_section():
        nonlocal section_open
        if section_open:
            out.append("</section>")
            section_open = False

    while i < n:
        line = lines[i]
        stripped = line.strip()

        if not stripped:
            i += 1
            continue

        # Fenced code
        if stripped.startswith("```"):
            lang = stripped[3:].strip()
            i += 1
            buf = []
            while i < n and not lines[i].strip().startswith("```"):
                buf.append(lines[i])
                i += 1
            i += 1
            cls = ' class="lang-%s"' % _esc(lang) if lang else ""
            out.append("<pre><code%s>%s</code></pre>"
                       % (cls, _esc("\n".join(buf))))
            continue

        # Raw HTML passthrough (the tile grid, and anything the renderer
        # composed before handing the document over).
        if stripped.startswith("<") and not stripped.startswith("<!--"):
            buf = [line]
            i += 1
            while i < n and lines[i].strip():
                buf.append(lines[i])
                i += 1
            out.append("\n".join(buf))
            continue

        # Headings
        m = re.match(r"^(#{1,4})\s+(.*)$", stripped)
        if m:
            level, content = len(m.group(1)), m.group(2).strip()
            if level == 1 and not seen_title:
                seen_title = True
                # Collect the metadata block that follows the title.
                j = i + 1
                meta = []
                while j < n:
                    s = lines[j].strip()
                    if not s:
                        j += 1
                        if meta:
                            break
                        continue
                    if s.startswith("#") or s.startswith("---") or s.startswith("|"):
                        break
                    if _META_LINE.match(s) or (meta and s.startswith("**")):
                        meta.append(s)
                        j += 1
                        continue
                    break
                out.append(_masthead(content, meta))
                i = j
                continue
            if level == 2:
                close_section()
                out.append("<section>")
                section_open = True
            out.append("<h%d>%s</h%d>" % (level, _inline(content), level))
            i += 1
            continue

        # Horizontal rule. Between sections it is redundant with the section
        # rule the stylesheet draws, so it is dropped there.
        if re.match(r"^(\*\s*){3,}$|^(-\s*){3,}$|^(_\s*){3,}$", stripped):
            j = i + 1
            while j < n and not lines[j].strip():
                j += 1
            if j < n and lines[j].strip().startswith("## "):
                i += 1
                continue
            out.append("<hr>")
            i += 1
            continue

        # Standalone image -> figure
        m = re.match(r"^!\[([^\]]*)\]\(([^)\s]+)(?:\s+\"([^\"]*)\")?\)$", stripped)
        if m:
            alt, src, title = m.group(1), m.group(2), m.group(3)
            html = figure_resolver(src, alt) if figure_resolver else None
            if html is None:
                html = ('<figure><img src="%s" alt="%s">%s</figure>'
                        % (_esc(src), _esc(alt),
                           "<figcaption>%s</figcaption>" % _inline(title) if title else ""))
            out.append(html)
            i += 1
            continue

        # Table
        if stripped.startswith("|") and i + 1 < n and _is_delimiter(lines[i + 1]):
            header, delim = lines[i], lines[i + 1]
            i += 2
            rows = []
            while i < n and lines[i].strip().startswith("|"):
                rows.append(lines[i])
                i += 1
            out.append(_table(header, delim, rows))
            continue

        # Blockquote
        if stripped.startswith(">"):
            buf = []
            while i < n and lines[i].strip().startswith(">"):
                buf.append(re.sub(r"^\s*>\s?", "", lines[i]))
                i += 1
            out.append("<blockquote>%s</blockquote>" % render_body("\n".join(buf)))
            continue

        # Lists
        m = re.match(r"^([-*+]|\d+\.)\s+(.*)$", stripped)
        if m:
            ordered = not m.group(1) in ("-", "*", "+")
            tag = "ol" if ordered else "ul"
            items = []
            while i < n:
                s = lines[i].strip()
                mm = re.match(r"^([-*+]|\d+\.)\s+(.*)$", s)
                if mm:
                    items.append(mm.group(2))
                    i += 1
                elif s and not re.match(r"^(#{1,4}\s|\||>|```)", s) and items:
                    items[-1] += " " + s      # lazy continuation
                    i += 1
                else:
                    break
            out.append("<%s>%s</%s>"
                       % (tag,
                          "".join("<li>%s</li>" % _priority_chip(_inline(x))
                                  for x in items),
                          tag))
            continue

        # Paragraph
        buf = []
        while i < n and lines[i].strip():
            s = lines[i].strip()
            if re.match(r"^(#{1,4}\s|\||>|```|!\[)", s) or _is_delimiter(s):
                break
            if re.match(r"^([-*+]|\d+\.)\s+", s) and buf:
                break
            buf.append(s)
            i += 1
        if buf:
            out.append("<p>%s</p>" % _inline(" ".join(buf)))

    close_section()
    return "\n".join(out)


def render(text, figure_resolver=None):
    return render_body(text, figure_resolver)
