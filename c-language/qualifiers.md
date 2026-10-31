# C 语言 - volatile / const / static 三者辨析专题

> 面向嵌入式开发。本文不从"语法定义"出发，而是**站在编译器视角**：它在生成代码时对这三个关键字分别做了什么决定。

## 学习要求

目标是能对任意一段嵌入式代码，准确说出其中每个 `volatile` / `const` / `static` **为什么必须加、或者为什么不该加**，并能解释"不加会出什么错"。

## 应掌握的程度

- 能说明 `volatile` 只约束"读"、不保证原子性与顺序。
- 能区分 `const` 的四种指针位置，并知道 `const` 是编译期约束而非物理只读。
- 能区分 `static` 的两个完全无关的含义（存储期 / 链接属性）。
- 能正确组合三者，写出符合规范的驱动模块。

## 学习方式与计划

1. 先建立"编译器视角"的总纲（§0），三者都挂在这张表上。
2. 每个关键字按「它解决什么问题 → 代码对比 → 嵌入式场景 → 常见误解」四步走。
3. 最后用组合场景收口（§4），并用三个实验验证（§6）。

---

## 0. 总纲：三者的本质区别

| 关键字 | 对编译器说什么 | 改变代码生成 | 改变内存布局 | 管什么 |
| :--- | :--- | :--- | :--- | :--- |
| **`volatile`** | "这个变量可能被你看不见的东西改，别优化" | ✅ **会** | ❌ 不会 | **读** |
| **`const`** | "我不打算改它"——这是**承诺**，不是强制 | ⚠️ 通常不会 | ⚠️ 可能 | **写** |
| **`static`** | "这个变量的生命周期/可见性特殊" | ❌ 不会 | ✅ **会** | **生命周期 + 可见性** |

一句话记忆：

- **`volatile` 管读**：每次都真的去内存读。
- **`const` 管写**：承诺不写，让编译器和调用者放心。
- **`static` 管活多久、谁能看见**：存储期和链接属性。

三者**互不冲突**，可以叠加：`static const volatile uint32_t reg;` 完全合法。

---

# 一、volatile

## 1.1 它解决什么问题

编译器会做优化。如果它看到「连续两次读同一个变量，中间没有任何写操作」，会认为第二次读到的值一定和第一次一样，于是**把第二次读删掉，复用寄存器里的旧值**。

这在普通程序里完全正确。但当这个变量是**硬件寄存器**时，它可能已经变了——只是编译器"看不见"。

**真实的坑：**

```c
// 错误的写法
uint32_t status = USART->SR;   // 读一次状态寄存器
while (!(status & RXNE)) {     // 编译器：status 没变，死循环读寄存器里的旧值
    ;
}
```

```c
// 正确的写法
volatile uint32_t *sr = &USART->SR;
while (!(*sr & RXNE)) {        // volatile：每次都真的去读内存地址
    ;
}
```

> **`volatile` 的准确含义**：这个对象的值可能在意料之外被改变，所以每次使用都必须重新从内存读取，不能缓存到寄存器。
>
> 注意：它约束的是**读**（有时也约束写——不能把多次写合并）。它**不保证**读和写之间不被打断。

## 1.2 必须用 volatile 的四个场景

| 场景 | 为什么必须 | 典型代码 |
| :--- | :--- | :--- |
| **① 内存映射寄存器** | 硬件随时可能改它，编译器不知道 | `#define GPIOA_ODR (*(volatile uint32_t*)0x40020014)` |
| **② ISR 与主循环共享的标志** | 中断在任意时刻改变量 | `volatile uint8_t g_rx_done;` |
| **③ 多任务共享的简单变量** | 任务切换在任意时刻发生 | `volatile int g_state;` |
| **④ 忙等循环里的变量** | 循环体内编译器看不到变化 | `while (!g_flag) {}` 里的 `g_flag` |

### 场景 ①：寄存器定义的标准写法

```c
// 方式一：指针强制转换
#define REG_STATUS  (*(volatile uint32_t *)0x40021000)

// 方式二：结构体映射（STM32 官方头文件的做法）
typedef struct {
    volatile uint32_t CR1;
    volatile uint32_t CR2;
    volatile uint32_t SR;
    volatile uint32_t DR;
} USART_TypeDef;

#define USART1  ((USART_TypeDef *)0x40011000)

// 使用
USART1->DR = 'A';              // 写：必须真的写进去
while (!(USART1->SR & 0x20));  // 读：必须每次都读
```

> **注意位置**：`volatile` 要加在**被指向的对象**上（`volatile uint32_t *`），而不是指针本身。写成 `uint32_t * volatile p` 是"指针本身不能改"，完全不是一回事。

