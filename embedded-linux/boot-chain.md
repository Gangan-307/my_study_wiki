# 嵌入式 Linux 启动链与系统组成

## 学习目标

能够看到串口启动日志就判断当前处于哪个阶段，知道每个镜像由谁加载、出现问题应查哪一层，并能说明 Bootloader、Kernel、DTB 和 RootFS 之间的关系。

## 一、典型启动链

以常见 ARM SoC 为例，启动过程可以抽象为：

```text
上电/复位
  ↓
SoC BootROM
  ↓
TPL/SPL（初始化时钟、DDR、选择启动介质）
  ↓
U-Boot proper（加载内核、DTB、可选 initramfs）
  ↓
Linux Kernel（初始化内存、调度器和驱动）
  ↓
挂载 RootFS，执行 /sbin/init
  ↓
启动服务，进入登录或业务应用
```

不同 SoC 和厂商 SDK 会增加可信固件、资源镜像、验证启动等阶段。泰山派所用 Rockchip 平台的具体文件名和打包方式应以对应硬件版本及官方 SDK 为准，但各阶段职责仍可按上图理解。

## 二、每一阶段负责什么

### 1. BootROM

- 固化在 SoC 内部，用户通常不能修改。
- 根据引脚、电阻或内部规则选择 eMMC、TF 卡、SPI Flash、USB 下载等启动路径。
- 验证或加载下一阶段引导程序。

若串口完全没有任何输出，不能直接认定 BootROM 失败，还要检查供电、串口电平、TX/RX、波特率和日志是否从该 UART 输出。

### 2. TPL/SPL

- 体积受限，完成最早期硬件初始化。
- 常见任务包括 DDR 初始化、时钟配置和加载完整 U-Boot。
- DDR 参数错误可能表现为早期启动卡死、随机异常或根本没有后续输出。

### 3. U-Boot

- 提供启动介质、文件系统、网络和命令行能力。
- 设置或读取 `bootargs`，将内核、DTB 和可选 initramfs 放到内存。
- 通过 `booti`/`bootm` 等命令把控制权交给内核。

首次学习只做只读观察：

```text
version
printenv
bdinfo
help
```

不要在不了解恢复流程时执行 `saveenv`、擦除、分区写入或更新引导程序。

### 4. Linux Kernel

- 解压或展开自身，初始化 MMU、内存管理、中断、调度器和各子系统。
- 根据 DTB 描述发现板级硬件并匹配驱动。
- 根据内核命令行定位并挂载根文件系统。
- 最后尝试执行 init 进程。

常见关键日志：

```text
Linux version ...
Machine model: ...
Kernel command line: ...
VFS: Mounted root ...
Run /sbin/init as init process
```

### 5. RootFS 与 init

根文件系统提供：

- `/bin`、`/sbin`、库、配置、设备节点和业务应用。
- BusyBox 或完整 GNU 用户空间。
- systemd、SysV init、BusyBox init 等初始化系统。

内核已经启动却找不到根文件系统时，常见错误包括 `Unable to mount root fs`；根文件系统已挂载但 init 不存在、架构不匹配或依赖缺失时，常见错误包括 `No working init found`。

## 三、四个核心产物

| 产物 | 常见形式 | 作用 |
| :--- | :--- | :--- |
| Bootloader | `idbloader.img`、`u-boot.itb` 或厂商打包镜像 | 初始化硬件并加载系统 |
| Kernel | `Image`、`zImage`、`uImage` | Linux 内核本体 |
| Device Tree | `.dtb` | 描述本板硬件连接和启用状态 |
| RootFS | ext4、squashfs、cpio、UBIFS 等 | 用户空间程序、库和配置 |

这些名称会随平台变化。必须能回答“当前板卡实际使用的是哪一个文件、位于哪个分区、由谁加载”，不能只背通用名称。

## 四、运行系统中的只读观察

```bash
# 内核与启动参数
uname -a
cat /proc/version
cat /proc/cmdline

# init 与根文件系统
readlink -f /sbin/init
findmnt /
cat /proc/mounts

# 存储和分区
lsblk -o NAME,MAJ:MIN,SIZE,FSTYPE,LABEL,PARTLABEL,MOUNTPOINTS
blkid

# 设备树模型与兼容串
tr -d '\0' </proc/device-tree/model; echo
tr '\0' '\n' </proc/device-tree/compatible

# 启动日志
dmesg -T | less
```

`/boot` 的内容不一定就是当前实际加载的全部产物。有些板卡从独立原始分区、FIT 镜像或厂商专用分区加载，必须结合分区表、U-Boot 环境和官方打包脚本判断。

## 五、内核命令行

重点理解以下类别，实际参数以 `/proc/cmdline` 为准：

- `console=`：内核控制台设备和串口参数。
- `root=`：根文件系统所在设备、UUID 或网络位置。
- `rootfstype=`：根文件系统类型。
- `rootwait`：等待根设备出现。
- `ro`/`rw`：初始只读或读写挂载。
- `init=`：覆盖默认 init 程序，通常只用于调试。

启动参数错误会让“内核已正常运行”和“用户空间无法启动”同时出现，因此要按阶段看日志。

## 六、启动故障分层

| 最后可见现象 | 优先怀疑 | 第一批证据 |
| :--- | :--- | :--- |
| 无串口输出 | 供电、串口接线/参数、BootROM/早期镜像 | 电源、TX 波形、官方串口配置 |
| 只有早期加载日志 | DDR 初始化、镜像布局、U-Boot | 完整原始日志、镜像版本、启动介质 |
| 停在 U-Boot | 环境变量、内核/DTB 路径或格式 | `printenv`、加载地址、文件系统列表 |
| 内核早期崩溃 | 内核/DTB 不匹配、时钟/内存/驱动 | panic 前完整日志、版本和 DTB |
| 无法挂载 RootFS | `root=`、驱动、文件系统、存储 | `/proc/cmdline`、分区、内核配置 |
| 找不到 init | RootFS 内容、权限、架构、动态加载器 | `/sbin/init`、`file`、库和 symlink |
| 服务未启动 | init 配置、依赖、权限、应用错误 | 服务状态、应用日志、退出码 |

## 七、实验：给启动日志分段

1. 通过串口从上电开始保存未经裁剪的日志。
2. 标出 BootROM/TPL/SPL、U-Boot、Kernel、init 和业务服务的边界。
3. 为每段记录版本、耗时、加载的产物和下一阶段入口。
4. 找出 `bootargs`、内核版本、Machine model、根文件系统和 init。
5. 将串口观察与运行后的 `/proc/cmdline`、`lsblk`、`findmnt` 相互验证。

## 八、完成标准

- [ ] 能在白纸上画出完整启动链并说明每层职责。
- [ ] 能从日志判断故障发生在加载内核前、内核中还是用户空间。
- [ ] 能说明 Kernel、DTB 和 RootFS 为什么必须彼此兼容。
- [ ] 能指出当前板卡启动介质、根分区、内核版本和 init 系统。
- [ ] 在任何写盘实验前，已有可验证的官方恢复方法和镜像备份。

## 九、后续补充区

- Rockchip 启动镜像布局与打包工具。
- FIT image、签名验证与 A/B 升级。
- initramfs、只读根文件系统与 overlayfs。
- U-Boot 网络启动（TFTP/NFS）调试流程。
