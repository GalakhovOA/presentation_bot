from pathlib import Path
import re
import fitz  # PyMuPDF

from config import TEMPLATES_DIR, GENERATED_DIR, FONT_PATH, FONT_BOLD_PATH

FONT_NAME = "DejaVuSans"
FONT_BOLD_NAME = "DejaVuSansBold"


def _clean_filename(value: str) -> str:
    value = re.sub(r"[\\/:*?\"<>|]+", "_", value)
    value = re.sub(r"\s+", "_", value.strip())
    return value[:80] or "organization"


def _install_fonts(page):
    page.insert_font(fontname=FONT_NAME, fontfile=FONT_PATH)
    if Path(FONT_BOLD_PATH).exists():
        page.insert_font(fontname=FONT_BOLD_NAME, fontfile=FONT_BOLD_PATH)
    else:
        page.insert_font(fontname=FONT_BOLD_NAME, fontfile=FONT_PATH)


def _draw_card(page, rect, fill=(0.02, 0.20, 0.17), opacity=0.88, radius=8):
    page.draw_rect(
        rect,
        color=(0.12, 0.45, 0.36),
        fill=fill,
        width=0.7,
        fill_opacity=opacity,
        overlay=True,
    )


def _insert_text(page, rect, text, size=11, bold=False, color=(1, 1, 1), align=0, lineheight=1.25):
    if not text:
        return
    fontname = FONT_BOLD_NAME if bold else FONT_NAME
    page.insert_textbox(
        rect,
        text,
        fontsize=size,
        fontname=fontname,
        color=color,
        align=align,
        lineheight=lineheight,
        overlay=True,
    )


def _nonempty_contact(name: str, phone: str):
    parts = []
    if name:
        parts.append(name.strip())
    if phone:
        parts.append(phone.strip())
    return "\n".join(parts)


def generate_director_pdf(company_name: str, manager_name: str, manager_phone: str,
                          salary_manager_name: str, salary_manager_phone: str) -> Path:
    src = TEMPLATES_DIR / "director.pdf"
    out = GENERATED_DIR / f"01_{_clean_filename(company_name)}_директор_и_бухгалтер.pdf"
    doc = fitz.open(src)
    page = doc[0]
    _install_fonts(page)

    # Персональный блок в свободной правой части верхней зоны.
    card = fitz.Rect(500, 62, 812, 230)
    _draw_card(page, card)

    _insert_text(page, fitz.Rect(520, 78, 792, 112), f"Для {company_name}", size=12.5, bold=True)

    manager = _nonempty_contact(manager_name, manager_phone)
    salary = _nonempty_contact(salary_manager_name, salary_manager_phone)

    # Фиксированные компактные зоны: обе пары контактов помещаются без обрезки.
    if manager:
        _insert_text(page, fitz.Rect(520, 116, 792, 134), "Ваш менеджер", size=9.5, bold=True, color=(0.72, 0.94, 0.32))
        _insert_text(page, fitz.Rect(520, 136, 792, 168), manager, size=9.5)

    if salary:
        _insert_text(page, fitz.Rect(520, 174, 792, 192), "Зарплатный менеджер", size=9.5, bold=True, color=(0.72, 0.94, 0.32))
        _insert_text(page, fitz.Rect(520, 194, 792, 226), salary, size=9.5)

    doc.save(out, garbage=4, deflate=True)
    doc.close()
    return out


def generate_employees_pdf(company_name: str, salary_manager_name: str, salary_manager_phone: str) -> Path:
    src = TEMPLATES_DIR / "employees.pdf"
    out = GENERATED_DIR / f"02_{_clean_filename(company_name)}_для_сотрудников.pdf"
    doc = fitz.open(src)
    page = doc[0]
    _install_fonts(page)

    card = fitz.Rect(520, 62, 812, 180)
    _draw_card(page, card)
    _insert_text(page, fitz.Rect(540, 78, 792, 112), f"Для сотрудников\n{company_name}", size=11.5, bold=True)

    salary = _nonempty_contact(salary_manager_name, salary_manager_phone)
    if salary:
        _insert_text(page, fitz.Rect(540, 122, 792, 140), "Зарплатный менеджер", size=9.2, bold=True, color=(0.72, 0.94, 0.32))
        _insert_text(page, fitz.Rect(540, 141, 792, 174), salary, size=9.5)

    doc.save(out, garbage=4, deflate=True)
    doc.close()
    return out


def generate_booklet_pdf(company_name: str, salary_manager_name: str, salary_manager_phone: str) -> Path:
    src = TEMPLATES_DIR / "booklet.pdf"
    out = GENERATED_DIR / f"03_{_clean_filename(company_name)}_буклет.pdf"
    src_doc = fitz.open(src)
    out_doc = fitz.open()
    out_doc.insert_pdf(src_doc)

    # Вариант B: отдельная финальная страница с контактами.
    last = out_doc.new_page(width=src_doc[0].rect.width, height=src_doc[0].rect.height)
    last.show_pdf_page(last.rect, src_doc, 0)
    _install_fonts(last)

    # Затемняем исходную обложку, сохраняя фирменный фон.
    last.draw_rect(
        last.rect,
        color=None,
        fill=(0.00, 0.13, 0.11),
        fill_opacity=0.96,
        overlay=True,
    )

    _insert_text(last, fitz.Rect(34, 42, 390, 78), "СБЕР", size=12, bold=True, color=(0.80, 1.0, 0.38))
    _insert_text(last, fitz.Rect(34, 120, 386, 208), "Остались вопросы?", size=29, bold=True)
    _insert_text(
        last,
        fitz.Rect(34, 216, 386, 278),
        f"Предложение подготовлено для сотрудников\n{company_name}",
        size=13,
        color=(0.92, 0.97, 0.95),
    )

    salary = _nonempty_contact(salary_manager_name, salary_manager_phone)
    if salary:
        card = fitz.Rect(34, 315, 386, 445)
        _draw_card(last, card, opacity=0.94)
        _insert_text(last, fitz.Rect(54, 338, 366, 362), "Ваш зарплатный менеджер", size=11, bold=True, color=(0.72, 0.94, 0.32))
        _insert_text(last, fitz.Rect(54, 372, 366, 430), salary, size=14, bold=True)

    _insert_text(last, fitz.Rect(34, 528, 386, 557), "Зарплатный проект Сбера", size=8.7, color=(0.72, 0.88, 0.82))
    _insert_text(last, fitz.Rect(34, 558, 386, 580), "06", size=8.7, bold=True, color=(0.72, 0.94, 0.32), align=2)

    out_doc.save(out, garbage=4, deflate=True)
    out_doc.close()
    src_doc.close()
    return out


def generate_all(company_name: str, manager_name: str = "", manager_phone: str = "",
                 salary_manager_name: str = "", salary_manager_phone: str = ""):
    GENERATED_DIR.mkdir(parents=True, exist_ok=True)
    return [
        generate_director_pdf(
            company_name,
            manager_name,
            manager_phone,
            salary_manager_name,
            salary_manager_phone,
        ),
        generate_employees_pdf(company_name, salary_manager_name, salary_manager_phone),
        generate_booklet_pdf(company_name, salary_manager_name, salary_manager_phone),
    ]
