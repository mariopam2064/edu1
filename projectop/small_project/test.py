from googletrans import Translator
def trans(text):
    trans = Translator()
    transed = trans.translate(text ,dest='ko').text
    return transed