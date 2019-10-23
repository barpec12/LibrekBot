# Python libraries that we need to import for our bot
import config

import asyncio
import random
import string
import threading
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
                if message.get('message'):
                    # print("istnieje")
                    # Facebook Messenger ID for user so we know where to send response back to
                    recipient_id = message['sender']['id']
                    if message['message'].get('text'):
                        msg = message['message']['text']
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
                            send_message(recipient_id, f'{newslist[-1].content}')
                            send_message(recipient_id, f'{newslist[-2].content}')
                            if (recipient_id == config.developer_id):
                                send_message(recipient_id, f'{newslist[-1].unique_id}')
                                send_message(recipient_id, f'{newslist[-2].unique_id}')
                        elif (msg.lower().replace('!', '').replace('.', '') in ['cześć', 'witaj', 'czesc', 'hi',
                                                                                'hello', 'hej', 'siema',
                                                                                'good morning', 'greetings']):
                            send_message(recipient_id, "Hej! Jestem Librekbot.")
                            send_message(recipient_id, "Staram się sprawić, abyś otrzymywał szkolne ogłoszenia"
                                                       " jak najszybciej!")
                            send_message(recipient_id, "Napisz \"pomoc\", aby dowiedzieć się, jak mnie używać!")
                        elif (msg.lower().replace('!', '').replace('.', '') in ['pomoc', 'help']):
                            send_message(recipient_id, "Widzę, że jeszcze nie wiesz, jak mnie używać!")
                            send_message(recipient_id, "Mam nadzieję, że to Ci pomoże:")
                            send_message(recipient_id, "Jeśli chcesz mnie spytać o ostatnie zmiany w planie, napisz:")
                            send_message(recipient_id, "\"ostatnie zmiany\"")
                            send_message(recipient_id, "Jeśli chciałbyś dowiadywać się regularnie o zmianach w planie,"
                                                       " wpisz:")
                            send_message(recipient_id, "\"subskrybuj\" lub \"subskrybuj KLASA\", np. \"subskrybuj 3F\"")
                            send_message(recipient_id, "Dzięki wpisaniu klasy będziesz otrzymywać tylko te zmiany"
                                                       ", które się do niej odnoszą.")
                            send_message(recipient_id, "Możesz też zrezygnować z otrzymywania zmian, wpisując:")
                            send_message(recipient_id, "\"odsubskrybuj\"")

                        elif (msg.lower().replace('!', '').replace('.', '') in ['info', 'informacje', 'author', 'autor']):
                            send_message(recipient_id,
                                         "Zostałem stworzony przez barpec12, żebyś mógł łatwiej"
                                         " dowiedzieć się o zmianach w planie :)")
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
                        elif "sendtoall " in msg:
                            if recipient_id == config.developer_id:
                                mess = msg.split("sendtoall ")[1]
                                for recipient in Recipient.query.all():
                                    send_message(recipient.fb_id, mess)
                        elif "sendme " in msg:
                            if recipient_id == config.developer_id:
                                mess = msg.split("sendme ")[1]
                                send_message(recipient_id, mess)
                        elif "sendmeann " in msg:
                            if recipient_id == config.developer_id:
                                aid = msg.split("sendmeann ")[1]
                                for news in session.news_feed():
                                    if news.unique_id == aid:
                                        send_message(recipient_id, f'{news.content}')
                        elif "sendmefann " in msg:
                            if recipient_id == config.developer_id:
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


# uses PyMessenger to send response to user
def send_message(recipient_id, response):
    # sends user the text message provided via input response parameter
    n = 2000
    msgs = [response[i:i + n] for i in range(0, len(response), n)]
    for msg in msgs:
        bot.send_text_message(recipient_id, msg)
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
                        found.checksum = checksum
                    else:
                        db.session.add(SentAnnouncement(unique_id=news.unique_id, checksum=checksum,
                                                        content=news_content))
                    db.session.commit()
                    for recipient in Recipient.query.all():
                        message_filtered = filter_message(news.content, recipient.student_class)
                        old_filtered = filter_message(old_text, recipient.student_class)
                        if not old_filtered == message_filtered:
                            send_message(recipient.fb_id, f'{message_filtered}')
                            print("do:" + str(recipient.fb_id))
            if in_error:
                send_message(config.developer_id, 'Już działam!')
                in_error = False
            print("sprawdzilem")
        except Exception as e:
            if not in_error:
                send_message(config.developer_id, 'Jakiś błąd - nie działam!')
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
    send_message(config.developer_id, 'Włączyłem się!')
    loop = asyncio.get_event_loop()
    t = threading.Thread(target=loop_in_thread, args=(loop,))
    t.start()
    app.run(host='0.0.0.0')
