from report_generator.utils import wrap_text


def test_wrap_text_simple():
    text = "Это очень длинный текст, который должен быть перенесён по ширине."
    wrapped = wrap_text(text, width=20)

    lines = wrapped.split('\n')
    assert all(len(line) <= 20 for line in lines)
    assert "перенесён" in wrapped
    assert isinstance(wrapped, str)

