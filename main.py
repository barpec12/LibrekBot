# Python libraries that we need to import for our bot
import config

import asyncio
import random
import string
import threading
import inspect
import json
import requests
from hashlib import sha1

from flask import request
from pymessenger.bot import Bot

from librus_tricks import create_session

from librekbot import app, db
from librekbot.models import Recipient, SentAnnouncement

bot = Bot(config.access_token)

# When Librus and Synergia accounts have diffrent passwords
# session = SynergiaClient(authorizer('MAIL', 'HASLOLIBRUS')[0], synergia_user_passwd='HASLOSYNERGIA')
session = create_session(config.login, config.password)


# We will receive messages that Facebook sends our bot at this endpoint 
@app.route("/", methods=['GET', 'POST'])
def receive_message():
    if request.method == 'GET':
        """Before allowing people to message your bot, Facebook has implemented a verify token
        that confirms all requests that your bot receives came from Facebook."""
        token_sent = request.args.get("hub.verify_token")
        return verify_fb_token(token_sent)
    # if the request was not get, it must be POST and we can just proceed with sending a message back to user
    else:
        # get whatever message a user sent the bot
        output = request.get_json()
        # if(not session.user.is_valid):
        # session.user.revalidate_user()
        for event in output['entry']:
            messaging = event['messaging']
            for message in messaging:
                # print("wiadomosc")
                # print(repr(message))
                if message.get('postback'):
                    received_payload = message['postback']['payload']
                    if received_payload == 'pressed_start_button':
                        recipient_id = message['sender']['id']
                        greetings_message = """
                        Hej! Jestem Librekbot.
                        Staram się sprawić, abyś otrzymywał szkolne ogłoszenia jak najszybciej!
                        Napisz "pomoc", aby dowiedzieć się, jak mnie używać!
                        """
                        send_message_multiline(recipient_id, greetings_message)
                if message.get('policy-enforcement'):
                    msg = message['policy-enforcement']
                    print(config.developer_id, msg['action'] + " " + msg['reason'])
                    send_message(config.developer_id, msg['action'] + " " + msg['reason'])
                if message.get('message'):
                    # print("istnieje")
                    # Facebook Messenger ID for user so we know where to send response back to
                    recipient_id = message['sender']['id']
                    if message['message'].get('text'):
                        msg = message['message']['text']
                        sent_by_admin = recipient_id == config.developer_id

                        if "odsubskrybuj" in msg.lower():
                            db.session.query(Recipient).filter(Recipient.fb_id == recipient_id).delete()
                            db.session.commit()
                            send_message(recipient_id, "Pomyślnie usunięto z listy!")
                        elif "subskrybuj" in msg.lower():
                            student_class = ""
                            splitted = msg.lower().split("subskrybuj ")
                            if len(splitted) > 1:
                                if len(splitted[1]) == 2:
                                    student_class = splitted[1]
                            row = Recipient.query.filter_by(fb_id=recipient_id).first()
                            if not row:
                                db.session.add(Recipient(fb_id=recipient_id, student_class=student_class))
                                db.session.commit()
                                send_message(recipient_id, "Pomyślnie dodano do listy!")
                                if len(student_class) == 2:
                                    send_message(recipient_id, "Będziesz teraz otrzymywać powiadomienia dla klasy "
                                                 + student_class + ".")
                            else:
                                # TODO allow changing class
                                # if not row.student_class.lower() == student_class:
                                #
                                # else:
                                send_message(recipient_id, "Jestes juz dodany do listy!")
                            print("wyslalem")
                        # elif(msg.lower() == "wszystkie_zmiany"):
                        # for news in session.news_feed():
                        # send_message(recipient_id, f'{news.content}')
                        elif (msg.lower().replace('!', '').replace('.', '') in ['ostatnie zmiany', 'zmiany',
                                                                                'last changes', 'ostatnie ogłoszenia',
                                                                                'changes'] or "zmiany" in msg.lower() or "ogłoszenia" in msg.lower()):
                            newslist = session.news_feed()
                            send_message(recipient_id, "Jasne! Już przesyłam ostatnie dwa ogłoszenia")
                            # TODO do this with for loop
                            news_count = 2
                            for index in range(news_count):
                                article = newslist[::-1][index]  # goes backwards
                                send_message(recipient_id, article.content)
                                if sent_by_admin:
                                    send_message(recipient_id, article.unique_id)

                        elif (msg.lower().replace('!', '').replace('.', '') in ['cześć', 'witaj', 'czesc', 'hi',
                                                                                'hello', 'hej', 'siema',
                                                                                'good morning', 'greetings']):
                            greetings_message = """
                            No Hej!
                            """
                            send_message_multiline(recipient_id, greetings_message)

                        elif (msg.lower().replace('!', '').replace('.', '') in ['pomoc', 'help']):
                            help_message = """
                            Jeśli chcesz mnie spytać o ostatnie zmiany w planie, napisz:
                            "ostatnie zmiany"
                            Jeśli chciałbyś dowiadywać się regularnie o zmianach w planie, wpisz:
                            "subskrybuj" lub "subskrybuj KLASA", np. "subskrybuj 3F"
                            Dzięki wpisaniu klasy będziesz otrzymywać tylko te zmiany, które się do niej odnoszą.
                            Możesz też zrezygnować z otrzymywania zmian, wpisując:
                            "odsubskrybuj"
                            Jeśli chcesz poznać mojego autora i pomóc w ulepszaniu mnie, napisz "autor".
                            """
                            send_message_multiline(recipient_id, help_message)

                        elif (msg.lower().replace('!', '').replace('.', '') in ['info', 'informacje', 'author',
                                                                                'autor']):
                            author_message = """
                            Zostałem stworzony przez barpec12.
                            Możesz zamieszczać sugestie odnośnie mojego działania!
                            Stwórz issue na https://github.com/barpec12/LibrekBot.
                            Jeśli potrafisz programować, Ty też możesz mnie ulepszyć! :)
                            """
                            send_message_multiline(recipient_id, author_message)
                        elif (msg.lower().replace('!', '').replace('.', '') in ['dzięki', 'dzieki', 'dziekuje',
                                                                                'dziękuję', 'thanks', 'thank\'s',
                                                                                'thank you']):
                            wiad = random.choice(["Zawsze do usług!", "Nie ma sprawy", "Miło było Ci pomóc!"])
                            send_message(recipient_id, wiad)
                        elif (msg.lower().replace('!', '').replace('.', '') in ['bye', 'do zobaczenia', 'goodbye',
                                                                                'see ya', 'see ya later', 'dobranoc',
                                                                                'good night']):
                            wiad = random.choice(["Zawsze do usług!", "Nie ma sprawy!", "Miło było Ci pomóc!"])
                            send_message(recipient_id, wiad)

                        elif "sendtoall " in msg and sent_by_admin:
                            mess = msg.split("sendtoall ")[1]
                            for recipient in Recipient.query.all():
                                send_message(recipient.fb_id, mess)

                        elif "sendme " in msg and sent_by_admin:
                            mess = msg.split("sendme ")[1]
                            send_message(recipient_id, mess)

                        elif "sendmeann " in msg and sent_by_admin:
                            aid = msg.split("sendmeann ")[1]
                            for news in session.news_feed():
                                if news.unique_id == aid:
                                    send_message(recipient_id, f'{news.content}')

                        elif "sendmefann " in msg and sent_by_admin:
                            aid = msg.split("sendmefann ")[1]
                            for news in session.news_feed():
                                if news.unique_id == aid:
                                    send_message(recipient_id, f'{filter_message(news.content, "3F")}')
                        else:
                            first = random.choice(
                                ["Niestety, ale tym razem nie udało mi się zrozumieć Twojej wiadomości.",
                                 "Nie wiem, jak Ci odpowiedzieć, może spróbujesz czegoś innego?",
                                 "Nie zrozumiałem Cię, czy możesz napisać inaczej?"])
                            send_message(recipient_id, first)
                            send_message(recipient_id, "Możesz mnie spytać o ostatnie zmiany w planie, pisząc:")
                            send_message(recipient_id, "\"ostatnie zmiany\"")
                            send_message(recipient_id,
                                         "Możesz też napisać \"pomoc\", aby poznać resztę moich możliwości!")
                            # send_message(recipient_id,newslist[-3])
                    # if user sends us a GIF, photo,video, or any other non-text item
                    if message['message'].get('attachments'):
                        response_sent_nontext = get_message()
                        send_message(recipient_id, response_sent_nontext)
    return "Message Processed"


