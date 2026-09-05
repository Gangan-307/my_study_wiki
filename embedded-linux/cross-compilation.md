# 交叉编译、构建与 ELF

## 学习目标

能够在 x86_64 WSL 主机上稳定构建可在 ARM64 开发板运行的程序，并独立定位“找不到文件”“格式错误”“动态库缺失”和 ABI 不匹配问题。

## 一、先分清三个角色

- **build**：实际执行构建工具的机器。
- **host**：构建出来的程序将运行的平台。
- **target**：工具链本身生成代码所面向的平台；日常讨论中常把 host/target 简化为“目标板”。

本机编译器通常生成 x86_64 程序，不能直接在 ARM64 板上运行。先分别确认架构：

```bash
# WSL 主机
uname -m

# 开发板
uname -m
getconf LONG_BIT
file /bin/sh
```

不能只根据 SoC 支持 ARM64 就认定用户空间一定是 64 位，还要检查板端镜像和动态加载器。

## 二、工具链组成

以常见 GNU ARM64 工具链前缀为例：

| 工具 | 作用 |
| :--- | :--- |
| `aarch64-linux-gnu-gcc` | 编译 C 并驱动链接过程 |
| `aarch64-linux-gnu-g++` | 编译 C++ 并链接 C++ 运行库 |
| `aarch64-linux-gnu-as` | 汇编 |
| `aarch64-linux-gnu-ld` | 链接 |
| `aarch64-linux-gnu-ar` | 创建静态库 |
| `aarch64-linux-gnu-nm` | 查看符号 |
| `aarch64-linux-gnu-objdump` | 反汇编与查看节区 |
| `aarch64-linux-gnu-readelf` | 查看 ELF 头、段、节和依赖 |
| `aarch64-linux-gnu-strip` | 移除非运行必需的符号信息 |

Ubuntu/WSL 可安装基础工具：

```bash
sudo apt update
sudo apt install build-essential gcc-aarch64-linux-gnu \
  g++-aarch64-linux-gnu binutils-aarch64-linux-gnu \
  make cmake ninja-build pkg-config gdb-multiarch
```

若项目依赖板卡厂商 SDK，应优先使用 SDK 指定的工具链和 sysroot，避免 libc 或 ABI 不一致。

## 三、第一个交叉编译闭环

`hello.c`：

```c
#include <stdio.h>
#include <sys/utsname.h>

int main(void)
{
    struct utsname info;

    if (uname(&info) != 0) {
        perror("uname");
        return 1;
    }

    printf("hello from %s/%s\n", info.sysname, info.machine);
    return 0;
}
```

构建、检查、传输、运行：

```bash
aarch64-linux-gnu-gcc -Wall -Wextra -Werror -g \
  -o hello-aarch64 hello.c
file hello-aarch64
aarch64-linux-gnu-readelf -h hello-aarch64
scp hello-aarch64 user@<board-ip>:/tmp/
ssh user@<board-ip> 'chmod +x /tmp/hello-aarch64 && /tmp/hello-aarch64'
```

将主机原生版本与 ARM64 版本都交给 `file` 和 `readelf -h`，比较 `Machine`、位数和动态加载器信息。

## 四、编译和链接过程

### 四个主要阶段

```bash
# 预处理：.c -> .i
aarch64-linux-gnu-gcc -E hello.c -o hello.i

# 编译：.i -> .s
aarch64-linux-gnu-gcc -S hello.i -o hello.s

# 汇编：.s -> .o
aarch64-linux-gnu-gcc -c hello.s -o hello.o

# 链接：.o + 库 -> ELF
aarch64-linux-gnu-gcc hello.o -o hello
```

需要能区分：

- **编译错误**：语法、类型或声明问题。
- **链接错误**：符号未定义、重复定义、库顺序等问题。
- **加载错误**：解释器或动态库不存在、架构/ABI 不匹配。
- **运行错误**：程序已启动，但出现逻辑、权限或资源问题。

## 五、ELF 必须会看什么

```bash
file ./app
readelf -h ./app
readelf -l ./app
readelf -S ./app
readelf -d ./app
nm -C ./app | less
objdump -d ./app | less
size ./app
```

交叉构建的文件优先使用同前缀工具，例如 `aarch64-linux-gnu-readelf`。需要理解：

