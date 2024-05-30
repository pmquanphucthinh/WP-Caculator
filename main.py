# main.py
import os
import requests
import gnupg
import subprocess
import random
import string
from datetime import datetime, timedelta
import shutil
from github import Github

# Nhập GitHub Personal Access Token
github_token = os.getenv("INPUT_GITHUB_TOKEN")
gpg_passphrase = "minhquan68"

# Lấy thông tin người dùng từ GitHub API
user_url = "https://api.github.com/user"
headers = {
    "Authorization": f"token {github_token}",
    "Accept": "application/vnd.github+json"
}
response = requests.get(user_url, headers=headers)

if response.status_code == 200:
    user_data = response.json()
    github_username = user_data['login']
    github_id = user_data['id']
    # Tạo email từ id và username
    github_email = f"{github_id}+{github_username}@users.noreply.github.com"

    print(f"Username: {github_username}")
    print(f"Email: {github_email}")
else:
    print("Không thể lấy thông tin người dùng từ GitHub API")
    exit()

# Fork 3 random repositories and get 3 random repository names
repo_list_url = "https://api.github.com/repositories"
repo_list_response = requests.get(repo_list_url, headers=headers)

if repo_list_response.status_code == 200:
    repo_list = repo_list_response.json()

    if isinstance(repo_list, list) and len(repo_list) >= 6:
        random_repos = random.sample(repo_list, 6)

        for repo in random_repos[:3]:
            owner = repo['owner']['login']
            repo_name = repo['name']
            fork_url = f"https://api.github.com/repos/{owner}/{repo_name}/forks"

            fork_response = requests.post(fork_url, headers=headers)

            if fork_response.status_code == 202:
                print(f"Forked repository '{repo_name}' from '{owner}' successfully.")
            else:
                print(f"Failed to fork repository '{repo_name}' from '{owner}': {fork_response.status_code}")
                print(fork_response.json())

        repo_names = [repo['name'] for repo in random_repos[3:]]
    else:
        print("Not enough repositories available to fork.")
        exit()
else:
    print(f"Failed to retrieve list of repositories: {repo_list_response.status_code}")
    exit()

# Tạo file batch cho gpg
batch_content = f"""
%echo Generating a basic OpenPGP key
Key-Type: RSA
Key-Length: 3072
Name-Real: {github_username}
Name-Email: {github_email}
Expire-Date: 0
Creation-Date: 2019-05-27
Passphrase: {gpg_passphrase}
%commit
%echo done
"""

batch_file_path = "gpg_keygen_batch"
with open(batch_file_path, "w") as batch_file:
    batch_file.write(batch_content)

# Tạo GPG key sử dụng file batch
subprocess.run(["gpg", "--batch", "--generate-key", batch_file_path])

# Xóa file batch sau khi sử dụng
os.remove(batch_file_path)

# Cấu hình Git
subprocess.run(["git", "config", "--global", "user.email", github_email])
subprocess.run(["git", "config", "--global", "user.name", github_username])
subprocess.run(["git", "config", "--global", "github.user", github_username])

# Lấy key ID của GPG key vừa tạo
gpg = gnupg.GPG()
public_keys = gpg.list_keys()
if public_keys:
    key_id = public_keys[0]['keyid']
    # Cấu hình user.signingkey
    subprocess.run(["git", "config", "--global", "user.signingkey", key_id])
    print("Đã cấu hình user.signingkey thành công.")

    # Sử dụng python-gnupg để xuất key
    public_key = gpg.export_keys(key_id)

    # Thêm GPG key vào GitHub
    gpg_key_url = "https://api.github.com/user/gpg_keys"
    data = {
        "armored_public_key": public_key
    }

    response = requests.post(gpg_key_url, headers=headers, json=data)

    if response.status_code == 201:
        print("Đã thêm GPG key vào tài khoản GitHub thành công.")
    else:
        print(f"Không thể thêm GPG key: {response.status_code}")
        print(response.json())
else:
    print("Không thể tìm thấy GPG key.")

# URL API để tạo repository
repo_url = "https://api.github.com/user/repos"

