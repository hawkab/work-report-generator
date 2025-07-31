from datetime import datetime
from io import BytesIO
from collections import defaultdict
import matplotlib.pyplot as plt
from matplotlib import colormaps
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
)
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.pagesizes import letter
import os
import qrcode
from reportlab.lib.utils import ImageReader
from .utils import wrap_text
from .config import logger

PAGE_WIDTH = 550
MAIN_FONT = "DejaVuSans"
PDF_OUTPUT_DIR = "./report_generator/reports"

# Регистрация шрифта
try:
    pdfmetrics.registerFont(TTFont(MAIN_FONT, "DejaVuSans.ttf"))
except Exception:
    MAIN_FONT = "Helvetica"
    logger.warning("Шрифт DejaVu не найден. Используется Helvetica.")

def generate_qr_code(url: str) -> BytesIO:
    """
    Генерирует QR-код для указанной ссылки и возвращает BytesIO объект с изображением.
    """
    qr = qrcode.QRCode(
        version=1,
        box_size=2,
        border=2
    )
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    buffer = BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer
    
def setup_styles():
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle('MainHeader', fontName=MAIN_FONT, fontSize=12, textColor=colors.darkblue, spaceAfter=12))
    styles.add(ParagraphStyle('SectionHeader', fontName=MAIN_FONT, fontSize=10, textColor=colors.darkblue, spaceAfter=8))
    styles['Normal'].fontName = MAIN_FONT
    styles['Normal'].fontSize = 8
    styles.add(ParagraphStyle(name='RightAligned', fontName=MAIN_FONT, fontSize=8, alignment=2, leading=10))
    return styles


def create_pie_chart_from_grouped_data(grouped_by_date):
    action_counter = defaultdict(int)
    for actions in grouped_by_date.values():
        for action, details in actions.items():
            action_counter[action] += len(details)

    labels = list(action_counter.keys())
    sizes = list(action_counter.values())

    fig, ax = plt.subplots()
    cmap = colormaps.get_cmap('tab20').resampled(len(sizes))
    colors_pie = [cmap(i) for i in range(len(sizes))]

    wedges, texts, autotexts = ax.pie(
        sizes,
        labels=labels,
        colors=colors_pie,
        autopct='%1.1f%%',
        startangle=140,
        textprops={'fontsize': 6}
    )
    ax.axis('equal')

    ax.legend(
        wedges, labels, title="Типы работ", loc="lower center",
        bbox_to_anchor=(0.5, -0.4), fontsize=6, title_fontsize=7, ncol=2
    )

    buf = BytesIO()
    plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
    plt.close(fig)
    buf.seek(0)
    return buf


def generate_pdf(grouped_by_date, report_start_date, report_end_date, output_path=None):
    if output_path is None:
        filename = f"work_report_{report_start_date}_{report_end_date}.pdf"
        output_path = os.path.join(PDF_OUTPUT_DIR, filename)

    styles = setup_styles()
    story = []

    # Заголовок
    header_info = [
        f'ФИО: {os.getenv("PDF_HEADER_ISSUER_NAME")}',
        f'email: <a href="mailto:{os.getenv("PDF_HEADER_ISSUER_EMAIL")}">{os.getenv("PDF_HEADER_ISSUER_EMAIL")}</a>',
        f"Должность: {os.getenv('PDF_HEADER_ISSUER_POSITION')},",
        f'Отдел {os.getenv("PDF_HEADER_ISSUER_DEP")}',
        f'Организация: {os.getenv("PDF_HEADER_ISSUER_ORG_NAME")}',
        f'Руководитель: {os.getenv("PDF_HEADER_ISSUER_MANAGER")}'
    ]
    header_table = Table([[Paragraph("<br/>".join(header_info), styles["RightAligned"])]],
                         colWidths=[PAGE_WIDTH],
                         hAlign='RIGHT')
    header_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.extend([header_table, Spacer(1, 20)])

    # Заголовок отчёта
    story.append(Paragraph(
        f"<b>Отчёт о выполненной работе с {report_start_date.strftime('%d.%m.%Y')} по {report_end_date.strftime('%d.%m.%Y')}</b>",
        styles["MainHeader"]
    ))
    story.append(Spacer(1, 12))

    # Круговая диаграмма
    pie_buf = create_pie_chart_from_grouped_data(grouped_by_date)
    pie_img = Image(pie_buf, width=400, height=300)
    pie_img.hAlign = 'CENTER'
    story.extend([pie_img, Spacer(1, 20)])

    # Дневная активность
    date_width, type_width, project_width, details_width = 60, 120, 40, PAGE_WIDTH - 210
    weekday_names = ['понедельник', 'вторник', 'среда', 'четверг', 'пятница', 'суббота', 'воскресенье']
    sorted_dates = sorted(grouped_by_date.keys(), key=lambda d: datetime.strptime(d, "%d.%m.%Y"))

    for date in sorted_dates:
        actions = grouped_by_date[date]
        date_dt = datetime.strptime(date, "%d.%m.%Y")
        weekday_ru = weekday_names[date_dt.weekday()]
        weekday_color = 'red' if date_dt.weekday() > 4 else 'gray'
        date_title = f"{date} <font size=6 color='{weekday_color}'>({weekday_ru})</font>"

        story.append(Paragraph(date_title, styles["SectionHeader"]))

        data = [["Тип работ", "Проект", "Детали"]]
        for action, details in actions.items():
            for (project_name, msg), _ in details.items():
                data.append([action, project_name, wrap_text(msg)])

        table = Table(data, colWidths=[type_width, project_width, details_width])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('FONTNAME', (0, 0), (-1, -1), MAIN_FONT),
            ('FONTSIZE', (0, 0), (-1, -1), 7),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('LEFTPADDING', (0, 0), (-1, -1), 3),
            ('RIGHTPADDING', (0, 0), (-1, -1), 3),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        story.extend([table, Spacer(1, 12)])

    # Заключение
    story.append(Paragraph("Начало и окончание рабочего дня — с 09:00 по 18:00", styles["SectionHeader"]))
    story.append(Spacer(1, 10))
    disclaimer = (
        '* Отчёт составлен в информационных целях на основе технических данных и воспоминаний сотрудника. '
        'Некоторые виды активности могли не попасть в отчёт. Возможны неточности, частичные или обобщённые формулировки.'
    )
    

    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        leftMargin=40, rightMargin=40,
        topMargin=40, bottomMargin=40
    )
    
    archive_url = os.getenv("REPORTS_ARCHIVE_URL", "#")
    qr_buf = generate_qr_code(archive_url)
    qr_img = Image(qr_buf, width=80, height=80)

    qr_text = [
        Paragraph(f'<para align="left"><b><a href="{archive_url}">Архив отчётов о проделанной работе</a></b></para>', styles["Normal"]),
        Spacer(1, 4),
        Paragraph('<font size=6 color="gray">* Для перехода по ссылке отсканируйте QR-код слева</font>', styles["Normal"])
    ]

    qr_table = Table([[qr_img, qr_text]], colWidths=[95, PAGE_WIDTH - 300])
    qr_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
    ]))

    story.append(Spacer(1, 20))
    story.append(qr_table)
    story.append(Spacer(1, 15))
    story.append(Paragraph(f'<font size=6 color="gray">{disclaimer}</font>', styles["Normal"]))
    
    doc.build(story)

    logger.info(f"PDF-отчёт успешно сгенерирован: file://{os.path.abspath(output_path)}")
    return output_path

