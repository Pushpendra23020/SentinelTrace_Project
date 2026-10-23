from copy import deepcopy
from pathlib import Path
from shutil import copyfile

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.style import WD_STYLE_TYPE
from docx.enum.table import WD_ALIGN_VERTICAL
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor


ROOT = Path('/home/pushpendra/Documents/ChatGPT/Mini Project/SentinelTrace_Project')
TEMPLATE = Path('/home/pushpendra/Downloads/Mini_Project_Report_Format.docx')
OUTPUT = ROOT / 'deliverables/02_Project_Report/SentinelTrace_Project_Report_LIET_Format.docx'
TITLE = 'SentinelTrace An Explainable Local Log Based Threat Triage and Alert Prioritization System'
BRANCH = 'Computer Science and Engineering Cyber Security'


def set_cell_shading(cell, fill):
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = tc_pr.find(qn('w:shd'))
    if shd is None:
        shd = OxmlElement('w:shd')
        tc_pr.append(shd)
    shd.set(qn('w:fill'), fill)


def set_cell_border(cell, color='808080', size='6'):
    tc_pr = cell._tc.get_or_add_tcPr()
    borders = tc_pr.first_child_found_in('w:tcBorders')
    if borders is None:
        borders = OxmlElement('w:tcBorders')
        tc_pr.append(borders)
    for name in ('top', 'left', 'bottom', 'right', 'insideH', 'insideV'):
        edge = borders.find(qn(f'w:{name}'))
        if edge is None:
            edge = OxmlElement(f'w:{name}')
            borders.append(edge)
        edge.set(qn('w:val'), 'single')
        edge.set(qn('w:sz'), size)
        edge.set(qn('w:color'), color)


def set_repeat_table_header(row):
    tr_pr = row._tr.get_or_add_trPr()
    element = OxmlElement('w:tblHeader')
    element.set(qn('w:val'), 'true')
    tr_pr.append(element)


def clear_paragraph(paragraph):
    p = paragraph._p
    for child in list(p):
        if child.tag != qn('w:pPr'):
            p.remove(child)


def set_para(paragraph, text, *, size=11, bold=False, align=WD_ALIGN_PARAGRAPH.JUSTIFY,
             before=0, after=5, line=1.5, color=None, italic=False):
    clear_paragraph(paragraph)
    run = paragraph.add_run(text)
    run.font.name = 'Times New Roman'
    run._element.rPr.rFonts.set(qn('w:eastAsia'), 'Times New Roman')
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.italic = italic
    if color:
        run.font.color.rgb = RGBColor(*color)
    pf = paragraph.paragraph_format
    pf.alignment = align
    pf.space_before = Pt(before)
    pf.space_after = Pt(after)
    pf.line_spacing = line
    return paragraph


def style_run(run, size=11, bold=False, italic=False):
    run.font.name = 'Times New Roman'
    run._element.rPr.rFonts.set(qn('w:eastAsia'), 'Times New Roman')
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.italic = italic


def paragraph_after(paragraph, text='', style=None):
    new_p = OxmlElement('w:p')
    paragraph._p.addnext(new_p)
    p = paragraph._parent.add_paragraph()
    p._p.getparent().remove(p._p)
    new_p.addnext(p._p)
    if style:
        p.style = style
    if text:
        p.add_run(text)
    return p


def add_page_field(paragraph):
    fld = OxmlElement('w:fldSimple')
    fld.set(qn('w:instr'), ' PAGE \\* MERGEFORMAT ')
    run = OxmlElement('w:r')
    text = OxmlElement('w:t')
    text.text = '1'
    run.append(text)
    fld.append(run)
    paragraph._p.append(fld)


def set_page_number_format(section, fmt, start=None):
    sect_pr = section._sectPr
    pg = sect_pr.find(qn('w:pgNumType'))
    if pg is None:
        pg = OxmlElement('w:pgNumType')
        sect_pr.append(pg)
    pg.set(qn('w:fmt'), fmt)
    if start is not None:
        pg.set(qn('w:start'), str(start))


def set_cell_text(cell, text, *, size=10, bold=False, align=WD_ALIGN_PARAGRAPH.LEFT):
    for p in list(cell.paragraphs)[1:]:
        p._element.getparent().remove(p._element)
    set_para(cell.paragraphs[0], text, size=size, bold=bold, align=align, before=0, after=0, line=1.0)


def set_footer(section, label=None):
    footer = section.footer
    footer.is_linked_to_previous = False
    for p in footer.paragraphs:
        clear_paragraph(p)
    p = footer.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(0)
    if label:
        r = p.add_run(label + ' | ')
        style_run(r, 9)
    add_page_field(p)
    for run in p.runs:
        style_run(run, 9)


def add_update_fields(document):
    settings = document.settings.element
    update = settings.find(qn('w:updateFields'))
    if update is None:
        update = OxmlElement('w:updateFields')
        settings.append(update)
    update.set(qn('w:val'), 'true')


def paragraph_by_text(document, starts):
    for p in document.paragraphs:
        if p.text.strip().startswith(starts):
            return p
    raise ValueError(starts)


def remove_from_paragraph_to_end(document, marker):
    start = paragraph_by_text(document, marker)._p
    body = document._element.body
    removing = False
    for child in list(body):
        if child is start:
            removing = True
        if removing and child.tag != qn('w:sectPr'):
            body.remove(child)


def base_body_style(document):
    normal = document.styles['Normal']
    normal.font.name = 'Times New Roman'
    normal._element.rPr.rFonts.set(qn('w:eastAsia'), 'Times New Roman')
    normal.font.size = Pt(11)
    normal.paragraph_format.line_spacing = 1.5
    normal.paragraph_format.space_after = Pt(5)
    for name, size in [('Heading 1', 15), ('Heading 2', 13), ('Heading 3', 11)]:
        style = document.styles[name]
        style.font.name = 'Times New Roman'
        style._element.rPr.rFonts.set(qn('w:eastAsia'), 'Times New Roman')
        style.font.size = Pt(size)
        style.font.bold = True


def add_heading(document, text, level=2, chapter=False):
    p = document.add_paragraph()
    p.style = document.styles['Heading 1' if chapter else ('Heading 2' if level == 2 else 'Heading 3')]
    set_para(p, text, size=15 if chapter else (13 if level == 2 else 11), bold=True,
             align=WD_ALIGN_PARAGRAPH.CENTER if chapter else WD_ALIGN_PARAGRAPH.LEFT,
             before=0 if chapter else 6, after=10 if chapter else 5, line=1.0)
    p.paragraph_format.keep_with_next = True
    return p


def add_body(document, text, italic=False):
    p = document.add_paragraph()
    set_para(p, text, size=11, italic=italic, align=WD_ALIGN_PARAGRAPH.JUSTIFY,
             before=0, after=5, line=1.5)
    return p


def add_bullet(document, text):
    p = document.add_paragraph()
    set_para(p, '• ' + text, size=11, align=WD_ALIGN_PARAGRAPH.JUSTIFY, before=0, after=2, line=1.25)
    p.paragraph_format.left_indent = Inches(0.25)
    return p


def add_table(document, headers, rows, widths=None, font_size=10):
    table = document.add_table(rows=1, cols=len(headers))
    table.autofit = True
    hdr = table.rows[0]
    set_repeat_table_header(hdr)
    for i, text in enumerate(headers):
        c = hdr.cells[i]
        c.text = ''
        set_cell_shading(c, 'D9E2F3')
        set_cell_border(c)
        c.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
        p = c.paragraphs[0]
        set_para(p, text, size=font_size, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, before=0, after=0, line=1.0)
        if widths:
            c.width = Inches(widths[i])
    for row in rows:
        cells = table.add_row().cells
        for i, text in enumerate(row):
            c = cells[i]
            c.text = ''
            set_cell_border(c)
            c.vertical_alignment = WD_ALIGN_VERTICAL.TOP
            p = c.paragraphs[0]
            set_para(p, str(text), size=font_size, align=WD_ALIGN_PARAGRAPH.LEFT, before=0, after=0, line=1.0)
            if widths:
                c.width = Inches(widths[i])
    return table


def add_caption(document, text, figure=False):
    p = document.add_paragraph()
    set_para(p, text, size=10, bold=True, italic=figure,
             align=WD_ALIGN_PARAGRAPH.CENTER if figure else WD_ALIGN_PARAGRAPH.LEFT,
             before=3, after=6, line=1.0)
    return p


def add_diagram(document, columns, figure_no, caption):
    table = document.add_table(rows=1, cols=len(columns))
    for i, item in enumerate(columns):
        cell = table.cell(0, i)
        cell.text = ''
        set_cell_shading(cell, 'EAF2F8')
        set_cell_border(cell, color='4F81BD', size='10')
        p = cell.paragraphs[0]
        set_para(p, item, size=10, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, before=5, after=5, line=1.0)
        cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
    add_caption(document, f'Figure {figure_no} {caption}', figure=True)


def page_break(document):
    p = document.add_paragraph()
    p.add_run().add_break(WD_BREAK.PAGE)
    return p


def logical_page(document, heading, paragraphs, *, table=None, figure=None, bullets=None, label=None):
    if label:
        add_heading(document, label, chapter=True)
    add_heading(document, heading, level=2)
    for text in paragraphs:
        add_body(document, text)
    if bullets:
        for item in bullets:
            add_bullet(document, item)
    if figure:
        add_diagram(document, figure[0], figure[1], figure[2])
    if table:
        add_caption(document, table[0], figure=False)
        add_table(document, table[1], table[2], table[3] if len(table) > 3 else None)
    page_break(document)


