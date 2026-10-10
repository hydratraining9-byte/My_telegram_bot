import os
import asyncio
from pyrogram import Client, filters
from pyrogram.types import ChatMemberUpdated, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from py_tgcalls import PyTgCalls
from py_tgcalls.types import AudioPiped
import yt_dlp

API_ID = int(os.environ.get("API_ID", "39898677"))
API_HASH = os.environ.get("API_HASH", "ecc862416723402ae18ef3d45e1d2dc9")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8745896947:AAGlhXv6tC3X92ft_2TFFAaxuefJr9QjDBY")
OWNER_ID = int(os.environ.get("OWNER_ID", "7677244398"))

app = Client(
    "media_broadcast_vc_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

call_py = PyTgCalls(app)
saved_groups = set()

@app.on_message(filters.command("start"))
def start_command(client, message):
    message.reply(
        "မင်္ဂလာပါ Owner! 🚀\n\n"
        "• **DM ပို့ပါက:** ဂရုများသို့ ဖြန့်ဝေရန် Broadcast Button ပေါ်လာမည်။\n"
        "• **Group Voice Chat တွင်:** `/play [သီချင်းနာမည် သို့မဟုတ် Link]` ဖြင့် သီချင်းဖွင့်နိုင်ပါသည်။"
    )

@app.on_chat_member_updated()
def auto_save_group(client, chat_member: ChatMemberUpdated):
    chat_id = chat_member.chat.id
    new_status = chat_member.new_chat_member.status if chat_member.new_chat_member else None
    if new_status in ["administrator", "creator"]:
        saved_groups.add(chat_id)
    elif new_status in ["left", "banned", "member"]:
        if chat_id in saved_groups:
            saved_groups.remove(chat_id)

@app.on_message(filters.private & filters.user(OWNER_ID) & ~filters.command(["start", "play", "stop"]))
def owner_post_preview(client, message):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🚀 ဤပိုစ့်ကို ဂရုများသို့ ဖြန့်မည်", callback_data="confirm_broadcast")]
    ])
    message.reply("အောက်ပါ ပိုစ့်ကို ဂရုများသို့ ဖြန့်ဝေရန် အသင့်ဖြစ်ပါပြီ။ ခလုတ်ကို နှိပ်ပါ။ 👇", reply_markup=keyboard)

@app.on_callback_query(filters.regex("confirm_broadcast") & filters.user(OWNER_ID))
def execute_broadcast(client, callback_query: CallbackQuery):
    original_message = callback_query.message.reply_to_message
    if not original_message:
        callback_query.answer("❌ ဖြန့်ဝေမည့် ပိုစ့်ကို ရှမတွေ့ပါ။", show_alert=True)
        return
    callback_query.answer("⏳ ဂရုများသို့ စတင် ဖြန့်ဝေနေပါပြီ...")
    success_count = 0
    for target_id in saved_groups:
        try:
            original_message.copy(chat_id=target_id)
            success_count += 1
        except Exception:
            pass
    callback_query.message.edit_text(f"✅ **ဖြန့်ဝေမှု ပြီးဆုံးပါပြီ!**\n• ပို့ဆောင်နိုင်သော ဂရုအရေအတွက်: {success_count}")

def get_audio_url(query):
    ydl_opts = {'format': 'bestaudio', 'noplaylist': True}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        if "http" not in query:
            query = f"ytsearch:{query}"
        info = ydl.extract_info(query, download=False)
        if 'entries' in info:
            info = info['entries'][0]
        return info['url'], info.get('title', 'Audio')

@app.on_message(filters.command("play") & filters.group)
async def play_music(client, message):
    if len(message.command) < 2:
        await message.reply("❌ ကျေးဇူးပြု၍ သီချင်းနာမည် (သို့) Link ထည့်ပါ။ ဥပမာ: `/play Shape of you`")
        return
    
    query = " ".join(message.command[1:])
    chat_id = message.chat.id
    m = await message.reply("🔎 သီချင်း ရှာဖွေနေပါပြီ...")
    
    try:
        url, title = await asyncio.get_event_loop().run_in_executor(None, get_audio_url, query)
        await call_py.join_group_call(
            chat_id,
            AudioPiped(url)
        )
        await m.edit_text(f"🎶 **Voice Chat တွင် စတင်ဖွင့်နေပါပြီ:**\n• `{title}`")
    except Exception as e:
        await m.edit_text(f"❌ အမှားအယွင်း ဖြစ်ပေါ်သွားပါသည်: `{e}`")

@app.on_message(filters.command("stop") & filters.group)
async def stop_music(client, message):
    chat_id = message.chat.id
    try:
        await call_py.leave_group_call(chat_id)
        await message.reply("⏹ Voice Chat ကို ရပ်တန့်ပြီး Bot ထွက်ခွာသွားပါပြီ။")
    except Exception as e:
        await message.reply(f"❌ Error: `{e}`")

async def main():
    await app.start()
    await call_py.start()
    print("Bot နှင့် PyTgCalls အောင်မြင်စွာ စတင် పనిచేနေပါပြီ...")
    await asyncio.gather(asyncio.Event().wait())

if __name__ == "__main__":
    asyncio.run(main())
  
