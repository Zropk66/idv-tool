import requests

# GitHub仓库信息
github_repo_owner = "Alexander-Porter"
github_repo_name = "idv-login"

# GitHub API的基础URL
github_api_url = f"https://api.github.com/repos/{github_repo_owner}/{github_repo_name}/releases/latest"

# 定义本地更新文件的存储路径
local_update_path = "D:\\Misc\\update_package.exe"
# 定义更新包解压缩后的目标目录
update_extract_dir = "%temp%"


def download_update(url, save_path):
    """ 下载更新文件 """
    print("Downloading update...")
    response = requests.get(url)
    with open(save_path, 'wb') as f:
        f.write(response.content)


def main():
    try:
        # 发送请求获取最新发布信息
        response = requests.get(github_api_url)
        if response.status_code == 200:
            release_info = response.json()
            # 获取下载链接
            download_url = release_info['assets'][0]['browser_download_url']  # 假设只有一个附件
            print(f"更新链接为{download_url}")
            # 下载更新
            download_update(download_url, local_update_path)
            print("Update successful!")
        else:
            print(f"Failed to fetch release info. Status code: {response.status_code}")
    except Exception as e:
        print(f"Update failed: {e}")


if __name__ == "__main__":
    main()
