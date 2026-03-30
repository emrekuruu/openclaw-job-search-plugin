from pathlib import Path

def esc(s: str) -> str:
    return s.replace('\\', '\\\\').replace('(', '\\(').replace(')', '\\)')

W, H = 595, 842  # A4 points
left = 42
right = 553
cursor_y = 800
line_h = 12

content = []

def add(cmd):
    content.append(cmd)

def text(x, y, s, font='F1', size=10, color=(0,0,0)):
    r,g,b = color
    add(f"BT /{font} {size} Tf {r:.3f} {g:.3f} {b:.3f} rg 1 0 0 1 {x} {y} Tm ({esc(s)}) Tj ET")

def line(x1,y1,x2,y2,width=1,color=(0.75,0.80,0.90)):
    r,g,b = color
    add(f"{r:.3f} {g:.3f} {b:.3f} RG {width} w {x1} {y1} m {x2} {y2} l S")

def wrap(s, max_chars):
    words = s.split()
    lines = []
    cur = ''
    for w in words:
        cand = w if not cur else cur + ' ' + w
        if len(cand) <= max_chars:
            cur = cand
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines

# Header
text(left, 806, 'Tahsin Mert Ulu', 'F2', 22, (0.09,0.20,0.39))
text(left, 788, 'Unity / Game Developer CV', 'F1', 10, (0.36,0.42,0.51))
text(left, 770, 'Istanbul, Turkey  |  +90 507 601 32 81  |  ulu@sabanciuniv.edu  |  LinkedIn available', 'F1', 9, (0.18,0.18,0.18))
line(left, 758, right, 758, 1.3)

cursor_y = 736

def section(title):
    global cursor_y
    text(left, cursor_y, title.upper(), 'F2', 10, (0.09,0.20,0.39))
    cursor_y -= 8
    line(left, cursor_y, right, cursor_y, 0.8, (0.86,0.88,0.92))
    cursor_y -= 18

def bullet(text_str, max_chars=88, indent=12):
    global cursor_y
    lines = wrap(text_str, max_chars)
    text(left + 2, cursor_y, u'•', 'F1', 10)
    first = True
    for ln in lines:
        text(left + indent, cursor_y, ln, 'F1', 9)
        cursor_y -= 11
        first = False
    cursor_y -= 1

section('Experience')
text(left, cursor_y, 'Yapı Kredi Teknoloji', 'F2', 11, (0.12,0.12,0.12))
text(340, cursor_y, 'Software Engineering Intern', 'F1', 9, (0.35,0.35,0.35))
cursor_y -= 15
bullet('Contributed to internal banking applications used by internal teams.')
bullet('Worked on a full-stack banking application focused on efficiency and security.')
bullet('Used React on the frontend and contributed to backend and BFF layers with Java and Spring Boot.')
bullet('Worked with PostgreSQL for data access and application functionality.')

text(left, cursor_y, 'Asis Elektronik ve Bilişim Sistemleri', 'F2', 11, (0.12,0.12,0.12))
text(315, cursor_y, 'Software / Mobile Development Intern', 'F1', 9, (0.35,0.35,0.35))
cursor_y -= 15
bullet('Contributed to a mobile application for real-time bus tracking and card balance inquiry.')
bullet('Integrated open data APIs into the mobile application workflow.')
bullet('Worked with MVVM architecture in Android development.')

section('Projects')
text(left, cursor_y, 'Unity Puzzle Game Prototype', 'F2', 11, (0.12,0.12,0.12))
cursor_y -= 15
bullet('Developed a casual puzzle game prototype in Unity using C#.')
bullet('Designed grid-based gameplay mechanics for object interaction.')
bullet('Built reusable level structures and logic for dynamically generated levels.')
bullet('Added animation behaviors to improve gameplay feedback.')

text(left, cursor_y, 'Word Puzzle Prototype', 'F2', 11, (0.12,0.12,0.12))
cursor_y -= 15
bullet('Developed a word puzzle prototype inspired by letter-selection and word-validation gameplay loops.')
bullet('Recreated core mechanics by analyzing and reverse-engineering interaction patterns.')
bullet('Focused on gameplay logic, progression structure, and responsive user interaction.')

text(left, cursor_y, 'Match-Style Game Prototype', 'F2', 11, (0.12,0.12,0.12))
cursor_y -= 15
bullet('Built a match-style puzzle prototype in Unity with tile-matching and grid-based interactions.')
bullet('Explored gameplay loop design, state management, and casual puzzle mechanics.')

section('Education')
text(left, cursor_y, 'Sabancı University', 'F2', 11, (0.12,0.12,0.12))
text(320, cursor_y, 'B.Sc. Computer Science and Engineering', 'F1', 9, (0.35,0.35,0.35))
cursor_y -= 14
for ln in wrap('Minor in Decision and Behavior · GPA: 3.01 · Exchange: Technische Universität Hamburg · Graduation: 2025', 92):
    text(left, cursor_y, ln, 'F1', 9)
    cursor_y -= 11

section('Skills')
for ln in wrap('Unity, C#, Gameplay Systems, Level Design Systems, Grid-Based Mechanics, Game Prototyping, Animation Integration, Event-Driven Gameplay Logic, UI Development, Object-Oriented Programming, Java, Python, JavaScript, React, SQL, PostgreSQL, Android Studio, Django, Git, Scrum, Jira, Bitbucket', 94):
    text(left, cursor_y, ln, 'F1', 9)
    cursor_y -= 11

section('Languages')
text(left, cursor_y, 'Turkish (Native), English (Advanced), German (Beginner)', 'F1', 9)

stream = '\n'.join(content).encode('latin-1', 'replace')
objs = []
objs.append(b'1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj\n')
objs.append(b'2 0 obj << /Type /Pages /Count 1 /Kids [3 0 R] >> endobj\n')
objs.append(f'3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 {W} {H}] /Resources << /Font << /F1 4 0 R /F2 5 0 R >> >> /Contents 6 0 R >> endobj\n'.encode())
objs.append(b'4 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj\n')
objs.append(b'5 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold >> endobj\n')
objs.append(f'6 0 obj << /Length {len(stream)} >> stream\n'.encode() + stream + b'\nendstream endobj\n')

pdf = b'%PDF-1.4\n%\xe2\xe3\xcf\xd3\n'
offsets = [0]
for obj in objs:
    offsets.append(len(pdf))
    pdf += obj
xref_start = len(pdf)
pdf += f'xref\n0 {len(objs)+1}\n'.encode()
pdf += b'0000000000 65535 f \n'
for off in offsets[1:]:
    pdf += f'{off:010d} 00000 n \n'.encode()
pdf += f'trailer << /Size {len(objs)+1} /Root 1 0 R >>\nstartxref\n{xref_start}\n%%EOF\n'.encode()

out = Path('/Users/mertulu/.openclaw/workspace/runtime-data/cv/Tahsin_Mert_Ulu_Unity_Game_Developer_CV.pdf')
out.parent.mkdir(parents=True, exist_ok=True)
out.write_bytes(pdf)
print(out)
