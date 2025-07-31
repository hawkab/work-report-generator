from report_generator.pdf_builder import create_pie_chart_from_grouped_data
from io import BytesIO
from PIL import Image


def test_create_pie_chart_returns_image_buffer():
    # Минимальные входные данные
    grouped_by_date = {
        "01.07.2025": {
            "Разработка": {
                ("Проект X", "Создание модуля"): ["a", "b"],
            },
            "Код-ревью": {
                ("Проект X", "Просмотр PR"): ["c"]
            }
        },
        "02.07.2025": {
            "Разработка": {
                ("Проект Y", "Доработка сервиса"): ["d", "e", "f"],
            }
        }
    }

    buffer = create_pie_chart_from_grouped_data(grouped_by_date)

    assert isinstance(buffer, BytesIO)
    assert buffer.getbuffer().nbytes > 0

    # Убедимся, что изображение читаемо
    try:
        img = Image.open(buffer)
        img.verify()  # не кидает исключение = валидно
    except Exception as e:
        assert False, f"Невалидное изображение: {e}"

