# -*- coding: utf-8 -*-

# ------- imports -------
from datetime import datetime, timedelta
from telegraph import Telegraph
from bs4 import BeautifulSoup
import feedparser
import requests
import telegram
import time
import re

# ------- Global variables -------
DAY = str(datetime.date(datetime.now()))
DB = {}
VISITED = {}
CHAT_ID = -0 # int, channel ID
RAGHAV_ID = 0 # int, account ID
TOKEN = 'token of a bot'
BOT = telegram.Bot(TOKEN)
TELEGRAPH = Telegraph()
TELEGRAPH_ACC = TELEGRAPH.create_account(short_name='ieFeedBot')
TOMORROW = ['front_page', 'eye', 'editorials', 'opinion', ]
LINKS = {
    'politics': 'https://indianexpress.com/section/india/politics/feed/',
    'front_page': 'https://indianexpress.com/print/front-page/feed/',
    'eye': 'https://indianexpress.com/print/eye/feed/',
    'india': 'https://indianexpress.com/section/india/feed/',
    'world': 'https://indianexpress.com/section/world/feed/',
    'editorials': 'https://indianexpress.com/section/opinion/editorials/feed/',
    'opinion': 'https://indianexpress.com/section/opinion/feed/',
    'cricket': 'https://indianexpress.com/section/sports/cricket/feed/',
    'sports': 'https://indianexpress.com/section/sports/feed/',
}


# ------- Finds if now() is new day or'nt -------
def new_day():
    if DAY != str(datetime.date(datetime.now())):
        return True
    return False


# ------- Create telegra.ph article -------
def create_tgph(entry):
    prse = entry['id']
    response = requests.get(prse).text
    soup = BeautifulSoup(response, 'html.parser')
    content = f'<strong><a href="{prse}">Source article</a></strong><br><br>'
    content += ''.join(map(lambda element: f'<p>{element.text}</p>', soup.findAll('p')[1:-2]))
    tgph = TELEGRAPH.create_page(
        entry.title,
        html_content=content,
        author_name='IE Feed Bot',
        author_url='https://t.me/ieFeedBot',
    )
    return f"https://telegra.ph/{tgph['path']}"


# ------- Insert new feeds(by editing the message) -------
def rss():
    global DAY
    DAY = str(datetime.date(datetime.now()))
    for link_key in LINKS:
        print('\n', '-' * 10, link_key, '-' * 10)
        xml = feedparser.parse(LINKS[link_key])

        for entry in xml.entries:
            entry_time = entry.published_parsed
            if time.strftime('%Y-%m-%d', entry_time) != str(datetime.date(datetime.now())):
                if link_key in TOMORROW and time.strftime('%Y-%m-%d', entry_time) == str(datetime.date(datetime.now() - timedelta(1))):
                    pass
                else:
                    break

            entry_id = int(re.split('&p=', entry['id'])[1])
            print(entry_id, entry.title)
            if entry_id not in VISITED[link_key]:
                tgph_link = create_tgph(entry)
                content = f"\n\n〈{datetime.now().strftime('%I:%M %p')}〉 ⟶ [{entry.title}]({tgph_link})"
                VISITED[link_key].append(entry_id)
                DB[link_key] = DB[link_key].edit_text(DB[link_key].text_markdown + content,
                                                      parse_mode=telegram.ParseMode.MARKDOWN,
                                                      disable_web_page_preview=True,)


# ------- Called once in a day at 00:0 -------
def new_message():
    global DB
    DB = {}
    for key in LINKS:
        msg_obj = BOT.send_message(CHAT_ID, f'#{key}', disable_notification=True)
        DB[key] = msg_obj
        VISITED[key] = []
    time.sleep(5 * 60)


# ------- Calling Functions -------
try:
    new_message()
except Exception as e:
    print(e)
while True:
    try:
        if new_day():
            new_message()
        elif DB != {}:
            rss()
            time.sleep(30 * 60)
    except Exception as e:
        try:
            BOT.send_message(RAGHAV_ID, f'⚠️ *ERROR:* ```{e}```', parse_mode=telegram.ParseMode.MARKDOWN)
        except Exception as e:
            pass
        print(e)
        time.sleep(30 * 60)
