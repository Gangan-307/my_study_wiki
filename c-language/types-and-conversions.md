# C 语言 - 数据类型与类型转换专题

## 学习要求

面向嵌入式开发，重点解决“数据到底有多宽、符号如何变化、表达式最终按什么类型计算”三个问题。所有协议字段、寄存器值和长度参数都要能明确其类型与取值范围。

## 应掌握的程度

- 能根据需求选用 `uint8_t`、`uint16_t`、`uint32_t`、`int32_t`、`size_t` 等类型，而不依赖 `int` 的平台大小。
- 能判断整数提升、隐式转换、显式转换、比较和移位表达式的最终类型及风险。
- 能定位有符号/无符号比较、截断、溢出造成的实际 Bug，并给出修复方式。

## 学习方式与计划

1. 先用小程序打印各类型大小、范围与表达式结果，在 PC 和目标 MCU 编译器上对照。
2. 每学一个规则，编写一个“错误示例 + 修复示例”，记录编译器告警。
3. 最后用 UART 协议帧的长度、校验和、字节序字段完成一次综合练习。

---

## 一、基础类型与定宽整数

### 1. 基本类型的大小与范围

C 的类型大小与目标平台、编译器和 ABI 有关。PC 上 `int` 常见为 32 位，但部分 MCU 工具链中 `int` 可能是 16 位。因此，协议、寄存器和存储格式不能依赖 `int`、`long` 的“通常大小”。

| 类型 | 保证 | 嵌入式中的常见用途 | 注意事项 |
| :--- | :--- | :--- | :--- |
| `char` | 恰好 1 字节，字节位数由 `CHAR_BIT` 决定 | 字符、原始字节 | `char` 是否有符号由实现决定 |
| `int` | 至少 16 位 | 循环计数、一般运算 | 不用于固定格式的协议字段 |
| `uint8_t` / `int8_t` | 恰好 8 位，平台提供时才存在 | UART 数据、寄存器字节、缓存 | 参与表达式时通常会提升为 `int` |
| `uint16_t` / `int16_t` | 恰好 16 位 | ADC 值、传感器原始值、协议字段 | 注意端序与有符号含义 |
| `uint32_t` / `int32_t` | 恰好 32 位 | 寄存器、计时器、计数器 | 时间差优先使用 `uint32_t` |
| `size_t` | 能表示任意对象的大小 | 数组长度、缓冲区容量、`sizeof` 返回值 | `printf` 使用 `%zu` |

`CHAR_BIT` 在 `<limits.h>` 中定义。绝大多数 MCU 的一个字节为 8 位，但这是目标平台特性，不是 C 语言对“字节位数”的保证。

观察当前编译目标实际类型，而不是背固定数值：

```c
#include <limits.h>
#include <stdint.h>
#include <stdio.h>

int main(void)
{
    printf("CHAR_BIT = %d\n", CHAR_BIT);
    printf("sizeof(int) = %zu\n", sizeof(int));
    printf("sizeof(uint32_t) = %zu\n", sizeof(uint32_t));
    printf("UINT16_MAX = %u\n", (unsigned int)UINT16_MAX);
    return 0;
}
```

### 2. `stdint.h` 与 `stdbool.h`

嵌入式代码优先使用 `<stdint.h>` 的定宽类型表达接口和数据格式：

```c
#include <stdbool.h>
#include <stdint.h>

typedef struct {
    uint32_t baud_rate;  // 波特率是非负的明确数值
    uint8_t data_bits;   // 协议字段宽度固定
    bool parity_enabled; // 只有真/假两种状态
} uart_config_t;
```

选择类型时先回答四个问题：

1. 数据是否允许负数？
2. 最大值和最小值是多少？
3. 它是否要写入寄存器、协议或 Flash 中？
4. 它是否用于数组长度、内存偏移或指针差？

只有第 4 类通常应使用 `size_t` 或 `ptrdiff_t`。不要因为“数值不会很大”就把长度写成 `uint8_t`，否则缓冲区容量扩大后容易截断。

### 3. `size_t`、`ptrdiff_t` 与格式化输出

