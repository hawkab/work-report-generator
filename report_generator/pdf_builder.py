import os
from datetime import datetime
from io import BytesIO
from collections import defaultdict, OrderedDict
import tempfile

from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import qrcode
from itertools import groupby
from operator import itemgetter
from .config import logger

weekday_names = ['понедельник', 'вторник', 'среда', 'четверг', 'пятница', 'суббота', 'воскресенье']

def _parse_date(d):
    return datetime.strptime(d, "%d.%m.%Y")

def flatten_details(grouped):
    rows = []
    for date in sorted(grouped.keys(), key=_parse_date):
        weekday_ru = weekday_names[datetime.strptime(date, "%d.%m.%Y").weekday()]
        for act, details in grouped[date].items():
            for (proj, msg), _ in details.items():
                rows.append({
                    "date": date + f" ({weekday_ru})",
                    "action": act,
                    "project": proj,
                    "details": msg
                })
    return rows

def group_details(details_sorted):
    grouped = OrderedDict()
    for date, rows in groupby(details_sorted, key=itemgetter("date")):
        grouped[date] = list(rows)
    return grouped

def calc_summary(grouped):
    c_type = defaultdict(int)
    c_proj = defaultdict(int)
    days = []
    totals = []

    for date in sorted(grouped.keys(), key=_parse_date):
        dt = _parse_date(date)
        weekday = ["пн","вт","ср","чт","пт","сб","вс"][dt.weekday()]
        days.append(weekday)
        per = 0
        for act, details in grouped[date].items():
            for (proj,_),_ in details.items():
                c_type[act]+=1
                c_proj[proj]+=1
                per+=1
        totals.append(per)

    main_proj = max(c_proj.items(), key=lambda kv:kv[1])[0] if c_proj else "—"
    main_act = max(c_type.items(), key=lambda kv:kv[1])[0] if c_type else "—"
    proj_pct = round((c_proj.get(main_proj,0)/(sum(c_proj.values()) or 1))*100)
    act_pct = round((c_type.get(main_act,0)/(sum(c_type.values()) or 1))*100)

    return OrderedDict(sorted(c_type.items())), days, totals, main_proj, proj_pct, main_act, act_pct

# ---------- Графики и QR ----------
CHART_COLORS = [
    "#3498db","#2ecc71","#e67e22","#e74c3c",
    "#9b59b6","#1abc9c","#f39c12","#7f8c8d"
]

def chart_doughnut(counts: OrderedDict, path: str):
    labels = list(counts.keys()); vals = list(counts.values()) or [1]
    fig,ax = plt.subplots(figsize=(4.5,3.2),dpi=120)
    ax.pie(vals,labels=labels,autopct='%1.0f%%',
           colors=CHART_COLORS[:len(vals)],startangle=90,
           wedgeprops=dict(width=0.5,edgecolor="white"),
           textprops={'fontsize':8})
    ax.set(aspect="equal")
    fig.savefig(path, format="png", dpi=150, bbox_inches="tight")
    plt.close(fig)

def chart_line(days, totals, path: str):
    fig,ax = plt.subplots(figsize=(4.5,3.2),dpi=120)
    ax.plot(days,totals,linewidth=2,marker="o",color=CHART_COLORS[0])
    ax.fill_between(days,totals,alpha=0.2,color=CHART_COLORS[0])
    ax.set_ylabel("Активности"); ax.grid(True,alpha=0.2)
    fig.savefig(path, format="png", dpi=150, bbox_inches="tight")
    plt.close(fig)

def generate_qr_code(url: str, path: str):
    qr = qrcode.QRCode(version=1,box_size=3,border=2)
    qr.add_data(url or "#"); qr.make(fit=True)
    img = qr.make_image(fill_color="black",back_color="white")
    img.save(path)

# ---------- Основной генератор ----------
def generate_pdf(grouped_by_date, start_date, end_date,
                 output_path=None, total_hours="40.0 ч", work_schedule="Пн–Пт, 09:00–18:00"):
    if output_path is None:
        fn = f"work_report_{start_date:%Y-%m-%d}_{end_date:%Y-%m-%d}.pdf"
        output_path = os.path.join("./report_generator/reports", fn)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # ENV переменные
    context = {
        "org_name": os.getenv("PDF_HEADER_ISSUER_ORG_NAME","Организация"),
        "employee_name": os.getenv("PDF_HEADER_ISSUER_NAME","—"),
        "employee_position": os.getenv("PDF_HEADER_ISSUER_POSITION","—"),
        "employee_dep": os.getenv("PDF_HEADER_ISSUER_DEP","—"),
        "manager_name": os.getenv("PDF_HEADER_ISSUER_MANAGER","—"),
        "archive_url": os.getenv("REPORTS_ARCHIVE_URL","#"),
    }

    counts,days,totals,main_proj,proj_pct,main_act,act_pct = calc_summary(grouped_by_date)
    details = flatten_details(grouped_by_date)
    grouped_details = group_details(details)

    # --- Новая аналитика ---
    total_tasks = sum(totals)
    work_days = len(days) or 1

    # Индекс деловой активности (BAI)
    bai = round(total_tasks / work_days, 2)

    # Фокус на проекте (FI)
    focus_index = proj_pct

    # Полезная активность (PTS)
    productive_types = {"GIT", "Анализ", "Confluence", "Консультация", "Помощь", "Мониторинг"}
    productive_count = sum(v for k,v in counts.items() if k in productive_types)
    productive_share = round((productive_count / (total_tasks or 1)) * 100, 1)

    with tempfile.TemporaryDirectory() as tmpdir:
        pie_path  = os.path.join(tmpdir, "chart_pie.png")
        line_path = os.path.join(tmpdir, "chart_line.png")
        qr_path   = os.path.join(tmpdir, "qr.png")

        chart_doughnut(counts, pie_path)
        chart_line(days, totals, line_path)
        generate_qr_code(context["archive_url"], qr_path)

        context.update({
            "period": f"{start_date:%d.%m.%Y} — {end_date:%d.%m.%Y}",
            "total_hours": total_hours,
            "work_schedule": work_schedule,
            "main_project": main_proj,
            "main_activity": main_act,
            "main_activity_pct": act_pct,
            "chart_pie": pie_path,
            "chart_line": line_path,
            "grouped_details": grouped_details,
            "qr_path": qr_path,
            "generated_at": datetime.now().strftime("%d.%m.%Y %H:%M:%S"),
            # --- Новые KPI ---
            "bai": bai,
            "focus_index": focus_index,
            "productive_share": productive_share,
        })

        template_loader = FileSystemLoader(searchpath='./report_generator/')
        template_env = Environment(loader=template_loader)
        template = template_env.get_template("report_template.html")
        html_out = template.render(**context)

        HTML(string=html_out, base_url=os.getcwd()).write_pdf(output_path)

    logger.info(f"PDF-отчёт успешно сгенерирован: file://{os.path.abspath(output_path)}")
    return output_path
