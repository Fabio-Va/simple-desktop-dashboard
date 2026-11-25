"""Colori dei marchi dei siti più noti, per le app aggiunte come link (es. linkedin.com -> blu LinkedIn).

Chiave: dominio (vale anche per i suoi sottodomini; per i domini a due livelli, es. amazon.com, anche
con altre estensioni, es. amazon.it). Valore: colore di sfondo, oppure (sfondo, colore della lettera)
quando lo sfondo è chiaro, oppure (sfondo, lettera, disegno) per i loghi disegnati (vedi DRAWINGS in sidd.py).
"""
from urllib.parse import urlparse

DARK = "#111111"

BRANDS = {
    # Google
    "google.com": "#4285F4", "mail.google.com": "#EA4335", "drive.google.com": "#1FA463",
    "docs.google.com": "#4285F4", "sheets.google.com": "#0F9D58", "calendar.google.com": "#4285F4",
    "maps.google.com": "#34A853", "meet.google.com": "#00897B", "photos.google.com": ("#FBBC04", DARK),
    "keep.google.com": ("#FBBC04", DARK), "translate.google.com": "#4285F4", "classroom.google.com": "#0F9D58",
    "gemini.google.com": "#8E75B2", "gmail.com": "#EA4335",
    "youtube.com": "#FF0000", "youtu.be": "#FF0000",
    # social e messaggi
    "facebook.com": "#1877F2", "instagram.com": "#E4405F", "whatsapp.com": "#25D366", "messenger.com": "#0084FF",
    "threads.net": "#000000", "threads.com": "#000000", "x.com": "#000000", "twitter.com": "#1DA1F2",
    "linkedin.com": "#0A66C2", "reddit.com": "#FF4500", "pinterest.com": "#E60023", "tiktok.com": "#000000",
    "snapchat.com": ("#FFFC00", DARK), "tumblr.com": "#36465D", "telegram.org": "#26A5E4", "t.me": "#26A5E4",
    "discord.com": "#5865F2", "discord.gg": "#5865F2", "slack.com": "#4A154B", "zoom.us": "#0B5CFF",
    "skype.com": "#00AFF0", "signal.org": "#3A76F0", "bsky.app": "#0085FF", "mastodon.social": "#6364FF",
    "quora.com": "#B92B27", "medium.com": "#000000", "substack.com": "#FF6719", "line.me": "#06C755",
    "wechat.com": "#07C160", "weibo.com": "#E6162D", "bilibili.com": "#00A1D6", "baidu.com": "#2932E1",
    # Microsoft e Apple
    "microsoft.com": "#0078D4", "teams.microsoft.com": "#6264A7", "outlook.com": "#0078D4",
    "outlook.live.com": "#0078D4", "outlook.office.com": "#0078D4", "office.com": "#D83B01",
    "onedrive.live.com": "#0078D4", "live.com": "#0078D4", "bing.com": "#008373", "xbox.com": "#107C10",
    "apple.com": "#000000", "icloud.com": "#3693F3", "music.apple.com": "#FA243C",
    # lavoro e sviluppo
    "github.com": "#181717", "gitlab.com": "#FC6D26", "bitbucket.org": "#0052CC", "stackoverflow.com": "#F58025",
    "notion.so": "#000000", "notion.com": "#000000", "trello.com": "#0052CC", "atlassian.net": "#0052CC",
    "figma.com": "#F24E1E", "canva.com": "#00C4CC", "dropbox.com": "#0061FF", "box.com": "#0061D5",
    "evernote.com": "#00A82D", "todoist.com": "#E44332", "asana.com": "#F06A6A", "miro.com": ("#FFD02F", "#050038"),
    "airtable.com": "#18BFFF", "behance.net": "#1769FF", "dribbble.com": "#EA4C89",
    "vercel.com": "#000000", "netlify.com": "#00C7B7", "cloudflare.com": "#F38020", "docker.com": "#2496ED",
    "npmjs.com": "#CB3837", "pypi.org": "#3775A9", "huggingface.co": ("#FFD21E", DARK), "kaggle.com": "#20BEFF",
    # elettronica e maker
    "arduino.cc": "#00878F", "st.com": "#03234B", "raspberrypi.com": "#A22846", "digikey.com": "#CC0000",
    "digikey.it": "#CC0000", "mouser.com": "#004A85", "mouser.it": "#004A85", "adafruit.com": "#000000",
    "sparkfun.com": "#E53525", "thingiverse.com": "#248BFB", "printables.com": "#FA6831",
    # IA
    "chatgpt.com": "#10A37F", "openai.com": "#000000", "claude.ai": "#D97757", "anthropic.com": "#191919",
    "perplexity.ai": "#20808D", "deepl.com": "#0F2B46", "grammarly.com": "#15C39A",
    # musica, video e giochi
    "spotify.com": ("#1ED760", "#000000", "spotify"), "soundcloud.com": "#FF5500", "deezer.com": "#A238FF",
    "netflix.com": "#E50914", "primevideo.com": "#00A8E1", "disneyplus.com": "#113CCF", "twitch.tv": "#9146FF",
    "vimeo.com": "#1AB7EA", "crunchyroll.com": "#F47521", "max.com": "#002BE7", "dazn.com": ("#F8FC00", DARK),
    "steampowered.com": "#171A21", "steamcommunity.com": "#171A21", "epicgames.com": "#313131",
    "playstation.com": "#003791", "nintendo.com": "#E60012", "riotgames.com": "#D13639",
    "leagueoflegends.com": "#C89B3C", "op.gg": "#5383E8", "battle.net": "#148EFF", "roblox.com": "#000000",
    "chess.com": "#81B64C", "imdb.com": ("#F5C518", DARK),
    # acquisti, viaggi e soldi
    "amazon.com": ("#FF9900", DARK), "ebay.com": "#E53238", "aliexpress.com": "#FF4747", "etsy.com": "#F16521",
    "temu.com": "#FB7701", "vinted.com": "#09B1BA", "zalando.com": "#FF6900", "ikea.com": "#0058A3",
    "subito.it": "#F9423A", "paypal.com": "#003087", "revolut.com": "#0666EB", "n26.com": "#36A18B",
    "wise.com": ("#9FE870", "#163300"), "satispay.com": "#EF373F", "coinbase.com": "#0052FF",
    "binance.com": ("#F0B90B", DARK), "tradingview.com": "#131722", "booking.com": "#003580",
    "airbnb.com": "#FF5A5F", "tripadvisor.com": ("#34E0A1", DARK), "uber.com": "#000000",
    "deliveroo.com": "#00CCBC", "glovoapp.com": ("#FFC244", DARK), "justeat.it": "#FF8000",
    # altro
    "wikipedia.org": "#000000", "yahoo.com": "#6001D2", "duckduckgo.com": "#DE5833", "proton.me": "#6D4AFF",
    "duolingo.com": "#58CC02", "udemy.com": "#A435F0", "coursera.org": "#0056D2", "khanacademy.org": "#14BF96",
    "unsplash.com": "#000000", "flickr.com": "#0063DC", "imgur.com": "#1BB76E", "deviantart.com": "#05CC47",
    "waze.com": ("#33CCFF", DARK),
}

