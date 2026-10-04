import os
from pathlib import Path

from dotenv import load_dotenv
from telegram import Update, InputFile, BotCommand
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)

from config import BOT_TOKEN
from database import init_db, get_user, update_user, add_organization
from keyboards import MAIN_MENU, SKIP_MENU
from pdf_generator import generate_all

load_dotenv()

(
    SETUP_MANAGER_NAME,
    SETUP_MANAGER_PHONE,
    SETUP_SALARY_NAME,
    SETUP_SALARY_PHONE,
    CREATE_INN,
    CREATE_NAME,
    EDIT_MANAGER_NAME,
    EDIT_MANAGER_PHONE,
    EDIT_SALARY_NAME,
    EDIT_SALARY_PHONE,
) = range(10)


def _value(text: str) -> str:
    text = (text or "").strip()
    return "" if text.casefold() == "не нужно" else text


async def post_init(app):
    await app.bot.set_my_commands(
        [
            BotCommand("start", "Открыть главное меню"),
            BotCommand("create", "Создать презентации"),
        ]
    )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    user = get_user(uid)
    if not user["setup_complete"]:
        await update.message.reply_text(
            "Добро пожаловать! Сначала один раз настроим данные.\n\n"
            "Введите ваше имя. Если указывать его не нужно, нажмите «Не нужно».",
            reply_markup=SKIP_MENU,
        )
        return SETUP_MANAGER_NAME

    await update.message.reply_text(
        "Главное меню. Можно создать сразу три персонализированных презентации или изменить сохранённые контакты.",
        reply_markup=MAIN_MENU,
    )
    return ConversationHandler.END


async def setup_manager_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    update_user(update.effective_user.id, manager_name=_value(update.message.text))
    await update.message.reply_text("Введите ваш номер телефона или нажмите «Не нужно».", reply_markup=SKIP_MENU)
    return SETUP_MANAGER_PHONE


async def setup_manager_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    update_user(update.effective_user.id, manager_phone=_value(update.message.text))
    await update.message.reply_text("Введите ФИО зарплатного менеджера или нажмите «Не нужно».", reply_markup=SKIP_MENU)
    return SETUP_SALARY_NAME


async def setup_salary_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    update_user(update.effective_user.id, salary_manager_name=_value(update.message.text))
    await update.message.reply_text("Введите телефон зарплатного менеджера или нажмите «Не нужно».", reply_markup=SKIP_MENU)
    return SETUP_SALARY_PHONE


async def setup_salary_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    update_user(
        update.effective_user.id,
        salary_manager_phone=_value(update.message.text),
        setup_complete=1,
    )
    await update.message.reply_text("Готово. Данные сохранены и будут использоваться до изменения.", reply_markup=MAIN_MENU)
    return ConversationHandler.END


async def create_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Введите название организации:")
    return CREATE_NAME



async def create_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    company_name = update.message.text.strip()
    inn = ""
    uid = update.effective_user.id
    user = get_user(uid)
    add_organization(uid, inn, company_name)

    status = await update.message.reply_text("Готовлю 3 PDF…")
    try:
        files = generate_all(
            company_name=company_name,
            manager_name=user["manager_name"],
            manager_phone=user["manager_phone"],
            salary_manager_name=user["salary_manager_name"],
            salary_manager_phone=user["salary_manager_phone"],
        )
        captions = [
            "Для директора и бухгалтера",
            "Для сотрудников",
            "Буклет «Больше для жизни»",
        ]
        for path, caption in zip(files, captions):
            with open(path, "rb") as fh:
                await update.message.reply_document(
                    document=InputFile(fh, filename=Path(path).name),
                    caption=caption,
                )
        await status.edit_text("✅ Готово. Отправил все три презентации.")
    except Exception as exc:
        await status.edit_text(f"Не удалось создать PDF: {exc}")
    await update.message.reply_text("Главное меню", reply_markup=MAIN_MENU)
    return ConversationHandler.END


async def edit_manager_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = get_user(update.effective_user.id)
    await update.message.reply_text(
        "Ваши текущие данные:\n"
        f"ФИО: {user['manager_name'] or 'не указано'}\n"
        f"Телефон: {user['manager_phone'] or 'не указан'}\n\n"
        "Введите новое ФИО или нажмите «Не нужно», чтобы оставить поле пустым.",
        reply_markup=SKIP_MENU,
    )
    return EDIT_MANAGER_NAME


