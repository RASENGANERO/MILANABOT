import logging
from aiogram import Bot, Dispatcher, executor, types
from aiogram.dispatcher import FSMContext
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.utils.exceptions import BotBlocked
import sqlite3
import time
import asyncio

storage = MemoryStorage()
bot = Bot(token="5912227264:AAEi6Y5322FqQmbKZ9LESgdzOMQuHUyvqNo")
dp = Dispatcher(bot,storage=storage)
logging.basicConfig(level=logging.INFO)
MESS=[]

class DelFilm(StatesGroup):
    id = State()

@dp.message_handler(state=DelFilm.id)
async def set_id_del_film(message: types.Message,state: FSMContext):
    await state.update_data(id=message.text)
    data = await state.get_data()
    data_answer = await del_film(str(data['id']).strip())
    await message.answer(data_answer)
    await state.finish()

async def del_film(id):
    conn = sqlite3.connect('milana_bot.db')
    cursor=conn.cursor()
    cursor.execute("SELECT *FROM films WHERE film_id=?",(id,))
    one_result = cursor.fetchone()
    send_res=''
    if one_result==None:
        send_res="Фильма с таким ID нет!"
    else:
        cursor.execute("DELETE FROM films WHERE film_id=?",(id,))
        conn.commit()
        send_res="Фильм с ID "+str(one_result[0])+"\n и названием: "+str(one_result[1])+"\n был удалён!"
    cursor.close()
    conn.close()
    return send_res


async def update_state_user(ids,type):
    conn = sqlite3.connect('milana_bot.db')
    cursor=conn.cursor()
    cursor.execute('''UPDATE users SET user_type =? WHERE id=?''',(type,ids))
    one_result = cursor.fetchone()
    conn.commit()
    cursor.close()
    conn.close()

async def gen_markup_user():
    markup = types.ReplyKeyboardMarkup(keyboard=[types.KeyboardButton("Пользователь"),types.KeyboardButton("Админ")],
                                       row_width=1,resize_keyboard=True)
    s1=types.KeyboardButton("Пользователь")
    s2=types.KeyboardButton("Админ")
    markup.add(s1)
    markup.add(s2)
    return markup

class AdminSet(StatesGroup):
    username=State()
    type_user=State()

@dp.message_handler(state=AdminSet.username)
async def set_name_film(message: types.Message, state: FSMContext):
    await state.update_data(username=str(message.text))
    await message.answer("Выберите тип для пользователя: "+str(message.text).split(" ----> ")[1],
                         reply_markup=await gen_markup_user())
    await AdminSet.type_user.set()
    


@dp.message_handler(state=AdminSet.type_user)
async def get_film(message: types.Message, state: FSMContext):
    await state.update_data(type_user=message.text)
    data = await state.get_data()
    if data["type_user"]=="Пользователь":
        data["type_user"]="user"
    else:
        data["type_user"]="admin"
    data["username"]=int(str(data["username"]).split(" ----> ")[0])
    await update_state_user(data["username"],data["type_user"])
    await bot.send_message(message.chat.id,"Статус пользователя измененён!",reply_markup=types.ReplyKeyboardRemove())
    await state.finish()


async def save_content(mess):
    pass

async def send_spam_all(mess):
    conn = sqlite3.connect('milana_bot.db')
    cursor=conn.cursor()
    cursor.execute("SELECT *FROM users WHERE user_type=?",("user",))
    one_result = cursor.fetchall()
    print(one_result)
    for v in range(len(one_result)):
        try:
            await bot.copy_message(one_result[v][0],mess.chat.id,mess["message_id"])
        except Exception:
            pass
    await bot.send_message(mess.chat.id,"Готово!")
    cursor.close()
    conn.close()




class Spam(StatesGroup):
    messages = State()

@dp.message_handler(content_types=types.ContentTypes.all(),state=Spam.messages)
async def set_photo(message: types.Message, state: FSMContext):
    await state.update_data(messages=message)
    await send_spam_all(message)
    await state.finish()
    
class AddFilm(StatesGroup):
    id = State()
    name = State()

