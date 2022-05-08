## 安裝／升級步驟

個人是在 Windows 11 中的 Python 3.9 開發的，以下是參考

### 安裝 Python

安裝檔可以從 Python 官方網站 [https://www.python.org/](https://www.python.org/) 下載。

安裝時記得要選「Add python.exe to path」，才能使用 pip 指令。

### 安裝 Node.js

部分網站的爬蟲使用 Node.js 來分析 JavaScript 。

安裝檔可以從 Node.js 官方網站 [https://nodejs.org/](https://nodejs.org/) 下載。

### 安裝 Real-CUGAN ncnn Vulkan （如用圖片AI強化功能）

PS: 如你是用Windows 64 bits版本，可選擇下載一體包

https://github.com/nihui/realcugan-ncnn-vulkan

下載之後，在漫畫工具箱的設定中設置一下 Real-CUGAN ncnn Vulkan 的位置就可以了

### 安裝 Tesseract （如用翻譯工具必須）

https://tesseract-ocr.github.io/tessdoc/Home.html#binaries

在安裝時把以下有需要的文字方式選擇了

- jpn_vert
- chi_tra_vert
- chi_sim_vert
- kor_vert
- jpn
- chi_tra
- chi_sim
- kor

并且在安裝之後把Tesseract的路徑加入系統環境的PATH中
