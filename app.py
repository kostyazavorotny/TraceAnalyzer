import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import exifread
from PIL import Image
from io import BytesIO
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor
import re

st.set_page_config(page_title="TraceAnalyzer OSINT Suite", layout="wide")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
}

SITES = {
    "VK": {"url": "https://m.vk.com/{}", "category": "Соцсети"},
    "OK.ru": {"url": "https://ok.ru/profile/{}", "category": "Соцсети"},
    "Telegram": {"url": "https://t.me/{}", "category": "Мессенджеры"},
    "TikTok": {"url": "https://urlebird.com/user/{}/", "category": "Медиа"},
    "Reddit": {"url": "https://www.reddit.com/user/{}", "category": "Форумы"},
    "Pinterest": {"url": "https://www.pinterest.com/{}", "category": "Медиа"},
    "Twitter (Nitter)": {"url": "https://nitter.net/{}", "category": "Соцсети"},
    "Instagram (Mirror)": {"url": "https://imginn.com/{}", "category": "Соцсети"},
    "Facebook": {"url": "https://www.facebook.com/{}", "category": "Соцсети"},
    "Mastodon": {"url": "https://mastodon.social/@{}", "category": "Соцсети"},
    "Tumblr": {"url": "https://{}.tumblr.com", "category": "Блоги"},
    "Snapchat": {"url": "https://www.snapchat.com/add/{}", "category": "Соцсети"},
    "Zen.yandex.ru": {"url": "https://dzen.ru/id/{}", "category": "Медиа"},
    "TamTam": {"url": "https://tt.me/{}", "category": "Мессенджеры"},
    "Ask.fm": {"url": "https://ask.fm/{}", "category": "Соцсети"},
    "Ask.ru": {"url": "http://www.ask.ru/{}", "category": "Соцсети"},
    "Spaces.im": {"url": "https://spaces.im/{}", "category": "Соцсети"},
    "Amino": {"url": "https://aminoapps.com/u/{}", "category": "Соцсети"},
    "My.mail.ru": {"url": "https://my.mail.ru/mail/{}/", "category": "Соцсети"},
    "Foursquare": {"url": "https://foursquare.com/user/{}", "category": "Медиа"},

    "GitHub": {"url": "https://github.com/{}", "category": "IT & Разработка"},
    "GitLab": {"url": "https://gitlab.com/{}", "category": "IT & Разработка"},
    "Habr": {"url": "https://habr.com/ru/users/{}/", "category": "IT & Разработка"},
    "Codeforces": {"url": "https://codeforces.com/profile/{}", "category": "IT & Разработка"},
    "StackOverflow": {"url": "https://stackoverflow.com/users/{}", "category": "IT & Разработка"},
    "Docker Hub": {"url": "https://hub.docker.com/u/{}", "category": "IT & Разработка"},
    "PyPi": {"url": "https://pypi.org/user/{}", "category": "IT & Разработка"},
    "NPM": {"url": "https://www.npmjs.com/~{}", "category": "IT & Разработка"},
    "Bitbucket": {"url": "https://bitbucket.org/{}/", "category": "IT & Разработка"},
    "Kaggle": {"url": "https://www.kaggle.com/{}", "category": "IT & Разработка"},
    "Launchpad": {"url": "https://launchpad.net/~{}", "category": "IT & Разработка"},
    "SourceForge": {"url": "https://sourceforge.net/u/{}/", "category": "IT & Разработка"},
    "Replit": {"url": "https://replit.com/@{}", "category": "IT & Разработка"},
    "Coderwall": {"url": "https://coderwall.com/{}", "category": "IT & Разработка"},
    "Geekbrains": {"url": "https://geekbrains.ru/users/{}", "category": "IT & Разработка"},
    "Gitee": {"url": "https://gitee.com/{}", "category": "IT & Разработка"},
    "CodePen": {"url": "https://codepen.io/{}", "category": "IT & Разработка"},
    "HackerRank": {"url": "https://www.hackerrank.com/{}", "category": "IT & Разработка"},
    "LeetCode": {"url": "https://leetcode.com/{}", "category": "IT & Разработка"},
    "Tproger": {"url": "https://tproger.ru/users/{}/", "category": "IT & Разработка"},

    "Steam": {"url": "https://steamcommunity.com/id/{}", "category": "Игры"},
    "Chess.com": {"url": "https://www.chess.com/member/{}", "category": "Игры"},
    "Twitch": {"url": "https://www.twitch.tv/{}", "category": "Игры"},
    "Roblox": {"url": "https://www.roblox.com/user.aspx?username={}", "category": "Игры"},
    "Osu!": {"url": "https://osu.ppy.sh/users/{}", "category": "Игры"},
    "Xbox": {"url": "https://www.xboxgamertag.com/search/{}", "category": "Игры"},
    "Battle.net": {"url": "https://worldofwarcraft.com/en-us/character/{}", "category": "Игры"},
    "GOG": {"url": "https://www.gog.com/u/{}", "category": "Игры"},
    "EpicGames": {"url": "https://www.epicgames.com/id/{}", "category": "Игры"},
    "Speedrun.com": {"url": "https://www.speedrun.com/user/{}", "category": "Игры"},
    "ModDB": {"url": "https://www.moddb.com/members/{}", "category": "Игры"},
    "NexusMods": {"url": "https://www.nexusmods.com/users/{}", "category": "Игры"},
    "GameJolt": {"url": "https://gamejolt.com/@{}", "category": "Игры"},
    "Itch.io": {"url": "https://{}.itch.io", "category": "Игры"},
    "Raptr": {"url": "http://raptr.com/{}", "category": "Игры"},

    "SoundCloud": {"url": "https://soundcloud.com/{}", "category": "Медиа"},
    "Vimeo": {"url": "https://vimeo.com/{}", "category": "Медиа"},
    "Last.fm": {"url": "https://www.last.fm/user/{}", "category": "Медиа"},
    "Bandcamp": {"url": "https://bandcamp.com/{}", "category": "Медиа"},
    "DailyMotion": {"url": "https://www.dailymotion.com/{}", "category": "Медиа"},
    "Behance": {"url": "https://www.behance.net/{}", "category": "Дизайн"},
    "DeviantArt": {"url": "https://www.deviantart.com/{}", "category": "Дизайн"},
    "Dribbble": {"url": "https://dribbble.com/{}", "category": "Дизайн"},
    "ArtStation": {"url": "https://www.artstation.com/{}", "category": "Дизайн"},
    "Flickr": {"url": "https://www.flickr.com/photos/{}", "category": "Медиа"},
    "500px": {"url": "https://500px.com/p/{}", "category": "Медиа"},
    "Mixcloud": {"url": "https://www.mixcloud.com/{}/", "category": "Медиа"},
    "ReverbNation": {"url": "https://www.reverbnation.com/{}", "category": "Медиа"},
    "SmugMug": {"url": "https://{}.smugmug.com", "category": "Медиа"},
    "VSCO": {"url": "https://vsco.co/{}", "category": "Медиа"},

    "Duolingo": {"url": "https://www.duolingo.com/profile/{}", "category": "Обучение"},
    "Coursera": {"url": "https://www.coursera.org/user/{}", "category": "Обучение"},
    "Upwork": {"url": "https://www.upwork.com/freelancers/~{}", "category": "Работа"},
    "Fiverr": {"url": "https://www.fiverr.com/{}", "category": "Работа"},
    "Freelancer": {"url": "https://www.freelancer.com/u/{}", "category": "Работа"},
    "Linktree": {"url": "https://linktr.ee/{}", "category": "Профессиональное"},
    "Tilda": {"url": "https://tilda.ws/project{}/", "category": "Профессиональное"},
    "Wix": {"url": "https://{}.wixsite.com", "category": "Профессиональное"},
    "Patreon": {"url": "https://www.patreon.com/{}", "category": "Работа"},
    "BuyMeACoffee": {"url": "https://www.buymeacoffee.com/{}", "category": "Работа"},
    "About.me": {"url": "https://about.me/{}", "category": "Профессиональное"},
    "Stepik": {"url": "https://stepik.org/users/{}", "category": "Обучение"},
    "SlideShare": {"url": "https://www.slideshare.net/{}", "category": "Обучение"},
    "Issuu": {"url": "https://issuu.com/{}", "category": "Обучение"},
    "ProductHunt": {"url": "https://www.producthunt.com/@{}", "category": "Работа"},

    "Pikabu": {"url": "https://pikabu.ru/@{}", "category": "Блоги"},
    "LiveJournal": {"url": "https://{}.livejournal.com", "category": "Блоги"},
    "Blogger": {"url": "https://{}.blogspot.com", "category": "Блоги"},
    "Quora": {"url": "https://www.quora.com/profile/{}", "category": "Блоги"},
    "Drive2.ru": {"url": "https://www.drive2.ru/users/{}", "category": "Стиль жизни"},
    "Drom.ru": {"url": "https://forums.drom.ru/member.php?u={}", "category": "Стиль жизни"},
    "Otvet.mail.ru": {"url": "https://otvet.mail.ru/profile/id{}/", "category": "Блоги"},
    "Baby.ru": {"url": "https://www.baby.ru/u/{}/", "category": "Стиль жизни"},
    "Woman.ru": {"url": "https://www.woman.ru/user/{}/", "category": "Стиль жизни"},
    "Yaplakal": {"url": "https://www.yaplakal.com/members/member{}.html", "category": "Блоги"},
    "JoyReactor": {"url": "https://joyreactor.cc/user/{}", "category": "Блоги"},
    "4pda": {"url": "https://4pda.to/forum/index.php?showuser={}", "category": "Блоги"},
    "Sports.ru": {"url": "https://www.sports.ru/profile/{}/", "category": "Стиль жизни"},
    "Kinopoisk": {"url": "https://www.kinopoisk.ru/user/{}/", "category": "Медиа"},
    "LiveInternet": {"url": "https://www.liveinternet.ru/users/{}", "category": "Блоги"},
}

