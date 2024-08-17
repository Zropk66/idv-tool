import configparser
import ctypes
import glob
import hashlib
import os
import platform
import socket
import sys
import time
from datetime import datetime

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


def find_program(program_name):
    pattern = os.path.join(Program_dir, program_name)
    idv_login_programs = glob.glob(pattern)
    return [os.path.basename(programs) for programs in idv_login_programs]


def disable_quick_edit():
    kernel32 = ctypes.windll.kernel32
    kernel32.SetConsoleMode(kernel32.GetStdHandle(-10), (0x4 | 0x80 | 0x20 | 0x2 | 0x10 | 0x1 | 0x00 | 0x100))


def load_module_config():
    global timer_enable, save_playtime_enable, auto_update_enable, auto_exit_idv_login_enable

    check_config()

    auto_update_enable = load_from_config("settings", "auto update")
    timer_enable = load_from_config("settings", "timer")
    save_playtime_enable = load_from_config("settings", "save playtime")
    auto_exit_idv_login_enable = load_from_config("settings", "auto exit idv-login")


def check_config():
    all_config = {"auto update": "是否开启自动更新?",
                  "timer": "是否开启计时器？",
                  "save playtime": "是否保存游玩时间？",
                  "auto exit idv-login": "是否开启自动退出idv-login?"
                  }

    configs = configparser.ConfigParser()
    configs.read("config.ini")

    for key, description in all_config.items():
        config_status = configs.get("settings", key, fallback="None")
        if config_status == "None":
            while True:
                choice = input(f"{description}（y/n）: ").strip().lower()
                if choice in ['y', 'n']:
                    save_to_config({'settings': {key: choice == 'y'}})
                    break
                else:
                    print("请输入 'y' 或 'n'.")


def save_to_config(settings_dict):
    try:
        config = configparser.ConfigParser()
        config.read(CONFIG_FILE)

        for section, options in settings_dict.items():
            if section not in config:
                config[section] = {}
            for key, value in options.items():
                config[section][key] = str(value)

        config.write(open(CONFIG_FILE, 'w'))
    except KeyboardInterrupt:
        print("检测到用户退出程序，输入中断！")


def load_from_config(section, key):
    try:
        config = configparser.ConfigParser()
        config.read(CONFIG_FILE)

        value = config.get(section, key, fallback=None)
        if value in ("True", "False"):
            value = eval(value)
        return value
    except Exception as load_from_config_exception:
        print(f"加载配置时发生错误：{load_from_config_exception}")
        return None


def auto_update():
    try:
        print("正在检查工具更新，可能需要一点时间...")
        check_hash()
        try:
            os.remove(os.path.join(Program_dir, "hash.sha256"))
        except FileNotFoundError:
            pass
        if idv_login_program is True:
            check_update()
        return True
    except (requests.exceptions.ConnectTimeout, requests.exceptions.ConnectionError):
        print("无法连接更新服务器，请确保您目前使用的网络能够正常访问 api.github.com")
        print("本次更新跳过！")


def auto_exit_idv_login_module():
    path = "C:\\ProgramData\\idv-login\\log.txt"
    find = False
    print("正在等待游戏登录...")

    while not find and is_process_running("dwrg.exe"):
        with open(path, 'r', encoding='utf-8') as file:
            log_list = file.readlines()
        log = log_list[-1]

        login_successful = {"('verify_status', '1')", "渠道服登录信息已更新"}

        for login_message in login_successful:
            if login_message in log:
                print("登录成功！")
                os.system(f"taskkill /im {idv_login_program} /f")
                find = True
        time.sleep(1)


def get_file_hash(file_path: str, hash_method) -> str:
    if not os.path.isfile(file_path):
        print('文件不存在。')
        return ''
    h = hash_method()
    with open(file_path, 'rb') as f:
        while b := f.read(8192):
            h.update(b)
    return h.hexdigest()


def get_info(mode, updater):
    if mode == "idv-login":
        Author_name = "Alexander-Porter"
        repository_name = "idv-login"
        repository_info = "releases/latest"
    elif mode == "idv-tool":
        Author_name = "Zropk66"
        repository_name = "idv-tool"
        repository_info = "contents" if updater else "releases/latest"
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
        response = requests.get(github_api_url, timeout=10000)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"无法获取发布信息。状态码: {response.status_code}")
            return False
    except (requests.exceptions.ConnectTimeout, requests.exceptions.Timeout):
        print("获取api信息超时！")
    except requests.exceptions.RequestException as get_info_request_exception:
        print(f"请求错误: {get_info_request_exception}")


def get_download_index(info, get_hash):
    suffix = "sha256" if get_hash else "exe"
    version = "Py3.12" if int(platform.release()) > 7 else "Py3.8"

    index = 0
    while True:
        try:
            name = info['assets'][index]['name']
            if name.startswith("idv-login") and name.endswith(suffix) and version in name:
                break
            index += 1
        except IndexError:
            break
    return index


