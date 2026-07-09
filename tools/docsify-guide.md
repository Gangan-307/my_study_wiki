# 🛠️ Docsify 个人知识库搭建与使用指南

本教程详细记录了从零开始搭建 Docsify 个人知识库的完整步骤，包含环境配置、安装、常用指令以及常见问题处理。

---

## 一、 环境准备（Node.js 安装与配置）

Docsify 基于 Node.js 运行，因此首先需要安装 Node.js 环境。

### 1. 下载与安装
*   **官方下载地址**：[Node.js 官方下载网站](https://nodejs.cn/download/)
* ![nodejs下载图](/images/nodejs-download.png ':size=400')
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

### 方案 B：部署到 Gitee Pages（国内访问速度极快）

如果您希望国内（包括手机 Wi-Fi/移动数据）访问速度飞快，可以选择码云（Gitee）。

#### 步骤 1：在 Gitee 上新建仓库
1. 登录 [Gitee](https://gitee.com/)（首次使用需要完成实名认证）。
2. 点击右上角的 **“+” -> “新建仓库”**。
3. **仓库名称**填入：`my_study_wiki`。
4. 选择 **开源**（即公开）。
5. 不要勾选初始化仓库的选项，直接点击 **创建**。

#### 步骤 2：推送代码到 Gitee
如果您已经关联过 GitHub，可以先删除关联或者直接使用 Gitee 提供的指令推送。如果第一次推送，在本地根目录终端运行：
```bash
git init
git add .
git commit -m "deploy to gitee"
git remote add origin https://gitee.com/您的用户名/my_study_wiki.git
git push -u origin "master"
```

#### 步骤 3：开启 Gitee Pages 服务
1. 进入您在 Gitee 的仓库页面。
2. 点击顶部菜单栏的 **“服务” -> “Gitee Pages”**。
3. 部署分支选择 **`master`**，部署目录保持为空（代表根目录）。
4. 点击 **“激活”**（首次使用需要上传身份证进行实名审核，审核通常需要 1 个工作日）。
5. 激活成功后，页面会给出您的专属网址：`https://您的用户名.gitee.io/my_study_wiki`。

> **📌 维护与更新提示**：
> 无论使用哪个平台，后续您在本地写了新笔记，只需在终端运行：
> ```bash
> git add .
> git commit -m "更新笔记"
> git push
> ```
> GitHub 会自动拉取并更新网页。如果是 Gitee Pages，每次推送后需要手动去“Gitee Pages”页面点击一次**“更新”**按钮。
```