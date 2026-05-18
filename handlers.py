import csv
import io

from aiogram import Router, types, F, BaseMiddleware
from aiogram.types import CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from config import ADMIN_ID
from database import delete_order, get_all_clients, add_client, add_order, complete_order, get_debts, get_pending_tasks, get_order_by_id, add_payment, get_today_tasks, get_today_payments, update_order, search_orders, get_statistics, get_month_report, get_all_orders
from keyboards import delete_keyboard, pay_keyboard, payment_received_keyboard, service_keyboard, main_menu_keyboard, done_keyboard, confirm_done_keyboard, debt_confirm_keyboard, debt_keyboard, edit_order_keyboard, edit_keyboard, delete_confirm_keyboard
from datetime import date, datetime

router = Router()

class AdminMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data):
        if hasattr(event, 'from_user') and event.from_user.id != ADMIN_ID:
            await event.answer("🚫 Rugsat ýok!")
            return
        return await handler(event, data)
router.message.middleware(AdminMiddleware())
router.callback_query.middleware(AdminMiddleware())

class AddOrder(StatesGroup):
    waiting_for_name = State()
    waiting_for_service = State()
    waiting_for_amount = State()
    waiting_for_due_date = State()
    waiting_for_deadline = State()
    waiting_for_description = State()



class AddPayment(StatesGroup):
    waiting_for_amount = State()


class EditOrder(StatesGroup):
    waiting_for_field = State()
    waiting_for_amount = State()


class FindOrder(StatesGroup):
    waiting_for_query = State()


class MonthReport(StatesGroup):
    waiting_for_month = State()


class ExportOrder(StatesGroup):
    waiting_for_month = State()



@router.message(Command('add_order'))
async def cmd_add_order(message: types.Message, state: FSMContext):  
    await state.clear()  
    await state.set_state(AddOrder.waiting_for_name)
    await message.answer('Müşderiniň adyny ýazyň:')
    

@router.message(Command('start'))
async def salam(message: types.Message, state: FSMContext):
    await state.clear()
    if message.from_user.id != ADMIN_ID:
        await message.answer('Rugsat yok')
        return
    await message.answer(
        "✅ Salam! Men seniň zakaz botaň.\n"
        "Aşakdaky düwmelerden saýla:",
        reply_markup=main_menu_keyboard
    )


@router.message(Command('my_tasks'))
async def cmd_my_tasks(message: types.Message, state: FSMContext):
    await state.clear() 
    tasks = get_pending_tasks()
    if not tasks:
        await message.answer("📭 Ýerine ýetirilmedik zakaz ýok.")
        return
    
    text = "📋 Ýerine ýetirilmedik zakazlar:\n\n"
    for t in tasks:
        text += f"ID: {t['id']} | Müşderi: {t['client_name']}\n"
        text += f"   {t['service_type']} - {t['amount']} manat\n"
        text += f"   Töleg: {t['due_date']} | Ý.möhlet: {t['completion_deadline'] or '?'}\n\n"
    await message.answer(text)



@router.message(Command("done"))
async def cmd_done(message: types.Message, state: FSMContext):
    await state.clear() 
    tasks = get_pending_tasks()
    if not tasks:
        await message.answer("📭 Ýerine ýetirilmedik zakaz ýok.")

    for t in tasks:
        text = (
            f"ID: {t['id']} | {t['client_name']}\n"
            f"{t['service_type']} — {t['amount']:.0f} ₽\n"
            f"Möhlet: {t['completion_deadline'] or '?'}"
        )
        await message.answer(text, reply_markup=done_keyboard(t['id']))
    


@router.callback_query(F.data.startswith("complete_"))
async def callback_done(call: CallbackQuery):
    order_id = int(call.data.split("_")[1])
    await call.message.answer(
        f"Zakaz #{order_id} tamamlandy diýip tassyklaýarsyňyzmy?",
        reply_markup=confirm_done_keyboard(order_id)
    )

    await call.answer()



