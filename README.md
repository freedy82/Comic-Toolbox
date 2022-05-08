<img src="uis/resources/icon.png" align="right" width="100"/>

# Comic Toolbox ( Manga Toolbox )

[Chinese version please check this page (中文版請看這)](readmes/README_zh.md)

## At the front

This tool is mainly for practicing Python before, and then I will change it when I have time, so the overall code is not very well written 😅 And because it is a learning work, sometimes you may find something strange or useless function in this tool? ! !

Another part of the functions may be more convenient and useful for users of e-ink e-book readers, because my original intention is to use it for my own Light 2 reader 😅

Please also be kind to the comics websites, if the site is broken, no one has to download it😅

Please set the crawler's delay time (in the setting interface) before starting the download. I am not responsible for the IP blocked by the website!

If you think this tool is helpful to you, please click star to follow, thank you for your support

If you encounter problems during use, please submit ISSUE

## Main features

- [x] Full GUI interface operation
- [x] Comic batch download
- [x] Bookmark function (more convenient to follow)
- [x] Sub-categories are stored by chapter/volume/extra
- [x] Support proxy function
- [x] Batch conversion of images (such as webp, gif, png to jpg)
- [x] Batch processing of pictures (such as changing contrast, brightness, sharpness, color, supporting Real-CUGAN AI enhancement, which is helpful for older comics)
- [x] Batch cropping of pictures (supports the integrated cropping of common Japanese manga covers, 2-page integrated cropping, semi-automatic fine-tuning, convenient for e-book readers)
- [x] Compression tool: support to generate cbz, epub, pdf, zip, docx (multiple chapters can be combined into one file)
- [x] Reader, supports multi-level subdirectory diversity / CBZ / ZIP / PDF, can set different number of pages, reading order from left to right or right to left, page ratio, reading method: page or full page Vertical (convenient for Korean comics), support bookmark reading progress, full screen reading
- [x] Translator tool supports simple automatic dialog detection, OCR, translation, generating new translated images

## Supported download site

- 動漫狂 `www.cartoonmad.com`
- 無限動漫 `www.comicabc.com`
- 动漫屋 `www.dm5.com`
- 动漫之家 `www.dmzj.com`
- 酷漫屋 `www.kumw5.com`
- 漫畫柜 `www.mhgui.com`
- Read Comic Online (American manga) `readcomicsonline.ru`
- WEBTOON (Korean manga) `www.webtoons.com`
- MangaDex (Multi-language manga) `mangadex.org`

## Interface Introduction

Download tool

![Download Tool](readmes/screenshots/en/downloader.jpg "Download Tool")

Reader

![Reader](readmes/screenshots/en/reader.jpg "Reader")

Conversion tool

![Converter Tool](readmes/screenshots/en/converter.jpg "Converter Tool")

Crop tool

![Crop tool](readmes/screenshots/en/cropper.jpg "Crop tool")

Compression tool

![Compressor](readmes/screenshots/en/archiver.jpg "Compressor")

Image processing

![Image processing](readmes/screenshots/en/image_filter.jpg "Image processing")

Image cropping

![Image crop](readmes/screenshots/en/image_cropper.jpg "Image crop")

Translator

(Page credit from https://www.mangaz.com/book/detail/44851 )

![Translator](readmes/screenshots/en/translator.jpg "Translator")

Settings - Prevent Banned

![Settings](readmes/screenshots/en/settings_anti-ban.jpg "Settings")

Bookmarks of downloader (some I'm watching, some I'm testing 😅 )

![Bookmarks](readmes/screenshots/en/bookmarks.jpg "Bookmarks")

Dark theme

![Dark Theme](readmes/screenshots/en/dark_theme.jpg "Dark Theme")


2 times the Real-CUGAN noise reduction effect (the left is the original image, the right is the rendering)

![Real-CUGAN effect](readmes/screenshots/real-cugan.jpg "Real-CUGAN effect")

## Notice

For Convert Tool, Crop Tool, Compress Tool, please select the folder of the comic series before scanning\
E.g:\
📁 d:\comics\ (download folder)\
📁 d:\comics\book_name\ (folder of series)\
📁 d:\comics\book_name\chapter-##\ (chapter/volume folder)\
🖼 d:\comics\book_name\chapter-##\\###.jpg (image file)

The conversion tool destination folder is suggested to be different from the source folder, even though it should be fine, but to be on the safe side 😅

## Notes

It is only for academic research and exchange, respect copyright, please support genuine, and resources downloaded or generated through this tool ** are prohibited from spreading and sharing! It is forbidden to use this project for commercial activities! **

## Installation

View [Installation](readmes/installation.md)

## Changelog

View [Changelog](readmes/change_log.md)

## Refer to

The crawler part has some code references from

- [ComicBook](https://github.com/lossme/ComicBook) by lossme (but doesn't seem to be maintained anymore)
- [ComicCrawler](https://github.com/eight04/ComicCrawler) by eight04
- [manhuagui-dlr](https://github.com/HSSLC/manhuagui-dlr) by HSSLC

Dialog detection [ComicVision](https://github.com/jemsbhai/comicvision/blob/master/Comic%20Vision.ipynb) by Muntaser Syed 

Learn Python from Luo Hao's [Python - 100 days from novice to master](https://github.com/jackfrued/Python-100-Days) (still not finished yet😅 still a novice)

PyQt5 learned from buzzing [this year is still not enough money to buy psQQ, let's use PyQt to write one by ourselves](https://www.wongwonggoods.com/category/portfolio/13th_ironman/)

QSS dark theme refers to [QSS-Skin-Builder](https://github.com/satchelwu/QSS-Skin-Builder) of Schoolbag

Some icons are from [Icons8](https://icons8.com/icon/set/show/ios-glyphs)

## License

**Comic Toolbox** is licensed under [GPL v3.0 license](LICENSE)
