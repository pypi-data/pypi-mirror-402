import msvcrt

Colors = {
    # Reds
    "red"        : "255;0;0",
    "maroon"     : "128;0;0",
    "crimson"    : "220;20;60",
    "pink"       : "255;192;203",
    "hotpink"    : "255;105;180",

    # Oranges & Browns
    "orange"     : "255;165;0",
    "darkorange" : "255;140;0",
    "brown"      : "165;42;42",
    "darkbrown"  : "100;64;0",
    "chocolate"  : "210;105;30",
    "coral"      : "255;127;80",

    # Yellows
    "yellow"     : "255;255;0",
    "gold"       : "255;215;0",
    "khaki"      : "240;230;140",

    # Greens
    "lightgreen" : "144;238;144",
    "darkgreen"  : "0;100;0",
    "green"      : "0;255;0",
    "lime"       : "50;205;50",
    "olive"      : "128;128;0",
    "seagreen"   : "46;139;87",

    # Blues
    "blue"       : "0;0;255",
    "navy"       : "0;0;128",
    "royalblue"  : "65;105;225",
    "skyblue"    : "135;206;235",
    "cyan"       : "0;255;255",
    "teal"       : "0;128;128",

    # Purples
    "purple"     : "128;0;128",
    "violet"     : "238;130;238",
    "indigo"     : "75;0;130",
    "magenta"    : "255;0;255",
    "orchid"     : "218;112;214",

    # Grays & Neutrals
    "black"      : "0;0;0",
    "gray"       : "128;128;128",
    "darkgray"   : "169;169;169",
    "lightgray"  : "211;211;211",
    "white"      : "255;255;255",
    "silver"     : "192;192;192"
}
def ColorPrint(text=None, fg=None, bg=None, font=None, end=None):
    fg_code = f"\033[38;2;{Colors[fg.lower()]}m" if isinstance(fg, str) else ""
    bg_code = f"\033[48;2;{Colors[bg.lower()]}m" if isinstance(bg, str) else ""
    style = ""
    if font == "bold": style = "\033[1m"
    elif font == "italic": style = "\033[3m"
    elif font == "underline": style = "\033[4m"

    print(f"{style}{fg_code}{bg_code}{text}\033[0m") if not end else print(f"{style}{fg_code}{bg_code}{text}\033[0m", end=end)

def ColorUP(text=None, fg=None, bg=None, font=None):
    fg_code = f"\033[38;2;{Colors[fg.lower()]}m" if isinstance(fg, str) else ""
    bg_code = f"\033[48;2;{Colors[bg.lower()]}m" if isinstance(bg, str) else ""
    
    style = ""
    if font == "bold":
        style = "\033[1m"
    elif font == "italic":
        style = "\033[3m"
    elif font == "underline":
        style = "\033[4m"

    return f"{style}{fg_code}{bg_code}{text}\033[0m"

def ColorInput(prompt=None, questionFG=None, questionBG=None, questionFont=None,
               answerFG=None, answerBG=None, answerFont=None, styleReturn=False):
    
    q_fg = f"\033[38;2;{Colors[questionFG.lower()]}m" if questionFG else ""
    q_bg = f"\033[48;2;{Colors[questionBG.lower()]}m" if questionBG else ""
    q_style = ""
    if questionFont == "bold": q_style = "\033[1m"
    elif questionFont == "italic": q_style = "\033[3m"
    elif questionFont == "underline": q_style = "\033[4m"

    if prompt:
        print(f"{q_style}{q_fg}{q_bg}{prompt}\033[0m", end="", flush=True)

    chars = []
    styled_chars = []
    while True:
        key = msvcrt.getch()

        if key == b'\r':
            print()
            break
        elif key == b'\x08':
            if chars:
                chars.pop()
                styled_chars.pop()
                print("\b \b", end="", flush=True)
        else:
            ch = key.decode(errors="ignore")
            chars.append(ch)

            a_fg = f"\033[38;2;{Colors[answerFG.lower()]}m" if answerFG else ""
            a_bg = f"\033[48;2;{Colors[answerBG.lower()]}m" if answerBG else ""
            a_style = ""
            if answerFont == "bold": a_style = "\033[1m"
            elif answerFont == "italic": a_style = "\033[3m"
            elif answerFont == "underline": a_style = "\033[4m"

            styled_char = f"{a_style}{a_fg}{a_bg}{ch}\033[0m"
            styled_chars.append(styled_char)

            print(styled_char, end="", flush=True)
    
    if styleReturn:
        return "".join(styled_chars)
    else:
        return "".join(chars)

