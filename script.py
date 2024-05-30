import os
import requests
import gnupg
import subprocess
import random
import string
from datetime import datetime, timedelta

# Hàm để tạo chuỗi ngẫu nhiên gồm 4 chữ số
def random_suffix():
    return ''.join(random.choices(string.digits, k=4))

# Tên thư mục gốc
original_folder_name = 'Android'

# Đường dẫn đến thư mục gốc
original_path = 'D:\\Quan\\GithubCommitNew\\Android'

# Kiểm tra xem thư mục 'Android' có tồn tại không
if os.path.exists(original_path):
    # Tạo tên mới với suffix ngẫu nhiên
    new_folder_name = original_folder_name + random_suffix()

    # Đường dẫn đến thư mục mới
    new_path = os.path.join(os.path.dirname(original_path), new_folder_name)

    # Đổi tên thư mục
    os.rename(original_path, new_path)

    print(f'Tên mới của thư mục: {new_folder_name}')
else:
    # Nếu thư mục không tồn tại, thông báo và tiếp tục các lệnh tiếp theo
    print("Thư mục 'Android' không tồn tại, tiếp tục")

# Xóa key cũ
gpg = gnupg.GPG()
keys = gpg.list_keys()
for key in keys:
    gpg.delete_keys(key['fingerprint'], True, passphrase='Hoichoxom6868')
    # Xóa public key
    gpg.delete_keys(key['fingerprint'], secret=False)

# Nhập GitHub Personal Access Token
github_token = os.getenv("GITHUB_TOKEN")

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
Passphrase: Hoichoxom6868
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
        start_date = datetime.now() - timedelta(days=600)  # Mặc định là 180 ngày trước
    if not end_date:
        end_date = datetime.now()  # Mặc định là ngày hiện tại

    commit_dates = create_commit_date_list(start_date, end_date)

    for commit in commit_dates:
        commit_message = commit["description"]
        commit_date = commit["date"]
        with open("file.txt", "w") as file:
            file.write(commit_message)
        subprocess.run(["git", "add", "file.txt"])
        subprocess.run(["git", "commit", "-m", commit_message, "--date", commit_date, "--gpg-sign"])

    print(f"Lịch sử commit đã được tạo thành công cho repository '{repo_name}'.")

# Clone từng repository và tạo lịch sử commit
for repo_name in repo_names:
    clone_url = f"https://{github_username}:{github_token}@github.com/{github_username}/{repo_name}.git"
    subprocess.run(["git", "clone", clone_url])
    os.chdir(repo_name)
    generate_git_history(repo_name)
    subprocess.run(["git", "push", "--force"])
    os.chdir("..")
    subprocess.run(["rm", "-rf", repo_name])
