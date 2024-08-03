import configparser
import ctypes
import glob
import hashlib
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
        except socket.error:
            return True
        return False


def is_process_running(process_name):
    for proc in psutil.process_iter(['pid', 'name']):
        if proc.info['name'].lower() == process_name.lower():
            return True
    return False


def find_program(directory, program_name):
    pattern = os.path.join(directory, program_name)
    idv_login_programs = glob.glob(pattern)
    # program_names = [os.path.basename(programs) for programs in idv_login_programs]
    return [os.path.basename(programs) for programs in idv_login_programs]


def get_version(file_path):
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


def Timer_module(config_file):
    while True:
        choice = input("是否开启计时？（y/n）: ").strip().lower()
        if choice in ['y', 'n']:
            save_to_config({'settings': {'timer_enable': choice == 'y'}}, config_file)
            return choice == 'y'
        else:
            print("请输入 'y' 或 'n'.")


def get_file_hash(file_path: str, hash_method) -> str:
    if not os.path.isfile(file_path):
        print('文件不存在。')
        return ''
    h = hash_method()
    with open(file_path, 'rb') as f:
        while b := f.read(8192):
            h.update(b)
    return h.hexdigest()


def check_hash(idv_login_release_info):
    current_hash = get_file_hash(f"{Program_dir}\\{idv_login_program}", hashlib.sha256)
    hash_from_config = load_from_config(CONFIG_FILE, "idv-login", "hash")

    if hash_from_config is None or current_hash.upper() != hash_from_config.upper():
        print("验证失败，可能是 idv-login 已损坏!")
        print("正在尝试下载最新 idv-login...")

        download_index = get_download_index(idv_login_release_info, False)
        download_url = get_download_url(idv_login_release_info, False)
        download_file(download_url, f"{Program_dir}\\{idv_login_release_info['assets'][download_index]['name']}")

        hash_url = get_download_url(idv_login_release_info, True)
        download_file(hash_url, f"{Program_dir}\\hash.sha256")
        with open(f"{Program_dir}\\hash.sha256", "r") as f:
            hash_value = f.read().strip()
        save_to_config({'idv-login': {'hash': hash_value}}, CONFIG_FILE)
    if current_hash.upper() == hash_from_config.upper():
        return True


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
    except KeyboardInterrupt:
        print("检测到用户退出程序，输入中断！")


def load_from_config(config_path, section, key):
    config = configparser.ConfigParser()
    config.read(config_path)

    return config.get(section, key, fallback=None)


def get_info(mode, updater):
    if mode == "idv-login":
        Author_name = "Alexander-Porter"
        repository_name = "idv-login"
        repository_info = "releases/latest"
    elif mode == "idv-tool":
        Author_name = "Zropk66"
        repository_name = "idv-tool"
        repository_info = "contents" if updater else "releases/latest"

        # if updater:
        #     repository_info = "contents"
        # else:
        #     repository_info = "releases/latest"
    else:
        print("无效更新模式")
        return None

    try:
        socket.gethostbyname("api.github.com")
        github_api_url = f"https://api.github.com/repos/{Author_name}/{repository_name}/{repository_info}"
    except socket.error:
        print("api.github.com连接错误，将使用镜像源！")
        github_api_url = f"http://47.94.167.221:1563/repos/{Author_name}/{repository_name}/{repository_info}"

    try:
        response = requests.get(github_api_url)
        if response.status_code == 200:
            # release_info = response.json()
            # return release_info
            return response.json()
        else:
            print(f"无法获取发布信息。状态码: {response.status_code}")
            return False
    except requests.exceptions.ConnectTimeout:
        print("获取api信息出现错误，请确保您的网络环境良好，本次更新跳过！")


def download_file(url, save_path):
    try:
        try:
            os.remove(save_path)
            print()
        except FileNotFoundError:
            print()

        socket.gethostbyname(image_source[8:])
        print("使用镜像源下载！")
        url = f"{image_source}/{url}"
    except socket.error:
        print("镜像源无法连接，尝试使用github官方源下载！")
    try:
        response = requests.get(url, stream=True)
        total_size_in_bytes = int(response.headers.get('content-length', 0))
        block_size = 1024
        progress_bar = tqdm(total=total_size_in_bytes, unit='iB', unit_scale=True, desc="下载进度")

        with open(save_path, 'wb') as f:
            for data in response.iter_content(block_size):
                progress_bar.update(len(data))
                f.write(data)
        progress_bar.close()
    except KeyboardInterrupt:
        print("检测到程序被强制关闭...")
        os.remove(save_path)
        time.sleep(3)
        sys.exit()


def check_update(idv_login_release_info, idv_tool_release_info, program_dir, program_name):
    latest_idv_tool_version = idv_tool_release_info['tag_name']
    if __version__ < latest_idv_tool_version:
        print("检测到本工具存在新版本！")

        if not find_program(Program_dir, 'updater.exe'):
            idv_tool_update_info = get_info("idv-tool", True)
            index = 0

            while True:
                try:
                    name = idv_tool_update_info[index]['name']
                    if name == "updater.exe":
                        break
                    index += 1
                except IndexError:
                    break

            # for k in info:
            #     name = info[i]['name']
            #     if name == "updater.exe":
            #         break
            #     i += 1

            download_url = idv_tool_update_info[index]['download_url']

            download_file(download_url, idv_tool_update_info[index]['name'])

        updater_url = idv_tool_release_info['assets'][0]['browser_download_url']
        file = open("updater.ini", "w")
        file.write(updater_url)
        file.close()

        os.system("start " + program_dir + "\\updater.exe")
        sys.exit()

    try:
        # if int(platform.release()) <= 7:
        #     download_url = idv_login_release_info['assets'][2]['browser_download_url']
        # else:
        #     download_url = idv_login_release_info['assets'][0]['browser_download_url']

        file_path = program_dir + "\\" + program_name
        current_version = get_version(file_path)
        version = idv_login_release_info['tag_name']
        latest_version = version[1:6]

        if current_version == latest_version:
            return True
        else:
            print("检测到 idv-login 存在新版本！")
            try:
                os.remove(file_path)
                print("正在更新...")
                download_index = get_download_index(idv_login_release_info, False)
                download_file(get_download_url(idv_login_info, False),
                              f"{Program_dir}\\{idv_login_release_info['assets'][download_index]['name']}")
                # if int(platform.release()) <= 7:
                #     download_update(download_url, f"{Program_dir}\\{idv_login_release_info['assets'][2]['name']}")
                # else:
                #     download_update(download_url, f"{Program_dir}\\{idv_login_release_info['assets'][0]['name']}")
                print("更新成功！")

                return idv_login_release_info
            except OSError as OSErrorPrint:
                print(f"删除旧文件时出错: {OSErrorPrint}")
            return False
    except Exception as e:
        print(f"更新失败!,错误代码: {e}")


