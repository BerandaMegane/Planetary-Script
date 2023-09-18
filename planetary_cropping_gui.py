import enum
import base64
import pathlib
import traceback

# third party
import flet as ft
import cv2
import numpy as np

# self made
import planetary_cropping as my

class RecordStatus(enum.Enum):
    UNPROCESSED = (enum.auto(), "未処理")
    PROCESSING  = (enum.auto(), "処理中")
    PROCESSED   = (enum.auto(), "処理済み")

    def __init__(self, id, ja):
        self.id = id
        self.ja = ja

class CropSize(enum.IntEnum):
    X128 = 128
    X192 = 192
    X256 = 256
    X384 = 384
    X512 = 512
    
class CvImage:
    def __init__(self) -> None:
        pass

    def get_nodata_cv_image(self):
        cv_image = np.empty((720, 1280))
        cv_image.fill(128)
        return cv_image

    def get_nodata_b64_image(self):
        return self.cv_to_b64_image(self.get_nodata_cv_image())
    
    def cv_to_b64_image(self, cv_image):
        _, encoded = cv2.imencode(".jpg", cv_image)
        b64_image = base64.b64encode(encoded).decode("ascii")
        return b64_image

class PreviewController():
    def __init__(self) -> None:
        
        self.is_open = False
        self.cv_img = CvImage()
        
        # 表示領域
        self.image_control = ft.Image(
            src_base64=self.cv_img.get_nodata_b64_image(),
            width=960,
            fit=ft.ImageFit.SCALE_DOWN,
        )

        # スライドバー
        self.slider_control = ft.Slider(
            disabled=True,
            divisions=100,
            on_change=self.on_slider_change,
        )

        # スイッチ
        self.box_display_switch = ft.Switch(
            label="切り抜き枠表示",
            label_position=ft.LabelPosition.LEFT
        )
        self.box_size_dd = ft.Dropdown(
            options=[ft.dropdown.Option(int(size)) for size in CropSize]
        )

        # 閉じるボタン
        self.close_button = ft.ElevatedButton(
            "CLOSE",
            on_click=self.on_close_button_click
        )
        
        self.opend_file_text = ft.Text()
    
    def on_close_button_click(self, e):
        self.close_movie()
        self.opend_file_text.value = ""

    def open_movie(self, path):
        if self.is_open:
            self.close_movie()
        
        # ファイルオープン
        self.cv_video = cv2.VideoCapture(str(path))
        if self.cv_video.isOpened():
            self.is_open = True
        else:
            self.is_open = False
            return
        
        # 表示
        self.display_current_cv_image()

        # スライダー
        self.enable_slider()

        self.opend_file_text.value = str(path)
        self.opend_file_text.update()

    def close_movie(self):
        if self.is_open:
            self.cv_video.release()
            self.disable_slider()
            self.image_control.src_base64 = self.cv_img.get_nodata_b64_image()
            self.is_open = False
            self.opend_file_text.value = ""
            self.opend_file_text.update()

    def display_current_cv_image(self):
        # フレーム取得
        ret, cv_frame = self.cv_video.read()
        if not ret:
            cv_frame = self.cv_img.get_nodata_cv_image()
        
        # スイッチで切り替え
        # print(self.box_display_switch.value)
        # print(self.box_size_dd.value)
        if self.box_display_switch.value and self.box_size_dd is not None:

            # 前処理
            img = my.preprocess(cv_frame)
            # 惑星写ってなかったら1回おやすみ
            if my.exists_planets(img):
                # 重心計算
                x, y = my.calc_moment(img)

                # 切り出しサイズ決定
                width = int(self.cv_video.get(cv2.CAP_PROP_FRAME_WIDTH))
                height = int(self.cv_video.get(cv2.CAP_PROP_FRAME_HEIGHT))
                crop_size = int(self.box_size_dd.value)
                x1, x2, y1, y2 = my.calc_crop_range(width, height, x, y, crop_size)

                # 線を描画
                cv2.rectangle(img, (x1, y1), (x2, y2), (255, 255, 255))
                cv_frame = img

        # 画像表示
        self.set_cv_image(cv_frame)

    def set_cv_image(self, cv_img):
        b64_img = self.cv_img.cv_to_b64_image(cv_img)
        self.image_control.src_base64 = b64_img
        self.image_control.update()

    def enable_slider(self):
        self.slider_control.disabled = False
        self.slider_control.value = 0
        self.slider_control.update()

    def disable_slider(self):
        self.slider_control.disabled = True
        self.slider_control.update()

    def on_slider_change(self, e):
        if self.is_open:
            self.seek_cv_video(self.slider_control.value)
            # print(self.slider_control.value)

    def seek_cv_video(self, value):
        frames_all = int(self.cv_video.get(cv2.CAP_PROP_FRAME_COUNT))
        
        seek = int(value * (frames_all - 1))
        seek = max(0, min(frames_all-1, seek))
        self.cv_video.set(cv2.CAP_PROP_FRAME_COUNT, seek)
        # print(seek)
    
        self.display_current_cv_image()

