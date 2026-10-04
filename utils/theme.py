def css(theme):
    dark = theme == "Dark"
    c = (
        dict(bg="#050505", side="#0a0a0a", card="#0e0e0f", border="#242427", text="#ececec", muted="#9aa0aa", acc="#5b9dff", inp="#0e0e0f")
        if dark
        else dict(bg="#f6f7f9", side="#ffffff", card="#ffffff", border="#e2e5ea", text="#14181f", muted="#5b6472", acc="#2457d6", inp="#ffffff")
    )
    return f"""
<style>
.stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"] {{ background:{c['bg']}; color:{c['text']}; }}
[data-testid="stHeader"] {{ background:transparent; }}
[data-testid="stSidebar"], [data-testid="stSidebar"] > div {{ background:{c['side']}; border-right:1px solid {c['border']}; }}
.stApp h1,.stApp h2,.stApp h3,.stApp h4,.stApp p,.stApp li,.stApp label,.stApp span,.stApp div[data-testid="stMarkdownContainer"],
.stApp [data-testid="stMetricValue"], .stApp [data-testid="stMetricLabel"] {{ color:{c['text']}; }}
.stApp [data-testid="stCaptionContainer"], .stApp small, .stApp .muted {{ color:{c['muted']} !important; }}
.stApp a {{ color:{c['acc']} !important; text-decoration:none; }}
.stApp a:hover {{ text-decoration:underline; }}
div[data-baseweb="input"], div[data-baseweb="textarea"], div[data-baseweb="select"] > div {{ background:{c['inp']} !important; border-color:{c['border']} !important; }}
textarea, input {{ color:{c['text']} !important; background:{c['inp']} !important; }}
div[data-baseweb="popover"] *, ul[role="listbox"], li[role="option"] {{ background:{c['card']} !important; color:{c['text']} !important; }}
.stButton > button, .stDownloadButton > button {{ background:{c['card']}; color:{c['text']}; border:1px solid {c['border']}; border-radius:10px; }}
.stButton > button:hover, .stDownloadButton > button:hover {{ border-color:{c['acc']}; color:{c['acc']}; }}
.stButton > button[kind="primary"] {{ background:{c['acc']}; color:#fff; border:none; }}
[data-testid="stVerticalBlockBorderWrapper"] {{ border-color:{c['border']} !important; background:{c['card']}; border-radius:12px; }}
[data-testid="stExpander"] {{ background:{c['card']}; border:1px solid {c['border']}; border-radius:10px; }}
[data-testid="stExpander"] summary, [data-testid="stExpander"] summary * {{ color:{c['text']} !important; }}
[data-testid="stTabs"] button {{ color:{c['muted']}; }}
[data-testid="stTabs"] button[aria-selected="true"] {{ color:{c['acc']}; }}
table {{ border-collapse:collapse; width:100%; font-size:0.9rem; }}
th, td {{ border:1px solid {c['border']} !important; padding:6px 8px; color:{c['text']}; }}
th {{ background:{c['card']}; }}
hr {{ border-color:{c['border']}; }}
.hero h1 {{ font-size:2.1rem; margin-bottom:0.2rem; }}
.hero p {{ color:{c['muted']}; margin-top:0; }}
.chip {{ display:inline-block; padding:3px 10px; border-radius:999px; border:1px solid {c['border']}; margin:2px 4px 2px 0; font-size:0.85rem; }}
.chip.run {{ border-color:{c['acc']}; color:{c['acc']}; }}
.chip.done {{ opacity:0.85; }}
</style>
"""
