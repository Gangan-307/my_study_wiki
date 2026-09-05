# 🛠️ Docsify 个人知识库搭建与使用指南

本教程详细记录了从零开始搭建 Docsify 个人知识库的完整步骤，包含环境配置、安装、常用指令以及常见问题处理。

---

## 一、 环境准备（Node.js 安装与配置）

Docsify 基于 Node.js 运行，因此首先需要安装 Node.js 环境。

### 1. 下载与安装
*   **官方下载地址**：[Node.js 官方下载网站](https://nodejs.cn/download/)
* ![nodejs下载图](../images/opt_20260712_02.png ':size=600')
*   **版本选择**：推荐选择 **msi-64位**，稳定性更好。
*   **安装步骤**：双击下载好的安装包，一路点击“Next（下一步）”即可。安装程序会自动将 Node.js 和 npm（包管理器）写入系统环境变量。

### 2. 验证安装是否成功
打开系统终端（Cmd 或 PowerShell），输入以下指令验证：
```bash
# 检查 Node.js 版本
node -v

# 检查 npm 版本
npm -v
```
*如果输出类似 `v24.18.0` 的版本号，说明安装成功。*

### 3. 配置国内镜像源（推荐）[可选]
为了加快后续下载插件的速度，建议将 npm 源切换为国内镜像源（如腾讯云或淘宝镜像）：
```bash
# 查看当前源
npm config get registry

# 切换为国内源
npm config set registry https://registry.npmmirror.com/
```

---

## 二、 Docsify 安装

有了 npm 之后，即可全局安装 Docsify 命令行工具。

### 1. 全局安装指令
在终端中运行以下命令：
```bash
npm install -g docsify-cli
```

### 2. Windows 权限问题处理（可选）
如果在 Windows PowerShell 中运行 Docsify 指令报错，提示“无法加载文件，因为在此系统上禁止运行脚本”，需要修改执行策略：
1. 以**管理员身份**打开 PowerShell。
2. 输入以下指令并回车：
   ```powershell
   Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
   ```
3. 输入 `Y` 确认。

---

## 三、 项目初始化与结构说明

### 1. 初始化指令
在您想建立知识库的文件夹目录下（例如，桌面新建一个“my_study_wiki.docx”），打开该文件夹终端运行以下指令：
```bash
# 初始化当前文件夹
docsify init .
```

### 2. 初始化后生成的三个核心文件
*   **`index.html`**：整个网站的配置文件，控制主题样式、启用的插件（如搜索、代码高亮）以及核心设置。
*   **`README.md`**：默认的首页内容，网站启动后展示的第一个页面。
*   **`.nojekyll`**：用于阻止 GitHub Pages 忽略以下划线开头的文件（如 `_sidebar.md`），保证静态网站能正常在云端渲染。

---

## 四、 常用运行与预览指令

在本地编写笔记时，我们需要启动一个本地服务器来实时预览网页效果。

### 1. 启动本地服务
在项目根目录下运行：
```bash
# 启动本地服务（默认端口 3000）
docsify serve .
```

### 2. 访问网址
打开浏览器，输入以下网址进行预览：
```text
http://localhost:3000
```
*只要不关闭运行中的终端，您在 VS Code 中修改并保存 Markdown 文件后，浏览器都会**实时自动刷新**。*

---

## 五、 常用核心配置文件说明

若要让网站拥有侧边栏、导航栏和封面，需要手动在**项目根目录**下创建以下 Markdown 文件，并在 `index.html` 中开启对应配置。

### 1. 侧边栏 `_sidebar.md`
用于控制左侧的菜单目录，格式为标准的 Markdown 列表：
```markdown
* [🏠 首页](README.md)
* 💻 C 语言专题
  * [指针与内存](c-language/pointer.md)
```

### 2. 导航栏 `_navbar.md`
用于控制网页右上角的快捷导航链接：
```markdown
* [🏠 首页](README.md)
* [🐱 GitHub](https://github.com)
```

### 3. 封面页 `_coverpage.md`
用于开启网站的欢迎封面：
```markdown
# 我的技术知识库

> “不积跬步，无以至千里。”

[开始阅读](README.md)
```

---

## 六、 常见问题与避坑指南

### 1. 终端提示“无法将 docsify/npx 识别为 cmd let...”
*   **原因**：VS Code 的终端缓存了旧的环境变量，未能检测到新安装的 Node.js 路径。
*   (先重启电脑再试)
*   **解决方案一**：在 VS Code 终端右侧点击下拉菜单，将终端类型切换为 **Command Prompt (CMD)**。
*   **解决方案二**：按下 `Ctrl + Shift + P`，输入 `Reload Window` 并回车，强制刷新 VS Code 窗口。
*   **解决方案三**：使用 **npx** 免全局变量路径运行：
    ```bash
    # 初始化
    npx docsify-cli init .
    
    # 本地预览
    npx docsify-cli serve .
    ```

---

## 七、 部署到云端（实现手机访问与简历展示）

本地写好笔记后，我们可以将其免费部署到 **GitHub Pages** 或 **Gitee Pages**。部署成功后，您将获得一个专属的公网网址，可以在手机上随时查看，也可以写在简历上展示给面试官。

---

### 方案 A：部署到 GitHub Pages（长期推荐，全球通用）

GitHub Pages 是最主流的静态网页托管平台，完全免费且稳定。

#### 步骤 1：在 GitHub 上新建仓库
1. 登录 [GitHub](https://github.com/)（如果没有账号请先注册）。
2. 点击右上角的 **“+” -> “New repository”**。
3. **Repository name**（仓库名）填入：`my_study_wiki`。
4. 选择 **Public**（公开，注意：私有仓库使用 Pages 服务可能需要付费）。
5. 不要勾选 “Add a README file”，直接点击 **Create repository**。

#### 步骤 2：在本地使用 Git 上传代码
在您电脑的项目根目录终端中，依次运行以下指令（请将用户名和仓库名替换为您自己的）：
```bash
# 1. 初始化本地 Git 仓库
git init

# 2. 将所有文件添加到暂存区
git add .

# 3. 提交到本地版本库
git commit -m "deploy docsify wiki"

# 4. 强制重命名主分支为 main
git branch -M main

# 5. 关联远程 GitHub 仓库（请替换为您的仓库地址）
git remote add origin https://github.com/您的用户名/my_study_wiki.git

# 6. 推送代码到 GitHub
git push -u origin main
```

#### 步骤 3：开启 GitHub Pages 服务
1. 页面打开您在 GitHub 上的仓库，点击右上角的 **Settings**（设置）。
2. 在左侧菜单栏中，点击 **Pages**。
3. 在 **Build and deployment** 下方的 **Branch**（分支）下拉菜单中：
   * 将 `None` 改为 `main`。
   * 旁边的文件夹选择 `/ (root)`。
   * 点击 **Save**（保存）。
4. 稍等 1-2 分钟，刷新该页面，顶部会出现一个绿色的提示框，里面就是您的专属网址，例如：
   `Your site is live at https://username.github.io/my_study_wiki/`

> **📌 关键注意**：根目录下的 `.nojekyll` 文件必不可少。如果没有它，GitHub 会默认使用 Jekyll 引擎解析网页，导致以下划线开头的 `_sidebar.md` 和 `_navbar.md` 无法被读取，网页会出现空白。

---

## 八、 极客效率升级：一键式自动化运维控制台（高级）

在搭建完基础系统后，日常编写笔记、处理截图、手动 Git 提交、以及启动本地服务器等繁琐步骤会产生较多重复性劳动。为了实现“零摩擦”的极客开发体验，我们使用 **Python 脚本** 和 **VS Code 自动任务机制** 建立了一套一键式自动化运维控制台。

### 1. 核心自动化功能
*   **一键新建今日日志**：自动计算当天日期、生成本地 Markdown 模板并在 VS Code 中打开。`daily/` 与 `weekly/` 已加入 `.gitignore`，不会进入公共仓库或公共侧边栏。
*   **一键智能图片压缩**：自动扫描 `images/` 文件夹下所有新截图（PNG 格式），通过**自适应颜色量化算法**将几 MB 的波形图/大截图压缩至 100~200 KB（肉眼无损），自动规范化命名为 `opt_日期_序号.png`，并自动递归扫描替换整个项目中所有 `.md` 文件里的图片链接，最后自动清理本地原始大图。
*   **一键开启开发沙盒**：自动为您配置 `.vscode/tasks.json`。只要您在控制台输入指令或打开项目，VS Code 会自动唤醒并在其**内部集成终端**中静默启动本地 Docsify 服务器，不再占用或弹窗外部 CMD 窗口。
*   **一键打包部署 Git**：自动将所有修改打包（Git Stage），自动获取当前系统时间戳作为 Commit 信息进行提交，并一键推送到 GitHub 远程仓库，实现瞬间秒级部署。

---

### 2. 自动化运维控制台部署步骤

#### 步骤 1：安装依赖库
在电脑终端中安装 Python 图片处理库 `Pillow`：
```bash
pip install Pillow
```

#### 步骤 2：创建主控制台脚本 `manage.py`
在项目**根目录**（和 `index.html` 平级）新建 `manage.py` 文件，并写入以下完整代码：

```python
import os
import sys
import subprocess
from datetime import datetime
from PIL import Image

# ================= 基础全局配置 =================
IMAGE_DIR = "images"
ALLOWED_EXTENSIONS = (".png", ".jpg", ".jpeg")
# ===============================================

def create_daily_log():
    """1. 自动新建仅保存在本地的今日日志"""
    print("\n[正在执行] 1. 一键新建今日日志...")
    today_str = datetime.now().strftime("%Y-%m-%d")
    log_file_path = f"daily/{today_str}.md"

    if not os.path.exists("daily"):
        os.makedirs("daily")

    template = f"""# {today_str} 学习日志

---

## 🎯 今日计划
- [ ] 
- [ ] 

---

## 📝 学习记录
### 1. 核心收获
*   

---

## 🤔 今日复盘
*   **🏆 今日最大收获**：
*   **📈 待改进与明日计划**：
"""

    if not os.path.exists(log_file_path):
        with open(log_file_path, "w", encoding="utf-8", newline="\n") as f:
            f.write(template)
        print(f"  [成功] 已生成今日日志模板: {log_file_path}")
    else:
        print(f"  [提示] 今天的日志文件已存在: {log_file_path}")

    try:
        subprocess.run(["code", log_file_path], shell=True)
        print("  [成功] 已自动在 VS Code 中打开今日日志！")
    except Exception:
        print(f"  [提示] 请手动在 VS Code 中打开: {log_file_path}")


def compress_image(input_path, output_path):
    """自适应图片压缩算法"""
    img = Image.open(input_path)
    ext = os.path.splitext(input_path)[1].lower()
    if ext == ".png":
        if img.mode != 'P':
            img = img.convert('P', palette=Image.ADAPTIVE, colors=256)
        img.save(output_path, "PNG", optimize=True)
    else:
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
        img.save(output_path, "JPEG", quality=80, optimize=True)


def update_markdown_links(old_name, new_name):
    """递归扫描整个项目，替换 Markdown 中的图片链接"""
    modified_count = 0
    for root, dirs, files in os.walk("."):
        if ".git" in root or "node_modules" in root:
            continue
        for file in files:
            if file.endswith(".md"):
                file_path = os.path.join(root, file)
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                
                if old_name in content:
                    new_content = content.replace(old_name, new_name)
                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write(new_content)
                    modified_count += 1
                    print(f"    [链接替换] 已成功更新文件: {file_path}")
    return modified_count


def optimize_images():
    """2. 自动检索、压缩图片，并更新 Markdown 中的链接"""
    print("\n[正在执行] 2. 一键智能压缩图片...")
    if not os.path.exists(IMAGE_DIR):
        print(f"  [错误] 未找到 {IMAGE_DIR} 文件夹")
        return

    today_str = datetime.now().strftime("%Y%m%d")
    files = os.listdir(IMAGE_DIR)
    raw_images = [f for f in files if f.lower().endswith(ALLOWED_EXTENSIONS) and not f.startswith("opt_")]

    if not raw_images:
        print("  [提示] 暂无需要优化的原始图片。")
        return

    print(f"  [开始] 发现 {len(raw_images)} 张原始图片，开始进行自适应压缩...")
    for idx, filename in enumerate(raw_images):
        old_path = os.path.join(IMAGE_DIR, filename)
        ext = os.path.splitext(filename)[1].lower()
        new_filename = f"opt_{today_str}_{idx + 1:02d}{ext}"
        new_path = os.path.join(IMAGE_DIR, new_filename)

        old_size = os.path.getsize(old_path) / 1024

        try:
            compress_image(old_path, new_path)
            new_size = os.path.getsize(new_path) / 1024
            ratio = (1 - new_size / old_size) * 100
            print(f"\n  🚀 压缩成功: {filename} -> {new_filename}")
            print(f"     大小变化: {old_size:.1f}KB -> {new_size:.1f}KB (暴减: {ratio:.1f}%)")

            print("     正在全项目扫描并更新 Markdown 图片链接...")
            update_markdown_links(filename, new_filename)

            os.remove(old_path)
            print(f"     [清理] 已安全删除本地大图原图: {filename}")
        except Exception as e:
            print(f"  ❌ 处理图片 {filename} 失败: {e}")
    print("\n[完成] 所有新图片处理完毕！")


def open_project_in_vscode_and_server():
    """4. 自动在 VS Code 中打开项目，并通过 VS Code 自动任务在内部终端启动服务器"""
    print("\n[正在执行] 4. 一键开启开发工作空间...")
    
    vscode_dir = ".vscode"
    tasks_json_path = os.path.join(vscode_dir, "tasks.json")
    if not os.path.exists(vscode_dir):
        os.makedirs(vscode_dir)
        
    tasks_json_content = """{
    "version": "2.0.0",
    "tasks": [
        {
            "label": "启动 Docsify 网页服务器",
            "type": "shell",
            "command": "npx docsify-cli serve .",
            "runOptions": {
                "runOn": "folderOpen"
            },
            "presentation": {
                "reveal": "always",
                "panel": "new"
            },
            "problemMatcher": []
        }
    ]
}"""
    
    if not os.path.exists(tasks_json_path):
        with open(tasks_json_path, "w", encoding="utf-8") as f:
            f.write(tasks_json_content)
        print("  [配置] 自动为您创建了 VS Code 内部终端自动启动任务配置文件。")

    try:
        print("  -> 正在唤醒 VS Code...")
        subprocess.run(["code", "."], shell=True)
        print("  [🎉 成功] 已成功唤醒 VS Code 并载入项目！")
        print("\n  📢  特别提示（仅首次需要）：")
        print("      VS Code 首次打开此项目时，右下角会弹窗提示：")
        print("      '是否允许在此工作区中自动运行任务？'")
        print("      👉 请务必点击【允许(Allow)】或【允许在工作区运行】。")
    except Exception as e:
        print(f"  ❌ 打开 VS Code 失败，请确保 code 命令已加入环境变量。错误: {e}")


def git_push_assets():
    """5. 一键打包并推送到 GitHub 远程仓库"""
    print("\n[正在执行] 5. 一键同步推送到远程 Git 仓库...")
    
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    commit_msg = f"Wiki Auto-Update: {now_str}"
    
    try:
        print("  -> 运行: git add .")
        subprocess.run(["git", "add", "."], check=True)
        
        print(f"  -> 运行: git commit -m \"{commit_msg}\"")
        result = subprocess.run(["git", "commit", "-m", commit_msg], capture_output=True, text=True)
        
        if "nothing to commit" in result.stdout or "无文件要提交" in result.stdout:
            print("  [提示] 检查完毕：本地内容无任何改动，无需提交。")
        else:
            print("  [成功] 本地代码版本提交成功！")
            
            print("  -> 运行: git push")
            subprocess.run(["git", "push"], check=True)
            print("  [🎉 成功] 您的最新 Wiki 已成功部署至 GitHub Pages！")
            
    except subprocess.CalledProcessError as e:
        print(f"  ❌ Git 命令执行失败，请检查网络或配置: {e}")
    except Exception as e:
        print(f"  ❌ 发生未知错误: {e}")


def show_menu():
    """显示极客感十足的控制台菜单"""
    os.system('cls' if os.name == 'nt' else 'clear')
    print("=====================================================")
    print("               🚀  Wiki 控制")
    print("=====================================================")
    print("   1. 📅 一键新建本地今日日志 (打开VS Code)")
    print("   2. 📸 一键智能压缩图片 (自动更新全局 Markdown 链接)")
    print("   3. 🔄 运行全部 (新建今日日志 + 压缩优化图片)")
    print("   4. 💻 一键开启开发沙盒 (VS Code 内部集成终端跑服务器)")
    print("   5. 🚀 一键打包推送到 GitHub (自动部署静态网页)")
    print("   6. ❌ 退出管理系统")
    print("=====================================================")


def main():
    while True:
        show_menu()
        choice = input("请选择操作 [1-6] 并回车: ").strip()
        if choice == "1":
            create_daily_log()
            input("\n按回车键返回主菜单...")
        elif choice == "2":
            optimize_images()
            input("\n按回车键返回主菜单...")
        elif choice == "3":
            create_daily_log()
            optimize_images()
            input("\n按回车键返回主菜单...")
        elif choice == "4":
            open_project_in_vscode_and_server()
            input("\n按回车键返回主菜单...")
        elif choice == "5":
            git_push_assets()
            input("\n按回车键返回主菜单...")
        elif choice == "6":
            print("\n感谢使用，祝您备战面试顺利，代码无 Bug！👋")
            break
        else:
            input("\n[输入错误] 请输入 1~6 之间的数字。按回车继续...")

if __name__ == "__main__":
    main()
```

#### 步骤 3：创建 Windows 桌面快捷方式 `一键管理知识库.bat`
在项目**根目录**（和 `index.html` 平级）新建一个名为 `一键管理知识库.bat` 的文件，复制并保存以下代码：

```bat
@echo off
:: 设置编码为 UTF-8 防止控制台中文乱码
chcp 65001 > nul
python manage.py
```

以后您在本地进行文档管理时，双击运行该 `.bat` 文件，即可通过数字菜单一键调起以上所有的高级开发工作流。
