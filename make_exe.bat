@echo --clean --disable-windowed-traceback
SET PYTHONDONTWRITEBYTECODE=1
pyinstaller -F start.py -i ./uis/resources/icon.ico --add-data="models/sites/*;models/sites/" --add-data="models/readers/*;models/readers/" -w --name ComicToolbox --python-option B
@mkdir dist\languages\
@copy /Y languages\*.qm dist\languages\
@mkdir dist\themes\
@copy /Y themes\*.qss dist\themes\
@del /F /Q dist\themes\base.qsst
SET PYTHONDONTWRITEBYTECODE=0