- ELF header 描述架构、位数、端序和入口。
- section 主要面向链接，segment 主要面向加载运行。
- `.text`、`.rodata`、`.data`、`.bss` 的基本用途。
- 动态程序由 ELF 中指定的 interpreter 加载，板端缺少它时，shell 可能报 `No such file or directory`，即使程序文件本身明明存在。

板端定位动态依赖：

```bash
file /tmp/app
readelf -l /tmp/app | grep interpreter
ldd /tmp/app
```

不要对不可信二进制直接执行 `ldd`；可优先使用 `readelf -d` 查看声明的依赖。

## 六、静态库、动态库与 sysroot

- 静态库 `.a` 在链接时把所需目标代码放入可执行文件。
- 动态库 `.so` 在程序加载或运行时解析，便于共享和升级，但依赖目标系统环境。
- **sysroot** 是目标系统头文件和库的逻辑根目录，不是简单复制几个 `.so` 就能替代。

检查编译器默认搜索位置：

```bash
aarch64-linux-gnu-gcc -print-sysroot
aarch64-linux-gnu-gcc -print-search-dirs
aarch64-linux-gnu-gcc -v -E -x c /dev/null
```

涉及第三方库时，必须让头文件、链接库、运行库来自兼容的一套目标环境。不要把 WSL 的 x86_64 库路径硬塞给 ARM64 编译器。

## 七、Make 与 CMake 应掌握到什么程度

### Make

必须掌握：目标、依赖、命令、变量、模式规则、自动变量和增量构建。一个交叉编译项目应能通过变量切换编译器：

```make
CROSS_COMPILE ?= aarch64-linux-gnu-
CC := $(CROSS_COMPILE)gcc
CFLAGS := -Wall -Wextra -Werror -O2 -g

app: main.o protocol.o
	$(CC) $(CFLAGS) $^ -o $@

%.o: %.c
	$(CC) $(CFLAGS) -c $< -o $@

clean:
	rm -f app *.o

.PHONY: clean
```

### CMake

理解 toolchain file 的用途，不要在 `CMakeLists.txt` 里到处硬编码交叉编译器：

```cmake
set(CMAKE_SYSTEM_NAME Linux)
set(CMAKE_SYSTEM_PROCESSOR aarch64)
set(CMAKE_C_COMPILER aarch64-linux-gnu-gcc)
set(CMAKE_CXX_COMPILER aarch64-linux-gnu-g++)
```

```bash
cmake -S . -B build-aarch64 \
  -DCMAKE_TOOLCHAIN_FILE=cmake/aarch64-linux-gnu.cmake
cmake --build build-aarch64
```

## 八、典型故障表

| 现象 | 优先检查 |
| :--- | :--- |
| `Exec format error` | ELF 架构、位数、脚本 shebang、文件是否损坏 |
| 文件存在却报 `No such file or directory` | ELF interpreter、动态加载器、脚本解释器、CRLF |
| `error while loading shared libraries` | 库是否存在、架构、SONAME、搜索路径 |
| `undefined reference` | 是否遗漏目标文件/库、链接顺序、C/C++ 名字修饰 |
| `Permission denied` | 执行位、挂载参数、目录权限、安全策略 |
| 板端崩溃 | `dmesg`、退出码、core dump、GDB、库版本和未定义行为 |

## 九、实践清单

- [ ] 同一份程序分别构建 x86_64 和 ARM64 版本并解释差异。
- [ ] 建立包含静态库、动态库和可执行程序的小项目。
- [ ] 用 Makefile 支持 `debug`、`release`、`clean` 和可配置工具链前缀。
- [ ] 用 CMake toolchain file 复现同一项目。
- [ ] 主动制造架构错误、缺库和未定义符号，并记录定位证据。
- [ ] 保留未 strip 调试版本，部署时另生成 strip 后版本。

## 十、完成标准

- [ ] 能从空目录写出一个可维护的多文件构建流程。
- [ ] 能解释头文件、库、运行时加载器和 sysroot 各自解决什么问题。
- [ ] 看到运行错误时，先用 `file`、`readelf`、`ldd` 获取证据，而不是反复重编。
- [ ] 能在 WSL 上使用 `gdb-multiarch` 配合板端 `gdbserver` 调试程序。