### 场景 ②：ISR 与主循环共享

```c
volatile uint8_t g_uart_byte;
volatile uint8_t g_uart_ready = 0;

void USART_IRQHandler(void) {
    g_uart_byte = USART1->DR;   // 读数据寄存器会清标志
    g_uart_ready = 1;
}

int main(void) {
    while (1) {
        if (g_uart_ready) {          // 必须 volatile，否则编译器可能把它优化成只读一次
            process(g_uart_byte);
            g_uart_ready = 0;
        }
    }
}
```

**但这里还有个隐藏的坑**：`volatile` 只保证"每次都读"，**不保证 `if` 判断和后面的处理是原子的**。如果中断恰好在 `if (g_uart_ready)` 判断为真之后、`g_uart_ready = 0` 之前又来了新数据，新数据会被覆盖丢失。

**这就是为什么 `volatile` 不够，还需要临界区或 RTOS 同步原语。**

## 1.3 volatile 不能做什么（面试最爱挖）

| 你以为 volatile 能 | 实际不能 | 原因 |
| :--- | :--- | :--- |
| 保证 `counter++` 原子 | ❌ 不能 | `counter++` 是读-加-写三步，中间可能被打断 |
| 保证两个变量的读写顺序 | ❌ 不能 | `volatile` **不是内存屏障**，编译器和 CPU 都可能重排 |
| 解决多核共享 | ❌ 不能 | 需要内存屏障 + 原子操作 + Cache 一致性处理 |
| 解决 DMA 的 Cache 问题 | ❌ 不能 | Cache 一致性和 `volatile` 完全是两回事 |

### 为什么 `volatile counter++` 不安全

```c
volatile int counter = 0;

// 实际编译成三条指令：
//   LDR  r0, [counter]   ← 读
//   ADD  r0, r0, #1      ← 加
//   STR  r0, [counter]   ← 写
```

```text
时间线：
任务A: LDR 读到 5 ────────────────────────→ ADD 6 → STR 写 6
中断:        LDR 读到 5 → ADD 6 → STR 写 6
                                      ↑
                              任务A 的写覆盖了中断的写，丢了一次
```

**正确做法：**

```c
// 方案一：关中断（裸机）
__disable_irq();
counter++;
__enable_irq();

// 方案二：原子操作（C11 / 编译器内建）
counter = __atomic_add_fetch(&counter, 1, __ATOMIC_SEQ_CST);

// 方案三：RTOS 临界区
taskENTER_CRITICAL();
counter++;
taskEXIT_CRITICAL();
```

## 1.4 const volatile 组合

`const volatile uint32_t STATUS;` 表示：

- `const`：我的代码不应该写它（写了是 bug）
- `volatile`：但它的值会被硬件改变，每次都要重新读

**典型场景**：只读状态寄存器、ADC 数据寄存器、输入捕获寄存器。

面试被问到「const 和 volatile 能一起用吗」，答案是**能，而且很常见**。

---

# 二、const

## 2.1 const 的本质：一个承诺，不是一道锁

**`const` 不是"把它变成只读内存"，而是"我承诺不通过这个名字修改它"。**

```c
const int x = 10;
int *p = (int *)&x;   // 强转去掉 const
*p = 20;              // ⚠️ 未定义行为！但很多平台"能跑"
```

为什么是 UB？因为编译器可能把 `x` 放进 `.rodata`（真正的只读段），写它会触发段错误；也可能把它当成立即数直接内联，写内存根本没影响。

**关键区分：**

- 如果**原对象本来就是 `const`**，强转去掉后修改 → **未定义行为**
- 如果**原对象不是 `const`**，只是通过 `const` 指针访问 → 通过别的可写别名修改是**合法的**

> 面试问「const 变量能不能改」，正确回答是：**取决于原对象是不是真的 const，以及它被放在哪个段。**

## 2.2 四种 const 位置

**读法：从右往左读。**

| 声明 | 中文读法 | 能改指针 | 能改目标 |
| :--- | :--- | :--- | :--- |
| `const int *p` | p 是 指向 const int 的 指针 | ✅ 能 | ❌ 不能 |
| `int const *p` | 同上（写法不同，含义相同） | ✅ 能 | ❌ 不能 |
| `int * const p` | p 是 const 的 指针，指向 int | ❌ 不能 | ✅ 能 |
| `const int * const p` | p 是 const 的 指针，指向 const int | ❌ 不能 | ❌ 不能 |

**记忆口诀：看 `const` 在 `*` 的哪一边。**

- `const` 在 `*` **左边** → 锁**值**（指向的内容不能改）
- `const` 在 `*` **右边** → 锁**指针**（不能指向别处）
- 两边都有 → 全锁

