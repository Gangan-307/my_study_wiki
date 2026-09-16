# Linux 基础命令：词源、用途与易错点

[返回 Linux 专区](index.md) | [Linux 使用基础与知识地图](linux-foundations.md)

根据本地 `linux-command-etymology.html` 整理，按原文的 **14 组**保留全部命令，并加入常用写法与易错点。原 HTML 标为“100 条”，但存在重复编号；这里按实际 **119 条记录**重新编号，合并介绍的 `vim / vi`、`jobs / fg / bg`、`apt / apt-get` 展开后共 **123 个命令名**。

词源用于助记，不是每个命令都有固定的“英文全称”。区分正式名称、普通英文词、历史来源和后来的助记解释；最终要能说清命令操作的对象、参数含义与执行结果。

## 当前学习顺序

| 优先级 | 先掌握什么 | 对应分组 |
| :--- | :--- | :--- |
| 第一轮 | 路径、创建与复制文件、查看文本、编辑器、身份和权限 | 01-06 |
| 第二轮 | 进程、内存、磁盘、SSH、IP 与服务日志 | 07-09、12-13 |
| 第三轮 | 压缩归档、APT、systemd、管道和批量处理 | 03、10-11 |
| 按需补充 | RPM 系包管理、数据库客户端、复杂网络工具 | 11、12、14 中与项目相关的条目 |

示例主要面向 Debian/Ubuntu 的常见 GNU 工具和 Bash。BusyBox、不同发行版及工具版本的选项可能不同；命令未安装时先查来源。`app.log`、`hello.c`、`demo/` 等是实验文件名，先在自己的工作目录准备对应对象。

## 命名规律

| 规律 | 示例 | 记忆边界 |
| :--- | :--- | :--- |
| 单词截短 | copy → `cp`，move → `mv`，remove → `rm`，password → `passwd` | 看懂动作，不必强行逐字母拆解 |
| 词组缩写 | print working directory → `pwd`，process status → `ps` | `ps` 是 process，不是拼成 `pross` |
| 历史用法 | `grep` 来自 ed 的 `g/re/p`，`tar` 来自 tape archive | 现代用途不再局限于最初环境 |
| 人名或命名趣味 | `awk` 来自 Aho、Weinberger、Kernighan；`less` 呼应 more | 人名首字母也是缩写，但不是功能英文短语 |
| 前后缀 | `mk-` 表示 make，`-ctl` 表示 control，`-gen` 表示 generator | `systemctl` 的 ctl 与 `nmcli` 的 cli 含义不同 |

`cli` 是 command-line interface（命令行接口），`ctl` 是 control（控制）；`daemon` 指守护进程，许多相关程序名以 `d` 结尾，但不能把所有名字都按这一规则硬拆。

## 01. 文件与目录

