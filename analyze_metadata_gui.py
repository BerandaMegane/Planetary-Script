import pathlib
import traceback

# third party
import flet as ft

# self made
import analyze_metadata as my

def init(page: ft.Page):
    page.title = "動画ファイル metadata 解析"
    page.window_width = 800
    page.window_height = 300

def main(page: ft.Page):

    def get_directory_result(e: ft.FilePickerResultEvent):
        dir_path.value = e.path if e.path else "Cancelled!"
        dir_path.update()

    def check_movie(e):
        print("click check_movie")
        try:
            movies_path = pathlib.Path(dir_path.value)
            movie_list = my.glob_movies_list(movies_path)
            print("movie count:", len(movie_list))
            check_text.value = "%d件の動画が見つかりました" % (len(movie_list))
            check_text.update()
        except:
            traceback.print_exc()
            check_text.value = "エラー"
            check_text.update()

    def execute_analyze(e):
        print("click check_movie")
        try:
            movies_path = pathlib.Path(dir_path.value)
            save_path = movies_path / "metadata.csv"
            my.save_movies_datetime(movies_path, save_path)
            execute_status.value = "成功: %s" % (str(save_path))
            execute_status.update()
        except:
            traceback.print_exc()
            execute_status.value = "エラー"
            execute_status.update()
    
    init(page)
    
    # ディレクトリの選択
    get_dir_dialog = ft.FilePicker(on_result=get_directory_result)
    dir_path = ft.Text("未選択")
    page.overlay.extend([get_dir_dialog])

    # チェック項目
    check_button = ft.ElevatedButton("チェック", on_click=check_movie)
    check_text = ft.Text("未チェック")

    # 実行ボタン
    execute_button = ft.ElevatedButton("実行", on_click=execute_analyze)
    execute_status = ft.Text()

    # コントロールを配置
    page.add(
        ft.Row(
            [
                ft.ElevatedButton(
                    "フォルダ参照",
                    icon=ft.icons.FOLDER_OPEN,
                    on_click=lambda _: get_dir_dialog.get_directory_path(),
                    disabled=page.web,
                ),
                dir_path,
            ]
        ),
        ft.Row(
            [
                check_button,
                check_text,
            ]
        ),
        ft.Row(
            [
                execute_button,
                execute_status,
            ]
        ),
    )

if __name__ == "__main__":
    ft.app(target=main)
