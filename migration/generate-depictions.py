#!/usr/bin/env python3
"""One-off generator used on 2026-11-21 to write depictions/<id>/depiction.json,
depictions/<id>/index.html and the home page index.html from the data carried over
from YouRepo (see migration/yourepo/).

Run from the repository root:  python3 migration/generate-depictions.py

The generated files are committed and are meant to be edited by hand afterwards
(a new version = edit depiction.json + index.html of that package). Do not run this
again without checking `git diff`: it overwrites those files.
"""
import html
import json
import os
import re

BASE = "https://imod-commission.github.io/imod-repo"
SOURCE_URL = BASE + "/"
YR_DATE = "2026-11-21"  # when the YouRepo numbers were read

P = []


def pkg(**kw):
    P.append(kw)


pkg(
    id="com.imodcommission.ersatz", name="Ersatz Reborn", section="Tweaks", version="2.3.1",
    author="Skitty, TweakDev22, imod_commission", archs=["iphoneos-arm64e"],
    short="Replace any text, system-wide!",
    desc=(
        "Replace any text, system-wide!\n\n"
        "Fork of Ersatz by Skitty, updated for roothide and extended.\n\n"
        "Features:\n"
        "- RootHide support\n"
        "- Search bar (matches phrase and replacement)\n"
        "- Longest-phrase-first replacement order\n"
        "- Adaptive label sizing (widen first, then shrink font)\n"
        "- Whole-word replacement\n"
        "- Per-rule app whitelist / blacklist (with app picker + search)\n"
        "- Exact-match replacement\n"
        "- English, Traditional/Simplified Chinese, Japanese localizations\n"
        "- Logging"
    ),
    downloads="57", rating=None, votes=0, icon=True,
    shots=["1.jpg", "2.jpg", "3.jpg"],
    changelog=[
        ("2.3.1", ["renamed to ersatz reborn", "fixed replacement looping"]),
        ("2.3", ["Exact-match replacement"]),
        ("2.2", ["whole-word replacement and prefs cleanup"]),
        ("2.1.1", ["able to search for system apps"]),
        ("2.1", ["fix issues for liquidass",
                 "logs available at `jbroot/var/mobile/Library/Logs/Ersatz.log`"]),
        ("2.0", ["Initial release"]),
    ],
)
pkg(
    id="com.imodcommission.griddy", name="Griddy", section="Tweaks", version="1.1.6",
    author="mikifp, imod_commission", archs=["iphoneos-arm64"],
    short="Layout your icons anywhere you want!",
    desc=("Layout your icons anywhere you want! Fixed issues for icon themes, "
          "folder icons, and app library."),
    downloads="180", rating=None, votes=0, icon=False, shots=[],
    changelog=[
        ("1.1.6", ["Completely fix App Library"]),
        ("1.1.5", ["Fixed some crashing bugs"]),
        ("1.1", ["initial release"]),
    ],
)
pkg(
    id="com.imodcommission.iconsizefix", name="IconSizeFix", section="Tweaks", version="1.1",
    author="imod_commission", archs=["iphoneos-arm64 (1.1)", "iphoneos-arm64e (0.1.0)"],
    short="Adjusts icon sizes etc",
    desc=("Adjusts icon sizes etc\n\n"
          "独立调整图标大小 / 隐藏 App 与小组件名称（roothide 兼容）\n\n"
          "Note: in this source the newest build, 1.1, is iphoneos-arm64 only. "
          "The iphoneos-arm64e build is the older 0.1.0."),
    downloads="78", rating=4.0, votes=1, icon=False, shots=[],
    changelog=[
        ("1.1", ["fixed crash when opening widget then returning to Home Screen",
                 "fixed version scheming", "updated for rootless"]),
    ],
)
pkg(
    id="com.imodcommission.movesleepalarm", name="MoveSleepAlarm", section="Tweaks",
    version="1.0.0", author="imod_commission", archs=["iphoneos-arm64"],
    short="实时调整锁屏睡眠闹钟Y轴偏移 (RootHide)",
    desc="实时调整锁屏睡眠闹钟Y轴偏移 (RootHide)",
    downloads="38", rating=1.0, votes=1, icon=False, shots=[], changelog=[],
)
pkg(
    id="com.imodcommission.notifyyy", name="notifyyy", section="Tweaks", version="1.0.0",
    author="imod_commission", archs=["iphoneos-arm64e"],
    short="只控制直屏（竖屏）通知横幅的上下位置，横屏不干预",
    desc="只控制直屏（竖屏）通知横幅的上下位置，横屏不干预",
    downloads="12", rating=None, votes=0, icon=False, shots=[], changelog=[],
)
pkg(
    id="com.imodcommission.hidelsclock", name="Hide LS Clock", section="Tweaks",
    version="0.0.1-1+debug", author="imod_commission", archs=["iphoneos-arm64"],
    short="An awesome MobileSubstrate tweak!",
    desc="An awesome MobileSubstrate tweak!",
    downloads="55", rating=3.75, votes=4, icon=False, shots=[], changelog=[],
    note="YouRepo listed this package as version 0.1; the build in this source is 0.0.1-1+debug.",
)
pkg(
    id="com.imodcommission.liquidglasstheme", name="Liquid Glass", section="Themes",
    version="1.0", author="imod_commission", archs=["iphoneos-arm", "iphoneos-arm64"],
    short="iOS 26 styled Liquid Glass dock and icon masks",
    desc="iOS 26 styled Liquid Glass dock and icon masks",
    downloads="396", downloads_detail="343 (arm64) + 53 (arm)", rating=4.33, votes=3,
    icon=False, shots=[], changelog=[],
    note="YouRepo listed the arm64 and arm builds as two packages; downloads and votes are added together.",
)
pkg(
    id="com.imodcommission.nig", name="Nig", section="Tweaks", version="1.0.0",
    author="imod_commission", archs=["iphoneos-arm64", "iphoneos-arm64e"],
    short="Night mode for unsupported apps and websites!",
    desc=(
        "**Night mode for unsupported apps and websites!**\n\n"
        "Night mode for apps and websites that do not have a dark theme. "
        "Nig follows the system appearance: when iOS is in Dark mode it recolours UIKit apps "
        "and the web pages shown in Safari, in-app browsers and web views. "
        "In Light mode it does nothing.\n\n"
        "Dark colours become a lighter shade of the same hue, photos and QR codes are left alone.\n\n"
        "Exclude a single app with Choicy, or a website in the Nig settings pane "
        "(Settings ▸ Nig ▸ Excluded sites).\n\n"
        "Nig cannot recolour apps that draw their own UI (Flutter, games, some cross-platform apps) "
        "and it does not work in every app: some will look wrong or be left unchanged. "
        "Turn Nig off for that app or site if that happens.\n\n"
        "Packages for rootless (iphoneos-arm64) and roothide (iphoneos-arm64e) jailbreaks. "
        "Requires iOS 16.0 or later, MobileSubstrate and PreferenceLoader."
    ),
    downloads=None, rating=None, votes=0, icon=True, shots=[], changelog=[],
    license="MIT", link=("Source code", "https://github.com/imod-commission/Nig"),
)