@router.callback_query(F.data.startswith("confirm_done_"))
async def callback_confirm_done(call: CallbackQuery):
    order_id = int(call.data.split("_")[2])
    success = complete_order(order_id)

    if success:
        await call.message.edit_text(
            f"✅ Zakaz #{order_id} tamamlandy!\n\nPuluny aldyňyzmy?",
            reply_markup=payment_received_keyboard(order_id))
    else:
        await call.message.edit_text(f"⚠️ Zakaz #{order_id} tapylmady ýa-da eýýäm tamamlanan.")
            
    await call.answer()



@router.callback_query(F.data.startswith("cancel_done_"))
async def callback_cancel_done(call: CallbackQuery):
    await call.message.edit_text("❌ Ýatyryldy.")
    await call.answer()



@router.message(Command("debts"))
async def cmd_debts(message: types.Message, state: FSMContext):
    await state.clear() 
    debts = get_debts()
    if not debts:
        await message.answer("📭 Klientlerden algylar ýok.")
        return

    for d in debts:
        text = (
            f"👤 {d['client_name']}\n"
            f"🔧 {d['service_type']}\n"
            f"💰 Jemi: {d['amount']:.0f} ₽ | Tölenilen: {d['paid']:.0f} ₽\n"
            f"❗ Galýan: {d['debt']:.0f} ₽"
        ) 
        await message.answer(text, reply_markup=debt_keyboard(d['id']))


@router.callback_query(F.data.startswith("payment_yes_"))
async def callback_payment_yes(call: CallbackQuery):
    order_id = int(call.data.split("_")[2])
    # Bu ýerde töleg alnan diýip belläp bilersiňiz (ýokarda zakazy tamamlandy diýip belläpdiňiz)
    order = get_order_by_id(order_id)
    remaining = order['amount'] - order['paid']
    add_payment(order_id, remaining)  # Tölegi zakazyň möçberine deň edip belläň
    await call.message.edit_text(f"💰 Zakaz #{order_id} doly tölendi!")
    await call.answer()



@router.callback_query(F.data.startswith("payment_no_"))
async def callback_payment_no(call: CallbackQuery):
    order_id = int(call.data.split("_")[2])
    await call.message.edit_text(f"📋 Sargyt #{order_id} tamamlandy, töleg garaşylýar.")
    await call.answer()



@router.callback_query(F.data.startswith("debt_paid_"))
async def callback_debt_paid(call: CallbackQuery):
    order_id = int(call.data.split("_")[2])
    # Bu ýerde bergi tölen diýip belläp bilersiňiz
    await call.message.edit_text(f"Hakykatdan alyndymy?", reply_markup=debt_confirm_keyboard(order_id))
    await call.answer()



@router.callback_query(F.data.startswith("debt_confirm_"))
async def callback_debt_confirm(call: CallbackQuery):
    order_id = int(call.data.split("_")[2])
    order = get_order_by_id(order_id)
    remaining = order['amount'] - order['paid']
    add_payment(order_id, remaining)  # Galan bergi möçberini tölen diýip belläň
    await call.message.edit_text(f"✅ Bergi #{order_id} doly tölenildi!")
    await call.answer()



@router.callback_query(F.data.startswith("debt_back_"))
async def callback_debt_back(call: CallbackQuery):
    order_id = int(call.data.split("_")[2])
    order = get_order_by_id(order_id)
    await call.message.edit_text(
        f"👤 {order['client_name']} — {order['amount'] - order['paid']:.0f} ₽",
        reply_markup=debt_keyboard(order_id)
    )
    await call.answer()



@router.message(Command("today"))
async def cmd_today(message: types.Message, state: FSMContext):
    await state.clear() 
    tasks = get_today_tasks()
    payments = get_today_payments()

    if not tasks and not payments:
        await message.answer("📭 Bu gün ýerine ýetiriljek zakaz ýok.")
        return

    text = "📅 Bu günki işler:\n\n"
    if tasks:
        text += "📋 Ýerine ýetiriljek zakazlar:\n"
        for t in tasks:
            text += f"ID: {t['id']} | {t['client_name']} — {t['service_type']}\n"
    if payments:
        text += "\n💰 Töleg möhleti:\n"
        for p in payments:
            remaining = p['amount'] - p['paid']
            text += f"ID: {p['id']} | {p['client_name']} - {remaining:.0f} ₽\n"

    await message.answer(text)


