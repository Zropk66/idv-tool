import glob
import socket
import sys
import time

import psutil
import ctypes
import os
import configparser

import requests
import win32api


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
            save_to_config({'settings': {'timing_enabled': choice == 'y'}}, config_file)
            return choice == 'y'
        else:
            print("请输入 'y' 或 'n'.")


def save_to_config(settings_dict, config_file):
    config = configparser.ConfigParser()
    config.read(config_file)

    for section, options in settings_dict.items():
        if section not in config:
            config[section] = {}
        for idx, program in enumerate(options):
            config[section][f'program_{idx + 1}'] = program

    with open(config_file, 'w') as configfile:
        config.write(configfile)
    print(f"设置已保存到 {config_file} 文件中。")


def load_from_config():
    config = configparser.ConfigParser()
    config.read(CONFIG_FILE)
    if 'settings' in config:
        timer_enable = config['settings'].getboolean('timing_enabled', fallback=False)
        return timer_enable
    else:
        return False


def find_idv_login_programs(directory):
    pattern = os.path.join(directory, 'idv-login*')
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


def update(url, save_path):
    print("正在更新...")
    response = requests.get(url)
    with open(save_path, 'wb') as f:
        f.write(response.content)


def check_and_update(Program_dir, idv_login_program_name):
    github_repo_owner = "Alexander-Porter"
    github_repo_name = "idv-login"

    # GitHub API的基础URL
    github_api_url = f"https://api.github.com/repos/{github_repo_owner}/{github_repo_name}/releases/latest"
    try:
        response = requests.get(github_api_url)
        if response.status_code == 200:
            release_info = response.json()

            download_url = release_info['assets'][0]['browser_download_url']

            file_path = Program_dir + "\\" + idv_login_program_name
            current_version = get_file_version(file_path)
            version = release_info['name']
            latest_version = version[1:6]

            if current_version == latest_version:
                print("无需更新")
                return True
            else:
                update(download_url, f"D:\\Misc\\{release_info['assets'][0]['name']}")
                print("更新成功！")
                try:
                    os.remove(file_path)
                    print("请重新打开本程序")
                    time.sleep(3)
                    sys.exit()
                except OSError as e:
                    print(f"删除旧文件时出错: {e}")
                return False
        else:
            print(f"无法获取发布信息。状态码: {response.status_code}")
    except Exception as e:
        print(f"更新失败!: {e}")


if __name__ == '__main__':
    __version__ = '1.2.0'
    CONFIG_FILE = 'config.ini'

    Program_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
    # Program_dir = "E:\\Netease\\dwrg"

    idv_login_programs = find_idv_login_programs(Program_dir)
    if not idv_login_programs:
        print("未找到登陆程序，请将登陆程序放在与本程序一起放在第五人格根目录")
        os.system("pause")
        sys.exit()
    else:
        idv_login_program_name = idv_login_programs[0]

    check_and_update(Program_dir, idv_login_program_name)

    if not os.path.exists(CONFIG_FILE):
        timing_enabled = ask_and_save(CONFIG_FILE)
    else:
        timing_enabled = load_from_config()

    if timing_enabled:
        print("计时已开启。")
    else:
        print("计时未开启。")

    if is_admin():
        print("正在启动登录工具...")
        os.system("start " + Program_dir + "\\" + idv_login_program_name)
        while not is_port_in_use(443):
            time.sleep(1)
        print("登录工具启动成功，正在唤醒第五人格！")
        os.system("start " + Program_dir + "\dwrg.exe")

        print("正在等待第五人格运行... \n(第五人格若在 10 秒后还未启动程序将自动关闭)")

        for i in range(10):
            if is_process_running("dwrg.exe"):
                print("第五人格已启动！")
                break
            time.sleep(1)

        if timing_enabled:
            second = 0
            minute = 0
            hour = 0

            while is_process_running("dwrg.exe"):
                if second >= 60:
                    second -= 60
                    minute += 1
                elif minute >= 60:
                    minute -= 60
                    hour += 1
                os.system("cls")
                print("第五人格运行中...")
                print("已运行 " + str(hour) + " 时 " + str(minute) + " 分 " + str(second) + " 秒")
                second += 1
                time.sleep(1)
        else:
            sys.exit()

        print("第五人格已关闭...")
        if is_process_running(idv_login_program_name):
            os.system(f"taskkill /im {idv_login_program_name} /f")
            print("登录工具已关闭已关闭...")
        print("程序即将关闭...")
        time.sleep(1)
        sys.exit()
    else:
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, __file__, None, 1)
