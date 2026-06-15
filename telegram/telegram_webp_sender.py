import asyncio
from telegram import Bot

# Initialize Telegram Bot
bot = Bot(token='7329071416:AAHy70lpiWdaSFsAClpZPQPR7WkERjnzMrY')

async def send_sticker_to_telegram():
    # If you have the sticker file
    with open('divider.webp', 'rb') as sticker:
        await bot.send_sticker(chat_id='49487552', sticker=sticker)

    # If you have the sticker file ID (uncomment the following lines)
    # sticker_file_id = 'CAACAgIAAxkBAAEBMyBgggV11FhgggfgggY1N3Z7JX_oQAACAgADggg2AACyRgY1UeAzSUYHgQ'
    # await bot.send_sticker(chat_id='49487552', sticker=sticker_file_id)

if __name__ == '__main__':
    asyncio.run(send_sticker_to_telegram())
