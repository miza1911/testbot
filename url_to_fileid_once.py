import os, json, asyncio
from aiogram import Bot

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

# читаем ссылки из images.txt
with open("images.txt", "r", encoding="utf-8") as f:
    urls = [ln.strip() for ln in f if ln.strip()]

async def main():
    bot = Bot(BOT_TOKEN)
    mapping = {}
    for url in urls:
        try:
            msg = await bot.send_photo(CHAT_ID, url, caption=url)
            fid = msg.photo[-1].file_id
            mapping[url] = fid
            print("OK:", url, "->", fid)
        except Exception as e:
            print("ERR:", url, e)
    with open("url_fileid_map.json", "w", encoding="utf-8") as f:
        json.dump(mapping, f, ensure_ascii=False, indent=2)
    print("Saved", len(mapping), "items to url_fileid_map.json")

if __name__ == "__main__":
    asyncio.run(main())
