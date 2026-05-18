import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from config import BOT_TOKEN, ADMIN_ID
from database import init_db, check_db, get_today_payments, get_today_tasks, get_pending_tasks, get_debts, get_tomorrow_tasks, get_tomorrow_payments, get_overdue_tasks
from handlers import router, FSMContext
from keyboards import main_menu_keyboard
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime, timedelta
# dp.include_router(router)
# print(get_all_clients())


bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
dp.include_router(router)


async def send_morning_report():
    text = f"🌅 Gündelik hasabat — {datetime.now().strftime('%d-%m-%Y')}\n\n"


    # Şu günki etmeli işler
    today_tasks = get_today_tasks()
    if today_tasks:
        text += "📋 Şu günki etmeli işler:\n"
        for t in today_tasks:
            text += f"\n- {t['client_name']} — {t['service_type']}"
        text += "\n\n\n"

        # Şu gün töleg möhleti
    today_payments = get_today_payments()
    if today_payments:
        text += "💰 Şu gün töleg möhleti:\n"
        for p in today_payments:
            remaining = p['amount'] - p['paid']
            text += f"\n- {p['client_name']} —  {remaining:.0f} ₽"
        text += "\n\n\n"

    # Ähli algylar
    debts = get_debts()
    if debts:
        text += "💸 Algylar:\n"
        for d in debts:
            text += f"\n- {d['client_name']} — {d['debt']:.0f} ₽"
        text += "\n\n" + '-' * 30 + "\n\n\n"

    overdue = get_overdue_tasks()
    if overdue:
        text += "\n\n\n⏰ 🔴 Möhleti geçen sargytlar:\n"
        for task in overdue:
            text += f"\n- {task['client_name']} — {task['service_type']} (Töleg möhleti: {task['due_date']})"
        text += "\n\n\n"

    await bot.send_message(ADMIN_ID, text)


async def send_tomorrow_report():
    text = f"🌙 Ertirki hasabat — {(datetime.now() + timedelta(days=1)).strftime('%d-%m-%Y')}\n\n"

    # Ertirki etmeli işler
    tomorrow = get_tomorrow_tasks()
    if tomorrow:
        text += "📋 Ertirki etmeli işler:\n"
        for t in tomorrow:
            text += f"\n- {t['client_name']} — {t['service_type']}"
        text += "\n\n\n"

    # Ertirki töleg möhleti
    tomorrow_payments = get_tomorrow_payments()
    if tomorrow_payments:
        text += "💰 Ertirki töleg möhleti:\n"
        for p in tomorrow_payments:
            remaining = p['amount'] - p['paid']
            text += f"\n- {p['client_name']} — {remaining:.0f} ₽"
        text += "\n\n\n"

    # Ähli algylar
    debts = get_debts()
    if debts:
        text += "💸 Algylar:\n"
        for d in debts:
            text += f"\n- {d['client_name']} — {d['debt']:.0f} ₽"
    await bot.send_message(ADMIN_ID, text)


async def main():
    init_db()  
    check_db()

    scheduler = AsyncIOScheduler()
    scheduler.add_job(send_morning_report, 'cron', hour=20, minute=25)  
    scheduler.add_job(send_tomorrow_report, 'cron', hour=20, minute=26)
    scheduler.start()

    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main()) 