def get_download_url(info, get_hash: bool):
    index = get_download_index(info, get_hash)
    return info['assets'][index]['browser_download_url']


def download_file(url, save_path):
    try:
        os.remove(save_path)
    except FileNotFoundError:
        pass

    try:
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
    except requests.exceptions.RequestException:
        print("下载异常！")
        try:
            os.remove(save_path)
        except FileNotFoundError:
            pass
        time.sleep(3)
        sys.exit()


def check_update():
    latest_idv_tool_version = idv_tool_info['tag_name']
    if __version__ < latest_idv_tool_version:
        print("检测到本工具存在新版本！")

        if not find_program('updater.exe'):
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
            download_file(idv_tool_update_info[index]['download_url'], idv_tool_update_info[index]['name'])

        updater_url = idv_tool_info['assets'][0]['browser_download_url']
        file = open("updater.ini", "w")
        file.write(updater_url)
        file.close()

        os.system("start " + Program_dir + "\\updater.exe")
        sys.exit()


def get_idv_tool_latest_hash():
    download_hash_url = get_download_url(idv_login_info, True)
    open(f'{Program_dir}\\hash.sha256', 'wb').write(requests.get(download_hash_url, stream=True).content)
    latest_hash_value = open(f"{Program_dir}\\hash.sha256", "r").read().strip()
    return latest_hash_value


def check_hash():
    current_hash = get_file_hash(f"{Program_dir}\\{idv_login_program[0]}", hashlib.sha256)

    latest_hash_value = get_idv_tool_latest_hash()

    if current_hash.upper() != latest_hash_value.upper():
        print("验证失败，可能是 idv-login 已损坏 或 已更新...!")
        print("正在尝试下载最新 idv-login...")
        os.remove(f"{Program_dir}\\{idv_login_program[0]}")

        idv_login_download_index = get_download_index(idv_login_info, False)
        idv_login_download_url = get_download_url(idv_login_info, False)
        idv_login_save_path = f"{Program_dir}\\{idv_login_info['assets'][idv_login_download_index]['name']}"
        download_file(idv_login_download_url, idv_login_save_path)
        current_hash = get_file_hash(f"{Program_dir}\\{idv_login_program[0]}", hashlib.sha256)

    if current_hash.upper() == latest_hash_value.upper():
        return True


class operational_status:
    def __init__(self):
        self.start_time = None
        win32api.SetConsoleCtrlHandler(self.on_exit, True)
        self.play_log_file = f"{Program_dir}\\playtime.log"

    def get_running_time(self):
        global hours, minutes, seconds
        current_time = datetime.now()
        time_diff = current_time - self.start_time

        total_seconds = int(time_diff.total_seconds())

        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60

        return f"{hours} 时 {minutes} 分 {seconds} 秒"

    def save_playtime(self):
        global hours, minutes, seconds
        end_time = datetime.now()
        today_date = time.strftime('%Y-%m-%d', time.localtime())

        fond_write = (f"开始时间: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}\n"
                      f"结束时间: {end_time.strftime('%Y-%m-%d %H:%M:%S')}\n"
                      f"游玩时长: {hours} 时 {minutes} 分 {seconds} 秒\n\n")
        no_fond_write = (f"[{today_date}]\n"
                         f"开始时间: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}\n"
                         f"结束时间: {end_time.strftime('%Y-%m-%d %H:%M:%S')}\n"
                         f"游玩时长: {hours} 时 {minutes} 分 {seconds} 秒\n\n")
        if not os.path.exists(self.play_log_file):
            open(self.play_log_file, 'w').close()

        found = False
        with open(self.play_log_file, 'r+', encoding='utf-8') as file:
            allLines = file.readlines()

            for line in reversed(allLines):
                if f"[{today_date}]" in line:
                    found = True
                    break
            if not found:
                file.write(no_fond_write)
            else:
                file.write(fond_write)
            file.close()

    def run(self):
        global save_playtime_enable
        try:
            if auto_exit_idv_login_enable:
                auto_exit_idv_login_module()
            os.system("cls")
            self.start_time = datetime.now()
            while is_process_running("dwrg.exe"):
                time.sleep(1)
                print("\033[0;0H第五人格运行中...")
                print(f"已运行 {self.get_running_time()}   ")
            if save_playtime_enable:
                self.save_playtime()
                print("游玩时间已保存！")

            if is_process_running(idv_login_program):
                os.system(f"taskkill /im {idv_login_program} /f")
                print("登录工具已关闭已关闭...")
            print("程序即将关闭...")
            time.sleep(1)
            sys.exit()
        except KeyboardInterrupt:
            self.on_exit(self)

    def on_exit(self, signal_type):
        print("检测到强制退出！游玩时间将不会保存！")
        time.sleep(1)
        sys.exit()


