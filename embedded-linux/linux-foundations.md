# 嵌入式 Linux 使用基础

## 学习目标

目标不是背命令，而是能在没有桌面环境的开发板上完成文件管理、权限配置、进程控制、网络排查和日志定位。每学一组命令，都要在 WSL 和开发板各操作一次并比较差异。

查命令名称、英文词源和常用写法，见[基础命令词源与速查](basic-commands.md)；本页继续按系统概念与实验组织学习。

## 一、先建立 Linux 的整体认识

### 1. 用户空间与内核空间

- 应用程序运行在用户空间，不能直接随意访问硬件或内核内存。
- 应用通过系统调用请求内核提供文件、进程、网络和设备访问能力。
- `/dev` 下的设备节点是用户空间访问驱动的一种入口，不等于真实硬件本身。
- `/proc` 和 `/sys` 是内核导出的虚拟文件系统，内容通常不是存储在磁盘上的普通文件。

### 2. “一切皆文件”应如何理解

普通文件、终端、管道、Socket 和许多设备都能抽象成文件描述符，并使用相似的读写接口；但它们的行为并不完全相同，不能把这句话理解为“所有对象都是磁盘文件”。

### 3. 发行版和嵌入式系统的差异

WSL Ubuntu 通常使用 GNU 工具、APT 和较完整的用户空间；开发板镜像可能使用 BusyBox、精简 RootFS 或不同 init 系统。命令缺失、选项不同不一定是系统损坏，先执行：

```bash
cat /etc/os-release
uname -a
readlink -f /sbin/init
busybox 2>/dev/null | head -n 1
```

## 二、文件系统与路径

### 应掌握的命令

| 任务 | 常用命令 | 必须理解 |
| :--- | :--- | :--- |
| 浏览与识别 | `pwd`、`ls -lah`、`tree`、`file`、`stat` | 绝对路径、相对路径、隐藏文件 |
| 创建与移动 | `mkdir -p`、`cp -a`、`mv`、`rm` | 覆盖风险、递归操作 |
| 查找内容 | `find`、`rg`、`grep` | 按名称、类型、内容查找 |
| 链接 | `ln`、`ln -s`、`readlink` | inode、硬链接、符号链接 |
| 空间与挂载 | `df -hT`、`du -sh`、`lsblk`、`mount` | 块设备、分区、文件系统、挂载点 |

### 嵌入式 Linux 知识地图

本节根据 `embedded-linux-knowledge-map.html` 整理，保留原图的 14 个模块、关键命令和面试自查内容，并修正部分平台相关表述。适用于泰山派等运行 Linux 的 ARM Cortex-A / RISC-V 开发板，前置知识是 C 语言与 Linux 基本命令。

先建立五层关系：**硬件 → Bootloader → 内核与驱动 → 根文件系统 → 构建与交付**。命令帮助观察和操作某一层，知识地图帮助判断问题属于哪一层。当前先理解整体，再随实验补充细节，不要求第一轮就完成全部驱动、实时性和 OTA 内容。

#### 01. 硬件与 SoC 基础

- **处理器定位**：Cortex-A 常用于 Linux/Android 应用处理器，Cortex-R 面向实时处理，Cortex-M 常用于裸机或 RTOS。典型 Cortex-M 没有 MMU，不能直接使用普通 Debian/Ubuntu 这类依赖虚拟内存的系统；Linux 也有面向部分架构的 no-MMU 配置，不能概括为“没有 MMU 就绝对不能运行 Linux”。RISC-V 同样要区分具体核心与系统能力。
- **SoC（System on Chip）**：在一颗芯片中集成 CPU、内存控制器及 UART、I2C、SPI、USB、eMMC 等控制器，也可能包含 GPU/NPU。驱动通常围绕设备和控制器展开。
- **MMU（Memory Management Unit）**：提供地址转换和访问权限检查，是虚拟内存与进程隔离的重要硬件基础；按需调页还需要内核配合。
- **常见平台**：NXP i.MX6/8、瑞芯微 RK3308/RK3566/RK3568/RK3588、全志 H3/A64、博通 BCM2711、TI AM335x/AM62x。学习时记录具体 SoC、板型和 BSP 版本。
- **总线与接口**：UART 用于调试和串口通信，I2C 常接传感器，SPI 常接高速串行外设；还需认识 USB、PCIe、SDIO 与 MDIO。组合无线模块可能由 SDIO 连接 Wi-Fi、UART 连接蓝牙，以原理图为准。
- **中断控制器**：ARM 应用处理器常用 GIC（Generic Interrupt Controller）；它与 Cortex-M 上的 NVIC 不同，RISC-V 也有自己的中断控制器体系。
- **时钟、引脚与复位**：外设能否工作需要同时核对供电、clock、pinctrl 和 reset。具体使能顺序由硬件手册和驱动决定。

#### 02. 启动流程全景

下面是常见启动链示意；有些平台使用厂商 Loader，ARM64 平台还可能包含可信固件等阶段，不能把它当作所有板卡固定的六步流程。