| 编号 | 命令 | 词源 / 助记 | 用途、常用写法与易错点 |
| :--- | :--- | :--- | :--- |
| 001 | `ls` | list，列出 | `ls -lah` 查看隐藏项、权限和大小；目录项的大小不等于目录内全部文件的总大小 |
| 002 | `pwd` | print working directory | 显示当前工作目录；`pwd -P` 查看解析符号链接后的物理路径 |
| 003 | `cd` | change directory | `cd /userdata/workspace` 切目录，`cd ..` 返回父目录，`cd -` 返回上次目录；命令与路径之间要有空格 |
| 004 | `mkdir` | make directory | `mkdir -p demo/logs` 创建目录及缺失的父目录 |
| 005 | `rmdir` | remove directory | `rmdir empty-dir` 只删除空目录，非空时报错 |
| 006 | `rm` | remove | `rm -i sample.txt` 交互删除文件，`-r` 递归处理目录；`-f` 不代表能绕过权限或只读挂载 |
| 007 | `cp` | copy | `cp hello.c hello-copy.c` 复制文件，`cp -a demo demo-copy` 尽量保留属性；已有目标可能被覆盖 |
| 008 | `mv` | move | `mv old.txt new.txt` 移动或改名；跨文件系统通常涉及复制再删除，不能视为一次原子重命名 |
| 009 | `touch` | touch，触碰 | `touch notes.txt` 更新访问/修改时间；文件不存在时通常创建空文件，存在时不会清空内容 |
| 010 | `ln` | link | `ln -s target.txt shortcut.txt` 创建符号链接；不加 `-s` 创建硬链接，硬链接通常不能跨文件系统 |
| 011 | `find` | find，查找 | `find . -type f -name '*.c'` 递归查找；引号防止 Shell 提前展开通配符 |
| 012 | `which` | which，哪一个 | `which gcc` 在 PATH 中查找程序；不能完整解释 Shell 内建、函数和别名，另查 `type` / `command -v` |
| 013 | `whereis` | where is，在哪里 | `whereis gcc` 在指定或标准位置查找二进制、源码和手册；不保证本机安装了源码 |
| 014 | `locate` | locate，定位 | `locate hello.c` 查询文件名数据库；结果可能过期，数据库通常由 `updatedb` 维护 |
| 015 | `tree` | tree，树 | `tree -L 2 .` 显示两层目录结构；可能需要单独安装 |
| 016 | `file` | file，文件 | `file ./hello` 根据内容和规则判断文件类型；查看 ELF 架构时比文件扩展名更有用 |

`cd` 通常是 Shell 内建，因为需要改变当前 Shell 的目录。输入 `cd/` 会被当作另一个命令路径；`ip tspi` 也不能查询用户身份，应该使用 `id tspi`。

## 02. 查看文件内容

| 编号 | 命令 | 词源 / 助记 | 用途、常用写法与易错点 |
| :--- | :--- | :--- | :--- |
| 017 | `cat` | concatenate，连接 | `cat /etc/os-release` 查看文本，`cat part1.txt part2.txt` 拼接输出；大文件宜用分页器 |
| 018 | `more` | more，更多 | `more app.log` 分页查看；部分实现可以后退，不能一概说只能向前 |
| 019 | `less` | less is more 的命名呼应 | `less app.log` 支持滚动和搜索，`/error` 搜索，`q` 退出；不修改文件 |
| 020 | `head` | head，头部 | `head -n 20 app.log` 显示前 20 行，默认通常为 10 行 |
| 021 | `tail` | tail，尾部 | `tail -n 20 app.log` 看末尾；`tail -f` 跟随增长，GNU `tail -F` 按名字跟随并重试，适合日志轮转 |
| 022 | `tailf` | tail + follow 的助记 | 历史日志跟随工具，许多现代系统已不提供；优先学习 `tail -f` / `tail -F`，不把实现细节视为完全相同 |
| 023 | `stat` | status，状态 | `stat hello.c` 查看 inode、权限、大小与时间；ctime 是元数据变更时间，不是创建时间，birth time 是否可用取决于支持 |

## 03. 文本搜索与处理

| 编号 | 命令 | 词源 / 助记 | 用途、常用写法与易错点 |
| :--- | :--- | :--- | :--- |
| 024 | `grep` | ed 的 `g/re/p`：全局、正则、打印 | `grep -n 'error' app.log` 输出匹配行号；`-F` 按固定字符串，`-E` 使用扩展正则 |
| 025 | `sed` | stream editor | `sed -n '1,20p' app.log` 输出指定行，`sed 's/old/new/g' file.txt` 替换后输出；不加 `-i` 通常不改原文件 |
| 026 | `awk` | Aho、Weinberger、Kernighan | `awk '{print $1}' data.txt` 取第一字段，默认按空白分字段；不是按屏幕上的固定字符列切割 |
| 027 | `wc` | word count | `wc -l file.txt` 统计换行符，`-w` 统计词，`-c` 统计字节；字节数不等于中文字符数 |
| 028 | `sort` | sort，排序 | `sort -n numbers.txt` 按数值排序；默认排序受 locale 影响，普通字典序与数值序不同 |
| 029 | `uniq` | unique，唯一 | `uniq -c sorted.txt` 合并并计数相邻重复行；非相邻重复项不会自动合并 |
| 030 | `cut` | cut，剪切 | `cut -d ':' -f 1 /etc/passwd` 提取字段；不理解 CSV 引号、转义等复杂格式 |
| 031 | `tr` | translate / transliterate | `tr '[:lower:]' '[:upper:]' < words.txt` 转换字符；读取标准输入，不按 sed 的方式解释整段替换字符串 |
| 032 | `diff` | difference | `diff -u old.txt new.txt` 比较文本；退出码 1 表示有差异，并非命令运行错误 |
| 033 | `tee` | T 形分流管 | `printf '%s\n' hello` 的输出可接到 `tee output.txt`，同时输出到终端和文件；默认覆盖文件，`-a` 追加 |
| 034 | `xargs` | 构造 arguments，常按扩展参数助记 | 从标准输入构造命令参数；文件名含空格或换行时优先使用与 `find -print0` 配对的 `xargs -0` |

