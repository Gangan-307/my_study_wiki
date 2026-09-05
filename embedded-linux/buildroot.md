# Buildroot 与根文件系统

## 学习目标

能够从配置构建工具链、内核和根文件系统，将自己的应用作为 package 集成，使用 overlay 添加配置，并产出一套可复现的系统。首轮重点是理解系统如何组成，不追求极致裁剪。

## 一、Buildroot 做什么

Buildroot 通过 Kconfig 和 Makefile 组织嵌入式 Linux 系统构建，可以生成：

- 交叉工具链，或使用指定的外部工具链。
- Bootloader 和 Linux Kernel。
- BusyBox、C 库、系统服务及第三方软件包。
- ext4、squashfs、cpio 等形式的根文件系统镜像。
- 主机侧打包和镜像生成工具。

Buildroot 是构建系统，不是运行在板端的软件包管理器。通常修改配置后在主机重新构建镜像，而不是把目标系统当 Ubuntu 一样长期 `apt install`。

## 二、先分清官方 SDK 与上游 Buildroot

泰山派官方 SDK 可能包含厂商维护的 U-Boot、Linux、Buildroot 以及专用打包脚本。第一次构建建议：

1. 固定官方文档、SDK commit/版本和推荐主机环境。
2. 不改代码，完整复现一次官方默认镜像。
3. 保存构建命令、耗时、输出文件和烧录/恢复流程。
4. 再做一次只增加自己应用的最小修改。

直接用上游 Buildroot 的通用 RK356x 配置，不保证泰山派所有板级资源可用。上游版本适合后续理解标准结构和减少厂商脚本依赖。

## 三、基本工作流

下面是通用形式，实际 defconfig 以板卡 SDK 为准：

```bash
# 源码外构建，避免污染源码树
make O="$PWD/output/taishan" <board_defconfig>

# 查看或调整配置
make O="$PWD/output/taishan" menuconfig

# 构建
make O="$PWD/output/taishan" -j"$(nproc)"

# 保存最小配置
make O="$PWD/output/taishan" savedefconfig
```

常见输出目录：

| 路径 | 用途 |
| :--- | :--- |
| `output/build/` | 各软件包解压和构建目录，不应手工长期修改 |
| `output/host/` | 主机工具、交叉工具链及 sysroot |
| `output/staging/` | 通常链接到目标 sysroot |
| `output/target/` | 根文件系统展开树，不应把临时手改当正式方案 |
| `output/images/` | 最终镜像、内核、DTB 等产物 |

如果要修改包源码，应通过补丁、包定义或外部源码机制完成；直接编辑 `output/build` 的修改会在清理后消失。

## 四、配置系统要掌握什么

- `make menuconfig`：配置用户空间包、工具链和系统级选项。
- `make linux-menuconfig`：配置 Linux Kernel。
- `make uboot-menuconfig`：配置 U-Boot，前提是当前配置启用了它。
- defconfig：保存项目必须的最小 Buildroot 配置。
- fragment：为内核等组件维护可审查的增量配置。

每次调整后都要保存配置 diff，不能只保留巨大的构建目录。

## 五、rootfs overlay

overlay 用于把固定文件覆盖到目标根文件系统，例如：

```text
board/taishan/rootfs-overlay/
├── etc/
│   └── my_gateway.conf
└── usr/
    └── share/
        └── my_gateway/
```

适合放配置模板、启动脚本和少量静态资源。不适合用 overlay 粗暴塞入无法追踪来源的动态库或手工编译二进制；应用及依赖应优先封装为 package。

## 六、自定义应用 package

建议通过 `BR2_EXTERNAL` 保存板级配置和自定义软件包，使其不直接混入 Buildroot 主仓库：

```text
br2-external-study/
├── external.desc
├── external.mk
├── Config.in
├── configs/
│   └── taishan_study_defconfig
├── board/taishan/
└── package/my-gateway/
    ├── Config.in
    └── my-gateway.mk
```

本地源码 package 需要明确：