```text
BootROM → SPL / 厂商早期 Loader → U-Boot → Kernel → init（PID 1）→ Application
```

| 阶段 | 主要职责 | 出现异常时优先检查 |
| :--- | :--- | :--- |
| BootROM | 执行芯片固化代码，根据启动配置查找并加载下一阶段 | 启动介质、启动模式、镜像格式和认证状态 |
| SPL / 早期 Loader | 在片内 RAM 中运行，完成 DDR 等必要初始化 | DDR 参数、供电、板级初始化和固件匹配 |
| U-Boot | 访问存储或网络，准备启动参数，加载内核、DTB 和可选 initramfs | 环境变量、读取路径、加载地址与镜像类型 |
| Kernel | 初始化内存和驱动，准备根文件系统，启动用户空间 | 内核日志、设备树、存储驱动、`root=` 参数 |
| init / PID 1 | 初始化用户空间，挂载所需文件系统并启动服务 | init 程序、动态加载器、配置和启动日志 |
| Application | 运行业务程序、守护进程和健康监控 | 应用依赖、权限、服务配置和业务日志 |

存在 initramfs 时，内核可以先运行其中的 `/init`，再由它切换到真正的根文件系统。定位启动故障时，先从串口确定最后成功的阶段，再分析后续失败原因。

深入学习：[启动链与系统组成](boot-chain.md)。

#### 03. Bootloader 与 U-Boot

U-Boot（Universal Boot Loader）是常见的嵌入式 Bootloader。`bootcmd` 是自动启动时执行的命令，`bootargs` 是传给内核的参数，常涉及 `console=`、`root=`、`rootfstype=` 与 `ip=`；它们是环境变量，不是独立命令。

下表命令在 **U-Boot 控制台**使用，不是在 SSH 登录后的 Linux Shell 中使用；可用命令取决于编译配置。

| 命令或变量 | 全称 / 助记 | 作用与边界 |
| :--- | :--- | :--- |
| `printenv` / `setenv` / `saveenv` | print / set / save environment | 查看、临时修改、持久保存环境变量；`saveenv` 会写入环境存储 |
| `bootargs` / `bootcmd` | boot arguments / boot command | 内核参数与自动启动命令序列，通过环境命令查看或设置 |
| `tftpboot <addr> <file>` | TFTP boot | 将服务器文件下载到内存；下载完成不等于已经启动内核 |
| `bootz <kaddr> - <dtbaddr>` | boot zImage | 常用于启动 ARM 32 位 `zImage`，`-` 表示不提供 initrd |
| `booti <kaddr> - <dtbaddr>` | boot Image | 常用于启动 ARM64 `Image`；压缩格式支持取决于配置 |
| `bootm` | boot image | 常用于 legacy `uImage` 或 FIT 镜像，按镜像格式选择 |
| `load mmc 0:1 <addr> <file>` | load from MMC | 从 MMC 设备 0 的第 1 分区读取文件；设备号不等同于 Linux 中的编号 |
| `nand erase/write`、`sf probe/erase/write` | NAND flash / SPI flash | 操作 raw flash；SPI flash 通常先 probe，擦写范围必须按实际布局确认 |
| `md` / `mw` | memory display / write | 查看或修改内存；访问寄存器需核对地址、宽度及读写副作用 |
| `mmc rescan` / `usb start` | 重新枚举设备 | 扫描 MMC 或初始化 USB 存储支持 |
| `dhcp` / `ping` | 网络配置 / 连通检查 | 网络启动前排查；部分 U-Boot 配置下 `dhcp` 还会尝试加载文件 |
| `fastboot` / `ums` | Fastboot / USB Mass Storage | 进入支持的 USB 下载模式，或把指定存储暴露给主机 |

开发期可使用 TFTP 加载内核与 DTB、NFS 挂载根文件系统，减少反复烧写。前提是 U-Boot、内核、网卡和服务器配置均支持；加载地址、串口名和存储编号应来自当前板卡资料。

#### 04. 内核配置与编译

- **版本选择**：优先确认当前板卡 BSP 支持的内核和补丁集。厂商内核通常包含板级适配，主线内核的支持程度需实际核对；LTS 的维护状态以 kernel.org 公告为准。
- **配置流程**：使用板卡对应的 `<board>_defconfig` 或厂商配置脚本，再用 `make menuconfig` 调整，结果写入 `.config`。通用 `make defconfig` 不自动等于厂商板级配置。
- **构建目标**：区分内核映像、DTB 和模块；构建模块时需要与目标内核的源码、配置及相关构建产物匹配。
- **内核日志**：用 `dmesg` 查看 printk 日志；`/proc/sys/kernel/printk` 中的控制台阈值影响哪些已有日志打印到控制台，不会自动启用所有 `pr_debug` 调试点。

以下展示常见工具链参数，应在**已配置的内核源码目录**执行，实际配置和目标以 BSP 文档为准；两种架构选择对应的一组。

