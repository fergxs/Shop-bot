# Importing necessary objects from aiogram, FSMContext from aiogram.dispatcher to maintain the bot's states,
# CallbackData from aiogram.utils.callback_data to handle the callback queries, and some other necessary objects.
# Importing AnswerState from a custom module 'states'.
# Importing the dispatcher 'dp', a database object 'db', and a bot object 'bot' from a custom module 'loader'.
# Importing a custom 'IsAdmin' filter from a 'filters' module.
from handlers.user.menu import questions
from aiogram.dispatcher import FSMContext
from aiogram.utils.callback_data import CallbackData
from keyboards.default.markups import all_right_message, cancel_message, submit_markup
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardRemove
from aiogram.types.chat import ChatActions
from states import AnswerState
from loader import dp, db, bot
from filters import IsAdmin

# Define callback data factory. It's used to pack and unpack data into/from a string format.
question_cb = CallbackData('question', 'cid', 'action')

# This handler processes messages that match 'questions' command and are from admins.
@dp.message_handler(IsAdmin(), text=questions)
async def process_questions(message: Message):
    # Simulate typing...
    await bot.send_chat_action(message.chat.id, ChatActions.TYPING)

    # Fetch all records from 'questions' table in the database.
    questions = db.fetchall('SELECT * FROM questions')

    # If there are no questions, reply to the admin with a message stating that there are no questions.
    if len(questions) == 0:
        await message.answer('No questions.')
    else:
        # For each question, create an inline keyboard markup with one button 'Answer'.
        # Send this markup with the question to the admin.
        for cid, question in questions:
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton('Answer', callback_data=question_cb.new(cid=cid, action='answer')))
            await message.answer(question, reply_markup=markup)

# This handler processes callback queries from 'Answer' button and are from admins.
@dp.callback_query_handler(IsAdmin(), question_cb.filter(action='answer'))
async def process_answer(query: CallbackQuery, callback_data: dict, state: FSMContext):
    # Put the chat id from callback data to a state storage.
    async with state.proxy() as data:
        data['cid'] = callback_data['cid']

    # Ask the admin to write an answer and remove the keyboard.
    # Set the bot's state to 'answer'.
    await query.message.answer('Write an answer.', reply_markup=ReplyKeyboardRemove())
    await AnswerState.answer.set()

# This handler processes messages (that are the answers from admin) in 'answer' state.
@dp.message_handler(IsAdmin(), state=AnswerState.answer)
async def process_submit(message: Message, state: FSMContext):
    # Put the answer to a state storage.
    async with state.proxy() as data:
        data['answer'] = message.text

    # Move to the next state and ask the admin to confirm the correctness of the answer.
    await AnswerState.next()
    await message.answer('Ensure you have not made a mistake in your answer.', reply_markup=submit_markup())

# This handler processes messages with 'cancel_message' text in 'submit' state.
@dp.message_handler(IsAdmin(), text=cancel_message, state=AnswerState.submit)
async def process_send_answer(message: Message, state: FSMContext):
    # Cancel the answer submitting, send a message about it and remove the keyboard.
    await message.answer('Cancelled!', reply_markup=ReplyKeyboardRemove())
    await state.finish()

# This handler processes messages with 'all_right_message' text in 'submit' state.
@dp.message_handler(IsAdmin(), text=all_right_message, state=AnswerState.submit)
async def process_send_answer(message: Message, state: FSMContext):
    # If the answer is confirmed, fetch it and the corresponding chat id from the state storage.
    async with state.proxy() as data:
        answer = data['answer']
        cid = data['cid']

        # Fetch the question from the database and delete the question record from the database.
        question = db.fetchone('SELECT question FROM questions WHERE cid=?', (cid,))[0]
        db.query('DELETE FROM questions WHERE cid=?', (cid,))

        # Format the text with the question and the answer and send it to the user.
        # Send a message about successful answer submitting to the admin and remove the keyboard.
        text = f'Question: <b>{question}</b>\n\nAnswer: <b>{answer}</b>'
        await message.answer('Sent!', reply_markup=ReplyKeyboardRemove())
        await bot.send_message(cid, text)
    # Finish the current state.
    await state.finish()