def rating_text(p):
    v = "vote" if p["votes"] == 1 else "votes"
    s = "%.2f" % p["rating"]
    if s.endswith("0"):
        s = s[:-1]
    return "%s from %d %s" % (s, p["votes"], v)


def rating_note(p):
    t = "Ratings carried over from YouRepo (%s): %s. " % (YR_DATE, rating_text(p))
    t += "These are anonymous star votes; this source cannot collect new votes."
    if p.get("note"):
        t += " " + p["note"]
    return t


def downloads_title():
    return "Downloads (YouRepo, as of %s)" % YR_DATE


def json_depiction(p):
    d = "%s/depictions/%s" % (BASE, p["id"])
    det = []
    if p["shots"]:
        det.append({
            "class": "DepictionScreenshotsView", "itemCornerRadius": 9, "itemSize": "{232, 440}",
            "screenshots": [{"url": "%s/screenshots/%s" % (d, s), "accessibilityText": "Screenshot"}
                            for s in p["shots"]],
        })
        det.append({"class": "DepictionSeparatorView"})
    det.append({"class": "DepictionHeaderView", "title": "Description"})
    det.append({"class": "DepictionMarkdownView", "markdown": p["desc"], "useSpacing": True})
    det.append({"class": "DepictionSeparatorView"})
    if p["rating"] is not None:
        det.append({"class": "DepictionHeaderView", "title": "Rating"})
        det.append({"class": "DepictionRatingView", "rating": p["rating"], "alignment": 1})
        det.append({"class": "DepictionMarkdownView", "markdown": "*" + rating_note(p) + "*",
                    "useSpacing": True})
        det.append({"class": "DepictionSeparatorView"})
    elif p.get("note"):
        det.append({"class": "DepictionMarkdownView", "markdown": "*" + p["note"] + "*",
                    "useSpacing": True})
        det.append({"class": "DepictionSeparatorView"})
    det.append({"class": "DepictionHeaderView", "title": "Information"})
    rows = [("Version", p["version"]), ("Author", p["author"]), ("Section", p["section"]),
            ("License", p.get("license", "Free"))]
    if p["downloads"] is not None:
        rows.append((downloads_title(), p["downloads"]))
    for k, v in rows:
        det.append({"class": "DepictionTableTextView", "title": k, "text": v})
    if p.get("downloads_detail"):
        det.append({"class": "DepictionMarkdownView", "markdown": "*Downloads: %s.*" % p["downloads_detail"],
                    "useSpacing": True})
    if p.get("link"):
        det.append({"class": "DepictionTableButtonView", "title": p["link"][0],
                    "action": p["link"][1], "openExternal": 1})
    tabs = [{"tabname": "Details", "class": "DepictionStackView", "views": det}]
    if p["changelog"]:
        cl = []
        for ver, lines in p["changelog"]:
            cl.append({"class": "DepictionSubheaderView", "title": ver})
            cl.append({"class": "DepictionMarkdownView",
                       "markdown": "\n".join("- " + x for x in lines), "useSpacing": True})
        tabs.append({"tabname": "Changelog", "class": "DepictionStackView", "views": cl})
    return {"class": "DepictionTabView", "minVersion": "0.4", "tintColor": "#5E7CE2", "tabs": tabs}