- `sizeof` 的结果是 `size_t`，应使用 `%zu` 输出。
- 两个同一数组元素指针相减的结果是 `ptrdiff_t`，应使用 `%td` 输出。
- `uint32_t` 的输出不要假设等同于 `unsigned int`；可使用 `<inttypes.h>` 的 `PRIu32`。

```c
#include <inttypes.h>
#include <stddef.h>
#include <stdint.h>
#include <stdio.h>

void print_buffer_info(const uint8_t *buffer, size_t length)
{
    printf("length = %zu\n", length);
    printf("first byte = %" PRIu8 "\n", buffer[0]);
}
```

传递长度时，接口应同时携带指针和长度；`uint8_t *data` 本身无法告诉函数缓冲区有多大。

---

## 二、整数提升与通常算术转换

### 1. `char`、`short` 为什么先提升为 `int`

`uint8_t`、`int8_t`、`uint16_t` 等较窄的整数参与算术、比较和位运算时，通常会先提升为 `int`（若 `int` 无法容纳全部值，则提升为 `unsigned int`）。因此变量的声明类型和表达式的计算类型不一定相同。

```c
uint8_t a = 200U;
uint8_t b = 100U;

// 在多数 32 位 MCU 上，a + b 按 int 计算，结果为 300。
// 赋回 uint8_t 时只保留低 8 位，最终得到 44。
uint8_t sum = a + b;
```

关键结论：**窄类型不是天然的窄位宽运算。** 需要明确中间结果范围，再决定保存结果的类型。

对于 ADC 缩放等计算，先选择能容纳中间结果的类型：

```c
uint16_t raw = 4095U;
uint32_t millivolts = ((uint32_t)raw * 3300U) / 4095U;
```

这里的转换发生在乘法之前，确保中间结果不会按窄类型截断。最终若需要写入更窄的变量，仍必须先做范围检查。

### 2. 有符号与无符号混合运算

有符号数和无符号数比较是常见 Bug 来源。若无符号类型的转换等级不低于有符号类型，负数可能被转换为很大的无符号数。

```c
int16_t length = -1;
uint16_t capacity = 128U;

// 不要依赖这一比较的直觉。length 可能先转成很大的无符号数。
if (length <= capacity) {
    // 错误的业务判断风险
}
```

正确做法是先在有符号域内排除非法值，再转换：

```c
bool length_fits(int16_t length, uint16_t capacity)
{
    return (length >= 0) && ((uint16_t)length <= capacity);
}
```

同一原则适用于循环条件。数组下标和容量通常为 `size_t`，而从外部输入得到的长度需要先验证非负，再转换为 `size_t`。

### 3. 截断、符号扩展与显式转换

从宽类型转换为窄类型时，高位可能被丢弃：

```c
uint16_t adc_value = 1000U;
uint8_t low_byte = (uint8_t)adc_value; // 结果为 232，不是 1000
```

显式转换不会让转换变安全，它只是告诉编译器“我知道正在转换”。正确顺序应当是：**先验证范围，再转换，最后赋值。**

```c
#include <stdbool.h>
#include <stdint.h>

bool set_threshold(uint16_t input, uint8_t *threshold)
{
    if ((threshold == NULL) || (input > UINT8_MAX)) {
        return false;
    }

    *threshold = (uint8_t)input;
    return true;
}
```

从有符号窄类型转换为更宽的有符号类型时会进行符号扩展：

```c
int8_t temperature = -10;
int32_t display_value = temperature; // 结果仍为 -10
```

从无符号类型转换为更宽类型时补零。分析协议字段时必须先确认该字段是“二进制无符号量”还是“二进制补码有符号量”。

---

## 三、溢出、移位与字节序

### 1. 有符号溢出与无符号回绕

- 无符号整数按 `2^N` 取模回绕，这个行为由标准定义。
- 有符号整数溢出是未定义行为，不能依赖它得到固定结果。

因此，循环计数、协议序号和毫秒计时器通常使用无符号类型。处理 32 位时钟回绕时，直接求差是可靠的：

```c
#include <stdbool.h>
#include <stdint.h>

bool has_elapsed(uint32_t now, uint32_t start, uint32_t timeout_ms)
{
    return (uint32_t)(now - start) >= timeout_ms;
}
```

