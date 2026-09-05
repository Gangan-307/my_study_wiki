# Linux 系统编程

## 学习目标

从 MCU/RTOS 的“任务 + 驱动 API”思维，过渡到 Linux 用户空间的“进程 + 文件描述符 + 系统调用”模型。目标是写出能处理异常、支持退出、可调试的常驻应用，而不是只让 demo 跑通一次。

## 一、文件描述符与文件 I/O

### 必须掌握

- `open`、`read`、`write`、`lseek`、`close`。
- `errno`、`perror`、`strerror` 与系统调用返回值。
- 短读、短写、`EINTR`、阻塞和非阻塞。
- 标准输入 `0`、标准输出 `1`、标准错误 `2`。
- 标准 I/O `FILE *` 的缓冲与系统调用 I/O 的区别。

一个健壮的写循环不能假定一次 `write` 就发送全部数据：

```c
#include <errno.h>
#include <stddef.h>
#include <unistd.h>

ssize_t write_all(int fd, const void *buffer, size_t length)
{
    const char *cursor = buffer;
    size_t remaining = length;

    while (remaining > 0) {
        ssize_t written = write(fd, cursor, remaining);

        if (written > 0) {
            cursor += written;
            remaining -= (size_t)written;
            continue;
        }
        if (written < 0 && errno == EINTR) {
            continue;
        }
        return -1;
    }

    return (ssize_t)length;
}
```

### 实验

- [ ] 实现文件复制工具，处理部分读写并保留权限。
- [ ] 使用 `strace` 对比 `printf` 和 `write` 的调用行为。
- [ ] 打开串口或管道，观察阻塞与 `O_NONBLOCK` 的差异。

## 二、进程、程序与信号

### 必须掌握

- `fork` 复制进程执行上下文，`exec` 用新程序替换当前进程映像。
- `wait`/`waitpid` 回收子进程，避免僵尸进程。
- 退出码用于父进程或脚本判断结果。
- 信号是异步通知；信号处理函数中只能安全调用有限的 async-signal-safe 函数。
- 常驻程序应正确处理 `SIGTERM`，完成资源清理后退出。

### 实验

- [ ] 父进程启动子程序并获取退出状态。
- [ ] 制造一个僵尸进程，通过 `ps` 观察并修复。
- [ ] 为循环运行的程序增加 `SIGINT`/`SIGTERM` 优雅退出。

## 三、线程与同步

已有 FreeRTOS 基础时，重点比较而不是重新背概念：

| Linux/POSIX | RTOS 中的相近概念 | 需要注意 |
| :--- | :--- | :--- |
| `pthread_create` | 创建任务 | 同一进程线程共享地址空间和文件描述符 |
| mutex | 互斥量 | 保护共享不变量，不只是“包住一行变量修改” |
| condition variable | 事件/通知 | 必须与谓词和 mutex 配合，等待要使用循环 |
| semaphore | 计数/二值信号量 | 明确它代表资源计数还是事件 |
| atomic | 原子操作 | 原子性不自动保证复杂业务逻辑一致 |

必须理解线程函数生命周期、`join`/`detach`、竞态、死锁、虚假唤醒和锁的粒度。

### 实验：有界队列

- [ ] 一个采集线程生产数据，一个处理线程消费数据。
- [ ] 使用 mutex + condition variable 实现固定容量队列。
- [ ] 队列满和空时不忙等。
- [ ] 收到退出请求后唤醒所有等待线程并干净退出。
- [ ] 使用 ThreadSanitizer 在主机侧检查竞态条件。

## 四、进程间通信（IPC）

按场景理解机制，不需要一开始把所有 API 都背完：

| 机制 | 适合场景 | 首轮掌握程度 |
| :--- | :--- | :--- |
| 匿名管道 | 有亲缘关系进程的字节流 | 会创建、关闭无用端、处理 EOF |
| FIFO | 无亲缘本机进程的简单字节流 | 会创建和双端通信 |
| Unix domain socket | 本机双向通信、可传递凭据 | 会设计简单请求/响应协议 |
| POSIX 消息队列 | 带消息边界和优先级 | 理解并完成一个 demo |
| 共享内存 | 大量数据、低复制 | 理解同步责任，后续深入 |