@router.message(Command('pay'))
async def cmd_pay(message:types.Message, state:FSMContext):
    await state.clear() 
    pedding = get_pending_tasks()
    debts = get_debts()
    if not pedding and not debts:
        await message.answer("✅ Algylar ýok.")
        return
    
    if pedding:
        await message.answer("📋Tamamlanmadyk sargytlar:")
        for d in pedding:
            text = (
                f"👤 {d['client_name']}\n"
                f"Hyzmat: {d['service_type']}\n"
                f"Galýan: {d['amount'] - d['paid']:.0f} ₽"
            )
            await message.answer(text, reply_markup=pay_keyboard(d['id']))

    if debts:        
        await message.answer("✅ Tamamlanan, töleg garaşylýan:")
        for d in debts:
            text = (
                f"👤 {d['client_name']}\n"
                f"Hyzmat: {d['service_type']}\n"
                f"Galýan: {d['amount'] - d['paid']:.0f} ₽"
    )   
            await message.answer(text, reply_markup=pay_keyboard(d['id']))
  


@router.callback_query(F.data.startswith("pay_"))
async def callback_pay(call: CallbackQuery, state: FSMContext):
    order_id = int(call.data.split("_")[1])
    await state.update_data(order_id=order_id)
    await state.set_state(AddPayment.waiting_for_amount)
    await call.message.edit_text(
        f"Näçe töleg aldyňyz? (₽)\nMysal: 500",
    )

    await call.answer()



@router.message(AddPayment.waiting_for_amount)
async def payment_get_amount(message: types.Message, state: FSMContext):
    try:
        amount = float(message.text.strip().replace(',', '.'))
        if amount <= 0:
            raise ValueError
    except ValueError:
        await message.answer("❌ Nädogry san! Gaýtadan ýazyň: (mysal: 500)")

    data = await state.get_data()
    order_id = data['order_id']
    order = get_order_by_id(order_id)

    add_payment(order_id, amount)

    remaining = order['amount'] - (order['paid'] + amount)

    if remaining <= 0:
        await message.answer(f"✅ Zakaz #{order_id} doly tölendi!")
    else:
        await message.answer(f"✅ {amount:.0f} ₽ alyndy!\nGalýan: {remaining:.0f} ₽")

    await state.clear()

@router.message(Command('edit'))
async def cmd_edit(message: types.Message, state: FSMContext):
    await state.clear()
    tasks  = get_pending_tasks()
    debts = get_debts()

    if not tasks and not debts:
        await message.answer("📭 Üýtgetmek üçin açyk sargyt ýok.")
        return
    if tasks:
        await message.answer("📋 Tamamlanmadyk sargytlar:")
        for t in tasks:
            text =(
                f"ID: {t['id']} | {t['client_name']}\n"
                f"{t['service_type']} — {t['amount']} ₽\n"
                f"Möhlet: {t['completion_deadline'] or '?'}"
            )
            await message.answer(text, reply_markup=edit_order_keyboard(t['id']))

    if debts:
        await message.answer("✅ Tamamlanan, töleg garaşylýan:")
        for d in debts:
            text = (
                f"ID: {d['id']} | {d['client_name']}\n"
                f"{d['service_type']} — {d['amount']} ₽\n"
                f"Galýan: {d['debt'] or '?'}"
            )
            await message.answer(text, reply_markup=edit_order_keyboard(d['id']))



@router.callback_query(F.data.startswith("editorder_"))
async def callback_edit(call: CallbackQuery):
    parts = call.data.split("_")
    if len(parts) == 2:
        order_id = int(parts[1])
        await call.message.edit_text(
            f"Zakaz #{order_id} -  näme üýtgetmeli?",
            reply_markup=edit_keyboard(order_id)
        )
    await call.answer()



@router.callback_query(F.data.startswith("edit_amount_"))
async def callback_edit_amount(call: CallbackQuery, state: FSMContext):
    order_id = int(call.data.split("_")[2])
    await state.update_data(order_id=order_id, field='amount')
    await state.set_state(EditOrder.waiting_for_field)
    await call.message.edit_text(
        f"Zakaz #{order_id} üçin täze möçberi ýazyň (Rubl):\nMysal: 2500", 
    )
    await call.answer()


