# 更早年份与对照卷（2008–2024）

[返回专区](/embedded-interview/index.md) | [海康笔试总分析](/embedded-interview/hikvision-written-test.md) | [2019 多媒体卷](/embedded-interview/hikvision-2019-multimedia.md)

这一页收录**年份更早、或岗位不同**的海康威视笔试材料。它们的作用是证明"哪些考点是长期主干"，以及给出**跨岗位差异**。每题都标注了来源与核对状态；**原文缺的部分一律不补**。

## 一、2013 年校园招聘卷

来源：<https://blog.csdn.net/fguihbfg/article/details/83922705>《2013年海康威视校园招聘笔试题》（599 阅读，转载无作者署名）。正文第 3 题起被 CSDN VIP 墙截断，**只拿到 3 题**。

### E13-Q1｜24 点（10、10、4、4） :id=e13q1
**题（原文）：** 10、10、4、4 四个数，怎么算出 24 点？
**答案（原文）：** `(10*10-4)/4 = 24`
**【自核】：** 100 − 4 = 96，96 ÷ 4 = 24 ✓。要点是**必须用到除法**，所以中间结果不是 24 的整数倍——这类题靠"先把目标写成 96/4、72/3 之类的分数形式"来倒推，比硬试快。
**意义：** 海康早期卷里有**智力/数学题**，2014 DSP 卷也有（见下方 20 瓶药）。近年嵌入式软件卷未见此类题，但笔试遇到不必慌。

### E13-Q2｜`#pragma pack` 与空类/虚函数的 `sizeof` :id=e13q2
**题（原文）：** 下列表达式在 32 位机器编译环境下的值（）。
```cpp
class A{
    };
class B{
    public: B(); virtual ~B();};
class C{
    private:#pragma pack(4)
        int i; short j; float k; char l[64]; long m; char *p;
    #pragma pack()};
class D{
    private:#pragma pack(1)
        int i; short j; float k; char l[64]; long m; char *p;
    #pragma pack()};
int main(void){
    printf("%d\n",sizeof(A));
    printf("%d\n",sizeof(B));
    printf("%d\n",sizeof(C));
    printf("%d\n",sizeof(D));
    return 0;}
```
**选项（原文）：** A、1、4、84、82　B、4、4、82、84　C、4、4、84、82　D、1、4、82、82
**答案：**【自核】A（`1、4、84、82`）。原文 KEY 在 VIP 墙内未取得，以下为独立推算。
**推导（32 位、4 字节指针）：**

| 类 | 结果 | 依据 |
| :--- | :--- | :--- |
| `A`（空类） | **1** | C++ 要求每个对象有可区分的地址，空类 `sizeof` 为 1，**不是 0** |
| `B`（有虚析构） | **4** | 多态类含虚表指针（32 位下 4 字节）；仅一个 `int` 成员的空类才是 4 |
| `C`（`pack(4)`） | **84** | `i`@0-3、`j`@4-5、`k` 需 4 对齐 → @8-11、`l[64]`@12-75、`m`@76-79、`p`@80-83；整体对齐 4 → 84 |
| `D`（`pack(1)`） | **82** | 逐字节紧排：`i`@0-3、`j`@4-5、`k`@6-9、`l`@10-73、`m`@74-77、`p`@78-81 → 82 |

