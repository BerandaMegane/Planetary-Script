## 概要

Python3 で動作します。使用ライブラリは次の通りです。  

* auto-py-to-exe
* flet
* matplotlib
* numpy
* opencv-contrib-python
* opencv-python

詳細は requirements.txt を参照してください。  
また、動作確認時の `pip freeze` 結果を `pip_freeze.txt` ファイルに保存しています。

動作確認用データが test_data ディレクトリにあります。

* P8130019.MOV
  * 動画メタデータ解析、惑星動画クロッピング用 動画ファイル
* test_metadata.json
  * 動画メタデータ解析 JSON ファイル

### 1. 動画メタデータ解析
動画ファイルのメタデータを参照し、動画撮影データを出力する。  
ディレクトリを指定すると、ディレクトリ内の動画をすべて解析し、同じディレクトリに `metadata.csv` という名前の CSV ファイルとして出力します。

* analyze_metadata_gui.py
  * Flet による GUI 版
* analyze_metadata.py

### 2. 惑星動画クロッピング
惑星撮影動画の一部をクロッピングし、AVI(RAW) ファイルとして出力する。

* planetary_cropping_gui.py
  * Flet による GUI 版
* planetary_cropping.py

## 使用方法

### 0. とりあえず使うだけ (Windows 向け)

output ディレクトリ内の exe ファイルを実行する。

### 1. インストール・環境構築

初めて使用するときは、venv を使った Python 環境構築を行う。  

```powershell
# git clone
## 省略します
# venv 環境構築
python -m venv venv
# venv アクティベート
.\venv\Scripts\activate
# 推奨ライブラリのインストール requirements.txt 使用
pip install -r requirements.txt
```

### 2. Python スクリプト実行
```powershell
# venv アクティベート
.\venv\Scripts\activate
# 動画ファイル解析
python analyze_metadata_gui.py
# 惑星動画クロッピング
python planetary_cropping_gui.py
```

### 3. exe ファイルへのビルド
auto-py-to-exe を使用して exe ファイルへビルドする。  
ビルドオプションは、「ファイル1つ」へのビルドを設定するのみ。
```powershell
auto-py-to-exe
```
