# Linux 入门面试题

[返回专区](/embedded-interview/index.md) | [复习与自测表](/embedded-interview/review-plan.md)

学习要求：先通过泰山派和 WSL 理解实际命令，再回答进程、权限、网络和构建问题。当前以 Linux 使用与应用基础为主，内核驱动能力需要后续实验单独证明。

## L01：程序、进程、线程与 PID 是什么？ :id=l01

**参考回答：** 程序是可执行代码等静态内容，进程是程序的一次运行实例，通常拥有独立虚拟地址空间。一个进程可有多个线程，它们共享地址空间和文件描述符等资源，但各有执行上下文与栈。常见用户接口中的 PID 标识进程，线程也有各自的内核标识。

**易错点：** 运行同一个程序可以产生不同进程；PID 会在退出后被复用，不能当永久身份。线程共享内存不等于没有同步问题。Linux 的“线程”也是调度实体，不能简单把所有进程内执行都理解为一个 PID 对应一个 CPU 上下文。

**面试追问：** `echo $$`、`echo $!` 与 `echo $PPID` 各表示什么？结束一个子进程是否会让整个 SSH 服务退出？

**验证命令：** 在自己的普通用户终端运行，只结束本次创建的 `sleep`；`&` 表示后台运行。

```bash
sleep 300 &
demo_pid=$!
ps -o pid,ppid,user,stat,comm,args -p "$demo_pid"
kill "$demo_pid"
wait "$demo_pid"
```

默认 `kill` 发送 SIGTERM，请求退出；`wait` 此处可能报告进程被终止或返回非零，这是实验的预期结果。SIGKILL 则不能被捕获以执行用户态清理。

## L02：普通用户、root、sudo 与文件权限有什么关系？ :id=l02

**参考回答：** 日常开发使用普通用户，系统管理通过已授权的 `sudo` 执行。常见配置中 `sudo` 验证当前用户密码，`su -` 切换 root 通常验证目标 root 密码。文件权限结合用户、组、访问位和其他访问控制共同决定操作能否成功。

**易错点：** 目录 `r` 允许列出名字，`x` 允许穿过目录查找条目，创建/删除条目通常需要该目录的 `w+x`，还可能受 sticky bit、ACL 等影响。能进入目录不代表能新建文件。文件只读、目录不可写与分区只读要分别排查。

**面试追问：** 为什么 `nano` 能打开文件却保存失败？`chmod`、`chown` 各改什么？为什么不应把 `chmod 777` 当通用修复？

**验证命令：** 查看现状，不修改系统账户或目录所有权。

```bash
id
ls -ld /userdata/workspace
ls -l /userdata/workspace
findmnt -T /userdata/workspace
```

## L03：`systemctl`、PID 1 和 `systemd` 有什么关系？ :id=l03

**参考回答：** Debian 常由 systemd 作为 PID 1 管理系统与服务；`systemctl` 是与其交互的控制工具，`ctl` 是 control 的命名缩写。`.service` 是被管理的单元，单元可能管理多个进程，`MainPID` 表示其中的主进程。

**易错点：** `start` 是当前启动，`enable` 是建立开机等启动关系，`enable --now` 同时执行两者；`failed` 需要查日志，可能是启动失败，也可能是运行中失败。改服务单元后用 `daemon-reload`，改 sshd 自身配置则按服务支持方式 reload/restart。并非所有嵌入式 Linux 都使用 systemd。

**面试追问：** 为什么 `enabled` 的服务也能处于 `failed`？串口有 Shell、SSH 却不能用时，应先检查什么？

```bash
ps -p 1 -o pid,comm,args
systemctl show ssh -p MainPID -p ActiveState -p SubState
systemctl is-enabled ssh
systemctl status ssh --no-pager -l
sudo journalctl -u ssh -b -n 30 --no-pager
```

## L04：SSH 超时、拒绝连接与 `Permission denied` 怎么区分？ :id=l04

**参考回答：** 超时通常先查地址、链路、路由和丢包/防火墙；拒绝连接通常意味着收到明确拒绝，可能没服务监听或被防火墙主动拒绝；认证阶段的 `Permission denied` 应查用户名、密码/密钥、账户状态、PAM 与 sshd 认证策略。

**易错点：** `PasswordAuthentication yes` 不代表 root 一定允许密码登录。`PermitRootLogin prohibit-password` 或其别名 `without-password` 禁止 root 的密码与键盘交互认证。串口自动登录 root 不证明知道 root 密码；账户状态 `P` 只说明有可用密码字段，不保证所有登录策略都允许它。

**面试追问：** 为什么 SSH 能用普通用户登录，但 `su -` 仍失败？不开放 root 密码登录，怎样完成日常管理？

```bash
sudo ss -lntp
sudo /usr/sbin/sshd -t
sudo /usr/sbin/sshd -T | grep -E 'permitrootlogin|passwordauthentication'
```

`sshd -t` 无输出且返回成功，表示配置语法等检查通过；不代表所有用户均能登录。存在 `Match` 条件块时，应用 `sshd -T -C` 带实际连接参数检查对应配置，并结合认证日志判断。

