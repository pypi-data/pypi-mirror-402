import random
from plyer import notification
# from data.nagging import NAG_MESSAGES # OLD
from ..config import config

def send_alert(title, message):
    try:
        notification.notify(
            title=title,
            message=message,
            timeout=4
        )
    except:
        pass

def send_nag():
    try:
        # nag = random.choice(NAG_MESSAGES) # OLD
        nag = random.choice(config.nag_messages)
        message_title = nag["title"]
        message_body = nag["body"]
        notification.notify(
            title=message_title,
            message=message_body,
            timeout=4
        )
    except:
        pass