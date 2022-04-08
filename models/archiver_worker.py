import glob
import shutil
import util
from const import *
from zipfile import ZipFile
from PIL import Image
from ebooklib import epub

from PyQt5.QtCore import QThread, pyqtSignal

class ArchiverWorker(QThread):
	trigger = pyqtSignal(str,int,int)
	finished = pyqtSignal()
	canceled = pyqtSignal()
	MIMES = {"jpg":"image/jpeg", "jpeg":"image/jpeg", "png":"image/png", "gif":"image/gif", "webp":"image/webp"}

	def __init__(self,folders,from_folder,to_format,is_overwrite,num_pre_archive,title):
		super().__init__()
		self.stop_flag = True
		self.folders = folders
		self.from_folder = from_folder
		self.to_format = to_format
		self.is_overwrite = is_overwrite
		self.num_pre_archive = num_pre_archive
		self.folders_need_archive = []
		self.current_action_count = 0
		self.total_action_count = 0
		self.title = title

	def run(self):
		self.stop_flag = False
		self.trigger.emit(TRSM("Start checking, please wait"),0,0)
		self.current_action_count = 0
		self.total_action_count = 0
		self.folders_need_archive = self._pre_check_folder(self.folders)
		if len(self.folders_need_archive) > 0:
			self.trigger.emit(TRSM("Starting archive"),0,len(self.folders_need_archive))
			self.total_action_count = len(self.folders_need_archive)

			for idx, folders_info in enumerate(self.folders_need_archive, start=1):
				if self.stop_flag:
					break
				self._start_archive(folders_info)
				self.current_action_count += 1
				if not self.stop_flag:
					message = TRSM("Finish %s") % folders_info["to_file"]
					self.trigger.emit(message,self.current_action_count,self.total_action_count)

		if self.stop_flag:
			self.canceled.emit()
		else:
			self.finished.emit()

	def stop(self):
		self.stop_flag = True

	#internal
	def _pre_check_folder(self,folders):
		results = []
		final_folder_sets = [folders[i:i + self.num_pre_archive] for i in range(0, len(folders), self.num_pre_archive)]
		for final_folders in final_folder_sets:
			if len(final_folders) > 1:
				folder1_parts = final_folders[0].split("-",1)
				folder2_parts = final_folders[-1].split("-",1)
				if folder1_parts[0] == folder2_parts[0]:
					target_name = final_folders[0] + "-" + folder2_parts[1]
				else:
					target_name = final_folders[0] + "-" + final_folders[-1]
				target_name += "." + self.to_format
			else:
				target_name = final_folders[0] + "." + self.to_format

			if self.title:
				target_name = self.title + "-" + target_name

			full_target_file = os.path.join(self.from_folder,target_name)

			if self.is_overwrite or not os.path.exists(full_target_file):
				results.append({"folders":final_folders,"to_file":target_name})
			else:
				message = TRSM("File exist of %s") % full_target_file
				self.trigger.emit(message,self.current_action_count,self.total_action_count)

		return results

	def _start_archive(self,folder_info):
		if self.to_format in ("cbz","zip"):
			self._make_zip_from_multi_folder(folder_info["folders"],folder_info["to_file"])
		elif self.to_format == "epub":
			self._make_epub_from_multi_folder(folder_info["folders"],folder_info["to_file"])
			pass
		elif self.to_format == "pdf":
			self._make_pdf_from_multi_folder(folder_info["folders"],folder_info["to_file"])
			pass
		pass

	def _make_zip_from_multi_folder(self, folders, zip_file):
		full_zip_file = os.path.join(self.from_folder,zip_file)
		with ZipFile(full_zip_file, "w") as myzip:
			for folder in folders:
				if self.stop_flag:
					break
				full_folder = os.path.join(self.from_folder,folder)
				files = sorted(os.listdir(full_folder))
				name_prefix = 'cover.'

				with_cover = [x for x in files if x.startswith(name_prefix)]
				without_cover = [x for x in files if x not in with_cover]

				for file_list in (with_cover,without_cover):
					if self.stop_flag:
						break
					for filename in file_list:
						if self.stop_flag:
							break
						if self.to_format == "cbz":
							if util.get_ext(filename) not in ("jpg","png","gif","jpeg"):
								continue

						full_file = os.path.join(full_folder, filename)
						if self.to_format == "cbz":
							file_name_in_zip = folder + "-" + filename
						else:
							file_name_in_zip = folder + "/" + filename

						message = TRSM("Adding %s") % full_file
						self.trigger.emit(message,self.current_action_count,self.total_action_count)
						myzip.write(str(full_file), arcname=file_name_in_zip)

		pass

	def _make_pdf_from_multi_folder(self, folders, pdf_file):
		full_pdf_file = os.path.join(self.from_folder,pdf_file)

		images_datas = []
		for folder in folders:
			if self.stop_flag:
				break
			full_folder = os.path.join(self.from_folder,folder)
			files = sorted(os.listdir(full_folder))
			name_prefix = 'cover.'

			with_cover = [x for x in files if x.startswith(name_prefix)]
			without_cover = [x for x in files if x not in with_cover]

			for file_list in (with_cover,without_cover):
				if self.stop_flag:
					break
				for filename in file_list:
					if self.stop_flag:
						break
					if util.get_ext(filename) not in ("jpg","png","gif","jpeg","bmp","webp"):
						continue
					full_file = os.path.join(full_folder, filename)

					tmp_image = Image.open(full_file)
					tmp_image.convert('RGB')
					images_datas.append(tmp_image)

					message = TRSM("Adding %s") % full_file
					self.trigger.emit(message,self.current_action_count,self.total_action_count)

		if not self.stop_flag:
			if len(images_datas) > 1:
				message = TRSM("Creating %s") % full_pdf_file
				self.trigger.emit(message, self.current_action_count, self.total_action_count)
				images_datas[0].save(full_pdf_file, save_all=True, append_images=images_datas[1:])
				message = TRSM("Finish create %s") % full_pdf_file
				self.trigger.emit(message, self.current_action_count, self.total_action_count)
			elif len(images_datas) == 1:
				images_datas[0].save(full_pdf_file)
				message = TRSM("Finish create %s") % full_pdf_file
				self.trigger.emit(message, self.current_action_count, self.total_action_count)
			else:
				message = TRSM("Not images found to create %s") % full_pdf_file
				self.trigger.emit(message, self.current_action_count, self.total_action_count)

		pass

	def _make_epub_from_multi_folder(self, folders, epub_file):
		full_epub_file = os.path.join(self.from_folder,epub_file)

		book = epub.EpubBook()
		book.set_title(epub_file.replace(".epub",""))
		#book.add_author('')

		chapters = []
		tocs = []
		is_added_cover = False
		for folder in folders:
			if self.stop_flag:
				break
			full_folder = os.path.join(self.from_folder,folder)
			files = sorted(os.listdir(full_folder))
			name_prefix = 'cover.'
			counter_in_folder = 1
			# add make section
			tocs.append((epub.Section(folder),[]))

			with_cover = [x for x in files if x.startswith(name_prefix)]
			without_cover = [x for x in files if x not in with_cover]

			for file_list in (with_cover,without_cover):
				if self.stop_flag:
					break
				for filename in file_list:
					if self.stop_flag:
						break
					ext = util.get_ext(filename)
					if ext not in ("jpg","png","gif","jpeg","webp"):
						continue

					full_file = os.path.join(full_folder, filename)
					message = TRSM("Adding %s") % full_file
					self.trigger.emit(message,self.current_action_count,self.total_action_count)

					file_name_in_epub = folder + "-" + filename

					if not is_added_cover:
						is_added_cover = True
						book.set_cover(file_name_in_epub, open(full_file, 'rb').read())
					else:
						ei = epub.EpubImage()
						ei.file_name = file_name_in_epub
						ei.media_type = self.MIMES[ext]
						ei.content = open(full_file, 'rb').read()
						book.add_item(ei)

					epub_chapter = epub.EpubHtml(
						title="Image "+str(counter_in_folder),
						file_name=file_name_in_epub+'.xhtml'
					)
					epub_chapter.content = u'<html><body><img src="'+file_name_in_epub+'" width="100%"></body></html>'
					book.add_item(epub_chapter)

					tocs[len(tocs)-1][1].append(epub_chapter)

					chapters.append(epub_chapter)
					counter_in_folder += 1

		book.toc = tocs

		book.spine = ['nav'] + chapters

		book.add_item(epub.EpubNcx())
		book.add_item(epub.EpubNav())

		# "play_order":{'enabled': False, 'start_from': 1}
		epub.write_epub(full_epub_file, book, {})

		pass