```bash
# ARM 32 位工具链示例
make ARCH=arm CROSS_COMPILE=arm-linux-gnueabihf- -j"$(nproc)"

# ARM64 工具链示例
make ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu- -j"$(nproc)" Image dtbs modules
make ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu- modules_install INSTALL_MOD_PATH="$PWD/rootfs"
```

| 产物 | 含义 |
| :--- | :--- |
| `vmlinux` | ELF 格式内核，保留匹配版本与调试信息以供分析 |
| `zImage` | 常见 ARM 32 位压缩内核，带自解压启动代码 |
| `Image` | ARM64 常见的未压缩内核映像，不能与 `zImage` 一概称为自解压镜像 |
| `Image.gz` 等 | 压缩后的映像，需要启动加载方支持对应的解压流程 |
| `uImage` / FIT | U-Boot 使用的镜像封装；FIT 可以描述多个组件和认证信息 |
| `*.dtb` | 编译后的设备树 |
| `*.ko` | 可加载内核模块 |

模块安装到暂存根目录下的 `lib/modules/<目标内核 release>/`。这里的版本由本次构建决定，不能使用 WSL 主机的 `uname -r` 推断；目标板运行后，`uname -r` 才反映它正在运行的内核。

系统调用是用户程序主动请求内核服务的重要入口，硬件中断和异常也会进入内核，因此不能称系统调用为“进入内核的唯一入口”。用户空间访问硬件通常通过驱动提供的接口与映射完成。

#### 05. 设备树 Device Tree

设备树把板上的硬件连接、地址和资源描述从驱动实现中分离。同一 SoC 的不同板卡可以复用驱动与公共硬件描述，再提供各自的板级配置。

- **文件关系**：`.dtsi` 常保存 SoC 或板族公共描述，`.dts` 进行包含和覆盖，经构建系统预处理与 `dtc` 编译得到 `.dtb`。Bootloader 向内核传递实际加载的 DTB。
- **Overlay**：`.dtbo` 是设备树叠加描述，可以在支持的引导或运行环境中应用；不保证所有 BSP 都支持动态叠加。
- **匹配与资源**：`compatible` 常参与驱动匹配；`reg` 的含义由父总线和 binding 决定，可能是寄存器范围，也可能是 I2C 地址，不能统一解释成“物理地址和长度”。
- **常见属性**：`interrupts`、`clocks`、`status = "okay"` / `"disabled"`、`pinctrl-names`、`pinctrl-0`；还需按外设核对供电、复位及 GPIO 极性。
- **运行时验证**：查看 `/proc/device-tree` 或 `/sys/firmware/devicetree/base` 中的生效信息，确认部署并加载的是修改后的 DTB，而非只修改了源码。
- **驱动接口**：认识 `of_match_table`、`platform_get_resource`、`of_property_read_u32`、`of_property_read_string` 和 `gpiod_get`；按照对应子系统 binding 与目标内核 API 使用。

建议实验：使能一个串口、描述一个 I2C 传感器，或通过 `gpio-leds` 驱动控制 LED，并记录驱动绑定和实际硬件行为。深入学习：[内核、设备树与模块](kernel-device-tree.md)。

#### 06. 设备驱动

| 知识点 | 应掌握的内容 | 易错边界 |
| :--- | :--- | :--- |
| 设备分类 | 字符设备如 `/dev/ttyS0`；块设备如 `/dev/mmcblk0`；网络设备通常经 Socket 接口使用 | 字符设备不只支持字节流，网络接口通常没有一一对应的 `/dev` 节点 |
| 设备模型 | bus / device / driver 的注册与匹配；许多不可自枚举的 SoC 设备使用 platform bus | SoC 内部存在真实互连，platform bus 是软件模型，不能说内部外设“没有总线” |
| 字符驱动 | 注册设备号、`cdev`、`file_operations`，提供 open/read/write/ioctl 等操作 | `module_init` / `module_exit` 管模块生命周期；`class_create` / `device_create` 配合 devtmpfs、udev 或 mdev 管理节点，API 随内核版本变化 |
| 中断 | `request_irq` / `request_threaded_irq`；硬中断处理尽量短，将工作交给适当上下文 | 硬中断、softirq 和 tasklet 上下文不能睡眠；线程化 IRQ 和普通 workqueue 运行于线程上下文，但持有原子锁时仍不能睡眠；新驱动优先考虑后两者 |
| 并发 | 理解 spinlock、mutex、原子操作、信号量与资源所有权 | 普通 mutex 获取可能睡眠，不能放在硬中断中；共享 IRQ 数据时需匹配锁和 IRQ 屏蔽方式，PREEMPT_RT 下还需核对锁语义 |
| 寄存器访问 | 使用框架提供的 MMIO 映射，例如 `devm_platform_ioremap_resource`，再用 `readl` / `writel` 等访问器 | 不能把物理地址直接当普通内核指针；部分设备应通过已有子系统 API 操作 |
| 用户与内核传输 | `copy_to_user` / `copy_from_user`、受控的 `mmap` 接口 | 用户指针可能无效或触发缺页；拷贝接口返回未复制的字节数，需要检查，不能随手换成 `memcpy` |
| 资源回收 | 理解 `devm_*` 托管资源与驱动卸载流程 | 托管释放不等于自动解决异步工作、DMA 或回调的生命周期，应先停止访问再释放资源 |