def setup_front_matter(document):
    # Cover edits preserve the template's visual arrangements and logos.
    p = paragraph_by_text(document, 'PROJECT TITLE')
    set_para(p, TITLE, size=16, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, before=0, after=0, line=1.0, color=(0, 32, 96))
    set_para(paragraph_by_text(document, 'Computer Science & Engineering'), BRANCH, size=13, bold=True,
             align=WD_ALIGN_PARAGRAPH.CENTER, before=0, after=0, line=1.0, color=(128, 0, 0))
    cover_table = document.tables[0]
    set_cell_text(cover_table.cell(0, 0), 'Submitted by\nName: __________________________\nRoll No.: ________________________\nSemester and Section: ___________', size=10, align=WD_ALIGN_PARAGRAPH.LEFT)
    set_cell_text(cover_table.cell(0, 1), 'Under the Supervision of\nGuide Name: _____________________\nDesignation: ____________________', size=10, align=WD_ALIGN_PARAGRAPH.LEFT)

    set_para(paragraph_by_text(document, 'This is to certify'),
             f'This is to certify that the Mini Project Report entitled “{TITLE}” is a bonafide work carried out by ____________________ (Roll No. ____________________) in partial fulfilment of the requirements for the award of the degree of Bachelor of Technology in {BRANCH}, during the academic session 2026–27, under our supervision.',
             size=11, align=WD_ALIGN_PARAGRAPH.JUSTIFY, before=0, after=8, line=1.5)
    set_para(paragraph_by_text(document, 'The work embodied'),
             'The work embodied in this report has not been submitted elsewhere for the award of any other degree or diploma. To the best of our knowledge, the report fulfils the prescribed structure and formatting requirements of the Mini Project guidelines.',
             size=11, align=WD_ALIGN_PARAGRAPH.JUSTIFY, before=0, after=8, line=1.5)
    cert = document.tables[1]
    cert_values = [
        '______________________\nProject Guide\nName: __________________',
        '______________________\nProject Coordinator\nName: __________________',
        '______________________\nHead of Department\nName: __________________',
    ]
    for cell, value in zip(cert.rows[0].cells, cert_values):
        set_cell_text(cell, value, size=9, align=WD_ALIGN_PARAGRAPH.CENTER)
    set_para(paragraph_by_text(document, 'Date: [DD/MM/YYYY]'), 'Date: ____ / ____ / 2027', size=11, align=WD_ALIGN_PARAGRAPH.LEFT, before=0, after=0, line=1.0)
    set_para(paragraph_by_text(document, 'Place: [City]'), 'Place: Greater Noida', size=11, align=WD_ALIGN_PARAGRAPH.LEFT, before=0, after=0, line=1.0)

    set_para(paragraph_by_text(document, 'I hereby declare'),
             f'I hereby declare that the Mini Project Report entitled “{TITLE}” submitted to the Department of Computer Science and Engineering and Allied Branches, Lloyd Institute of Engineering and Technology, in partial fulfilment of the requirements for the degree of Bachelor of Technology in {BRANCH}, is an original record of work carried out by me under the guidance of the assigned project supervisor.',
             size=11, align=WD_ALIGN_PARAGRAPH.JUSTIFY, before=0, after=8, line=1.5)
    set_para(paragraph_by_text(document, 'I further declare'),
             'I further declare that this report has not been copied from any other source and that all references, data and material taken from other sources have been duly acknowledged. The institutional similarity report will be attached after the prescribed plagiarism check; no similarity percentage is claimed in this draft.',
             size=11, align=WD_ALIGN_PARAGRAPH.JUSTIFY, before=0, after=8, line=1.5)
    set_para(paragraph_by_text(document, 'Name: [Student Name]'), 'Name: __________________________', size=11, align=WD_ALIGN_PARAGRAPH.LEFT, before=0, after=0, line=1.0)
    set_para(paragraph_by_text(document, 'Roll No.: [University Roll No.]'), 'Roll No.: _______________________', size=11, align=WD_ALIGN_PARAGRAPH.LEFT, before=0, after=0, line=1.0)
    set_para(paragraph_by_text(document, 'Date: [DD/MM/YYYY]'), 'Date: ____ / ____ / 2027', size=11, align=WD_ALIGN_PARAGRAPH.LEFT, before=0, after=0, line=1.0)

    set_para(paragraph_by_text(document, 'I would like to express'),
             'I express my sincere gratitude to my project guide for clear technical direction, careful review, and constructive suggestions throughout the design, implementation and testing of SentinelTrace. The guidance helped convert a broad cybersecurity idea into a focused, verifiable local log-triage project.',
             size=11, align=WD_ALIGN_PARAGRAPH.JUSTIFY, before=0, after=8, line=1.5)
    set_para(paragraph_by_text(document, 'I am thankful to'),
             'I thank the Project Coordinator, the Head of the Department, and the faculty members of the Department of Computer Science and Engineering and Allied Branches for the laboratory facilities, academic support, and evaluation opportunities provided during this work.',
             size=11, align=WD_ALIGN_PARAGRAPH.JUSTIFY, before=0, after=8, line=1.5)
    set_para(paragraph_by_text(document, 'Finally, I thank'),
             'Finally, I thank my family, friends and classmates for their encouragement and for the feedback that improved the clarity of the dashboard, documentation and test cases.',
             size=11, align=WD_ALIGN_PARAGRAPH.JUSTIFY, before=0, after=8, line=1.5)

    abstract_anchor = paragraph_by_text(document, 'ABSTRACT')
    abstract = paragraph_after(abstract_anchor)
    set_para(abstract,
             'Security logs frequently contain early evidence of password guessing, probing, malformed requests and attempts to reach restricted resources; however, small teams often lack an accessible way to turn those raw records into prioritized and explainable leads. SentinelTrace is a local, rule-based cyber threat triage system developed to address this gap. It reads Apache-style access logs and SSH authentication messages, normalizes supported events, correlates repeated activity by source address, and produces findings for six observable attack categories: SSH brute force, successful login after repeated failures, path traversal, SQL injection indicators, command injection indicators, and web scanning. Each finding retains the relevant log evidence, severity, confidence, MITRE ATT&CK mapping, and a practical remediation recommendation. A transparent risk score aggregates distinct triggered categories per source IP and caps the result at 100 so that analysts can begin with the most concerning activity without trusting an opaque model. A standard-library Python backend exposes a local browser dashboard and JSON export, keeping the prototype simple to run and easy to inspect during evaluation. The supplied demonstration dataset produces six findings across four source addresses, while six automated unit tests verify detection coverage, parser separation, malformed-line resilience, encoded traversal handling, and scoring behaviour. SentinelTrace is intentionally a triage prototype rather than a replacement for a production SIEM, but it demonstrates a defensible workflow from log ingestion to evidence-backed alert prioritization.',
             size=11, align=WD_ALIGN_PARAGRAPH.JUSTIFY, before=6, after=0, line=1.5)

    # Insert list entries into the source front-matter pages without moving its static contents control.
    lof = paragraph_by_text(document, 'LIST OF FIGURES')
    lot = paragraph_by_text(document, 'LIST OF TABLES')
    for item in reversed([
        'Figure 3.1 SentinelTrace processing architecture ........................................ 20',
        'Figure 3.2 Data flow for log analysis ............................................................ 22',
        'Figure 3.3 Conceptual finding model ............................................................. 23',
        'Figure 4.1 Module interaction flow .................................................................. 30',
        'Figure 4.2 Detection and prioritization pipeline ............................................. 34',
        'Figure 5.1 Test execution workflow ................................................................... 43',
        'Figure 6.1 Demonstration finding distribution ................................................ 51',
    ]):
        p = paragraph_after(lof, item)
        set_para(p, item, size=10, align=WD_ALIGN_PARAGRAPH.LEFT, before=0, after=2, line=1.0)
    for item in reversed([
        'Table 1.1 Project objectives and success criteria .......................................... 12',
        'Table 2.1 Related-work comparison .................................................................. 16',
        'Table 3.1 Functional requirements ..................................................................... 18',
        'Table 3.2 Feasibility assessment ......................................................................... 19',
        'Table 4.1 Detection-rule catalogue ..................................................................... 33',
        'Table 5.1 Functional test cases ........................................................................... 45',
        'Table 6.1 Demonstration results ......................................................................... 52',
    ]):
        p = paragraph_after(lot, item)
        set_para(p, item, size=10, align=WD_ALIGN_PARAGRAPH.LEFT, before=0, after=2, line=1.0)

    abbr = document.tables[2]
    values = [
        ('API', 'Application Programming Interface'),
        ('DFD', 'Data Flow Diagram'),
        ('HTTP', 'Hypertext Transfer Protocol'),
        ('IDS', 'Intrusion Detection System'),
        ('IP', 'Internet Protocol'),
        ('JSON', 'JavaScript Object Notation'),
        ('MITRE ATT&CK', 'Adversarial Tactics Techniques and Common Knowledge'),
        ('SIEM', 'Security Information and Event Management'),
        ('SSH', 'Secure Shell'),
        ('URL', 'Uniform Resource Locator'),
    ]
    while len(abbr.rows) > 1:
        abbr._tbl.remove(abbr.rows[-1]._tr)
    for ab, full in values:
        row = abbr.add_row().cells
        set_para(row[0].paragraphs[0], ab, size=10, align=WD_ALIGN_PARAGRAPH.LEFT, before=0, after=0, line=1.0)
        set_para(row[1].paragraphs[0], full, size=10, align=WD_ALIGN_PARAGRAPH.LEFT, before=0, after=0, line=1.0)