def generate_breach_intel(username):
    """Генерация потенциальных email и прямых ссылок на базы утечек"""
    emails = [f"{username}@gmail.com", f"{username}@yandex.ru", f"{username}@mail.ru"]
    breach_dbs = [
        {"name": "IntelligenceX", "url": f"https://intelx.io/?s={username}"},
        {"name": "DeHashed", "url": f"https://dehashed.com/search?query={username}"},
        {"name": "LeakCheck", "url": f"https://leakcheck.io/search?query={username}"}
    ]
    return emails, breach_dbs

def generate_mutations(username):
    """Структурная генерация реальных алиасов (без мусора)"""
    m = set()
    base = username.lower().strip()
    
    if len(base) > 8:
        for i in [5, 6, 7]:
            p1, p2 = base[:i], base[i:]
            m.update([f"{p1}_{p2}", f"{p1}.{p2}", f"{p1[0]}{p2}", f"{p2}{p1}"])
            
    for suf in ['_ru', 'bot', 'live', 'tv', 'page', 'blog']:
        m.add(f"{base}{suf}")

    no_nums = ''.join([c for c in base if not c.isdigit()])
    if no_nums != base and len(no_nums) > 3:
        m.add(no_nums)

    if len(base) > 6:
        m.add(base[:6])

    m.discard(base)
    return sorted(list(m), key=len)[:16]

