# Linux 内核、设备树与模块

## 学习目标

能识别当前运行内核与其构建产物，读懂并小幅修改设备树，完成与当前内核严格匹配的模块构建、加载和排错。首轮不要求通读内核源码。

## 一、内核源码树先看哪里

| 路径 | 内容 |
| :--- | :--- |
| `arch/arm64/` | ARM64 架构代码、配置和设备树 |
| `drivers/` | 各类设备驱动与总线子系统 |
| `include/` | 公共头文件和架构相关接口 |
| `kernel/` | 调度、进程、锁等核心机制 |
| `mm/` | 内存管理 |
| `fs/` | VFS 和文件系统 |
| `net/` | 网络协议栈 |
| `Documentation/` | 内核官方文档和设备树 binding |

遇到 API 或设备树属性时，先查当前源码版本的 `Documentation/` 和同子系统现有驱动，不要只依赖版本不明的博客。

## 二、版本匹配

```bash
uname -r
cat /proc/version
zcat /proc/config.gz > running-kernel.config 2>/dev/null
ls /lib/modules/$(uname -r)
```

外部模块至少需要匹配：

- 内核 release/version magic。
- ARM64 架构和编译选项。
- 相关配置项与符号版本（启用 `CONFIG_MODVERSIONS` 时尤其重要）。
- 厂商对内核源码的补丁和配置。

从另一个镜像随便取同名版本内核头文件，不等于匹配当前内核。

## 三、配置与构建产物

### Kconfig 与 defconfig

- `Kconfig` 定义配置项及其依赖。
- `.config` 是一次具体构建的完整配置。
- `defconfig` 是用于生成 `.config` 的精简基线，不应简单等同于完整配置文件。
- `make menuconfig` 修改的是当前输出目录中的 `.config`。

通用的 ARM64 外部输出目录构建形式：

```bash
export ARCH=arm64
export CROSS_COMPILE=aarch64-linux-gnu-

make O=out <board_defconfig>
make O=out -j"$(nproc)" Image dtbs modules
```

`<board_defconfig>`、工具链和构建命令必须按板卡 SDK 说明替换。厂商内核常有额外脚本和打包步骤，首次应先完整复现官方构建，再做最小修改。

### 常见产物

- `arch/arm64/boot/Image`：ARM64 未压缩内核镜像。
- `arch/arm64/boot/dts/.../*.dtb`：编译后的设备树二进制。
- `*.ko`：可加载内核模块。
- `vmlinux`：带符号的 ELF 内核映像，调试和分析很重要。
- `System.map`：内核符号地址映射。

## 四、内核模块

### 最小模块

```c
#include <linux/init.h>
#include <linux/kernel.h>
#include <linux/module.h>

static int __init study_init(void)
{
    pr_info("study_module: loaded\n");
    return 0;
}

static void __exit study_exit(void)
{
    pr_info("study_module: unloaded\n");
}

module_init(study_init);
module_exit(study_exit);

MODULE_LICENSE("GPL");
MODULE_AUTHOR("lichen");
MODULE_DESCRIPTION("Embedded Linux study module");
```

外部模块 Makefile：

```make
obj-m += study_module.o

KDIR ?= /lib/modules/$(shell uname -r)/build

all:
	$(MAKE) -C $(KDIR) M=$(CURDIR) modules

clean:
	$(MAKE) -C $(KDIR) M=$(CURDIR) clean
```

板端具备匹配的构建目录时可原生编译；交叉编译时应把 `KDIR` 指向已经配置并构建过的对应内核输出目录，同时传入 `ARCH` 和 `CROSS_COMPILE`。

### 模块观察与管理

```bash
modinfo ./study_module.ko
sudo insmod ./study_module.ko
dmesg | tail
lsmod | grep study_module
sudo rmmod study_module
```

- `insmod` 按路径加载单个模块，不自动解析依赖。
- `modprobe` 使用模块数据库并处理依赖，通常配合安装到 `/lib/modules/<release>` 和 `depmod`。
- 加载失败时立即查看 `dmesg`，`Invalid module format` 常与 version magic 或架构不匹配有关。

