@echo --clean --disable-windowed-traceback
SET PYTHONDONTWRITEBYTECODE=1
pyinstaller -F start.py -i ./uis/resources/icon.ico --add-data="models/sites/*;models/sites/" -w --name ComicToolbox --python-option B --paths=models/sites
@mkdir dist\languages\
@copy /Y languages\*.qm dist\languages\
@copy /Y themes\*.qss dist\themes\
SET PYTHONDONTWRITEBYTECODE=0