def disable_quick_edit():
    kernel32 = ctypes.windll.kernel32
    kernel32.SetConsoleMode(kernel32.GetStdHandle(-10), (0x4 | 0x80 | 0x20 | 0x2 | 0x10 | 0x1 | 0x00 | 0x100))


def get_download_index(info, get_hash):
    end = "sha256" if get_hash else "exe"
    version = "Py3.12" if int(platform.release()) > 7 else "Py3.8"

    index = 0
    while True:
        try:
            name = info['assets'][index]['name']
            if name.startswith("idv-login") and name.endswith(end) and version in name:
                break
            index += 1
        except IndexError:
            print("错误")
            break
    return index


def get_download_url(info, get_hash: bool):
    index = get_download_index(info, get_hash)
    download_url = info['assets'][index]['browser_download_url']
    return download_url


if __name__ == '__main__':
    # try:
    __version__ = '1.4.4'
    CONFIG_FILE = 'config.ini'
    image_source = "https://mirror.ghproxy.com"

    idv_login_info = get_info("idv-login", False)
    idv_tool_info = get_info("idv-tool", False)

    Program_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
    dwrg_program = find_program(Program_dir, 'dwrg.exe')

    os.system(f"title 第五人格小助手 - 当前版本：{__version__}")

    if not dwrg_program:
        print("当前文件夹未找到第五人格， 请将程序放置在第五人格根目录后再运行！")
        os.system("pause")
        sys.exit()
    else:
        print(f"成功找到第五人格，路径：{Program_dir}\\{dwrg_program[0]}")

    idv_login_program = find_program(Program_dir, 'idv-login*')

    if len(idv_login_program) > 1:
        print("识别到当前目录有多个 idv-login 将自动删除并下载最新版本！")
        for program in idv_login_program:
            os.remove(program)
        idv_login_program.clear()
    elif not idv_login_program:
        print("未在当前目录找到idv-login正在尝试下载")

    if not idv_login_program:
        try:
            download_index = get_download_index(idv_login_info, False)
            download_file(get_download_url(idv_login_info, False),
                          f"{Program_dir}\\{idv_login_info['assets'][download_index]['name']}")
            # if int(platform.release()) <= 7:
            #     download_url = release_info['assets'][2]['browser_download_url']
            #     download_update(download_url, f"{Program_dir}\\{release_info['assets'][2]['name']}")
            # else:
            #     download_url = release_info['assets'][0]['browser_download_url']
            #     download_update(download_url, f"{Program_dir}\\{release_info['assets'][0]['name']}")

            print("下载成功！")
            hash_url = get_download_url(idv_login_info, True)
            download_file(hash_url, f"{Program_dir}\\hash.sha256")
            with open(f"{Program_dir}\\hash.sha256", "r") as f:
                hash_value = f.read().strip()
            save_to_config({'idv-login': {'hash': hash_value}}, CONFIG_FILE)
        except Exception as e:
            print(f"下载失败!: {e}")
            os.system("pause")
            sys.exit()

    idv_login_program = find_program(Program_dir, 'idv-login*')[0]
    print(f"成功找到idv-login，路径:{Program_dir}\\{idv_login_program}")

    check_hash(idv_login_info)
    try:
        os.remove(Program_dir + "\\hash.sha256")
    except FileNotFoundError:
        print()

    if idv_login_program:
        check_update(idv_login_info, idv_tool_info, Program_dir, idv_login_program)

    if not os.path.exists(CONFIG_FILE):
        timer_enable = Timer_module(CONFIG_FILE)
    else:
        timer_enable = load_from_config(CONFIG_FILE, "settings", "timer_enable")

    if timer_enable:
        print("计时已开启。(若需要关闭计时器可以在本工具同级目录找到“config.ini”文件，将其值改为False即可)")
    else:
        print("计时未开启。(若需要开启计时器可以在本工具同级目录找到“config.ini”文件，将其值改为True即可)")

    if ctypes.windll.shell32.IsUserAnAdmin():
        disable_quick_edit()
        print("正在启动登录工具...")
        os.system("start " + Program_dir + "\\" + idv_login_program)
        while not is_port_in_use(443):
            time.sleep(1)
        print("登录工具启动成功，正在唤醒第五人格！")
        os.system("start " + Program_dir + "\\dwrg.exe")

        # print("正在等待第五人格运行... (第五人格若在 10 秒后还未启动程序将自动关闭)")

        for timing in range(10):
            if is_process_running("dwrg.exe"):
                print("第五人格已启动！")
                break
            elif timing == 9:
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
# except Exception as e:
#     print(f"程序出现未知错误，现已退出！错误代码:{e}")
#     os.system("pause")
