import os
import re
import importlib

class BubbleDetectEngine(object):
	def __init__(self):
		super(BubbleDetectEngine, self).__init__()

	def get_bubble_from_file(self,file_name):
		return []

	@staticmethod
	def find_all_sub_class():
		for file in os.listdir(os.path.join(os.path.dirname(__file__), "bubble_detect")):
			if re.match(r"^[a-zA-Z].*?\.py(c)?$", file) and file != "empty.py" and file != "empty.pyc":
				importlib.import_module(".bubble_detect.{}".format(file.split(".")[0]), __package__)
		return [sub_class for sub_class in BubbleDetectEngine.__subclasses__()]

	@classmethod
	def init_by_name(cls,name):
		all_sub_class = cls.find_all_sub_class()
		for sub_class in all_sub_class:
			if sub_class.__name__ == name:
				sub_obj = sub_class()
				return sub_obj
		return None