## 五、设备树解决什么问题

设备树描述“这块板上有哪些不可自动枚举的硬件、地址/中断/引脚如何连接、哪些节点启用”。驱动代码描述“如何控制某类兼容硬件”。二者通过 `compatible` 等信息匹配。

### 源文件关系

- `.dts`：具体板级入口。
- `.dtsi`：SoC 或多个板卡共享的包含文件。
- `.dtb`：由 DTC 编译、Bootloader 交给内核的二进制。
- YAML binding：属性语义和约束，是新增/修改节点的重要依据。

### 基础语法示意

```dts
/ {
    demo_device {
        compatible = "study,demo-device";
        status = "okay";
        label = "lab-device";
    };
};
```

真实总线设备还会涉及 `reg`、`interrupts`、`clocks`、`resets`、`pinctrl-*`、GPIO phandle 等。`reg` 的单元数量和含义由父节点的 `#address-cells`、`#size-cells` 决定，不能脱离父节点直接解释。

### 常见关键属性

- `compatible`：按从具体到通用的顺序列出兼容串，用于驱动匹配。
- `status`：常见为 `okay` 或 `disabled`。
- `reg`：地址/编号及范围，语义由所在总线决定。
- `interrupts`：中断描述，格式由 interrupt parent 决定。
- `pinctrl-0`、`pinctrl-names`：设备不同状态对应的引脚配置。
- `*-gpios`：对某项功能引用 GPIO 控制器和标志。

## 六、查看正在运行的设备树

```bash
# 板卡模型和根 compatible
tr -d '\0' </proc/device-tree/model; echo
tr '\0' '\n' </proc/device-tree/compatible

# 浏览运行时树
find /proc/device-tree -maxdepth 2 -type d | sort | less

# 系统装有 dtc 时，将运行时树导出为可读 DTS
dtc -I fs -O dts -o running.dts /sys/firmware/devicetree/base
```

DTC 反编译可能给出告警，厂商设备树也可能使用宏展开后难以阅读。分析时应结合原始 DTS/DTSI、binding、`dmesg` 和 `/sys/bus/*/devices`。

## 七、设备与驱动是否匹配

```bash
# 平台设备与驱动
find /sys/bus/platform/devices -maxdepth 1 -type l | sort
find /sys/bus/platform/drivers -maxdepth 1 -type d | sort

# 查看某个设备绑定的驱动
readlink -f /sys/bus/platform/devices/<device>/driver

# 查内核日志中的 probe 信息
dmesg | grep -iE 'probe|defer|fail|error'
```

节点存在不代表驱动已成功工作。要依次验证：节点启用、compatible 匹配、驱动已编译/加载、依赖资源就绪、probe 返回成功、用户态接口出现。

## 八、设备树实验的安全流程

1. 保存当前可启动镜像、DTB、完整串口日志和恢复方法。
2. 找到官方 DTS/DTSI 中一个实际外设节点，查对应 binding。
3. 每次只修改一个属性，并保存修改前后的 diff。
4. 只重新构建必要产物，但按板卡要求完成正确打包。
5. 不覆盖唯一可启动介质；优先使用可回退的 TF 卡或备份启动项。
6. 上电后通过模型、日志、`/proc/device-tree` 和设备接口验证实际加载的是新 DTB。

## 九、完成标准

- [ ] 能解释 `.config`、defconfig、Image、DTB、module 和 `vmlinux` 的关系。
- [ ] 能为当前运行内核构建并加载版本匹配的模块。
- [ ] 能读懂基础 DTS 层级、引用和关键属性。
- [ ] 能从设备树节点追踪到 `/sys` 设备、绑定驱动和用户态接口。
- [ ] 能通过串口恢复一次错误的 DTB 修改，不把“能重刷”留在想象中。

## 十、后续补充区

- pinctrl、clock、reset、regulator 和中断域。
- Device Tree overlay 与板卡支持情况。
- Kconfig/Makefile 新驱动集成。
- ftrace、dynamic debug 和内核崩溃分析。