## 2.3 嵌入式中的五大应用

### 应用 ①：只读配置表放 Flash，省 RAM

```c
// ❌ 不好：占用 RAM（.data 段，启动时从 Flash 拷到 RAM）
const char *menu_items[] = {"设置", "音乐", "运动"};

// ✅ 好：指针数组本身也是 const，全部留在 Flash
static const char *const menu_items[] = {
    "设置", "音乐", "运动"
};
```

> **这一条在 MCU 上是真金白银**：`const` 修饰的全局数组，链接器会放进 `.rodata` 段，**留在 Flash，不占 RAM**。
>
> 对于一个 64KB RAM 的 MCU，一张 10KB 的菜单/字库/协议表，加不加 `const` 就是能不能跑起来的差别。
>
> **注意**：`const char *p[]`（指针数组）只有指针指向的内容是 const，数组本身在 RAM。要 `const char *const p[]` 才能全放 Flash。

### 应用 ②：函数参数承诺不修改

```c
// 好的 API 设计
void uart_send(const uint8_t *buf, size_t len);
// 调用者放心：这个函数不会改我的 buf

size_t str_len(const char *s);
// 语义清晰：只读不写
```

> 如果写成 `void uart_send(uint8_t *buf, size_t len)`，调用者会怀疑"它会不会改我的缓冲区"，还得自己拷贝一份。

### 应用 ③：编译期检查

```c
const uint8_t MAX_RETRY = 3;
MAX_RETRY = 5;   // ❌ 编译错误：assignment of read-only variable
```

**但更好的做法**是用宏或 enum，连存储都不占：

```c
#define MAX_RETRY 3
// 或
enum { MAX_RETRY = 3 };
```

| 方式 | 类型检查 | 占存储 | 调试可见 | 推荐场景 |
| :--- | :--- | :--- | :--- | :--- |
| `const` 变量 | ✅ 有 | ⚠️ 可能 | ✅ 能看 | 只读数据（表、字库） |
| `#define` 宏 | ❌ 无 | ✅ 零 | ❌ 看不到 | 简单常量、配置开关 |
| `enum` | ✅ 有 | ✅ 零 | ✅ 能看 | **整数常量首选** |

> **嵌入式的习惯**：整数常量用 `enum` 或 `#define`，只读数据用 `const`。

### 应用 ④：防止指针被意外改指向

```c
// 硬件寄存器基址：永远不应该指向别处
static USART_TypeDef * const USART1_BASE = (USART_TypeDef *)0x40011000;

// 或者更常见的做法：直接宏定义
#define USART1  ((USART_TypeDef *)0x40011000)
```

### 应用 ⑤：const 成员函数（C++ 场景）

```cpp
class Sensor {
public:
    int read() const;   // 承诺：这个函数不修改对象状态
private:
    int value_;
};

const Sensor s;
s.read();   // ✅ 可以
```

## 2.4 const 的常见误解

| 误解 | 真相 |
| :--- | :--- |
| `const` 变量一定在 Flash | 不一定。局部 const 通常在栈上；全局 const 才可能进 `.rodata` |
| `const` 一定不占 RAM | 不一定。取决于编译器是否把它当立即数内联 |
| `const` 能防止所有修改 | 不能。强转可以绕过，只是 UB |
| `const` 会让程序变慢 | 不会。`const` 只增不减优化机会 |
| `const` 就是只读内存 | 不是。它是**类型系统层面的约束**，与物理内存属性无关 |

---

# 三、static

## 3.1 两个完全不同的含义

**这是最容易混淆的地方。** `static` 在 C 里有**两个毫不相关的含义**，取决于它出现在哪里：

- **在函数内部** → 改变**存储期**（生命周期）
- **在文件作用域** → 改变**链接属性**（可见性）

这两件事没有任何关系，只是恰好共用一个关键字。

| 位置 | 改变了什么 | 效果 | 典型用途 |
| :--- | :--- | :--- | :--- |
| 函数内部 `static int x;` | **存储期** | 从自动→静态：跨调用保值，只初始化一次 | 计数器、状态缓存 |
| 文件作用域 `static int x;` | **链接属性** | 从外部→内部：只在本 `.c` 可见 | 模块私有变量 |
| 文件作用域 `static void f()` | **链接属性** | 函数只在本 `.c` 可见 | 模块私有函数 |

## 3.2 用法一：函数内 static（静态存储期）

```c
void count_calls(void) {
    static int count = 0;   // 只在第一次调用时初始化为 0
    count++;
    printf("called %d times\n", count);
}
// 每次调用 count 都保留上次的值
```

