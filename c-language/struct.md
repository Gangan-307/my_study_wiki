# C语言结构体（Struct）学习笔记

本笔记系统地记录了 C 语言中结构体的核心概念、常见操作、指针应用、内存对齐底层逻辑以及综合实战案例，便于后续查阅与复习。

---

## 一、 基础概念与定义方式

### 1. 为什么需要结构体？
C 语言的基本数据类型（如 `int`, `char`, `float`）仅能表示单一属性。结构体（`struct`）允许开发者将不同类型的数据组合成一个自定义的复合类型，用以描述具有多属性的复杂对象（如学生、书籍、商品等）。

### 2. 结构体的定义与变量声明

在 C 语言中，主要有以下几种声明和初始化结构体的方式：

#### 方式一：先定义结构体模板，再声明变量
```c
#include <stdio.h>

// 定义结构体模板
struct Student {
    char name[50];
    int id;
    float gpa;
};

int main() {
    // 声明结构体变量
    struct Student s1 = {"Alice", 1001, 3.8}; 
    return 0;
}
```

#### 方式二：使用 `typedef` 简化声明（实际开发中最常用）
使用 `typedef` 可以为结构体起一个别名，在声明变量时无需重复书写 `struct` 关键字。

```c
#include <stdio.h>

typedef struct {
    char name[50];
    int id;
    float gpa;
} Student; // Student 为该结构体类型的别名

int main() {
    // 直接使用别名声明变量并初始化
    Student s1 = {"Bob", 1002, 3.5};
    
    // 指定成员初始化（C99 标准）
    Student s2 = {.id = 1003, .name = "Charlie", .gpa = 3.9};

    // 访问与修改成员（使用 "." 操作符）
    s1.gpa = 3.7;
    printf("Name: %s, ID: %d, GPA: %.2f\n", s1.name, s1.id, s1.gpa);

    return 0;
}
```

---

## 二、 结构体进阶组合（嵌套与数组）

### 1. 结构体嵌套
一个结构体的成员可以是另一个已经定义好的结构体。

```c
#include <stdio.h>

typedef struct {
    int year;
    int month;
    int day;
} Date;

typedef struct {
    char title[100];
    char author[50];
    Date publishDate; // 嵌套结构体成员
} Book;

int main() {
    Book myBook = {
        "C Programming Language",
        "Kernighan & Ritchie",
        {1988, 4, 1} // 嵌套初始化
    };

    // 访问嵌套成员
    printf("Published in: %d-%d-%d\n", 
           myBook.publishDate.year, 
           myBook.publishDate.month, 
           myBook.publishDate.day);
    return 0;
}
```

### 2. 结构体数组
结构体数组用于表达同类型对象的集合。

```c
#include <stdio.h>

typedef struct {
    char name[20];
    int score;
} Student;

int main() {
    // 声明并初始化一个包含 3 个元素的结构体数组
    Student classA[3] = {
        {"Tom", 85},
        {"Jerry", 92},
        {"Spike", 78}
    };

    for (int i = 0; i < 3; i++) {
        printf("Student: %-10s | Score: %d\n", classA[i].name, classA[i].score);
    }
    return 0;
}
```

---

## 三、 结构体指针与函数传参

在涉及大型结构体或需要修改原结构体内容时，必须使用结构体指针。

### 1. 结构体指针与 `->` 操作符
当使用指针指向结构体变量时，访问成员应使用指向操作符（`->`）。

```c
Student s = {"Mary", 90};
Student *ptr = &s;

// 以下两种访问方式等价，但推荐使用第一种
ptr->score = 95;      // 推荐写法
(*ptr).score = 95;    // 繁琐，注意括号不可省略
```

### 2. 函数传参：值传递 vs 指针传递

*   **值传递**：函数接收的是结构体的一个副本。若结构体体积较大，复制过程会消耗较多内存和时间。
*   **指针传递**：仅传递结构体的地址（4 或 8 字节），效率高。如果不允许函数修改原数据，应加 `const` 限定。

```c
#include <stdio.h>

typedef struct {
    char title[50];
    double price;
} Product;

// 值传递（不推荐用于大型结构体）
void printByValue(Product p) {
    printf("[Value] Title: %s, Price: %.2f\n", p.title, p.price);
}

// 指针传递（推荐，使用 const 避免数据被意外篡改）
void printByPointer(const Product *p) {
    printf("[Pointer] Title: %s, Price: %.2f\n", p->title, p->price);
}

// 修改原结构体内容（必须使用指针传递）
void applyDiscount(Product *p, double discount) {
    if (p != NULL) {
        p->price *= discount;
    }
}

int main() {
    Product laptop = {"Laptop", 1000.00};
    
    printByPointer(&laptop);
    applyDiscount(&laptop, 0.90); // 打九折
    printByPointer(&laptop);
    
    return 0;
}
```

