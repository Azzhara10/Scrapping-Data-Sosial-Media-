#import requests
#from bs4 import BeautifulSoup
#url = "https://news.dailysocial.id/"
#response = requests.get(url)
#soup = BeautifulSoup(response.text, "html.parser")
#title = soup.title

#print(title)

import requests
from bs4 import BeautifulSoup
import pandas as pd
import json
from urllib.parse import urljoin

# URL website
base_url = "https://news.dailysocial.id/"

# User-Agent
headers = {
    "User-Agent": "Mozilla/5.0"
}

session = requests.Session()
session.headers.update(headers)


# =========================
# Fungsi mengambil JSON-LD
# =========================
def get_jsonld(soup):
    data = []

    scripts = soup.find_all(
        "script",
        type="application/ld+json"
    )

    for script in scripts:
        try:
            obj = json.loads(script.get_text())

            if isinstance(obj, list):
                data.extend(obj)

            elif isinstance(obj, dict):
                data.append(obj)

                if "@graph" in obj:
                    if isinstance(obj["@graph"], list):
                        data.extend(obj["@graph"])

        except:
            pass

    return data


# =========================
# Fungsi mengambil author
# =========================
def get_author(author):
    if isinstance(author, dict):
        return author.get("name", "")

    if isinstance(author, list):
        names = []

        for item in author:
            if isinstance(item, dict):
                name = item.get("name", "")
            else:
                name = str(item)

            if name:
                names.append(name)

        return ", ".join(names)

    return str(author) if author else ""


# =========================
# Ambil link artikel
# =========================
response = session.get(
    base_url,
    timeout=15
)

soup = BeautifulSoup(
    response.text,
    "html.parser"
)

links = []

for a in soup.find_all("a", href=True):

    link = urljoin(
        base_url,
        a["href"]
    )

    # Hanya mengambil halaman artikel
    if "/post/" in link:

        if link not in links:
            links.append(link)


# Batasi jumlah artikel
links = links[:20]

print("Jumlah artikel:", len(links))


# =========================
# Scraping artikel
# =========================
data = []

for url in links:

    try:

        response = session.get(
            url,
            timeout=15
        )

        soup = BeautifulSoup(
            response.text,
            "html.parser"
        )

        # Nilai awal
        description = ""
        content = ""
        title = ""
        timestamp = ""
        created_at = ""
        user = ""


        # =========================
        # JSON-LD
        # =========================

        jsonld_data = get_jsonld(soup)

        article_data = None

        for item in jsonld_data:

            if isinstance(item, dict):

                item_type = item.get(
                    "@type",
                    ""
                )

                if isinstance(
                    item_type,
                    list
                ):
                    types = item_type
                else:
                    types = [item_type]

                if (
                    "Article" in types
                    or "NewsArticle" in types
                    or "BlogPosting" in types
                    or "headline" in item
                ):

                    article_data = item
                    break


        # =========================
        # Ambil data JSON-LD
        # =========================

        if article_data:

            title = article_data.get(
                "headline",
                article_data.get(
                    "name",
                    ""
                )
            )

            description = article_data.get(
                "description",
                ""
            )

            content = article_data.get(
                "articleBody",
                ""
            )

            timestamp = article_data.get(
                "datePublished",
                ""
            )

            created_at = article_data.get(
                "dateCreated",
                timestamp
            )

            user = get_author(
                article_data.get(
                    "author",
                    ""
                )
            )


        # =========================
        # TITLE
        # =========================

        if not title:

            tag = soup.find(
                "meta",
                property="og:title"
            )

            if tag:
                title = tag.get(
                    "content",
                    ""
                )

        if not title:

            h1 = soup.find("h1")

            if h1:
                title = h1.get_text(
                    " ",
                    strip=True
                )


        # =========================
        # DESCRIPTION
        # =========================

        if not description:

            tag = soup.find(
                "meta",
                property="og:description"
            )

            if tag:
                description = tag.get(
                    "content",
                    ""
                )

        if not description:

            tag = soup.find(
                "meta",
                attrs={
                    "name": "description"
                }
            )

            if tag:
                description = tag.get(
                    "content",
                    ""
                )


        # =========================
        # CONTENT
        # =========================

        if not content:

            content_tag = soup.select_one(
                ".entry-content, "
                ".post-content, "
                ".article-content, "
                ".article-body, "
                "article"
            )

            if content_tag:

                content = content_tag.get_text(
                    " ",
                    strip=True
                )


        # =========================
        # DESCRIPTION FALLBACK
        # =========================

        if not description and content:

            description = content[:150]

            if len(content) > 150:
                description += "..."


        # Batasi description
        # maksimal 150 karakter
        if description:

            if len(description) > 150:
                description = (
                    description[:150]
                    + "..."
                )


        # =========================
        # AUTHOR
        # =========================

        if not user:

            tag = soup.find(
                "meta",
                attrs={
                    "name": "author"
                }
            )

            if tag:
                user = tag.get(
                    "content",
                    ""
                )


        if not user:

            author_tag = soup.find(
                "a",
                rel="author"
            )

            if author_tag:
                user = author_tag.get_text(
                    " ",
                    strip=True
                )


        # =========================
        # TIMESTAMP
        # =========================

        if not timestamp:

            tag = soup.find(
                "meta",
                property="article:published_time"
            )

            if tag:
                timestamp = tag.get(
                    "content",
                    ""
                )


        if not timestamp:

            time_tag = soup.find("time")

            if time_tag:

                timestamp = time_tag.get(
                    "datetime",
                    time_tag.get_text(
                        strip=True
                    )
                )


        # =========================
        # CREATED AT
        # =========================

        if not created_at:

            created_at = timestamp


        # =========================
        # Simpan data
        # =========================

        data.append({

            "description": description,

            "content": content,

            "title": title,

            "timestamp": timestamp,

            "created_at": created_at,

            "user": user

        })


        print(
            "Berhasil:",
            title
        )


    except Exception as e:

        print(
            "Gagal:",
            url
        )

        print(e)


# =========================
# Buat DataFrame
# =========================

df = pd.DataFrame(
    data,
    columns=[
        "description",
        "content",
        "title",
        "timestamp",
        "created_at",
        "user"
    ]
)


# =========================
# Hapus data tanpa judul
# =========================

df = df[
    df["title"].notna()
    & (df["title"] != "")
]


# =========================
# Tampilkan hasil dalam tabel
# =========================

print("\n")
print("=" * 120)
print("HASIL SCRAPING DAILY SOCIAL")
print("=" * 120)

# Hanya menampilkan kolom ringkas
# agar tabel terminal tetap rapi
tabel = df[
    [
        "title",
        "timestamp",
        "created_at",
        "user",
        "description"
    ]
].copy()

print(
    tabel.to_string(
        index=False
    )
)

print("=" * 120)


# =========================
# Cek kelengkapan data
# =========================

print("\nKelengkapan data:")

print(
    df.notna().sum()
)


# =========================
# Simpan CSV
# =========================

df.to_csv(
    "dailysocial.csv",
    index=False,
    encoding="utf-8-sig"
)

print(
    "\nCSV berhasil dibuat: dailysocial.csv"
)