@router.message(EditOrder.waiting_for_field)
async def edit_get_amount(message: types.Message, state: FSMContext):
    date = await state.get_data()
    order_id = date['order_id']
    field = date['field']
    value = message.text.strip()

    if field == 'amount':
        try:
            amount = float(value.replace(',', '.'))
            if amount <= 0:
                raise ValueError
            value = amount
        except ValueError:
            await message.answer("❌ Nädogry san! Gaýtadan ýazyň (mysal: 2500)")
            return
    
    elif field in ['due_date', 'completion_deadline']:
        try:
            date_obj = datetime.strptime(value, "%d-%m-%Y")
            value = date_obj.strftime("%Y-%m-%d")
        except ValueError:
            await message.answer("❌ Nädogry format! DD-MM-YYYY formatynda ýazyň (mysal: 15-06-2026)")
            return
        
    update_order(order_id, field, value)
    await message.answer(f"✅ Zakaz #{order_id} üýtgedildi!")
    await state.clear()


@router.callback_query(F.data.startswith("edit_due_"))
async def callback_edit_due(call: CallbackQuery, state: FSMContext):
    order_id = int(call.data.split("_")[2])
    await  state.update_data(order_id=order_id, field='due_date')
    await state.set_state(EditOrder.waiting_for_field)
    await call.message.edit_text("Täze töleg möhletini ýazyň (DD-MM-YYYY):\nMysal: 15-06-2026",)
    await call.answer()


@router.callback_query(F.data.startswith("edit_deadline_"))
async def callback_edit_deadline(call: CallbackQuery, state: FSMContext):
    order_id = int(call.data.split("_")[2])
    await  state.update_data(order_id=order_id, field='completion_deadline')
    await state.set_state(EditOrder.waiting_for_field)
    await call.message.edit_text("Täze ýerine ýetiriş möhletini ýazyň (DD-MM-YYYY):")
    await call.answer()


@router.callback_query(F.data.startswith("edit_desc_"))
async def callback_edit_desc(call: CallbackQuery, state: FSMContext):
    order_id = int(call.data.split("_")[2])
    await  state.update_data(order_id=order_id, field='description')
    await state.set_state(EditOrder.waiting_for_field)
    await call.message.edit_text("Täze düşündiriş ýazyň:")
    await call.answer()


@router.message(Command('find'))
async def cmd_find(message: types.Message, state: FSMContext):
    await state.clear() 
    await state.set_state(FindOrder.waiting_for_query)
    await message.answer("🔍 Gözleg sözüni ýazyň:\n(müşderi ady, hyzmat görnüşi)")



@router.message(FindOrder.waiting_for_query)
async def find_query_handler(message: types.Message, state: FSMContext):
    if message.text == "🔙 Yza":
        await state.clear()
        await message.answer('Menýu:', reply_markup=main_menu_keyboard)
        return
    
    query = message.text.strip()
    results = search_orders(query)

    if not results:
        await message.answer(f"🔍 '{query}' boýunça hiç zat tapylmady.")
        return
    
    text = f"🔍 '{query}' boýunça tapylan maglumatlar:\n\n"
    for r in results:
        text += (
            f"ID: {r['id']} | {r['client_name']}\n"
            f"{r['service_type']} — {r['amount']} ₽\n"
            f"Status: {r['status']} | Töleg: {r['due_date'] or '?'} \n\n"
        ) 
    
    await message.answer(text, reply_markup=main_menu_keyboard)
 

@router.message(Command('stats'))
async def cmd_stats(message: types.Message, state: FSMContext):
    await state.clear()
    stats = get_statistics()
    text = (
        f"📊 Umumy statistika:\n\n"
        f"📋 Jemi sargyt: {stats['total_orders']}\n"
        f"✅ Tamamlanan: {stats['done_count']}\n"
        f"⏳ Garaşylýan: {stats['pending_count']}\n\n"
        f"💰 Jemi möçber: {stats['total_amount']:.0f} ₽\n"
        f"✅ Alyndy: {stats['total_paid']:.0f} ₽\n"
        f"❗ Galýan algy: {stats['total_debt']:.0f} ₽"
    )
    await message.answer(text)