---

## 四、 内存对齐底层原理

### 1. 为什么需要内存对齐？
为了提高 CPU 访问内存的效率，编译器在安排结构体成员的空间时，通常不会将它们紧挨着存放，而是让每个成员都对齐到其自身大小的整数倍地址上。这可能导致结构体的实际大小大于各成员大小之和。

### 2. 对齐规则示例
*   每个成员的偏移量必须是该成员大小（或编译指定的对齐模数）的整数倍。
*   结构体的总大小必须是结构体内最大基本类型成员大小的整数倍。

```c
#include <stdio.h>

struct A {
    char a;   // 1 字节
    // 填充 3 字节（为了让 b 对齐到 4 字节边界）
    int b;    // 4 字节
    char c;   // 1 字节
    // 填充 3 字节（为了使整体大小为最大成员 int 的倍数，即 4 的倍数）
}; // 预期大小：12 字节

struct B {
    int b;    // 4 字节
    char a;   // 1 字节
    char c;   // 1 字节
    // 填充 2 字节（为了使整体大小为 4 的倍数）
}; // 预期大小：8 字节

int main() {
    printf("Size of Struct A: %zu bytes\n", sizeof(struct A)); // 输出: 12
    printf("Size of Struct B: %zu bytes\n", sizeof(struct B)); // 输出: 8
    return 0;
}
```
> **优化建议**：在定义结构体时，将空间占用大或相同的成员尽量排在一起，可以有效减少由于内存对齐带来的空间浪费。

---

## 五、 综合实战案例：学生信息管理系统

以下是一个结合了 **结构体定义、typedef、结构体数组、指针传参、动态查找修改** 的完整、可运行示例。

```c
#include <stdio.h>
#include <string.h>

#define MAX_STUDENTS 100

// 定义单个学生结构体
typedef struct {
    int id;
    char name[30];
    float score;
} Student;

// 定义班级结构体（包含结构体数组）
typedef struct {
    Student students[MAX_STUDENTS];
    int count;
} Class;

// 函数原型声明
void addStudent(Class *c, int id, const char *name, float score);
void printClass(const Class *c);
Student* findHighestScore(Class *c);

int main() {
    Class myClass;
    myClass.count = 0; // 初始化学生计数器

    // 添加测试数据
    addStudent(&myClass, 101, "Alice", 88.5);
    addStudent(&myClass, 102, "Bob", 94.5);
    addStudent(&myClass, 103, "Charlie", 79.0);

    // 打印班级名册
    printf("=== Class List ===\n");
    printClass(&myClass);

    // 查找并输出最高分获得者
    Student *topStudent = findHighestScore(&myClass);
    if (topStudent != NULL) {
        printf("\n=== Top Student ===\n");
        printf("ID: %d | Name: %s | Score: %.1f\n", 
               topStudent->id, 
               topStudent->name, 
               topStudent->score);
    }

    return 0;
}

// 往班级中添加学生
void addStudent(Class *c, int id, const char *name, float score) {
    if (c == NULL || c->count >= MAX_STUDENTS) {
        printf("Error: Class is full or invalid pointer.\n");
        return;
    }
    
    Student *s = &c->students[c->count];
    s->id = id;
    // 使用安全的字符串复制，并手动添加结束符
    strncpy(s->name, name, sizeof(s->name) - 1);
    s->name[sizeof(s->name) - 1] = '\0';
    s->score = score;
    
    c->count++;
}

// 打印班级所有学生信息（只读）
void printClass(const Class *c) {
    if (c == NULL || c->count == 0) {
        printf("No student records found.\n");
        return;
    }
    for (int i = 0; i < c->count; i++) {
        printf("ID: %d \t| Name: %-10s \t| Score: %.1f\n", 
               c->students[i].id, 
               c->students[i].name, 
               c->students[i].score);
    }
}

// 寻找成绩最高的学生，返回其结构体指针
Student* findHighestScore(Class *c) {
    if (c == NULL || c->count == 0) {
        return NULL;
    }
    
    int maxIndex = 0;
    for (int i = 1; i < c->count; i++) {
        if (c->students[i].score > c->students[maxIndex].score) {
            maxIndex = i;
        }
    }
    // 返回对应的结构体地址，避免复制大块数据
    return &c->students[maxIndex];
}
```