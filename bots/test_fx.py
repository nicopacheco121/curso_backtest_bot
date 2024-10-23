import alertas


def asdfasdf():
    x = 1
    pass


if __name__ == '__main__':
    print('hola')

    from keys_no_commit import BOT_TOKEN, CHAT_ID_LIST

    alertas.send_telegram_message(BOT_TOKEN, 'Hola', CHAT_ID_LIST)

