# import necessary modules and classes
from aiogram.dispatcher import FSMContext
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, ContentType, ReplyKeyboardMarkup, ReplyKeyboardRemove
from aiogram.utils.callback_data import CallbackData
from keyboards.default.markups import *
from states import ProductState, CategoryState
from aiogram.types.chat import ChatActions
from handlers.user.menu import settings
from loader import dp, db, bot
from filters import IsAdmin
from hashlib import md5

# Initialize callback data factories
category_cb = CallbackData('category', 'id', 'action')
product_cb = CallbackData('product', 'id', 'action')

# Some text messages for use in the keyboard
add_product = '➕ Add product'
delete_category = '🗑️ Delete category'

# This handler processes the settings command if the user is an admin
@dp.message_handler(IsAdmin(), text=settings)
async def process_settings(message: Message):
    # Initializes a markup for inline keyboard
    markup = InlineKeyboardMarkup()
    # Fetch all categories from the database and add each as a button to the markup
    for idx, title in db.fetchall('SELECT * FROM categories'):
        markup.add(InlineKeyboardButton(
            title, callback_data=category_cb.new(id=idx, action='view')))

    # Add an additional button for adding a new category
    markup.add(InlineKeyboardButton(
        '+ Add category', callback_data='add_category'))

    # Send a message with the prepared keyboard
    await message.answer('Setting up categories:', reply_markup=markup)


# This handler processes the callback from category buttons for admins
@dp.callback_query_handler(IsAdmin(), category_cb.filter(action='view'))
async def category_callback_handler(query: CallbackQuery, callback_data: dict, state: FSMContext):
    # Extract the category id from the callback data
    category_idx = callback_data['id']

    # Fetch all products associated with this category from the database
    products = db.fetchall('''SELECT * FROM products product
    WHERE product.tag = (SELECT title FROM categories WHERE idx=?)''',
                           (category_idx,))

    # Delete the original message, send a new one, and update the state data with the chosen category
    await query.message.delete()
    await query.answer('All products added to this category.')
    await state.update_data(category_index=category_idx)
    await show_products(query.message, products, category_idx)


# Handlers for adding a new category

@dp.callback_query_handler(IsAdmin(), text='add_category')
async def add_category_callback_handler(query: CallbackQuery):
    # Delete the original message and send a new one
    await query.message.delete()
    await query.message.answer('Category name?')
    # Set the state to the title state of the CategoryState
    await CategoryState.title.set()


@dp.message_handler(IsAdmin(), state=CategoryState.title)
async def set_category_title_handler(message: Message, state: FSMContext):
    # Insert the new category into the database
    category = message.text
    idx = md5(category.encode('utf-8')).hexdigest()
    db.query('INSERT INTO categories VALUES (?, ?)', (idx, category))

    # Finish the state and call the process_settings again to show updated categories
    await state.finish()
    await process_settings(message)


# Handlers for deleting a category

@dp.message_handler(IsAdmin(), text=delete_category)
async def delete_category_handler(message: Message, state: FSMContext):
    async with state.proxy() as data:
        if 'category_index' in data.keys():
            idx = data['category_index']
            # Delete the category and all associated products from the database
            db.query('DELETE FROM products WHERE tag IN (SELECT title FROM categories WHERE idx=?)', (idx,))
            db.query('DELETE FROM categories WHERE idx=?', (idx,))

            await message.answer('Done!', reply_markup=ReplyKeyboardRemove())
            await process_settings(message)

# The handlers for adding a product are similarly organized, 
# but there are more states to go through (title, body, image, price, confirm).

# Handler for deleting a product
@dp.callback_query_handler(IsAdmin(), product_cb.filter(action='delete'))
async def delete_product_callback_handler(query: CallbackQuery, callback_data: dict):
    product_idx = callback_data['id']
    db.query('DELETE FROM products WHERE idx=?', (product_idx,))
    await query.answer('Deleted!')
    await query.message.delete()


# A helper function for displaying all products in a category
async def show_products(m, products, category_idx):
    await bot.send_chat_action(m.chat.id, ChatActions.TYPING)

    for idx, title, body, image, price, tag in products:
        text = f'<b>{title}</b>\n\n{body}\n\nPrice: {price} rubles.'
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton('🗑️ Delete', callback_data=product_cb.new(id=idx, action='delete')))

        await m.answer_photo(photo=image, caption=text, reply_markup=markup)

    markup = ReplyKeyboardMarkup()
    markup.add(add_product)
    markup.add(delete_category)

    await m.answer('Do you want to add or delete anything?', reply_markup=markup)