下面两条各自展示管道的用法，不会修改输入日志或源码；示例中 `find` / `xargs` 选项按 GNU 工具说明。

```bash
grep -i 'error' app.log | sort | uniq -c
find . -type f -name '*.c' -print0 | xargs -0 -r wc -l
```

## 04. 编辑器

| 编号 | 命令 | 词源 / 助记 | 用途、常用写法与易错点 |
| :--- | :--- | :--- | :--- |
| 035 | `vim / vi` | Vi IMproved / visual | `vi hello.c` 打开文件，`i` 插入，Esc 回普通模式，`:wq` 保存退出，`:q!` 放弃未保存修改；vi 不一定是完整 Vim |
| 036 | `nano` | 命名呼应 pico；也有 Nano's ANOther editor 的递归展开 | `nano hello.c` 编辑，Ctrl+O 写入并确认文件名，Ctrl+X 退出；终端显示的 `^` 表示 Ctrl |

编辑器未安装与文件不可写是两种问题。Debian 中可按需要通过已授权的 `sudo apt install nano` 安装；保存失败时检查文件及父目录权限、所有权和只读挂载，不能仅靠换编辑器解决。

## 05. Shell 基础

| 编号 | 命令 | 词源 / 助记 | 用途、常用写法与易错点 |
| :--- | :--- | :--- | :--- |
| 037 | `man` | manual | `man ls` 查手册，`man 2 read` 查系统调用；NAME 一节通常是名称与简介，不保证解释词源 |
| 038 | `clear` | clear，清除 | 清理终端显示；常见交互式 Shell 中 Ctrl+L 可重绘屏幕，但不等于删除命令历史或所有滚动缓存 |
| 039 | `alias` | alias，别名 | `alias ll='ls -l'` 定义当前 Shell 别名；新终端是否保留取决于启动文件，脚本也不一定展开别名 |
| 040 | `echo` | echo，回声 | `echo "$PWD"` 输出展开后的变量；转义和 `-n` 等行为存在差异，精确输出优先 `printf '%s\n' "$value"` |
| 041 | `history` | history，历史 | Bash 中 `history 20` 查看近期命令；历史范围和保存行为由 Shell 与配置决定 |
| 042 | `env` | environment | 查看环境，或用 `env APP_LOG_LEVEL=debug ./app` 仅为本次启动设置环境变量 |
| 043 | `export` | export，导出 | `export APP_LOG_LEVEL=debug` 让后续子进程继承变量；不会修改父进程或已经运行的程序环境 |

`>` 覆盖写入、`>>` 追加写入、`|` 连接标准输出与标准输入；这些是 Shell 语法。`sudo echo value > file` 中的重定向仍由当前 Shell 执行，不能因此获得写入受限文件的权限。

## 06. 用户与权限