学习顺序：最小模块 → 简单字符设备及节点 → 按键中断与消抖 → I2C 传感器 → 一个真实子系统，例如 input、backlight 或 regulator。能够复用现有框架时优先复用。深入学习：[Linux 驱动开发](driver-development.md)。

#### 07. 存储与文件系统

先区分 **MTD（Memory Technology Devices）管理的 raw NOR/NAND** 与 **块设备层中的 eMMC/SD**。eMMC/SD 内部控制器通常处理闪存转换、坏块和磨损管理，不能直接套用 raw NAND 的操作方法。

| 文件系统或机制 | 含义 | 特点与典型用途 |
| :--- | :--- | :--- |
| SquashFS | 压缩只读文件系统 | 常用于只读 rootfs，可配 OverlayFS；不能保护刷写镜像时被断电破坏的数据 |
| ext4 | Fourth Extended Filesystem | 日志型可读写文件系统，常用于 eMMC/SD 的 rootfs 或 data；日志不等于业务写入永不丢失 |
| UBIFS | UBI File System | 位于 UBI 卷之上，配合 UBI 的坏块处理与磨损均衡，常用于 raw NAND / SPI-NAND |
| JFFS2 | Journalling Flash File System 2 | 用于 raw flash，小容量 NOR 中仍常见；挂载扫描成本随容量增长 |
| F2FS | Flash-Friendly File System | 面向闪存块设备的可写文件系统，关注随机写入和写放大，具体效果取决于负载 |
| initramfs | initial RAM filesystem | 常由 cpio 归档展开到内存，可内置内核或单独加载，用于早期用户空间、救援和挂载真实 rootfs |
| tmpfs | 内存文件系统 | 常用于临时文件，内容不跨重启保存；通常可使用交换空间，取决于配置 |
| procfs / sysfs / devtmpfs | 内核提供的不同文件系统 | 分别常见于 `/proc`、`/sys`、`/dev`；它们的职责不能混为一谈 |

常见产品布局可以是 `[Bootloader][Kernel + DTB][rootfs A][rootfs B][data]`，实际分区以镜像和升级方案为准。raw flash 可以通过设备树 fixed-partitions 或受支持的 `mtdparts=` 等方式描述分区。

OverlayFS 将只读 lower 层与可写 upper 层合并展示；upper 放 tmpfs 时改动重启丢失，放 data 分区时可以持久保存。只读系统与可写数据分离有助于减少破坏范围，但仍需考虑数据一致性、介质故障和升级过程中的断电。

#### 08. 用户空间与 rootfs

根文件系统需要提供 init、基础工具、运行库、配置和应用。了解每个组件的职责，才能判断“命令不存在”或“服务没启动”究竟缺了什么。

| 组件 | 作用 | 应核对的条件 |
| :--- | :--- | :--- |
| BusyBox | 把多个 applet 编进一个可执行文件，可通过 `busybox ls` 或相应链接调用 | applet 数量和选项由配置决定；系统里的 `ls` 也可能来自 GNU coreutils，不能默认两者完全等价 |
| init 系统 | BusyBox init、systemd 等负责 PID 1 的系统初始化与服务管理 | BusyBox init 可按 `/etc/inittab` 启动 `/etc/init.d/rcS`，具体内容由 rootfs 构建配置决定；systemd 使用 unit，不能照搬脚本路径 |
| C 运行库 | glibc、musl、uClibc-ng 等提供 C/POSIX 运行支持 | ABI、动态加载器、库版本和应用构建必须匹配；更换 C 库通常需要重建相关用户空间组件 |
| 设备节点 | devtmpfs 提供基础节点，udev / mdev 补充权限、命名和热插拔处理 | mdev 常查看 `/etc/mdev.conf`，udev 则检查规则；仅有驱动不代表当前用户有权访问设备 |
| SSH 与网络 | Dropbear / OpenSSH、udhcpc、wpa_supplicant、hostapd | 分别涉及远程服务、DHCP、无线客户端和 AP；网络由谁管理要先确认 |
| 音视频与 Web | ALSA、GStreamer、nginx、lighttpd | 按业务需要选择，不是所有开发板镜像都会预装 |
| 常用配置 | `/etc/fstab`、`/etc/passwd`、`/etc/hostname`，以及 init 和网络配置 | `/etc/network/interfaces` 只适用于相应管理方案，NetworkManager 等可能使用其他配置位置 |

泰山派当前使用 Debian，先熟悉普通用户、APT、systemd、SSH 与日志。理解 BusyBox rootfs 时，重点比较它与当前系统的工具、服务和配置差异。深入学习：[Buildroot 与根文件系统](buildroot.md)、[Linux 系统编程](system-programming.md)。

#### 09. 交叉编译工具链

