pyuic5 --from-imports --import-from=uis -x main_window.ui -o main_window.py
pyuic5 --from-imports --import-from=uis -x about_window.ui -o about_window.py
pyuic5 --from-imports --import-from=uis -x crop_window.ui -o crop_window.py
pyuic5 --from-imports --import-from=uis -x crop_frame.ui -o crop_frame.py
pyuic5 --from-imports --import-from=uis -x help_window.ui -o help_window.py
pyuic5 --from-imports --import-from=uis -x image_filter_window.ui -o image_filter_window.py
pyuic5 --from-imports --import-from=uis -x bookmark_window.ui -o bookmark_window.py
pyuic5 --from-imports --import-from=uis -x reader_window.ui -o reader_window.py

pyrcc5 -o resources_rc.py resources.qrc

pylupdate5 main_window.py about_window.py crop_window.py crop_frame.py image_filter_window.py help_window.py bookmark_window.py reader_window.py -ts ../languages/en.ts
qt5-tools lrelease ../languages/en.ts ../languages/en.qm

pylupdate5 main_window.py about_window.py crop_window.py crop_frame.py image_filter_window.py help_window.py bookmark_window.py reader_window.py -ts ../languages/zh_Hant.ts
qt5-tools lrelease ../languages/zh_Hant.ts ../languages/zh_Hant_extra.ts  -qm ../languages/zh_Hant.qm

pylupdate5 main_window.py about_window.py crop_window.py crop_frame.py image_filter_window.py help_window.py bookmark_window.py reader_window.py -ts ../languages/zh_Hans.ts
qt5-tools lrelease ../languages/zh_Hans.ts ../languages/zh_Hans_extra.ts -qm ../languages/zh_Hans.qm


