from googletrans import Translator

from models.controllers.translator.Translator import TranslatorEngine

class GoogleTranslatorEngine(TranslatorEngine):
	original_image = None

	def __init__(self):
		super(GoogleTranslatorEngine, self).__init__()

	def translate_text(self,text,to_lang,from_lang="auto"):
		translator = Translator()
		translations = translator.translate(text, dest=to_lang, src=from_lang)
		translated_text = translations.text
		return translated_text

	def translate_multi_text(self,text_list,to_lang,from_lang="auto"):
		print(text_list)
		translator = Translator()
		translations = translator.translate(text_list, dest=to_lang, src=from_lang)
		results = []
		for translation in translations:
			results.append(translation.text)
		return results

