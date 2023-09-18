"""
https://note.nkmk.me/python-opencv-videocapture-file-camera/
"""

# 公式
import pathlib
import sys
import traceback

# サードパーティ
import cv2
import numpy as np
import matplotlib.pyplot as plt

# 画像の表示
def display_image(img):
    cv2.imshow("img", img)
    cv2.waitKey()
    cv2.destroyAllWindows()

def preprocess(img):
    # グレースケール化
    img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    # メディアンフィルタ
    # img = cv2.medianBlur(img, 5)
    # 2値化
    # ret, img = cv2.threshold(img, 10, 255, cv2.THRESH_BINARY)
    # ret, img = cv2.threshold(img, 0, 255, cv2.THRESH_OTSU)
    ret, img = cv2.threshold(img, 0, 255, cv2.THRESH_TRIANGLE)
    return img

# 白割合を計算
def calc_white_rate(grey_img):
    # 白部分の画素数
    white_area = cv2.countNonZero(grey_img)
    return white_area / grey_img.size

# 白割合をもとに惑星が存在するか調べる
def exists_planets(grey_img):
    rate = calc_white_rate(grey_img)
    
    # しきい値は経験則的
    if rate >= 0.00005 and rate < 0.1:
        return True
    else:
        return False

def calc_crop_range(width, height, center_x, center_y, crop_size):
    """
    「元画像のサイズ、切り抜きたい中心座標、切り抜きたいサイズ」を基に
    切り抜き後の座標を算出する
    """
    assert crop_size % 2 == 0
    half_crop_size = crop_size // 2

    x1 = center_x - half_crop_size
    x2 = center_x + half_crop_size

    y1 = center_y - half_crop_size
    y2 = center_y + half_crop_size

    if y1 < 0:
        # top はみ出し
        y1 = 0
        y2 = crop_size
    elif y2 > height:
        # bottom はみ出し
        y1 = height - crop_size
        y2 = height

    if x1 < 0:
        # left はみ出し
        x1 = 0
        x2 = crop_size
    elif x2 > width:
        # bottom はみ出し
        x1 = width - crop_size
        x2 = width

    return x1, x2, y1, y2

# 重心の計算
def calc_moment(grey_img):
    """
    画像の重心を計算する
    
    URL: https://www.higashisalary.com/entry/movie-object-moment
    """
    M = cv2.moments(grey_img, False)
    x, y = int(M["m10"]/M["m00"]) , int(M["m01"]/M["m00"])
    return x, y

def main_cropping(infile_path: pathlib.Path, crop_size):
    outfile_path = infile_path.parent / (infile_path.stem + "_crop.avi")

    # ファイル読み込み
    inmovie = cv2.VideoCapture(str(infile_path))
    if not inmovie.isOpened():
        print("inmovie error")
        sys.exit()
    width = int(inmovie.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(inmovie.get(cv2.CAP_PROP_FRAME_HEIGHT))

    # ファイル書き出し
    fourcc = cv2.VideoWriter_fourcc(*"RAW ")
    size = (crop_size, crop_size)

    outmovie = cv2.VideoWriter(str(outfile_path), fourcc, inmovie.get(cv2.CAP_PROP_FPS), size)
    if not outmovie.isOpened():
        print("outmovie error")
        sys.exit()

    # # 1枚試し処理
    # ret, frame = movie.read()
    # grey_img = preprocess(frame)

    # print(calc_white_rate(grey_img))

    try:
        # 何枚に1回、切り抜く座標をチェックするかどうか
        count = 10
        # 総フレーム数
        frames_all = int(inmovie.get(cv2.CAP_PROP_FRAME_COUNT))
        # 座標リスト
        moment_pos_list = []
        
        # count フレームごとに確認する
        for i in range(0, frames_all, count):
            
            # 再生フレームの指定
            inmovie.set(cv2.CAP_PROP_FRAME_COUNT, i)
            print(i, "/", frames_all)

            # フレーム取得
            ret, frame = inmovie.read()
            if not ret:
                # 再生終了
                break
            
            # 前処理
            img = preprocess(frame)
            # cv2.imshow("preprocess", img)
            # cv2.waitKey(10)

            # 惑星写ってなかったら1回おやすみ
            if not exists_planets(img):
                continue

            # 重心計算
            x, y = calc_moment(img)
            moment_pos_list.append([x, y])

            # 切り出しサイズ決定
            x1, x2, y1, y2 = calc_crop_range(width, height, x, y, crop_size)
            
            # 保存
            # 再生フレームを count フレームごとの始めに戻す
            inmovie.set(cv2.CAP_PROP_FRAME_COUNT, i)
            for j in range(count):
                
                ret, frame = inmovie.read()
                if not ret:  # 格納されてなかったら
                    break

                # print((i + j), x1, x2, y1, y2)

                frame = frame[y1 : y2, x1 : x2]
                outmovie.write(frame)

        #重心履歴の可視化
        # moment_pos_list = np.array(moment_pos_list)

        # plt.scatter(moment_pos_list[:,0], moment_pos_list[:,1],color='red', linestyle='solid', linewidth = 2.0, label='moment')
        # plt.xlabel('x', color='black', fontsize=14)
        # plt.ylabel('y', color='black', fontsize=14)
        # plt.savefig('moment.jpg', dpi=300)
        
    except ZeroDivisionError:
        pass

    except:
        traceback.print_exc()

    finally:
        outmovie.release()

if __name__ == "__main__":
    infile_pathstr = r"./test_data/P8130021.MOV"
    infile_path = pathlib.Path(infile_pathstr)
    main_cropping(infile_path, 384)