| 编号 | 命令 | 词源 / 助记 | 用途、常用写法与易错点 |
| :--- | :--- | :--- | :--- |
| 044 | `su` | substitute user 的常见解释 | `su -` 通常切换到 root 并建立登录环境；认证通常使用目标用户密码，仍受 PAM 等策略约束 |
| 045 | `sudo` | 历史上常解释为 superuser do | 按授权策略以目标身份执行命令，不仅限于 root；常见配置验证当前用户密码，`sudo -l` 查看允许的操作 |
| 046 | `id` | identity | `id` 查看当前 UID、GID 与组，`id tspi` 查询指定用户；用户名不是 `ip` 的子命令 |
| 047 | `useradd` | user add | 创建账户，`useradd -D` 可查看默认设置；创建家目录、Shell 等由参数和配置决定 |
| 048 | `userdel` | user delete | 删除账户；`-r` 还会处理家目录等内容，不是普通文件删除或退出登录命令 |
| 049 | `passwd` | password | 修改密码，`passwd -S` 查看自己账户的状态；状态信息不代表所有登录方式均被允许 |
| 050 | `chgrp` | change group | `chgrp group file.txt` 修改所属组，能改到哪些组取决于身份与权限 |
| 051 | `chmod` | change mode | `chmod u+x ./app` 增加所有者执行位，`chmod 644 notes.txt` 设置权限；不会改变所有者 |
| 052 | `chown` | change owner | `chown user:group file.txt` 修改所有权，通常需要管理权限；递归 `-R` 会扩大修改范围，注意路径拼写 |

目录的 `r`、`w`、`x` 分别关系到列出名字、修改目录项、穿过目录查找对象。新建或删除文件通常需要父目录的 `w+x`，还可能受 ACL、sticky bit 等限制。学习时用 `id`、`ls -ld`、`ls -l` 分别确认身份、目录和文件状态。

## 07. 进程与任务

| 编号 | 命令 | 词源 / 助记 | 用途、常用写法与易错点 |
| :--- | :--- | :--- | :--- |
| 053 | `ps` | process status | `ps -ef` 查看进程快照；PID、PPID、用户和命令各自有不同含义 |
| 054 | `top` | top，顶部排行 | 动态观察任务和资源，`q` 退出；不把 table of processes 当作必须背诵的官方全称 |
| 055 | `htop` | 由作者 Hisham 命名的 top 类工具 | 交互查看进程、线程与资源，需要单独安装；显示列和线程展示由配置决定 |
| 056 | `kill` | kill，名称直译为终止 | 按 PID 发信号，默认通常是 SIGTERM；目标可捕获、忽略或延后响应，不保证一定正常退出 |
| 057 | `killall` | kill + all | Linux 常见实现按名称向匹配进程发信号；可能匹配多个进程，跨系统同名命令行为也可能不同 |
| 058 | `pkill` | process + kill 的助记 | 按名称等条件匹配并发信号；可先用 `pgrep -a -x app` 确认目标，`-f` 会扩大到完整命令行匹配 |
| 059 | `jobs / fg / bg` | jobs / foreground / background | `jobs -l` 看当前 Shell 作业，`fg %1` 转前台，`bg %1` 在后台继续暂停的作业；作业号不是 PID |
| 060 | `nohup` | no hangup | `nohup ./app > app.log 2>&1 &` 忽略 SIGHUP 并后台运行；后台由 `&` 实现，nohup 不保证能绕过系统的登录会话清理策略 |
| 061 | `watch` | watch，持续观察 | `watch -n 2 'free -h'` 每两秒重新运行；它是重复执行，不是实时监听内核事件 |
| 062 | `lsof` | list open files | `lsof -i :22` 查看相关网络文件，`lsof app.log` 查打开该文件的进程；信息完整度受权限限制 |

SIGKILL（`kill -9`）不能被捕获执行用户态清理，遇到不可中断内核等待也未必立即消失。通常先查状态、保存日志，再选择信号；结束进程不等于删除可执行文件。

## 08. 系统信息与电源

