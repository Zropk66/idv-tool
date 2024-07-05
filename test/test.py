import os

import requests
import win32api

import os
import glob

Program_dir = "D:\\Zropk\\Documents\\"
idv_login_program_name = "123"


def get_file_version(file_path):
    try:
        info = win32api.GetFileVersionInfo(file_path, '\\')

        # 提取文件版本号
        file_version = (
            info['FileVersionMS'] >> 16,
            info['FileVersionMS'] & 0xFFFF,
            info['FileVersionLS'] >> 16,
            info['FileVersionLS'] & 0xFFFF
        )

        # 仅保留主版本号、次版本号和修订版本号
        simplified_version = f"{file_version[0]}.{file_version[1]}.{file_version[2]}"

        return simplified_version

    except Exception as e:
        print(f"获取文件版本信息失败: {str(e)}")
        return None


# # GitHub仓库信息
# github_repo_owner = "Alexander-Porter"
# github_repo_name = "idv-login"
#
# # GitHub API的基础URL
# github_api_url = f"https://api.github.com/repos/{github_repo_owner}/{github_repo_name}/releases/latest"
#
# def update(url, save_path):
#     print("正在更新...")
#     response = requests.get(url)
#     with open(save_path, 'wb') as f:
#         f.write(response.content)
#
# def check_and_update():
#     try:
#         # 发送请求获取最新发布信息
#         response = requests.get(github_api_url)
#         if response.status_code == 200:
#             release_info = response.json()
#
#             download_url = release_info['assets'][0]['browser_download_url']
#
#             file_path = Program_dir + "\\" + idv_login_program_name
#             current_version = get_file_version(file_path)
#             version = release_info['name']
#             latest_version = version[1:6]
#
#             if current_version == latest_version:
#                 return True
#             else:
#                 update(download_url, f"D:\\Misc\\{release_info['assets'][0]['name']}")
#                 print("更新成功！")
#                 return False
#         else:
#             print(f"无法获取发布信息。状态码: {response.status_code}")
#     except Exception as e:
#         print(f"更新失败!: {e}")



if __name__ == "__main__":
    print()
    # file_path = Program_dir + "\\" + idv_login_program_name
    file_path = "E:\\Netease\\dwrg\\idv-login.exe"
    current_version = get_file_version(file_path)
    print(current_version)
