import os
import socket
import sys
import time

import requests
from tqdm import tqdm

image_source = "https://mirror.ghproxy.com"


def download_update(url, save_path):
    try:
        socket.gethostbyname(image_source[8:])
        print("使用镜像源下载")
        url = f"{image_source}/{url}"
    except socket.error:
        print("镜像源无法连接，尝试使用github下载！")

    response = requests.get(url, stream=True)
    total_size_in_bytes = int(response.headers.get('content-length', 0))
    block_size = 1024
    progress_bar = tqdm(total=total_size_in_bytes, unit='iB', unit_scale=True, desc="下载进度")

    with open(save_path, 'wb') as f:
        for data in response.iter_content(block_size):
            progress_bar.update(len(data))
            f.write(data)

    progress_bar.close()


def read_download_url():
    try:
        file = open("updater.ini", "r")
        url = file.read()
        file.close()
        return url
    except FileNotFoundError as e:
        sys.exit()


if __name__ == '__main__':
    __version__ = "1.0.0"
    os.system(f"title 正在更新。。。 - 当前版本：{__version__}")
    Program_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
    url = read_download_url()
    if not url.startswith('https://github.com/'):
        sys.exit()
    try:
        print("正在准备更新...")
        time.sleep(2)
        try:
            os.remove(Program_dir + "\\idv-tool.exe")
        except FileNotFoundError as e:
            print("尝试删除文件失败")
        time.sleep(1)
        download_update(url, f"{Program_dir}\\idv-tool.exe")
        print("更新成功！")
        os.remove(Program_dir + "\\updater.ini")
        time.sleep(2)
        os.system(f"start {Program_dir}\\idv-tool.exe")
        time.sleep(3)
        sys.exit()
    except Exception as e:
        print(f"更新失败,错误代码{e}")