# link che non sono indirizzi web: schema -> dominio del marchio
SCHEMES = {"spotify": "spotify.com", "steam": "steampowered.com", "discord": "discord.com",
           "zoommtg": "zoom.us", "msteams": "teams.microsoft.com", "slack": "slack.com", "tg": "telegram.org",
           "whatsapp": "whatsapp.com", "mailto": "mail.google.com"}

# nome senza estensione -> dominio (amazon -> amazon.com), per riconoscere anche amazon.it, ebay.de...
_BY_NAME = {}
for _d in BRANDS:
    _parts = _d.split(".")
    if len(_parts) == 2:
        _BY_NAME.setdefault(_parts[0], _d)


def _norm(v):
    v = (v,) if isinstance(v, str) else tuple(v)
    return v[0], (v[1] if len(v) > 1 else "#FFFFFF"), (v[2] if len(v) > 2 else None)


def brand_for(target):
    """(sfondo, colore lettera, disegno) del marchio del link, oppure None se il sito non è noto."""
    t = (target or "").strip()
    if not t:
        return None
    scheme = t.split(":", 1)[0].lower() if ":" in t else ""
    if scheme in SCHEMES:
        return _norm(BRANDS[SCHEMES[scheme]])
    if "://" not in t:
        return None
    host = (urlparse(t).hostname or "").lower().removeprefix("www.")
    labels = host.split(".")
    for i in range(len(labels) - 1):  # mail.google.com, poi google.com
        d = ".".join(labels[i:])
        if d in BRANDS:
            return _norm(BRANDS[d])
    # stesso marchio con un'altra estensione: amazon.it, amazon.co.uk
    if len(labels) >= 2:
        name = labels[-3] if len(labels) >= 3 and labels[-2] in ("co", "com") and len(labels[-1]) == 2 else labels[-2]
        if name in _BY_NAME:
            return _norm(BRANDS[_BY_NAME[name]])
    return None
