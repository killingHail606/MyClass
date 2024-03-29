from aiogram import types
from aiogram.dispatcher import FSMContext

from handlers.users.commands import get_main_menu
from utils.db_api import db_commands

from loader import dp

from keyboards.default import main_keyboard
from keyboards.inline import inline_keyboards
from states.all_states import NewClass


db = db_commands


@dp.message_handler(text='Создать класс')
async def start_create_new_class(message: types.Message):
    user_class = await db.check_in_class()
    if not user_class:
        await message.answer('Введите название класса:')
        await NewClass.Name.set()
    else:
        await message.answer('Вы уже являетесь участником класса.')


@dp.message_handler(state=NewClass.Name)
async def complete_create_new_class(message: types.Message, state: FSMContext):
    new_class = db_commands.SchoolClass()
    new_class.name = message.text
    await state.update_data(new_class=new_class)

    await message.answer(f'Вы ввели: {message.text}. Всё верно?',
                         reply_markup=inline_keyboards.create_class)


@dp.message_handler(text='Главное меню')
async def go_to_main_menu(message: types.Message):
    user_class = await db.check_in_class()
    if user_class:
        await message.answer('Главное меню:', reply_markup=main_keyboard.main_menu)
    else:
        await message.answer('Главное меню:', reply_markup=main_keyboard.start_menu_for_new_user)


@dp.callback_query_handler(text_contains="create_class", state=NewClass.Name)
async def confirm_create_new_class(call: types.CallbackQuery, state: FSMContext):
    await call.answer()
    data = await state.get_data()
    new_class = data.get('new_class')
    action = call.data.split(':')[1]

    if action == 'confirm':

        new_class.members = [call.from_user.id]
        await new_class.create()

        lessons_schedule = db_commands.LessonSchedule()
        lessons_schedule.class_id = new_class.id
        await lessons_schedule.create()

        await state.reset_state()

        await call.message.answer('Поздравляю, вы создали новый класс!\n\nПерейдите в раздел "Мой класс", '
                                  'чтобы пригласить других участников или же начните добавлять расписание, '
                                  'дз, мероприятия... с помощью соответстующих кнопок меню',
                                  reply_markup=main_keyboard.main_menu)

    else:
        await call.message.answer('Введите название заново:')


@dp.message_handler(text='Присоединиться')
async def message_join_class(message: types.Message):
    user_class = await db.check_in_class()
    if not user_class:
        await message.answer('Введите код класса, к которому хотите присоединиться:')
        await NewClass.JoinClass.set()
    else:
        await message.answer('Вы уже являетесь участником класса.')


@dp.message_handler(state=NewClass.JoinClass)
async def join_class(message: types.Message, state: FSMContext):
    if message.text == 'Создать класс':
        await state.reset_state()
        await start_create_new_class(message)
    elif message.text == 'Присоединиться':
        await state.reset_state()
        await message_join_class(message)
    elif message.text == 'Главное меню':
        print('hi')
        await state.reset_state()
        await get_main_menu(message)
    else:
        print('wtf')
        class_id = message.text
        user_id = types.User.get_current().id
        user_class = await db.get_class_by_id(class_id)
        if user_class:
            await state.reset_state()
            user_class.members += [user_id]
            await user_class.update(members=user_class.members).apply()
            await message.answer(f'Вы присоединились к классу: {user_class.name}')
            await get_main_menu(message)
        else:
            await message.answer('Такого класса не существует.')


