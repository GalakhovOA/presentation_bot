from telegram import ReplyKeyboardMarkup

MAIN_MENU = ReplyKeyboardMarkup(
    [
        ["📄 Создать 3 PDF"],
        ["👤 Мои данные", "💼 Зарплатный менеджер"],
        ["🔄 Старт"],
    ],
    resize_keyboard=True,
)

SKIP_MENU = ReplyKeyboardMarkup(
    [["Не нужно"]],
    resize_keyboard=True,
    one_time_keyboard=True,
)