@router.message(Command('month_report'))
async def cmd_month_report(message: types.Message, state: FSMContext):
    await state.clear() 
    await state.set_state(MonthReport.waiting_for_month)
    await message.answer("📅 Aýyny ýazyň (MM-YYYY):\nMysal: 06-2023")

@router.message(MonthReport.waiting_for_month)
async def month_report_handler(message: types.Message, state: FSMContext):
    text = message.text.strip()

    if message.text == "🔙 Yza":
        await state.clear()
        await message.answer('Menýu:', reply_markup=main_menu_keyboard)
        return
       # MM-YYYY → YYYY-MM
    try:
        parts = text.split('-')
        if len(parts) != 2:
            raise ValueError
        month = f"{parts[1]}-{parts[0]}"
        datetime.strptime(month, "%Y-%m")
    except ValueError:
        await message.answer("❌ Nädogry format! Mysal: 05-2026")
        return
    
    stats = get_month_report(month)

    if stats['total_orders'] == 0:
        await message.answer(f"📊 {text} aýynda sargyt ýok.")
        return
    
    report = (
        f"📊 {text} aýynyň hasabaty:\n\n"
        f"📋 Jemi sargyt: {stats['total_orders']}\n"
        f"✅ Tamamlanan: {stats['done_count']}\n"
        f"⏳ Garaşylýan: {stats['pending_count']}\n\n"
        f"💰 Jemi möçber: {stats['total_amount']:.0f} ₽\n"
        f"✅ Alyndy: {stats['total_paid']:.0f} ₽\n"
        f"❗ Galýan bergi: {stats['total_debt']:.0f} ₽"
    )
    await message.answer(report, reply_markup=main_menu_keyboard)


@router.message(Command('delete'))
async def cmd_delete(message: types.Message, state: FSMContext):
    await state.clear() 
    tasks = get_pending_tasks()
    debts = get_debts()

    if not tasks and not debts:
        await message.answer("📭 Öçürmek üçin açyk sargyt ýok.")
        return
    
    if tasks:
        await message.answer("📋 Tamamlanmadyk sargytlar:")
        for t in tasks:
            text =(
                f"ID: {t['id']} | {t['client_name']}\n"
                f"{t['service_type']} — {t['amount']:.0f} ₽"
            )
            await message.answer(text, reply_markup=delete_keyboard(t['id']))
    
    if debts:
        await message.answer("✅ Tamamlanan, töleg garaşylýan:")
        for d in debts:
            text = (
                f"ID: {d['id']} | {d['client_name']}\n"
                f"{d['service_type']} — {d['amount']:.0f} ₽"
            )
            await message.answer(text, reply_markup=delete_keyboard(d['id']))



@router.callback_query(F.data.startswith("delete_"))
async def callback_delete(call: CallbackQuery):
    parts = call.data.split("_")
    if len(parts) == 2:
        order_id = int(parts[1])
        await call.message.edit_text(
            f"Zakaz #{order_id} hakykatdanam öçürmek isleýärsiňizmi?",
            reply_markup=delete_confirm_keyboard(order_id)
        )
    await call.answer()


@router.callback_query(F.data.startswith("confirm_delete_"))
async def callback_delete_confirm(call: CallbackQuery):
    order_id = int(call.data.split("_")[2])
    success = delete_order(order_id)

    if success:
        await call.message.edit_text(f"✅ Zakaz #{order_id} öçürildi!")
    else:
        await call.message.edit_text("⚠️ Tapylmady.")
    await call.answer()


@router.callback_query(F.data.startswith("cancel_delete_"))
async def callback_delete_cancel(call: CallbackQuery):
    await call.message.edit_text("❌ Öçürmek ýatyryldy.")
    await call.answer() 