if __name__ == '__main__':
    try:
        disable_quick_edit()
        __version__ = '1.5.7'
        CONFIG_FILE = 'config.ini'
        image_source = "https://mirror.ghproxy.com"

        global hours, minutes, seconds
        global timer_enable, save_playtime_enable, auto_update_enable, auto_exit_idv_login_enable

        idv_login_info = get_info("idv-login", False)
        idv_tool_info = get_info("idv-tool", False)

        Program_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
        dwrg_program = find_program('dwrg.exe')

        os.system(f"title 第五人格小助手 - 当前版本：{__version__}")

        if not dwrg_program:
            print("当前文件夹未找到第五人格， 请将程序放置在第五人格根目录后再运行！")
            os.system("pause")
            sys.exit()
        else:
            print(f"成功找到第五人格，路径：{Program_dir}\\{dwrg_program[0]}\n")

        if not os.path.exists(f"{Program_dir}\\config.ini"):
            open(f"{Program_dir}\\config.ini", "w").write("")

        idv_login_program = find_program('idv-login*')

        if len(idv_login_program) > 1:
            try:
                print("识别到当前目录有多个 idv-login")
                latest_hash = get_idv_tool_latest_hash()

                for program in idv_login_program:
                    current_hash = get_file_hash(os.path.join(Program_dir, program), hashlib.sha256)
                    if latest_hash.upper() == current_hash.upper():
                        temp_idv_login_program = program
                        for program_rm in idv_login_program:
                            if program_rm != temp_idv_login_program:
                                os.remove(os.path.join(Program_dir, program_rm))
                        idv_login_program = temp_idv_login_program
                        break
                    else:
                        os.remove(os.path.join(Program_dir, program))
            except (requests.exceptions.ConnectTimeout, requests.exceptions.ConnectionError):
                print("获取最新hash值失败，将随机使用一个idv-login")
                print("若随机使用的 idv-login 无法打开，请确保网络能正常访问 api.github.com 或自行下载最新 idv-login")
                idv_login_program = idv_login_program[0]
        elif not idv_login_program:
            try:
                print("未在当前目录找到 idv-login 正在尝试下载...")
                download_index = get_download_index(idv_login_info, False)
                download_url = get_download_url(idv_login_info, False)
                download_file(download_url, f"{Program_dir}\\{idv_login_info['assets'][download_index]['name']}")
                print("下载成功！")
                idv_login_program = find_program('idv-login*')[0]

            except Exception as e:
                print(f"下载失败!: {e}")
                os.system("pause")
                sys.exit()
        elif len(idv_login_program) == 1:
            idv_login_program = idv_login_program[0]

        print(f"成功找到idv-login，路径:{Program_dir}\\{idv_login_program}\n")

        load_module_config()

        if auto_update_enable is True:
            auto_update()
        else:
            print("自动更新已关闭。若需要开启可以在本工具同级目录找到“config.ini”文件，将其值改为True即可\n")

        if timer_enable is True:
            print("计时已开启。(若需要关闭计时器可以在本工具同级目录找到“config.ini”文件，将其值改为False即可)\n")
        else:
            print("计时未开启。(若需要开启计时器可以在本工具同级目录找到“config.ini”文件，将其值改为True即可)\n")

        if save_playtime_enable is True:
            print(
                "保存游戏时间已开启。(若不需要保存时间功能可以在本工具同级目录找到“config.ini”文件，将其值改为False即可)\n")
        else:
            print(
                "保存游戏时间未开启。(若需要保存时间功能可以在本工具同级目录找到“config.ini”文件，将其值改为True即可)\n")

        if ctypes.windll.shell32.IsUserAnAdmin():
            print("正在启动idv-login...\n")
            os.system("start " + Program_dir + "\\" + idv_login_program)
            while not is_port_in_use(443):
                time.sleep(1)
            print("idv-login启动成功，正在唤醒第五人格！\n")
            os.system("start " + Program_dir + "\\dwrg.exe")

            for timing in range(10):
                if is_process_running("dwrg.exe"):
                    print("第五人格已启动！\n")
                    break
                elif timing == 9:
                    print("第五人格启动超时，程序已退出！")
                    os.system("pause")
                    sys.exit()
                time.sleep(1)

            time.sleep(3)
            if timer_enable:
                operational_status().run()
            else:
                if auto_exit_idv_login_enable:
                    auto_exit_idv_login_module()
                sys.exit()

        else:
            ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, __file__, None, 1)
    except Exception as e:
        print(f"程序出现未知错误，现已退出！错误代码:{e}")
        os.system("pause")