## L05：网口 `UP` 为什么还不能 SSH 或上网？ :id=l05

**参考回答：** 接口启用、底层链路成立、IP 地址、路由、DNS 和目标服务是不同层次。`UP` 主要表示接口被启用；以太网 `LOWER_UP` 通常表示已检测到底层链路。DHCP 可分配 IP、网关与 DNS；同网段互通不一定需要外网网关。

**易错点：** `end1 unmanaged` 表示 NetworkManager 未管理它，不等于网卡损坏，它可能归其他网络工具管理。临时 `ip` 或 `dhclient` 操作不能自动当作持久配置。多个管理工具同时改同一接口可能冲突，持久化前要先确认管理归属。

**面试追问：** 电脑以太网共享需要什么？开发板能 SSH 到电脑却不能访问外网，怎样区分网关、共享转发与 DNS 问题？

```bash
ip -br link
ip -br -4 addr
ip route
nmcli device status
ip route get 223.5.5.5
```

Wi-Fi 与网线并存时，确认测试流量走的接口；默认路由存在并不等于 Windows 共享已经正常转发。ICMP 被过滤也可能导致 Ping 失败，必要时用目标 TCP 服务验证。

## L06：文件描述符是什么？`read/write` 一次就能完成吗？ :id=l06

**参考回答：** 文件描述符是进程中用于引用已打开文件、Socket、管道等资源的小整数；常见标准输入、输出、错误分别为 0、1、2。POSIX `read/write` 通过返回值说明实际处理的字节数，可能短读、短写或被信号中断，调用者要按对象和错误类型处理。

**易错点：** `read` 返回 `-1` 才通过 `errno` 查看错误。对普通文件或流式 Socket，在请求读取非零字节时，返回 0 通常表示 EOF/对端有序关闭；不能把这个结论直接套给 UDP 零长度数据报或所有特殊设备。非阻塞 `EAGAIN` 表示稍后再试，不是数据一定损坏。

**面试追问：** `printf` 为什么不一定马上对应一次 `write`？应用缓冲区刷新与存储落盘又有什么区别？

## L07：交叉编译是什么？为什么有文件也可能“无法执行”？ :id=l07

**参考回答：** 在一种主机环境构建另一目标环境运行的程序就是交叉编译，例如在 x86-64 WSL 为 AArch64 泰山派构建。需要匹配 CPU 架构、ABI、目标运行库和必要的 sysroot；目标程序还可能依赖动态加载器与共享库。

**易错点：** `gcc` 通常构建当前主机目标，不自动生成 ARM 程序。架构错误可能报 `Exec format error`；即使文件存在，缺少 ELF 解释器也可能报“没有那个文件”。还要检查执行权限、挂载 `noexec`、动态库路径和版本。对不可信程序不要随意运行 `ldd`。

**面试追问：** 为什么在泰山派自己运行 `gcc` 属于本机编译？`aarch64-linux-gnu-gcc` 编译成功就一定能在任意 ARM64 系统运行吗？

```bash
file ./hello
readelf -h ./hello
readelf -l ./hello
readelf -d ./hello
```

分别核对文件类型、目标架构、解释器与所需库；这些只检查文件，不会启动目标程序。

## L08：Bootloader、内核、设备树与根文件系统各做什么？ :id=l08

**参考回答：** 典型嵌入式 Linux 启动从 SoC BootROM 开始，后续可能经过多个固件阶段与 U-Boot；Bootloader 准备环境并加载内核及硬件描述，内核初始化子系统并挂载根文件系统，最终运行 PID 1 完成用户空间初始化。设备树描述硬件拓扑与资源，不是驱动程序本身。

**易错点：** 实际启动链可能包含 SPL、可信固件、initramfs 等阶段，不能把简图当所有平台的完整流程。只改 DTS 文件而未生成并加载对应 DTB，不会改变运行配置。`.ko` 模块也需要与目标内核的版本、配置及相关接口兼容。

**面试追问：** 串口停在 U-Boot、内核找不到根文件系统、用户空间 SSH 启动失败，这三种故障分别查哪里？

## 动手验证

- [ ] 用 L01 命令观察 Shell 和子进程；解释每个 PID 字段，确认只结束实验进程。
- [ ] 用普通用户在自己的工作目录保存并编译程序，解释所需权限，避免用 root 掩盖目录所有权问题。
- [ ] 记录 SSH 服务状态、监听端口、认证策略，说明网络连通与认证成功的区别。
- [ ] 用 `ip route get` 确认默认出口；网络恢复后再验证重启是否保留配置。
- [ ] 在 WSL 与泰山派分别对自己构建的 ELF 执行 `file/readelf`，比较架构与依赖。

## 继续学习

- [Linux 使用基础](/embedded-linux/linux-foundations.md)、[泰山派实战](/embedded-linux/taishan-pi.md)
- [系统编程](/embedded-linux/system-programming.md)、[交叉编译](/embedded-linux/cross-compilation.md)
- [启动链](/embedded-linux/boot-chain.md)、[设备树与模块](/embedded-linux/kernel-device-tree.md)
- [Linux 专项面试清单](/embedded-linux/review-checklist.md)