@router.message(Command('help'))
async def cmd_help(message: types.Message, state:FSMContext):
    await state.clear() 
    help_text = (
        "📖 Kommandalar:\n\n"
        "/start — Menýu\n"
        "/add_order — Täze sargyt goş\n"
        "/my_tasks — Tamamlanmadyk sargytlar\n"
        "/done — Sargyt tamamla\n"
        "/debts — Algylar\n"
        "/today — Şu günki işler\n"
        "/pay — Töleg bellemek\n"
        "/edit — Sargyt üýtget\n"
        "/find — Gözleg\n"
        "/stats — Statistika\n"
        "/month_report — Aýlyk hasabat\n"
        "/delete — Sargyt öçür\n"
        "/export — CSV eksport\n"
        "/help — Kömek"
    )
    await message.answer(help_text)


@router.message(Command('export'))
async def cmd_export(message: types.Message, state: FSMContext):
    await state.clear() 
    await state.set_state(ExportOrder.waiting_for_month)
    await message.answer("📅 Aýyny ýazyň (MM-YYYY):\nHemmesi üçin '0' ýaz")
   


@router.message(ExportOrder.waiting_for_month)
async def export_month_handler(message:types.Message, state:FSMContext):
    if message.text == "🔙 Yza":
        await state.clear()
        await message.answer("Menýu:",reply_markup=main_menu_keyboard)
        return
    
    text = message.text.strip()
    month = None

    if text != '0':
        try:
            parts = text.split('-')
            if len(parts) != 2:
                raise ValueError
            month = f"{parts[1]}-{parts[0]}"
            datetime.strptime(month, "%Y-%m")
        except ValueError:
            await message.answer("❌ Nädogry format! Mysal: 05-2026")
            return
        
    orders = get_all_orders(month)

    if not orders:
        await message.answer("📭 Sargyt ýok.")
        return
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID', 'Müşderi', 'Hyzmat', 'Möçber', 'Tölenilen', 'Status', 'Töleg möhleti', 'Ýerine ýetiriş', 'Düşündiriş', 'Döredilen'])

    for o in orders:
        writer.writerow([
            o['id'], o['client_name'], o['service_type'],
            f"{o['amount']:.0f}", f"{o['paid']:.0f}",
            o['status'], o['due_date'] or '',
            o['completion_deadline'] or '',
            o['description'] or '', o['created_at']
        ])

    total_amount = sum(float(o['amount']) for o in orders)
    total_paid = sum(float(o['paid']) for o in orders)
    writer.writerow([])
    writer.writerow(['', '', 'JEMI:', f"{total_amount:.0f}", f"{total_paid:.0f}", '', '', '', '', ''])

    output.seek(0)
    await message.answer_document(
        types.BufferedInputFile(
            output.getvalue().encode('utf-8-sig'), 
            filename='orders.csv'
        ), 
        caption='Export tamamlandy!'
    )







@router.message(AddOrder.waiting_for_name)
async def get_name(message: types.Message, state: FSMContext):

    
    if message.text == "🔙 Yza":
        await state.clear()
        await message.answer('Menýu:', reply_markup=main_menu_keyboard)
        return
    
    name = message.text.strip()
    if not name:
        await message.answer('Ady boş goýmaň, ýene:')
        return
    
    added, msg = add_client(name)
    if added:
        await message.answer(f"✅ Müşderi '{name}' bazada saklandy.")
    else:
        await message.answer(f"⚠️ Müşderi '{name}' eýýäm bar.")
    
    # Müşderiniň ID-sini sakla
    all_clients = get_all_clients()
    for cid, cname in all_clients:
        if cname == name:
            await state.update_data(client_id=cid)
            break
    
    # Indiki sorag: hyzmat görnüşi
    await state.set_state(AddOrder.waiting_for_service)
    await message.answer(
        "Hyzmat görnüşini saýlaň:\n", 
        reply_markup=service_keyboard
    )



@router.message(AddOrder.waiting_for_service)
async def get_service(message: types.Message, state: FSMContext):
    if message.text == "🔙 Yza":
        await state.clear()
        await message.answer('Menýu:', reply_markup=main_menu_keyboard)
        return
    
    service = message.text.strip()

    if service == "✏️ Başga (öz ýaz)":
        await message.answer("Hyzmatyň adyny ýazyň:", reply_markup=types.ReplyKeyboardRemove())
        return
    
    await state.update_data(service_type=service)
    await state.set_state(AddOrder.waiting_for_amount)
    await message.answer(
        "Zakazyň jemi möçberini ýazyň (Rubl):\nMysal: 1500", 
        reply_markup=types.ReplyKeyboardRemove()
    )



