from telegram.ext import Updater, CommandHandler

def start(update, context):
    update.message.reply_text("Hi!")


while 1:

    try:
        updater = Updater(token='6678392405:AAFiEMELrZ0Ju0Pmva5bNL__gdY3D6B4LnI')
        dispatcher = updater.dispatcher

        start_handler = CommandHandler('start', start)
        dispatcher.add_handler(start_handler)

        updater.start_polling()
        updater.idle()
        print("ok")

    except:
        print("nokay")

#6678392405:AAFiEMELrZ0Ju0Pmva5bNL__gdY3D6B4LnI