**这就是本专区 [C10 结构体为什么有填充](/embedded-interview/c-basics.md#c10) 的完整计算版**，同时也是"内存对齐能不能直接发到串口"的现实答案：**对齐方式一变，同一份结构体的字节布局就不同**，跨设备/跨版本传数据必须显式 `pack(1)` 或手工序列化。见 [结构体专题](/c-language/struct.md)、[字符串与缓冲区](/c-language/strings-buffers.md)。

### E13-Q3｜`struct info_t` + `union info_u` 的运行结果 :id=e13q3
**题（原文，截断）：**
```c
#pragma pack(4)
struct info_t{
    unsigned char version; unsigned char padding; unsigned char extension;
    unsigned char count; unsigned char marker; unsigned char payload;
    unsigned short sequence; unsigned int timestamp; unsigned int ssrc;
};
union info_u{ unsigned ...
```
**答案：** 未取得——原文在 `union info_u` 定义处被 VIP 墙截断，**题面不完整，不做推测**。
**【自核】可核对的部分：** `struct info_t` 在 `pack(4)` 下：6 个 `unsigned char`（@0-5）→ `sequence` 需 2 对齐 @6-7 → 填充到 8 → `timestamp`@8-11 → `ssrc`@12-15 → `sizeof` = **16**。这类题的常规问法是"用 union 覆盖 struct 来读原始字节"，从而考**字节序与共享内存视图**。关联 [C10](/embedded-interview/c-basics.md#c10)。

## 二、未标年份的"海康嵌入式笔试题"（4 题问答，含答案）

来源：<https://blog.csdn.net/qq_37951246/article/details/82695260>《嵌入式笔试题（答案有待讨论）》，作者 ALIX阿利克斯，3.1k 阅读，发布于 2018-09-13。正文第一行写明"海康嵌入式笔试题"，但**作者未标注年份/届次**。Q4 的实现代码在函数签名后被抓取长度上限截断。

### EN-Q1｜TCP/IP 分几层？FTP 在哪一层？ :id=enq1
**答案（原文）：** 「可以分为 物理层，数据链路层，网络层，传输层，应用层」；「再回过头来看，ftp 是用 tcp 写的一个文件传输协议，明显就是在应用层了」。
**原文还给了 OSI 各层协议清单**（摘要）：应用层（Telnet、FTP、HTTP、SMTP、POP3、SNMP、DNS）／传输层（TCP、UDP）／网络层（IP、ARP、RARP、ICMP、IGMP、BOOTP）／数据链路层（HDLC、SLIP、PPP、802.2，网桥与交换机在此层）／物理层（中继器、集线器）。
**注意：** 原文答"五层"，而海康 2014 技术支持卷的口径是"TCP/IP 四层 + OSI 七层"都要会说。**面试时先问对方按哪个模型**，再报层名与协议归属。关联 [N02](/embedded-interview/network-iot.md#n02)、真题 [P7-4 协议分层归属](/embedded-interview/hikvision-written-test.md#p7q4)。

### EN-Q2｜`htons` / `htonl` / `ntohs` / `ntohl` 的作用 :id=enq2
**答案（原文）：** 「htons：把短整型的主机字节顺序转变为网络字节顺序，其它依次类推；htons 一般用来转变端口，htonl 一般用来转 IP；网络字节顺序是先高位字节，再低位字节；主机字节顺序则视 CPU 而定」。
**【自核】记忆法：** `h`→host、`n`→network，后缀 `s`=short（2 字节，给端口）、`l`=long（4 字节，给 IPv4 地址）。原文另外用 `inet_addr` / `inet_network` / `inet_aton` 对 `"255.255.255.255"` 的处理差异举例，并提醒 **`inet_addr` 对广播地址会返回 −1 而无法区分错误**，这是 `inet_aton` 存在的原因——面试常追问这一点。关联 [类型与转换](/c-language/types-and-conversions.md)。

### EN-Q3｜`static` 函数与普通函数的区别 :id=enq3
**答案（原文，三点结构）：**
1. **全局静态变量**：在静态存储区，未初始化自动置 0，作用域限于本文件（从定义处到文件结尾）；好处是不会被其他文件访问修改，且其他文件可用同名变量而不冲突。
2. **局部静态变量**：也在静态存储区；`static` 把局部变量从**栈**改存到静态存储区，离开作用域不销毁、驻留到程序结束，只是不能再访问。
3. **静态函数**：返回类型前加 `static`；函数默认是 `extern`，静态函数只在本文件可见、不能被其他文件使用。

原文补充了 `static` 的三段历史含义：C 里表示"退出块后仍存在"与"不能被其他文件访问"，C++ 又增加"属于类而非属于某个对象"。原文结论：**「静态的东西就是只在本文件中可见，而且在本文件中保持，它只初始化一次，存在静态存储区中」**。关联 [C04](/embedded-interview/c-basics.md#c04)、[存储期与模块化](/c-language/storage-modules.md)。

### EN-Q4｜手写内存复制函数 :id=enq4
**题（原文）：** 请实现内存复制函数 `void memcpy(void *dst, void *src, int size)`？
**答案：** 原文只给出实现所用的函数签名 `void *MyMemCopy(void *dest, const void *src, size_t count)`，**函数体在抓取中被截断，未取得**。
**【自核】需要能默写的版本（含重叠处理方向）：**

```c
void *MyMemCopy(void *dest, const void *src, size_t count)
{
    char *d = (char *)dest;
    const char *s = (const char *)src;

    if (d <= s || s + count <= d) {      /* 无重叠，或目标在源之前 */
        for (size_t i = 0; i < count; i++)
            d[i] = s[i];
    } else {                             /* 重叠且目标在后：倒着拷 */
        for (size_t i = count; i > 0; i--)
            d[i - 1] = s[i - 1];
    }
    return dest;
}
```
**要点：** ① 返回 `void *` 以支持链式调用；② `const` 修饰源；③ **重叠时必须从高地址往低地址拷**，否则会覆盖掉还没读的源数据（这正是 `memmove` 的做法，也是 [P1-Q03](/embedded-interview/hikvision-written-test.md#p1q03) 与 2023 届简答 [P3-2](/embedded-interview/hikvision-written-test.md#p3q2) 的核心）；④ 面试追问会问"为什么不用 `int size` 而用 `size_t`"（负数与截断）。

## 三、2014 届 DSP/嵌入式卷（考后考点清单，8 题 + 附加题）

来源：<https://blog.csdn.net/yangwenjun2017/article/details/20468053>，作者 wendale309，8.3k 阅读，发布于 2014-03-04。**性质是考后回忆的"考点清单"**：每题只有"考察××"一句话，除附加题外**没有题面、没有选项、没有答案**。原文题号从 5 直接跳到 7（缺第 6 题，非抓取丢字）。

| 条目 | 原文记载 | 怎么准备 |
| :--- | :--- | :--- |
| 1 | 考察字节对齐 | 见 [E13-Q2](#e13q2) 与 [C10](/embedded-interview/c-basics.md#c10) |
| 2 | SoC 芯片的相关设计（作者自述"不会"） | 了解 CPU/总线（AMBA）/存储控制器/外设 IP/地址划分/时钟域与复位域即可，软件岗一般不深挖 |
| 3 | 字符串反转 | 见模拟卷 [S23](/embedded-interview/hikvision-mock-paper.md)；双指针原地交换 |
| 4 | 测试驱动编程的概念、步骤、优点、缺点 | 【自核】红→绿→重构；优点是需求可执行、自带回归、促进低耦合；缺点是前期成本高、不利于探索性原型、测不到性能与并发问题 |
| 5 | TCP 与 UDP 的区别 + 应用举例 + 画出 TCP 释放连接的四次挥手图（原文注："没画出来"） | 见 [N02](/embedded-interview/network-iot.md#n02)、真题 [P7-7](/embedded-interview/hikvision-written-test.md#p7q7)；**挥手图要能默画**：`FIN`→`ACK`→`FIN`→`ACK`，主动关闭方进 `TIME_WAIT`（2MSL） |
| 7 | `volatile` 关键字的使用；用 `volatile` 分别定义整型和指针；给一段代码问风险 | 见下方【自核】代码分析 |
| 8 | 解释 `n & (n-1) == 0` 是用来判断什么 | 见下方【自核】 |
| 附加题 | 20 瓶药称一次找坏瓶（**原文含答案**） | 见下方 |

### E14-Q7｜自旋等待 `flag` 的代码风险 :id=e14q7
**原文代码：**
```c
int flag = 0;

void doSomething()
{
  start:
    if(flag) goto start;
}
```
**【自核】风险：** `flag` 会被另一个执行流（中断服务程序或其他线程）修改，但它**不是 `volatile`**——编译器可能把 `flag` 缓存进寄存器反复判断同一个值，导致这个循环永不退出（或永不等待）。正确做法：`volatile int flag;`，多核还需考虑可见性与顺序（原子操作/内存屏障），并且这个"等待外部事件"的结构本身应该用信号量或事件标志，而不是忙等。关联 [C05](/embedded-interview/c-basics.md#c05)、[中断、并发与 volatile](/c-language/isr-concurrency.md)、[R10](/embedded-interview/rtos.md#r10)。
**原文要求的两种 `volatile` 定义写法（【自核】示例）：**

```c
volatile int flag;              /* volatile 整型 */
volatile int *p;                /* 指向 volatile int 的指针（值可变，指针可变） */
int * volatile q;               /* volatile 指针本身（常用于 ISR 换缓冲区） */
volatile int * volatile r;      /* 两者都 volatile */
```

### E14-Q8｜`n & (n-1) == 0` 判断什么 :id=e14q8
**【自核】答案：** 判断 `n` 是否为 **2 的幂**——`n & (n-1)` 会抹掉最低位的 1，结果为 0 说明二进制里只有一个 1。
**两个必说的坑：** ① 优先级：`==` 高于 `&`，原式实际按 `n & ((n-1) == 0)` 计算，必须写成 `(n & (n-1)) == 0`；② `n = 0` 时 `0 & (-1) == 0` 也成立，所以严格判定要写成 `n != 0 && (n & (n-1)) == 0`。关联 [C09](/embedded-interview/c-basics.md#c09)、[位运算与寄存器操作](/c-language/bitwise-registers.md)。

### E14-Q9｜附加题：20 瓶药只称一次找出坏瓶 :id=e14q9
**题（原文）：** 有二十瓶药，其中 19 瓶的药品是 1g/粒，一瓶有问题，是 1.1g/粒，有一个非常精准的天平，只称量 1 次，找出有问题的那瓶。
**答案（原文）：** 「对 20 瓶编号 1–20，第 i 瓶取出 i 粒，称量，多出的重量（g）乘以 10 即可得到有问题的瓶编号」。
**【自核】验算：** 共取 1+2+…+20 = 210 粒，全合格应重 210 g；实际重量 = 210 + 0.1k（k 为坏瓶编号），故 k = (实际 − 210) × 10 ✓。
**方法名：用"编号即权重"把一次测量编码成多个候选**——同族题（称金币、坏电池）都靠这个套路。

## 四、2024 届数字逻辑设计岗（IC 方向，对照用）

来源：<https://blog.csdn.net/qq_43045275/article/details/130630054>，作者"在路上-正出发"，1.16 万阅读。**笔试实际发生在 2023-05-11（面向 2024 届实习批）**，岗位是**数字逻辑设计工程师（杭州），不是嵌入式软件岗**。全文被作者的收费专栏（¥19.90 / ¥99.00）挡住，免费部分只有 2 道单选题；付费区关键词显示还有形式验证、网表验证、乘法器、多周期约束、SRAM、存储层次、AMBA、指令集架构等题，**题面未取得**。

### E24-Q1｜Verilog 哪个不是分支语句 :id=e24q1
**题（原文）：** 在 Verilog 中，下列语句哪个不是分支语句？（3 分）
**选项（原文）：** A. case　B. if-else　C. casez　D. repeat
**答案（原文）：** D（作者原话"一眼见，D"）。
**【自核】：** `case`/`if-else`/`casez`（及 `casex`）都是分支；`repeat` 是**循环**语句。

### E24-Q2｜`reg [0:31]` 下 `hik[0:+8]` 指什么 :id=e24q2
**题（原文）：** 对于 `reg[0:31]`，表达式 `hik[0:+8]` 指的是？（3 分）
**答案：** 原文未给文字答案（解析是两张 IEEE 标准截图，图中文字未取得）。
**【自核】：** `reg [0:31] hik;` 是**升序声明**（索引 0 为最高位）。`[base +: width]` 是 indexed part-select：从 `base=0` 起、沿**索引增大方向**取 8 位，等价于 `hik[0:7]`。要点：`+:` 向索引增大方向、`-:` 向索引减小方向；`base` 可为变量、`width` 必须是常量——这正是可变起点切片必须用 part-select 语法的原因。

## 五、没能取得原文的卷（诚实清单）

以下材料**确实存在**，但本环境抓不到正文（CSDN 概率性 HTTP 521 反复重试仍失败）。**不据此编造题干**，需要时人工打开补齐：

| 卷 | 来源 | 卡在哪 |
| :--- | :--- | :--- |
| 2008 嵌入式软件工程师 A 卷（`volatile`、TCP/IP 分层、`hton*`、`static`） | <https://blog.csdn.net/qq_26646141/article/details/56677794> | HTTP 521，多次重试失败；据第三方摘要其考点与本页 [EN-Q1/Q3](#enq1) 高度重合 |
| 2018 应用开发方向（二级指针改错、DP「和尚挑水」、地址转换函数、野指针） | <https://blog.csdn.net/qq_21148843/article/details/79940970> | HTTP 521，多次重试失败（该文同时含朗国/中科创达/深信服等公司题） |
| 2019 海康威视 C++ 岗完整面经（笔试 + 一面 + 二面 + 三面 + Offer） | <https://jasonlee.blog.csdn.net/article/details/84878391> | 仅在相关推荐里读到摘要「海康的提前批挺早的，8 月份就开始了……2019 校招整体难度不是很高」，正文未取得 |
| 2014 视音频算法工程师笔试、2017 视音频算法笔试题、海康往年硬件笔试题（模电数电） | CSDN 下载频道（`download.csdn.net`，需积分） | 需登录/付费，未获取 |

## 六、这些老卷子说明了什么

1. **主干考点十年没变**：TCP/IP 分层与协议归属、字节序转换、`static`/`volatile`、内存对齐、手写 `memcpy`/字符串反转、TCP 与 UDP 及挥手图——从 2008、2013、2014 一直出现在 2023、2024 卷里。**先把这些吃透，比追新题划算。**
2. **早期卷爱考"业务与智力题"**（24 点、20 瓶药、视频传输方式），近年软件卷更多是代码求值与 OS 概念。
3. **早期卷以问答/画图为主，近年以选择题为主**——意味着现在要练"读代码给数"，但也别忘了**能画图、能口述协议过程**（面试仍在用）。
4. **不同岗位差异极大**：技术支持卷全是网络与英语翻译；数字逻辑卷全是 Verilog；DSP/多媒体卷有存储与音频计算；BSP/应用卷是 C 语言与 Linux。**投哪个岗就重点看哪个岗的卷。**