| 编号 | 命令 | 词源 / 助记 | 用途、常用写法与易错点 |
| :--- | :--- | :--- | :--- |
| 063 | `date` | date，日期 | `date '+%F %T %z'` 显示时间与时区；设置系统时间属于管理操作，错误时间可能影响 TLS 和日志定位 |
| 064 | `uname` | Unix name 的助记 | `uname -a` 查看内核等信息，`uname -m` 看架构；发行版信息另查 `/etc/os-release` |
| 065 | `hostname` | host name | 显示或设置主机名；临时设置不一定在重启后保留，持久配置由系统管理方案决定 |
| 066 | `uptime` | up time | 显示运行时长与 1/5/15 分钟平均负载；Linux load average 不只是 CPU 使用百分比，还涉及不可中断等待任务 |
| 067 | `free` | free，空闲 | `free -h` 查看内存与交换空间；估计还能运行多少程序时关注 available，不能只看 free 一列 |
| 068 | `who` | who，谁 | 查看登录会话记录；不是系统中所有用户的列表，也不保证所有类型的会话都被记录 |
| 069 | `w` | who 类信息的简短命名 | 显示登录用户、活动及系统负载，具体内容受会话记录和工具实现影响 |
| 070 | `shutdown` | shut down | `sudo shutdown -h now` 在当前 Debian 中请求关机，`-r` 请求重启，`-c` 可取消尚未执行的计划；SSH 会断开 |
| 071 | `reboot` | re + boot，重新引导 | `sudo reboot` 请求重启；它不会重新烧录系统，网络恢复后再重新连接 |

开发板关机后，SoC 停止运行不等于板上所有电源轨都已断电。等待关机完成后再拔电；在 WSL 中，Linux 内部的关机行为与 Windows 的 WSL 实例管理也不是同一件事。

## 09. 磁盘与文件系统

| 编号 | 命令 | 词源 / 助记 | 用途、常用写法与易错点 |
| :--- | :--- | :--- | :--- |
| 072 | `df` | disk free | `df -hT` 查看已挂载文件系统的容量和类型；不是物理磁盘所有分区的容量清单 |
| 073 | `du` | disk usage | `du -sh demo` 统计目录树已分配空间；稀疏文件、硬链接、权限和打开但已删除的文件都会影响它与 df 的比较 |
| 074 | `mount` | mount，挂接 | 将文件系统挂到目录树；无参数常可查看挂载信息，定位某路径也可用 `findmnt -T /userdata` |
| 075 | `umount` | unmount 的历史拼写 | `umount /mnt/demo` 卸载挂载点，不是删文件；当前目录或打开文件可能造成 busy |
| 076 | `lsblk` | list block devices | `lsblk -o NAME,SIZE,FSTYPE,MOUNTPOINTS,MODEL` 查看块设备和分区；编号不能直接当作 TF 卡或 eMMC 的身份 |
| 077 | `fdisk` | 常以 fixed disk 助记 | `sudo fdisk -l` 列出分区信息；交互模式可以修改分区表，写入前须核对目标 |
| 078 | `mkfs` | make filesystem | 创建文件系统，具体工具如 `mkfs.ext4`；格式化不是普通挂载，会改变目标上的文件系统数据 |
| 079 | `dd` | 历史名称；参数风格常与 IBM JCL 联系起来 | 按块复制或转换数据；`if=` 是输入，`of=` 是输出，输出可能被覆盖，不能把 disk destroyer 之类戏称当正式全称 |

先理解设备、分区、文件系统与挂载点四者的关系。当前泰山派的 `/` 与 `/userdata` 是不同挂载点，`/userdata` 空闲很多，并不意味着安装到 `/usr` 的软件就能自动使用那部分空间。

## 10. 压缩与归档