@dp.message_handler(state=AddFilm.id)
async def set_name_film(message: types.Message, state: FSMContext):
    await state.update_data(id=message.text)
    await message.answer("Введите название фильма для добавления")
    await AddFilm.name.set()

@dp.message_handler(state=AddFilm.name)
async def get_film(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    data = await state.get_data()
    data_answer=await add_film(str(data['id']).strip(),str(data['name']).strip())
    await message.answer(data_answer)
    await state.finish()

    
async def add_film(id,name):
    conn = sqlite3.connect('milana_bot.db')
    cursor=conn.cursor()
    cursor.execute("SELECT film_id,film_name FROM films WHERE film_id=? AND film_name=?",(id,name))
    one_result = cursor.fetchone()
    if one_result==None:
        cursor.execute("SELECT film_id FROM films WHERE film_id=?",(id,))
        one_result = cursor.fetchone()
        if one_result!=None:#если найден id
            cursor.execute("UPDATE films SET film_name=? WHERE film_id=?",(name,id))
            conn.commit()
            one_result="Название фильма обновлено!"+"\n"+"Его ID: "+str(id)+"\n"+"Его название: "+str(name)+"\n"
        else:
            cursor.execute("SELECT film_name FROM films WHERE film_name=?",(name,))
            one_result = cursor.fetchone()
            if one_result!=None:#если найдено имя
                cursor.execute("UPDATE films SET film_id=? WHERE film_name=?",(id,name))
                conn.commit()
                one_result="ID фильма обновлено!"+"\n"+"Его название: "+str(name)+"\n"+"Его ID: "+str(id)+"\n"
            else:
                sqlite_insert="""INSERT INTO films (film_id, film_name) VALUES (?, ?);"""
                cursor.execute(sqlite_insert,(id,name))
                conn.commit()
                one_result="Фильм добавлен!"+"\n"+"Его ID: "+str(id)+"\n"+"Его название: "+str(name)+"\n"
    else:
        one_result="Фильм обновлён! Его данные не изменились!"+"\n"+"Его ID: "+str(id)+"\n"+"Его название: "+str(name)+"\n"
    cursor.close()
    conn.close()
    return one_result
    
async def gen_markup():
    markup = types.InlineKeyboardMarkup(row_width=1)
    s1=types.InlineKeyboardButton("Я подписался✅", callback_data='check_user')
    markup.add(s1)
    return markup

async def gen_markup2():
    markup = types.InlineKeyboardMarkup(row_width=1)
    s1=types.InlineKeyboardButton("❓ Помощь ❓", callback_data='helped')
    s2=types.InlineKeyboardButton("Добавить фильм", callback_data='add')
    s3=types.InlineKeyboardButton("Удалить фильм", callback_data='del')
    s4=types.InlineKeyboardButton("Все фильмы", callback_data='viewall')
    s5=types.InlineKeyboardButton("Количество пользователей", callback_data='usercount')
    s6=types.InlineKeyboardButton("Изменить тип пользователя", callback_data='settypeuser')
    s7=types.InlineKeyboardButton("Разослать", callback_data='spamuser')
    markup.add(s1)
    markup.add(s2)
    markup.add(s3)
    markup.add(s4)
    markup.add(s5)
    markup.add(s6)
    markup.add(s7)
    return markup


async def gen_markup_user_change(lk):
    print(lk)
    markup = types.ReplyKeyboardMarkup(row_width=1)
    for v in range(len(lk)):
        s1=types.KeyboardButton(lk[v])
        markup.add(s1)
    return markup




async def setallusers(bot,id):
    conn = sqlite3.connect('milana_bot.db')
    cursor=conn.cursor()
    cursor.execute("SELECT *FROM users;")
    one_result = cursor.fetchall()
    lk=[]
    id_s=[]
    for v in range(len(one_result)):
        print(one_result)
        try:
            s=await bot.get_chat(one_result[v][0])
            lk.append(one_result[v][0]+" ----> "+"@"+s["username"]+" ----> "+one_result[v][1])
            id_s.append(one_result[v][0])
        except Exception:
            id_s.append(None)
            lk.append(None)
    lk=list(filter(None,lk))
    id_s=list(filter(None,id_s))
    await bot.send_message(id, "Выберите пользователя\n",reply_markup=await gen_markup_user_change(lk))
    await AdminSet.username.set()
    cursor.close()
    conn.close()

async def get_film(id_film):
    conn = sqlite3.connect('milana_bot.db')
    cursor=conn.cursor()
    cursor.execute("SELECT * FROM films WHERE film_id="+id_film+";")
    one_result = cursor.fetchone()
    cursor.close()
    conn.close()
    return one_result

async def add_user_of_not(user_id):
    conn = sqlite3.connect('milana_bot.db')
    cursor=conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id="+user_id+";")
    one_result = cursor.fetchone()
    if one_result==None:
        sqlite_insert = """INSERT INTO users (id, user_type) VALUES (?, ?);"""
        data_tuple = (user_id,"user")
        cursor.execute(sqlite_insert, data_tuple)
        conn.commit()
        cursor.close()
        conn.close()
        return "user"
    else:
        cursor.close()
        conn.close()
        return one_result[1]


async def all_films(bot,id):
    conn = sqlite3.connect('milana_bot.db')
    cursor=conn.cursor()
    cursor.execute("SELECT *FROM films;")
    one_result = cursor.fetchall()
    s="ID ----> FILM\n"
    for v in range(len(one_result)):
        s+=str(one_result[v][0])+"  ---->  "+str(one_result[v][1])+"\n"
    cursor.close()
    conn.close()
    await bot.send_message(id,s)
    


async def all_users(bot,id):
    conn = sqlite3.connect('milana_bot.db')
    cursor=conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users;")
    one_result = cursor.fetchone()
    cursor.close()
    conn.close()
    await bot.send_message(id,"Количество пользователей в боте: "+str(one_result[0]))

async def check_member_user(bot,id):
    k=int(1)
    lk=[-1001720769176,-1001625684481,-1001718778976,-1001808852453,-1001769541458,-1001695902741]
    for v in range(len(lk)):
        s=await bot.get_chat_member(lk[v],id)
        if s["status"]=="left":
            k*=0
        if s["status"]=="member":
            k*=1
    return k

@dp.message_handler(content_types=['text'])
async def message_check(messages):
    mess_text=str(messages.text).strip()
    check_user=await add_user_of_not(str(messages.chat.id))    
    if mess_text=='/start':
        if check_user=="user":
            await bot.send_message(messages.chat.id,'<b>Для доступа к базе данных фильмов подпишитесь на каналы</b>\n⬇️⬇️⬇️\n\n'+
                     '1. <a href="https://t.me/+_ZJK5-WOjaIxNDNi">YOUWORLD</a>\n'+
                     '2. <a href="https://t.me/+8_IKtVMH5bMyYTRi">Темы и Языки для Telegram</a>\n'+
                     '3. <a href="https://t.me/+UoMx1VJtoIw5Y2Yy">Ночной таролог🌚</a>\n'+
                     '4. <a href="https://t.me/+WU-XgkU9fLo3NDMy">ТехноНаука🧪</a>\n'+
                     '5. <a href="https://t.me/+R-KwXJRxSdYzYWUy">Интимология</a>\n'+
                     '6. <a href="https://t.me/+fyfgHcLgEEFkMzli">Cinema Land</a>\n'+
                     '<i>После подписки, обязательно нажмите</i>\n\n'+
                     '<i>«Я подписался✅»</i>\n\n'+
                     '<i>Доступ к базе данных фильмов в боте будет открыт</i>\n'+
                     '<i>автоматически.</i>\n\n'+
                     '<b>Внимание!</b> Код нужно вводить в боте.',
                     reply_markup=await gen_markup(),
                     parse_mode='HTML',
                     disable_web_page_preview=True)
        else:
            await bot.send_message(messages.chat.id,"Привет Милан!",reply_markup=await gen_markup2())

    else:
        if check_user=="user":
            checked=await check_member_user(bot,messages.chat.id)
            if checked==0:
                await bot.send_message(messages.chat.id,'<b>Сначала подпишитесь на каналы</b>\n⬇️⬇️⬇️\n\n'+
                     '1. <a href="https://t.me/+_ZJK5-WOjaIxNDNi">YOUWORLD</a>\n'+
                     '2. <a href="https://t.me/+8_IKtVMH5bMyYTRi">Темы и Языки для Telegram</a>\n'+
                     '3. <a href="https://t.me/+UoMx1VJtoIw5Y2Yy">Ночной таролог🌚</a>\n'+
                     '4. <a href="https://t.me/+WU-XgkU9fLo3NDMy">ТехноНаука🧪</a>\n'+
                     '5. <a href="https://t.me/+R-KwXJRxSdYzYWUy">Интимология</a>\n'+
                     '6. <a href="https://t.me/+fyfgHcLgEEFkMzli">Cinema Land</a>\n',
                     reply_markup=await gen_markup(),
                     parse_mode='HTML',
                     disable_web_page_preview=True)
            else:
                print("asdasd")
                if mess_text.isnumeric()==True:
                    check_films=await get_film(mess_text)
                    if check_films==None:
                        await bot.send_message(messages.chat.id,"Внимание!\n\n<b>Фильма с таким кодом не существует!</b>",parse_mode='HTML')
                    else:
                        await bot.send_message(messages.chat.id,"Фильм найден!\n\n<b>"+check_films[1]+"</b>",parse_mode='HTML')
                else:
                    await bot.send_message(messages.chat.id,"Допускаются только цифры!\n\n<b>Введите только цифры.</b>",parse_mode='HTML')

@dp.callback_query_handler(lambda c: c.data)
async def callback_inline(callback_query: types.CallbackQuery):
    if callback_query.message:
        if callback_query.data == "check_user":
            checked=await check_member_user(bot,callback_query.message.chat.id)
            if checked==0:
                await bot.send_message(callback_query.message.chat.id,'<b>Сначала подпишитесь на каналы</b>\n⬇️⬇️⬇️\n\n'+
                     '1. <a href="https://t.me/+_ZJK5-WOjaIxNDNi">YOUWORLD</a>\n'+
                     '2. <a href="https://t.me/+8_IKtVMH5bMyYTRi">Темы и Языки для Telegram</a>\n'+
                     '3. <a href="https://t.me/+UoMx1VJtoIw5Y2Yy">Ночной таролог🌚</a>\n'+
                     '4. <a href="https://t.me/+WU-XgkU9fLo3NDMy">ТехноНаука🧪</a>\n'+
                     '5. <a href="https://t.me/+R-KwXJRxSdYzYWUy">Интимология</a>\n'+
                     '6. <a href="https://t.me/+fyfgHcLgEEFkMzli">Cinema Land</a>\n',
                     reply_markup=await gen_markup(),
                     parse_mode='HTML',
                     disable_web_page_preview=True)
            else:
                await bot.send_message(callback_query.message.chat.id, '<i>Доступ к базе данных открыт.</i>\n\n'+
                             '<b>Введите номер фильма</b>',parse_mode='HTML')

        if callback_query.data == "helped":
            await bot.send_message(callback_query.message.chat.id, 'Помощь!')
            

        if callback_query.data == "add":
            await callback_query.message.answer("Введите номер фильма для добавления")
            await AddFilm.id.set()

        if callback_query.data == "del":
            await callback_query.message.answer("Введите номер фильма для удаления")
            await DelFilm.id.set()

        if callback_query.data == "viewall":
            await all_films(bot,callback_query.message.chat.id)

        if callback_query.data == "usercount":
            await all_users(bot,callback_query.message.chat.id)

        if callback_query.data == "settypeuser":
            await setallusers(bot,callback_query.message.chat.id)

        if callback_query.data=="spamuser":
            await callback_query.message.answer("Введите своё сообщение")
            await Spam.messages.set()
            
    await bot.answer_callback_query(callback_query.id, text="")

if __name__ == "__main__":
    while True:
        try:
            executor.start_polling(dp, skip_updates=True)
        except Exception:
            continue