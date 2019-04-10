# -*- coding: utf-8 -*-

# ------- imports -------
from datetime import datetime, timedelta
from telegraph import Telegraph
from bs4 import BeautifulSoup
import feedparser
import requests
import telegram
import time
import sys
import re

# ------- Global variables -------
DAY = str(datetime.date(datetime.now()))
DB = {}
VISITED = {}
CHAT_ID = -0    # int, channel ID
RAGHAV_ID = 0   # int, account ID
TOKEN = 'token of a bot'
BOT = telegram.Bot(TOKEN)
TELEGRAPH = Telegraph()
TELEGRAPH_ACC = TELEGRAPH.create_account(short_name='ieFeedBot')
TOMORROW = ['front_page', 'editorials', 'opinion']
LINKS = {
    'front_page': 'https://indianexpress.com/print/front-page/feed/',
    'lifestyle': 'https://indianexpress.com/section/lifestyle/feed/',
    'health': 'https://indianexpress.com/section/lifestyle/health/feed/',
    'science_tech': 'https://indianexpress.com/section/technology/feed/',
    'cricket': 'https://indianexpress.com/section/sports/cricket/feed/',
    'hockey': 'https://indianexpress.com/section/sports/hockey/feed/',
    'india': 'https://indianexpress.com/section/india/feed/',
    'world': 'https://indianexpress.com/section/world/feed/',
    'eye': 'https://indianexpress.com/print/eye/feed/',
    'editorials': 'https://indianexpress.com/section/opinion/editorials/feed/',
    'opinion': 'https://indianexpress.com/section/opinion/feed/',
    # 'politics': 'https://indianexpress.com/section/india/politics/feed/',
    # 'sports': 'https://indianexpress.com/section/sports/feed/',
}


# ------- Finds if DAY is new day or'nt -------
def new_day():
    if DAY != str(datetime.date(datetime.now())):
        report_me(f'*new_day() returns True:* ```DAY```')
        return True
    return False


# ------- Create telegra.ph article -------
def create_tgph(entry):
    prse = entry['id']
    response = requests.get(prse).text
    soup = BeautifulSoup(response, 'html.parser')

    try:
        thumb = f"<img src='{entry['media_thumbnail'][0]['url']}'>"
    except Exception as e:
        thumb = ''
    content = f'<strong><a href="{prse}">Indian Express</a> |</strong> {time.strftime("%b %d, %Y %l:%M %p")}<br><br>{thumb}'
    content += ''.join(map(lambda element: f'<p>{element.text}</p>', soup.findAll('p')[1:-2]))

    try:
        tgph = TELEGRAPH.create_page(
            entry.title,
            html_content=content,
            author_name='IE Feed Bot',
            author_url='https://t.me/ieFeedBot',
        )
    except Exception as e:
        report_me(f'⚠️ *ERROR:* ```{err[0]}```.\n\n *Content:* \n ```{content}```')

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
            if entry_id not in VISITED[link_key]:
                print(f"{datetime.now().strftime('%I:%M %p')} | {entry.title[:50]}")
                tgph_link = create_tgph(entry)
                content = f"\n\n〈{datetime.now().strftime('%I:%M %p')}〉 ⟶ [{entry.title}]({tgph_link})"
                try:
                    DB[link_key] = DB[link_key].edit_text(DB[link_key].text_markdown + content, parse_mode=telegram.ParseMode.MARKDOWN, disable_web_page_preview=True,)
                    VISITED[link_key].append(entry_id)
                except Exception as e:
                    print('Error in editing', e)
                    time.sleep(30)
    print('Exiting rss()')


# ------- Called once in a day -------
def new_message():
    for key in LINKS:
        while True:
            try:
                msg_obj = BOT.send_message(CHAT_ID, f'#{key}', disable_notification=True)
                DB[key] = msg_obj
                VISITED[key] = []
                break
            except Exception as e:
                print(e)
                time.sleep(30)
    global DAY
    DAY = str(datetime.date(datetime.now()))


# ------- Report error or messages to me -------
def report_me(msg):
    BOT.send_message(RAGHAV_ID, msg, parse_mode=telegram.ParseMode.MARKDOWN)


# ------- Calling Functions -------
try:
    new_message()
    report_me(f'*AUTH_URL* ⟶ {TELEGRAPH_ACC["auth_url"]}')
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
            err = sys.exc_info()
            report_me(f'⚠️ *ERROR:* ```{err[0]}``` _at line number_ ```{err[2].tb_lineno}```')
        except Exception as e:
            pass
        print(e)
        time.sleep(30 * 60)
