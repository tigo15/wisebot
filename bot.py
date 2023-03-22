import re
import config
import logging
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, types
from aiogram.utils import exceptions as tg_exc
from aiogram.types import ParseMode
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.filters.builtin import CommandStart
from aiogram.utils.exceptions import BadRequest
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean
from sqlalchemy.orm import sessionmaker, declarative_base
from aiogram import executor
from aiogram.types import ContentType, Message

# Set up logging
logging.basicConfig(level=logging.INFO)

# Create bot instance
bot = Bot(token=config.TOKEN)

# Create dispatcher instance
dp = Dispatcher(bot)

# Set up database connection
engine = create_engine('sqlite:///chatbot.db')
Session = sessionmaker(bind=engine)
Base = declarative_base()


# Define database model for banned users
class BannedUser(Base):
    __tablename__ = 'banned_users'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer)
    until_date = Column(DateTime)
    is_banned = Column(Boolean, default=True)


# Create tables
Base.metadata.create_all(engine)

# վերաակտիվացնում
@dp.message_handler(commands=['restart'])
async def restart(message: types.Message):
    if message.from_user.id == config.ADMIN_ID or message.from_user.id == config.MODER_ID:
        await message.answer(f'<a href="tg://user?id={message.from_user.id}">{message.from_user.first_name}</a>-նը թարմացրեց բոտին',  parse_mode='html')
    else:
        await message.reply("դուք չունեք հասանելիություն այս հրամանին")

# խոսքի զրկում
@dp.message_handler(commands=['mute'])
async def mute(message: types.Message):
    if message.from_user.id == config.ADMIN_ID or message.from_user.id == config.MODER_ID:
        name1 = message.from_user.get_mention(as_html=True)
        if not message.reply_to_message:
            await message.reply("Այս հրամանը պետք է լինի հաղորդագրության պատասխանը!")
            return
        try:
            muteint = int(message.text.split()[1])
            mutetype = message.text.split()[2]
            comment = " ".join(message.text.split()[3:])
        except IndexError:
            await message.reply('Բացակայում են արգումենտները:\nՕրինակ՝\n`/mute 1 ժ պատճառ`')
            return
        if mutetype == "ժ" or mutetype == "ժամ" or mutetype == "ժամաչափ":
            dt = datetime.now() + timedelta(hours=muteint)
            timestamp = dt.timestamp()
            await bot.restrict_chat_member(message.chat.id, message.reply_to_message.from_user.id, types.ChatPermissions(False), until_date = timestamp)
            await message.reply(f'| <b>Խախտող։</b> <a href="tg://user?id={message.reply_to_message.from_user.id}">{message.reply_to_message.from_user.first_name}</a>\n| <b>Պատժի ժամկետը։</b> {muteint} {mutetype}\n| <b>Պատճառը:</b> {comment}',  parse_mode='html')
        elif mutetype == "ր" or mutetype == "րոպե" or mutetype == "րոպեով":
            dt = datetime.now() + timedelta(minutes=muteint)
            timestamp = dt.timestamp()
            await bot.restrict_chat_member(message.chat.id, message.reply_to_message.from_user.id, types.ChatPermissions(False), until_date = timestamp)
            await message.reply(f'| <b>Խախտող։</b> <a href="tg://user?id={message.reply_to_message.from_user.id}">{message.reply_to_message.from_user.first_name}</a>\n| <b>Պատժի ժամկետը։</b> {muteint} {mutetype}\n| <b>Պատճառը:</b> {comment}',  parse_mode='html')
        elif mutetype == "օր" or mutetype == "օրով":
            dt = datetime.now() + timedelta(days=muteint)
            timestamp = dt.timestamp()
            await bot.restrict_chat_member(message.chat.id, message.reply_to_message.from_user.id, types.ChatPermissions(False), until_date = timestamp)
            await message.reply(f'| <b>Խախտող։</b> <a href="tg://user?id={message.reply_to_message.from_user.id}">{message.reply_to_message.from_user.first_name}</a>\n| <b>Պատժի ժամկետը։</b> {muteint} {mutetype}\n| <b>Պատճառը:</b> {comment}',  parse_mode='html')
    else:
        await message.reply("դուք չունեք հասանելիություն այս հրամանին")

# արգելափակել
@dp.message_handler(commands=['ban'])
async def ban_user(message: types.Message):
    if message.from_user.id == config.ADMIN_ID or message.from_user.id == config.MODER_ID:
        await message.answer(f"{message.text.split()[1]}-ն անդամն արգելափակվել է\nՊատճառը: {message.text.split()[2]}")
        await message.bot.ban_chat_member(message.chat.id, message.reply_to_message.from_user.id)
    else:
        await message.reply("դուք չունեք հասանելիություն այս հրամանին")


# հանել արգելափակումը
@dp.message_handler(commands=['unban'])
async def unban_user(message: types.Message):
    if message.from_user.id == config.ADMIN_ID or message.from_user.id == config.MODER_ID:
        await message.bot.unban_chat_member(message.chat.id, message.reply_to_message.from_user.id)
        await app.add_chat_members(message.chat.id, message.reply_to_message.from_user.id)
        await message.answer(f"{message.text.split()[1]}-ն անդամի արգելափակումը հավել է։")
    else:
        await message.reply("դուք չունեք հասանելիություն այս հրամանին:")


# հղումներ
@dp.message_handler()
async def filter_messages(message: types.Message):
    if config.LINK_REGEX.findall(message.text):
        await message.reply("Հղումները արգելված են!")
        await message.delete()

# արգելված բառացանկ
@dp.message_handler()
async def filter_messages(message: types.Message):
    lower_message = message.text.lower()
    for bad_word in config.BAD_WORDS:
        if bad_word in lower_message:
            await message.delete()
            await message.reply("Հեռևեք կանոններին!")
            break

# ողջույնի ուղերձ
@dp.message_handler(content_types=[ContentType.NEW_CHAT_MEMBERS])
async def new_members_handler(message: Message):
    new_member = message.new_chat_members[0]
    await bot.send_message(message.chat.id, f"Դիմաորեք {new_member.mention}-ին։")

#run long-polling
if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
