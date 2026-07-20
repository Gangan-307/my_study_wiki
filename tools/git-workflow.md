# Git 团队协作与日常开发实战手册

### 🔗 我的个人主页
* **Gitee 主页**：[https://gitee.com/gangan97307](https://gitee.com/gangan97307)
* **GitHub 主页**：[https://github.com/Gangan-307](https://github.com/Gangan-307)

---

# 第一部分：准备工作（安装与初始配置）

### 1. 多平台安装方法

* **Windows**: 访问 [Git 官网](https://git-scm.com/download/win) 下载 `64-bit Git for Windows Setup`。双击运行，一律保持默认选项点击“下一步”即可。或在 PowerShell 中运行：
  ```powershell
  winget install --id Git.Git -e --source winget
  ```
* **macOS**: 在终端运行 `brew install git`（需提前安装 Homebrew）或运行 `git --version` 配合系统弹窗安装。
* **Linux (Debian/Ubuntu)**: 
  ```bash
  sudo apt update && sudo apt install git -y
  ```

### 2. 首次使用初始化配置
安装完成后，必须配置您的**用户名**和**邮箱**，它们将作为您提交代码的“身份证”。

```bash
# 配置全局个人信息
git config --global user.name "您的真实姓名或昵称"
git config --global user.email "your_email@example.com"

# 推荐配置：让 Git 终端输出支持中文显示
git config --global core.quotepath false

# 检查配置
git config --list
```

---

# 第二部分：现代团队协作工作流 (Workflow)

在实际企业开发中，**绝对禁止**直接向 `main` (或 `master`) 分支推送代码。通常采用以下 **Feature Branch (特性分支) + Pull Request (代码审查)** 工作流。

### 🔄 团队协作标准生命周期图解

```text
    [远程 main 分支] ──────────────────────────────────────────────► [合并 PR] ──► [更新后的 main]
         │                                                                          ▲
         │ ① 克隆 / 拉取                                                             │ ⑤ 代码审查
         ▼                                                                          │
  [本地 main 分支] ──► ② 创建新分支 ──► [feature-login 分支]                          │
                                              │                                     │
                                              ▼                                     │
                                         ③ 本地开发                                  │
                                              │                                     │
                                              ▼                                     │
                                         ④ 提交并 Push ─────────────────────────────┘
```

---

### 🟢 协作步骤详解：从领任务到代码上线

#### 第一步：开始工作前，同步主干（每日清晨）
开始写代码前，先确保本地的 `main` 分支是最新的，避免基于过时的代码开发导致后期冲突。
```bash
git checkout main
git pull origin main
```

#### 第二步：创建专属特性分支（Feature Branch）
永远为每一个新任务创建一个独立的分支，命名规范通常为 `feature/功能名` 或 `bugfix/缺陷名`。
```bash
git checkout -b feature-login
# 注：创建并自动切换到新分支
```

#### 第三步：本地开发与频繁提交
在本地编写代码。建议**小步快跑**，完成一个微小但完整的逻辑就提交一次，便于后续回滚。
```bash
# 1. 编写代码后查看状态
git status

# 2. 暂存修改
git add login.html

# 3. 提交到本地仓库（遵循语义化 Commit 规范，如 feat:, fix:, docs: 等）
git commit -m "feat: add basic login form structure"
```

#### 第四步：推送分支并准备“代码审查”
当功能开发完毕并通过本地测试后，将本地的分支推送到远程仓库。
```bash
git push -u origin feature-login
```

#### 第五步：发起 Pull Request (PR) 与代码审查 (Code Review)
这是团队协作中保证代码质量的核心环节：
1. **发起 PR**：打开 GitHub 或 Gitee 网页，系统会检测到您刚刚推送了新分支，点击 **"Compare & pull request" (创建拉取请求)**。
2. **指派审查人 (Reviewer)**：在网页右侧，将 PR 指派给您的导师或资深同事进行 Review。
3. **代码审查 (Code Review)**：
   * 审查人会逐行阅读您的代码，提出修改意见、指出潜在 Bug 或性能问题。
   * 如果审查人提出修改意见，您**不需要**关闭 PR。只需在本地继续修改代码，然后再次 `git add` -> `git commit` -> `git push`。PR 页面会自动更新这些修改。
4. **合并 (Merge)**：审查人点击 **"Approve" (批准)** 后，分支将被合并入远程的 `main` 分支。

---

# 第三部分：代码合并与冲突处理

当多个开发者修改了同一个文件的同一行代码时，Git 无法决定保留哪一个，就会产生**冲突 (Conflict)**。

### 🛠 实战演练：如何优雅地解决冲突

当您准备合并代码，或者在本地拉取最新代码时，如果遇到冲突：

1. **同步主干代码到您的开发分支**：
   ```bash
   git checkout feature-login
   git merge main
   ```
   *如果此时控制台提示 `CONFLICT (content): Merge conflict in login.html`，说明产生冲突。*

2. **定位冲突文件**：
   打开冲突的文件（如 `login.html`），您会看到 Git 自动标记的冲突区域：
   ```html
   <<<<<<< HEAD
   <!-- 您本地在 feature-login 分支修改的代码 -->
   <button class="btn-blue">登录</button>
   =======
   <!-- 远程 main 分支上别人已经合并的代码 -->
   <button class="btn-navy">确认登录</button>
   >>>>>>> main
   ```

3. **手动裁决**：
   * 与相关同事沟通，决定保留哪行代码。
   * **删除**所有的冲突标记符号（`<<<<<<<`, `=======`, `>>>>>>>`）。
   * 最终将文件修改为您期望的正确状态：
     ```html
     <button class="btn-navy">登录</button>
     ```

4. **提交解决后的代码**：
   ```bash
   git add login.html
   git commit -m "build: resolve merge conflict with main"
   ```
   *注意：解决冲突后，无需重新运行 `git merge`，直接 `add` 并 `commit` 即可完成合并。*

---

# 第四部分：安全退路（纠错与回退场景）

> **⚠️ 避坑提醒**：在运行以下命令时，凡是看到形如 `<commit-id>` 或 `<file>` 的部分，代表占位符。在实际输入时，**请连同 `<` 和 `>` 符号一起删掉**。

### 场景一：代码写乱了，想彻底放弃本地未提交的修改
* **适用情况**：刚写的几行代码逻辑全错，想一键恢复到上一次提交时的干净状态。
* **命令**：
  ```bash
  # 恢复单个文件
  git restore login.html
  
  # 恢复当前目录下所有文件
  git restore .
  ```

### 场景二：执行了 `git add`，但想撤回，不希望它被 commit
* **适用情况**：不小心把一个临时文件或敏感配置文件加入了暂存区。
* **命令**：
  ```bash
  git restore --staged config.json
  ```

### 场景三：代码已经 `commit` 了，但想反悔（未 push 到远程）
* **适用情况**：刚刚提交了代码，突然发现有个错别字，或者少提交了一个文件。
* **命令（保留代码修改，仅撤销 Commit 记录）**：
  ```bash
  git reset --soft HEAD~1
  ```
  *(此时代码仍然完好地保留在您的暂存区中，修改后可重新提交)*

### 场景四：代码已经 `push` 到远程，现在需要紧急撤销该功能
* **适用情况**：功能已经上线，但线上出现严重 Bug，需要立刻下线该功能，且不能破坏团队其他人的提交历史。
* **命令**：
  ```bash
  # 使用 --no-edit 可以自动生成撤销说明，避免跳转到繁琐的 Vim 编辑器
  git revert --no-edit 9bf2a35f7b82c6e659d3afd1537c33b4f152fe14
  
  # 随后正常推送至远程
  git push origin feature-login
  ```

---

# 第五部分：Git 核心指令速查表

### 1. 基础工作流 (日常高频)
| 命令 | 核心说明 | 最佳实践时机 |
| :--- | :--- | :--- |
| `git status` | 查看文件状态（未跟踪/已修改/已暂存） | 每次准备执行 `add` 前后运行一次 |
| `git add .` | 将当前目录下的所有修改放入暂存区 | 准备打包提交前 |
| `git commit -m "msg"` | 将暂存区内容正式提交到本地仓库 | 完成一个独立且可运行的小功能时 |
| `git commit --amend` | 修改/追加上一次的提交记录 | 发现刚提交的注释写错，或漏了文件 |

### 2. 团队协作与同步
| 命令 | 核心说明 | 最佳实践时机 |
| :--- | :--- | :--- |
| `git pull origin main` | 拉取远程主干最新代码并自动合并到当前分支 | 每天开工前，或准备合并分支前 |
| `git push origin <branch>` | 将本地开发分支推送到远程仓库 | 本地功能开发测试完毕，准备提 PR 时 |
| `git remote -v` | 查看当前绑定的远程仓库地址 | 项目初始化或检查配置时 |

### 3. 分支管理
| 命令 | 核心说明 | 最佳实践时机 |
| :--- | :--- | :--- |
| `git branch -a` | 查看本地和远程的所有分支 | 需要切换到同事的分支协助排查时 |
| `git checkout -b <name>` | 创建并立即切换到该新分支 | 领到新的开发或修复任务时 |
| `git switch <name>` | 切换到已有分支（新版推荐，语义更清晰） | 需要在不同任务间来回切换时 |
| `git branch -d <name>` | 安全删除已经合并过的本地分支 | 功能上线后清理本地空间 |

### 4. 临时暂存 (Stash)
| 命令 | 核心说明 | 最佳实践时机 |
| :--- | :--- | :--- |
| `git stash` | 将当前未提交的修改存入临时堆栈，恢复干净的工作区 | 开发到一半，被叫去紧急修复其他 Bug 时 |
| `git stash pop` | 恢复最近一次暂存的修改，并将其从堆栈中删除 | 紧急 Bug 修复完毕，切回原分支继续开发时 |
| `git stash list` | 查看当前所有的暂存记录 | 存在多次暂存，需要确认恢复哪一次时 |