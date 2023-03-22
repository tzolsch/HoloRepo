import PyPDF2

# creating a pdf file object
pdfFileObj = open('D:\HoloProject\HoloRepo\Secrets\WICCA.pdf', 'rb')
pdfReader = PyPDF2.PdfReader(pdfFileObj)
pdfReader.pages
pageObj = pdfReader.pages[40]