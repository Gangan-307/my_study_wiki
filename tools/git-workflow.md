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

# 3. 提交到本地仓库（遵循下方的约定式提交规范）
git commit -m "feat(auth): 新增登录表单结构"
```

### 提交信息规范：Conventional Commits（约定式提交）

从现在的新提交开始统一使用约定式提交；**已经推送到 GitHub 或 Gitee 的历史提交不建议改写**。改写已推送历史通常需要强制推送，会影响其他协作者；需要撤销时优先使用 `git revert` 创建一条新的反向提交。

#### 1. 固定格式

```text
<type>(<scope>): <subject>
```

- `type`：必须填写，说明本次改动的性质。
- `scope`：可选，说明影响的模块；小型改动可省略。
- `subject`：必须填写，使用一句简短、明确的动作描述本次改动。

推荐中文描述，便于个人知识库回顾；团队若要求英文，则只统一语言，不改变前缀格式。

#### 2. 常用 `type`

| 类型 | 含义 | 适用场景 |
| :--- | :--- | :--- |
| `feat` | 新功能 | 新增驱动、协议能力、页面或模块 |
| `fix` | 修复缺陷 | 修复功能异常、边界条件或兼容性问题 |
| `docs` | 文档变更 | 修改 Markdown、README、注释或学习记录 |
| `style` | 代码格式 | 仅调整空格、缩进、换行或格式化，不改变行为 |
| `refactor` | 重构 | 改善代码结构，不新增功能也不修复缺陷 |
| `test` | 测试 | 新增或修正单元测试、集成测试与测试数据 |
| `chore` | 工程杂务 | 修改构建脚本、编辑器配置、依赖或辅助工具 |

#### 3. `scope` 的命名建议

`scope` 应使用稳定的模块名，而不是具体文件名。此知识库可优先使用：

```text
c-language / hardware-drivers / rtos / middleware / esp / tools / docsify
```

例如，一篇 C 语言学习笔记使用 `docs(c-language)`；修改 Git 使用说明使用 `docs(tools)`。

#### 4. 可直接使用的提交示例

```bash
# 知识库文档
git commit -m "docs(c-language): 完善数据类型与类型转换专题"
git commit -m "docs(tools): 补充约定式提交规范"

# 嵌入式代码
git commit -m "feat(uart): 新增串口环形缓冲区"
git commit -m "fix(spi): 修复连接超时判断"
git commit -m "refactor(lvgl): 拆分屏幕刷新逻辑"
git commit -m "test(protocol): 增加协议帧解析边界测试"

# 工程配置
git commit -m "chore(docsify): 更新本地预览配置"
```

#### 5. 提交前检查清单

- 一次提交只做一件独立的事，避免将功能、格式化和无关文件混在一起。
- `subject` 写清“做了什么”，避免 `update`、`修改文件`、`fix bug` 等模糊描述。
- 提交前运行 `git status`，确认暂存区只包含本次要提交的文件。
- 本地尚未推送的最后一次提交可用 `git commit --amend` 修正；已推送提交不要用 `--amend` 后强制推送。

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

# 第三部分：多远程仓库与 Git Subtree 分仓推送

当同一份本地代码需要同步到多个远程仓库，或需要将大仓库中的一个子目录独立发布时，可以使用“多远程仓库 + Git Subtree”。例如：完整项目推送到 Gitee，而 `a` 子目录单独发布到 GitHub 的另一个仓库。

## 一、多远程仓库（Multi-remote）

一个本地仓库可以绑定多个远程地址。`origin` 通常保留给主仓库，其他仓库使用有语义的别名，例如 `github-origin`。

```bash
# 添加 GitHub 远程仓库
git remote add github-origin https://github.com/Gangan-307/LCHSP_Watch.git

# 查看远程别名及其读写地址
git remote -v
```

多远程仓库的作用是统一管理一份本地工作区，避免维护多个手动复制的目录。推送前仍应先确认当前分支和目标分支，防止将错误分支发布到错误仓库。

## 二、Git Subtree：将子目录作为独立仓库推送

`git subtree push` 会从当前仓库中提取指定子目录的提交内容，并将该目录内容作为目标仓库分支的根目录推送。本地目录结构不需要改变。

```bash
# 将当前仓库的 a 目录推送到 github-origin 的 main 分支
git subtree push --prefix=a github-origin main
```

使用前提和边界：

- `--prefix=a` 必须是当前仓库中真实存在且已提交的目录。
- 目标仓库应以当前仓库为内容来源；不要同时在目标仓库独立开发相同文件，否则后续同步历史会复杂。
- `subtree push` 会为该子目录生成可推送的历史视图，但它不是两个仓库的自动双向同步方案。
- 团队项目应在代码合并到约定的发布分支后，再执行分仓推送；不要绕过 PR 直接发布未审查的特性分支。

## 三、避免嵌套 Git 仓库

不要在外层 Git 仓库的普通子目录中直接执行 `git init`。外层仓库无法正常追踪内层仓库中的文件；若把内层仓库作为 gitlink 提交，平台通常显示为不可直接浏览的子模块链接。

如果目标是“发布某个子目录”，使用 Subtree；如果确实需要独立依赖仓库，应显式使用 `git submodule add` 并理解子模块的初始化、更新和固定提交版本流程。

## 四、使用 Git Alias 简化分仓推送

以下示例使用**当前仓库级配置**，只影响本项目；确认每个仓库都使用相同目录、远程别名和分支名后，才考虑加 `--global` 设为全局别名。

```bash
# 简化 GitHub 子目录推送：git psg
git config alias.psg "subtree push --prefix=a github-origin main"

# 一键双推：先推主仓库，成功后再推子目录仓库
git config alias.pushall "!f() { git push origin main && git subtree push --prefix=a github-origin main; }; f"
```

若主分支实际名为 `master`，将以上命令中的 `main` 替换为 `master`；不要混用两个分支名。

## 五、极简日常流程

```bash
# 1. 只暂存本次提交相关文件，并使用约定式提交信息
git add <文件路径>
git commit -m "feat(scope): 描述信息"

# 2. 推送完整仓库和子目录仓库
git pushall
```

首次配置或别名失效时，使用完整命令替代：

```bash
git push origin main
git subtree push --prefix=a github-origin main
```

---

# 第四部分：代码合并与冲突处理

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
   git commit -m "chore(git): 解决与 main 的合并冲突"
   ```
   *注意：解决冲突后，无需重新运行 `git merge`，直接 `add` 并 `commit` 即可完成合并。*

---

# 第五部分：安全退路（纠错与回退场景）

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

# 第六部分：Git 核心指令速查表

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
