# 嵌入式 Linux 使用基础

## 学习目标

目标不是背命令，而是能在没有桌面环境的开发板上完成文件管理、权限配置、进程控制、网络排查和日志定位。每学一组命令，都要在 WSL 和开发板各操作一次并比较差异。

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