async def edit_manager_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    update_user(update.effective_user.id, manager_name=_value(update.message.text))
    await update.message.reply_text("Введите новый телефон или нажмите «Не нужно».", reply_markup=SKIP_MENU)
    return EDIT_MANAGER_PHONE


async def edit_manager_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    update_user(update.effective_user.id, manager_phone=_value(update.message.text))
    await update.message.reply_text("Данные менеджера обновлены.", reply_markup=MAIN_MENU)
    return ConversationHandler.END


async def edit_salary_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = get_user(update.effective_user.id)
    await update.message.reply_text(
        "Текущие данные зарплатного менеджера:\n"
        f"ФИО: {user['salary_manager_name'] or 'не указано'}\n"
        f"Телефон: {user['salary_manager_phone'] or 'не указан'}\n\n"
        "Введите новое ФИО или нажмите «Не нужно», чтобы оставить поле пустым.",
        reply_markup=SKIP_MENU,
    )
    return EDIT_SALARY_NAME


async def edit_salary_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    update_user(update.effective_user.id, salary_manager_name=_value(update.message.text))
    await update.message.reply_text("Введите новый телефон или нажмите «Не нужно».", reply_markup=SKIP_MENU)
    return EDIT_SALARY_PHONE


async def edit_salary_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    update_user(update.effective_user.id, salary_manager_phone=_value(update.message.text))
    await update.message.reply_text("Данные зарплатного менеджера обновлены.", reply_markup=MAIN_MENU)
    return ConversationHandler.END


async def menu_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == "📄 Создать презентации":
        return await create_start(update, context)
    if text == "👤 Мои данные":
        return await edit_manager_start(update, context)
    if text == "💼 Зарплатный менеджер":
        return await edit_salary_start(update, context)
    if text == "🔄 Старт":
        return await start(update, context)
    await update.message.reply_text("Выберите действие в меню.", reply_markup=MAIN_MENU)
    return ConversationHandler.END


def build_app():
    token = os.getenv("BOT_TOKEN") or BOT_TOKEN
    if not token:
        raise RuntimeError("BOT_TOKEN не задан. Создайте .env по примеру .env.example")

    init_db()
    app = ApplicationBuilder().token(token).post_init(post_init).build()

    conv = ConversationHandler(
        entry_points=[
            CommandHandler("start", start),
            CommandHandler("create", create_start),
            MessageHandler(filters.Regex(r"^📄 Создать презентации$"), create_start),
            MessageHandler(filters.Regex(r"^👤 Мои данные$"), edit_manager_start),
            MessageHandler(filters.Regex(r"^💼 Зарплатный менеджер$"), edit_salary_start),
            MessageHandler(filters.Regex(r"^🔄 Старт$"), start),
        ],
        states={
            SETUP_MANAGER_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, setup_manager_name)],
            SETUP_MANAGER_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, setup_manager_phone)],
            SETUP_SALARY_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, setup_salary_name)],
            SETUP_SALARY_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, setup_salary_phone)],
            CREATE_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, create_name)],
            EDIT_MANAGER_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_manager_name)],
            EDIT_MANAGER_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_manager_phone)],
            EDIT_SALARY_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_salary_name)],
            EDIT_SALARY_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_salary_phone)],
        },
        fallbacks=[CommandHandler("start", start)],
        allow_reentry=True,
    )

    app.add_handler(conv)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, menu_router))
    return app


if __name__ == "__main__":
    app = build_app()
    run_mode = os.getenv("RUN_MODE", "polling").strip().lower()
    if run_mode == "webhook":
        public_base = os.getenv("WEBHOOK_BASE_URL", "").rstrip("/")
        url_path = os.getenv("WEBHOOK_PATH", "salary/webhook").strip("/")
        port = int(os.getenv("WEBHOOK_PORT", "8081"))
        listen = os.getenv("WEBHOOK_LISTEN", "127.0.0.1")
        if not public_base:
            raise RuntimeError("Для RUN_MODE=webhook задайте WEBHOOK_BASE_URL")
        app.run_webhook(
            listen=listen,
            port=port,
            url_path=url_path,
            webhook_url=f"{public_base}/{url_path}",
            drop_pending_updates=True,
        )
    else:
        app.run_polling(drop_pending_updates=True)