def ColorInputEcho(prompt=None, questionFG=None, questionBG=None, questionFont=None,
                   answerFG=None, answerBG=None, answerFont=None, styleReturn=False):
    q_fg = f"\033[38;2;{Colors[questionFG.lower()]}m" if questionFG else ""
    q_bg = f"\033[48;2;{Colors[questionBG.lower()]}m" if questionBG else ""
    q_style = ""
    if questionFont == "bold": q_style = "\033[1m"
    elif questionFont == "italic": q_style = "\033[3m"
    elif questionFont == "underline": q_style = "\033[4m"

    if prompt:
        print(f"{q_style}{q_fg}{q_bg}{prompt}\033[0m", end="", flush=True)

    chars = []
    styled_chars = []
    print()
    while True:
        key = msvcrt.getch()

        if key == b'\r':  # Enter
            print()
            break
        elif key == b'\x08':  # Backspace
            if chars:
                chars.pop()
                styled_chars.pop()
                print("\r" + "".join(styled_chars) + " ", end="", flush=True)
        elif key in (b"\x00", b"\xe0"):  # special keys (arrows, F-keys)
            msvcrt.getch()  # consume second byte
            continue
        else:
            ch = key.decode(errors="ignore")
            chars.append(ch)

            a_fg = f"\033[38;2;{Colors[answerFG.lower()]}m" if answerFG else ""
            a_bg = f"\033[48;2;{Colors[answerBG.lower()]}m" if answerBG else ""
            a_style = ""
            if answerFont == "bold": a_style = "\033[1m"
            elif answerFont == "italic": a_style = "\033[3m"
            elif answerFont == "underline": a_style = "\033[4m"

            styled_char = f"{a_style}{a_fg}{a_bg}{ch}\033[0m"
            styled_chars.append(styled_char)
            print("\r" + "".join(styled_chars), end="", flush=True)

    if styleReturn:
        return "".join(styled_chars)
    else:
        return "".join(chars)

def RainbowPrint(text=None):
    rainbow = ["red", "orange", "yellow", "green", "blue", "indigo", "violet"]
    for i, ch in enumerate(text):
        color = rainbow[i % len(rainbow)]
        fg_code = f"\033[38;2;{Colors[color]}m"
        print(f"{fg_code}{ch}\033[0m", end="")
    print()

def ColorSeriesPrint(text=None, colors=None):
    for i, ch in enumerate(text):
        color = colors[i % len(colors)]
        fg_code = f"\033[38;2;{Colors[color]}m"
        print(f"{fg_code}{ch}\033[0m", end="")
    print()

def RainbowUP(text=None):
    rainbow = ["red", "orange", "yellow", "green", "blue", "indigo", "violet"]
    styled = []
    for i, ch in enumerate(text):
        color = rainbow[i % len(rainbow)]
        fg_code = f"\033[38;2;{Colors[color]}m"
        styled.append(f"{fg_code}{ch}\033[0m")
    return "".join(styled)

def ColorSeriesUP(text=None, colors=None):
    styled = []
    for i, ch in enumerate(text):
        color = colors[i % len(colors)]
        fg_code = f"\033[38;2;{Colors[color]}m"
        styled.append(f"{fg_code}{ch}\033[0m")
    return "".join(styled)   