| 编号 | 命令 | 词源 / 助记 | 用途、常用写法与易错点 |
| :--- | :--- | :--- | :--- |
| 080 | `tar` | tape archive，磁带归档 | `tar -czf demo.tar.gz demo/` 归档并用 gzip 压缩；`tar -tf demo.tar.gz` 先查看内容，`tar -xzf` 解包；打包与压缩是不同步骤 |
| 081 | `zip` | ZIP 格式及工具名 | `zip -r demo.zip demo/` 将目录压缩归档；不必把名称硬拆成英文缩写 |
| 082 | `unzip` | un + zip | `unzip -l demo.zip` 查看清单，`unzip demo.zip -d unpacked` 解压到指定目录，留意已有同名文件 |
| 083 | `gzip` | GNU zip | `gzip -c app.log > app.log.gz` 输出压缩数据并保留输入；直接 `gzip app.log` 通常会用 `.gz` 替换原文件 |
| 084 | `gunzip` | gzip 的解压工具名 | `gunzip -c app.log.gz` 把解压结果输出到标准输出；直接解压文件通常会移除压缩版本 |

`.tar.gz` 通常表示 tar 归档再经 gzip 压缩，不能直接推断为 zstd；zstd 常见扩展名是 `.zst`。解压 SDK 前先查看文件清单、可用空间和厂商要求的目录位置。

## 11. 软件包与服务

| 编号 | 命令 | 词源 / 助记 | 用途、常用写法与易错点 |
| :--- | :--- | :--- | :--- |
| 085 | `apt / apt-get` | Advanced Package Tool | Debian/Ubuntu 包管理；`apt show nano` 查看信息，`sudo apt update` 更新索引，`sudo apt install nano` 安装；自动化脚本通常优先 apt-get 的稳定接口 |
| 086 | `yum` | Yellowdog Updater, Modified | RPM 系发行版包管理；`yum info 包名` 查信息，现代系统上的 yum 也可能由 DNF 兼容实现提供 |
| 087 | `dnf` | Dandified YUM | Fedora/RHEL 等的软件包管理工具；`dnf info 包名` 查询，本机 Debian 的基础学习无需安装它 |
| 088 | `dpkg` | Debian package | `dpkg -l` 查询安装记录，`dpkg -L 包名` 查文件；直接 `dpkg -i` 安装本地 deb 不会自动下载缺失依赖 |
| 089 | `rpm` | 历史为 Red Hat Package Manager，现用 RPM Package Manager | `rpm -qa` 查询安装包；rpm 管理包数据库，与 yum/dnf 的仓库依赖解析层次不同 |
| 090 | `systemctl` | system + control 的助记，ctl = control | `systemctl status ssh` 查状态；start 管当前启动，enable 管启动关联，`enable --now` 同时处理；需要 systemd 环境 |
| 091 | `service` | service，服务 | `service ssh status` 查询服务；常作为 SysV 脚本或系统服务的兼容入口，行为由发行版决定 |
| 092 | `cron` | 常追溯至表示时间的 chronos | 定时任务守护进程，某些系统程序名为 crond；不是打开一个终端就自动具备服务 |
| 093 | `crontab` | cron table | `crontab -l` 查看当前用户任务，`crontab -e` 编辑；通常是五个时间字段加命令，系统级任务文件还可能有用户字段 |

APT 的 `update` 不等于升级已安装软件，`upgrade` 才处理相应升级。systemd 的 `enabled` 不等于 `active`；修改 unit 后用 `daemon-reload`，修改应用自身配置则按服务支持方式 reload/restart。

cron 的 PATH、工作目录和环境通常与交互式终端不同，脚本使用明确路径并记录日志。是否存在 NetworkManager、cron、OpenSSH 等服务，要以当前镜像为准。

## 12. 网络与远程