交叉编译是指构建环境与程序目标运行环境不同，例如在 x86-64 WSL 上生成泰山派 ARM64 程序。工具链名称常表达 `arch[-vendor]-os-abi`，不能仅凭前缀推断所有 CPU 指令集和运行库细节。

| 常见工具链前缀 | 含义 | 适用边界 |
| :--- | :--- | :--- |
| `arm-linux-gnueabihf-` | 32 位 ARM、GNU/Linux、硬浮点调用约定 | 常见于支持该 ABI 的 ARMv7 用户空间；具体指令集和 FPU 还要核对编译配置 |
| `arm-linux-gnueabi-` | 32 位 ARM、GNU/Linux、基础 EABI 浮点调用约定 | 是否使用硬件浮点指令还受 `-mfloat-abi` 等选项影响，不能仅理解成所有浮点都由软件计算 |
| `aarch64-linux-gnu-` | AArch64 GNU/Linux 工具链 | 适用于目标为 ARM64 且运行库兼容的系统，例如当前泰山派 Debian；不能只根据 SoC 支持 64 位判断已安装系统的 ABI |
| `arm-linux-musleabihf-` | 32 位 ARM、musl、硬浮点 ABI 的常见命名 | 常用于精简用户空间，实际前缀以 SDK 输出为准，不能与 glibc 动态库任意混用 |

- **Autotools**：`--build` 描述构建所在系统，`--host` 描述所构建程序的运行系统，`--target` 主要用于编译器等会生成目标代码的工具；普通应用交叉编译通常关心前两者。例如 `./configure --host=aarch64-linux-gnu --prefix=/usr`，再按项目约定用 `DESTDIR` 暂存安装结果。
- **CMake**：使用 `-DCMAKE_TOOLCHAIN_FILE=...` 提供编译器、目标系统和搜索路径，而不是只替换某个 `gcc` 字符串。
- **sysroot**：包含目标头文件、库和开发链接文件，不一定直接复制板上运行时 rootfs 就完整可用。`pkg-config` 还需正确配置 `PKG_CONFIG_SYSROOT_DIR` 与 `PKG_CONFIG_LIBDIR` 等，避免误用主机 `.pc` 文件和库。
- **工具链来源**：厂商 SDK、Bootlin 等预编译工具链、Buildroot 或 crosstool-ng。内核和模块保持构建条件匹配，应用则匹配目标用户空间 ABI；内核与应用不必在所有项目中使用完全相同的编译器版本。
- **部署前检查**：`file` 检查架构，`readelf -l` 检查 ELF 解释器，`readelf -d` 检查动态依赖；对自己构建的可信程序，可在目标系统进一步用 `ldd` 检查库解析结果。

下面以已经构建好的 `app` 为例，在主机检查；交叉工具前缀根据 SDK 调整。

```bash
file ./app
aarch64-linux-gnu-readelf -h ./app
aarch64-linux-gnu-readelf -l ./app
aarch64-linux-gnu-readelf -d ./app
```

使用目标工具链的 `strip` 可以减小部署文件体积，但应保留未剥离的匹配 ELF 和调试信息，避免出现故障后无法还原调用位置。深入学习：[交叉编译、构建与 ELF](cross-compilation.md)。

#### 10. 构建系统：Buildroot 与 Yocto

手工制作 rootfs 适合理解组成，持续维护产品还需要可复现的源码版本、配置、依赖与构建流程。Buildroot 和 Yocto/OpenEmbedded 都可组织工具链、内核、软件包及镜像构建。

| 维度 | Buildroot | Yocto / OpenEmbedded |
| :--- | :--- | :--- |
| 配置入口 | `make menuconfig`、defconfig、包配置和板级文件 | layer、recipe（`.bb`）、配置文件与 BitBake 任务 |
| 主要概念 | target、toolchain、package、rootfs、board | Poky、`meta-*`、`MACHINE`、`IMAGE_INSTALL`、任务依赖与 sstate |
| 构建与产物 | 支持包级构建，常见镜像位于 `output/images/`；部分配置变更需要干净重建 | 使用任务依赖与共享状态缓存组织增量构建，可产出镜像、软件包和 SDK |
| 适合的维护方式 | 相对直接的整机镜像构建，单一或较少板型的项目 | 多板型、多产品、跨团队复用和长期分层维护 |
| 学习与维护成本 | 入口较集中，但仍要掌握包集成、补丁与重建规则 | 概念更多，需理解层优先级、变量展开、任务和缓存 |

两者都有定制和复用能力，不能简化成“Buildroot 不支持增量”或用固定天数承诺掌握。当前可先沿泰山派 BSP 学习 Buildroot，Yocto 作为后续扩展。

**镜像部署**：整盘镜像可用 `dd` 等工具写入确认后的目标块设备；厂商方案可能使用瑞芯微 RKDevTool / `upgrade_tool`、NXP `uuu`、全志 PhoenixSuit 或 Fastboot。镜像格式与烧写位置必须匹配，不把分区镜像当作整盘镜像使用。