重点：IPC 只负责传输，不自动解决消息边界、版本兼容、超时、同步和异常退出。

## 五、网络编程

### TCP 服务端基本链路

```text
socket → setsockopt → bind → listen → accept
                                    ↓
                         recv/send → close
```

### TCP 客户端基本链路

```text
socket → connect → send/recv → close
```

必须理解：

- TCP 是字节流，不保留应用消息边界；一次 `send` 不对应一次 `recv`。
- 网络字节序、粘包/拆包、半关闭、超时和断线重连。
- `SIGPIPE`、`EPIPE`、`ECONNRESET` 等常见异常。
- UDP 保留报文边界，但不保证到达、顺序和去重。

### 自定义协议最小设计

建议使用固定头部，而不是假设每行都是完整消息：

```text
magic | version | type | payload_length | sequence | payload | checksum
```

首个项目可以简化，但至少要限制长度、校验输入并处理协议版本。

## 六、I/O 多路复用

- `select`：接口通用，但描述符数量和集合操作受限。
- `poll`：不受固定 fd 位图限制，每次仍需线性扫描。
- `epoll`：Linux 下适合管理较多 fd；理解 LT/ET、就绪通知和非阻塞 I/O。

学习顺序建议 `poll` → `epoll`。不要为了演示而给每个连接创建一个永久线程，也不要在未理解非阻塞读写前直接照抄 ET 模式。

### 实验

- [ ] 使用 `poll` 同时监听终端输入和一个 Socket。
- [ ] 使用 `epoll` 编写多客户端 echo server。
- [ ] 处理客户端半包、主动断开、异常断开和空闲超时。

## 七、时间、定时与日志

- 使用 `CLOCK_MONOTONIC` 计算超时和持续时间，避免系统时间调整造成跳变。
- 使用 `CLOCK_REALTIME` 表示真实日期时间。
- 区分睡眠、超时和周期任务，避免简单 `sleep(period)` 造成持续漂移。
- 日志至少包含时间、级别、模块和关键上下文；不得输出密码和密钥。

## 八、调试工具

| 工具 | 回答的问题 |
| :--- | :--- |
| `strace` | 程序调用了哪些系统调用，在哪里失败或阻塞 |
| `gdb`/`gdbserver` | 崩溃位置、调用栈、变量和线程状态 |
| `lsof` 或 `/proc/<PID>/fd` | 打开了哪些文件和 Socket |
| `ss` | 哪个进程监听或建立了哪些连接 |
| `pmap`、`/proc/<PID>/maps` | 地址空间如何映射 |
| `valgrind`/Sanitizer | 内存错误、泄漏或数据竞争 |
| `tcpdump`/Wireshark | 网络实际收发了什么 |

## 九、阶段项目

编写一个 **设备状态采集守护程序**：

- 周期读取 `/proc` 或 `/sys` 中的 CPU、内存、温度等信息。
- 一个线程采集，一个线程发送，使用有界队列解耦。
- 通过 TCP 将长度明确的消息发给 WSL 服务端。
- 支持配置文件、日志级别、断线重连和 `SIGTERM` 退出。
- 用 Make/CMake 交叉编译，用 `strace` 和 GDB 完成一次问题定位。

## 十、完成标准

- [ ] 能解释用户态 API、C 库包装和系统调用之间的关系。
- [ ] 所有系统调用都检查返回值，不把 `errno` 当作函数返回值使用。
- [ ] 能写出线程安全队列并解释同步条件。
- [ ] 能设计处理半包的 TCP 协议并完成多客户端服务端。
- [ ] 程序面对断网、对端退出和终止信号时可预测地恢复或退出。
- [ ] 能使用 `strace`、GDB 和系统状态命令建立完整证据链。

## 十一、后续补充区

- `mmap` 与共享内存。
- `eventfd`、`timerfd`、`signalfd`。
- Unix domain socket 凭据与文件描述符传递。
- 守护进程、systemd 服务和资源限制。