| 编号 | 命令 | 词源 / 助记 | 用途、常用写法与易错点 |
| :--- | :--- | :--- | :--- |
| 094 | `ping` | 原始命名来自声纳 ping 的声音；Packet InterNet Groper 是后来的展开 | `ping -c 4 127.0.0.1` 测试 ICMP 回应；失败可能是过滤，不直接证明目标服务不可用 |
| 095 | `ifconfig` | interface configuration | `ifconfig -a` 查看接口，来自传统 net-tools；当前优先学习 iproute2 的 `ip` |
| 096 | `ip` | Internet Protocol | `ip -br addr` 看地址，`ip link` 看接口，`ip route` 看路由；临时修改不会自动成为重启后配置 |
| 097 | `netstat` | network statistics | `netstat -lnt` 查看 TCP 监听信息，是传统工具；连接排查常可用 ss |
| 098 | `ss` | socket statistics | `ss -lntp` 查看 TCP 监听及进程，`-u` 涉及 UDP；查看其他用户的进程信息可能需要权限 |
| 099 | `nmcli` | NetworkManager command-line interface | `nmcli device status` 看设备，`nmcli connection show` 看连接配置；unmanaged 表示 NM 未管理，不等于硬件损坏 |
| 100 | `iptables` | IP tables | `sudo iptables -S` 查看当前相应表的规则；系统可能使用 nft 后端或原生 nftables，不能只查一个工具便认定没有过滤规则 |
| 101 | `ufw` | uncomplicated firewall | `sudo ufw status verbose` 查状态；它是防火墙管理前端，开放规则与启用防火墙是不同操作 |
| 102 | `traceroute` | trace + route | `traceroute 主机名` 探测路径上的响应；中间跳不响应不等于那里一定断网，路径也可能变化 |
| 103 | `telnet` | 常按 Teletype Network 助记 | 传统明文远程终端协议/客户端，也可尝试 TCP 端口连接；不适合传送账户密码，端口连通不代表应用处理正常 |
| 104 | `dig` | Domain Information Groper | `dig example.com A` 查询 DNS A 记录；注意实际查询的服务器、响应状态和 TTL |
| 105 | `nslookup` | name server lookup | `nslookup example.com` 查询 DNS；解析成功与目标主机、业务端口可达是不同阶段 |
| 106 | `nmap` | Network Mapper | `nmap -p 22 127.0.0.1` 检查本机指定端口；使用时选自己的设备或获准检查的目标，结果受探测方式与过滤策略影响 |
| 107 | `nc` | netcat，network + cat | 常见实现用 `nc -vz 127.0.0.1 22` 检查 TCP 端口；OpenBSD、传统和 BusyBox 版本的参数不完全相同 |
| 108 | `ssh` | Secure Shell | `ssh tspi@<board-ip>` 加密登录；`-p` 指定端口，`-v` 查看连接过程；首次主机密钥指纹应与目标设备核对 |
| 109 | `scp` | secure copy | `scp hello.c tspi@<board-ip>:/userdata/workspace/` 复制文件；端口参数是大写 `-P`，现代 OpenSSH 默认使用 SFTP 协议传输 |
| 110 | `ssh-keygen` | SSH key generator | `ssh-keygen -t ed25519` 生成密钥，`-l -f 公钥文件` 查看指纹；生成时核对路径，不覆盖已有密钥，私钥口令与登录密码不同 |
| 111 | `wget` | web + get | `wget -O page.html https://example.com/` 下载并指定文件名，`-c` 尝试续传；续传是否可用还取决于服务器 |
| 112 | `curl` | cURL；可按 client + URL 助记，也有 see URL 的读法 | `curl -I https://example.com/` 请求响应头，`-L` 跟随重定向，`-o` 保存结果；默认退出成功不代表 HTTP 状态码一定为 2xx |
| 113 | `rsync` | remote synchronization | `rsync -av --dry-run demo/ backup/` 预览同步；源目录末尾 `/` 影响复制内容还是目录本身，`--delete` 会删除目标端多余项 |

`<board-ip>` 是需要替换的占位符，不连同尖括号输入终端。先分清网卡、IP、路由、DNS、服务监听与认证；SSH 的 `Permission denied` 与连接超时不是同一层问题。

`rsync` 能减少重复传输，但“只传差异块”受本地/远程模式和参数影响。TLS 请求失败时核对时间、证书、主机名与网络，不把关闭证书验证当作常规修复。

## 13. 硬件、日志与校验

