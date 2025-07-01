from telethon.sync import TelegramClient
import json
import re
import os

api_id = 22367763
api_hash = "5cf7b52befeb13143c04c6ece4488de2"
channel_username = "uzmacbook"

client = TelegramClient("session", api_id, api_hash)

# Keywords to filter posts containing price info
keywords = ["narx", "narxi", "price"]

def contains_keywords(text):
    text_lower = text.lower()
    return any(k in text_lower for k in keywords)

def parse_product(text):
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    product = {
        "title": None,
        "cpu": None,
        "ram": None,
        "storage": None,
        "display": None,
        "battery": None,
        "warranty": None,
        "condition": None,
        "year": None,
        "included": None,
        "price": None,
        "other": [],
    }

    spec_keywords = [
        "cpu", "core", "ddr", "ram", "ssd", "hdd", "storage", "m2", "m3", "m1",
        "display", "batareka", "battery", "garantiya", "kafolat", "displey",
        "kafolat", "holati", "yili", "protsessor", "komplektda", "narx", "price"
    ]

    for i, line in enumerate(lines):
        if not any(sk in line.lower() for sk in spec_keywords):
            product["title"] = line
            lines = lines[i+1:]
            break
    else:
        product["title"] = lines[0]
        lines = lines[1:]

    patterns = {
        "price": re.compile(r"narx[i]?\s*[:\-]?\s*([\d\s,.$]+)|^([\d\s,.$]+)\s*\$$", re.I),
        "cpu": re.compile(r"(cpu|protsessor|core\s*i\d{1,2}|celeron|pentium|ryzen[\d\.]*|apple\s*m[123])\s*[:\-]?\s*(.+)", re.I),
        "ram": re.compile(r"(ddr\d|ram)\s*[:\-]?\s*([\d\s\w]+)", re.I),
        "storage": re.compile(r"(ssd|hdd|storage|m2|m3|xotira)\s*[:\-]?\s*([\d\s\w]+)", re.I),
        "display": re.compile(r"(display|displey|ekran)\s*[:\-]?\s*([\d\s\w,.]+)", re.I),
        "battery": re.compile(r"(battery|batareka)\s*[:\-]?\s*([\d\s\w,-]+)", re.I),
        "warranty": re.compile(r"(garantiya|kafolat)\s*[:\-]?\s*([\d\s\w-]+)", re.I),
        "condition": re.compile(r"holati\s*[:\-]?\s*(.+)", re.I),
        "year": re.compile(r"yili\s*[:\-]?\s*(\d{4})", re.I),
        "included": re.compile(r"komplektda\s*[:\-]?\s*(.+)", re.I),
    }

    apple_chip_match = re.search(r"(macbook\s*pro\s*m[123])", product["title"].lower())
    if apple_chip_match:
        product["cpu"] = apple_chip_match.group(1).upper()

    for line in lines:
        if product["price"] is None:
            price_match = re.match(r"^\s*([\d\s,.]+)\s*\$", line)
            if price_match:
                product["price"] = price_match.group(1).strip() + "$"
                continue

        for key, pattern in patterns.items():
            if product[key] is None:
                m = pattern.search(line)
                if m:
                    value = m.group(len(m.groups())) if len(m.groups()) > 1 else m.group(1)
                    if value:
                        product[key] = value.strip()
                    break
        else:
            product["other"].append(line)

    product["other"] = "\n".join(product["other"]) if product["other"] else None
    return product

# Ensure image folder exists
os.makedirs("images", exist_ok=True)

# Scrape
products = []

with client:
    print("✅ Connected! Fetching last 100 posts...\n")
    for msg in client.iter_messages(channel_username, limit=100):
        if msg.text and contains_keywords(msg.text):
            parsed = parse_product(msg.text)

            # Handle image download if photo exists
            photo_path = None
            if msg.photo:
                photo_path = f"images/{msg.id}.jpg"
                msg.download_media(file=photo_path)

            parsed.update({
                "id": msg.id,
                "date": str(msg.date),
                "raw_text": msg.text,
                "photo": photo_path
            })

            products.append(parsed)
            print(f"#{msg.id} - {parsed['title']} ({'📷 yes' if photo_path else 'no photo'})")

# Save to file
with open("products.json", "w", encoding="utf-8") as f:
    json.dump(products, f, ensure_ascii=False, indent=2)

print(f"\n💾 Saved {len(products)} products with photos to products.json")