def build_chapters(document):
    # Chapter 1
    logical_page(document, '1.1 Background', [
        'Modern services generate access and authentication records continuously. A web server records the requested path, response status, remote address and user agent; an SSH service records successful and unsuccessful authentication attempts. These records are valuable because an attacker generally interacts with exposed services before a serious compromise is confirmed. The difficulty is not only collecting logs but deciding which small set of events deserves immediate attention.',
        'Commercial security information and event management platforms can collect, correlate and visualise this evidence, but their cost, deployment effort and rule complexity can discourage a small laboratory, student project or low-resource team. In those settings, an analyst may read files manually or rely on a single keyword search. That approach loses context: a failed SSH login has a different meaning when it appears many times from one address, and a suspicious URL has more value when the exact encoded request is preserved.',
        'SentinelTrace explores a deliberately constrained alternative. It operates locally on two common log sources, makes each detection rule visible, and explains why a result was prioritised. The project therefore focuses on analyst support and defensible evidence rather than attempting to claim autonomous intrusion prevention.'
    ], table=('Table 1.1 Project objectives and success criteria', ['Objective', 'Evaluation indicator'], [
        ('Parse supported log sources', 'Apache access and SSH password messages are classified separately.'),
        ('Detect observable threats', 'Six documented categories are triggered by the demonstration data.'),
        ('Prioritize transparently', 'Per-IP category weights form a bounded risk score.'),
        ('Explain each result', 'Finding retains evidence, severity, confidence, mapping and recommendation.'),
    ], [2.4, 4.0]), label='CHAPTER 1 INTRODUCTION')
    logical_page(document, '1.2 Problem Statement', [
        'Raw logs are high-volume, semi-structured records. A user who opens them in a text editor sees separate lines rather than an investigation story. The same hostile source may attempt several passwords, search for common administrative paths, submit an encoded traversal sequence, and later send an injection-like request. Without correlation, each line looks small and the most important source can be missed.',
        'The problem addressed by this project is to transform selected local log files into a short, evidence-backed triage view. The solution must accept noisy input, ignore unsupported lines safely, identify a limited and documented set of patterns, group the resulting evidence by source IP address, and produce a clear reason for every score. It should not depend on a cloud account, a database server or third-party machine-learning services.',
        'A useful outcome is not a binary claim that a host is compromised. Instead, the outcome is a ranked list of investigation leads. A security reviewer can compare the preserved log evidence with the rule that matched, inspect the confidence and mitigation advice, and decide whether further containment or log collection is justified.'
    ])
    logical_page(document, '1.3 Objectives and Contributions', [
        'The primary objective is to deliver a demonstrable cybersecurity mini project with a clear chain from input evidence to output decision. The system accepts a log file, recognizes supported access and SSH formats, and builds a normalized event record before any rule is applied. This separation makes parsing and detection easier to test independently.',
        'A second objective is transparent alerting. SentinelTrace does not hide its decisions behind a statistical classifier. It names the triggered rule category, retains the original line, assigns a documented severity and confidence, attaches a relevant MITRE ATT&CK technique where appropriate, and suggests a focused response action. This design supports evaluation because the reviewer can reproduce the result from the sample input.',
        'A third objective is local usability. The project contains a small Python HTTP server, a browser dashboard, a JSON export path, sample data and automated tests. The implementation uses the Python standard library only, which reduces installation friction and makes the codebase suitable for laboratory demonstration on a typical student machine.'
    ], bullets=[
        'Detect six scoped categories without claiming coverage of all attacker behaviour.',
        'Prioritize sources through a bounded category-based risk score.',
        'Keep evidence and recommendation attached to every finding.',
        'Provide a reproducible demonstration dataset and unit-test suite.'
    ])
    logical_page(document, '1.4 Scope of the Project and Organisation of the Report', [
        'The project scope is intentionally narrow. SentinelTrace supports Apache-style access log lines and SSH password authentication messages represented in the supplied sample. It is an offline or local-file triage tool; it does not ingest a live message queue, perform endpoint response, authenticate users, or provide multi-tenant storage. The rule set is signature-oriented and its output must be reviewed by a human analyst.',
        'This boundary is useful because it keeps the implemented claims testable. A path traversal rule can be verified with both plain and URL-encoded path patterns. SSH repeated-failure behaviour can be verified with a known sequence. A bounded risk score can be checked from the documented rule weights. Features outside this boundary, such as long-term threat intelligence enrichment and distributed storage, are recorded as future scope rather than presented as completed work.',
        'The remainder of the report reviews related practice, states requirements and design decisions, explains implementation modules, documents test evidence, discusses the sample results, and concludes with limitations and feasible extensions.'
    ])

    # Chapter 2
    logical_page(document, '2.1 Review of Related Work', [
        'Log management guidance emphasises that logs are useful only when the organization defines collection, review and retention practices around them. NIST SP 800-92 describes log management as a lifecycle involving generation, analysis, storage and disposal [1]. SentinelTrace takes the analysis portion of that lifecycle as its educational focus: it receives already-generated lines and makes a small set of meaningful patterns easier to review.',
        'OWASP guidance is relevant because web application logs can capture suspicious requests, errors, authentication activity and contextual attributes that assist incident response [2]. The project keeps raw evidence close to the result rather than presenting an alert title alone. This is important when a rule detects an encoded path or an injection-like token: the analyst must see the request that caused the finding.',
        'MITRE ATT&CK provides a common vocabulary for behaviours such as password guessing, valid-account use, exploitation of public-facing applications, command interpretation and scanning [3]–[8]. SentinelTrace does not claim to identify an adversary group; it uses selected technique references to help a student evaluator relate simple log observations to recognized security concepts.'
    ], table=('Table 2.1 Related-work comparison', ['Approach', 'Strength', 'Gap addressed by SentinelTrace'], [
        ('Manual log review', 'Direct access to raw evidence', 'Slow, inconsistent prioritization across related lines.'),
        ('Full SIEM platform', 'Broad ingestion and correlation', 'May be costly or complex for a small local demonstration.'),
        ('Black-box anomaly model', 'Can surface unusual patterns', 'Often difficult to explain and needs representative training data.'),
        ('SentinelTrace', 'Local, evidence-led, reproducible rules', 'Limited scope; not a replacement for enterprise monitoring.'),
    ], [1.55, 1.6, 3.25]), label='CHAPTER 2 LITERATURE REVIEW AND EXISTING SYSTEM')
    logical_page(document, '2.1.1 Log Management and Evidence Preservation', [
        'A detection result is useful only when it can be checked. For that reason, the normalized event retains source information, the parsed address where available, timestamp text, the original line, and the source type. The finding then references this event evidence. This is a modest but important form of traceability: a reviewer can move from dashboard result to the log fragment without re-running a search.',
        'The project also treats malformed or unsupported lines as an expected condition. Real log files may contain service messages, partial records, rotated-file headers or a format that the parser does not support. Rather than failing the complete analysis, SentinelTrace increments the event count and avoids producing an unsupported finding. This behaviour is covered by an automated test and reflects the engineering principle that imperfect input should not make the triage tool unusable.',
        'The design is not intended to establish forensic chain of custody. It is a classroom prototype that demonstrates evidence-aware analysis. A production deployment would need secure log transport, access controls, timestamp normalization, retention policy, cryptographic integrity measures and documented incident-handling procedures.'
    ])
    logical_page(document, '2.1.2 Detection Approaches and Explainability', [
        'Signature and rule-based detection are appropriate when a pattern has a clear textual expression. Repeated SSH failure messages, traversal sequences such as dot-dot slash, common scanner paths, and recognisable SQL or command separators can be expressed as readable conditions. Their advantages are deterministic output, low local resource use, and simple unit testing. Their weakness is sensitivity to evasion, variation and false positives.',
        'Statistical anomaly detection and machine learning can discover patterns beyond fixed signatures, but they introduce different challenges: a dataset must represent normal and hostile activity, model behaviour must be evaluated, and the output must still be understood by the analyst. For a mini project, an opaque score without supporting evidence would reduce the value of the demonstration.',
        'SentinelTrace therefore adopts an explainable rule engine. Each rule is a small, named predicate applied after parsing or correlation. The report documents what the rule observes, which severity it contributes, and how the finding is shown. This makes limitations visible rather than concealing them under a generic “AI detection” label.'
    ])
    logical_page(document, '2.2 Existing System', [
        'Existing systems typically fall into three categories. First, a command-line workflow lets an administrator search files with a tool such as grep or filter them with a script. It is flexible but depends heavily on the operator remembering the right pattern and manually connecting related events. Second, commercial or open-source SIEM solutions can centralize logs and apply numerous correlation rules, but installation, storage and operational administration may be beyond the intended scope of a short academic project.',
        'Third, simple dashboard projects often display line counts or keyword matches. They may identify that a word such as “failed” appears, but they do not always preserve an explanation of why a specific source was ranked higher than another source. They can also overstate their security value by turning a single suspicious token into a definitive attack conclusion.',
        'The existing baseline for a small laboratory is therefore usually manual reading plus basic filtering. SentinelTrace improves that baseline with parsers, scoped rules, correlation by source IP, explicit risk contributions and exportable structured output, while retaining a minimal and inspectable deployment model.'
    ])
    logical_page(document, '2.3 Gaps Identified', [
        'The literature and existing-system review identifies five practical gaps for the stated mini-project context. First, raw line-by-line review does not rank sources. Second, keyword-only matching loses parser context and can confuse access logs with authentication messages. Third, a generic alert title may omit the exact evidence that an evaluator needs to verify. Fourth, unexplained score values make prioritization difficult to defend. Fifth, many rich platforms require services or accounts that are not necessary for demonstrating the core triage concept.',
        'The project addresses these gaps by separating ingestion, normalization, rule detection, correlation and presentation. The rule catalogue is limited but documented. The risk calculation is category-based, not a hidden accumulator of every repeated log line, so repeated instances do not automatically create an unbounded score. This prevents volume alone from obscuring the reason for priority.',
        'These choices do not eliminate false positives or adversarial evasion. They make the system’s reasoning inspectable and therefore easier to refine. An evaluator can identify a weak rule, adjust it, and add a corresponding unit test without redesigning the entire application.'
    ])
    logical_page(document, '2.4 Proposed System', [
        'The proposed system is SentinelTrace, a local web-assisted log triage application. A user selects a supported log file through the dashboard. The backend reads lines, parses known formats, constructs normalized event dictionaries, evaluates event-level rules, evaluates correlated SSH behaviour, aggregates unique rule categories by IP address, and returns a structured analysis. The browser interface displays a summary, ranked sources and detailed findings; the same analysis can be exported as JSON.',
        'The system has three design properties. It is explainable because every result contains evidence and a named category. It is bounded because the score uses documented category weights and a maximum of 100. It is lightweight because the backend relies on Python standard-library modules and listens on the local loopback interface. These properties suit a fourth-year mini-project demonstration where evaluators should be able to run and inspect the program quickly.',
        'The proposal is evaluated against the sample data and tests rather than a claim of production-grade attack coverage. This distinction is maintained throughout the report so that the completed implementation remains credible.'
    ])

    # Chapter 3
    logical_page(document, '3.1 Requirement Analysis', [
        'Requirement analysis translated the problem statement into observable system behaviour. The core requirement is not merely to count lines; it is to create a structured result that a reviewer can trace back to source evidence. The design therefore distinguishes normalised events, findings, per-IP summaries and overall summary values. Each object has a purpose in the analysis workflow and can be inspected in a JSON export.',
        'Requirements were prioritised according to demonstrability and security relevance. Correct parsing and safe handling of unknown lines come before visual appearance. Detection rules must produce evidence and recommendations before scoring is introduced. The local interface is then added as a presentation layer over the same analysis result, avoiding separate dashboard-only logic.',
        'The following functional requirements form the acceptance baseline for the prototype.'
    ], table=('Table 3.1 Functional requirements', ['ID', 'Requirement', 'Verification'], [
        ('FR1', 'Read a selected local text log file.', 'Dashboard upload and sample-data run.'),
        ('FR2', 'Recognize supported Apache and SSH formats.', 'Parser-source unit test.'),
        ('FR3', 'Detect six scoped threat categories.', 'Demonstration-category unit test.'),
        ('FR4', 'Correlate repeated SSH attempts by source IP.', 'Transparent-score unit test.'),
        ('FR5', 'Show evidence, severity and recommendation.', 'Dashboard finding detail / JSON export.'),
        ('FR6', 'Ignore malformed lines without crashing.', 'Malformed-line unit test.'),
    ], [0.55, 3.7, 2.2]), label='CHAPTER 3 SYSTEM ANALYSIS AND DESIGN')
    logical_page(document, '3.1.1 Functional Requirements', [
        'The ingestion function must preserve the original input line even when it extracts structured fields. For Apache-style access logs, the relevant fields include remote IP address, method, path, status and user agent when available. For SSH authentication records, the relevant fields include source address, account context where present and whether the event represents a failed or accepted password attempt.',
        'The detection layer must identify event-level web patterns and correlation-level SSH patterns. It must produce a finding object with an identifier, category, severity, confidence, source address, evidence, attack-technique mapping and recommendation. The system must not invent missing fields; when parsing does not yield a source address, the source is marked as unknown rather than guessed.',
        'The presentation layer must provide summary counts, a ranked IP view, detailed findings and JSON export. The browser is a convenience interface, not an alternate analysis engine. This separation makes it possible to run the analyzer from tests and from the local server using the same code path.'
    ])
    logical_page(document, '3.1.2 Non Functional Requirements', [
        'Explainability is the principal non-functional requirement. A finding without its triggering evidence does not satisfy the project goal, even if its label appears plausible. The system consequently returns a human-readable reason and retains raw line context. Relatedly, score calculation must be understandable from code and documentation: distinct categories contribute fixed weights, and the total is capped at 100.',
        'Reliability is addressed through defensive parsing. Unsupported or malformed lines should not terminate analysis. Maintainability is addressed through a small project structure in which parsing and rules reside in clearly named modules. Portability is addressed by using a standard Python interpreter and a local browser rather than requiring a database or cloud service.',
        'The prototype also applies a practical privacy and exposure constraint: the server binds to 127.0.0.1. This reduces accidental network exposure during a classroom demonstration. It is not an authentication mechanism and would need augmentation before any multi-user deployment.'
    ], table=('Table 3.2 Non-functional requirements', ['Property', 'Design response'], [
        ('Explainability', 'Evidence, rule category, confidence and recommendation accompany each finding.'),
        ('Reliability', 'Malformed records are counted but do not crash analysis.'),
        ('Maintainability', 'Parser, rules, analyzer and server are separated into modules.'),
        ('Portability', 'Standard-library Python and a local browser are sufficient.'),
        ('Safety', 'Loopback-only listener avoids unintended remote access during evaluation.'),
    ], [1.5, 5.0]))
    logical_page(document, '3.1.3 Hardware and Software Requirements', [
        'The project was intentionally designed for ordinary student hardware. Analysis of the supplied sample is lightweight because it processes text locally and retains only a small structured representation. No GPU, external database service, message broker or cloud account is required. A machine capable of running a modern Python interpreter and a web browser is sufficient for the demonstration.',
        'The source code is organized as a Python application. The backend uses standard-library facilities for text processing, regular expressions, JSON serialization, HTTP serving and file handling. The interface is a static HTML page served locally. This technology choice is appropriate for a mini project because a reviewer can inspect the implementation without resolving a large dependency tree.',
        'The test suite uses Python unittest and runs from the project directory. The report documents the actual supported environment rather than providing unsupported performance claims for high-volume enterprise streams.'
    ], table=('Table 3.3 Minimum evaluation environment', ['Component', 'Requirement'], [
        ('Processor and memory', 'Typical laboratory or personal computer; no special accelerator required.'),
        ('Operating system', 'Any platform with a supported Python 3 interpreter and browser.'),
        ('Runtime', 'Python 3 standard library.'),
        ('Interface', 'Modern local web browser.'),
        ('Input', 'Plain-text Apache-style or SSH password log lines.'),
    ], [2.2, 4.3]))
    logical_page(document, '3.2 Feasibility Study', [
        'Feasibility analysis asks whether the proposed scope can be built, demonstrated and maintained within a mini-project schedule. The project is technically feasible because the target log formats are text-based and the scoped rules are simple enough to express as parser checks or regular expressions. The sample dataset provides a controlled input for verification.',
        'Economic feasibility is favourable because the implementation uses the installed Python runtime and standard library. No paid API, managed database or commercial SIEM license is required for the prototype. Operational feasibility is also favourable for a classroom setting because the workflow is short: start the local server, open the browser, analyze the supplied log, inspect results, and export JSON if required.',
        'Feasibility does not imply production readiness. A broader deployment would introduce operational requirements such as secure log collection, permission handling, role-based access, storage planning and alert escalation procedures.'
    ], table=('Table 3.4 Feasibility assessment', ['Dimension', 'Assessment', 'Reason'], [
        ('Technical', 'Feasible', 'Supported formats and rules are implementable with local text processing.'),
        ('Economic', 'Feasible', 'No paid platform or external service is required.'),
        ('Operational', 'Feasible', 'Simple local workflow suits laboratory demonstration.'),
        ('Schedule', 'Feasible', 'Module boundaries allow incremental construction and testing.'),
    ], [1.35, 1.2, 3.95]))
    logical_page(document, '3.3 System Architecture', [
        'The architecture follows a layered pipeline. The input layer reads a text file. The parser layer labels supported lines as access or SSH events and extracts fields required by later stages. The detection layer applies rules to individual events and a correlation rule to grouped SSH activity. The scoring layer combines distinct categories by source IP. Finally, the server and browser layer render the same structured output for human review.',
        'This arrangement avoids mixing web-page code with security reasoning. The analyzer can be invoked directly in tests, which gives better confidence than testing only a rendered page. It also provides a natural location for future extensions: a new parser could be added without changing the dashboard, and a new rule could be registered without changing how JSON is exported.',
        'The architecture deliberately keeps the raw log evidence in the result rather than substituting a database identifier. This is convenient for the local prototype and makes the evaluation artefact self-contained.'
    ], figure=(['Log file input', 'Parser and normalizer', 'Rule and correlation engine', 'Risk scorer', 'Dashboard and JSON export'], '3.1', 'SentinelTrace processing architecture'))
    logical_page(document, '3.4.1 Data Flow Diagram', [
        'At the context level, a student or evaluator supplies a local log file and receives a structured analysis. The system does not send the log to an external service. This is important when working with security records that may contain addresses, account names or request paths. The output contains a summary, finding list, IP prioritization list and parser statistics.',
        'At the next level, the file is split into lines. Each line is classified as a supported format or unknown. Supported lines become event objects. Event rules examine path or message content; correlation rules group relevant events by source IP. Findings feed a category set for each source, which feeds the risk-score calculation. The dashboard consumes this final analysis object and creates a readable table-based view.',
        'The DFD is conceptual: it illustrates movement of data rather than implementation classes. The actual project keeps this flow in the analyzer module and exposes it through a small server module.'
    ], figure=(['Evaluator', 'Local log file', 'SentinelTrace analysis', 'Findings and risk summary'], '3.2', 'Conceptual data flow for local log analysis'))
    logical_page(document, '3.4.2 Conceptual Data Model and UML View', [
        'The implementation uses Python dictionaries and lists rather than a persistent relational database. Nevertheless, its conceptual entities are clear. An Event describes one parsed record. A Finding links one or more events to a named detection category. An IP summary groups unique categories and contributes a bounded risk score. An Analysis result contains the source information, counters, findings and summary collections returned to the interface.',
        'This lightweight model reduces setup overhead while keeping responsibilities distinct. It also makes JSON export straightforward because the in-memory objects already use serializable primitives. The model does not include user accounts, storage tables or incident tickets because those features fall outside the local proof-of-concept scope.',
        'A future production design could map these entities to a database with retention and access-control policies. The present model is sufficient for reproducible test data and clear dashboard output.'
    ], figure=(['Event\nsource, IP, raw line', 'Finding\ncategory, evidence, mapping', 'IP Summary\nunique categories, risk', 'Analysis\ncounts and collections'], '3.3', 'Conceptual finding model'))
    logical_page(document, '3.5 Technology Stack', [
        'Python was selected because it provides readable string handling, regular expressions, JSON support and a built-in HTTP server in the standard library. These features are sufficient for the project’s fixed local scope. The parser and rule modules use no third-party security library, making it easier for evaluators to understand the implementation and reproduce the environment.',
        'HTML, CSS and browser-side JavaScript provide the dashboard. Their role is presentational: users choose a log file or sample, view the response, and inspect rows of output. The local server is responsible for running the analysis and returning JSON. This client-server separation keeps the rule logic in one trusted backend location.',
        'Git-compatible source organization, sample data, README documentation and unittest cases complete the development environment. The project is not dependent on external services; this is a conscious trade-off that improves classroom portability but limits live integration capabilities.'
    ], table=('Table 3.5 Technology stack', ['Layer', 'Technology', 'Purpose'], [
        ('Analysis', 'Python standard library', 'Parsing, rules, correlation, scoring and JSON generation.'),
        ('Service', 'http.server and local routes', 'Serve interface and expose local analysis endpoints.'),
        ('Interface', 'HTML, CSS and JavaScript', 'Display summary, findings and prioritized sources.'),
        ('Testing', 'unittest', 'Verify scoped detection and resilience behaviour.'),
        ('Data', 'Plain-text sample log', 'Reproducible demonstration input.'),
    ], [1.2, 2.0, 3.3]))

    # Chapter 4
    logical_page(document, '4.1 Implementation Overview', [
        'The SentinelTrace repository is organized so that an evaluator can move from launch command to source logic without searching through unrelated files. The run script starts the local server. The analyzer module coordinates ingestion, parsing, detection and risk aggregation. The rules module centralizes rule definitions and detection text. The server module exposes local HTTP endpoints. The web folder contains the browser interface, and the tests folder contains reproducible unit cases.',
        'This organization supports traceability from report to code. A statement about a detection category can be checked in the rule module. A statement about the risk score can be checked in the analyzer. A statement about browser interaction can be checked in the web file. The report therefore describes implementation decisions rather than merely listing tools.',
        'The following pages explain the modules in their execution order. Snippets are shortened for explanation; the complete evaluated source remains in the separate project-code folder and repository package.'
    ], figure=(['run.py', 'server.py', 'analyzer.py', 'rules.py', 'web/index.html'], '4.1', 'Module interaction flow'), label='CHAPTER 4 IMPLEMENTATION')
    logical_page(document, '4.1.1 Input Ingestion and Parser Dispatch', [
        'The ingestion stage opens the chosen text file and processes it line by line. This approach is more appropriate than loading a whole file into a single string because it mirrors how logs are naturally structured and keeps the parser responsible for one record at a time. The original line is retained in the event record so later findings can show evidence without reconstructing it.',
        'Parser dispatch first checks whether a line resembles an Apache-style access entry or an SSH password authentication message. The source category is stored separately. This distinction is important because an IP address in an access record may accompany a requested path, while an SSH event is meaningful in the context of failed or accepted credentials. Treating both formats as unstructured keyword text would make later rules less reliable.',
        'Lines that match neither format are not forced into a misleading structure. They remain part of the total input count but do not generate a false finding. The corresponding unit test confirms that an unknown line never causes the analysis to crash.'
    ])
    logical_page(document, '4.1.2 Event Normalization', [
        'Normalization creates a common event shape even though the original sources differ. The event contains a source label, source IP where available, raw line, parsed fields and contextual attributes such as request path or SSH success/failure state. A normalized shape lets rule functions receive predictable inputs, reducing repeated format-specific code.',
        'The process preserves meaning rather than aggressively transforming it. For example, URL decoding is used where necessary for traversal inspection, but the original path and source line remain available as evidence. This balance helps detect an encoded representation while allowing a reviewer to see exactly what appeared in the input.',
        'The normalizer also establishes a boundary for future support. Adding another log format would mean writing a new parser that returns the same event contract. Existing risk scoring and dashboard code could remain unchanged as long as the new parser supplies the required fields.'
    ])
    logical_page(document, '4.1.3 Rule Engine', [
        'The rule engine uses named, readable checks rather than an opaque aggregate classifier. Each rule returns enough information to construct a finding: category, severity, confidence, evidence, selected MITRE ATT&CK reference and remediation recommendation. Named rules make review practical because a test case can target one rule and the dashboard can show a precise explanation.',
        'Rules are separated into event-level and correlation-level logic. Path traversal, SQL injection, command injection and scanning can be evaluated from an access event. SSH brute force and login after failures need history across several events from the same source address. The analyzer collects this history before applying the correlation rule.',
        'The rule set is intentionally conservative in scope. It flags observable indicators rather than proving exploitation. For example, a SQL-related token is reported as an indicator requiring review, not as proof that a database was compromised.'
    ], table=('Table 4.1 Detection-rule catalogue', ['Category', 'Observed indicator', 'Risk weight'], [
        ('SSH brute force', 'Repeated failed password messages from one IP.', '35'),
        ('Login after failures', 'Successful SSH password login following repeated failures.', '45'),
        ('Path traversal', 'Plain or URL-decoded traversal sequence.', '25'),
        ('SQL injection indicator', 'Suspicious SQL-like token pattern in a request.', '25'),
        ('Command injection indicator', 'Shell-separator or command-like sequence in a request.', '35'),
        ('Web scanning', 'Request for a common sensitive or probing path.', '15'),
    ], [1.55, 3.85, 1.1]))
    logical_page(document, '4.1.4 SSH Brute Force and Follow-On Login Detection', [
        'SSH password failures are gathered by source IP. When a threshold of repeated failed attempts is observed, the system creates an SSH brute-force finding. The result records the implicated address and representative evidence so the reviewer can check the source messages. The rule is a triage signal, not an assertion that each failed attempt was malicious; configuration errors and legitimate users can also generate failures.',
        'A second correlation rule checks for a successful password authentication after a sequence of failures from the same source. This is assigned a higher category weight because it is more concerning than failures alone. The finding is intended to prompt review of account activity, source legitimacy and credential hygiene rather than to conclude compromise automatically.',
        'The demonstration data contains both conditions for 203.0.113.45. The two distinct categories contribute 35 and 45 points, producing the documented capped score of 80. A unit test checks this calculation directly, which is more defensible than relying on a visual dashboard assertion.'
    ])
    logical_page(document, '4.1.5 Web Request Detection', [
        'The access-log rules focus on strings that are commonly suspicious in request paths. Path traversal detection inspects raw and decoded paths so a URL-encoded representation cannot trivially bypass a simple dot-dot-slash check. The implemented test specifically verifies detection of a double-encoded traversal style in the supported sample context.',
        'The SQL injection and command injection rules look for indicator patterns, not a comprehensive grammar of malicious payloads. Their purpose is to surface requests that deserve manual review. Severity and confidence describe the strength of the rule’s alerting posture; they do not transform a textual pattern into forensic proof.',
        'Web scanning detects requests for selected sensitive, administrative or reconnaissance-oriented paths. Alone, such a request receives a modest contribution. When it appears from an address that also triggers traversal, the aggregated category score gives the reviewer a reason to inspect that source before isolated low-risk traffic.'
    ])
    logical_page(document, '4.1.6 Risk Scoring and Prioritization', [
        'SentinelTrace computes priority per source IP address. It first determines which distinct rule categories have been triggered by that source. It then sums the fixed category weights and caps the result at 100. The use of distinct categories avoids assigning an unlimited score merely because a log contains a large number of repeated copies of the same message.',
        'The score is accompanied by severity labels: critical at 75 or above, high at 50 or above, medium at 25 or above, and lower otherwise. The label is a sorting aid. It must be read with the evidence, source context and rule categories, because two sources with the same numeric score could have different operational implications.',
        'This algorithm is appropriate for an educational prototype because every term can be shown in the report and source code. A production system might introduce time windows, asset importance, threat intelligence, user context and confidence calibration. Those enhancements are future work, not hidden assumptions in the current score.'
    ], figure=(['Normalized findings', 'Unique categories per IP', 'Fixed weights', 'Cap at 100', 'Severity label and ranking'], '4.2', 'Detection and prioritization pipeline'))
    logical_page(document, '4.1.7 Local Dashboard', [
        'The dashboard provides a browser-based way to run the same analyzer used by tests. It offers a practical evaluation flow: start the local server, open the loopback address, select sample or uploaded input, and inspect summary cards, ranked IP entries and detailed findings. Each display element is backed by the structured response rather than a manually typed demonstration screenshot.',
        'The interface is deliberately restrained. It does not attempt to reproduce an enterprise SOC console. Instead, it makes the analysis result readable at a glance and keeps enough detail available for a viva or code walkthrough. The user can see the risk score, triggered categories, severity, confidence, evidence and recommended next action without consulting a separate rule manual.',
        'Binding the service to 127.0.0.1 keeps the evaluation interface local to the machine. This reduces accidental exposure of log content on a network. It should not be interpreted as a substitute for application authentication or encrypted transport in a multi-user environment.'
    ])
    logical_page(document, '4.1.8 JSON Export and Analyst Workflow', [
        'The analysis response can be exported as JSON. This format is useful because it preserves the same machine-readable evidence shown by the dashboard and can be inspected with any text editor or passed to a later integration. The export includes summary information, parser counters, finding records and prioritized IP information.',
        'An intended analyst workflow is simple: analyze the log, begin with the highest-ranked IP, read the categories and preserved raw evidence, validate whether the source should be expected, apply the corresponding recommendation, and retain the exported result with the case notes. This workflow is intentionally human-in-the-loop; the prototype offers prioritization, not automated blocking.',
        'By providing both visual and JSON outputs, the project supports two evaluation styles. A college evaluator can use the dashboard in a demonstration, while a technical reviewer can inspect the response structure and compare it against unit-test expectations.'
    ])
    logical_page(document, '4.2 Key Algorithms', [
        'The primary algorithm is a deterministic pipeline. It reads each line, attempts parser classification, stores the resulting event, applies event rules, groups SSH events by IP, applies correlation rules, aggregates category weights, and returns a stable analysis object. Determinism matters because the same file should produce the same result during code review and testing.',
        'The algorithm favours clarity over premature optimisation. In the supplied scope, simple lists and dictionaries are sufficient. The source carries no hidden training state and no remote lookup, so the analysis remains reproducible offline. The score cap and category de-duplication are explicit business rules, not incidental side effects of data structure behaviour.',
        'The pseudo-code below summarizes the control flow used by the analyzer. It is not a replacement for the source; it is included to make the implementation reasoning easy to follow during the evaluation.'
    ], table=('Algorithm 4.1 High-level analysis procedure', ['Step', 'Pseudo-code action'], [
        ('1', 'For each input line, preserve raw text and attempt supported parser classification.'),
        ('2', 'For each normalized event, run applicable event-level detection rules.'),
        ('3', 'Group SSH authentication events by source IP and evaluate correlation rules.'),
        ('4', 'For each IP, sum weights of distinct triggered categories and cap at 100.'),
        ('5', 'Return summary, findings, ranked IP list and parser statistics.'),
    ], [0.6, 5.9]))
    logical_page(document, '4.3 Selected Code Explanations', [
        'The following compact excerpts describe the intent of the production code without reproducing the complete source listing. The first condition shows why input handling is defensive: unknown records do not throw an exception merely because they do not match a supported parser. The second illustrates the score design: the calculation works from distinct categories so an attacker cannot inflate or hide priority through simple repetition alone.',
        'During evaluation, the reviewer can locate the full implementation in src/sentineltrace. The source has deliberately small functions and descriptive names, which makes it suitable for a fourth-year code viva. Test names also state the expected behaviour in plain language, providing a useful map between requirements and verification.'
    ], table=('Code excerpt 4.1 Defensive analysis concept', ['Illustrative logic'], [
        ('event = parse_line(raw_line)\nif event is None:\n    unknown_count += 1\n    continue\nfindings.extend(apply_event_rules(event))',),
        ('categories = unique_categories_for(ip_address)\nrisk = min(100, sum(RULE_WEIGHTS[c] for c in categories))\nseverity = label_for(risk)',),
    ], [6.5], 9))
    logical_page(document, '4.4 Engineering and Security Considerations', [
        'Secure software engineering for a log tool includes more than detection patterns. Input should be treated as untrusted text. SentinelTrace avoids executing content from log lines, uses local file processing, and serializes structured output. The UI displays analysis values as data rather than interpreting requests as commands. These constraints reduce the risk that a malicious log line changes the tool’s control flow.',
        'The project also documents its boundaries. It does not contain real credentials, external tokens or hard-coded cloud keys. It does not promise to sanitize a hostile file for every possible web-view context, and it does not expose the dashboard to a network. Such limits are useful to state because an academic project is often evaluated as much on responsible scope control as on feature count.',
        'Code quality is reinforced by a compact test suite. Each security-relevant rule has a testable narrative: a benign line should not create a finding, a malformed line should not stop the run, encoded traversal should be recognised, and the documented SSH sequence should calculate the stated score.'
    ])

    # Chapter 5
    logical_page(document, '5.1 Testing Strategy', [
        'Testing was planned around requirements rather than only user-interface appearance. The analyzer can be invoked without starting a browser, which enables fast deterministic unit tests. The test suite uses a controlled demonstration log so each expected category and score has a known cause. This is more suitable for a mini-project evaluation than attempting to label an uncontrolled external traffic dataset.',
        'The testing strategy has three levels. Unit tests check isolated parser, detector and scoring behaviour. Integration checks run the complete analyzer on the sample log and verify the combined category set. Manual interface checks confirm that the local dashboard presents the returned information in an understandable form. JSON export can be checked against the same structured response.',
        'The strategy intentionally distinguishes detection coverage from real-world accuracy. Six passing unit tests demonstrate that the implemented rules behave as designed for the supplied cases. They do not establish a statistically valid false-positive or false-negative rate over production traffic.'
    ], figure=(['Requirements', 'Unit tests', 'Integrated sample run', 'Manual dashboard review', 'Documented evidence'], '5.1', 'Test execution workflow'), label='CHAPTER 5 TESTING')
    logical_page(document, '5.1.1 Test Environment and Dataset', [
        'The test environment is the local SentinelTrace project directory with Python unittest. The supplied sample_data/demo.log contains a compact mixture of Apache-style requests and SSH authentication records. It was designed to produce identifiable examples of all six documented categories while retaining a few benign or unsupported cases for negative testing.',
        'Controlled synthetic data is appropriate here because the purpose is reproducibility. A reviewer can open the file, inspect each line and understand why a rule should or should not match. It also avoids presenting sensitive production logs in an academic report. The limitation is clear: synthetic cases cannot represent the full variation, volume and ambiguity of real organizational traffic.',
        'The current automated suite contains six tests. The command used for verification is python3 -m unittest discover -s tests -v from the project root. The observed result for the completed project is six tests run and all passing.'
    ])
    logical_page(document, '5.2 Unit-Test Coverage', [
        'The first test verifies that an ordinary benign access line does not create a finding. This negative case prevents the report from focusing only on attacks and demonstrates that the detector does not flag every request. A second test verifies that the demonstration file triggers the complete documented category set, connecting the project requirements to its sample data.',
        'A third test verifies the transparent risk result for the SSH sequence from 203.0.113.45. It checks that repeated failed logins and a later successful login generate the expected priority. Additional tests verify that the parser preserves distinct source categories, unknown input is handled safely, and a URL-encoded traversal sequence is detected.',
        'Taken together, the tests exercise normal handling, negative handling, parsing separation, encoding awareness, correlation behaviour and scoring. They are intentionally small and readable so that a viva evaluator can understand what each assertion proves.'
    ], table=('Table 5.1 Automated unit tests', ['Test', 'Expected result'], [
        ('Benign access line', 'No finding is created.'),
        ('Demonstration categories', 'All six documented categories are present.'),
        ('SSH login burst', '203.0.113.45 receives transparent risk score 80.'),
        ('Parser sources', 'Apache and SSH source categories remain distinct.'),
        ('Unknown line', 'Analysis continues without a crash.'),
        ('Encoded traversal', 'URL-encoded traversal is detected.'),
    ], [2.2, 4.3]))
    logical_page(document, '5.2.1 Functional Test Cases', [
        'Functional cases use the full analysis path, not individual helper functions alone. They begin with an input line or sequence, execute parsing and detection, and compare the observable result to the rule catalogue. The expected results use cautious language: an indicator is expected to be surfaced for review, not a compromise verdict.',
        'The cases below are suitable for an evaluation demonstration because they connect input, rule category and expected response. The same concepts can be extended with additional safe test fixtures as the rule set grows. Any newly added rule should be accompanied by a positive case, a negative case and, where relevant, an evasion or encoding case.'
    ], table=('Table 5.2 Functional test cases', ['ID', 'Input condition', 'Expected output'], [
        ('TC01', 'Repeated SSH password failures from one IP.', 'SSH brute-force finding with preserved evidence.'),
        ('TC02', 'SSH success after repeated failures.', 'Login-after-failures finding and high priority contribution.'),
        ('TC03', 'Request contains decoded traversal sequence.', 'Path-traversal indicator with mitigation advice.'),
        ('TC04', 'Request contains SQL-like token pattern.', 'SQL injection indicator requiring review.'),
        ('TC05', 'Request contains shell-separator pattern.', 'Command injection indicator requiring review.'),
        ('TC06', 'Probe for sensitive/common scan path.', 'Web-scanning finding with lower contribution.'),
    ], [0.6, 3.0, 2.9]))
    logical_page(document, '5.2.2 Resilience and Negative Testing', [
        'A security parser should not become unavailable because a record is incomplete or unfamiliar. SentinelTrace therefore includes an unknown-line test. The analyzer keeps a count for the input and safely excludes an unsupported line from rule evaluation. This design makes it easier to analyze mixed files where only some records belong to supported sources.',
        'Negative testing also includes a benign access line. This case matters because simplistic token matching can create alert fatigue. The project does not claim that the rule set has no false positives; rather, it demonstrates that the supplied benign record remains unflagged and establishes a test pattern for future tuning.',
        'Encoding is another resilience concern. Attackers and ordinary clients can express path characters in encoded forms. The explicit encoded traversal test verifies that the parser and rule path handle this selected representation. A production system would require a broader canonicalization policy and careful testing to avoid over-decoding or inconsistent interpretation.'
    ])
    logical_page(document, '5.3 Sample Input', [
        'The sample log contains a short sequence of web and SSH records. An evaluator can point the dashboard to the included demo file or invoke the analyzer through the tests. The important property of the sample is traceability: each designed indicator can be located in a raw line and linked to one expected category. The tool never requires the evaluator to trust an unobservable external feed.',
        'For example, the SSH section includes repeated password failures from 203.0.113.45 followed by a successful password authentication. The web section contains suspicious request patterns from other example addresses. These addresses are documentation-only ranges used in the sample and do not represent live hosts.',
        'The report does not reproduce an entire log file because the complete source is kept separately. The following abbreviated examples illustrate the formats used in the input and the kind of evidence that appears in a finding.'
    ], table=('Sample input 5.1 Abbreviated log evidence', ['Source', 'Example evidence'], [
        ('SSH', 'Failed password for invalid user admin from 203.0.113.45 port 22 ssh2'),
        ('SSH', 'Accepted password for demo from 203.0.113.45 port 22 ssh2'),
        ('Apache', 'GET /..%252f..%252fetc/passwd HTTP/1.1'),
        ('Apache', 'GET /search?q=1%27%20OR%20%271%27=%271 HTTP/1.1'),
    ], [1.1, 5.4]))
    logical_page(document, '5.3.1 Sample Output', [
        'The primary output is a structured analysis. At summary level, the supplied demonstration produces 13 parsed events, six findings and four source IP entries. The dashboard then presents findings and prioritization. At source level, 203.0.113.45 is the most concerning example because it contains two high-value distinct SSH categories: repeated failures and a successful follow-on login.',
        'Other IP addresses demonstrate the web rules. The report treats these outputs as expected results of the controlled sample, not as performance statistics. A reviewer can compare them with raw evidence and the test suite. JSON export contains the same fields, permitting an external verifier to inspect output without relying on the browser layout.',
        'This result format makes it possible to discuss a rule outcome with precision. Instead of saying only “attack detected,” an evaluator can state which source triggered which category, why it was ranked as shown, and which next action the tool recommends.'
    ], table=('Table 5.3 Expected sample analysis summary', ['Measure', 'Expected value'], [
        ('Parsed events', '13'),
        ('Findings', '6'),
        ('Prioritized source IP entries', '4'),
        ('Highest-risk source', '203.0.113.45 with risk 80'),
        ('Rule categories covered', '6'),
    ], [2.7, 3.8]))
    logical_page(document, '5.4 Test Results', [
        'The completed verification run executed six automated tests and reported all as passing. The result confirms the contract of the present code and sample: benign traffic is not automatically flagged, documented categories are produced, score composition is transparent, parser sources are separated, malformed input is safe, and encoded traversal is recognized.',
        'The result does not prove broad security effectiveness. No external benchmark dataset, red-team exercise or measured high-volume load test has been performed as part of this mini project. This distinction protects the credibility of the report. The implemented test evidence is strong for deterministic feature verification and limited for claims about operational detection rates.',
        'For future iterations, testing can expand with parameterized fixtures, more benign traffic, adversarial encodings, false-positive review, load experiments and regression tests for every new rule. The current suite provides a clean starting baseline.'
    ])

    # Chapter 6
    logical_page(document, '6.1 Results Overview', [
        'The demonstration analysis converts a compact mixed log into a small, ranked set of investigation leads. Six findings are produced across the supported categories, and the IP summary makes their relationship visible. This is a meaningful improvement over reading the same lines manually because the user can begin with the source that combines repeated failed SSH activity and a later successful authentication.',
        'The result is explainable at three levels. The category tells the reviewer what behaviour matched. The raw evidence shows the source record. The risk score explains why the source appears in a particular order. The recommendation supplies a next step such as reviewing authentication records, validating a source address, checking application input handling or restricting exposed administrative paths.',
        'The system therefore meets its stated educational aim: it demonstrates local, rule-based threat triage with an explicit evidence chain. It does not attempt to present a generic alert count as a complete security posture.'
    ], figure=(['6 findings', '4 source IPs', 'Evidence-led rules', 'Bounded risk ranking', 'Human review'], '6.1', 'Demonstration finding distribution'), label='CHAPTER 6 RESULTS AND DISCUSSION')
    logical_page(document, '6.1.1 Finding Coverage', [
        'The sample covers six categories selected because they are observable in the two supported sources. The SSH categories demonstrate temporal correlation. The web categories demonstrate path and token inspection. The coverage is intentionally breadth-limited rather than claiming exhaustive IDS capability. This makes the code and test set manageable while still showing several common web and authentication concerns.',
        'A useful feature of the result is that category names are not merely labels; they correspond to documented rule logic. Path traversal includes decoding awareness. Scanner probes have a lower weight because they can occur before a successful attack. Command-injection and SQL-injection rules indicate potentially dangerous request syntax but require application and server context before any incident conclusion.',
        'For a viva, the evaluator can open the sample log, identify one event per category, run the tool, and explain the relation between that line, the finding details and the associated mitigation. This is a stronger demonstration than showing static screenshots without reproducible input.'
    ], table=('Table 6.1 Demonstration results by source', ['Source IP', 'Triggered categories', 'Risk score'], [
        ('203.0.113.45', 'SSH brute force; login after failures', '80'),
        ('198.51.100.27', 'Path traversal; web scanning', '40'),
        ('Example command source', 'Command injection indicator', '35'),
        ('Example SQL source', 'SQL injection indicator', '25'),
    ], [1.45, 3.75, 1.3]))
    logical_page(document, '6.2 Risk-Prioritization Analysis', [
        'The most important result is not the raw number of log lines but the prioritized source order. For 203.0.113.45, the system records two distinct SSH categories. The score is 35 for brute-force evidence plus 45 for a successful login after failures, producing 80. The high weight of the follow-on success reflects the need to investigate whether credentials were guessed, reused or otherwise compromised.',
        'For the web example, path traversal and scanning combine to 40. This is below the SSH example because the selected web patterns do not show a confirmed successful action in the sample. The score communicates relative triage priority, not severity of a proven breach. A reviewer should still inspect the request, web-server response and affected application route.',
        'This category-based approach is easy to explain and avoids a common problem with event-count scores. A source that repeats one low-confidence pattern many times does not automatically exceed a source that exhibits several different concerning behaviours. The trade-off is that time and volume carry less nuance; these are listed as future improvements.'
    ])
    logical_page(document, '6.2.1 Explainability of Results', [
        'Explainability is assessed qualitatively through the availability of information needed for review. Each finding contains a category, severity, confidence, raw evidence, a selected ATT&CK mapping and a recommended action. The analyst does not need to guess which rule caused the alert or search through an unrelated log archive to find the original text.',
        'The risk score is likewise explainable because the report gives the category weights and thresholds. An evaluator can calculate 80 for the SSH sequence manually. If a weight appears inappropriate, it can be changed in a documented configuration or rule source, then verified with a regression test. This is more auditable than an unexplained probability number.',
        'Explainability does not guarantee correctness. A transparent rule can still be too broad or too narrow. Its value is that the limitation is visible and can be discussed. For a student project, this honest reasoning is preferable to overstating intelligent behaviour that has not been evaluated.'
    ])
    logical_page(document, '6.2.2 Performance and Accuracy Considerations', [
        'No statistical accuracy percentage is claimed because the project does not include a labelled, representative real-world dataset. Similarly, no throughput benchmark is claimed because the implemented evaluation focuses on a small local sample. Presenting either figure without the necessary methodology would be misleading.',
        'What has been verified is deterministic rule behaviour on selected input cases. Six automated tests pass, the sample produces the documented categories, and the risk calculation is reproducible. These are valid project results, but they should be described as functional verification rather than operational detection accuracy.',
        'A later performance study could measure events per second across files of controlled size and compare memory usage. An accuracy study could use a labelled corpus with separate training/tuning and test partitions, report false-positive and false-negative counts per rule, and document the effect of URL decoding and rule thresholds. Those evaluations are outside the current scope.'
    ])
    logical_page(document, '6.3 Discussion', [
        'The project demonstrates that a small codebase can provide more useful security context than a plain keyword search. The main contribution is the combination of parser separation, evidence retention, selected rule categories and per-IP prioritization. These elements turn a few raw strings into an investigation-oriented output that an evaluator can follow without specialist infrastructure.',
        'There are deliberate trade-offs. A standard-library local service reduces installation complexity but does not offer the scalability of a message-driven platform. Explainable rules simplify evaluation but do not capture novel attacks automatically. The sample dataset produces a reliable demonstration but cannot establish performance in a noisy production environment.',
        'Within its stated limits, SentinelTrace is an appropriate fourth-year mini project because it includes a problem definition, security mapping, architecture, working implementation, testable rule logic, browser interface, exportable result and a clear future roadmap. The project is strengthened by documenting what it does not yet do.'
    ])
    logical_page(document, '6.3.1 Operational Interpretation', [
        'An analyst should interpret the dashboard as a queue for validation. A high-ranked source should lead to review of the raw record, server response, authentication history and environmental context. The output recommendation can guide that next check, but it should not trigger automatic blocking without local policy and additional evidence.',
        'For the SSH demonstration, suitable follow-up includes confirming whether the address is expected, reviewing the account involved, checking nearby authentication events and considering password or key-based access controls. For a traversal or injection indicator, suitable follow-up includes reviewing application logs, response codes, affected routes and secure coding controls.',
        'This human-review posture is important for ethical and practical use. The tool reduces the time needed to find suspicious evidence; it does not replace an incident-response procedure or guarantee that a pattern is malicious.'
    ])

    # Chapter 7
    logical_page(document, '7.1 Conclusion', [
        'SentinelTrace delivers a working local prototype for explainable log-based threat triage. It reads two scoped log-source styles, normalizes supported records, detects six documented categories, correlates selected SSH behaviour, calculates a transparent per-IP risk score, and presents results in a local browser dashboard with JSON export. The design keeps raw evidence and response guidance attached to each finding.',
        'The project met its core objectives through an implemented and tested workflow rather than a conceptual-only design. The supplied demonstration produces six findings across four source addresses, and six automated tests pass. The source structure, sample data and report make the system suitable for a fourth-year evaluation, code walkthrough and viva explanation.',
        'Most importantly, the project treats detection as decision support. It helps a reviewer prioritize what to inspect, explains why the item was surfaced, and acknowledges that a rule match is not proof of compromise. This balance makes the project technically credible and academically defensible.'
    ], label='CHAPTER 7 CONCLUSION AND FUTURE SCOPE')
    logical_page(document, '7.2 Limitations', [
        'The current implementation supports only selected Apache-style access lines and SSH password authentication messages. Other log formats, structured JSON records, Windows events, DNS telemetry and endpoint data are outside scope. The local analyzer reads a file rather than continuously consuming a live stream, and it has no persistent storage or multi-user access control.',
        'Detection is rule-based. It can miss novel payloads or unusual encodings and can flag benign activity that resembles a rule pattern. The score uses fixed weights and does not account for time windows, asset criticality, business context, threat intelligence or analyst feedback. The project has functional tests but no labelled real-world accuracy study or load benchmark.',
        'These are not hidden deficiencies; they are boundaries of the mini-project scope. Stating them helps future work target meaningful improvements and prevents the tool from being represented as a complete SIEM or intrusion-prevention platform.'
    ])
    logical_page(document, '7.3 Future Scope', [
        'The most direct extension is broader ingestion. New parser adapters could accept additional web formats, operating-system events, firewall records and structured JSON logs while returning the existing event contract. Live tailing or a message-queue adapter could replace manual file selection for a continuous monitoring mode.',
        'The rule engine can also be strengthened with configuration files, time windows, allow-lists, normalized URL canonicalization and more systematic detection content. A future score could combine category weights with recency, asset importance and confidence while preserving a clear explanation of every contribution. Threat-intelligence enrichment should be optional and carefully governed because it introduces privacy, availability and data-quality considerations.',
        'For deployment, a mature version would require authentication, secure transport, role-based access, storage retention, audit logging, test fixtures from representative data and an incident-response workflow. Any machine-learning addition should be evaluated against labelled data and presented with explanations, not used as a substitute for evidence.'
    ])
    logical_page(document, '7.4 Learning Outcomes', [
        'This project connects several fourth-year cybersecurity skills in one implementable artefact: reading logs, identifying attack indicators, using ATT&CK vocabulary, designing deterministic detection logic, preserving evidence, building a small web interface, writing automated tests and documenting limits responsibly. It also demonstrates that security engineering benefits from modularity: parser, rule, scoring and presentation responsibilities can be reviewed independently.',
        'The work reinforces a practical lesson about security analytics. Alerting is useful when it is traceable and actionable. A system that merely emits a high-risk label leaves the analyst with unanswered questions. SentinelTrace instead exposes its rule category, evidence and recommended next check, allowing an evaluator to reason about the output rather than accept it blindly.',
        'The completed prototype provides a foundation for a larger final-year project or research extension. Its codebase is small enough to understand, yet structured enough to accept additional sources, rules, tests and operational safeguards.'
    ])
    logical_page(document, '7.5 Demonstration Readiness', [
        'A project evaluation should demonstrate a repeatable sequence rather than depend on a manually prepared screen. SentinelTrace supports that sequence through its separate sample log, compact run entry point, local browser interface and automated tests. The evaluator can begin with the tests, inspect the source tree, run the local service, analyze the sample and compare the displayed findings with the raw evidence.',
        'The demonstration is intentionally arranged from verification to interpretation. First, the unit-test output establishes that the implemented rules satisfy the selected fixtures. Next, the dashboard makes the same logic accessible for a visual walkthrough. Finally, the JSON export shows that the result is structured data rather than only a presentation layer. This order helps answer both code-oriented and user-interface-oriented evaluation questions.',
        'The project should be shown on a local machine with the source code and sample data visible. No Internet connection, external API key or confidential production log is needed. This reduces the risk of a failed demonstration caused by unavailable services and keeps the security discussion grounded in reproducible input.'
    ], table=('Table 7.1 Suggested evaluation flow', ['Stage', 'Evidence to show'], [
        ('1. Verification', 'Six unittest checks pass from the project root.'),
        ('2. Input review', 'Open the controlled demo.log file and identify a suspicious sequence.'),
        ('3. Analysis', 'Run the local dashboard and inspect ranked findings.'),
        ('4. Explanation', 'Calculate the 80 risk score from its two documented categories.'),
        ('5. Output', 'Export JSON and show evidence/recommendation fields.'),
    ], [1.6, 4.9]))
    logical_page(document, '7.6 Ethical and Responsible Use', [
        'A log-triage application influences where a reviewer spends attention, so its output must be used responsibly. A rule match is an indicator for investigation, not proof that a person or machine acted maliciously. The report consistently uses cautious language for this reason. Incorrectly treating a pattern match as a verdict could lead to unnecessary blocking, privacy harm or poor incident decisions.',
        'The local and sample-based design also limits unnecessary exposure of sensitive information. The demonstration uses documentation address ranges and synthetic log content rather than real personal data. In a real deployment, logs may contain user identifiers, IP addresses, request parameters and security events, so access control, minimization, retention policy and incident-handling approval would be required.',
        'Responsible future work should retain the explainability principle. Even if a later version adds statistical models or threat-intelligence enrichment, a reviewer should be able to understand what data was used, why a result was elevated, and what uncertainty remains. This practice makes security automation more accountable.'
    ])
    logical_page(document, '7.7 Rule-Tuning Method', [
        'Rule tuning should be evidence-driven. When a rule creates a false positive, the correct response is not simply to silence the category globally. The reviewer should retain a safe fixture representing the benign condition, identify which predicate was over-broad, refine the condition or threshold, and add a regression test that proves both the benign fixture and the malicious fixture behave as intended.',
        'The current codebase supports this workflow because rules are named and tests are independent of the dashboard. For example, encoded traversal is covered by an explicit test. A future refinement can add adjacent encodings or benign URL cases without changing the scoring or display components. This makes tuning a controlled engineering activity rather than trial-and-error interaction with a production console.',
        'A future rule configuration file could expose selected weights and allow-lists while preserving safe defaults. Any configurable choice should still be logged in the analysis output so a reviewer knows which version of the rule logic produced a finding. Reproducible configuration is as important as reproducible code.'
    ], table=('Table 7.2 Rule-tuning discipline', ['Step', 'Purpose'], [
        ('Capture', 'Keep a minimal safe fixture for the observed condition.'),
        ('Classify', 'Decide whether the condition is expected, benign or suspicious.'),
        ('Refine', 'Adjust the narrowly responsible parser or rule predicate.'),
        ('Verify', 'Run positive, negative and encoding-aware tests.'),
        ('Document', 'Record the rationale, weight change and residual limitation.'),
    ], [1.5, 5.0]))
    logical_page(document, '7.8 Data Governance Considerations', [
        'Although the prototype processes local files, security logs should be treated as sensitive operational data. They can reveal infrastructure addresses, account names, request parameters, software paths and the timing of security events. Before moving from sample data to organizational data, a deployment should define who can upload logs, who can view findings, how exports are stored, and when records are deleted.',
        'Data minimization is especially relevant to web-request content. A request path or query string may contain identifiers that are unnecessary for a broad dashboard view but relevant to an investigator. A mature interface could show redacted summaries by default and make full evidence available only to authorized reviewers. Retention should reflect institutional policy and incident-response needs.',
        'SentinelTrace does not claim to implement these governance controls. The value of including them in the report is to show that a cybersecurity project is not complete merely because a detector works. Secure handling of the evidence is part of the problem that a production extension must solve.'
    ])
    logical_page(document, '7.9 Deployment Roadmap', [
        'The prototype can evolve in deliberate stages. The first stage is local evaluation with sample data and the current standard-library server. The second stage is controlled departmental use with more parsers, configuration, a protected storage layer and basic access control. The third stage is an operational service with secure log transport, user roles, monitoring, backups and reviewed alerting procedures.',
        'Each stage should preserve the current strengths: evidence retention, explainable rules, bounded scoring and automated tests. Features should not be added solely to increase the apparent complexity of the project. For example, a database is useful only when it supports a concrete requirement such as audit retention or investigation history; a machine-learning component is useful only when it is evaluated and its outputs can be explained.',
        'This staged view gives the project a realistic future path without pretending that the classroom version already satisfies enterprise operational requirements. It also helps an evaluator see how the present modular design can support later work.'
    ], figure=(['Local sample analysis', 'Controlled pilot', 'Protected storage and roles', 'Operational integration'], '7.1', 'Phased SentinelTrace deployment roadmap'))
    logical_page(document, '7.10 Reproducibility and Project Packaging', [
        'A fourth-year project should be possible to evaluate without reconstructing undocumented decisions. SentinelTrace is packaged with source modules, a launcher, web assets, sample data, tests, documentation and this report. The appendix provides a code inventory and a short demonstration checklist. Together, these artefacts allow a reviewer to identify what is claimed, where it is implemented and how it was verified.',
        'Reproducibility is strengthened by avoiding hidden dependencies. The project relies on the Python standard library and local files. The test command is explicit. The sample demonstrates the same categories described in the report. These choices make the project easier to hand over to a faculty evaluator or to continue in a later semester.',
        'For formal submission, the report document and the code folder should remain separate, as requested. The student should fill the remaining identity and approval fields, attach the institutional similarity result, export the final Word document to PDF if required by the college, and submit the code archive or repository link alongside it.'
    ])
    logical_page(document, '7.11 Security Review Checklist', [
        'A compact security review checklist can help maintain the prototype as it grows. The checks should cover input handling, rule behaviour, output safety, deployment exposure and data governance. A new feature that introduces a network listener, storage layer or third-party dependency should be reviewed before it is treated as part of the security solution.',
        'The current implementation already demonstrates several useful habits: it treats unsupported records defensively, keeps the service local for evaluation, avoids executing log content, retains evidence, documents limitations and uses automated tests for selected security behaviours. These practices are not a complete secure-development lifecycle, but they are a sound starting point for a student project.',
        'Applying the checklist before a demonstration also helps the presenter explain why particular scope decisions were made. It turns questions about missing enterprise features into a reasoned discussion of project boundaries and next steps.'
    ], table=('Table 7.3 Mini-project security review checklist', ['Area', 'Review question'], [
        ('Input', 'Can malformed or unsupported lines be handled without terminating analysis?'),
        ('Detection', 'Does each new rule have positive and negative tests?'),
        ('Output', 'Is evidence shown as data and accompanied by a review recommendation?'),
        ('Exposure', 'Is the service restricted appropriately for the evaluation environment?'),
        ('Data', 'Are sensitive logs, exports and retention handled under an approved policy?'),
    ], [1.4, 5.1]))
    logical_page(document, '7.12 Final Project Summary', [
        'SentinelTrace provides a complete mini-project narrative from cybersecurity problem to evaluated artefact. It does not overstate its detection scope, accuracy or operational readiness. Instead, it offers a transparent prototype whose behaviour can be reviewed from raw log line through parser, rule, finding, score and recommendation. This traceability is the project’s strongest technical contribution.',
        'The completed report, source folder, sample log and tests support multiple evaluation modes: documentation review, code walkthrough, automated verification and live dashboard demonstration. The project is therefore ready for academic assessment after the student completes the remaining personal and institutional fields on the front matter.',
        'Future work can extend sources, correlations, storage and security controls, but the core lesson remains the same: security analytics should make evidence easier to inspect and decisions easier to justify. SentinelTrace establishes that foundation in a form appropriate for a fourth-year cybersecurity mini project.'
    ])
    logical_page(document, '7.13 Evaluation Evidence Matrix', [
        'Academic evaluation is strongest when every project claim can be traced to observable evidence. The following matrix links the stated requirements for SentinelTrace to the artefacts that an evaluator can inspect during a demonstration. It deliberately distinguishes evidence of implementation from claims that would require a much larger operational study, such as enterprise-scale detection accuracy.',
        'The matrix supports a structured viva: the evaluator can begin with a sample event, inspect the parser and rule that create a finding, view the dashboard output, and finally execute the relevant automated test. This sequence demonstrates functional correctness while keeping the limits of the prototype clear and defensible.',
        'Maintaining this evidence trail also makes later improvements safer. A new rule, source or dashboard metric can be added with an explicit requirement, a test case and a documented output expectation. The same approach is appropriate for professional secure-development work, where security claims need reproducible support rather than informal assurance.'
    ], table=('Table 7.4 Evaluation evidence matrix', ['Project claim', 'Evidence available for evaluation'], [
        ('Six security event categories are identified', 'Rule catalogue, sample events and category-wise dashboard findings.'),
        ('Malformed input does not end analysis', 'Parser resilience unit test and unknown-line handling path.'),
        ('Risk labels are transparent', 'Severity mapping, finding rationale and recommended review action.'),
        ('Results are reproducible', 'Documented commands, fixed sample log and six automated checks.'),
        ('Prototype limits are disclosed', 'Scope statement, assumptions, ethics section and future-work plan.'),
    ], [2.35, 4.15]))