def verify_fb_token(token_sent):
    # take token sent by facebook and verify it matches the verify token you sent
    # if they match, allow the request, else return an error
    if token_sent == config.verify_token:
        return request.args.get("hub.challenge")
    return 'Invalid verification token'


# chooses a random message to send to the user
def get_message():
    sample_responses = ["Ale fajna fota!", "Jestem z Ciebie dumny.", "Dawaj więcej!", "Wow!"]
    # return selected item to the user
    return random.choice(sample_responses)


# calls send_message for each line of text
def send_message_multiline(recipient_id, message):
    message = inspect.cleandoc(message)  # fixes the doc-string indent issue
    for line in message.split('\n'):
        send_message(recipient_id, line)


# uses PyMessenger to send response to user
def send_message(recipient_id, response):
    # sends user the text message provided via input response parameter
    n = 2000
    msgs = [response[i:i + n] for i in range(0, len(response), n)]
    for msg in msgs:

        bot.send_text_message(recipient_id, msg)
    return "success"


# sends subscription message (outside 24h window)
def send_sub_message(recipient_id, response):
    n = 2000
    msgs = [response[i:i + n] for i in range(0, len(response), n)]
    for msg in msgs:
        payload = {
            'recipient': {
                'id': recipient_id
            },
            'message': {
                'text': msg
            },
            "tag": "CONFIRMED_EVENT_UPDATE"
        }
        bot.send_raw(payload)
    return "success"


