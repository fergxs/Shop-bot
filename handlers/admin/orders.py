# Importing Message object from aiogram, which represents a message from a user.
# Importing the dispatcher 'dp' and a database object 'db' from a custom module 'loader'.
# Importing a custom 'orders' function from a 'menu' module inside 'user' handlers.
# Importing a custom 'IsAdmin' filter from a 'filters' module.
from aiogram.types import Message
from loader import dp, db
from handlers.user.menu import orders
from filters import IsAdmin

# This handler responds to messages that match 'orders' from admins.
@dp.message_handler(IsAdmin(), text=orders)
async def process_orders(message: Message):
    # Fetch all records from 'orders' table in the database.
    orders = db.fetchall('SELECT * FROM orders')
    
    # If there are no orders, reply to the admin with a message stating that there are no orders.
    # Otherwise, generate a response for each order using the 'order_answer' function.
    if len(orders) == 0: await message.answer('You have no orders.')
    else: await order_answer(message, orders)

# This asynchronous function constructs a string response for each order in the orders list.
async def order_answer(message, orders):

    # Initialize an empty string for accumulating the response.
    res = ''

    # For each order, append a line to the response string that includes the order number.
    # The order number is extracted as the fourth element (index 3) of each order record.
    for order in orders:
        res += f'Order <b>№{order[3]}</b>\n\n'

    # Finally, the function sends a message with the accumulated string 'res'.
    await message.answer(res)