def add_references_and_appendix(document):
    add_heading(document, 'REFERENCES', chapter=True)
    references = [
        '[1] K. Kent and M. Souppaya, Guide to Computer Security Log Management, NIST Special Publication 800-92, Sep. 2006.',
        '[2] OWASP Foundation, “Logging Cheat Sheet.” [Online]. Available: https://cheatsheetseries.owasp.org/cheatsheets/Logging_Cheat_Sheet.html. [Accessed: 22-Oct-2026].',
        '[3] MITRE ATT&CK, “Brute Force: Password Guessing, T1110.001.” [Online]. Available: https://attack.mitre.org/techniques/T1110/001/. [Accessed: 22-Oct-2026].',
        '[4] MITRE ATT&CK, “Valid Accounts, T1078.” [Online]. Available: https://attack.mitre.org/techniques/T1078/. [Accessed: 22-Oct-2026].',
        '[5] OWASP Foundation, “SQL Injection Prevention Cheat Sheet.” [Online]. Available: https://cheatsheetseries.owasp.org/cheatsheets/SQL_Injection_Prevention_Cheat_Sheet.html. [Accessed: 22-Oct-2026].',
        '[6] MITRE ATT&CK, “Exploit Public-Facing Application, T1190.” [Online]. Available: https://attack.mitre.org/techniques/T1190/. [Accessed: 22-Oct-2026].',
        '[7] MITRE ATT&CK, “Command and Scripting Interpreter, T1059.” [Online]. Available: https://attack.mitre.org/techniques/T1059/. [Accessed: 22-Oct-2026].',
        '[8] MITRE ATT&CK, “Active Scanning, T1595.” [Online]. Available: https://attack.mitre.org/techniques/T1595/. [Accessed: 22-Oct-2026].',
    ]
    for ref in references:
        add_body(document, ref)
    add_heading(document, 'Reference Traceability', level=2)
    add_body(document, 'The following traceability note clarifies how the cited material informs the report. References are used to frame log-management practice, web-application logging and the selected ATT&CK vocabulary. They are not presented as evidence that SentinelTrace has been certified by, integrated with, or endorsed by any cited organization.')
    add_table(document, ['Reference group', 'Use within this report'], [
        ('NIST SP 800-92 [1]', 'Supports the discussion of log collection, analysis and evidence-aware handling.'),
        ('OWASP logging guidance [2]', 'Informs the discussion of web-request context and useful logging evidence.'),
        ('MITRE T1110.001 and T1078 [3], [4]', 'Provides terminology for password guessing and valid-account related review.'),
        ('OWASP SQL guidance [5]', 'Provides context for handling suspicious SQL-like request indicators.'),
        ('MITRE T1190, T1059 and T1595 [6]–[8]', 'Provides vocabulary for public-facing exploitation, command interpretation and scanning.'),
    ], [2.3, 4.2])
    page_break(document)
    add_heading(document, 'APPENDIX', chapter=True)
    add_heading(document, 'Appendix A Source Code Inventory', level=2)
    add_body(document, 'The complete source code is supplied separately in the SentinelTrace project-code folder for evaluation. The report intentionally provides an inventory rather than duplicating the full program, so that the main body remains focused on design, verification and discussion.')
    add_table(document, ['Path', 'Purpose'], [
        ('run.py', 'Convenience launcher for the local SentinelTrace server.'),
        ('src/sentineltrace/analyzer.py', 'Coordinates parsing, detection, aggregation and risk scoring.'),
        ('src/sentineltrace/rules.py', 'Contains detection categories, weights, evidence and recommendations.'),
        ('src/sentineltrace/server.py', 'Provides local HTTP routes and JSON responses.'),
        ('web/index.html', 'Local browser dashboard.'),
        ('tests/test_analyzer.py', 'Automated verification of scoped behaviour.'),
        ('sample_data/demo.log', 'Controlled demonstration input.'),
    ], [3.1, 3.4])
    page_break(document)
    add_heading(document, 'Appendix B Evaluation Demonstration Steps', level=2)
    for item in [
        'Open the separate SentinelTrace project-code folder in a terminal.',
        'Run python3 -m unittest discover -s tests -v to show the six passing checks.',
        'Run python3 run.py and open the loopback address printed by the server.',
        'Analyze sample_data/demo.log from the dashboard.',
        'Explain the score of 203.0.113.45 from the two SSH categories and show the preserved evidence.',
        'Export JSON and compare the result with the dashboard finding fields.',
    ]:
        add_bullet(document, item)
    add_heading(document, 'Appendix C Report Completion Checklist', level=2)
    for item in [
        'Fill student name, university roll number, semester and guide/coordinator/HOD names on the front pages.',
        'Insert the date of submission after departmental confirmation.',
        'Attach the institutional similarity report after it is generated; do not type an unverified percentage.',
        'If Word prompts to update fields, allow it to refresh page fields before final PDF submission.',
        'Submit this report PDF together with the separate project-code folder or its approved archive/repository link.',
    ]:
        add_bullet(document, item)


def main():
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    copyfile(TEMPLATE, OUTPUT)
    document = Document(OUTPUT)
    base_body_style(document)
    setup_front_matter(document)
    remove_from_paragraph_to_end(document, 'CHAPTER 1: INTRODUCTION')

    # The template's first section spans cover/front matter; its second section begins at Chapter 1.
    # Keep the cover unnumbered and use Roman front matter followed by Arabic chapter pagination.
    document.sections[0].different_first_page_header_footer = True
    for p in document.sections[0].first_page_footer.paragraphs:
        clear_paragraph(p)
    set_page_number_format(document.sections[0], 'lowerRoman', 1)
    set_footer(document.sections[0])
    if len(document.sections) > 1:
        set_page_number_format(document.sections[1], 'decimal', 1)
        set_footer(document.sections[1], 'SentinelTrace Mini Project Report')
    add_update_fields(document)

    build_chapters(document)
    add_references_and_appendix(document)

    # Avoid a trailing forced blank page; retain the last content paragraph.
    document.save(OUTPUT)
    print(OUTPUT)


if __name__ == '__main__':
    main()
