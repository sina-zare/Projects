from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext

bot_token = '6855445682:AAHaXmxpdSAiaKhjGBwshtdwZ2h1y6kmdA8'
bot = Bot(token=bot_token)

async def send_photo_to_telegram(update: Update, context: CallbackContext) -> None:
    # Send chart image to Telegram
    with open("C:\\Users\\sina.z\\Downloads\\img\\car.jpeg", 'rb') as photo:
        await bot.send_photo(chat_id='49487552', photo=photo)

async def start(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text('Hello! I am your bot.')

async def echo(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text(update.message.text)

def main():
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(bot_token).build()

    # on different commands - answer in Telegram
    application.add_handler(CommandHandler("start", start))

    # on non-command i.e message - echo the message on Telegram
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, send_photo_to_telegram))

    # Start the Bot
    application.run_polling()

if __name__ == '__main__':
    main()
