为您在之前内容的基础上，整理归纳了一份详细的 **WSL-Ubuntu 下载、安装、配置及与 VS Code 联动** 的全流程指南。您可以将其直接保存或记录下来。

---

# WSL-Ubuntu 下载、安装与配置保姆级指南

本指南适用于 Windows 10 (版本 2004 及以上) 或 Windows 11 系统，帮助您从零开始搭建一个纯净、高效的 WSL-Ubuntu 开发环境。

---

## 一、 安装准备（重要前提）（可直接从二开始）

为了确保 WSL 2 能够顺利运行，建议确认以下两点：
1. **Windows 版本**：按下 `Win + R` 键，输入 `winver`，确认 Windows 10 版本号大于或等于 **2004**（内部版本 19041 以上），或使用 Windows 11。
2. **启用 CPU 虚拟化**：
   * 按 `Ctrl + Shift + Esc` 打开任务管理器。
   * 点击“性能”选项卡 -> “CPU”，确认右下角的 **“虚拟化：已启用”**。
   * *如果未启用，需要在电脑开机时进入 BIOS 开启 `Intel Virtualization Technology` 或 `AMD-V`*。

---

## 二、 详细安装步骤

### 第一步：通过命令行安装

这是目前最简便、最推荐的安装方式。

1. 在 Windows 搜索框中输入 **PowerShell**。
2. 鼠标右键点击“Windows PowerShell”，选择 **以管理员身份运行**。
3. 在弹出的窗口中，输入以下命令并回车：
   ```powershell
   wsl --install
   ```
   * **注**：该命令默认会自动启用虚拟机平台、WSL 功能，并自动下载并安装最新的 **Ubuntu** 发行版。
   * 如果您想指定安装特定版本的 Ubuntu（例如 Ubuntu 22.04 LTS），可以运行：（也可在微软商店搜索“Ubuntu下载”）
     ```powershell
     wsl --install -d Ubuntu-22.04
     ```

### 第二步：重启计算机

当终端提示安装完成并要求重启时，请**手动重启电脑**。这一步是启用底层虚拟机服务所必需的。

### 第三步：初始化 Ubuntu 账户

1. 电脑重启后，系统会自动弹出一个 Ubuntu 的终端窗口。
   *(如果超过 2 分钟未弹出，请在 Windows 开始菜单中搜索并打开 "Ubuntu")*。
2. 稍等片刻，终端会提示：`Installing, this may take a few minutes...`。
3. 接着，根据提示创建您的 Linux 账户：
   * **Enter new UNIX username**: 输入您的用户名（建议全部使用小写英文和数字，例如 `lichen`）。
   * **New password**: 输入您的密码（**安全保护机制：输入时屏幕不会显示任何字符或星号，直接输入完按回车即可**）。
   * **Retype new password**: 再次输入密码以确认。

看到类似 `yourname@computername:~$` 的彩色提示符时，说明 Ubuntu 已成功安装。

---

## 三、 安装后的系统基础配置

为了确保后续开发和软件安装顺利，建议在 Ubuntu 终端内依次完成以下配置：

### 1. 更新系统软件包
```bash
# 更新软件包列表
sudo apt update

# 升级已安装的软件到最新版本（期间遇到提示输入 y 并回车）
sudo apt upgrade -y
```

### 2. 解决 Windows 与 WSL 的文件互通问题
在 WSL 中，你可以非常方便地管理和访问两端的文件：
* **在 Windows 中查看 WSL 文件**：
  打开 Windows 的“文件资源管理器”，在地址栏输入 `\\wsl$` 并回车，即可像访问 U 盘一样访问 Ubuntu 内部的所有文件。
* **在 WSL 中访问 Windows 的磁盘**：
  Windows 的磁盘（如 C 盘、D 盘）会自动挂载在 WSL 的 `/mnt/` 目录下。例如访问 D 盘：
  ```bash
  cd /mnt/d
  ```

---

## 四、 联动 VS Code 与 Git 开发配置（串联前文）

完成 WSL 安装后，按照以下三步，即可完美开启您的 ESP32 或其他项目开发：

### 步骤 1：在 WSL 中配置 Git
在 Ubuntu 终端中安装并配置您的身份信息：
```bash
# 安装 Git
sudo apt install git -y

# 配置 Git 全局身份
git config --global user.name "你的名字"
git config --global user.email "你的邮箱"
```

### 步骤 2：使用极速镜像克隆项目
避免 GitHub 连接超时，使用国内 Gitee 镜像：
```bash
# 创建并进入工作目录
mkdir -p ~/projects && cd ~/projects

# 克隆项目
git clone https://gitee.com/your-target-repo.git
```

### 步骤 3：在 VS Code 中打开项目
1. 在 Windows 上打开 VS Code，在插件市场搜索并安装 **WSL** 插件。
2. 返回 WSL 终端，进入项目目录，直接运行：
   ```bash
   code .
   ```
   *VS Code 会自动在 Windows 端弹出，并无缝连接到您 WSL 中的代码环境。*