**TFTP + NFS 开发**：在 U-Boot 中加载内核和 DTB，通过 `bootargs` 指定 `root=/dev/nfs`、`nfsroot=<server>:/nfsroot`、`ip=dhcp` 和当前板卡的 `console=`。还需要配置服务器导出权限，以及内核早期可用的网卡、网络自动配置和 NFS root 支持；它不是仅改一行环境变量就必然可用的方案。

深入学习：[Buildroot 与根文件系统](buildroot.md)。

#### 11. 调试与性能

| 工具或方法 | 观察内容 | 使用要点 |
| :--- | :--- | :--- |
| 串口控制台 | Bootloader、内核和用户空间的启动输出 | 使用相容电平的 USB-UART 和 `minicom` / `picocom` 等；115200 8N1 只是常见配置，部分瑞芯微镜像使用 1500000，按板卡资料核对 |
| GDB / gdbserver | 断点、寄存器、变量和调用栈 | 板上 `gdbserver :1234 ./app`，主机使用支持目标架构的 GDB 与匹配 ELF，通过 `target remote <board-ip>:1234` 连接 |
| core dump | 应用崩溃时的进程现场 | `ulimit -c unlimited` 只调整当前 Shell 及其子进程的资源限制，还需核对 `core_pattern`、存储权限和 systemd-coredump 等处理方式 |
| strace / ltrace | 系统调用 / 可追踪的动态库调用 | `strace -o app.strace ./app` 可记录系统调用与错误码；静态链接、内联等会影响 ltrace 可见范围 |
| 内核 Oops | 异常寄存器、调用栈和故障上下文 | 使用匹配的 `vmlinux` / 模块 ELF 与调试信息；`addr2line` 前先处理 KASLR、模块加载地址或符号偏移，不能总把运行地址直接代入 |
| top / vmstat / iostat | CPU、内存、调度与 I/O 的总体状态 | 先定位资源瓶颈，再决定是否分析具体函数；部分命令需要安装对应工具包 |
| perf / ftrace | 性能热点、事件与内核执行路径 | 依赖内核配置和权限；采样数据可用于火焰图，跟踪本身也有开销 |
| devmem | 受支持环境下的物理地址访问 | 依赖 `/dev/mem` 和权限；不能绕过驱动随意操作已被管理的硬件，读取某些寄存器也可能有副作用 |
| `/dev/watchdog` | 硬件看门狗控制与超时恢复 | 明确何时启动、谁喂狗、超时时间及关闭语义；业务卡死后若仍无条件喂狗，就无法反映真实健康状态 |

应用无法运行时，分别检查架构、执行权限、解释器、库依赖和配置，不凭经验比例断言根因。内核调试应保存与固件对应的配置、ELF、符号和日志。深入学习：[工程调试与项目追问](../embedded-interview/debugging-projects.md)。

#### 12. 实时性与电源管理

- **实时性目标**：区分平均响应快与最坏延迟可控。普通通用配置不能直接保证业务的硬实时截止时间，控制任务要明确可接受延迟与失约后果。
- **PREEMPT_RT**：提高内核可抢占性并使多数中断线程化，Linux 6.12 将相关核心支持合入主线；实际能否启用、驱动能否配合以及延迟水平，仍取决于架构、内核配置与负载，不能仅凭版本号认定系统已经实时化。
- **调度策略**：认识 `SCHED_FIFO` / `SCHED_RR`，用 `chrt` 查看或在受控实验中设置策略。高优先级忙循环可能饿死其他任务，优先级和 CPU 预算必须一起考虑。
- **测量延迟**：使用 `cyclictest` 等工具观察最大值和分布，同时记录测试时长、压力负载、CPU 调频和中断配置；测得的最大值不是所有场景的严格上界。
- **优先级反转**：低优先级任务持锁、高优先级任务等锁、中优先级任务抢占 CPU。按场景使用支持优先级继承的锁；用户态 POSIX mutex 的 PI 协议需要设置并确认支持，不是所有 mutex 默认具备。
- **CPU 调频**：认识 performance、powersave、ondemand、schedutil 等 governor。在 `/sys/devices/system/cpu/cpufreq/policy*/` 或相应 CPU 的 cpufreq 目录查看，实际选项与效果依赖驱动。
- **休眠与唤醒**：`/sys/power/state` 列出支持的系统休眠状态，`/sys/power/mem_sleep` 可说明 `mem` 的具体行为。`echo mem > /sys/power/state` 会尝试休眠，需要权限、可用唤醒源和驱动 PM 回调支持；SSH 连接可能因此中断。
- **功耗预算**：同时记录工作电流、待机电流、各状态时长与唤醒次数；CPU 休眠不代表无线、屏幕和其他外设已经处于低功耗。

设备树用于描述相关硬件资源和唤醒关系，驱动实现相应的 suspend/resume 或 runtime PM 回调；这两部分不能混成“在设备树中编写回调”。

#### 13. 安全与 OTA 升级

