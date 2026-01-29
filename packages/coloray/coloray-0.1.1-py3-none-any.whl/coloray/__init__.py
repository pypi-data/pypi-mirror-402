import os

# =====================
# enable dah ansi
# =====================
def _enable():
    if os.name != "nt":
        return
    try:
        import ctypes
        k = ctypes.windll.kernel32
        h = k.GetStdHandle(-11)
        m = ctypes.c_uint32()
        if k.GetConsoleMode(h, ctypes.byref(m)):
            k.SetConsoleMode(h, m.value | 0x0004)
    except Exception:
        pass

_enable()

CSI = "\033["
RESET = f"{CSI}0m"
_cache = {}
_truecolor = True  # ts is da default mode

def _ansi(code):
    if code not in _cache:
        _cache[code] = f"{CSI}{code}m"
    return _cache[code]

# =====================
# style
# =====================
class style:
    RESET = RESET
    BOLD = _ansi("1")
    DIM = _ansi("2")
    ITALIC = _ansi("3")
    UNDERLINE = _ansi("4")
    REVERSE = _ansi("7")
    STRIKE = _ansi("9")

# =====================
# ts internal helpers
# =====================
def _rgb(r,g,b,bg=False):
    if _truecolor:
        return _ansi(f"{48 if bg else 38};2;{r};{g};{b}")
    else:
        r5 = min(int(r/256*6),5)
        g5 = min(int(g/256*6),5)
        b5 = min(int(b/256*6),5)
        code = 16 + 36*r5 + 6*g5 + b5
        return _ansi(f"{48 if bg else 38};5;{code}")

def _hex_to_rgb(value):
    value = value.lstrip("#")
    return int(value[0:2],16), int(value[2:4],16), int(value[4:6],16)

# =====================
# background
# =====================
class bg:
    BLACK   = _rgb(0,0,0,bg=True)
    RED     = _rgb(255,0,0,bg=True)
    GREEN   = _rgb(0,255,0,bg=True)
    YELLOW  = _rgb(255,255,0,bg=True)
    BLUE    = _rgb(0,0,255,bg=True)
    MAGENTA = _rgb(255,0,255,bg=True)
    CYAN    = _rgb(0,255,255,bg=True)
    WHITE   = _rgb(255,255,255,bg=True)

    LIGHTBLUE = _rgb(173,216,230,bg=True)
    LIME      = _rgb(50,205,50,bg=True)
    ORANGE    = _rgb(255,165,0,bg=True)

    @staticmethod
    def rgb(r,g,b):
        return _rgb(r,g,b,bg=True)

    @staticmethod
    def hex(value):
        r,g,b = _hex_to_rgb(value)
        return _rgb(r,g,b,bg=True)

    @staticmethod
    def gradient(start_hex,end_hex,text, fg=None):
        """create a gradient on background. fg can be a fixed foreground color"""
        sr,sg,sb = _hex_to_rgb(start_hex)
        er,eg,eb = _hex_to_rgb(end_hex)
        n = len(text)-1 or 1
        out=[]
        for i,ch in enumerate(text):
            t=i/n
            r=int(sr+(er-sr)*t)
            g=int(sg+(eg-sg)*t)
            b=int(sb+(eb-sb)*t)
            bg_color = _rgb(r,g,b,bg=True)
            out.append((fg or "") + bg_color + ch)
        return "".join(out)

# =====================
# color
# =====================
class color:
    RESET = RESET

    BLACK   = _rgb(0,0,0)
    RED     = _rgb(255,0,0)
    GREEN   = _rgb(0,255,0)
    YELLOW  = _rgb(255,255,0)
    BLUE    = _rgb(0,0,255)
    MAGENTA = _rgb(255,0,255)
    CYAN    = _rgb(0,255,255)
    WHITE   = _rgb(255,255,255)

    LIGHTBLUE = _rgb(173,216,230)
    LIME      = _rgb(50,205,50)
    ORANGE    = _rgb(255,165,0)

    bg = bg

    @staticmethod
    def rgb(r,g,b):
        return _rgb(r,g,b)
    @staticmethod
    def hex(value):
        r,g,b = _hex_to_rgb(value)
        return _rgb(r,g,b)

    @staticmethod
    def gradient(start_hex,end_hex,text, bg_color=None):
        """Create gradient text, optional background"""
        sr,sg,sb = _hex_to_rgb(start_hex)
        er,eg,eb = _hex_to_rgb(end_hex)
        n = len(text)-1 or 1
        out=[]
        for i,ch in enumerate(text):
            t=i/n
            r=int(sr+(er-sr)*t)
            g=int(sg+(eg-sg)*t)
            b=int(sb+(eb-sb)*t)
            out.append(_rgb(r,g,b) + (bg_color or "") + ch)
        return "".join(out)

# =====================
# public api to switch modes
# =====================
def truecolor():
    global _truecolor
    _truecolor = True

def ansi8bit():
    global _truecolor
    _truecolor = False