@router.message(AddOrder.waiting_for_amount)
async def get_amount(message: types.Message, state: FSMContext):
    if message.text == "🔙 Yza":
        await state.clear()
        await message.answer('Menýu:', reply_markup=main_menu_keyboard)
        return
    try:
        amount = float(message.text.strip().replace(',', '.'))
        if amount <= 0:
            raise ValueError
        await state.update_data(amount=amount)
        await state.set_state(AddOrder.waiting_for_due_date)
        await message.answer("Töleg möhleti (DD-MM-YYYY formatynda):\nMysal: 15-06-2026")
    except:
        await message.answer("Nädogry san! Gaýtadan ýazyň (mysal: 1500)")



@router.message(AddOrder.waiting_for_due_date)
async def get_due_date(message: types.Message, state: FSMContext):
    if message.text == "🔙 Yza":
        await state.clear()
        await message.answer('Menýu:', reply_markup=main_menu_keyboard)
        return
    
    try:
        datetime.strptime(message.text.strip(), "%d-%m-%Y")
    except ValueError:
        await message.answer(" ❌ Nädogry format! Töleg möhletini DD-MM-YYYY formatynda ýazyň (mysal: 15-06-2026)")
        return
    
    date_obj = datetime.strptime(message.text.strip(), "%d-%m-%Y")
    due_date = date_obj.strftime("%Y-%m-%d")
    await state.update_data(due_date=due_date)
    await state.set_state(AddOrder.waiting_for_deadline)
    await message.answer("Ýerine ýetiriş möhleti (DD-MM-YYYY formatynda):\nBoş goýmak üçin '0' ýazyň")



@router.message(AddOrder.waiting_for_deadline)
async def get_deadline(message: types.Message, state: FSMContext):
    if message.text == "🔙 Yza":
        await state.clear()
        await message.answer('Menýu:', reply_markup=main_menu_keyboard)
        return

    deadline = message.text.strip()
    if deadline == '0':
        deadline = None
    else:
        try:
            date_obj = datetime.strptime(deadline, "%d-%m-%Y")
            deadline = date_obj.strftime("%Y-%m-%d")
        except ValueError:
            await message.answer("❌ Nädogry format! Mysal: 15-06-2026")
            return  
    await state.update_data(completion_deadline=deadline)
    await state.set_state(AddOrder.waiting_for_description)
    await message.answer("Düşündiriş ýazyň (islege bagly, boş goýmak üçin '0'):")



@router.message(AddOrder.waiting_for_description)
async def get_description(message: types.Message, state: FSMContext):
    if message.text == "🔙 Yza":
        await state.clear()
        await message.answer('Menýu:', reply_markup=main_menu_keyboard)
        return

    desc = message.text.strip()
    if desc == '0':
        desc = ''
    
    # Ähli maglumatlary al
    data = await state.get_data()
    client_id = data['client_id']
    service_type = data['service_type']
    amount = data['amount']
    due_date = data['due_date']
    deadline = data['completion_deadline']
    
    # Zakazy bazada sakla
    order_id = add_order(client_id, service_type, amount, due_date, deadline, desc)
    
    # Müşderiniň adyny al
    all_clients = get_all_clients()
    client_name = ""
    for cid, cname in all_clients:
        if cid == client_id:
            client_name = cname
            break
    
    # Jogap ber
    await message.answer(
        f"✅ Zakaz #{order_id} goşuldy!\n\n"
        f"Müşderi: {client_name} (ID: {client_id})\n"
        f"Hyzmat: {service_type}\n"
        f"Möçber: {amount} manat\n"
        f"Töleg möhleti: {due_date}\n"
        f"Ýerine ýetiriş: {deadline if deadline else 'bellenilmedik'}\n"
        f"Düşündiriş: {desc if desc else 'ýok'}"
    )
    
    await state.clear()