- **安全启动链**：从可信根出发，验证后续可变启动组件的真实性与完整性；典型链路可能覆盖早期 Loader、U-Boot、内核、DTB 与 initramfs。FIT 校验是其中一种实现，具体覆盖范围要看产品方案。
- **密钥与信任**：某些 SoC 将公钥摘要等信任锚存入 OTP/eFuse，而不是把签名私钥写入设备。TPM 的度量启动也不能直接等同于 SoC ROM 的强制验证启动。
- **断电一致性**：只读 rootfs 与可写 data 分离可缩小故障影响。关键文件更新需考虑临时文件、`fsync`、原子替换及目录持久化，数据库使用其事务机制；仅执行一次 `sync` 不等于解决所有中途断电场景。
- **A/B 升级**：向非当前启动分区写入新镜像，检查目标型号、空间、完整性和签名，再切换启动目标。启动次数限制、健康检查、成功确认与回滚状态必须由 Bootloader 和用户空间协作维护。
- **框架选择**：了解 SWUpdate、RAUC、Mender 的适用方式；全量、增量更新及回滚能力依赖具体版本、配置和后端，不能假定每个框架默认具备相同能力。
- **失败路径**：覆盖下载中断、镜像不匹配、写入断电、启动即崩溃、业务不健康及数据格式不兼容。看门狗可以触发重启，但如果没有启动失败计数和回滚逻辑，重启后仍可能反复进入坏系统。
- **系统维护**：管理默认账户与密钥、关闭无用服务、限制权限、按需配置防火墙并维护补丁。组件数量少有助于减少暴露面，不能替代认证、更新和故障恢复设计。

当前先能画出升级状态与恢复路径，再在具备恢复手段的实验设备上验证；未执行的断电或回滚实验不写成已完成的结果。

#### 14. 学习路线与高频面试题

把原图路线与当前 MCU、ESP32 实习和泰山派基础结合，按下面顺序推进：

```text
C 语言与数据结构
  → MCU 寄存器、中断和总线
  → Linux 使用、交叉编译与应用开发
  → U-Boot、Kernel、DTB、rootfs
  → 设备树与驱动
  → Buildroot / 后续按需学习 Yocto
  → 可复现的项目与故障复盘
```

**实验平台**：原图提到树莓派、i.MX6ULL 教学板和 RK3568 等路线，可分别参考其社区、教学或 BSP 资料；当前已有泰山派，可以继续用它完成基础、应用、设备树和系统构建实验，不必为了覆盖地图而另购开发板。

