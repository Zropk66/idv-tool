import configparser
import ctypes
import glob
import os
import platform
import socket
import sys
import time

import psutil
import requests
import win32api
from tqdm import tqdm


def is_port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(("localhost", port))
        except socket.error as e:
            return True
        return False


def is_process_running(process_name):
    for proc in psutil.process_iter(['pid', 'name']):
        if proc.info['name'].lower() == process_name.lower():
            return True
    return False


def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False


CONFIG_FILE = 'config.ini'


def ask_and_save(config_file):
    while True:
        choice = input("是否开启计时？（y/n）: ").strip().lower()
        if choice in ['y', 'n']:
            save_to_config({'settings': {'timer_enable': choice == 'y'}}, config_file)
            return choice == 'y'
        else:
            print("请输入 'y' 或 'n'.")


def save_to_config(settings_dict, config_file):
    try:
        config = configparser.ConfigParser()
        config.read(config_file)

        for section, options in settings_dict.items():
            if section not in config:
                config[section] = {}
            for key, value in options.items():
                config[section][key] = str(value)

        with open(config_file, 'w') as configfile:
            config.write(configfile)
        print(f"设置已保存到 {config_file} 文件中。")
    except KeyboardInterrupt as e:
        print("检测到用户退出程序，输入中断！")


def load_from_config():
    config = configparser.ConfigParser()
    config.read(CONFIG_FILE)
    if 'settings' in config:
        timer_enable = config['settings'].getboolean('timer_enable', fallback=False)
        return timer_enable
    else:
        return False


def find_programs(directory, program_name):
    pattern = os.path.join(directory, program_name)
    idv_login_programs = glob.glob(pattern)
    program_names = [os.path.basename(program) for program in idv_login_programs]
    return program_names


def get_file_version(file_path):
    try:
        info = win32api.GetFileVersionInfo(file_path, '\\')

        file_version = (
            info['FileVersionMS'] >> 16,
            info['FileVersionMS'] & 0xFFFF,
            info['FileVersionLS'] >> 16,
            info['FileVersionLS'] & 0xFFFF
        )

        simplified_version = f"{file_version[0]}.{file_version[1]}.{file_version[2]}"

        return simplified_version

    except Exception as e:
        print(f"获取文件版本信息失败: {str(e)}")
        return None


image_source = "https://mirror.ghproxy.com"


def idvLogin_info():
    try:
        socket.gethostbyname("api.github.com")
        github_api_url = f"https://api.github.com/repos/Alexander-Porter/idv-login/releases/latest"
    except socket.error:
        print("api.github.com连接错误，将使用镜像源！")
        github_api_url = f"http://47.94.167.221:1563/repos/Alexander-Porter/idv-login/releases/latest"

    try:
        response = requests.get(github_api_url)
        if response.status_code == 200:
            release_info = response.json()
            return release_info

        else:
            print(f"无法获取发布信息。状态码: {response.status_code}")
            return False
    except Exception:
        print("获取api信息出现错误，请确保您的网络环境良好，本次更新跳过！")


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


def check_update(program_dir, program_name):
    try:
        release_info = idvLogin_info()

        if int(platform.release()) <= 7:
            download_url = release_info['assets'][2]['browser_download_url']
        else:
            download_url = release_info['assets'][0]['browser_download_url']

        file_path = program_dir + "\\" + program_name
        current_version = get_file_version(file_path)
        version = release_info['name']
        latest_version = version[1:6]

        if current_version == latest_version:
            return True
        else:
            print("检测到新版本！")
            try:
                os.remove(file_path)
                print("正在更新...")
                if int(platform.release()) <= 7:
                    download_update(download_url, f"{Program_dir}\\{release_info['assets'][2]['name']}")
                else:
                    download_update(download_url, f"{Program_dir}\\{release_info['assets'][0]['name']}")
                print("更新成功！")

                return release_info
            except OSError as e:
                print(f"删除旧文件时出错: {e}")
            return False

    except Exception as e:
        print(f"更新失败!,错误代码: {e}")