这适用于超时时间小于计时器完整回绕周期的一半的常见嵌入式场景。不要先用 `now >= start` 判断，因为回绕后该条件会失效。

若业务计算可能超出类型范围，应使用更宽的中间类型、限制输入范围，或在运算前做溢出检查。

### 2. 左移、右移的边界条件

位移操作应遵守以下规则：

- 移位次数必须小于左操作数的位宽；`value << 32` 对 32 位数是未定义行为。
- 用无符号类型做掩码和移位；对负数左移、以及依赖有符号右移补位方式，都不适合写可移植驱动代码。
- 常量应带正确后缀，寄存器掩码推荐写成 `UINT32_C(1) << bit`。

```c
#include <stdint.h>

uint32_t make_mask(uint8_t bit)
{
    if (bit >= 32U) {
        return 0U;
    }
    return UINT32_C(1) << bit;
}
```

移位的寄存器读写细节将在 [位运算与寄存器操作专题](bitwise-registers.md) 中展开。

### 3. 大小端与协议字段转换

端序只影响“多个字节组成一个数”的存储顺序，不影响单个字节内的位顺序。网络协议常使用大端序，而 MCU 内存通常为小端序，因此不能把接收缓冲区直接强制转换为 `uint16_t *` 后解引用。

安全解析方式是逐字节组合：

```c
#include <stdint.h>

uint16_t read_be_u16(const uint8_t bytes[2])
{
    return ((uint16_t)bytes[0] << 8U) | (uint16_t)bytes[1];
}

uint32_t read_be_u32(const uint8_t bytes[4])
{
    return ((uint32_t)bytes[0] << 24U) |
           ((uint32_t)bytes[1] << 16U) |
           ((uint32_t)bytes[2] << 8U) |
           (uint32_t)bytes[3];
}
```

这种方式同时避开了未对齐访问、端序差异和严格别名问题。解析前仍要验证指针非空、缓冲区长度足够和协议字段合法。

---

## 四、嵌入式常见错误与调试方法

| 现象 | 常见根因 | 检查与修复方向 |
| :--- | :--- | :--- |
| 负长度被当作超大长度 | 有符号数与无符号数混合比较 | 先检查负值，再进行转换 |
| ADC 计算结果突然变小 | 中间乘法溢出或最终截断 | 使用更宽中间类型，验证最终范围 |
| 协议值在不同平台不一致 | 直接解引用字节缓冲区 | 按协议端序逐字节组合 |
| 超时判断在长时间运行后失效 | 用大小比较代替无符号时间差 | 使用 `now - start` 的无符号差值 |
| 寄存器掩码异常 | 移位常量为有符号，或移位次数越界 | 使用无符号常量，校验位号 |

编译练习时建议开启告警：

```bash
gcc -std=c11 -Wall -Wextra -Wconversion -Wsign-conversion -Werror type_lab.c -o type_lab
```

`-Wconversion` 和 `-Wsign-conversion` 会暴露许多隐式转换问题。不要仅靠强制类型转换消除告警；先明确数据范围和业务含义，再决定转换位置。

---

## 五、学习自测

完成本专题前，至少能独立回答并验证以下问题：

1. 为什么协议字段应使用 `uint16_t` 而不是 `int`？
2. 为什么 `uint8_t a = 200U; uint8_t b = 100U;` 相加后赋回 `uint8_t` 会得到意外结果？
3. 为什么将 `int16_t` 与 `uint16_t` 直接比较有风险？
4. 显式写 `(uint8_t)` 为什么不能代替范围检查？
5. 为什么 32 位毫秒计时器回绕后仍可使用无符号减法判断超时？
6. 为什么解析协议字节时不应把 `uint8_t *` 直接转换为 `uint16_t *`？

## 六、实战练习

- [ ] 编写类型观察程序，记录 PC 与目标 MCU 上的类型大小差异。
- [ ] 为一帧 UART 数据定义定宽字段并完成大端解析。
- [ ] 实现“先校验、后窄化转换”的参数设置函数。
- [ ] 修复三个有符号/无符号比较 Bug，并说明每处隐式转换。
- [ ] 使用编译告警定位一次窄化转换，记录错误、原因和修复方案。
