from PyPDF2 import PdfFileReader


def assert_pdf_equal(actual_stream, expected_stream):
    actual_pdf = PdfFileReader(actual_stream)
    expected_pdf = PdfFileReader(expected_stream)

    assert actual_pdf.numPages == expected_pdf.numPages
    actual_page = actual_pdf.getPage(0)
    expected_page = expected_pdf.getPage(0)
    assert actual_page.extractText() == expected_page.extractText()