def disable_quickedit():
    kernel32 = ctypes.windll.kernel32
    kernel32.SetConsoleMode(kernel32.GetStdHandle(-10), (0x4 | 0x80 | 0x20 | 0x2 | 0x10 | 0x1 | 0x00 | 0x100))


if __name__ == '__main__':
    try:
        __version__ = '1.4.0'
        CONFIG_FILE = 'config.ini'
        os.system(f"title 第五人格小助手 - 当前版本：{__version__}")

        Program_dir = os.path.dirname(os.path.abspath(sys.argv[0]))

        dwrg_program = find_programs(Program_dir, 'dwrg.exe')

        if not dwrg_program:
            print("当前文件夹未找到第五人格， 请将程序放置在第五人格根目录后再运行！")
            os.system("pause")
            sys.exit()
        else:
            print(f"成功找到第五人格，路径：{Program_dir}\{dwrg_program[0]}")

        idv_login_program = find_programs(Program_dir, 'idv-login*')

        if len(idv_login_program) > 1:
            print("识别到当前目录有多个 idv-login 将自动删除并自动下载最新版本！")
            for program in idv_login_program:
                os.remove(program)
            idv_login_program.clear()
        else:
            if not idv_login_program:
                print("未在当前目录找到idv-login正在尝试下载")

        if not idv_login_program:
            try:
                release_info = idvLogin_info()
                if int(platform.release()) <= 7:
                    download_url = release_info['assets'][2]['browser_download_url']
                    download_update(download_url, f"{Program_dir}\\{release_info['assets'][2]['name']}")
                else:
                    download_url = release_info['assets'][0]['browser_download_url']
                    download_update(download_url, f"{Program_dir}\\{release_info['assets'][0]['name']}")

                print("下载成功！")
                idv_login_program = find_programs(Program_dir, 'idv-login*')
            except Exception as e:
                print(f"下载失败!: {e}")
                os.system("pause")
                sys.exit()

        idv_login_program = idv_login_program[0]

        print(f"成功找到idv-login，路径:{Program_dir}\{idv_login_program}")

        if idv_login_program:
            check_update(Program_dir, idv_login_program)

        if not os.path.exists(CONFIG_FILE):
            timer_enable = ask_and_save(CONFIG_FILE)
        else:
            timer_enable = load_from_config()

        if timer_enable:
            print("计时已开启。(若需要关闭计时器可以在本工具同级目录找到“config.ini”文件，将其值改为False即可)")
        else:
            print("计时未开启。(若需要开启计时器可以在本工具同级目录找到“config.ini”文件，将其值改为True即可)")

        if is_admin():
            disable_quickedit()
            print("正在启动登录工具...")
            os.system("start " + Program_dir + "\\" + idv_login_program)
            while not is_port_in_use(443):
                time.sleep(1)
            print("登录工具启动成功，正在唤醒第五人格！")
            os.system("start " + Program_dir + "\dwrg.exe")

            # print("正在等待第五人格运行... (第五人格若在 10 秒后还未启动程序将自动关闭)")

            for i in range(10):
                if is_process_running("dwrg.exe"):
                    print("第五人格已启动！")
                    break
                elif i == 9:
                    print("第五人格启动超时，程序已退出！")
                    os.system("pause")
                    sys.exit()
                time.sleep(1)

            if timer_enable:
                second = 0
                minute = 0
                hour = 0

                time.sleep(5)

                while is_process_running("dwrg.exe"):
                    if second >= 60:
                        second -= 60
                        minute += 1
                    elif minute >= 60:
                        minute -= 60
                        hour += 1
                    os.system("cls")
                    print("第五人格运行中...")
                    print(f"已运行 {str(hour)} 时 {str(minute)} 分 {str(second)} 秒")
                    second += 1
                    time.sleep(1)
            else:
                sys.exit()

            print("第五人格已关闭...")
            if is_process_running(idv_login_program):
                os.system(f"taskkill /im {idv_login_program} /f")
                print("登录工具已关闭已关闭...")
            print("程序即将关闭...")
            time.sleep(1)
            sys.exit()
        else:
            ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, __file__, None, 1)
    except Exception as e:
        print(f"程序出现未知错误，现已退出！错误代码:{e}")
        os.system("pause")