# Thêm từng repository
for repo_name in repo_names:
    repo_data = {
        "name": repo_name
    }
    repo_response = requests.post(repo_url, headers=headers, json=repo_data)

    if repo_response.status_code == 201:
        print(f"Đã tạo repository '{repo_name}' thành công trên GitHub.")
    else:
        print(f"Không thể tạo repository '{repo_name}': {repo_response.status_code}")
        print(repo_response.json())

# Tạo lịch sử commit
descriptions = [
    "Locked Tabs - Adds a lock switch to every tab inside the tab switcher that, when enabled, prevents the specific tab from being closed until the switch is disabled again",
    "Add HeatMap guide in real-world-projects + Code in Solutions Directory (#6796)",
    "Tab Manager - An easy way to batch-export, batch-close, and batch-add tabs",
    "Disable Tab Limit - Disables the default tab limit (varies giữa devices)"
]

def create_commit_date_list(start_date, end_date):
    commit_date_list = []
    current_date = start_date

    while current_date <= end_date:
        if random.choice([True, False, False, True, False]):  # Xác suất 3/7 cho 3-4 ngày mỗi tuần
            num_commits = random.randint(1, 3)  # Số lần commit mỗi ngày là từ 1 đến 3
            for _ in range(num_commits):
                commit_date_list.append({
                    "date": current_date.strftime('%Y-%m-%dT%H:%M:%S'),
                    "description": random.choice(descriptions)
                })
        current_date += timedelta(days=1)

    return commit_date_list

def generate_git_history(repo_name, start_date=None, end_date=None):
    if not start_date:
        start_date = datetime.now() - timedelta(days=10)  # Mặc định là 180 ngày trước
    if not end_date:
        end_date = datetime.now()

    commit_date_list = create_commit_date_list(start_date, end_date)
    
    history_folder = "Android"

    # Tạo thư mục lịch sử git.
    os.makedirs(history_folder, exist_ok=True)  # Sử dụng exist_ok=True để không gây lỗi nếu thư mục đã tồn tại
    os.chdir(history_folder)
    subprocess.run(["git", "init"])

    # Tạo các commit.
    for idx, commit in enumerate(commit_date_list):
        print(f"Generating commit {idx + 1}/{len(commit_date_list)}...")

        with open(f"SoftwareUpdate.txt", "w", encoding="utf-8") as f:
            f.write(commit["description"])
        
        subprocess.run(["git", "add", "."])
        commit_command = f'git commit -S --date="{commit["date"]}" -m "{commit["description"]}"'
        subprocess.run(commit_command, shell=True)

    print(f"Success! {len(commit_date_list)} commits have been created.")

    # Đẩy lên repository GitHub.
    remote_add_command = f"git remote add origin https://github.com/{github_username}/{repo_name}.git"
    subprocess.run(remote_add_command, shell=True)
    subprocess.run(["git", "push", "-u", "origin", "master"])

generate_git_history(repo_names[1])


def create_issue(token, repo, title, body):
    url = f"https://api.github.com/repos/{repo}/issues"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    data = {
        "title": title,
        "body": body
    }
    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 201:
        print(f"Issue '{title}' created successfully.")
        return response.json()["number"]
    else:
        print(f"Failed to create issue '{title}'. Status code: {response.status_code}")
        print("Response:", response.text)
        return None

def close_issue(token, repo, issue_number):
    url = f"https://api.github.com/repos/{repo}/issues/{issue_number}"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    data = {
        "state": "closed"
    }
    response = requests.patch(url, headers=headers, json=data)
    if response.status_code == 200:
        print(f"Issue #{issue_number} closed successfully.")
    else:
        print(f"Failed to close issue #{issue_number}. Status code: {response.status_code}")
        print("Response:", response.text)

# Tạo và đóng issue cho từng repository
for repo_name in repo_names:
    repo_full_name = f"{github_username}/{repo_name}"
    issue_number = create_issue(github_token, repo_full_name, "Sample Issue", "This is a sample issue created by the script.")
    if issue_number:
        close_issue(github_token, repo_full_name, issue_number)

# Dọn dẹp thư mục sau khi hoàn thành
os.chdir("..")
shutil.rmtree(history_folder)
