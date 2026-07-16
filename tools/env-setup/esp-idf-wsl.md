# WSL-Ubuntu 环境下 ESP-IDF 开发搭建与使用指南（含 VS Code 联动）

本指南涵盖了从环境依赖安装、国内镜像加速克隆、VS Code 远程开发配置，到最终的 WSL 串口烧录与监视的完整流程。

---

## 一、 准备工作：安装 Ubuntu 编译依赖

在开始之前，必须在 WSL 终端中安装编译 ESP32 所需的 Linux 系统工具包：

```bash
sudo apt update
sudo apt install -y git wget flex bison gperf python3 python3-pip python3-venv cmake ninja-build ccache libffi-dev libssl-dev dfu-util libusb-1.0-0
```

---

## 二、 核心步骤：克隆与安装 ESP-IDF（国内加速版）

由于官方 GitHub 仓库体积庞大且子模块极多，国内直接克隆极易失败。以下是官方推荐的 **Gitee 国内镜像极速安装法**。

### 1. 克隆主仓库（以 v5.1 稳定版为例）
```bash
# 创建并进入工作目录
mkdir -p ~/esp && cd ~/esp

# 使用深度为 1 的克隆（不拉取历史记录，速度极快）
git clone -b v5.1 --depth 1 https://gitee.com/EspressifSystems/esp-idf.git
```

### 2. 使用官方国内工具更新子模块
```bash
cd ~/esp/esp-idf

# 下载乐鑫官方 Gitee 辅助工具
git clone https://gitee.com/EspressifSystems/esp-gitee-tools.git

# 运行工具，将所有依赖的子模块重定向到国内镜像并下载
./esp-gitee-tools/submodule-update.sh
```

### 3. 安装编译器与工具链（使用乐鑫国内 CDN 加速）
运行安装脚本前，设置环境变量使工具链从国内服务器下载：
```bash
# 设置国内下载源
export IDF_GITHUB_ASSETS="dl.espressif.cn/github_assets"

# 运行安装脚本（可指定芯片，如 esp32s3；若需支持所有芯片则不加参数或写 all）
./install.sh esp32s3
```

---

## 三、 配置环境变量（Export）

在编译代码前，必须激活 ESP-IDF 的环境变量。

### 1. 临时激活（当前终端有效）
```bash
. ~/esp/esp-idf/export.sh
```

### 2. 永久便捷配置（推荐）
为了避免每次打开终端都要手动输入，可以将其写为快捷命令（Alias）：
1. 打开配置文件：
   ```bash
   nano ~/.bashrc
   ```
2. 在文件末尾添加以下一行：
   ```bash
   alias get_idf='. ~/esp/esp-idf/export.sh'
   ```
3. 保存退出（`Ctrl + O` 保存，`Ctrl + X` 退出），并刷新配置：
   ```bash
   source ~/.bashrc
   ```
*以后每次打开 WSL 终端，只需输入 **`get_idf`** 即可快速激活开发环境。*

---

## 四、 联动 VS Code 远程窗口连接 Ubuntu (核心开发体验)

通过 VS Code 的远程连接功能，您可以在 Windows 的图形界面下，直接编辑和调试保存在 WSL-Ubuntu 中的代码。

### 1. 准备工作（Windows 端）
1. 在 Windows 上打开 **VS Code**。
2. 点击左侧活动栏的 **Extensions（插件）** 图标（快捷键 `Ctrl + Shift + X`）。
3. 搜索并安装 **WSL** 插件（由 Microsoft 官方出品）。

### 2. 方法 A：从 WSL 终端一键唤醒 VS Code（最简便）
1. 打开您的 WSL 终端（Ubuntu）。
2. 进入您克隆的项目目录（例如 `DOIT_AI`）：
   ```bash
   cd ~/DOIT_AI
   ```
3. 输入以下命令并回车：
   ```bash
   code .
   ```
   *如果是首次运行，VS Code 会自动在 WSL 中安装后台服务，随后在 Windows 端自动弹出一个连接好 WSL 的新窗口。*

### 3. 方法 B：从 VS Code GUI 手动连接
1. 在 Windows 上打开 VS Code。
2. 点击窗口左下角的 **蓝绿色双箭头“远程窗口”图标**。
3. 在顶部弹出的菜单中选择 **Connect to WSL**。
4. 连接成功后，点击菜单栏 `File -> Open Folder`，在弹出的路径框中选择或输入你在 WSL 中的项目路径（例如 `/home/lichen/DOIT_AI`），点击确定。

> **提示**：连接成功后，VS Code 左下角会显示 **`WSL: Ubuntu`**。此时在 VS Code 中按快捷键 **``Ctrl + ` ``** 调出的终端就是 WSL 终端。

---

## 五、 关键突破：WSL 2 串口挂载（解决烧录与监视问题）

WSL 2 默认无法读取 Windows 的 USB/串口。我们需要使用 `usbipd-win` 工具将开发板的串口“穿透”到 WSL 中。

### 步骤 1：Windows 主机端操作
1. 在 Windows 上下载并安装 [usbipd-win 最新版 (.msi)](https://github.com/dorssel/usbipd-win/releases)。
2. 插入您的 ESP32 开发板。
3. 以**管理员身份**打开 Windows PowerShell，运行：
   ```powershell
   # 列出所有 USB 设备
   usbipd list
   ```
   *找到类似 `Silicon Labs CP210x` 或 `CH340` 设备，记录其 `BUSID`（例如 `1-4`）。*
4. **共享设备**（仅首次连接需要绑定）：
   ```powershell
   usbipd bind --busid <你的BUSID>
   ```
5. **挂载到 WSL**（每次拔插板子或重启后需要运行）：
   ```powershell
   usbipd attach --wsl --busid <你的BUSID>
   ```

### 步骤 2：WSL 终端内操作（首次需要）
1. 在已连接 WSL 的 VS Code 内置终端中，赋予当前用户访问串口的权限：
   ```bash
   sudo usermod -a -G dialout $USER
   ```
   *(执行后建议重启 WSL：在 PowerShell 中运行 `wsl --shutdown`)*。
2. 检查串口是否成功挂载：
   ```bash
   ls /dev/ttyUSB*
   ```
   *如果输出 `/dev/ttyUSB0`，说明挂载成功。*

---

## 六、 实战：编译、烧录与监视标准工作流

准备工作完成后，在 VS Code 的 WSL 内置终端中执行以下标准开发流程：

```bash
# 1. 激活环境（如果您设置了 alias）
get_idf

# 2. 进入项目目录
cd ~/DOIT_AI

# 3. 设定目标芯片（如 esp32s3, esp32 等）
idf.py set-target esp32s3

# 4. 编译项目
idf.py build

# 5. 一键烧录并打开串口监视器
# -p 参数指定串口号，flash 代表烧录，monitor 代表监视打印
idf.py -p /dev/ttyUSB0 flash monitor
```

### 💡 常用监视器快捷键：
* **退出串口监视器**：按下 `Ctrl + ]`。