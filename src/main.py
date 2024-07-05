import socket
import sys
import time

import psutil
import ctypes
import os
import configparser


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


def ask_and_save():
    while True:
        choice = input("是否开启计时？（y/n）: ").strip().lower()
        if choice in ['y', 'n']:
            save_to_config(choice == 'y')
            return choice == 'y'
        else:
            print("请输入 'y' 或 'n'.")


def save_to_config(enabled):
    config = configparser.ConfigParser()
    config['settings'] = {
        'timing_enabled': str(enabled)
    }
    with open(CONFIG_FILE, 'w') as configfile:
        config.write(configfile)


def load_from_config():
    config = configparser.ConfigParser()
    config.read(CONFIG_FILE)
    if 'settings' in config:
        timing_enabled = config['settings'].getboolean('timing_enabled', fallback=False)
        return timing_enabled
    else:
        return False

if __name__ == '__main__':

    __version__ = '1.1.0'

    if not os.path.exists(CONFIG_FILE):
        ask_and_save()
        timing_enabled = load_from_config()
    else:
        timing_enabled = load_from_config()

    if timing_enabled:
        print("计时已开启。")
    else:
        print("计时未开启。")

    # 如果第一次运行或者需要重新设置选项，则询问用户并保存到配置文件
    if timing_enabled is None:
        timing_enabled = ask_and_save()
        print("已保存设置。")

    os.system("title 第五人格小助手 - " + __version__)

    # Program_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
    Program_dir = "E:\\Netease\\dwrg"

    if is_admin():

        print("正在启动登录工具...")
        result = os.system("start " + Program_dir + "\idv-login.exe")
        if result == 1:
            print("请将登录工具的名字修改为 《idv-login.exe》后再重试！")
        while not is_port_in_use(443):
            time.sleep(1)
        print("登录工具启动成功，正在唤醒第五人格！")
        os.system("start " + Program_dir + "\dwrg.exe")

        print("正在等待第五人格运行... \n(第五人格若在 10 秒后还未启动程序将自动关闭)")
        if is_process_running("dwrg.exe"):
            print("第五人格已启动！")
        else:
            for i in range(10):
                if is_process_running("dwrg.exe"):
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
        if is_process_running("idv-login.exe"):
            os.system("taskkill /im idv-login.exe /f")
            print("登录工具已关闭已关闭...")
        print("程序即将关闭...")
        time.sleep(1)
        sys.exit()
    else:
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, __file__, None, 1)
