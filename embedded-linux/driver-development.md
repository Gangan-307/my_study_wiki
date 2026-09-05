# Linux 驱动开发

## 学习目标

理解用户空间、设备节点、驱动框架与硬件之间的调用链。能先使用内核现有子系统访问外设，再完成简单字符设备和设备树匹配的平台驱动，并能依据日志和 `/sys` 定位 probe 失败。

## 一、先建立正确边界

```text
用户应用
  ↓ open/read/write/ioctl/poll/mmap
VFS 与具体子系统接口
  ↓
设备驱动
  ↓ clock/reset/pinctrl/irq/dma/regmap 等内核框架
  ↓
硬件控制器与外设
```

驱动的任务不是“把 MCU 裸机寄存器代码搬进内核”。Linux 中需要处理设备模型、并发、睡眠上下文、资源所有权、电源管理和用户空间 ABI。

## 二、学习顺序：先用现成驱动

### 1. GPIO：优先 libgpiod

```bash
gpiodetect
gpioinfo
gpioget <gpiochip> <offset>
gpioset <gpiochip> <offset>=<value>
```

不同 libgpiod 大版本的命令参数可能不同，先查看本机 `--help`。传统 `/sys/class/gpio` ABI 已废弃，新项目优先使用字符设备 GPIO 接口和 libgpiod。

实验时先根据原理图和官方引脚复用表确认：电压、GPIO 控制器、line offset、默认上下拉及该引脚是否已被其他设备占用。

### 2. I2C：使用 i2c-dev

```bash
i2cdetect -l
i2cdetect -y <bus-number>
i2cget -y <bus-number> <chip-address> <register>
```

扫描或随意读写某些 I2C 设备可能改变状态甚至导致异常。先确认总线上的器件和数据手册；生产代码使用 `/dev/i2c-*` 和 `I2C_RDWR` 等接口完成明确事务，不依赖命令行工具拼业务。

### 3. SPI：使用 spidev

- 确认控制器、片选、模式、位宽和最大频率。
- 通过 `/dev/spidevB.C` 和 `SPI_IOC_MESSAGE` 完成全双工传输。
- 逻辑分析仪验证 CPOL、CPHA、CS 时序和实际频率。

并非设备树里写一个泛化 `spidev` compatible 就一定被当前内核接受；优先遵循板卡内核和 binding 的要求。

### 4. 串口

- 理解 `/dev/ttyS*`、`/dev/ttyUSB*` 等设备的来源。
- 使用 `termios` 配置波特率、数据位、校验、停止位和流控。
- 处理短读、超时、粘包、热插拔和设备重命名。

## 三、内核驱动基本规则

### 上下文与睡眠

- 进程上下文通常可以睡眠，中断/原子上下文不能调用可能睡眠的 API。
- `GFP_KERNEL` 可能睡眠，原子上下文的分配策略不同。
- 自旋锁保护短小、不可睡眠的临界区；mutex 用于允许睡眠的互斥场景。
- 不要在持有自旋锁或关闭中断时执行耗时操作。

### 内存与用户指针

- 使用 `kmalloc`、`devm_kzalloc` 等内核 API，不使用用户态 `malloc`。
- 用户空间地址不能直接解引用，使用 `copy_to_user`、`copy_from_user` 等接口。
- MMIO 地址通过资源和 `ioremap`/`devm_ioremap_resource` 获取，不把芯片手册物理地址强转成普通指针。
- 优先使用 GPIO、I2C、SPI、regmap、clock 等子系统 API，不在驱动里绕过资源管理直接操作共享寄存器。

### 错误处理

- 按内核约定返回负 errno，例如 `-EINVAL`、`-ENOMEM`、`-EBUSY`。
- probe 每一步失败都要释放已获得资源；优先使用 `devm_*` 简化设备生命周期绑定。
- 日志包含设备上下文和失败阶段，但避免在高频路径刷屏。

## 四、字符设备要掌握什么

字符设备练习用于理解 VFS 到驱动的入口，不代表所有硬件都应该自创 `/dev/mydev`。

需要理解：

- 主设备号、次设备号和 `dev_t`。
- `alloc_chrdev_region`、`cdev_init`、`cdev_add`。
- class、device 与 `/dev` 节点创建关系。
- `struct file_operations` 中的 `open`、`release`、`read`、`write`、`unlocked_ioctl`、`poll`。
- `file->private_data` 保存每次打开对应的上下文。
- 用户 ABI 一旦发布就要考虑兼容性、长度、并发和 32/64 位差异。