**关键特性：**

- **只初始化一次**：不是每次进函数都初始化
- **不占栈**：放在 `.data`（有初值）或 `.bss`（无初值）段
- **作用域仍在函数内**：外面访问不到
- **⚠️ 不可重入**：所有调用共享同一份数据

### 嵌入式中的典型应用

```c
// ① 状态机（保存上次状态）
void ui_task(void) {
    static enum { IDLE, RUNNING, PAUSED } state = IDLE;
    switch (state) { /* ... */ }
}

// ② 一次性初始化
void sensor_init(void) {
    static bool inited = false;
    if (inited) return;
    inited = true;
    // 真正的初始化代码
}

// ③ 节省栈空间（大缓冲区）
void process_frame(void) {
    static uint8_t frame_buf[512];   // 不占栈！
    // ...
}
// ⚠️ 但这是不可重入的，多任务下必须加锁
```

> **第 ③ 种用法是双刃剑**：把大缓冲区改成 `static` 能救急（栈只有几 KB 时），但代价是**这个函数不能并发调用**。
>
> 如果在 RTOS 里两个任务都调用它，数据会互相覆盖——这种 bug 极难查，因为「平时是好的，一忙就出错」。
>
> **正确做法**：要么加锁，要么改成传入缓冲区指针（`void process(uint8_t *buf)`）。

## 3.3 用法二：文件作用域 static（内部链接）

```c
// sensor.c
static int g_calibration_offset = 0;   // 只有本文件能访问
static void apply_calibration(void) {  // 只有本文件能调用
    // ...
}

void sensor_read(void) {               // 对外公开的 API
    apply_calibration();
    // ...
}
```

**为什么嵌入式特别需要它：**

| 理由 | 说明 |
| :--- | :--- |
| 避免符号冲突 | 工程里有 20 个模块，每个都可能有个 `init()`。不加 static 会链接冲突 |
| 隐藏实现细节 | 外部只能看到 `sensor_read()`，改内部实现不影响别人 |
| 帮助编译器优化 | 编译器知道只在本文件用，可以内联、可以删掉没用到的 |
| 配合 `-Wmissing-prototypes` | 强制所有非 static 函数都要有声明，避免误暴露 |

### 模块化驱动的标准骨架

```c
// ---- bsp_led.c ----
#include "bsp_led.h"

static GPIO_TypeDef * const s_port = GPIOA;   // 私有常量
static uint16_t s_pin = 5;                    // 私有状态
static uint8_t  s_brightness = 100;           // 私有状态

static void set_pin(uint8_t on) {             // 私有函数
    HAL_GPIO_WritePin(s_port, s_pin, on ? GPIO_PIN_RESET : GPIO_PIN_SET);
}

void led_init(void) {                         // 公开 API
    // 配置 GPIO
}

void led_on(void) {                           // 公开 API
    set_pin(1);
}

void led_off(void) {                          // 公开 API
    set_pin(0);
}
```

> **这条规则能救命**：所有不需要对外暴露的函数和变量，**一律加 `static`**。这是嵌入式代码规范的第一条。

## 3.4 static 的陷阱

| 陷阱 | 说明 | 怎么避免 |
| :--- | :--- | :--- |
| **头文件里定义 static 变量** | 每个 include 它的 `.c` 都会得到一份**独立副本**，看起来共享实际各自独立 | 头文件只放 `extern` 声明，定义放 `.c` |
| **static 局部变量 + 多任务** | 不可重入，数据会被踩 | 加锁，或改成传参 |
| **误以为 static 能省 Flash** | 它省的是栈，不是 Flash。反而占用了静态 RAM | 真正要省 RAM 用 `const` 放 Flash |

### 头文件 static 的坑（重点）

```c
// ❌ config.h
static int g_config_value = 0;   // 危险！

// a.c 和 b.c 都 #include "config.h"
// 结果：a.c 有一份 g_config_value，b.c 也有一份，互不相干
// a.c 改了值，b.c 看不到 —— 这种 bug 极难发现

// ✅ 正确做法
// config.h
extern int g_config_value;   // 只是声明

// config.c
int g_config_value = 0;      // 唯一定义
```

---

# 四、三者组合

## 4.1 合法且常用的组合

| 组合 | 含义 | 典型场景 |
| :--- | :--- | :--- |
| `static const` | 本文件私有的只读数据 | 模块内的配置表、查找表 |
| `static volatile` | 本文件私有的易变变量 | ISR 标志、私有寄存器缓存 |
| `const volatile` | 我不写，但硬件会改 | 只读状态寄存器 |
| `static const volatile` | 全都要 | 模块私有的只读状态寄存器 |

