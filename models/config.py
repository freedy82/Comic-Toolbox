# import configparser
from __future__ import annotations
from configparser import RawConfigParser  # ConfigParser, SafeConfigParser, RawConfigParser

class MyConfig(RawConfigParser):
	CONFIG_FILE_NAME = ""

	def __init__(self, file_name=""):
		super().__init__()
		#print("try load config",file_name)
		found_config = self.read(file_name, encoding="utf-8")
		#if not found_config:
		#	raise ValueError('No config file found!')
		self.CONFIG_FILE_NAME = file_name
		#for name in section_names:
		#	self.__dict__.update(parser.items(name))
		self.inti_with_default()

	def inti_with_default(self):
		if self.get("general","language") == "":
			self.set("general","language","zh_Hant")

		if self.get("general","download_folder") == "":
			self.set("general","download_folder","./books")
		if self.get("general","max_retry") == "":
			self.set("general","max_retry","5")
		if self.get("general","timeout") == "":
			self.set("general","timeout","30")
		if self.get("general","agent") == "":
			self.set("general","agent","Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.113 Safari/537.36")
		if self.get("general","book_padding") == "":
			self.set("general","book_padding","2")
		if self.get("general","chapter_padding") == "":
			self.set("general","chapter_padding","3")
		if self.get("general","image_padding") == "":
			self.set("general","image_padding","3")
		if self.get("general","jpg_quality") == "":
			self.set("general","jpg_quality","90")
		if self.get("general","check_is_2_page") == "":
			self.set("general","check_is_2_page","1.0")

		if self.get("anti-ban","page_sleep") == "":
			self.set("anti-ban","page_sleep","10")
		if self.get("anti-ban","image_sleep") == "":
			self.set("anti-ban","image_sleep","1.0")
		if self.get("anti-ban","download_worker") == "":
			self.set("anti-ban","download_worker","2")

		if self.get("misc","display_message") == "":
			self.set("misc","display_message","True")
		if self.get("misc","play_sound") == "":
			self.set("misc","play_sound","True")

		if self.get("filter","contrast") == "":
			self.set("filter","contrast","1.0")
		if self.get("filter","sharpness") == "":
			self.set("filter","sharpness","1.0")
		if self.get("filter","brightness") == "":
			self.set("filter","brightness","1.0")
		if self.get("filter","color") == "":
			self.set("filter","color","1.0")

		pass

	def get(self, section: str, option: str, *, raw: bool = ..., vars: str | None = ...) -> str:
		if not self.has_section(section):
			return ""
		if not self.has_option(section,option):
			return ""
		return super().get(section,option)

	def getboolean(self, section: str, option: str, *, raw: bool = ..., vars: str | None = ...) -> bool:
		if not self.has_section(section):
			return False
		if not self.has_option(section,option):
			return False
		return super().getboolean(section,option)

	def getfloat(self, section: str, option: str, *, raw: bool = ..., vars: str | None = ...) -> float:
		if not self.has_section(section):
			return 0
		if not self.has_option(section,option):
			return 0
		return super().getfloat(section,option)

	def getint(self, section: str, option: str, *, raw: bool = ..., vars: str | None = ...) -> int:
		if not self.has_section(section):
			return 0
		if not self.has_option(section,option):
			return 0
		return super().getint(section,option)

	def set(self, section: str, option: str, value: str | None = ...) -> None:
		if not self.has_section(section):
			self.add_section(section)
		super().set(section,option,value)

	def load(self):
		self.read(self.CONFIG_FILE_NAME, encoding="utf-8")

	def save(self):
		#print("try save config",self.CONFIG_FILE_NAME)
		cfg_file = open(self.CONFIG_FILE_NAME, 'w', encoding="utf-8")
		self.write(cfg_file)
		cfg_file.close()

	def get_dict(self):
		sections_dict = {}

		# get all defaults
		#defaults = self.defaults()
		#temp_dict = {}
		#for key in defaults.iterkeys():
		#	temp_dict[key] = defaults[key]
		#sections_dict['default'] = temp_dict

		# get sections and iterate over each
		sections = self.sections()

		for section in sections:
			options = self.options(section)
			temp_dict = {}
			for option in options:
				temp_dict[option] = self.get(section, option)

			sections_dict[section] = temp_dict

		return sections_dict