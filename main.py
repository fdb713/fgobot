#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import re
import asyncio
import telepot
import requests
import json
from pyquery import PyQuery as q
from telepot.aio.loop import MessageLoop
from telepot.aio.delegate import pave_event_space, per_chat_id, create_open, include_callback_query_chat_id
from telepot.namedtuple import ReplyKeyboardMarkup, KeyboardButton
from telepot.namedtuple import InlineKeyboardMarkup, InlineKeyboardButton
from collections import OrderedDict
from configparser import ConfigParser

class Fgobot(telepot.aio.helper.ChatHandler):
    def __init__(self, *args, **kwargs):
        super(Fgobot, self).__init__(*args, **kwargs)
        self._count = 0
        self._servants = OrderedDict()
        self._message_with_inline_keyboard = None
        s_table = requests.get("https://www9.atwiki.jp/f_go/pages/671.html")
        q_table = q(s_table.content.decode("utf-8"))
        q_table = q_table("#wikibody table")
        t_list = list(q_table('tr').items())
        for i in t_list:
            sclass = q(i('td')[0]).text()
            if sclass:
                self._servants[sclass] = OrderedDict()
                for n, j in enumerate(i('td')[1:]):
                    t_list_tr_text = q(j).text()
                    if t_list_tr_text:
                        servants_text = ""
                        pqj = q(j)
                        for s in pqj('a'):
                            servants_text += "%s\nhttps:%s\n" % (q(s).text(), q(s).attr("href"))
                        self._servants[sclass][n] = servants_text

    async def on_chat_message(self, msg):
        # self._count += 1
        # await self.sender.sendMessage(self._count)
        content_type, chat_type, chat_id = telepot.glance(msg)
        if content_type == "text":
            msg = msg['text'].strip()
            reply, markup = self.reply_text(msg)
            if msg.startswith("/appmedia"):
                self._message_with_inline_keyboard = await self._bot.sendMessage(chat_id, reply, reply_markup=markup)
            else:
                await self._bot.sendMessage(chat_id, reply, reply_markup=markup)
        else:
            print(content_type)

    async def on_callback_query(self, msg):
        query_id, from_id, data = telepot.glance(msg, flavor='callback_query')
        print('Callback query:', query_id, from_id, data)
        if self._message_with_inline_keyboard:
            if data == "appmedia_ssr":
                rank_url = "https://appmedia.jp/fategrandorder/96261"
            if data == "appmedia_sr":
                rank_url = "https://appmedia.jp/fategrandorder/93558"

            r = requests.get(rank_url)
            if r.status_code == 200:
                rq = q(r.content.decode("utf-8"))
                tables = rq(".post-content > table[border='1']")
                table_rank = q((tables)[1])
                table_trs = table_rank("tr")[1:]
                reply = "%s\n" % rank_url
                for i in table_trs:
                    qi = q(i)
                    len_children = len(qi.children())
                    if len_children == 1:
                        reply += "\n%s\n" % qi.text()
                    if len_children == 3:
                        qic = qi("td")
                        qia = qi("a")
                        reply += "{} [{}]({})\n".format(q(qic[2]).text(), q(qic[0]).text(), qia.attr("href"))
            await self.sender.sendMessage(reply, parse_mode="Markdown")

    def reply_text(self, text):
        reply = "meow"
        markup = None
        if text.startswith("/appmedia"):
            reply = "Which ranking?"
            markup = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text='Appmedia SSR Ranking', callback_data='appmedia_ssr')],
                [InlineKeyboardButton(text='Appmedia SR Ranking', callback_data='appmedia_sr')]
            ])
        if text.startswith("/servant"):
            keyboards = []
            for i in self._servants.keys():
                keyboards.append([KeyboardButton(text="★{} {}".format(j, i)) for j in self._servants[i].keys()])
            markup = ReplyKeyboardMarkup(keyboard=keyboards, one_time_keyboard=True)

            # "Saber", "Archer", "Lancer", "Rider", "Caster", "Assassin", "Berserker", "Shielder", "Ruler", "Avenger", "MoonCancer", "AlterEgo", "Foreigner"
            reply = "Please choose class and rare"

        if text.startswith("★"):
            fgorare, fgoclass = text.split()
            fgorare = int(fgorare[1])
            reply = self._servants[fgoclass][fgorare]
        if text.startswith("/hougu"):
            reply = """
早见表
https://docs.google.com/spreadsheets/d/1ru35rHQ9DMsQcBXHPgUD5XDO-mSvR_j1fFTB_V507zw/htmlview

fc2 宝具計算
fgotouka.web.fc2.com
国人宝具計算
https://xianlechuanshuo.github.io/fgo2/calc4.html
            """
        if text.startswith("/drop"):
            reply = "FGO効率劇場\nhttps://docs.google.com/spreadsheets/d/1TrfSDteVZnjUPz68rKzuZWZdZZBLqw03FlvEToOvqH0/htmlview?sle=true#"
        if text.startswith("/wiki"):
            servant_name = " ".join(text.split()[1:])
            if servant_name:
                query_page_url = "https://www9.atwiki.jp/f_go/?cmd=wikisearch&keyword={}".format(servant_name)
                r = requests.get(query_page_url)
                if r.status_code == 200:
                    rq = q(r.content.decode("utf-8"))
                    links = rq("#wikibody li a")
                    filtered_links = [q(x) for x in links if not any(("コメント" in q(x).text(), "ボイス" in q(x).text(), "性能" in q(x).text()))][:10]
                    reply = ""
                    for i in filtered_links:
                        reply += "{}\nhttps:{}\n\n".format(i.html(), i.attr("href"))
                else:
                    reply = "connection timeout {}".format(r.status_code)
            else:
                reply = "https://www9.atwiki.jp/f_go/pages/671.html"

        if text.startswith("/price"):
            reply = "google: 9800 JPY = "
            google_finance_url = "https://finance.google.com/finance/converter?a={}&from={}&to={}".format(9800, "JPY", "CNY")
            result = requests.get(google_finance_url)
            if result.status_code == 200:
                rcontent = q(result.content)
                rcontent = rcontent("#currency_converter_result .bld").text()
                reply += rcontent
            jeanne_h5_url = "http://h5.m.taobao.com/awp/core/detail.htm?id=553971150031"
            reply += "\nJeanne {}".format(jeanne_h5_url)

            tu_jihua_url = "https://item.taobao.com/item.htm?spm=2013.1.w4023-16844942798.13.5692e503t594AU&id=558505049792"
            reply += "\n秃计划 {}".format(tu_jihua_url)

        if text.startswith("/gamewith"):
            reply = "https://gamewith.jp/fgo/article/show/62409"

        if text.startswith("/summon"):
            simulator_url = "https://konatasick.github.io/test_simulator/"
            simulator_js = "https://konatasick.github.io/test_simulator/js/index.js"
            reply = "Summon list\n%s\n\n" % simulator_url
            r = requests.get(simulator_js)
            if r.status_code == 200:
                rcontent = r.content.decode("utf-8")
                rcontent = rcontent.replace("\n", "")
                summon_json = re.findall('"sites"\:(.*)for', rcontent)[0].rstrip('}')
                summon_json = json.loads(summon_json)
                summon_json_last_ten = summon_json[::-1][:10]
                for i in summon_json_last_ten:
                    reply += "{} {}{}\n".format(i["name"], simulator_url, i["info"])

        if text.startswith("/help") or text.startswith("/start"):
            reply = """
Author: @fdb713
/appmedia - appmedia ranking
/drop - drop statistics
/gamewith - gamewith ranking link
/hougu - hougu damage quick reference
/price - compare JPY to CNY and 3rd-party charge
/servant - send link of servants by rare and class from atwiki
/summon - simulate summon
/wiki - search and send link of servant or other keywords on atwiki page
/help or /start - show this message
            """

        return reply, markup


if __name__ == '__main__':
    config = ConfigParser()
    config.read("config.ini")
    if "fgobot" in config:
        token = config["fgobot"].get("token")
    else:
        print("config syntax not correct")
        sys.exit(-1)

    bot = telepot.aio.DelegatorBot(token, [
        include_callback_query_chat_id(
            pave_event_space())(
                per_chat_id(), create_open, Fgobot, timeout=30),
    ])

    loop = asyncio.get_event_loop()
    loop.create_task(MessageLoop(bot).run_forever())
    print('Listening ...')

    loop.run_forever()