**参考资料**：[Bootlin 免费培训资料](https://bootlin.com/docs/)、[Linux 内核文档](https://docs.kernel.org/)、厂商对应版本 BSP 文档，以及《鸟哥的 Linux 私房菜》等使用基础资料。LDD3 可用于理解历史驱动概念，但代码基于较旧内核，移植时必须对照当前内核 API。

**面试自查表**：先闭卷解释，再用自己的命令、源码或实验结果支撑答案。

| 题目 | 对应模块 | 回答应覆盖 |
| :--- | :--- | :--- |
| 一颗芯片从上电到应用运行经历什么？ | 02 启动链 | 各阶段职责、当前板卡的实际差异，以及如何从串口定位停止阶段 |
| 设备树是什么，`compatible` 怎样匹配驱动？ | 05 设备树 | 硬件描述与驱动的区别、DTS 到生效 DTB、资源与 binding |
| 字符设备驱动的基本结构是什么，节点如何出现？ | 06 驱动 | 设备号、cdev、file_operations、设备模型及节点管理 |
| 中断处理为什么有不能睡眠的限制？ | 06 驱动 | 区分硬中断、softirq、线程化 IRQ、workqueue 和持锁约束 |
| MMU 有什么作用，Cortex-M 与应用处理器有什么差别？ | 01 硬件 | 地址转换、访问保护、典型系统需求，以及 no-MMU 的适用边界 |
| 交叉编译中 `--build`、`--host`、`--target` 有何区别？ | 09 工具链 | 构建工具运行在哪里、生成物运行在哪里，以及 ABI / sysroot |
| SquashFS + OverlayFS 能解决哪些断电问题，不能解决哪些？ | 07 文件系统 | 只读与可写层、持久化位置，以及应用事务和更新镜像的限制 |
| Buildroot 和 Yocto 怎么选？ | 10 构建 | 产品数量、板型复用、团队经验、构建和维护需求 |
| A/B 升级如何回滚，看门狗起什么作用？ | 13 OTA | 备用分区、启动状态、健康确认、失败计数、重启与回滚的区别 |
| 为什么不能用 `memcpy` 随意替代 `copy_to_user`？ | 04 内核、06 驱动 | 用户地址校验、访问异常处理、上下文限制和返回值检查 |

使用时先通读启动链，每个模块按“能解释 + 能验证”验收。例如设备树部分，应能说明节点和驱动关系，并验证一次实际配置修改。面试前用自查表定位薄弱点，再回到对应模块补课，不只记固定说法。

地图用于建立整体认识，基础命令、权限、进程、网络和 Shell 练习继续结合本页后续章节。后续扩展可进入[嵌入式面试八股专区](../embedded-interview/index.md)、[两个月学习路线](roadmap.md)和[综合项目](project.md)。

开发板上操作存储设备前，必须先用 `lsblk -o NAME,SIZE,FSTYPE,MOUNTPOINTS,MODEL` 确认对象。不要仅凭 `/dev/mmcblk0` 或 `/dev/mmcblk1` 的编号判断 TF 卡和 eMMC。



### 目录职责

- `/boot`：常见的内核、DTB 和启动配置位置，具体布局由镜像决定。
- `/dev`：设备节点。
- `/etc`：系统和服务配置。
- `/proc`：进程及内核运行信息。
- `/sys`：设备模型、驱动和内核对象信息。
- `/run`：本次启动期间的运行状态。
- `/var/log`：持久或轮转日志，精简系统不一定完整提供。
- `/lib/modules/$(uname -r)`：当前内核版本对应的模块目录。

## 三、用户、权限与环境

### 权限模型

读懂下面输出中：文件类型、所有者、用户组以及 `rwx` 三组权限。

```bash
ls -l app
id
umask
```

需要掌握：

- `chmod 755 app` 与 `chmod u+x app` 的含义。
- `chown user:group file` 修改的是所有权，不是访问模式。
- `sudo` 是以授权身份执行命令，不是解决所有权限问题的固定前缀。
- 普通用户无法访问设备时，应先检查设备节点权限、所属组和 udev 规则。

### 环境变量

```bash
printf '%s\n' "$PATH"
env | sort
export APP_LOG_LEVEL=debug
which gcc
type cd
```

要能解释 shell 内建命令、可执行文件搜索路径、当前 shell 临时变量和登录配置文件之间的关系。

## 四、进程、信号与资源

### 日常观察

```bash
ps -ef
ps -eo pid,ppid,stat,%cpu,%mem,comm --sort=-%cpu | head
top
free -h
cat /proc/meminfo | head
cat /proc/<PID>/status
ls -l /proc/<PID>/fd
```

### 进程控制

需要掌握：

- 前台、后台、`jobs`、`fg`、`bg` 和 `nohup` 的区别。
- PID、PPID、进程状态和僵尸进程的含义。
- `SIGTERM` 用于请求正常退出，`SIGKILL` 无法被捕获且不给程序清理机会。
- 程序异常时先保留现场，再决定是否强制终止。

```bash
kill -TERM <PID>
kill -KILL <PID>
```

## 五、网络与远程开发

```bash
ip -br address
ip route
ping -c 4 <gateway-or-host>
ss -lntup
ssh user@<board-ip>
scp ./app user@<board-ip>:/tmp/
curl -v http://<host>:<port>/
```

排查顺序建议固定为：

1. 网卡是否存在并处于 UP 状态。
2. 是否获得正确 IP 和掩码。
3. 路由和默认网关是否正确。
4. IP 是否可达，域名解析是否正常。
5. 目标进程是否存在、端口是否监听、防火墙是否拦截。

## 六、日志与问题定位

```bash
dmesg -T | tail -n 100
journalctl -b --no-pager | tail -n 100
journalctl -u <service-name> -f
tail -F /var/log/<log-file>
```

并非所有嵌入式镜像都使用 systemd。若 `journalctl` 不存在，先确认 init 系统，再查看串口输出、`dmesg`、服务自身日志和 `/var/log`。

形成固定记录格式：

```text
现象：用户实际看到了什么
时间：首次发生和复现时间
环境：镜像、内核、应用版本
证据：日志、退出码、进程、端口、波形
变化：问题发生前改过什么
结论：根因与验证方式
```

## 七、Shell 必备能力

理解下面符号，而不是只会复制：

- `>` 覆盖输出，`>>` 追加输出，`2>` 重定向标准错误。
- `|` 将前一程序的标准输出接到后一程序的标准输入。
- `&&` 仅在前一命令成功时继续，`||` 仅在失败时继续。
- `$?` 是上一命令退出状态，通常 `0` 表示成功。
- 双引号允许变量展开，单引号按字面保留内容。

### 实验：板卡信息采集脚本

脚本至少采集以下项目并写入带时间戳的文本：

- [ ] 系统版本、内核版本和启动时间。
- [ ] CPU、内存、磁盘与挂载信息。
- [ ] IP、路由和监听端口。
- [ ] CPU 或内存占用最高的 5 个进程。
- [ ] 最近 30 条内核日志。
- [ ] 任一命令失败时输出明确错误并返回非零退出码。

## 八、完成标准

- [ ] 不查资料完成文件搜索、权限修改、进程终止和 SSH 传输。
- [ ] 能解释 `/proc`、`/sys`、`/dev` 的区别。
- [ ] 能根据“板卡 SSH 不通”独立执行分层排查。
- [ ] 能写一个使用变量、判断、循环、函数和退出码的 Bash 脚本。
- [ ] 能从日志和系统状态中提取可用于定位问题的证据。

## 九、后续补充区

- Bash 参数展开与严格模式。
- systemd unit 或 BusyBox init 脚本。
- udev 规则与设备权限。
- 挂载、文件系统检查和只读根文件系统。