```c
// 真实例子：UART 驱动的私有状态寄存器映射
static volatile uint32_t * const s_uart_sr = (volatile uint32_t *)0x40011000;

// 拆开看：
//   static   → 只在本文件可见
//   volatile → 每次都要真的读（硬件会改）
//   * const  → 指针本身不能改指向（永远指向这个地址）
//   uint32_t → 指向的内容是 32 位整数
```

## 4.2 结构总览

```text
三个关键字
├── volatile ─── 管读：每次都从内存读
│   ├── 场景：寄存器 / ISR 标志 / 忙等
│   └── 不管：原子性 / 内存屏障 / Cache
├── const ────── 管写：承诺不修改
│   ├── 场景：只读表放 Flash / 参数保护
│   └── 注意：是承诺不是锁
└── static ───── 管生命周期与可见性
    ├── 函数内：改存储期（只初始化一次、不占栈、不可重入）
    ├── 文件内：改可见性（内部链接、避免冲突）
    └── 两个含义完全无关
```

---

# 五、面试速答

| 问题 | 答案要点 | 常见错误 |
| :--- | :--- | :--- |
| `volatile` 的作用 | 告诉编译器这个变量可能被意外改变，每次都要重新读 | 答"防止优化"太笼统，要说清"每次从内存读" |
| `volatile` 能保证原子性吗 | **不能**。`counter++` 是读-加-写三步 | 答"能"，直接暴露 |
| `volatile` 和 `const` 能一起用吗 | **能**。只读状态寄存器就典型：我不写，但硬件会改 | 答"不能" |
| `static` 的两个含义 | 函数内改存储期，文件内改链接属性，**两者无关** | 只答一个 |
| 为什么全局变量要加 `static` | 内部链接，避免符号冲突，隐藏实现 | 答"省内存"（错） |
| `const` 变量在哪个段 | 全局 `const` 通常在 `.rodata`（Flash）；局部 `const` 通常在栈 | 答"一定在 Flash" |
| `const` 能真的防止修改吗 | 不能，强转可绕过（UB）。它是编译期约束 | 答"能防止" |
| 头文件里能定义 `static` 变量吗 | 技术上能，但每个 `.c` 会有独立副本，几乎总是错的 | 不知道这个坑 |

---

# 六、动手验证

## 实验一：亲眼看到 volatile 的作用

写两段一样的忙等代码，一段变量加 `volatile`、一段不加，用 `gcc -O2 -S` 生成汇编。你会看到不加 `volatile` 的那段，循环里根本没有 load 指令——值被缓存在寄存器里了。

## 实验二：验证 const 放哪个段（最值得做）

```c
// lab.c
const int a[100] = {1};   // 应该进 .rodata
int       b[100] = {1};   // 应该进 .data

int main(void) { return a[0] + b[0]; }
```

```bash
arm-none-eabi-gcc -c lab.c -o lab.o
arm-none-eabi-size lab.o
# 观察 .rodata 和 .data 的大小
# 或直接看链接后的 .map 文件
```

> **如果你只有时间做一个，做这个。** 看到 `.map` 文件里 `const` 数组算在 Flash、非 const 算在 RAM 的那一刻，「const 省 RAM」就从一句话变成了肌肉记忆。

## 实验三：验证 static 不可重入

写一个用 `static` 缓冲区的函数，在 RTOS 里开两个任务同时调用它，打印结果。你会看到数据被踩——这比看十遍理论有用。

---

# 七、与其他专题的关系

- [存储期、作用域与模块化](storage-modules.md) —— 从"变量活多久、谁能看见"的角度展开 `static` / `extern` / `const`
- [中断、并发与 volatile](isr-concurrency.md) —— 从"并发安全"的角度展开 `volatile` 的边界
- [位运算与寄存器操作](bitwise-registers.md) —— 寄存器读改写的实际代码
- [内存布局与未定义行为](memory-undefined-behavior.md) —— `.data` / `.bss` / `.rodata` 的链接布局
- [嵌入式可靠性与测试](reliability-testing.md) —— 如何用测试暴露不可重入问题

**本文的定位**：上述四篇各讲一个侧面，本文把三者**放在同一张表上对比**，并用"编译器视角"统一解释。

---

# 八、一句话总结

**`volatile` = 「别相信寄存器里的缓存，每次都去内存看」——管读**

**`const` = 「我承诺不写它」——管写，但只是承诺**

**`static` = 「它的寿命/可见范围不一样」——管生命周期和可见性**

三者互不冲突，可以叠加。真正理解它们的关键是：**站在编译器视角看，它在生成代码时做了什么决定。**