def inline(s):
    s = html.escape(s, quote=False)
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"\*(.+?)\*", r"<em>\1</em>", s)
    s = re.sub(r"`(.+?)`", r"<code>\1</code>", s)
    return s


def md_html(text):
    out = []
    for block in text.split("\n\n"):
        lines = block.split("\n")
        if all(x.startswith("- ") for x in lines):
            out.append("<ul>" + "".join("<li>%s</li>" % inline(x[2:]) for x in lines) + "</ul>")
        elif any(x.startswith("- ") for x in lines):
            head = [x for x in lines if not x.startswith("- ")]
            items = [x for x in lines if x.startswith("- ")]
            out.append("<p>%s</p>" % "<br>".join(inline(x) for x in head))
            out.append("<ul>" + "".join("<li>%s</li>" % inline(x[2:]) for x in items) + "</ul>")
        else:
            out.append("<p>%s</p>" % "<br>".join(inline(x) for x in lines))
    return "\n".join(out)


CSS = """
:root{color-scheme:light dark;--fg:#1c1c1e;--bg:#fff;--mut:#6c6c70;--card:#f2f2f7;--tint:#3f5fd0}
@media(prefers-color-scheme:dark){:root{--fg:#f2f2f7;--bg:#000;--mut:#98989d;--card:#1c1c1e;--tint:#8da2f5}}
body{font:16px/1.5 -apple-system,system-ui,sans-serif;color:var(--fg);background:var(--bg);margin:0;padding:16px;max-width:680px;margin:0 auto}
a{color:var(--tint)}h1{margin:.2em 0}h2{font-size:1.1em;margin:1.6em 0 .4em;border-bottom:1px solid var(--card)}
.head{display:flex;gap:14px;align-items:center}.head img{width:64px;height:64px;border-radius:14px}
.mut{color:var(--mut)}table{border-collapse:collapse;width:100%}td{padding:6px 0;border-bottom:1px solid var(--card);vertical-align:top}td:first-child{color:var(--mut);padding-right:12px;white-space:nowrap}
.shots{display:flex;gap:10px;overflow-x:auto;padding:4px 0}.shots img{height:360px;border-radius:9px}
.card{background:var(--card);border-radius:10px;padding:10px 14px}code{background:var(--card);padding:0 4px;border-radius:4px}
.list a{display:flex;gap:12px;align-items:center;padding:10px 0;border-bottom:1px solid var(--card);text-decoration:none;color:inherit}
.list img,.list .noicon{width:44px;height:44px;border-radius:10px;flex:none;background:var(--card)}
.btn{display:inline-block;background:var(--tint);color:var(--bg);padding:8px 16px;border-radius:10px;text-decoration:none;font-weight:600}
"""


def stars(r):
    full = int(round(r))
    return "★" * full + "☆" * (5 - full)


