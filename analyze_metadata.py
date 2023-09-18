import csv
import datetime
import json
import pathlib
import pprint
import subprocess

def analyze_movie(movie_path: pathlib.Path) -> dict:
    """
    json_dataを返す
    """
    
    # 実行コマンド
    cmd = [
        'ffprobe',
        '-hide_banner',
        '-show_streams',
        '-of', 'json',
        movie_path
    ]

    # 解析実行
    proc = subprocess.run(cmd, stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
    json_data = json.loads(proc.stdout)
    
    return json_data

def fetch_creation_time(json_data: dict) -> datetime.datetime:
    """
    録画開始時間をで返す

    """
    """
    実データの例：
    "tags": {
        "creation_time": "2023-08-13T01:38:43.000000Z",
        "language": "jpn",
        "vendor_id": "[0][0][0][0]"
      }
    """
    
    # 実データはローカル時間なので、タイムゾーン付与
    s = json_data["streams"][1]["tags"]["creation_time"].replace("Z", "+09:00")
    return datetime.datetime.fromisoformat(s)

def test_fetch_creation_time():
    with open("test_metadata.json", "r") as f:
        data = json.load(f)
        print(fetch_creation_time(data))

def fetch_duration_time(json_data: dict) -> float:
    return float(json_data["streams"][1]["duration"])

def test_fetch_play_time():
    with open("test_metadata.json", "r") as f:
        data = json.load(f)
        print(fetch_duration_time(data))

def save_movie_metadata() -> None:
    movie_file = r"D:\Pictures\20230813_Jupiter_Messier_Meteoroid\Jupiter\P8130017.MOV"
    save_file = "metadata.json"
    
    # 解析
    data = analyze_movie(movie_file)

    # JSON 保存
    with open(save_file, "w") as f:
        json.dump(data, f, indent=2)

def glob_movies_list(movies_path: pathlib.Path) -> list:
    """
    拡張子が動画のファイルをリストにして返す
    """
    movies_list = list(movies_path.glob("*.MOV"))
    return movies_list

def test_glob_movies_list():
    movies_dir = r"D:\Pictures\20230813_Jupiter_Messier_Meteoroid\Jupiter"
    movies_path = pathlib.Path(movies_dir)
    pprint.pprint(glob_movies_list(movies_path))

def save_movies_datetime(movies_path: pathlib.Path, save_path: pathlib.Path) -> None:
    """
    動画データのディレクトリを指定し、リストにまとめる
    """
    metadata_list = list()

    for movie_path in glob_movies_list(movies_path):
        data = analyze_movie(movie_path)
        metadata = {
            "name": movie_path.name,
            "creation_time": fetch_creation_time(data),
            "duration_time": fetch_duration_time(data),
        }
        metadata_list.append(metadata)
    
    with open(str(save_path), "w", newline="") as f:
        header = ["name", "creation_time", "duration_time"]
        writer = csv.DictWriter(f, header)
        writer.writeheader()
        writer.writerows(metadata_list)

def cui_main():
    movies_dir = r"./test_data/"
    movies_path = pathlib.Path(movies_dir)
    
    save_path = movies_path / "metadata.csv"

    save_movies_datetime(movies_path, save_path)

if __name__ == "__main__":
    cui_main()
