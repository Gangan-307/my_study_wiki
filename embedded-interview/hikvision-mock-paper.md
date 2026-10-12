# 海康风格模拟卷（自编，非真题）

[返回专区](/embedded-interview/index.md) | [海康真题整理](/embedded-interview/hikvision-written-test.md) | [复习与自测表](/embedded-interview/review-plan.md)

> **这一卷是自编的**，题型结构仿照有据可查的 2023 届提前批（单选 15 + 多选 5 + 简答 2 + 编程 1~2），**每个考点都来自真题卷实际出现过的方向**（见[考点榜](/embedded-interview/hikvision-written-test.md#kaodianbang)），但题目本身不是真题。
>
> 建议用法：60 分钟闭卷。编程题写在**纯文本框式的环境**里——不要用 IDE 补全、不要调试，模拟海康"给个 txt 写代码"的真实作答条件。

## 一、单选题（每题 2 分，共 30 分）

**S1.** 32 位平台下：

```c
unsigned char c = 250;
c += 10;
printf("%d\n", c);
```

输出是？　A. 260　B. 4　C. 254　D. 未定义

**S2.** 下面程序的输出是？

```c
#define SQ(x) x*x
int a = SQ(2 + 3);
```

A. 25　B. 11　C. 10　D. 编译错误

**S3.** `int i = 2;` 执行下面的 switch 后 `i` 的值是？

```c
switch (i) {
case 2: i++;
case 3: i += 2; break;
case 4: i += 4;
}
```

A. 3　B. 5　C. 9　D. 8

**S4.** 32 位 MCU 上：

```c
short arr[10];
short *p = arr;
```

`(char*)p + 3` 与 `p + 3` 各偏移多少**字节**？　A. 3、3　B. 3、6　C. 6、6　D. 3、12

**S5.** 32 位平台上：

```c
char *s = "hello";
char t[] = "hello";
```

`sizeof(s)`、`sizeof(t)`、`strlen(s)` 分别是？　A. 4、6、5　B. 4、5、5　C. 6、6、5　D. 4、6、6

**S6.** 32 位平台，默认对齐：

```c
struct S { char a; int b; short c; };
```

`sizeof(struct S)` 是？　A. 7　B. 8　C. 12　D. 11

**S7.** 要把 32 位变量 `x` 的 bit[7:4] 清零、其余位不变，正确的是？　A. `x &= 0xFFFFFF0F;`　B. `x &= ~0xF0;`　C. `x |= 0xF0;`　D. `x ^= 0xF0;`

**S8.** 若 `int v;`，下面哪一句**编译报错**（C 语言）？　A. `const int *p = &v;`　B. `int *const p = &v; p = 0;`　C. `int *const p = &v; *p = 1;`　D. `const int *p = &v; p++;`

**S9.** 64 位 Linux（LP64）上 `long`、`int *`、`short` 的大小（字节）是？　A. 4、4、2　B. 8、8、2　C. 8、4、2　D. 4、8、2

**S10.** 关于进程与线程，说法**错误**的是？　A. 线程共享所属进程的地址空间　B. 进程是资源分配的基本单位　C. 线程拥有独立地址空间，崩溃不影响其他线程　D. 线程切换通常比进程切换开销小

**S11.** 关于互斥锁与信号量，说法**正确**的是？　A. 信号量的加锁和解锁必须由同一线程完成　B. 互斥锁用于线程间同步，信号量用于互斥　C. 互斥锁只能取 0/1，信号量可为非负整数　D. 互斥锁可以限制访问者的访问顺序

**S12.** 在当前目录及子目录的 `.c` 文件里查找包含 `HAL_UART` 的行，应该用？　A. `find . -name "*.c" | grep HAL_UART`　B. `grep -rn "HAL_UART" --include="*.c" .`　C. `cat *.c | find HAL_UART`　D. `ls -R | grep HAL_UART`

**S13.** `volatile int i;`，在中断与主循环共享且中断只写、主循环只读单字节的场景下，`volatile` **不能**保证的是？　A. 编译器不把该变量缓存在寄存器　B. 该变量的读改写是原子的　C. 每次访问都真实发生　D. 编译器不会删除"看似无效"的读取

**S14.** TCP、UDP、ICMP、ARP 依次属于 TCP/IP 模型的哪层？　A. 传输、传输、网络、网络　B. 传输、网络、网络、链路　C. 网络、传输、网络、链路　D. 传输、传输、传输、网络

**S15.** `strlen("abc\0def")` 的值是？　A. 7　B. 3　C. 4　D. 未定义

## 二、多选题（每题 3 分，共 15 分）

**S16.** 可用于 Linux 中断"下半部"处理的机制有？　A. tasklet　B. 工作队列　C. 软中断　D. 双向链表

**S17.** 关于链表与数组，正确的有？　A. 链表插入删除无需移动其他元素　B. 数组支持 O(1) 随机访问　C. 链表节点物理地址一定连续　D. 数组扩容需要重新分配并拷贝

**S18.** 宏与函数相比，正确的说法有？　A. 宏不检查参数类型　B. 宏参数可能被求值多次，带来副作用　C. 宏在预处理阶段展开，不进符号表、难调试　D. 用 `do { } while (0)` 包裹多条语句的宏可以让它在 if/else 中安全使用

**S19.** 关于 TCP，正确的有？　A. 面向字节流，不保留应用层消息边界　B. 通过确认与重传保证可靠交付　C. 提供广播和多播服务　D. 三次握手中服务器会进入 SYN_RECV 状态

**S20.** 关于 C 语言 `static`，正确的有？　A. 文件内 `static` 全局变量具有内部链接　B. 函数内 `static` 局部变量只初始化一次　C. `static` 变量存放在栈上　D. `static` 能保证多线程访问安全

## 三、简答题（每题 10 分，共 20 分）

**S21.** 栈与堆有什么区别？各自适合什么场景？（至少 4 点）

**S22.** 如果把判断条件中的 `==` 误写成 `=`，可能出现哪些问题？如何避免？

## 四、编程题（共 35 分）

**S23.（15 分）** 手写函数 `void reverse_str(char *s)`，原地反转字符串。要求：处理 `NULL` 与空串；不借助额外数组；写出你会测试的 4 个用例。

**S24.（20 分）** 用单链表实现队列的入队与出队：

```c
typedef struct QNode {
    struct QNode *next;
    int data;
} QNode;

typedef struct {
    QNode *head;   /* 出队端 */
    QNode *tail;   /* 入队端 */
} Queue;
```

实现 `int queue_push(Queue *q, int v);` 与 `int queue_pop(Queue *q, int *out);`。要求：处理空队列、只有一个节点、失败路径；说明线程不安全时的加锁位置。

---

## 参考答案与解析

**S1 → B。** `unsigned char` 回绕：250+10=260，260 mod 256 = 4。看 [C08](/embedded-interview/c-basics.md#c08)、[类型与转换](/c-language/types-and-conversions.md)。

**S2 → B。** 文本替换：`2 + 3*2 + 3` = 11。宏参数必须加括号。看 [C11](/embedded-interview/c-basics.md#c11)。真题同款：P1-Q13/Q18。

**S3 → B。** 命中 `case 2`：i=3；无 break 继续 `case 3`：i += 2 → 5；遇 `break` 停止。看 [运算符与语句](/c-language/operators.md)。真题同款：P1-Q11。

**S4 → B。** `(char*)p` 强转成字节指针再 +3 → 3 字节；`p + 3` 按 `short*` 步长 → 3×2=6 字节。看 [C01](/embedded-interview/c-basics.md#c01)。真题同款：P1-Q15。

**S5 → A。** 32 位下指针 4 字节；`t` 是数组，占 "hello"+`\0` 共 6 字节；`strlen` 不含 `\0` → 5。看 [C02](/embedded-interview/c-basics.md#c02)。真题同款：P1-Q20。

**S6 → C。** `char a` 偏移 0；`int b` 需 4 字节对齐 → padding 3；`short c` 偏移 8~9；整体对齐到最大成员 4 → 补到 12。看 [C10](/embedded-interview/c-basics.md#c10)、[结构体专题](/c-language/struct.md)。

**S7 → B。** `x &= ~0xF0` 等价于把 bit[7:4] 清 0；A 的掩码写死了 32 位低 8 位之外全 1，也"碰巧"对，但可读性差且依赖字长；C 是置位、D 是翻转。看 [C09](/embedded-interview/c-basics.md#c09)。真题同款：P1-Q17。

**S8 → B。** `p = 0` 试图修改 `const` 指针自身的指向，报错；A/D 修改指向合法；C 修改目标合法。看 [C03](/embedded-interview/c-basics.md#c03)。

**S9 → B。** LP64：`long` 8、指针 8、`short` 2。**必须先说平台**；Windows x64 下 `long` 是 4。看 [C01](/embedded-interview/c-basics.md#c01)。真题同款：P4-4、2019 应用岗"64 位机指针字节数"。

**S10 → C。** 线程没有独立地址空间，只有独立的栈和寄存器上下文。看 [L01](/embedded-interview/linux-basics.md#l01)。真题同款：P1-Q10、P3-1。

**S11 → C。** A 是互斥锁的属性；B 说法反了；D 是同步的职责、互斥锁做不到。看 [R03](/embedded-interview/rtos.md#r03)。真题同款：P1-Q06。

**S12 → B。** 按文件内容搜用 `grep`，`-r` 递归、`--include` 限定文件类型。A 把 find 的结果当文本过滤，语义错。看 [基础命令速查](/embedded-linux/basic-commands.md)。真题同款：P1-Q07。

**S13 → B。** `volatile` 只保证可见性语义，不保证原子性，`i++` 这种读改写仍可能被打断。看 [C05](/embedded-interview/c-basics.md#c05)、[ISR 与并发](/c-language/isr-concurrency.md)。

**S14 → A。** TCP/UDP 在传输层，ICMP/ARP 在网络层（ARP 归属有教材差异，海康 2014 卷口径也放网络层）。看 [N02](/embedded-interview/network-iot.md#n02)、真题 P7-4。

**S15 → B。** `strlen` 停在第一个 `\0`。看 [C02](/embedded-interview/c-basics.md#c02)。

**S16 → ABC。** 与真题 P1-Q21 相同的三件套；"双向链表"是数据结构不是下半部机制。看 [R05](/embedded-interview/rtos.md#r05)。

**S17 → ABD。** 链表节点由 malloc 分散分配，物理地址不保证连续。看 [C01](/embedded-interview/c-basics.md#c01)。真题同款：P1-Q23。

**S18 → ABCD。** 四条都是宏的经典边界。看 [C11](/embedded-interview/c-basics.md#c11)、[预处理、编译与链接](/c-language/preprocess-build-link.md)。

**S19 → ABD。** TCP 不支持广播/多播（UDP 才支持）；无消息边界即"粘包"问题。看 [N02](/embedded-interview/network-iot.md#n02)、[N03](/embedded-interview/network-iot.md#n03)、真题 P7-7。

**S20 → AB。** `static` 变量在静态存储区（C 错）；它不提供任何线程安全保证（D 错）。看 [C04](/embedded-interview/c-basics.md#c04)。

**S21 要点：** ① 管理方式：栈由编译器/OS 自动分配释放，堆由程序员 `malloc/free` 管理；② 空间与方向：栈小且向低地址生长，堆大、向高地址生长、碎片化；③ 效率：栈快（移动栈指针），堆慢（找空闲块、可能加锁）；④ 生命周期：栈随函数返回失效，堆到 `free` 为止；⑤ 适用：小而短命的对象用栈，大小不定、跨函数生命周期、缓冲区用堆；ISR/任务栈里**禁止**大局部数组（[R08](/embedded-interview/rtos.md#r08)）。看 [C06](/embedded-interview/c-basics.md#c06)。

**S22 要点：** ① `if (a = b)` 把 b 赋给 a 后以 b 的值当条件，条件恒随 b 变化，逻辑被静默改写，编译器常常只给告警；② `if (p = NULL)` 恒假/恒真类 bug；③ 循环条件里误写会死循环或提前退出；④ 规避：常量写左边 `if (CONST == var)`、开 `-Wall -Wparentheses`、对返回值赋值的语句单独一行。看 [运算符专题](/c-language/operators.md)。真题同款：2019 应用岗问答题。

**S23 参考实现：**

```c
void reverse_str(char *s)
{
    if (s == NULL)
        return;
    size_t len = strlen(s);
    if (len < 2)
        return;
    char *e = s + len - 1;
    while (s < e) {
        char t = *s;
        *s = *e;
        *e = t;
        s++; e--;
    }
}
```

测试用例：`NULL`、空串 `""`、单字符 `"a"`、偶数长度 `"abcd"`、含重复字符 `"aab"`。追问点：为什么不用临时数组（原地、栈开销）；为什么 `s < e` 而不是 `!=`（奇偶都安全）。

**S24 参考实现：**

```c
int queue_push(Queue *q, int v)
{
    if (q == NULL)
        return -1;
    QNode *n = (QNode *)malloc(sizeof(QNode));
    if (n == NULL)
        return -1;              /* 分配失败：不改链表，直接返回 */
    n->data = v;
    n->next = NULL;
    if (q->tail == NULL) {      /* 空队列：头尾都要接上 */
        q->head = n;
        q->tail = n;
    } else {
        q->tail->next = n;
        q->tail = n;
    }
    return 0;
}

int queue_pop(Queue *q, int *out)
{
    if (q == NULL || out == NULL || q->head == NULL)
        return -1;              /* 空队列出队是错误，不是 0 */
    QNode *n = q->head;
    *out = n->data;
    q->head = n->next;
    if (q->head == NULL)        /* 出完最后一个：尾指针也要清 */
        q->tail = NULL;
    free(n);
    return 0;
}
```

要点：**空队列插入要同时设置头尾**；**出完最后一个节点要把 tail 一起置 NULL**（否则留下悬空尾指针，下一次 push 会写坏内存——这是本题真正的区分点）；失败路径不动链表。线程不安全时，加锁范围要覆盖"读 tail→写 next→更新 tail"整段临界区，ISR 里调用要用无锁环形队列代替。看 [C07](/embedded-interview/c-basics.md#c07)、[R10](/embedded-interview/rtos.md#r10)。真题同款：P5-2、2019 应用岗编程题。

---

**做完之后**：把错题对应的知识页回炉，两天后只重做错题；再做一遍[两周复习表](/embedded-interview/review-plan.md)里对应的自测动作。