def extract_metadata(img_bytes):
    img_bytes.seek(0)
    tags = exifread.process_file(img_bytes)
    return {str(tag): str(val) for tag, val in tags.items() if tag not in ('JPEGThumbnail')}

def check_site(name, site_info, username):
    url = site_info["url"].format(username)
    cat = site_info["category"]
    try:
        if name == "GitHub":
            api_res = requests.get(f"https://api.github.com/users/{username}", headers=HEADERS, timeout=5)
            if api_res.status_code == 200:
                return {"site": name, "url": f"https://github.com/{username}", "avatar": api_res.json().get("avatar_url"), "category": cat}
            return None
        
        if name == "Reddit":
            api_res = requests.get(f"https://www.reddit.com/user/{username}/about.json", headers=HEADERS, timeout=5)
            if api_res.status_code == 200 and "error" not in api_res.json():
                return {"site": name, "url": f"https://reddit.com/user/{username}", "avatar": api_res.json().get("data", {}).get("icon_img", "").split("?")[0], "category": cat}
            return None

        if name == "SoundCloud":
            res = requests.get(url, headers=HEADERS, timeout=8, allow_redirects=False)
            if res.status_code == 200 and "we can't find that user" not in res.text.lower():
                return {"site": name, "url": url, "avatar": None, "category": cat}
            return None

        if name == "VK":
            res = requests.get(url, headers=HEADERS, timeout=8, allow_redirects=True)
            if res.status_code == 200 and "login" not in res.url:
                text = res.text.lower()
                if "страница не найдена" not in text and ("owner_id" in text or username.lower() in text):
                    soup = BeautifulSoup(res.text, 'html.parser')
                    meta_img = soup.find("meta", property="og:image")
                    avatar = meta_img.get("content") if meta_img and "camera" not in meta_img.get("content") else None
                    return {"site": name, "url": f"https://vk.com/{username}", "avatar": avatar, "category": cat}
            return None

        if name == "TikTok":
            res = requests.get(url, headers=HEADERS, timeout=8)
            if res.status_code == 200 and "not found" not in res.text.lower() and username.lower() in res.text.lower():
                soup = BeautifulSoup(res.text, 'html.parser')
                img = soup.find("img", alt=lambda x: x and username.lower() in x.lower())
                return {"site": name, "url": f"https://www.tiktok.com/@{username}", "avatar": img.get("src") if img else None, "category": cat}
            return None

        res = requests.get(url, headers=HEADERS, timeout=8, allow_redirects=True)
        if res.status_code == 200:
            text = res.text.lower()
            not_found = ["404", "not found", "профиль не найден", "такого пользователя нет", "страница не найдена"]
            if any(s in text for s in not_found): return None
            
            soup = BeautifulSoup(res.text, 'html.parser')
            meta_img = soup.find("meta", property="og:image")
            return {"site": name, "url": url, "avatar": meta_img.get("content") if meta_img else None, "category": cat}
    except: pass
    return None

