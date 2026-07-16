### 前往我的 Gitee 主页

这是我的 Gitee 主页：[https://gitee.com/gangan97307](https://gitee.com/gangan97307)

---

### 前往我的 GitHub 主页

这是我的 GitHub 主页：[https://github.com/Gangan-307](https://github.com/Gangan-307)

---

# 第一部分：Git 下载与安装指南

针对不同操作系统，Git 的安装和初始配置步骤如下：

### 1. 各平台安装步骤

#### Windows 系统
* **官方包安装（推荐）**：
  访问 [Git 官网下载页](https://git-scm.com/download/win)，下载 `64-bit Git for Windows Setup`。双击运行，**一律保持默认选项**点击“下一步（Next）”即可。安装后会获得 **Git Bash** 终端。
* **命令行安装（PowerShell）**：
  ```powershell
  winget install --id Git.Git -e --source winget
  ```

#### macOS 系统
* **通过 Homebrew 安装（推荐）**：
  ```bash
  brew install git
  ```
* **通过 Xcode 命令行工具**：
  打开终端，运行以下命令，系统会自动弹窗提示安装：
  ```bash
  git --version
  ```

#### Linux 系统（以 Debian/Ubuntu 为例）
* **通过包管理器安装**：
  ```bash
  sudo apt update
  sudo apt install git -y
  ```

#### WSL (Windows Subsystem for Linux)
* 如果在 WSL (如 Ubuntu) 中使用，请在 WSL 终端中运行：
  ```bash
  sudo apt update
  sudo apt install git -y
  ```

---

### 2. 安装后初始化配置

安装完成后，必须配置您的**用户名**和**邮箱**。这些信息会记录在您的每一次提交（Commit）中。

```bash
# 配置全局用户名
git config --global user.name "您的用户名或昵称"

# 配置全局邮箱（建议与 GitHub/Gitee 注册邮箱一致）
git config --global user.email "your_email@example.com"

# 查看当前配置列表（验证是否设置成功）
git config --list
```

---

# 第二部分：Git 常用指令速查手册


本手册涵盖了从初始化到日常开发、分支管理及远程同步的核心指令，适合初学者和日常快速复习。

---

## 一、 初始化与创建

| 命令 | 说明 |
| :--- | :--- |
| `git init` | 在当前文件夹初始化一个新的本地 Git 仓库（生成 `.git` 文件夹） |
| `git clone <远程仓库地址>` | 克隆远程仓库到本地（自动建立连接） |
| `git clone -b <分支名> --depth 1 <地址>` | 克隆指定分支，且只拉取最近一次提交（适合大仓库极速下载） |

---

## 二、 工作区与暂存区（日常最常用）

Git 的核心工作流：**工作区 (修改文件) -> 暂存区 (add) -> 本地仓库 (commit)**。

| 命令 | 说明 |
| :--- | :--- |
| `git status` | 查看当前工作区和暂存区的状态（哪些文件被修改/未跟踪） |
| `git add <文件名>` | 将指定文件添加到暂存区（Staging Area） |
| `git add .` | 将当前目录下所有修改和新文件添加到暂存区 |
| `git commit -m "提交说明"` | 将暂存区的文件提交到本地仓库，并添加本次提交的说明 |
| `git commit --amend` | 修改上一次的提交信息（或合并刚才漏掉的修改） |

---

## 三、 分支管理 (Branch)

分支用于隔离不同的开发任务，避免代码冲突。

| 命令 | 说明 |
| :--- | :--- |
| `git branch` | 列出本地所有分支（当前分支前会有 `*` 号） |
| `git branch -a` | 列出本地和远程的所有分支 |
| `git branch <新分支名>` | 创建一个新分支，但不会切换过去 |
| `git checkout <分支名>` | 切换到指定分支（较老指令） |
| `git switch <分支名>` | 切换到指定分支（较新、更直观的指令） |
| `git checkout -b <新分支名>` | 创建并立即切换到该新分支 |
| `git merge <分支名>` | 将指定分支的代码合并到当前分支 |
| `git branch -d <分支名>` | 删除已合并的本地分支 |
| `git branch -D <分支名>` | 强制删除未合并的本地分支 |

---

## 四、 远程仓库同步 (Remote)

| 命令 | 说明 |
| :--- | :--- |
| `git remote -v` | 查看当前配置的远程仓库地址和简称（通常是 `origin`） |
| `git remote add origin <地址>` | 将本地仓库关联到一个新的远程仓库 |
| `git fetch <远程主机名>` | 获取远程仓库的所有更新，但不与本地代码合并 |
| `git pull <远程名> <远程分支>:<本地分支>` | 拉取远程更新并自动与本地当前分支合并（常用 `git pull`） |
| `git push <远程名> <本地分支>:<远程分支>` | 将本地分支推送到远程仓库（常用 `git push origin main`） |
| `git push -u origin main` | 首次推送时使用 `-u`，后续只需输入 `git push` 即可 |

---

## 五、 撤销与版本回退（安全药箱）

使用以下命令时请谨慎，部分操作会覆盖本地未保存的修改。

| 命令 | 说明 |
| :--- | :--- |
| `git checkout -- <文件名>` | 丢弃工作区中该文件的修改（恢复到上次提交的状态） |
| `git restore <文件名>` | 同上，丢弃本地工作区的修改（新版 Git 推荐） |
| `git reset HEAD <文件名>` | 将已 add 到暂存区的文件撤回到工作区（不影响文件内容） |
| `git reset --soft HEAD~1` | 撤销上一次 commit，保留代码在暂存区（常用于写错 commit 想重写） |
| `git reset --hard HEAD~1` | 彻底回退到上一个版本（**工作区未提交的代码会丢失，慎用**） |
| `git reset --hard <Commit_ID>` | 彻底回退到指定的历史版本（通过 `git log` 获取 ID） |
| `git revert <Commit_ID>` | 撤销指定的提交，但通过创建一个新的提交来记录这次撤销（安全，不破坏历史） |

---

## 六、 查看历史与差异 (Log & Diff)

| 命令 | 说明 |
| :--- | :--- |
| `git log` | 查看详细的提交历史记录（按 `q` 退出） |
| `git log --oneline` | 以精简的单行形式查看提交历史 |
| `git log --graph --oneline` | 字符图形化展示分支合并历史 |
| `git diff` | 查看当前工作区与暂存区的代码差异 |
| `git diff <文件名>` | 查看指定文件在工作区和最近一次提交之间的差异 |
| `git reflog` | 查看命令操作历史（可以用来找回被误删/回退的 commit） |

---

## 七、 临时暂存修改 (Stash)

当你在开发新功能，突然需要切换到其他分支紧急修 Bug，但当前工作只进行了一半，不想生成无意义的 Commit 时使用。

| 命令 | 说明 |
| :--- | :--- |
| `git stash` | 把当前未提交的修改（工作区和暂存区）保存到暂存栈中，恢复干净的工作区 |
| `git stash list` | 查看所有临时保存的记录 |
| `git stash apply` | 应用最新一次保存的修改，但保留暂存栈中的记录 |
| `git stash pop` | 恢复最近一次保存的修改，并将其从暂存栈中删除（最常用） |
| `git stash drop` | 丢弃最近一次保存的记录 |
```