import os
import requests
import gnupg
import subprocess
import random
import string
from datetime import datetime, timedelta
import shutil

# Nhập GitHub Personal Access Token từ input
github_token = os.getenv('INPUT_GITHUB_TOKEN')

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
Passphrase:  # Bỏ trống mật khẩu
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

# Lấy key ID của GPG key vừa tạo
gpg = gnupg.GPG()
public_keys = gpg.list_keys()
if public_keys:
    key_id = public_keys[0]['keyid']
    # Xuất public key để thêm vào GitHub
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

# Cấu hình Git
subprocess.run(["git", "config", "--global", "user.email", github_email])
subprocess.run(["git", "config", "--global", "user.name", github_username])
subprocess.run(["git", "config", "--global", "github.user", github_username])
subprocess.run(["git", "config", "--global", "user.signingkey", key_id])
subprocess.run(["git", "config", "--global", "gpg.program", "gpg"])
subprocess.run(["git", "config", "--global", "commit.gpgSign", "true"])
subprocess.run(["echo", "allow-loopback-pinentry", ">>", os.path.expanduser("~/.gnupg/gpg-agent.conf")])
subprocess.run(["gpgconf", "--kill", "gpg-agent"])

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
            num_commits = random.randint(1, 3)
            for _ in range(num_commits):
                commit_date_list.append(current_date)
        current_date += timedelta(days=1)

    return commit_date_list

start_date = datetime.now() - timedelta(days=60)
end_date = datetime.now()
commit_dates = create_commit_date_list(start_date, end_date)

# Tạo ngẫu nhiên nội dung commit
def get_random_string(length):
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for i in range(length))

# Tạo commit trong từng repository
for repo_name in repo_names:
    repo_path = os.path.join(os.getcwd(), repo_name)
    os.makedirs(repo_path, exist_ok=True)
    subprocess.run(["git", "init"], cwd=repo_path)

    for commit_date in commit_dates:
        for description in descriptions:
            file_name = f"{get_random_string(10)}.txt"
            file_path = os.path.join(repo_path, file_name)
            with open(file_path, "w") as f:
                f.write(description)
            subprocess.run(["git", "add", file_name], cwd=repo_path)
            commit_message = f"Add file {file_name}"
            env = os.environ.copy()
            env['GIT_COMMITTER_DATE'] = commit_date.isoformat()
            env['GIT_AUTHOR_DATE'] = commit_date.isoformat()
            subprocess.run(["git", "commit", "-m", commit_message, "--gpg-sign"], cwd=repo_path, env=env)

print("Quá trình tạo lịch sử commit hoàn tất.")