st.title("🛡️ TraceAnalyzer: Cyber Forensics & OSINT")

with st.sidebar:
    st.header("Конфигурация поиска")
    target_user = st.text_input("Идентификатор (Username)", value="kostyazavorotny")
    run_btn = st.button("АКТИВИРОВАТЬ СКАНИРОВАНИЕ")
    st.divider()
    uploaded_file = st.file_uploader("EXIF-анализ локального файла", type=["jpg", "jpeg", "png"])

if run_btn:
    st.header(f"🕵️ Цифровой след объекта: {target_user}")
    
    with st.spinner('Синхронизация с базами данных...'):
        results = []
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(check_site, n, i, target_user) for n, i in SITES.items()]
            for f in futures:
                r = f.result()
                if r: results.append(r)

    found_names = [r['site'] for r in results]
    not_found_names = [name for name in SITES.keys() if name not in found_names]

    if results:
        st.subheader("🌐 Обнаруженные профили")
        for acc in results:
            st.markdown(f"✅ **{acc['site']}**: [{acc['url']}]({acc['url']})")

        st.divider()
        st.subheader("⚠️ Проверка компрометации (Data Breach OSINT)")
        emails, breach_dbs = generate_breach_intel(target_user)
        
        col_em, col_db = st.columns(2)
        with col_em:
            st.error("📧 Потенциальные Email-адреса")
            for em in emails:
                st.markdown(f"`{em}` ➔ [Проверить в HIBP](https://haveibeenpwned.com/account/{em})")
        with col_db:
            st.warning("🔎 Прямой поиск по базам")
            for db in breach_dbs:
                st.markdown(f"🔗 **{db['name']}**: [Перейти к поиску]({db['url']})")

        st.divider()
        st.subheader("🕸️ Векторный граф категорий")
        df_g = pd.DataFrame([{"Узел": target_user, "Сфера": r["category"], "Ресурс": r["site"]} for r in results])
        fig = px.sunburst(df_g, path=['Узел', 'Сфера', 'Ресурс'], color='Сфера', color_discrete_sequence=px.colors.qualitative.Pastel)
        st.plotly_chart(fig, use_container_width=True)

        st.divider()
        st.subheader("🧬 Структурный анализ алиасов (Мутации)")
        st.write("Логические перестановки частей никнейма и платформенные суффиксы:")
        
        mutations = generate_mutations(target_user)
        cols_mut = st.columns(4) 
        for idx, mut in enumerate(mutations):
            cols_mut[idx % 4].code(mut, language="text")

        st.divider()
        st.subheader("🖼️ Форензика медиа-артефактов")
        cols = st.columns(3)
        for i, acc in enumerate(results):
            with cols[i % 3]:
                if acc['avatar']:
                    st.write(f"**{acc['site']}**")
                    st.caption(f"[🔗 Исходный файл]({acc['avatar']})")
                    try:
                        img_res = requests.get(acc['avatar'], headers={"User-Agent": "Mozilla/5.0"}, timeout=8)
                        if 'image' in img_res.headers.get('Content-Type', '').lower() or 'octet-stream' in img_res.headers.get('Content-Type', '').lower():
                            img_b = BytesIO(img_res.content)
                            st.image(img_b, use_column_width=True)
                            meta = extract_metadata(img_b)
                            if meta:
                                with st.expander("Показать EXIF"): st.write(meta)
                            else: st.caption("Метаданные очищены.")
                        else:
                            st.warning("Защита CDN.")
                    except: st.error("Таймаут соединения.")
                else:
                    st.info(f"{acc['site']}: Аватар скрыт.")
    else:
        st.error("Пользователь не обнаружен.")

    st.divider()
    st.subheader("📂 Ресурсы без обнаруженных следов")
    if not_found_names:
        st.write("На следующих ресурсах профиль не найден или доступ ограничен:")
        st.info(", ".join(not_found_names))
    else:
        st.write("Профиль обнаружен на всех исследованных ресурсах.")

if uploaded_file:
    st.divider()
    st.subheader("📎 Локальная EXIF форензика")
    st.image(Image.open(uploaded_file), width=300)
    manual_meta = extract_metadata(uploaded_file)
    if manual_meta:
        st.write(manual_meta)
    else:
        st.warning("В данном файле EXIF данные отсутствуют.")