class FileListController:
    def __init__(self, main_con) -> None:
        self.main_con = main_con
        self.datatable = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("ファイル名")),
                ft.DataColumn(ft.Text("Size", width=100)),
                ft.DataColumn(ft.Text("Status")),
                ft.DataColumn(ft.Text("Preview")),
                ft.DataColumn(ft.Text("Remove")),
            ],
        )

        self.file_list: list[FileListRecord] = list()
    
    def on_file_list_record_preview_clicked(self, e):
        record = self.find_preview_record(e.control)
        self.main_con.preview_control.open_movie(record.path)

    def on_file_list_record_delete_clicked(self, e):
        record = self.find_delete_record(e.control)
        self.remove_record(record)
        
    def add_record(self, name: str, path: pathlib.Path()):
        self.file_list.append(FileListRecord(self, name, path))
    
    def remove_record(self, record):
        self.file_list.remove(record)
        self.update()

    def find_preview_record(self, control):
        for record in self.file_list:
            if control is record.preview_button:
                return record
        return None
            
    def find_delete_record(self, control):
        for record in self.file_list:
            if control is record.delete_button:
                return record
        return None
    
    def update(self):
        self.datatable.rows = list()
        for record in self.file_list:
            self.datatable.rows.append(record.data_row)
        self.datatable.update()
    

class FileListRecord:
    def __init__(self, controller: FileListController, name: str, path: pathlib.Path):
        self.controller = controller
        self.name = name
        self.path = path

        # 処理状況
        self.status: RecordStatus = RecordStatus.UNPROCESSED
        self.status_text = ft.Text()
        self.update_status(RecordStatus.UNPROCESSED)

        # 切り抜きサイズ列
        self.crop_size_dd = ft.Dropdown(
            width=100,
            options=[ft.dropdown.Option(int(size)) for size in CropSize]
        )
        self.crop_size_data_cell = ft.DataCell(self.crop_size_dd)

        self.preview_button = ft.FilledButton(
            "Preview",
            on_click=self.controller.on_file_list_record_preview_clicked
        )

        self.delete_button = ft.FilledButton(
            "Delete",
            icon=ft.icons.DELETE,
            on_click=self.controller.on_file_list_record_delete_clicked
        )

        self.data_row = ft.DataRow(
            cells=[
                ft.DataCell(ft.Text(self.name)),
                self.crop_size_data_cell,
                ft.DataCell(self.status_text),
                ft.DataCell(self.preview_button),
                ft.DataCell(self.delete_button),
            ]
        )

    def update_status(self, status: RecordStatus):
        self.status = status
        self.status_text.value = status.ja
    
    def get_crop_size(self) -> int:
        return int(self.crop_size_data_cell.content.value)
        
class MainController:
    def __init__(self) -> None:
        self.is_processing = False

    def init(self, page: ft.Page):
        page.title = "惑星動画クロッピング"
        page.scroll = ft.ScrollMode.ALWAYS

    def on_files_selected(self, e: ft.FilePickerResultEvent):
        print("on_files_selected")

        if e.files:
            for file in e.files:
                file_path = pathlib.Path(file.path)
                self.file_list_con.add_record(file_path.name, file_path)
            
            self.file_list_con.update()
    
    def on_execute_button_clicked(self, e):
        if not self.is_processing and len(self.file_list_con.file_list) != 0:
            self.is_processing = True
            self.execute_status.value = "処理中"

            try:
                for record in self.file_list_con.file_list:
                    if record.status is RecordStatus.UNPROCESSED:
                        record.update_status(RecordStatus.PROCESSING)
                        self.execute_status.value = record.status.ja
                        self.page.update()
                        
                        crop_size = record.get_crop_size()
                        my.main_cropping(record.path, crop_size)

                        record.update_status(RecordStatus.PROCESSED)
                        self.execute_status.value = record.status.ja
                        self.page.update()
                        
                self.execute_status.value = "完了"
                self.page.update()

            except:
                traceback.print_exc()
                self.execute_status.value = "エラー"
                self.page.update()
                self.is_processing = False

    
    def main(self, page: ft.Page):
        self.page = page
        self.init(page)
        
        # プレビュー表示コントローラ
        self.preview_control = PreviewController()

        # ファイルの選択
        select_file_dialog = ft.FilePicker(on_result=self.on_files_selected)
        page.overlay.extend([select_file_dialog])
        
        # ファイル一覧
        self.file_list_con = FileListController(self)

        # 実行ボタン
        self.execute_button = ft.ElevatedButton("実行", on_click=self.on_execute_button_clicked)
        self.execute_status = ft.Text()

        md_text1 = """
        ## 概要
        このソフトは、惑星撮影した動画から、小さく写った惑星のみをクロッピングして RAW 出力します。
        クロッピングサイズをプレビューすることができます。

        ## 1: ファイル選択・プレビュー
        クロッピングしたい動画ファイルを指定してください。
        表の Preview ボタンで下の領域にプレビューすることができますので、サイズを表に設定してください。
        
        ## 2: 連続出力
        クロッピングサイズを設定後、実行ボタンでバッチ出力します。
        """

        # コントロールを配置
        page.add(
            ft.Markdown(md_text1),
            ft.ElevatedButton(
                "ファイル選択",
                icon=ft.icons.FILE_OPEN,
                on_click=lambda _: select_file_dialog.pick_files(allow_multiple=True),
            ),
            self.file_list_con.datatable,
            ft.Row([
                self.execute_button,
                self.execute_status,
            ]),
            ft.Column([
                self.preview_control.image_control,
                self.preview_control.slider_control,
            ]),
            ft.Row([
                self.preview_control.close_button,
                self.preview_control.opend_file_text,
            ]),
            ft.Row([
                self.preview_control.box_display_switch,
                self.preview_control.box_size_dd,
            ]),
        )

if __name__ == "__main__":
    controller = MainController()
    ft.app(target=controller.main)