def html_depiction(p):
    h = []
    h.append('<!doctype html><html lang="en"><head><meta charset="utf-8">'
             '<meta name="viewport" content="width=device-width,initial-scale=1">'
             "<title>%s – imod</title><style>%s</style></head><body>" % (html.escape(p["name"]), CSS))
    h.append('<div class="head">')
    if p["icon"]:
        h.append('<img src="icon.png" alt="">')
    h.append("<div><h1>%s</h1><div class=\"mut\">%s · %s</div></div></div>" % (
        html.escape(p["name"]), html.escape(p["id"]), html.escape(p["version"])))
    if p["shots"]:
        h.append('<div class="shots">%s</div>' % "".join(
            '<img src="screenshots/%s" alt="Screenshot">' % s for s in p["shots"]))
    h.append("<h2>Description</h2>" + md_html(p["desc"]))
    if p["rating"] is not None:
        h.append("<h2>Rating</h2><p><strong>%s</strong> %s</p><p class=\"mut\"><em>%s</em></p>" % (
            stars(p["rating"]), html.escape(rating_text(p)), html.escape(rating_note(p))))
    elif p.get("note"):
        h.append('<p class="mut"><em>%s</em></p>' % html.escape(p["note"]))
    rows = [("Version", p["version"]), ("Architectures", ", ".join(p["archs"])),
            ("Author", p["author"]), ("Section", p["section"]), ("License", p.get("license", "Free"))]
    if p["downloads"] is not None:
        d = p["downloads"] + (" (%s)" % p["downloads_detail"] if p.get("downloads_detail") else "")
        rows.append((downloads_title(), d))
    h.append("<h2>Information</h2><table>%s</table>" % "".join(
        "<tr><td>%s</td><td>%s</td></tr>" % (html.escape(k), html.escape(v)) for k, v in rows))
    if p.get("link"):
        h.append('<p><a href="%s">%s</a></p>' % (html.escape(p["link"][1]), html.escape(p["link"][0])))
    if p["changelog"]:
        h.append("<h2>Changelog</h2>")
        for ver, lines in p["changelog"]:
            h.append("<h3>%s</h3>" % html.escape(ver))
            h.append("<ul>%s</ul>" % "".join("<li>%s</li>" % inline(x) for x in lines))
    h.append('<p class="mut"><a href="../../">← imod source</a></p></body></html>')
    return "\n".join(h)


def home():
    h = []
    h.append('<!doctype html><html lang="en"><head><meta charset="utf-8">'
             '<meta name="viewport" content="width=device-width,initial-scale=1">'
             "<title>imod – iOS package source</title><style>%s</style></head><body>" % CSS)
    h.append('<div class="head"><img src="CydiaIcon.png" alt=""><div><h1>imod</h1>'
             '<div class="mut">Tweaks by imod_commission</div></div></div>')
    h.append('<p><a class="btn" href="sileo://source/%s">Add to Sileo</a></p>' % SOURCE_URL)
    h.append('<p>Source URL (Sileo, Zebra, Irisin, Cydia…): <code>%s</code></p>' % SOURCE_URL)
    h.append('<p class="card">If you installed these from YouRepo (<code>com.yourepo.imod.*</code>), '
             "remove the old package first, the IDs changed to <code>com.imodcommission.*</code>.</p>")
    h.append("<h2>Packages</h2><div class=\"list\">")
    for p in sorted(P, key=lambda x: x["name"].lower()):
        icon = '<img src="depictions/%s/icon.png" alt="">' % p["id"] if p["icon"] else '<span class="noicon"></span>'
        h.append('<a href="depictions/%s/">%s<div><strong>%s</strong> <span class="mut">%s · %s</span><br>'
                 '<span class="mut">%s</span></div></a>' % (
                     p["id"], icon, html.escape(p["name"]), html.escape(p["version"]),
                     html.escape(p["section"]), html.escape(p["short"])))
    h.append('<div style="padding:10px 0"><strong>RounderLS</strong> <span class="mut">1.5-6+debug · Tweaks</span><br>'
             '<span class="mut">Third-party package by Azzou (<code>com.azzou.rounderls</code>), '
             "included as it is. A little tweak to make your LockScreen rounder! 下拉通知圆角</span></div>")
    h.append("</div>")
    h.append('<p class="mut">Download counts and ratings shown on the package pages were carried over '
             "from YouRepo as of %s. A static source cannot count downloads or collect votes.</p>" % YR_DATE)
    h.append("</body></html>")
    return "\n".join(h)


def main():
    for p in P:
        d = os.path.join("depictions", p["id"])
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, "depiction.json"), "w", encoding="utf-8") as f:
            json.dump(json_depiction(p), f, ensure_ascii=False, indent=2)
            f.write("\n")
        with open(os.path.join(d, "index.html"), "w", encoding="utf-8") as f:
            f.write(html_depiction(p) + "\n")
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(home() + "\n")


if __name__ == "__main__":
    main()