| 编号 | 命令 | 词源 / 助记 | 用途、常用写法与易错点 |
| :--- | :--- | :--- | :--- |
| 114 | `lscpu` | list CPU | 查看架构、CPU 数量与拓扑；在 WSL、虚拟机或容器中看到的是当前环境暴露的信息 |
| 115 | `dmesg` | 常按 diagnostic messages 助记 | `dmesg -T` 查看内核环形日志；可能受权限限制，日志可能覆盖，转换的墙上时间也有局限 |
| 116 | `journalctl` | journal + control | `journalctl -u ssh -b -n 30 --no-pager` 查本次启动的 SSH 日志；`-f` 跟随，能否查历史启动取决于日志保留配置 |
| 117 | `md5sum` | Message-Digest Algorithm 5 + checksum | `md5sum sdk.tar.gz` 计算摘要，`md5sum -c checksums.md5` 按清单核验；用于意外损坏检查，不能证明固件来源可信 |

发布方提供 SHA-256 时使用 `sha256sum` 对应核验；无论哪种普通摘要，期望值都需要可靠来源。固件真实性通常还需要签名与可信密钥，不能只凭“MD5 相同”认定安全。

## 14. 数据库

| 编号 | 命令 | 词源 / 助记 | 用途、常用写法与易错点 |
| :--- | :--- | :--- | :--- |
| 118 | `psql` | PostgreSQL 的交互终端名，可按 PostgreSQL + SQL 助记 | `psql --version` 查看客户端版本；连接数据库后 `\q` 退出，客户端存在不代表服务端已运行 |
| 119 | `mysql` | MySQL 产品及客户端名，不是通用的“shell”缩写 | `mysql --version` 查版本，连接时 `-p` 可提示输入密码；客户端可能来自 MySQL 或兼容实现，不能当作 Linux 系统账号登录 |

SQL 是 Structured Query Language。当前基础学习先认识这两个客户端，等网关项目确实需要数据库时再补连接、权限、SQL 与持久化，不必为了背词源同时安装两套数据库。

## 遇到不认识的命令怎么查

```bash
type cd
command -v gcc
help cd
whatis ls
man 1 ls
apropos 'list files'
info coreutils
```

`type`、`command -v` 帮助确认 Shell 实际如何解析名字，Bash 的 `help` 用于内建命令；`whatis` / `apropos` 依赖手册索引，`info` 需要对应程序与文档。没有查到手册不等于命令不存在，`man` 的 NAME 段也不一定提供名称的历史出处。

查阅时先读用途和 SYNOPSIS，再看准备使用的选项、返回值与示例。`--help` 是常见约定，不保证每个内建命令或 BusyBox applet 都支持同样形式。

## 动手练习与自查

在自己的工作目录逐项练习，记录命令、结果与解释：

- [ ] 建立 `demo/` 目录，创建、复制、重命名一个文本文件，再分别用相对路径和绝对路径访问。
- [ ] 用 `less`、`head`、`tail`、`grep` 查同一份日志，说清它们各自读取了什么。
- [ ] 对一份测试文件查看 `id`、`ls -l`、`stat`，再解释所有者、组和权限位。
- [ ] 用 `ps`、`top`、`free -h` 观察状态，区分 PID、CPU 占用、负载与可用内存。
- [ ] 比较 `df -hT`、`du -sh`、`lsblk` 输出，解释为什么看到的容量可能不同。
- [ ] 用 `ip`、`ss`、`systemctl`、`journalctl` 分层检查自己的 SSH 连接与服务。
- [ ] 打包并解压一个测试目录，验证文件内容；对下载的 SDK 使用发布方提供的摘要清单核验。

关联阅读：[Linux 使用基础与知识地图](linux-foundations.md)、[泰山派上板实战](taishan-pi.md)、[Linux 入门面试题](../embedded-interview/linux-basics.md)。

整理来源：本地 `linux-command-etymology.html`；原 HTML 标注参考 CSDN 作者 `wzk4869` 的文章 `132855372`。本页保留其命令范围与分类，对重复编号、部分词源说法和命令行为做了校正。
