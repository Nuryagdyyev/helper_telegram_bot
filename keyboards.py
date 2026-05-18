from aiogram.types import ReplyKeyboardMarkup, ReplyKeyboardRemove, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

service_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📄 Peçat")],
        [KeyboardButton(text="📝 Referat")],
        [KeyboardButton(text="🎓 Kursowa")],
        [KeyboardButton(text="🛂 Wiza")],
        [KeyboardButton(text="📦 Başga")], 
        [KeyboardButton(text="✏️ Başga (öz ýaz)")],
        [KeyboardButton(text="🔙 Yza")]
    ], 
    resize_keyboard=True, 
    one_time_keyboard=True
    )   


main_menu_keyboard = ReplyKeyboardRemove(
        keyboard=[
            [KeyboardButton(text="🔙 Yza")]
        ],
    
    resize_keyboard=True
)


def done_keyboard(order_id):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Tamamla", callback_data=f"complete_{order_id}")
            ]
        ]
    )


def confirm_done_keyboard(order_id):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Hawa", callback_data=f"confirm_done_{order_id}"),
                InlineKeyboardButton(text="❌ Ýok", callback_data=f"cancel_done_{order_id}")
            ]
        ]
    )


def payment_received_keyboard(order_id):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Puluny Aldym", callback_data=f"payment_yes_{order_id}"), 
                InlineKeyboardButton(text="❌ Puluny Almadym", callback_data=f"payment_no_{order_id}")
            ]
        ]
    )


def debt_keyboard(order_id):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="💰 Töleg alyndy", callback_data=f"debt_paid_{order_id}")
               
            ]
        ]
    )



def debt_confirm_keyboard(order_id):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Tassykla", callback_data=f"debt_confirm_{order_id}"),
                InlineKeyboardButton(text="⬅️ Yza", callback_data=f"debt_back_{order_id}")
            ]
        ]
    )


def pay_keyboard(order_id):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Aldym töleg", callback_data=f"pay_{order_id}")
            ]
        ]
    )


def edit_order_keyboard(order_id):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✏️ Üýtget", callback_data=f"editorder_{order_id}"),
            ]
        ]
    )


def edit_keyboard(order_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👤 Müşderi ady", callback_data=f"edit_client_{order_id}")],
        [InlineKeyboardButton(text="💰 Möçber", callback_data=f"edit_amount_{order_id}")],
        [InlineKeyboardButton(text="📅 Töleg möhleti", callback_data=f"edit_due_{order_id}")],
        [InlineKeyboardButton(text="⏰ Ýerine ýetiriş möhleti", callback_data=f"edit_deadline_{order_id}")],
        [InlineKeyboardButton(text="📝 Düşündiriş", callback_data=f"edit_desc_{order_id}")]
    ])


def delete_keyboard(order_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🗑️ Öçür", callback_data=f"delete_{order_id}")]
    ])


def delete_confirm_keyboard(order_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [
        InlineKeyboardButton(text="✅ Hawa", callback_data=f"confirm_delete_{order_id}"), 
        InlineKeyboardButton(text="❌ Ýok", callback_data=f"cancel_delete_{order_id}")
        ]
    ])