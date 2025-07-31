import os
import tempfile
from datetime import datetime
from report_generator.pdf_builder import generate_pdf


def test_generate_pdf_minimal():
    # Подготовка фиктивных данных
    grouped_by_date = {
        "01.07.2025": {
            "Тестовая активность": {
                ("Проект X", "Описание действия"): ["stub"]
            }
        }
    }

    report_start = datetime.strptime("01.07.2025", "%d.%m.%Y").date()
    report_end = datetime.strptime("05.07.2025", "%d.%m.%Y").date()

    with tempfile.TemporaryDirectory() as tmpdir:
        pdf_path = os.path.join(tmpdir, "test_report.pdf")
        result = generate_pdf(grouped_by_date, report_start, report_end, output_path=pdf_path)

        assert os.path.exists(result)
        assert os.path.isfile(result)
        assert result.endswith(".pdf")
        assert os.path.getsize(result) > 0