- 源码位置和版本。
- 依赖项。
- 使用目标交叉编译器的构建命令。
- 安装到 target 的路径。
- 许可证和许可证文件。

不要在 package 中调用主机裸 `gcc`，应使用 Buildroot 提供的 `$(TARGET_CC)`、`$(TARGET_MAKE_ENV)` 或对应基础设施。

## 七、启动服务

先确认系统 init 类型：

- systemd：编写 unit，定义依赖、重启策略、运行用户和日志方式。
- BusyBox/SysV init：按镜像约定增加 `/etc/init.d/SNNname` 脚本。

业务进程至少应满足：

- 可前台运行，便于 init 系统管理，不自行重复 daemonize。
- 正确响应 `SIGTERM`。
- 配置和可写数据分离，日志不会无限占满 eMMC。
- 重启策略有退避，不在永久故障时高速重启。

## 八、构建可复现性

仓库应记录：

- Buildroot、板卡 SDK、U-Boot、Kernel 和工具链版本。
- defconfig、内核配置片段、DTS 修改和补丁。
- `BR2_EXTERNAL` 内容、overlay 和应用源码版本。
- 主机发行版、必要依赖和一条完整构建命令。
- 输出镜像校验值、烧录方法和恢复方法。

不要提交庞大的 `output/` 目录；提交生成它所需的配置、补丁和脚本。

## 九、故障定位

| 现象 | 优先检查 |
| :--- | :--- |
| 主机工具构建失败 | 主机依赖、路径、磁盘、SDK 要求、第一处错误 |
| 目标包链接到 x86_64 库 | 是否绕过 `TARGET_*`、pkg-config/sysroot 配置 |
| 应用未出现在 RootFS | package 是否选中、install target 命令和目标路径 |
| 启动脚本不执行 | init 类型、文件名/权限、换行符、解释器 |
| 镜像启动但设备缺失 | Kernel 配置、DTB、模块安装和固件文件 |
| 增量构建不生效 | 包时间戳与依赖，必要时只清理目标 package 后重建 |

不要一遇到错误就删除整个输出目录。先定位失败 package 和首个有效报错，理解 Buildroot 的依赖后再选择局部重建或全量构建。

## 十、Buildroot 与 Yocto 的边界

| 维度 | Buildroot | Yocto Project |
| :--- | :--- | :--- |
| 首次上手 | 相对直接 | 概念和元数据体系更复杂 |
| 目标 | 快速构建固定嵌入式系统 | 大型产品发行版和多层复用 |
| 包管理 | 通常以整镜像更新为主 | 可生成完整包仓库和 SDK 流程 |
| 当前阶段 | 应实际完成一次项目 | 先理解用途，不并行深挖 |

掌握 Buildroot 后再学习 Yocto，会更容易理解交叉工具链、sysroot、RootFS 和 package recipe 解决的共同问题。

## 十一、实践清单

- [ ] 无修改完成一次官方 SDK 全量构建并记录产物。
- [ ] 使用独立输出目录和固定 defconfig 重建相同系统。
- [ ] 通过 overlay 增加一份配置文件。
- [ ] 将综合项目应用封装为 Buildroot package。
- [ ] 应用开机启动、可停止、可查看日志并能异常重启。
- [ ] 从干净源码按 README 再构建一次，验证不是依赖残留环境。

## 十二、完成标准

- [ ] 能解释 `host`、`staging`、`target`、`images` 目录的区别。
- [ ] 能通过配置和 package 添加功能，不依赖手改输出目录。
- [ ] 能追踪应用使用的交叉编译器、头文件、动态库和安装位置。
- [ ] 能把构建配置、源码版本、镜像和恢复步骤对应起来。
- [ ] 能判断问题属于构建系统、内核/DTB、RootFS 还是业务应用。

## 十三、后续补充区

- post-build、post-image 脚本和 genimage。
- initramfs、squashfs、overlayfs 与只读系统。
- 软件许可证清单与供应链版本管理。
- A/B 分区、升级包签名和断电保护。