### 第一阶段：虚拟字符设备

先实现不依赖真实硬件的 RAM buffer 设备：

- [ ] 支持有限长度的 `read`/`write` 和文件偏移。
- [ ] 检查用户输入长度并正确返回实际字节数。
- [ ] 两个进程并发访问时数据保持一致。
- [ ] 阻塞读取可被信号打断，支持 `poll` 通知数据到达。
- [ ] 模块卸载前确保没有悬空工作或资源。

## 五、platform driver 与设备树匹配

不可枚举的 SoC 外设常通过 platform 总线组织：

```text
DTS 节点 compatible
        ↓
of_match_table
        ↓
platform_driver 注册
        ↓
核心匹配后调用 probe
        ↓
获取资源并注册面向用户或其他内核模块的接口
```

probe 中的典型步骤：

1. 获取 MMIO、IRQ、GPIO、clock、reset、regulator 等资源。
2. 分配并初始化设备私有数据。
3. 初始化硬件，并注册到对应内核子系统。
4. 使用 `platform_set_drvdata` 保存设备数据。
5. 任何一步失败都返回准确错误；依赖尚未就绪时可能出现 deferred probe。

移除或关闭路径要停止中断、工作队列、定时器和 DMA，再释放资源，顺序通常与初始化相反。

## 六、中断、下半部与 DMA 只掌握边界

首轮需要知道：

- 顶半部只做快速确认、清中断和保存必要状态；耗时工作延后。
- threaded IRQ、workqueue、tasklet 等机制有不同上下文约束，新增代码优先根据当前内核文档选型。
- 中断共享时必须判断是否由自己的设备触发。
- DMA 涉及缓存一致性、映射方向、地址能力和生命周期，必须使用 DMA API，不能直接把虚拟地址交给硬件。

前两个月不要求独立写复杂 DMA 驱动，但面试时要能说出为什么不能照搬 MCU 的 buffer 地址。

## 七、调试路径

```bash
# 模块和日志
modinfo <module>
lsmod
dmesg -w

# 设备与驱动绑定
readlink -f /sys/bus/platform/devices/<device>/driver
ls -l /sys/class
cat /proc/devices
cat /proc/interrupts

# 用户态调用
strace -f ./test_app
```

推荐按层定位：

1. 原理图、电压、连线和波形是否正确。
2. 设备树节点是否存在、启用且实际加载。
3. 驱动是否编译进内核或模块已加载。
4. compatible 是否匹配，probe 是否进入和成功。
5. pinctrl、clock、reset、regulator、IRQ 等资源是否正常。
6. `/dev`、`/sys` 或网络接口是否出现，权限是否正确。
7. 用户应用参数与协议是否正确。

## 八、建议实验阶梯

1. **现有子系统**：libgpiod 控制 LED，或通过 i2c-dev 读取传感器 ID。
2. **模块闭环**：构建、加载、查看日志、卸载 hello module。
3. **虚拟字符设备**：实现带并发保护的内存设备和测试程序。
4. **设备树匹配**：让一个 demo platform driver 匹配自定义节点并读取属性。
5. **真实外设**：在确认内核没有合适现成驱动后，再为简单外设接入正确子系统。

每一级都保存测试应用、预期日志、异常用例和清理方法。

## 九、完成标准

- [ ] 能画出应用调用到驱动和硬件的路径。
- [ ] 能判断某项功能应放用户空间、通用内核子系统还是自定义驱动。
- [ ] 能实现并解释一个可并发访问的虚拟字符设备。
- [ ] 能通过 compatible 让 platform driver 与设备树节点匹配。
- [ ] 能从 `dmesg` 和 `/sys` 判断驱动未加载、未匹配或 probe 失败。
- [ ] 不使用 `/dev/mem` 或用户态寄存器映射替代正式驱动方案。

## 十、后续补充区

- input、IIO、hwmon、LED、RTC 等具体子系统。
- 中断线程化、workqueue、completion 与等待队列。
- runtime PM、regmap 与设备热插拔。
- ftrace、dynamic debug、lockdep 和 KASAN。