in_error = False


@asyncio.coroutine
async def send_new_messages():
    global in_error
    while True:
        # if(not session.user.is_valid):
        # session.user.revalidate_user()
        try:
            for news in session.news_feed():
                old_text = ""
                news_content = news.content.encode('utf-8')
                checksum = sha1(news.content.encode('utf-8')).hexdigest()
                if not SentAnnouncement.query.filter_by(checksum=checksum).first():
                    found = SentAnnouncement.query.filter_by(unique_id=news.unique_id).first()
                    if found:
                        old_text = found.content
                        found.content = news_content
                        found.checksum = checksum
                    else:
                        db.session.add(SentAnnouncement(unique_id=news.unique_id, checksum=checksum,
                                                        content=news_content))
                    db.session.commit()
                    for recipient in Recipient.query.all():
                        message_filtered = filter_message(news.content, recipient.student_class)
                        old_filtered = filter_message(old_text, recipient.student_class)
                        if not old_filtered == message_filtered:
                            send_sub_message(recipient.fb_id, f'{message_filtered}')
                            print("do:" + str(recipient.fb_id))
            if in_error:
                send_sub_message(config.developer_id, 'Już działam!')
                in_error = False
            print("sprawdzilem")
        except Exception as e:
            if not in_error:
                send_sub_message(config.developer_id, 'Jakiś błąd - nie działam!')
                in_error = True
            print("blad - nie sprawdzilem")
            print(str(e))
        await asyncio.sleep(60 * config.update_interval)


def loop_in_thread(loop):
    asyncio.set_event_loop(loop)
    loop.run_until_complete(send_new_messages())


def filter_message(message, student_class):
    to_return = ""
    for line in message.split("\n"):
        other_class = False
        lowclass = student_class.lower()
        if (lowclass not in line.lower() and "wszyscy" not in line.lower()
                and "wszystkie" not in line.lower() and "każda" not in line.lower()):
            for i in range(1, 4):
                for letter in string.ascii_lowercase:
                    # do not filter 3l. Wszyscy zwolnieni
                    if letter == 'l':
                        continue
                    # 3f -> 3df
                    if str(i) == lowclass[0] and str(i) + letter + lowclass[1] in line.lower():
                        other_class = False
                        i = 4
                        break
                    if str(i) + letter in line.lower():
                        other_class = True
        if not other_class:
            to_return += line + "\n"
    return to_return


if __name__ == "__main__":
    headers = {'content-type': 'application/json'}
    payload = {'get_started': {'payload': 'pressed_start_button'}}
    requests.post('https://graph.facebook.com/v4.0/me/messenger_profile?access_token=' + config.access_token,
                      json=payload, headers=headers)
    send_message(config.developer_id, 'Włączyłem się!')
    loop = asyncio.get_event_loop()
    t = threading.Thread(target=loop_in_thread, args=(loop,))
    t.start()
    app.run(host='0.0.0.0')
