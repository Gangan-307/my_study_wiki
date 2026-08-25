# ESPC2-M1 / TJ22F V1.1 —— PHY 校准数据验证与重校准 作业指导书

**适用**：ESPC2-M1（ESP8684 / ESP32-C2，PCB 天线，2MB 或 4MB 内嵌 flash）装于 TJ22F V1.1 客户板，模组作 SPI 从机 + UART，EN 由主板 FEN 驱动，IO9 有下载按键，TX0/RX0 已引出。
**回答两个问题**：① 怎么验证"partial 基于 NVS 中的 full cal 数据、partial 结果永不回写 NVS"；② 表现不好的模组怎么重新校准。
**标注约定**：`[待现场确认]` = 本文未在一手资料上核实，上台面前必须自己验一遍，禁止当成既定事实写进对客报告。

---

# 0 开工前的三条红线

| # | 红线 | 违反后果 | 硬性要求 |
|---|---|---|---|
| **R1** | **先整片备份再动任何东西** | 坏 cal_data 绑定本芯片 MAC，擦掉就再也造不出来；§6 的可逆复现（唯一的因果证据）永久断链；擦写中途掉电会把唯一物证变砖 | 必须先过 §2 的 **G-BACKUP 闸门**（efuse 检查 + 两遍读 SHA256 一致 + nvs 单独导出可解析 + 异地留存）。闸门未过，本文所有写/擦命令一律禁止执行 |
| **R2** | **擦 NVS 会抹掉应用数据** | `erase_region` / `erase_partition` 清的是整个 nvs 分区：Wi-Fi 配网、序列号、产测标记、云平台三元组/证书（一机一密不可再生则**直接报废**）、OTA 状态全没 | 第一手段固定用 **B1（`esp_phy_erase_cal_data_in_nvs()` 工装固件，只擦 `phy` 命名空间）**；A1/A2 只在"已列出全部命名空间并逐条与客户确认可丢"+"G-BACKUP 已过"两条同时成立时才允许 |
| **R3** | **重校准必须在受控好条件下做，否则只是写入一份新的坏数据** | full cal 的结果会被**永久写回 NVS** 并被之后每次 partial cal 复用；坏条件重校 = 新坏数据覆盖旧坏数据，样品的诊断价值同时归零 | 必须先过 §4.1 的环境条件清单。乐鑫 Kconfig 原文点名两种校坏情形：`1.If your board is easy to be booted up with antenna disconnected. 2.Because of your board design, each time when you do calibration, the result are too unstable.` |

## 0.1 三条追加红线（本项目专属，同等强制）

| # | 红线 | 说明 |
|---|---|---|
| **R4** | **不可补做的取证排在最前** | 顺序固定为：物理存证（含外壳内侧对应天线位置微距照片）→ X-ray → 无损物理检查（罩顶平面度、外壳压合印痕）→ G-BACKUP → 才允许电学写入。**拆焊换板（§3.4）、连续发射（§5）、按压/加热一律排在 X-ray 之后** |
| **R5** | **禁止任何形式的全网自动擦校准 / 自动重校 / 自动回写 cal_data 的 OTA** | 全网 OTA 擦校准 = 让每台设备在客户真实恶劣现场（软胶壳内、戴手套、贴人手、表面 50~70 ℃）各做一次 full cal，是**批量制造坏校准数据的最短路径**；同时会把现场上千套设备未来所有失效样品的原始 cal_data 在人介入前抹掉。允许的只有三件：只读上报 cal_version/cal_mac/cal_data 摘要；后台逐台人工触发；失效品回收 SOP 写明"不要重启、不要触发任何维护命令" |
| **R6** | **基准良品永不写入** | 被指定为同龄对照的良品（FA-OK-001~003）只做无损测量与 cal_data 导出比对，**禁止改固件、擦 NVS、拆装、加热、按压**——它们保留的出厂原始 cal_data 是字节级离群比对的唯一基准。一切破坏性动作用另取的**牺牲良品**承担 |

## 0.2 每次写 flash 前的四问（TJ22F 专属，逐条口头确认后才按回车）

| 问 | 要点 | 不满足怎么办 |
|---|---|---|
| ① efuse 干净吗？ | `SPI_BOOT_CRYPT_CNT` / `SECURE_BOOT_EN` / 安全下载模式**全未使能** | 任一使能 → **立即停手**。读出的是密文，明文回写会砖；`nvs_tool.py` 也无法解析（该工具确无解密能力） |
| ② EN / FEN 谁在控？ | 模组 EN 由主板大 BGA 的 FEN 驱动。擦写中途主机复位或重新驱动 FEN → 模组在 flash 擦除中途掉电。乐鑫检查表原文：电源不稳会 *cause flash erase operations to occasionally fail to complete*，而 cal_data 就在同一颗 flash 上 | 优先断开 FEN→EN 的 R110（使 EN 只由 4.7k 上拉 + 外部控制），或把主机保持在复位态 |
| ③ strapping 安全吗？ | ESP32-C2 的 strapping 是 **GPIO8 + GPIO9**。**ESPC2-M1 未引出 IO8，模组内部 GPIO8 的处理目前未知**；`GPIO8=0 且 GPIO9=0` 是乐鑫点名的无效组合（*triggers unexpected behavior and should be avoided*） | 先查我方模组内部原理图确认（几分钟的事）；确认不了就**不手动按 IO9**，改用 esptool 自动复位控制 |
| ④ 供电稳吗？ | 稳压电源限流 ≥1A，就近并 100µF + 0.1µF，全程不拔插 USB 线；SPI/UART 与主板 BGA 不得争总线 | 用电脑 USB 口供电做写入 = 赌运气 |

**写后必检**：每条写/擦命令执行完，立刻回读该区域与预期镜像比对 SHA256；**比对不过就地停手，不要上电**。

## 0.3 牺牲品闭环预演（与 G-BACKUP 并列的强制闸门）

对故障样品动手前，必须在**牺牲良品**上把本轮真正要用的全部写入动作原样跑通一遍：

```
备份 → 烧 B1 工装固件 → 擦 phy → 烧回客户 app → erase_region 擦 nvs
     → 回灌 nvs 备份 → 烧 cert_test → 整片回写
```

**通过判据**：回写后能正常启动、能连 AP、RSSI 与最初基线差 <3 dB。每条命令的实际输出全文贴进工程笔记。**预演不通过，禁止对故障样品动手。**

---

# 1 先确认环境（10 分钟）

> ⚠ **客户可能用自定义分区表，一切偏移必须从实际分区表读，不得用默认值。** 本文出现的 `0x9000 / 0x6000` 一律是占位符。

## 1.1 第一条命令：钉死 esptool 版本与命令风格

```powershell
esptool.py version          # IDF v5.0/v5.1 自带的多为 esptool v4.x → 命令用下划线
esptool version             # 独立安装的 v5.x → 命令用连字符
idf.py --version
```

把结果**写在工位卡上，全程只用对应的一套**。v5 已把所有命令由 `_` 改为 `-`（`write_flash`→`write-flash`），入口名由 `esptool.py`→`esptool`；旧下划线名仍可用但会告警、下个大版本移除。

配套差异（照抄错版本会直接 unrecognized arguments）：

| 项 | esptool v4.x | esptool v5.x |
|---|---|---|
| 命令名 | `read_flash` / `write_flash` / `erase_region` / `image_info` | `read-flash` / `write-flash` / `erase-region` / `image-info` |
| app 描述符 | `image_info --version 2 app.bin` | `image-info app.bin`（**`--version` 已完全移除**） |
| 复位选项 | `--before default_reset` | `--before default-reset` |
| efuse 工具 | `espefuse.py summary` | `espefuse summary` |
| 强制擦除 | `--force` 需较新版本，先 `erase_region --help` 确认存在 | 同左 |

`python -m esptool ...` 这种模块入口形式是否可用 `[待现场确认]`——统一以 `esptool.py version` 的结果为准。

## 1.2 定 IDF 版本（后面所有日志判据的前提）

| 方法 | 命令 / 做法 | 说明 |
|---|---|---|
| **A（最准，推荐）** | 从整片备份切出 app 分区，读 `esp_app_desc_t` | `esp_app_desc_t` 位于 app 分区起始 +0x20，含 `char idf_ver[32]`。**决定 phy_init.c 行为的是 app 的版本** |
| B（快，但有坑） | 115200 抓完整启动日志，看第一行 `ESP-IDF vX.Y.Z 2nd stage bootloader` | bootloader 源码是 `ESP_EARLY_LOGI(TAG, "ESP-IDF %s 2nd stage bootloader", IDF_VER);` —— **IDF_VER 是 bootloader 编译时的宏**。客户若只 OTA 过 app 未更新 bootloader，这个版本号与 app 的 idf_ver 不一致。**两者不一致时以 app 为准，并把这个不一致本身记为一条线索** |
| C（最省事） | 直接问客户要 sdkconfig + IDF tag + 编译用的 esp_phy 源码 | 若客户基于某 tag 打过私有 patch，phy_init.c 可能被改过 |

同一行 `bootloader_print_banner()` 还会打印 `compile time ...` 与 `chip revision: v%d.%d` —— **顺手记下 chip revision**（不同 eco 版本 PHY 库行为可能有差异）。

```powershell
# 方法 A（先切后读；app 偏移用 §1.4 实测值，勿照抄 0x10000）
python -c "d=open(r'E:\rfcal\00_backup\BAD_full.bin','rb').read(); open(r'E:\rfcal\02_idfver\app.bin','wb').write(d[0x10000:0x10000+0x150000])"
esptool.py image_info --version 2 E:\rfcal\02_idfver\app.bin      # v4 写法
```

**版本分支门槛（硬性）**：

| 定版结果 | 处理 |
|---|---|
| v5.0 / v5.1 | 本文全部判据直接适用（两版 phy_init.c 的写回条件与两条关键日志串**逐字相同**，已核实） |
| v5.2 ~ master | 主干一致，但 `PHY enable improve rx 11b` 等日志仅 master 有，逐条核对该版本源码后再用 |
| **v4.1 ~ v4.4** | **暂停执行 §3.6 / §3.2 的日志判据**。v4.x 的写回条件是两子句形式、日志是小写 `saving new calibration data because of checksum failure, mode(%d)` 且级别为 **W**，与 v5 完全不同 —— 但本轮**未独立复核 v4.x 分支** `[待现场确认]`。先按定出的具体 tag 抓一次该版本 phy_init.c 原文核对，再继续。跨版本最稳的抓手 `failed to load RF calibration data (0x%x), falling back to full calibration` 在 v5.0/v5.1/master 已逐字确认一致，可先行使用 |

## 1.3 读 phy_version、芯片版本、MAC

```powershell
esptool.py --chip esp32c2 -p COM7 -b 115200 flash_id      # flash 容量（2MB/4MB 定死）
esptool.py --chip esp32c2 -p COM7 -b 115200 read_mac      # 模组身份证，抄进记录表
```

`phy_version` 来自开机日志 `I (xxx) phy_init: phy_version xxxx,...`（全版本一致），用于 §3.5 与 §4.5 的版本比对。

## 1.4 读分区表，定位 nvs（三路互证）

```powershell
# 路径 A（离线，从整片备份里切，最安全，不碰硬件）
python -c "d=open(r'E:\rfcal\00_backup\BAD_full.bin','rb').read(); open(r'E:\rfcal\01_ptable\pt.bin','wb').write(d[0x8000:0x8000+0xC00])"
python $env:IDF_PATH\components\partition_table\gen_esp32part.py E:\rfcal\01_ptable\pt.bin E:\rfcal\01_ptable\pt.csv
type E:\rfcal\01_ptable\pt.csv

# 路径 B（在线读）
esptool.py --chip esp32c2 -p COM7 read_flash 0x8000 0xC00 E:\rfcal\01_ptable\pt_online.bin

# 路径 C（parttool 直接问设备，需 IDF 环境）
python $env:IDF_PATH\components\partition_table\parttool.py --port COM7 get_partition_info --partition-name nvs --info offset size

# 路径 D（零成本旁证）：开机日志里 bootloader 会打印分区表清单
```

分区表默认在 0x8000、长 0xC00（占整个 0x1000 扇区）；若客户改过 `CONFIG_PARTITION_TABLE_OFFSET`，`parttool` 加 `-o 0x...`。

**三条必须执行的判读规则（漏了会得出方向相反的结论）**：

| 情形 | 判读 |
|---|---|
| 分区表里有**多个** data/nvs 分区（另有 nvs_key 或第二个 nvs） | phy 数据只在 `nvs_flash_init()` 使用的那个**标签为 nvs** 的分区里。停下来问客户哪个是，拿错会得到"phy 命名空间不存在"的假象 |
| 分区表里**不存在**标签为 nvs 的分区 | `esp_phy_load_cal_data_from_nvs` 每次开机必然失败 → **每次都 full cal**。这本身就是独立根因，本议题的整个前提不成立，转向该线 |
| 存在 nvs_keys 分区 / 开了 NVS 加密 | `nvs_tool.py` **明确不支持加密分区** → §3.2 路径B、§4.2 的 A4 全部不可行，只能走 B1 + 日志判定（§3.6） |

## 1.5 读 sdkconfig 关键项（拿不到 sdkconfig 就从 build/config/sdkconfig.h 查）

| 配置项 | 期望值 | 不符时的含义 |
|---|---|---|
| `CONFIG_ESP_PHY_CALIBRATION_AND_DATA_STORAGE` | `y`（默认） | **=n → 整段 `#ifdef` 不编译，每次开机都 `PHY_RF_CAL_FULL` 且从不碰 NVS**。此时"擦 NVS 重新校准"完全无效，本议题的前提不成立 |
| `CONFIG_ESP_PHY_CALIBRATION_MODE` | `0`（PARTIAL，默认） | 映射：`0=PARTIAL / 1=NONE / 2=FULL`。=2 说明客户已在做全校准 |
| `CONFIG_ESP_PHY_IMPROVE_RX_11B` | 期望 `n` | **=y 会主动牺牲 OFDM（11g/n）接收性能换 11b**（Kconfig 原文：*enable this option will sacrifice Wi-Fi OFDM receive performance*）。"表现不好"可能是配置使然而非模组坏，**必须在怀疑硬件之前排除**。⚠ 该选项在 v5.1 的 phy_init.c 里**没有任何日志打印**（那条 `ESP_LOGW(TAG, "PHY enable improve rx 11b")` 只有 master 有）——**不要靠抓日志判定，只能查 sdkconfig** |
| `CONFIG_LOG_DEFAULT_LEVEL` / `CONFIG_LOG_MAXIMUM_LEVEL` | 见 §3.6 | 设成 ERROR/NONE 时 §3.6 的判据一条都看不到 |
| `CONFIG_ESP_PHY_MAX_WIFI_TX_POWER` / `REDUCE_TX_POWER` / 国家码 | 良品与故障品**必须完全一致** | 不一致则所有 A/B 对比作废 |

**C2 专属背景**（不放进可执行步骤，仅供判读）：`SOC_PHY_IMPROVE_RX_11B` 全版本存在；`SOC_PHY_COMBO_MODULE` 在 v5.0 的 esp32c2 soc_caps.h 中**缺失**、v5.1+ 才有，v5.1+ 会多调 `phy_init_param_set(1)` —— 客户若从 v5.0 升到 v5.1，C2 的 PHY 行为会变，这是升级排查时的混淆变量。除此之外 phy_init.c 中**没有任何 C2 专用分支**，校准主流程与其他芯片一致。

---

# 2 整片备份与留证（G-BACKUP 闸门，必须最先做）

> 前置：§0.2 四问已确认、§0.1-R4 的物理存证与 X-ray 已完成。

## 2.1 目录结构（统一采用，勿另起炉灶）

```
E:\rfcal\
  00_backup\   BAD_full.bin + .sha256.txt, GOOD_full.bin + .sha256.txt, nvs_BAD.bin, read_mac.txt
  01_ptable\   pt.bin, pt.csv, parttool_out.txt
  02_idfver\   image_info 输出, 字符串扫描结果, sdkconfig 摘录
  03_P1\  04_P2\  05_P3\  06_P4\
  07_recal\    重校准前后的 nvs 与日志
  08_measure\  原始 CSV / 波形 / 照片
  nvs_hashes.txt   （全过程哈希流水账，带时间戳）
  MANIFEST.csv     （全目录 SHA256 清单）
  README.md        （每步命令原文 + 判据 + 实际观测值）
```

## 2.2 命令

```powershell
mkdir E:\rfcal\00_backup

# ① efuse 检查（闸门第一条，不过就停）
espefuse.py -p COM7 summary   > E:\rfcal\00_backup\efuse.txt
#   查 SPI_BOOT_CRYPT_CNT / SECURE_BOOT_EN / 安全下载模式，任一使能 → 停手

# ② 身份信息
esptool.py --chip esp32c2 -p COM7 -b 115200 flash_id  > E:\rfcal\00_backup\flash_id.txt
esptool.py --chip esp32c2 -p COM7 -b 115200 read_mac  > E:\rfcal\00_backup\read_mac.txt

# ③ 整片备份，读两遍（推荐用 ALL，自动按实际容量，规避 2MB/4MB 填错）
esptool.py --chip esp32c2 -p COM7 -b 460800 read_flash 0 ALL E:\rfcal\00_backup\BAD_full.bin
esptool.py --chip esp32c2 -p COM7 -b 460800 read_flash 0 ALL E:\rfcal\00_backup\BAD_full_2.bin

# ④ 双 SHA256 比对
(Get-FileHash -Algorithm SHA256 E:\rfcal\00_backup\BAD_full.bin).Hash   | Tee-Object E:\rfcal\nvs_hashes.txt -Append
(Get-FileHash -Algorithm SHA256 E:\rfcal\00_backup\BAD_full_2.bin).Hash | Tee-Object E:\rfcal\nvs_hashes.txt -Append
fc /b E:\rfcal\00_backup\BAD_full.bin E:\rfcal\00_backup\BAD_full_2.bin

# ⑤ 单独导出 nvs 分区（偏移用 §1.4 实测值）
esptool.py --chip esp32c2 -p COM7 -b 460800 read_flash 0x9000 0x6000 E:\rfcal\00_backup\nvs_BAD.bin

# ⑥ 基准良品同样备份一份（只读，不做任何写入 —— R6）
esptool.py --chip esp32c2 -p COM8 -b 460800 read_flash 0 ALL E:\rfcal\00_backup\GOOD_full.bin
```

> **注意**：`Get-FileHash ... | Tee-Object` 直接管道会写入格式化表格文本（含表头），后续脚本无法解析 —— 必须取 `.Hash` 字段，如上。

## 2.3 闸门通过判据（四条全中才算过）

| # | 判据 |
|---|---|
| 1 | efuse 摘要确认 flash 加密 / Secure Boot / 安全下载模式**全未使能** |
| 2 | 两遍整片读的 SHA256 **完全一致**，且文件大小 = 2097152（2MB）或 4194304（4MB） |
| 3 | 单独导出的 nvs 镜像能被 `nvs_tool.py` 成功解析（反证备份确实含 NVS） |
| 4 | 两份备份已异地留存 + SHA256 已抄送客户 |

## 2.4 回滚命令（出事时用，现在不要执行）

```powershell
esptool.py --chip esp32c2 -p COM7 -b 460800 write_flash 0 E:\rfcal\00_backup\BAD_full.bin
```

## 2.5 数据处置（同等强制）

- 整片备份含客户 **Wi-Fi SSID/密码、云平台三元组、设备证书与私钥、序列号**。
- **两份备份只存放在受控内部存储（离线硬盘 / 公司内网加密目录），禁止上传任何公有云或个人网盘。** 登记保管人、留存期限、销毁节点。
- **对外只交付**：nvs 分区的 SHA256、`phy` 命名空间的 cal_version/cal_mac、cal_data 的"长度 + 哈希"摘要。**不给原始镜像，不给 cal_data 的 base64 原文**（内容不可解读，给了只会引发误读）。
- 索样时同步向客户书面说明"会读取整片 flash"并取得书面同意。

---

# 3 验证问题一：证明"partial 不回写 NVS、full 才写"

## 3.1 原理（一句话 + 源码写回条件原文）

**一句话**：正常开机时 NVS 读成功且 PHY 库判定数据有效，代码走的是 `else { err = ESP_OK; }` 分支，**根本不调用 `esp_phy_store_cal_data_to_nvs()`**；只有"加载失败"或"校验失败"才会写回。

**写回条件逐字原文**（release/v5.1 与 v5.0 的 `components/esp_phy/src/phy_init.c` 已核实**逐字相同**）：

```c
esp_phy_calibration_mode_t calibration_mode = CONFIG_ESP_PHY_CALIBRATION_MODE;
if (esp_rom_get_reset_reason(0) == RESET_REASON_CORE_DEEP_SLEEP) {
    calibration_mode = PHY_RF_CAL_NONE;
}
esp_err_t err = esp_phy_load_cal_data_from_nvs(cal_data);
if (err != ESP_OK) {
    ESP_LOGW(TAG, "failed to load RF calibration data (0x%x), falling back to full calibration", err);
    calibration_mode = PHY_RF_CAL_FULL;
}
ESP_ERROR_CHECK(esp_efuse_mac_get_default(sta_mac));
memcpy(cal_data->mac, sta_mac, 6);
esp_err_t ret = register_chipv7_phy(init_data, cal_data, calibration_mode);
if (ret == ESP_CAL_DATA_CHECK_FAIL) {
    ESP_LOGI(TAG, "Saving new calibration data due to checksum failure or outdated calibration data, mode(%d)", calibration_mode);
}

if ((calibration_mode != PHY_RF_CAL_NONE) && ((err != ESP_OK) || (ret == ESP_CAL_DATA_CHECK_FAIL))) {
    err = esp_phy_store_cal_data_to_nvs(cal_data);
} else {
    err = ESP_OK;
}
```

配套已核实事实：`TAG = "phy_init"`；命名空间/键 `"phy"` / `cal_version` / `cal_mac` / `cal_data`；结构体 `version[4] + mac[6] + opaque[1894] = 1904` 字节；枚举 `PARTIAL=0 / NONE=1 / FULL=2`；`esp_phy_erase_cal_data_in_nvs()` 实现确为 `nvs_open("phy", NVS_READWRITE)` → `nvs_erase_all()` → `nvs_commit()`（**只清 phy 命名空间**）。

## 3.2 实验 P1：反复冷启动后 NVS 字节不变 → 实证 partial 不回写

| 项 | 内容 |
|---|---|
| **目的** | 在客户自己的固件、自己的板子上证明"partial 结果不回写"，不要求客户信任任何源码解读 |
| **被测** | 故障模组（在 TJ22F 上）+ 一颗**基准良品**平行对照（良品只读，不写 —— R6） |
| **耗时** | 热身 5 min + 6 次循环 15 min + 取样比对 5 min ≈ **25 分钟** |

**步骤**

```powershell
# 步骤 0：热身 2 次冷启动并完成配网/连 AP，让应用自身的 NVS 写入先稳定。这两次不计入统计。

# 步骤 1：基线取样（取样脚本 dump_nvs.ps1 见 §9.3）
powershell -ExecutionPolicy Bypass -File E:\rfcal\dump_nvs.ps1 -Port COM7 -Tag P1_base
python $NVSTOOL -f json E:\rfcal\03_P1\nvs_P1_base.bin > E:\rfcal\03_P1\nvs_P1_base.json

# 步骤 2：N=6 次完整冷启动循环
#   每次：整板断电 ≥5s（示波器确认 3V3 归零）→ 上电 → 全程抓日志 → 连上 AP → 收发 ≥30s → 断电
#   日志按次存盘 log_P1_1.txt ... log_P1_6.txt
#   ⚠ 刻意覆盖不同场景：连得上 AP / 连不上 AP / 中途掉线重连

# 步骤 3：终态取样
powershell -ExecutionPolicy Bypass -File E:\rfcal\dump_nvs.ps1 -Port COM7 -Tag P1_after
python $NVSTOOL -f json E:\rfcal\03_P1\nvs_P1_after.bin > E:\rfcal\03_P1\nvs_P1_after.json

# 步骤 4：三级比对
python E:\rfcal\diff_nvs.py  E:\rfcal\03_P1\nvs_P1_base.bin  E:\rfcal\03_P1\nvs_P1_after.bin
python E:\rfcal\calhash.py   E:\rfcal\03_P1\nvs_P1_base.json E:\rfcal\03_P1\nvs_P1_after.json
Select-String -Path E:\rfcal\03_P1\log_P1_*.txt -Pattern "phy_init|calibration|phy_version"
```

**判据**

| 级别 | 判据 | 权重 |
|---|---|---|
| **主判据（唯一裁决）** | `phy:cal_version` / `cal_mac` / `cal_data` 三键的哈希在 base 与 after **完全一致** | 结论只由这一条裁决 |
| 辅判据（日志） | 6 份日志里都**没有** `failed to load RF calibration data`、也**没有** `Saving new calibration data due to` | 交叉验证 |
| 辅判据（整片） | `diff_nvs.py` 输出 `IDENTICAL` | **加分项，不出现属正常** —— 应用与 `nvs.net80211` 几乎必然写入，磨损均衡还会改写页头。拿不到 IDENTICAL 绝不等于实验失败 |
| 反向判据 | 若 cal_data 哈希变了 → 去日志找那两条关键字，定位是 load 失败还是 CHECK_FAIL，那是另一个（更严重的）问题 |

**关键 caveat**

1. **必须是冷启动，不能是 deep sleep 唤醒**。源码里深睡唤醒被强制改成 `PHY_RF_CAL_NONE`，也不回写，但那不能算 partial 的证据。用开机日志首行的 `rst:0x1 (POWERON)` 逐次确认。
2. **每次取样会引入一次额外复位**：esptool 默认 `--after hard_reset`。要么加 `--after no_reset` 让芯片停在下载模式、由人工断电完成下一次冷启动；要么在记录表里把 dump 引发的复位单独计数，别把"6 次冷启动"这个说法写得不精确。
3. **整片哈希不是判据**（见上表）。必须用 `nvs_tool.py` 把 phy 命名空间单独提出来比对。
4. NVS 加密时路径B 直接失效，只能走 §3.6 日志判定。
5. 每次 dump 前务必断电而非软复位，避免 NVS 缓存未落盘。

## 3.3 实验 P2：擦除后开机 → NVS 出现新数据 → 实证 full 会写回

| 项 | 内容 |
|---|---|
| **目的** | P1 是阴性结果（什么都没变），单独拿出去会被质疑"是不是你的方法根本测不出变化"。P2 用**同一套测量方法**制造一次必然发生的写回，证明测量系统有灵敏度 |
| **被测** | **优先在牺牲良品上做**，不在唯一的故障样品上做 |
| **耗时** | 10~15 分钟 |

**做法（三选一，推荐度递减）**

| 做法 | 命令 | 风险 |
|---|---|---|
| **① 工装固件调 API（推荐）** | 烧 §4.3 的 B1 工装固件，串口确认后触发 `esp_phy_erase_cal_data_in_nvs()` | 语义明确、**零误伤**、只擦 phy |
| ② 擦整个 nvs 分区 | `esptool.py --chip esp32c2 -p COM7 erase_region 0x9000 0x6000` | 丢配网/密钥 |
| ③ 字节翻转破坏校验 | 见下 | **易误伤，需三重断言** |

**做法③ 的正确姿势（原始"`d.find(mac)` 取第一处"的写法不可用）**
MAC 在 NVS 镜像里至少出现两处（`cal_mac` 条目本身、`cal_data` blob 内偏移 +4），还可能出现在 `nvs.net80211` 或客户命名空间（很多产品把 MAC 当设备 ID 存）；条目物理顺序取决于写入历史与磨损均衡，**不保证 phy 的排在最前**。命中错位置时脚本不会报错，结果是静默损坏客户数据、而 phy 数据完好 → 你会得到"阳性对照没做出来"的假象并去怀疑机制。

正确做法：
1. 先 `python $NVSTOOL nvs_orig.bin -d all --color never > all.txt`，从中确认 phy 命名空间下 `cal_mac` 条目的**确切页号与条目偏移**，硬编进脚本；
2. 翻转前三重断言：① 该偏移落在 phy 命名空间的条目范围内；② 翻转前后除该字节外整个镜像逐字节相同；③ 翻转后重新用 `nvs_tool.py -i` 解析，确认报出的完整性错误**确实指向 phy** 而不是别的命名空间；
3. 写入前先用 §1.2 的字符串扫描确认客户固件的 `nvs_flash_init()` 里**有没有**自动 `nvs_flash_erase()` 分支（有的话被破坏的 NVS 可能整片被清）。

**判据（四条全中即证明写回路径存在且工作正常）**

| # | 判据 |
|---|---|
| ① | 开机日志出现 `W (xxx) phy_init: failed to load RF calibration data (0x....), falling back to full calibration` —— 默认日志级别就能看到的 W 级日志，是 full cal 的铁证 |
| ② | 该次开机耗时比平常多约 **100 ms**（官方：full cal 比 partial 多约 100ms） |
| ③ | 重新 dump 后 `phy:cal_data` 内容与 P1 基线**不同**，`cal_mac` 为正确 MAC，`cal_version` 为当前 PHY 版本 |
| ④ | 再冷启动 N 次，cal_data 又重新"纹丝不动" —— 回到 P1 的行为 |

**复原**：实验后必须把原 nvs 写回并 dump 确认哈希回到 orig，别把残留留给客户。

## 3.4 实验 P3：模组换板后 cal_data 不变 → 实证"跟随模组走"

> **这条直接回应客户"故障跟随模组走"的交叉验证观察，是整个分析里最有说服力的一条。**
> ⚠ 涉及拆焊 = 不可逆物理改动，**必须排在 X-ray 与原始形态取证之后**；录像 + 热电偶记录峰值温度 **≤240 ℃**。

| 项 | 内容 |
|---|---|
| **目的** | 把客户的观察与机制对上：cal_data 存在模组自己的内嵌 flash 的 NVS 里，换板不换模组，数据原封不动 → **一次坏校准会被模组永久记住并带到任何板子上，永不自愈** |
| **耗时** | 20~40 分钟（主要花在拆焊与射频复测） |

```powershell
# A 板取样（复用 P1 基线即可）
powershell -File E:\rfcal\dump_nvs.ps1 -Port COM7 -Tag P3_boardA
esptool.py --chip esp32c2 -p COM7 read_mac      # 模组身份证

# 同一颗模组拆焊到 B 板 → B 板取样
powershell -File E:\rfcal\dump_nvs.ps1 -Port COM9 -Tag P3_boardB
esptool.py --chip esp32c2 -p COM9 read_mac      # MAC 必须与上面一致

python E:\rfcal\diff_nvs.py E:\rfcal\05_P3\nvs_P3_boardA.bin E:\rfcal\05_P3\nvs_P3_boardB.bin
```

**2×2 表格（射频列必须填 §5 口径下的四个数，不许填"好/差"）**

| 组合 | MAC | cal_data 哈希 | R̄ (dB) | s | n | 95% CI |
|---|---|---|---|---|---|---|
| 故障模组 + A 板 | | | | | | |
| 故障模组 + B 板 | | | | | | |
| 良品模组 + A 板 | | | | | | |
| 良品模组 + B 板 | | | | | | |

**判据**

| # | 判据 |
|---|---|
| ① | B 板读出的 `phy:cal_data` 与 A 板**逐字节相同** → 校准数据物理上存在于模组内嵌 flash，与客户板无关 |
| ② | 两次 `read_mac` 一致 → 确认是同一颗模组 |
| ③ | 2×2 表中"差"严格跟随**模组**而非跟随板 → 排除板级 RF 走线/匹配/电源 |
| ④ | **拆焊未引入新变量**：换板前后同板同条件测量差 ≤3 dB（不满足则本实验作废，拆焊本身已改变样品） |
| ⑤ | 良品的 `cal_version` 与故障品**相同**（同固件同 PHY 库）但 `cal_data` 内容不同 —— 这是正常的，逐模组校准本就该不同 |

⚠ `cal_data` 的 1894 字节 opaque 是闭源私有格式，**只能做"相同/不同"的同一性比对，绝不能用"和良品的 cal_data 不一样"来判定故障**。本实验唯一硬的结论是"跟随模组"。

## 3.5 实验 P4：换 PHY 库版本触发重校（可选，最后做）

| 项 | 内容 |
|---|---|
| **目的** | 验证官方五条 full cal 触发条件里最有工程价值的一条：**客户每次升级 IDF 并 OTA，全网设备会自动重校一次** —— 既是"免费自愈路径"，也是 §4.5 / §7 要追的风险点 |
| **被测** | **一颗牺牲良品**。**绝不能在故障模组上做** —— 一旦触发重校，原始 cal_data 就没了，§6 永久失效 |
| **耗时** | 1~2 小时（大头是装第二套 IDF 与首次编译） |

```powershell
# 1) 用 IDF 版本 X 编译官方最小例程（不用客户固件，减少变量），首次开机必然 full cal
# 2) 稳定后取样，记下 cal_version 数值
# 3) 换 IDF 版本 Y（跨度要大，如 v5.1.x → v5.3.x），只重编 app
#    ★ 必须只烧 app：idf.py -p COM8 app-flash monitor
#    一旦 idf.py flash 带 erase 或手滑 erase_flash，实验就退化成 P2，证明不了 PHY 版本这个因素
# 4) 冷启动抓日志，再取样比对
```

**判据（①~④ 全中即证明）**：① 两版 `phy_version` 日志串不同；② 版本 Y 首次开机出现 `falling back to full calibration`；③ `cal_version` 键的数值变化；④ `cal_data` 哈希变化。

**若 phy_version 两版一样**（小版本升级常见）→ 本实验无效，需换跨度更大的两版重做。**这本身也是有用结论：小版本升级不一定触发重校，不能指望靠升级 IDF 自动修复现场设备。**

## 3.6 从串口日志判定本次是 partial 还是 full

**已核实的判定关键字（TAG 全部是 `phy_init`，v5.0 与 v5.1 逐行一致）**

| 日志级别 | 逐字字符串 | 含义 |
|---|---|---|
| **W**（默认可见） | `failed to load RF calibration data (0x%x), falling back to full calibration` | 从 NVS 加载失败 → 本次强制 **FULL**，**一定回写 NVS**。跨 v4.1~master 逐字一致，最稳的抓手 |
| **I**（默认可见） | `Saving new calibration data due to checksum failure or outdated calibration data, mode(%d)` | `register_chipv7_phy()` 返回 `ESP_CAL_DATA_CHECK_FAIL` → **回写 NVS**。括号里数字：**0=PARTIAL / 1=NONE / 2=FULL** |
| I（默认可见） | `phy_version xxxx,...` | PHY 库版本，P4 / §4.5 用它对比 |
| **E**（默认可见） | `calibration data MAC check failed: expected xx:xx.., found xx:xx..` | MAC 不匹配 → 也是一条硬件线索（eFuse 读错/供电异常） |
| **E**（默认可见） | `failed to get cal_data(0x%x)` | blob 读取失败 |

**判定表（直接照抄给客户）**

| 本次开机日志 | 结论 |
|---|---|
| 上面两条 W/I 都没有 | **partial calibration（或深睡 NONE），不回写 NVS** |
| 有 `failed to load RF calibration data` | full calibration，**回写 NVS** |
| 无上条但有 `Saving new calibration data due to` | 数据校验失败，**回写 NVS** |

**要查"为什么加载失败"必须开 DEBUG**（以下诊断行都是 `ESP_LOGD`，默认看不到）：
`failed to get cal_version (0x%x)` / `expected calibration data format %d, found %d` / `failed to get cal_mac (0x%x)` / `invalid length of cal_mac (%d)` / `invalid length of cal_data (%d)` / `failed to open NVS namespace (0x%x)`

开 DEBUG 的两种方式：

1. menuconfig → `Component config → Log output → Default log verbosity` 选 **Debug**；
2. 保留 INFO 默认但把 `Maximum log verbosity` 设为 Debug/Verbose，然后运行时只放开 phy：
   ```c
   esp_log_level_set("phy_init", ESP_LOG_DEBUG);   // 必须在 esp_wifi_init()/esp_wifi_start() 之前
   ```
   ⚠ `esp_log_level_set()` **无法**放开高于 `CONFIG_LOG_MAXIMUM_LEVEL` 的级别，方式 2 的两步缺一不可。

**常见错误码速查**：`0x1101` NOT_INITIALIZED（没调 nvs_flash_init）、`0x1102` NOT_FOUND（键/命名空间不存在 = 从未 full cal 过或被擦了）、`0x1103` TYPE_MISMATCH、`0x110c` INVALID_LENGTH、`0x110d` NO_FREE_PAGES、`0x110f` PART_NOT_FOUND、`0x1110` NEW_VERSION_FOUND。

**闭环判据**：判定为 full 的那些开机，NVS `cal_data` **必然变**；判定为 partial 的，**必然不变**。日志与字节两条通道 100% 对应 = 证据链闭合。

---

# 4 回答问题二：怎么给表现不好的模组重新校准

## 4.1 ⚠ 重校准的环境条件清单（条件不对就别做）

**校准发生的确切时刻**：擦除后的**下一次上电、第一次调用 `esp_wifi_init()` / 蓝牙初始化**时。"条件"指的是那一次上电前后几秒钟内的物理环境。之后再怎么摆放都不影响已存的数据。

### 4.1.1 ★ 装配状态裁决（三份材料曾互相冲突，此处拍死）

| 环节 | 状态 | 理由 |
|---|---|---|
| **做校准的那一次上电** | **半装配态**：屏蔽罩**装好**、外壳**打开**、模组置于非金属支架、天线净空 ≥5 cm、无人手靠近 | 屏蔽罩压迫 π 型匹配网络本身是嫌疑对象，**必须保持在位**；而外壳/人手/手套是每次都不同的随机负载，**不可作为校准基准**（正中 Kconfig 点名的"每次校准结果都不稳定"） |
| **验收复测** | **裸板态 + 整机装壳态 各做一遍，数据分开记录、禁止混算** | 裸板态用于对比良品基线（判断校准是否有效）；装壳态用于对比实际使用（判断产品是否可交付） |
| **输出量** | 把"裸板态 vs 装壳态的差值"本身作为一项输出 | 若差 **>6 dB** → 装壳态已失配，那是天线/匹配设计问题，**不是校准能补的**，另开条目（正解是用 VNA 在装壳态调 π 型匹配） |

> 澄清一处常见误引：乐鑫 FAQ"外接天线必须在上电前接好，因为模组上电自校准 including power calibration"的原意是**天线不能断开**，PCB 天线机型不存在断开，**不要用它论证必须装壳**。

### 4.1.2 逐条打勾再上电

| # | 条件 | 具体要求 |
|---|---|---|
| 1 | **天线** | PCB 天线端伸出板边悬空；天线正上/正下 ≥5 cm 无金属，离机箱/机柜 ≥10 cm；**上电瞬间不得手握、手指不得靠近净空区**；屏蔽罩装到位且焊接正常；不要在屏蔽箱里贴壁校准（吸波材料紧贴天线 = 异常负载），必须用时天线离内壁 ≥10 cm |
| 2 | **供电（校准那一次）** | **必须走产品自己的完整电源路径**（FB7 在位），稳压电源设 5.0 V / 限流 2 A 从板上 USB-C 喂电，让板载 LDO/DCDC 正常工作。**不要跳过板上电源直接往模组 3V3 灌电** —— 那样校出来的数据不代表产品实际电源环境。3.3 V ±5%、纹波 <80 mV、瞬时电流能力 ≥500 mA。示波器 AC 耦合探 3V3（探头地弹簧、20 MHz 带宽限制）确认纹波达标。**不要用电脑 USB 口或劣质充电头** |
| 3 | **温度** | 环境 20~30 ℃，模组自身温度已稳定 ≥10 min。**不要**刚从 50~70 ℃ 工作态拔下来立刻校准，也不要在空调/冷风口正对处 |
| 4 | **干扰** | 关掉 1~2 m 内的微波炉、蓝牙耳机、2.4G 无线鼠标接收器、密集 AP；复测要有位置固定、信道固定（选空闲信道 1 或 11）的参考 AP |
| 5 | **对照组** | 取 **2 片牺牲良品**（不是基准良品 —— R6）走完全相同的擦除+重校流程，作为"重校准这个动作本身是否安全"的对照 |
| 6 | **示波器同时抓 3V3 与 EN(FEN)** | **这一条比任何软件手段都值得先查**：若 FEN 上升沿与 3V3 建立时序不当，会在电源未稳时就开始校准 —— 这可能才是"每次校出坏数据"的真正根因 |

**判据**：重校后**牺牲良品对照组**性能不变或变好（±2 dB 内）→ 校准条件合格；任一片掉 >3 dB → **条件不合格，立刻停手回滚，重做条件**。

**最大的坑**：坏条件下重校只会写入一份新的坏数据，且原数据已被覆盖 —— 这就是 §2 备份不可省的原因。

## 4.2 路线对照表

| 路线 | 做法 | 重编译 | 丢应用数据 | 耗时 | 推荐度 | 适用场景 |
|---|---|---|---|---|---|---|
| **B1** | 工装固件调 `esp_phy_erase_cal_data_in_nvs()`，**只烧 app 分区** | 编一个独立小 app，**不改客户固件** | **否**（只擦 `phy` 命名空间） | 30~60 min（含编译） | **★★★★★ 首选** | **实验室 FA + 量产返修 + 现场维修，全场景正解** |
| **C2** | 回头查"故障前是否做过跨 IDF 版本 OTA" | 否（是排查） | 否 | 1 h | **★★★★★ 必做** | 可能直接解释整个案子，见 §4.5 / §7 |
| **B4** | 完整校准工装（擦→全校→复测→打基线→存档） | 同 B1 | 否 | 半天 | ★★★★☆ | 批量返修、需要留出货基线 |
| **A2** | `parttool.py erase_partition --partition-name=nvs` | 否 | **是（整个 nvs）** | 5 min | ★★★☆☆ | 有 IDF 环境；比 A1 少一个"填错地址"的风险 |
| **A1** | `esptool erase_region <nvs_off> <nvs_size>` | 否 | **是（整个 nvs）** | 5 min | ★★☆☆☆ | 只在"已确认 NVS 无不可再生数据"+"G-BACKUP 已过"时用 |
| **A4** | 导出 NVS → 人工剔除 phy → 重建 → 写回 | 否 | 否（但人工易错） | 2~4 h | ★★☆☆☆ | **仅当** NVS 有不可再生密钥 **且** 完全无法编译工装固件 |
| **A3** | `erase_flash` 全擦 + 重烧原固件 | 否 | **是（一切）** | 30 min | ★★☆☆☆ | 需同时排除固件/分区被写坏时 |
| **B2** | `CONFIG_ESP_PHY_RF_CAL_FULL=y`（每次开机全校） | **是** | 否 | 半天 | ★☆☆☆☆ | **只做诊断固件**，不量产常开 |
| **B3** | 关 `CONFIG_ESP_PHY_CALIBRATION_AND_DATA_STORAGE` | **是** | 否 | 半天 | ☆☆☆☆☆ | **本产品不要用**，见 §4.4 |
| **C1** | 改 MAC 触发全校 | — | — | — | ☆☆☆☆☆ | **不可行**：eFuse 只能 0→1 不可逆，改错模组身份永久报废；MAC 变了 DHCP 绑定/白名单/云平台绑定/售后追溯全失效。软件路径 `esp_base_mac_addr_set()` 同样需改固件，且严格劣于 B1，**没有任何理由选它** |

**为什么 B1 而不是 A1（裁决理由）**：A1 省下的是半天编译时间，赌上的是把物证连同客户不可再生的密钥一起抹掉。在"只有 1~2 片故障样品、可能是现场返修件、NVS 里可能有唯一的三元组"的前提下，这个权衡不成立。

**A1/A2 的准入前提（两条同时成立才允许）**：
1. 已用 `nvs_tool.py -d namespaces` 列出**全部**命名空间，并逐条与客户确认"丢了不会有不可再生的损失"。**出现看不懂的命名空间 → 一律按含不可再生密钥处理，改走 B1**。
2. G-BACKUP 闸门已通过。

**作业卡点名**：`idf.py erase-flash` / `esptool erase_flash` 在本案中**任何情况下都不许用**（A3 除外，且 A3 需先拿到客户原始 bootloader/分区表/app 三个 bin，否则擦完就变砖）。

## 4.3 推荐路线 B1 的完整分步操作

### 4.3.1 工装固件源码（已修掉两处致命缺陷）

```c
#include "nvs_flash.h"
#include "esp_phy_init.h"
#include "esp_system.h"
#include "esp_log.h"
#include "esp_wifi.h"
#include "esp_netif.h"
#include "esp_event.h"
#include "driver/uart.h"

static const char *TAG = "phycal";

void app_main(void)
{
    /* ---- 缺陷修复 1：绝不自动 nvs_flash_erase()（那会擦掉本工装承诺保护的一切） ---- */
    esp_err_t err = nvs_flash_init();
    if (err != ESP_OK) {
        ESP_LOGE(TAG, "nvs_flash_init failed: %s (0x%x) —— 停止，人工介入",
                 esp_err_to_name(err), err);
        while (1) { vTaskDelay(pdMS_TO_TICKS(1000)); }
    }

    ESP_LOGI(TAG, "phy lib version: %s", get_phy_version_str());

    /* ---- 自保 1：擦除前先把原始 cal 数据打到串口留档 ---- */
    esp_phy_calibration_data_t *cd = calloc(1, sizeof(esp_phy_calibration_data_t));
    err = esp_phy_load_cal_data_from_nvs(cd);
    if (err != ESP_OK) {
        ESP_LOGE(TAG, "load cal data failed: %s (0x%x) —— 停止，先查为什么读不到",
                 esp_err_to_name(err), err);
        while (1) { vTaskDelay(pdMS_TO_TICKS(1000)); }
    }
    ESP_LOG_BUFFER_HEX(TAG, cd, sizeof(esp_phy_calibration_data_t));   /* 1904 字节全量 hex */

    /* ---- 自保 2：必须由串口输入确认字符串触发，不许上电即擦 ---- */
    ESP_LOGW(TAG, "输入 ERASE 并回车以擦除 phy 校准数据；输入其它任意内容则跳过");
    char buf[16] = {0};
    /* …从 UART0 读一行到 buf，实现略… */
    if (strncmp(buf, "ERASE", 5) != 0) {
        ESP_LOGI(TAG, "已跳过擦除");
        while (1) { vTaskDelay(pdMS_TO_TICKS(1000)); }
    }

    err = esp_phy_erase_cal_data_in_nvs();      /* 只擦 "phy" 命名空间 */
    ESP_LOGI(TAG, "erase phy cal data: %s", esp_err_to_name(err));

    /* ---- 缺陷修复 2：不 esp_restart()（会构成无限重启死循环）
            改为在同一个 app 里直接初始化 Wi-Fi —— full calibration 就在这一刻发生 ---- */
    ESP_ERROR_CHECK(esp_netif_init());
    ESP_ERROR_CHECK(esp_event_loop_create_default());
    esp_netif_create_default_wifi_sta();
    wifi_init_config_t cfg = WIFI_INIT_CONFIG_DEFAULT();
    ESP_ERROR_CHECK(esp_wifi_init(&cfg));       /* ← full calibration 发生点 */
    ESP_ERROR_CHECK(esp_wifi_set_mode(WIFI_MODE_STA));
    ESP_ERROR_CHECK(esp_wifi_start());

    int8_t p = 0; esp_wifi_get_max_tx_power(&p);
    ESP_LOGI(TAG, "full cal done. phy_version %s, max_tx_power=%d (0.25dBm)",
             get_phy_version_str(), p);
    while (1) { vTaskDelay(pdMS_TO_TICKS(1000)); }   /* 停在这里等人工判定 */
}
```

> **两处修复的原因**：
> ① 原模板的 `if (err == ESP_ERR_NVS_NO_FREE_PAGES ...) { ESP_ERROR_CHECK(nvs_flash_erase()); }` 会擦掉整个 nvs 分区，正好抹掉 B1 承诺保护的东西；而故障样品的 NVS 本来就有较高概率处于异常状态，**这条分支在最需要保住数据的机器上最容易被触发**。
> ② 原模板的"擦完 `esp_restart()`"会让同一个 app 重启后再擦再重启，**无限循环，模组永远起不来**，工位上会当成"被擦砖了"。

### 4.3.2 编译与烧录（B1 最大的坑在这里）

**★ 坑：切 app 的偏移写法**
不要用 `d[0x10000:0x200000]` 这种"从 app 起始到片尾整段"的切法。若客户分区表在 app 之后还排了 nvs / storage / ota_data（相当常见），回烧时会把**旧分区内容原样写回，包括那份刚被擦掉的坏 cal_data** —— 重校准静默失效，日志上看不出任何异常，工程师会误判"重校准无效 → 转硬件 FA"，方向彻底走偏。

**正确做法（按名字操作，不切备份）**：

```powershell
# 1) 备份客户 app（按分区名，不算偏移）
python $env:IDF_PATH\components\partition_table\parttool.py --port COM7 `
       read_partition --partition-name=factory --output E:\rfcal\07_recal\cust_app.bin

# 2) 烧工装固件（同样按分区名）
python $env:IDF_PATH\components\partition_table\parttool.py --port COM7 `
       write_partition --partition-name=factory --input E:\rfcal\07_recal\phycal_tool.bin

# 3) 按 §4.1 布好环境 → 上电 → 串口输入 ERASE → 观察 full cal 完成日志

# 4) 烧回客户 app
python $env:IDF_PATH\components\partition_table\parttool.py --port COM7 `
       write_partition --partition-name=factory --input E:\rfcal\07_recal\cust_app.bin

# 5) 回烧后立刻复查 phy 命名空间
esptool.py --chip esp32c2 -p COM7 read_flash 0x9000 0x6000 E:\rfcal\07_recal\nvs_after.bin
python $NVSTOOL -d minimal --color never E:\rfcal\07_recal\nvs_after.bin | Select-String "phy"
```

若一定要从整片备份切，**必须按 §1.4 解出的真实 app 分区 offset/size 精确切片**，例如 factory @0x10000 size 0x150000 时：`d[0x10000:0x10000+0x150000]`。

### 4.3.3 ★ PHY 库版本必须对上（B1 的第二个坑）

工装固件若用了与客户**不同**的 IDF 版本 → phy 库版本不同 → `cal_version` 对不上 → **烧回客户 app 后第一次开机会再做一次 full cal，工装那次校准白做**。

对策二选一：
- **首选**：用与客户**相同**的 IDF 版本编译工装固件（所以 §1.2 定版必须在动手之前完成）；
- 次选：接受"客户 app 第一次开机才是真正的校准时刻"，并**保证那次开机也在 §4.1 的好条件下**。

工装固件的**分区表必须与客户一致**（至少 app 分区 offset/size 一致），否则烧不进去或起不来。

### 4.3.4 判据

| # | 判据 |
|---|---|
| ① | 串口打印 `erase phy cal data: ESP_OK` |
| ② | Wi-Fi 初始化后 dump nvs：`phy` 命名空间重新出现，`cal_data` 长度**正好 1904 字节**，`cal_mac` 等于 `read_mac` 的 MAC |
| ③ | **其它命名空间自始至终存在** → 副作用为零 |
| ④ | 回烧客户 app 后再冷启动，**不出现** `falling back to full calibration` → 说明工装那次校准被正常继承（版本对上了） |
| ⑤ | 按 §5 复测，R 的 95% CI 下界 > 6 dB → 校准假设成立 |

## 4.4 ⚠ 为什么不建议直接关掉 NVS 存储让它每次开机重校（B3）

乐鑫 Kconfig 帮助文本原文：

> `If it's easy that your board calibrate bad data, choose 'n'. Two cases for example, you should choose 'n': 1.If your board is easy to be booted up with antenna disconnected. 2.Because of your board design, each time when you do calibration, the result are too unstable.`

**这个开关的隐含逻辑是"不存 比 存了一份坏的 好"。对本产品，前提反过来**：

| # | 理由 |
|---|---|
| 1 | 本产品是**内置 PCB 天线、天线永远接着** —— 第 1 种情形根本不成立 |
| 2 | 本产品的现场条件恰恰是**最差的校准条件**：装在软胶壳里、用户戴手套握持、可能贴人手/人体、表面 50~70 ℃，而且**每一次上电时的姿态都不同**。关掉 NVS 存储 = 强制每次上电都在这种随机的、最差的条件下重新校准 |
| 3 | **后果的量级变了**：现在是"2000 片里个别几片变差"（一次坏校准被钉死）；关掉后变成"每台设备每次上电都可能校出一份坏参数"—— 把**个体偶发放大成全体每次开机抽奖**，故障率不是降低而是升高；现象从"跟随模组"变成"重启后好坏随机"，**更难定位** |
| 4 | 每次开机多约 100 ms + 额外功耗；且深睡唤醒也不再跳过校准（原文：enabled 时才 *PHY calibration will be skipped on deep sleep wakeup*），对低功耗产品是双重代价 |
| 5 | **把 FA 抓手一并取消了**：以后 NVS 里再也没有可导出、可备份、可比对的基线数据。A1/A4/B1 这些手段全部失效 |

**正确做法**：保持 `y`，把力气花在**保证"那一次" full calibration 在好条件下发生**（§4.1 + B1 + §4.5 的产线校准工位）。

**唯一值得考虑关闭的场景**：FA 最终证明该板设计导致校准结果**确实**每次都不稳定 —— 验证方法是用 B2 的 full 模式反复上电 20 次、看 TX 功率/RSSI 离散度。但那时应该做的是**改天线/匹配设计**，而不是关这个开关。

**顺带**：如果发现客户**已经**把这个选项关了，这本身就是本案的一条重大嫌疑线索，立刻确认。

## 4.5 量产/返修场景的正确做法

### 4.5.1 产线增设校准工位

| 项 | 要求 |
|---|---|
| **站位** | 设在 **"SMT 后、装壳前"** 的裸板功能测试工位（客户产品必须装壳出厂，所以校准点不能放在整机段） |
| **装配态** | 屏蔽罩已装、外壳未合、非金属治具、天线净空 ≥5 cm、无人手 |
| **供电** | 稳压电源，走产品自己的完整电源路径 |
| **温度** | 常温 20~30 ℃，模组已热稳定 |
| **干扰** | 工位周边 2.4G 源受控；治具间距足够 |
| **动作** | 一次受控 full calibration（B1/B4 工装），**只做一次** |
| **记录** | **逐台记录并存档**：MAC / phy_version / cal_version / cal_data 的长度+哈希 / `esp_wifi_get_max_tx_power()` 读数 / 固定 AP 的 RSSI 中位数（30 次）/ AP 侧看到本机的 RSSI / 供电电压 / 时间戳 → **作为出货基线** |

有了逐台基线，将来任何一台返修品都能直接比对"现在的 cal_data 是不是出厂那份"。

### 4.5.2 固件侧长期对策（全部符合 R5）

| 对策 | 说明 |
|---|---|
| 保留"擦校准并重启"诊断入口 | 做成串口调试命令或隐藏按键组合，**只能由后台/维修人员逐台人工触发**，且必须在原始 cal 上传成功之后。现场维修不用拆机烧录 |
| 启动日志上报 `phy_version` + `cal_version` | 只读上报，便于后台按批次统计 |
| OTA 前上传 cal_data 存档 | 上传"长度 + 哈希 + cal_version/cal_mac"，OTA 后由后台按批次**统计劣化率**，**人工**决定是否逐台处理 |
| ❌ **禁止**设备自主判断劣化并自动回写 cal_data | OTA 换了 PHY 库后 `cal_version` 已变，把旧 cal_data 写回去 → 下次开机版本校验必然失败 → 再 full cal → 再判劣化 → 再回滚，**可能形成每次开机重校的循环**。且违反 R5 |
| 失效品回收 SOP | 明写"不要重启、不要触发任何维护命令"，保住原始 cal_data |

### 4.5.3 必须向客户问清楚的问题（这一轮 FA 的高价值输出）

| # | 问题 | 为什么问 |
|---|---|---|
| 1 | 故障出现的时间点前后，**有没有做过 OTA / 固件升级？** | `cal_version` 失配 → 全体设备在 OTA 后第一次开机做 full cal，而那一刻设备正装在软胶壳里、可能被用户握着、机内 50~70 ℃ —— **正是最差的校准条件**。个别设备在那一刻校出坏数据 → 之后每次 partial 都基于这份坏数据 → **表现为"某个时间点之后个别设备永久变差，换板不换模组照样差"。与本案现象高度吻合** |
| 2 | 那次升级**换过 ESP-IDF 版本或 phy 库版本吗？** | 对比新旧固件的 `get_phy_version_str()` 打印即可判定 |
| 3 | 出问题的设备与正常设备，**固件版本是否一致？** | |
| 4 | 有没有版本-故障率的交叉统计？ | |
| 5 | 客户产品曾经用 `esp_base_mac_addr_set()` 做过 MAC 定制吗？ | 若有，**每次固件改动 MAC 派生规则都会触发全体设备重校准** —— 另一条历史线索 |

**取证**：从故障品与良品的 NVS 备份里分别导出 `cal_version`（4 字节）比对；再与当前固件的 `get_phy_version_str()` 比对。

| 观察 | 提示 |
|---|---|
| 故障品与良品的 `cal_version` **不同** | 强烈提示两者的校准发生在不同固件版本下 → 坐实"OTA 触发重校"路径 |
| `cal_version`/`cal_mac` 相同但 `cal_data` 差异巨大 | 提示两者在不同物理条件下各校了一次 |
| `nvs_tool.py -i` 报完整性错误 | 提示 flash 数据损坏路径（高温下 flash 数据保持力下降 → 校验失败 → 现场自动重做 full cal） |

---

# 5 重校准前后怎么测（否则白做）

## 5.1 基线纪律（不做这一节，后面所有 dB 数字都是假的）

| 项 | 要求 |
|---|---|
| **判定量** | **一律用对良品的差距收敛量**：`Gap = median(良品) − median(故障品)`，`R = Gap_before − Gap_after`。**禁止用"故障品自己前后差"** —— 那个量吃满环境漂移 |
| **状态下标** | `Gap` 必须带装配状态下标：`Gap_bare` 与 `Gap_cased` **各算一套、分别判定、禁止跨状态相减**（否则装配差异会凭空多出或少掉好几 dB） |
| **对照组** | ≥2 片同批良品（G1、G2）。G2 的作用是给出"良品之间的固有离散" = 你的噪声本底。**基准良品只读不写（R6）** |
| **固件一致** | 故障品与良品必须同板型、同固件 bin、同 sdkconfig、同国家码、同 `max_tx_power`、关省电（`esp_wifi_set_ps(WIFI_PS_NONE)`）、锁定速率 |
| **夹具** | 泡沫/亚克力支架，天线端朝 AP，离桌面 ≥50 cm，周围 1.5 m 内无金属无人；位置用美纹纸在桌面刻死，三块板**共用同一个位置，靠拿起-放下换板** |
| **AP** | 固定信道（1/6/11 中最干净的）、20 MHz、关自动信道、关波束成形/MU-MIMO、关 2.4/5G 合并、TX 功率固定档；**优先单天线 AP 或关分集**（多天线 AP 的 RSSI 会在两根天线间跳，直接毁掉 1~2 dB 分辨率）。全程不重启不改配置 |
| **交替** | **禁止"先测完 3 片良品再测故障品"**。用 G1→B→G1→B→…，≥5 轮。环境漂移对相邻两格影响近似相同，相减即抵消 |
| **采样** | beacon 100 ms 一个 → 200 包 ≈ 20 s；**取中位数不取均值**（RSSI 有长尾）。中位数标准误 ≈ **1.25·σ/√N**，N=200 时约 0.2~0.45 dB —— **随机噪声不是瓶颈，系统性误差（重新摆放、环境漂移）才是**，所以宁可加轮数不要单纯加大 N |

**夹具验收（准入门槛）**：先做良品-良品空实验，跑完整 5 轮 A/B/A/B，算 `d_i = median(G1) − median(G2)` 的标准差 `σ_d`。

| 判据 | 值 |
|---|---|
| **准入门槛（沿用已批准的 G2 闸门）** | 拆装 10 次极差 **≤2 dB**、单次 σ **≤1.5 dB** |
| 目标值 | σ_d ≤1 dB |
| 必须记录 | **σ_d 的实测值必须写进报告** —— 它是 §5.5 所有判据的分母 |

⚠ 空实验必须**真的换板**（拿起-放下）。只在同一块板上连采多次，测到的是随机噪声不是重复性，σ_d 会被严重低估，判据虚假地变严格。**不要为了少测几轮去修饰 σ_d。**

## 5.2 五路独立测量

### A. 模组侧读 AP（RX 方向）—— 双路冗余自检

```c
int r1; wifi_ap_record_t ap;
esp_wifi_sta_get_rssi(&r1);          /* v5.0/v5.1 均存在，已核实 */
esp_wifi_sta_get_ap_info(&ap);       /* 用 ap.rssi */
ESP_LOGI(TAG, "%llu,%d,%d,%d", ts, r1, ap.rssi, ap.primary);
```

**两路并列打印，不是主备**。自检：若连续 300 s 内 `r1` 标准差为 0，判该路无效（已有报告 esp-idf issue #17664：v4.3.6 正常、升到 v5.5 后 `esp_wifi_sta_get_rssi` 返回恒定值）。两路应同步波动；一路动一路不动 = 不动的那路失效。

**第三路：sniffer 板收 AP 的 beacon**（完全独立的物理通道，不经过 STA 状态机）：

```c
const wifi_promiscuous_pkt_t *p = (wifi_promiscuous_pkt_t *)buf;
const uint8_t *a2 = p->payload + 10;             /* addr2 = 发送方 MAC */
if (memcmp(a2, target_mac, 6)) return;
printf("%d,%d,%u,%u\n", p->rx_ctrl.rssi, p->rx_ctrl.noise_floor,
       p->rx_ctrl.channel, p->rx_ctrl.sig_len);
```

**C2 有 `noise_floor`**（`signed noise_floor:8; /**< ... unit: dBm*/`，已核实）。**必须同时记 noise_floor**：`SNR = rssi − noise_floor` 才是真正决定解调的量。

| 观察 | 含义 |
|---|---|
| rssi 低 20 dB，noise_floor 与良品相同 | 纯通路损耗 |
| rssi 低且 noise_floor 也抬高 | **前端噪声系数恶化（LNA/ESD 损伤）** —— 这是 RSSI 单值给不出的信息 |

**工作点必须落在 −45 ~ −75 dBm**（−30 以上饱和压缩，−85 以下接近本底）。

### B. AP 侧看模组（TX 方向）

| 方式 | 做法 |
|---|---|
| **OpenWrt/Linux AP** | `iw dev wlan0 station dump`，看 signal / tx bitrate / tx retries / tx failed。⚠ signal 只在有流量时更新，必须 `ping -f -s 1000 <DUT>` 造流量 |
| **独立 sniffer 板（推荐作主数据）** | 同上 promiscuous 代码，过滤 `addr2 == DUT MAC`。sniffer **固定不动**（距 DUT 1.0 m，位置胶带标死），换 DUT 时 sniffer 一动不动 → 端上的所有变化都只能来自 DUT 的发射。**按 rate/sig_mode/mcs 分组统计**（不同速率发射功率不同，混算会得到假差值） |
| **笔记本 monitor + radiotap** | `tcpdump ... 'wlan addr2 aa:bb:...'` → 看 `radiotap.dbm_antsignal`。⚠ 笔记本网卡功率标定精度差（±5 dB 常见），**只做定性交叉，不做主数据** |

**方向分解**：

| 观察 | 结论 |
|---|---|
| ΔTX ≈ ΔRX ≥10 dB | 双向 → **无源通路**（匹配网络、焊点、天线、屏蔽罩、QFN 底盘） |
| ΔRX 大、ΔTX ≈0 | RX 侧（LNA / RX 增益校准） |
| ΔTX 大、ΔRX ≈0 | TX 侧（PA、供电、功率设置、TX 功率校准） |

### C. 零成本电子衰减：`esp_wifi_set_max_tx_power` 扫描

已核实的映射表（`attention 3` 原文）：`{{8,2},{20,5},{28,7},{34,8},{44,11},{52,13},{56,14},{60,15},{66,16},{72,18},{80,20}}` —— **实际可用档位只有 11 个**（2/5/7/8/11/13/14/15/16/18/20 dBm），单位 0.25 dBm、范围 [8,84]，**不是连续 0.25 dB**。写 80 得 20 dBm。必须在 `esp_wifi_start()` 之后调用。

逐档 30 s，同时在 sniffer 端统计 rssi 中位数，良品与故障品各一条曲线：

| 曲线形状 | 结论 |
|---|---|
| 两条线**平行下移**，间距 = ΔdB | 纯线性损耗。**该间距对夹具绝对定位不敏感**（同夹具同 sniffer，只看间距） |
| 故障品**斜率偏小或提前压平** | 功率控制/PA 已不线性（PA 损伤，或校准把功率表校歪） |
| 两条曲线**完全重合**但空口 RSSI 低 | 差异不在"设定→PA 输出"这一段，在 **PA 之后**（应与 E 的电流法结论一致） |

⚠ 国家码 / `CONFIG_ESP_PHY_MAX_WIFI_TX_POWER` / `REDUCE_TX_POWER` / PowerLimitTool 都会再限一层。**重校准前后各读一次 `esp_wifi_get_max_tx_power()` 并存档**（这是排除混淆项的关键，见 §5.5）。

### D. 衰减 / 距离门限法（最可靠的低成本方法）

**门限是一个跨越点，不是一个读数** —— 不依赖 RSSI 绝对标定，也不依赖夹具绝对定位。可做到 ±1 dB。

器材：0~60/90 dB、1 dB 步进、DC~6 GHz、≥2 W 的 SMA 步进衰减器 + 短跳线 + 带外置天线口的 AP。合计 <1000 元。

**★ 必做：泄漏地板标定（不做则衰减器等于废的）**
衰减从 0 逐档加到最大，记 DUT 端 RSSI。曲线开始变平的拐点即 `A_leak`（信号绕过衰减器空间直耦）。**超过 A_leak 的所有数据无效**。降低办法：DUT 装屏蔽袋/饼干盒、拉开距离、线缆加铁氧体。

不标定的后果：良品和故障品都被卡在同一个假门限上，得出"无差异"的**完全错误**结论。

**扫描**：0 dB 起每档 +2 dB（近门限改 +1 dB），每档 60 s，记 RSSI / PER。定义 `A_th` = **PER 首次 ≥10% 时的衰减值**。A/B/A/B 交替各 5 遍取中位数。

**⚠ PCB 天线模组做不了传导** → 把衰减器加在 **AP 侧**（AP 用外置天线口），**DUT 保持 PCB 天线原状不动**。这一点对 FA 极其重要：为做传导而拆匹配网络 = 把待检物拆掉重焊。

**无衰减器的兜底：距离扫描**。1/2/3/5/8/12 m，每个距离点在 ±5 cm 内取 5 个微移位置（λ/4 ≈ 3.07 cm 的整数倍）各测一次再平均，用来平掉驻波。画 RSSI vs 20·log10(d)，两条平行线的垂直间距即损失量。精度 ±2~3 dB。

### E. 发射电流法（信息量最高的一条）

**为什么这条能切开校准与硬件**：校准数据的作用点是"设定功率 → PA 偏置/驱动"，**无法改变 PA 之后的无源损耗**；反过来匹配网络裂纹/天线开路也无法改变 PA 偏置电流（除非严重失配引起 VSWR 变化）。这是本方案里**唯一一个不依赖空口测量的独立维度**。

**★ 接法（与 §4.1 的校准供电要求分工明确，勿混用）**

| 场景 | 接法 |
|---|---|
| **校准那一次上电** | **走产品自己的完整电源路径，FB7 在位** |
| **测发射电流时** | **先把 FB7 一端焊开**（保留元件以便复原），从模组侧焊盘灌电；整板其余部分**仍由原供电供电**（主板 BGA 必须活着才能驱动 FEN 与 SPI）。电源设 3.30 V / 限流 ≥1 A / 四线感测 / 长线就近并 100µF+0.1µF。实验结束复原 FB7 |

> ⚠ **不要在 FB7 仍在位时向 pin7 灌电（会与板上 A7_3V3 打架）**。焊开/复原 FB7 属物理改动，必须排在 X-ray 等原始形态取证之后并留照。
> 这两件事**不能在同一次上电里做**。

**Δ 法**：`I_TX − I_idle`（idle = 已连 AP、无流量、关省电），把板子其余部分的电流完全抵消。

**判定表（Δ电流 = 故障品 vs 良品，同档位）**

| 观察 | 结论 |
|---|---|
| 对端 RSSI 低 ≥10 dB，Δ电流差 <5%，电流-功率曲线与良品重合 | **PA 输出正常，损耗在 PA 之后**：匹配网络 0402 元件/焊点、馈线、天线、屏蔽罩压迫、QFN 底盘焊点。**校准假设基本出局**（TX 功率校准若被校坏，PA 驱动电平会降，电流必然跟着降）→ 转硬件 FA |
| 对端 RSSI 低 ≥10 dB，Δ电流也低 ≥10% | PA 驱动被压低。三个可能：①功率设置 ②供电跌落（查模组引脚实测 VCC 与 TX 突发纹波，官方限值 MCS7@11n 时 Vpp <80 mV）③**TX 功率校准数据坏** → **校准假设在这一格里，值得做 §6 的回灌验证** |
| 对端 RSSI 低，电流**反而高于**良品 | PA 负载失配/自激（VSWR 恶化，反射功率回灌），仍是 PA 之后的无源问题，且更严重 |
| RSSI 正常但电流异常 | 测量出错或工况不一致，回查固件/速率/占空比 |

**⚠ 连续发射的硬指标（同等强制）**

| 项 | 限值 |
|---|---|
| 温度监控 | 全程红外或 K 型热电偶贴罩顶 |
| 表面温度上限 | **80 ℃**（绝对红线 105 ℃） |
| 单次时长 | **≤60 秒**，每次之间冷却到室温 |
| 排序 | **必须排在 X-ray、原始形态照片、无损物理检查之后** |
| 收尾 | `wifiscwout` / `esp_tx` 用完立即 `-e 0` / `cmdstop` |

原因：模组现场就已 50~70 ℃；头号假设是匹配网络元件裂纹/焊点开裂/QFN 底盘空洞，这类临界缺陷在升温下形貌会变（裂缝张开、氧化物重新接触），**一次超温连续发射就可能把"可复现的间歇故障"永久变成"稳定开路"或"暂时自愈"，两种都会让后续 X-ray、切片和机械激励失去基准**。

若只是要比相对电流，可用**分组发射 + 电流包络示波器抓峰值**代替连续发射，规避升温。

**cert_test 补充说明**
- `-c/--packet_num` 传 **0** 的语义（不发 / 无限发）官方未定义 `[待现场确认]`。先用明确大数（如 `-c 100000`）验证，并**用 sniffer 确认确实有包在发、用电流表确认电流抬升**，再决定是否用 0。**开始记录电流前必须先确认 sniffer 端能收到该 DUT 的包。**
- **`txpwr_track_en` 不在 IDF cert_test 的注册命令表里**（属乐鑫 EspRFTestTool 配套的另一套 RF 测试固件，两套不可混用），在 cert_test 里输入会报 Unrecognized command。
- **`get_rx_result` 的打印标签在不同分支之间被对调、实参顺序不变，至少有一版标签是错的**。正确读法：**不看标签，两个数里较大的 = `phy_rx_total_count`，较小的 = `phy_rx_correct_count`**。
- **PER 必须用 `1 − N_correct / N_sent`**（N_sent = `esp_tx` 的 `-c` 参数），**不要用 `1 − correct/total`** —— total 含环境里其他设备的包，分母虚高会把 PER 算低，灵敏度门限直接测偏。
- `phy_rx_rssi` 字段头文件注释为 `/*!< Average RSSI of desired packets */`，**未标注单位**；README 示例输出 `RSSI: -527`，推测为 0.1 dBm 刻度 `[推断，官方未明示]`。**只作相对量用**，绝对参考改用 sniffer 的 `rx_ctrl.rssi`（该字段头文件明确标注 unit: dBm）。
- ESP8684 数据手册的电流/功率/灵敏度数值 `[待现场确认]`（本轮未独立核实，且内部有工况标注不一致处）。**M6 的判定全部基于"与良品的相对差"，本就不依赖手册绝对值** —— 手册数值一律降格为"参考量级"，不要拿绝对值下结论。

### F. iperf 吞吐曲线（把 dB 翻译成客户能理解的业务指标）

- 用 IDF 自带 `examples/wifi/iperf`。**PC 端必须装 iperf 2.0.x，iperf3 不兼容** `[待复核，工位上两分钟验证即可定论]`。
- **必须用 UDP 定速做主数据**：TCP 的重传与拥塞控制会把链路劣化藏起来。
- 在 D 的每个衰减档重复，画"吞吐 vs 衰减"与"丢包率 vs 衰减"。**膝点（吞吐开始崩塌的衰减值）之差 = 链路预算差**，应与 D 的 `A_th` 一致。
- 上下行都要测（只测下行会漏掉纯 TX 侧的问题）。
- ⚠ 烧 iperf 例程会覆盖客户 app，**分区表必须与客户一致**，否则 nvs 位置变了，§6 的回灌实验作废。

## 5.3 交叉验证判据（不要用 ±3 dB —— 那是循环论证）

用 ±3 dB 的一致性作交叉验证，而 ±3 dB 同时又是"校准假设出局"的门槛，两者同量级，几乎必然成立，不提供信息量。改为：

| 判据 | 要求 |
|---|---|
| 方向性 | 两种方法给出的差值**同号** |
| 量级性 | 比值落在 **0.6 ~ 1.6** 之间 |
| 辅助 | 两者之差不超过 `2·sqrt(σ_A² + σ_B²)` |

**交叉验证的目的是排除测量假象**（例如"RSSI 恢复 12 dB 但门限完全没变"这种自相矛盾），**不是为了提高精度**。

**R 至少要在两个互相独立的物理量上同号同量级才算数**：① 空口 RSSI ② 衰减/距离门限 ③ 发射电流 ④ 吞吐膝点。

## 5.4 重复次数：3 dB 判据在 ±2 dB 重复性下够不够

**要在 95% 置信、80% 把握下判出大小为 δ 的效应，配对重复次数：**

$$n \ge 8\left(\frac{\sigma_d}{\delta}\right)^2 \quad(\text{小样本再 }+2\text{ 补 t 分布修正})$$

| σ_d | δ | 计算 n | 取值 |
|---|---|---|---|
| 1 dB | 3 dB | 0.89 | **n = 3** |
| **2 dB** | **3 dB** | **3.56** | **n = 6（建议做到 8）** |
| 2 dB | 10 dB | 0.32 | **n = 2** |

**直接回答**：σ_d = ±2 dB 时，**3 dB 判据在单次测量下完全不够**（3 dB ≈ 1σ_diff，掷硬币水平）；**重复 6~8 轮配对后是够的**。**10 dB 判据在任何合理重复性下都稳。**

**报判据用置信区间，不用点估计**：n 轮配对得到 R 的均值 R̄ 与标准差 s，95% CI = R̄ ± t(0.975, n−1)·s/√n。

| CI | 结论 |
|---|---|
| **下界 > 6 dB** | 校准数据问题证实（比"点估计 ≥10 dB"更严谨，也更容易达成） |
| 含 0 但**上界 < 3 dB** | 校准假设出局（**这是等价性判定**） |
| 其余 | 不确定，加轮数或换门限法（分辨率更高） |

**"<3 dB 出局"的措辞必须改**：统计上你证明的是"在本装置 ±X dB 的分辨率下**未检出**效应"，不是"效应为零"。**证伪比证实更费数据** —— 要把上界压到 3 dB 以下，n 要比检出 3 dB 还多约一倍。做不到就如实写"未检出，分辨率 X dB"。

**报告里必须同时给出 R̄、s、n、CI 四个数。只给一个 dB 数字的结论一律不采信。**

## 5.5 必须排除的三个混淆（不做这三条，判据全是假的）

| # | 混淆 | 排除办法 |
|---|---|---|
| 1 | **擦 NVS 顺手擦掉了别的东西** —— nvs 里还有 Wi-Fi 凭据、国家码、应用参数。重校后功率设置可能变了 → "恢复"其实是配置变化不是校准 | **前后各读一次 `esp_wifi_get_max_tx_power()` 与国家码并存档** |
| 2 | **间歇性硬件故障** —— 焊点裂纹会因搬动/温度自己"好一阵" | 重校准前后之间**不许拔插、不许搬动、不许改温度**；且必须做 §6 的来回复现 |
| 3 | **校准本身不稳定** —— Kconfig 点名的"板设计导致每次校准结果都不稳定" | 重校准要做 **3 次**（擦→上电→测→再擦→再上电→再测…），看三次结果的离散。**若三次自己就差 5 dB，说明这块板属于"校准不稳定"设计** —— 这本身就是重要结论，且会污染所有前后对比 |

---

# 6 最强的证据：可逆复现

**目的**：把"擦了 NVS 之后好了"这个**相关性**，升级为"坏数据在则坏、坏数据去则好、再放回去又坏"的**因果实证**。相关性可以被巧合、被间歇性接触、被顺手改掉的配置解释；**来回可复现的开关效应不能**。

## 6.1 ★ 最关键的一条约束

**只能回灌这颗模组自己的备份。**

`phy` 命名空间加载时会拿 `cal_mac` 与芯片实际 MAC 比对。灌**别的模组**（哪怕是同批良品）的 cal_data，MAC 不匹配 → 加载失败 → 按 phy_init.c 的逻辑**直接走 full calibration 并回写 NVS**，实验完全无效；更糟的是你会误以为"灌了坏数据也没坏 → 校准假设不成立"，**得到一个方向相反的错误结论**。

反过来，灌回**自己**的备份时 MAC 与版本都对得上 → 被正常加载并用于 partial cal，且**不会被回写覆盖**（回写只在"加载失败或校验失败"时发生）—— 这正是回灌能稳定复现的机制原因。

## 6.2 状态机（每一步之间不许动板子、不许拔插、不许改温度）

| 相 | 动作 | 测量 |
|---|---|---|
| **S0 基线（坏）** | 不动，按 §5 测一轮，存档 | Gap_bare + Gap_cased |
| **S1 擦除重校** | B1 工装（首选）或 `erase_region`；**上电前按 §4.1.1 布置成半装配态**；冷启动触发 full cal | 测一轮 |
| **S2 回灌（坏）** | 五步回灌流程（见 6.3）；冷启动 | 测一轮 |
| **S3 再擦除** | 同 S1 | 测一轮 |
| **S4 再回灌** | 同 S2 | 测一轮 |

**至少走到 S4（两个完整来回）。**

## 6.3 回灌的五步（缺一步就可能砖或误判）

```powershell
# ① 长度断言：nvs_BAD.bin 长度必须 == nvs 分区实际 size（从实测分区表取，不许硬编）
python -c "import sys,os; s=os.path.getsize(r'E:\rfcal\00_backup\nvs_BAD.bin'); print(s); sys.exit(0 if s==0x6000 else 1)"
#   不等就停 —— 长了会盖掉相邻分区（0x10000 起就是 app），短了则分区尾部残留旧内容

# ② 确认 §0.2 四问 + espefuse 检查已通过（加密设备写明文 = 把 NVS 彻底写坏）

# ③ 写入
esptool.py --chip esp32c2 -p COM7 -b 460800 write_flash 0x9000 E:\rfcal\00_backup\nvs_BAD.bin

# ④ 写后回读比对 —— 不一致就地停手，不要上电
esptool.py --chip esp32c2 -p COM7 -b 460800 read_flash 0x9000 0x6000 E:\rfcal\07_recal\verify.bin
(Get-FileHash -Algorithm SHA256 E:\rfcal\07_recal\verify.bin).Hash
(Get-FileHash -Algorithm SHA256 E:\rfcal\00_backup\nvs_BAD.bin).Hash
#   两者必须完全一致

# ⑤ 上电后先看日志：必须【没有】falling back to full calibration、也【没有】Saving new calibration data due to
#    才说明这次确实在用回灌的旧数据跑，这一相的 RF 数据才允许计入判定
```

## 6.4 盲测（强烈建议，几乎零成本）

由第二个人执行烧写，测试员**不知道当前是哪个状态**，测完再解码。RSSI 这类"看着仪表调参数"的测量极易被期待效应污染。表 2 的"状态"列在盲测时先留空，解码后回填，**保留原始盲码**。

## 6.5 判读

| 观察 | 结论 |
|---|---|
| S0≈S2≈S4（坏）且 S1≈S3（好），组间差 ≥ §5.4 门槛、组内离散 ≤ σ_d | **校准数据是当前症状的直接原因，实证成立**。报告里可以写"因果"而不是"相关" |
| S1/S3 恢复但 S2/S4 **没复发** | 擦 NVS 时还改变了别的东西（配置/凭据）→ 回查 §5.5 混淆项 1 |
| S1/S3 与 S0 无差别 | **校准假设直接出局** → 转硬件 FA（X-ray 查 QFN 底盘/RF 脚焊点空洞裂纹、LCR 查 π 型匹配元件、VNA 对比 S11、ESD 损伤评估）。参考 esp-idf issue #15763 的先例：S3 模组个体差 40 dB，强制全校准无效，换模组才恢复，乐鑫判定 RX 前端 ESD 损伤 |
| 各状态之间毫无规律、离散很大 | 间歇性接触不良 → 去做发射电流法与热风/按压试验 |

## 6.6 caveat

1. **预演优先**：先在牺牲品上把整圈"备份→擦→冷启动→回灌→冷启动"跑一遍，确认能正常启动、能连 AP、RSSI 与最初基线差 <3 dB。**预演通过才允许对故障样品动手。**
2. 回灌整个 nvs 分区会连带恢复 Wi-Fi 凭据与应用数据 —— 这正好保证"完全相同的状态"，但应用运行时会写 NVS 导致镜像漂移，**每次读回都要重新算 SHA256 并记录**。
3. `write_flash` 会自动擦所涉扇区，起始地址必须 4 KB 对齐。
4. **S1 的上电条件必须与 §4.1.1 的裁决一致**。若擦除后的 full cal 是在天线被拿开、罩没装的条件下做的，等于人为造了一个新的坏校准，S1 会看起来更差 —— 整个实验作废。
5. 全程记录每次操作的时间戳与模组表面温度。
6. **本步骤之后模组的原始 NVS 状态已被反复改写，X-ray 等原始形态取证必须排在它之前。**

---

# 7 判定表与结论边界

## 7.1 恢复量判定表

| 恢复量 R（95% CI 下界） | 残差（重校后故障品 vs 良品的剩余差距） | 判定 | 下一步 |
|---|---|---|---|
| **CI 下界 > 6 dB**（点估计通常 ≥10 dB） | **≤3 dB** | **校准数据是直接原因，证实** | 全力查 §4.5.3 的 C2 线索（何时、为何被写入坏数据）；做 §6 确认因果 |
| CI 下界 > 6 dB | **>5 dB** | **校准 + 硬件叠加** | **两条线都继续走，不许结案** |
| CI 覆盖 3~10 dB 区间 | — | **部分相关**。校准把 TX 功率校歪的量级通常就在 3~10 dB（功率表偏一两档），**这一档是真实存在的物理区间，不是纯噪声区** | **必须靠 §6 的可逆复现来定性**，不能靠加大样本量解决 |
| CI 含 0 且**上界 < 3 dB** | — | **校准假设出局**（措辞：在本装置 ±X dB 分辨率下未检出效应） | 转硬件 FA：X-ray 查 QFN 底盘/RF 脚焊点、LCR 查 π 型匹配元件、VNA 对比 S11、ESD 损伤评估。**不要在校准上继续投入** |

**为什么加"残差归零"这一条**：故障幅度约 20 dB，恢复 10 dB 意味着还有 10 dB 没解释，此时模组相对良品仍严重超标 —— 只按"R ≥10 dB"结案会把一个未解决的问题结掉。

## 7.2 ⚠ 结论边界（必须逐字写进报告）

> **"擦除后恢复"只证明校准数据是当前症状的直接原因，不等于找到了根因。**

| 层级 | 问题 | 由什么回答 | 状态 |
|---|---|---|---|
| **直接原因** | 这份 cal_data 在则坏、去则好吗？ | §6 的 A/B/A/B 可逆复现（两个完整来回 + 盲测） | 本作业指导书可以给出 |
| **根本原因①** | **为什么会写入坏数据？** 在什么条件下、什么时刻被写进去的？ | §4.5.3 的 OTA / PHY 库版本时间线 + 产线首次上电站点的实际条件 + 示波器抓 3V3 与 EN(FEN) 时序 | **必须另行回答** |
| **根本原因②** | **为什么 2 个月后才出现？** | 两条候选路径：(a) OTA 换了 IDF/phy 库 → `cal_version` 失配 → 全体设备在 OTA 后第一次开机做 full cal，而那一刻设备正在软胶壳里、被握着、50~70 ℃；(b) 高温下 flash 数据保持力下降导致 cal_data 损坏 → 校验失败 → 现场自动重做 full cal | **必须另行回答** |
| **根本原因③** | **为什么偏偏是这几片？** | 大概率是**硬件处于临界状态 + 一次坏校准的叠加**（软硬两条线可能是叠加的，不是二选一） | **必须另行回答** |

**两者都拿到，才允许写进 8D 的 D4。** 只交"擦了就好"的黑箱结论，既写不进 D4 也无法向乐鑫举证。

## 7.3 统计边界

| 边界 | 表述 |
|---|---|
| 样本量 | **n = 1~2 片故障样品**。报告中必须写明这个统计边界，**禁止把单片结论外推为 2000 片批次的结论** |
| 版本范围 | 结论只覆盖"实测过的那个 IDF 版本 + 那份固件配置"。**不要泛化成"所有 ESP-IDF 都这样"** |
| 数据可解读性 | `cal_data` 的 1894 字节 opaque 是闭源私有格式，**只做同一性/差异性比对，不做内容评价**。对外材料必须明写这一句 |

## 7.4 复发监视（不做这条，"修好了"是没有期限的承诺）

| 项 | 要求 |
|---|---|
| 环境应力 | 重校后的样品做 **10 次 −20↔70 ℃ 温循 + 72 h 连续运行**后复测 |
| 现场回访 | 对现场处理过的机器建立 **3 个月回访节点** |

---

# 8 记录表（空表）

## 表 1 · 装置与条件（每个测试日填一次）

| 项 | 值 |
|---|---|
| 日期 / 时段 | |
| 操作员 / 记录员 | |
| AP 型号 / 固件 / 信道 / 带宽 / TX功率档 / 天线数与分集状态 | |
| 环境信道占用截图文件名 | |
| 夹具：距离 / 高度 / 朝向 / 刻线照片文件名 | |
| 供电：电源型号 / 设定电压 / **模组引脚实测 VCC** / FB7 状态（在位 / 焊开） | |
| 固件：bin 的 SHA256 / **IDF 版本（app 的 idf_ver）** / bootloader IDF_VER / chip revision | |
| sdkconfig 关键项：`CALIBRATION_AND_DATA_STORAGE` / `CALIBRATION_MODE` / `IMPROVE_RX_11B` / `MAX_WIFI_TX_POWER` / `REDUCE_TX_POWER` / 国家码 | |
| `esp_wifi_get_max_tx_power()` 读数 | |
| 室温 / 模组表面温度（预热后） | |
| esptool 版本与命令风格（下划线 / 连字符） | |
| **良品-良品空实验 σ_d = ___ dB（夹具验收，必填）** | |
| 夹具验收：拆装 10 次极差 = ___ dB（门槛 ≤2）、单次 σ = ___ dB（门槛 ≤1.5） | |

## 表 2 · 主数据（每格一行，A/B/A/B 交替填）

| 轮次 | 板号(G1基准/G2基准/GS牺牲/B故障) | **样品类别**(基准良品/牺牲良品/故障品) | **状态**(S0/S1/S2/S3/S4) | **装配态**(裸板/半装配/整机) | 时间戳 | 包数N | sta_get_rssi 中位数 | ap_info.rssi 中位数 | sniffer rssi 中位数 | noise_floor 中位数 | SNR | AP端 signal 中位数 | tx retries/failed | Δ电流(mA) | 备注 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | G1 | | | | | | | | | | | | | | |
| 1 | B | | | | | | | | | | | | | | |
| 2 | G1 | | | | | | | | | | | | | | |
| 2 | B | | | | | | | | | | | | | | |
| 3 | G1 | | | | | | | | | | | | | | |
| 3 | B | | | | | | | | | | | | | | |
| 4 | G1 | | | | | | | | | | | | | | |
| 4 | B | | | | | | | | | | | | | | |
| 5 | G1 | | | | | | | | | | | | | | |
| 5 | B | | | | | | | | | | | | | | |
| 6 | G1 | | | | | | | | | | | | | | |
| 6 | B | | | | | | | | | | | | | | |
| 7 | G1 | | | | | | | | | | | | | | |
| 7 | B | | | | | | | | | | | | | | |
| 8 | G1 | | | | | | | | | | | | | | |
| 8 | B | | | | | | | | | | | | | | |

**样品累计计数（每次操作累加）**：累计上电次数 ___ / 累计通电时长 ___ / 累计进出下载模式次数 ___ / 连续发射累计时长 ___ / 表面温度峰值 ___ ℃

## 表 3 · 功率扫描 / 电流曲线（每板每状态一张）

| 设定 power 参数 | 对应 dBm | sniffer 端 RSSI | Δ电流(mA) | 表面温度 | 备注 |
|---|---|---|---|---|---|
| 80 | 20 | | | | |
| 72 | 18 | | | | |
| 66 | 16 | | | | |
| 60 | 15 | | | | |
| 56 | 14 | | | | |
| 52 | 13 | | | | |
| 44 | 11 | | | | |
| 34 | 8 | | | | |
| 28 | 7 | | | | |
| 20 | 5 | | | | |
| 8 | 2 | | | | |

## 表 4 · 衰减/距离门限扫描（每板每状态一张）

| 衰减(dB) 或 距离(m) | DUT端RSSI | AP端signal | ping丢包% | UDP吞吐(Mbps) | UDP丢包% | N_sent | N_correct(**较小那个数**) | PER=1−N_correct/N_sent | 是否掉线 |
|---|---|---|---|---|---|---|---|---|---|
| 0 | | | | | | | | | |
| 2 | | | | | | | | | |
| 4 | | | | | | | | | |
| … | | | | | | | | | |

**A_leak = ___ dB（泄漏地板，必填，超过此值数据作废）**　**A_th (PER≥10%) = ___ dB**

## 表 5 · NVS / 校准数据比对

| 样品 | 状态 | MAC | phy_version | cal_version | cal_mac 是否等于 MAC | cal_data 长度(应=1904) | cal_data SHA256 | nvs_tool -i 完整性 |
|---|---|---|---|---|---|---|---|---|
| 故障品 | S0 | | | | | | | |
| 故障品 | S1 | | | | | | | |
| 故障品 | S2 | | | | | | | |
| 基准良品 G1 | — | | | | | | | |
| 基准良品 G2 | — | | | | | | | |

## 表 6 · 结论汇总（每颗故障品一张）

| 指标 | 装配态 | Gap_before | Gap_after | 恢复量 R̄ | s | n | 95% CI | 结论 |
|---|---|---|---|---|---|---|---|---|
| 模组端 RSSI (RX) | 裸板 | | | | | | | |
| 模组端 RSSI (RX) | 整机 | | | | | | | |
| sniffer RSSI (TX) | 裸板 | | | | | | | |
| 门限 A_th | 裸板 | | | | | | | |
| 吞吐膝点 | 裸板 | | | | | | | |
| Δ电流 | 裸板 | | | | | | | |

| 项 | 结果 |
|---|---|
| **交叉验证**：≥2 个独立物理量同号且比值 0.6~1.6？ | 是 / 否 |
| **混淆排除**：①功率设置前后一致 ②中途未搬动 ③三次重校离散 ≤___ dB | 全过 / 未过（哪条） |
| **残差**：重校后故障品 vs 良品剩余差距 | ___ dB |
| **可逆性 S0/S1/S2/S3/S4 是否来回复现** | 是 / 否 / 无规律 |
| **盲测解码是否与烧写记录一致** | 是 / 否 |
| **最终判定** | 校准证实 / 校准+硬件叠加 / 部分相关 / 校准出局→硬件FA |
| **根因三问是否已回答**（为何写入坏数据 / 为何 2 个月后 / 为何偏偏这几片） | 已答 ___ 条 / 3 |

## 表 7 · 操作留痕（每条写入类命令一行）

| 时间 | 四问是否逐条确认 | 命令原文 | 目标板 | 命令实际输出摘要 | 写后回读 SHA256 是否一致 | 操作前 RSSI 中位数 | 操作后 RSSI 中位数 | 文件 SHA256 |
|---|---|---|---|---|---|---|---|---|

**归档要求**：原始数据（每包 RSSI）另存 CSV，表里只放中位数，但**原始 CSV 必须归档**，否则事后无法重算 σ 与 CI。所有照片/截图/波形以**文件名**引用（文件名带板号+状态+时间戳）。表格用 Excel/CSV，不要 Word 手填。最后生成全目录哈希清单：

```powershell
Get-ChildItem -Recurse -File E:\rfcal | Get-FileHash -Algorithm SHA256 |
  Select-Object Hash, Path | Export-Csv E:\rfcal\MANIFEST.csv -NoTypeInformation -Encoding UTF8
```

---

# 9 命令速查（Windows / PowerShell 优先）

## 9.1 esptool v4 / v5 双写法对照

| 用途 | esptool **v4.x**（IDF v5.0/v5.1 自带） | esptool **v5.x** |
|---|---|---|
| 查版本 | `esptool.py version` | `esptool version` |
| 查芯片/flash | `esptool.py --chip esp32c2 -p COM7 flash_id` | `esptool --chip esp32c2 -p COM7 flash-id` |
| 读 MAC | `esptool.py ... read_mac` | `esptool ... read-mac` |
| 整片备份 | `esptool.py --chip esp32c2 -p COM7 -b 460800 read_flash 0 ALL out.bin` | `esptool ... read-flash 0 ALL out.bin` |
| 读区域 | `... read_flash 0x9000 0x6000 nvs.bin` | `... read-flash 0x9000 0x6000 nvs.bin` |
| 擦区域 | `... erase_region 0x9000 0x6000` | `... erase-region 0x9000 0x6000` |
| 写区域 | `... write_flash 0x9000 nvs.bin` | `... write-flash 0x9000 nvs.bin` |
| app 描述符 | `esptool.py image_info --version 2 app.bin` | `esptool image-info app.bin`（**无 `--version`**） |
| 复位选项 | `--before default_reset` / `--after no_reset` | `--before default-reset` / `--after no-reset` |
| efuse 摘要 | `espefuse.py -p COM7 summary` | `espefuse -p COM7 summary` |

**约束**：`erase_region` / `erase-region` 的**地址与长度都必须是 0x1000（4096）的整数倍**。长度写错会报错（好事）；**地址写错不会报错（坏事）** —— 这就是备份不可省的原因。

**连不上时的正确重试顺序**（不要试 74880/9600，那是 ESP8266 ROM 的日志波特率，esptool 下载协议里无意义）：
`-b 115200` → 加 `--no-stub` → 加 `--before no_reset` 并手动按住 IO9 复位 → 缩短飞线 / 换 USB-TTL。C2 的 26 MHz 晶振由 esptool 自动处理，不需要额外参数。

## 9.2 parttool / nvs_tool / nvs_partition_gen

```powershell
$PT      = "$env:IDF_PATH\components\partition_table\parttool.py"
$NVSTOOL = "$env:IDF_PATH\components\nvs_flash\nvs_partition_tool\nvs_tool.py"
$NVSGEN  = "$env:IDF_PATH\components\nvs_flash\nvs_partition_generator\nvs_partition_gen.py"
```

| 用途 | 命令（parttool 的子命令**全部是下划线**） |
|---|---|
| 查分区信息 | `python $PT --port COM7 get_partition_info --partition-name nvs --info offset size` |
| 读分区 | `python $PT --port COM7 read_partition --partition-name=nvs --output nvs.bin` |
| 写分区 | `python $PT --port COM7 write_partition --partition-name=factory --input app.bin` |
| 擦分区 | `python $PT --port COM7 erase_partition --partition-name=nvs` |
| 传 esptool 参数 | **必须用 key=value**：`--esptool-args chip=esp32c2`。⚠ 写成 `--esptool-args chip esp32c2` 会被展开成 `--chip --esp32c2` 直接报错。`--esptool-erase-args=force` 与 `--esptool-erase-args force` 两种写法都对 |
| 分区表非 0x8000 | 加 `-o 0x...` |

`--info` 可选值：`name / type / subtype / offset / size / encrypted`，默认 `offset size`。**parttool 必须在 IDF 环境（export.ps1）里跑，且会占用串口** —— 不能和 `idf.py monitor` 同时开。

| 用途 | 命令 |
|---|---|
| 看命名空间 | `python $NVSTOOL -d namespaces --color never nvs.bin` |
| 看 phy 三键 | `python $NVSTOOL -d minimal --color never nvs.bin \| Select-String "phy"` |
| 导出 blob（base64） | `python $NVSTOOL -d blobs --color never nvs.bin > blobs.txt` |
| 机器可比对 | `python $NVSTOOL -f json nvs.bin > nvs.json` |
| 完整性检查 | `python $NVSTOOL -i -d none --color never nvs.bin` |
| 页状态计数 | `python $NVSTOOL -d storage_info --color never nvs.bin` |
| 生成 NVS 镜像 | `python $NVSGEN generate nvs_new.csv nvs_new.bin 24576`（**size 用十进制**，须为 4096 倍数） |

**`nvs_tool.py` 在 release/v5.1 存在、v5.0 返回 404**。v5.0 用户拷贝 3 个文件离线使用（纯 Python 离线解析器，只吃 dump 文件）：

```powershell
mkdir E:\rfcal\nvstool
foreach ($f in @('nvs_tool.py','nvs_parser.py','nvs_logger.py')) {
  Invoke-WebRequest "https://raw.githubusercontent.com/espressif/esp-idf/release/v5.1/components/nvs_flash/nvs_partition_tool/$f" -OutFile "E:\rfcal\nvstool\$f"
}
```
> 从 GitHub 下载脚本属于引入外部文件，按贵司规程可能需报备；也可直接从公司已有的 v5.1 IDF 安装目录里拷。

**`nvs_tool.py` 确无 CSV 导出能力、确不支持加密分区**（这就是 A4 需要人工转 CSV、且加密时 A4 直接不可行的原因）。

## 9.3 取样与比对脚本

**`E:\rfcal\dump_nvs.ps1`**
```powershell
param(
  [string]$Port = "COM7",
  [string]$Tag  = "run0",
  [string]$Off  = "0x9000",   # 按 §1.4 实测值改
  [string]$Size = "0x6000",   # 按 §1.4 实测值改
  [string]$Dir  = "E:\rfcal\03_P1"
)
$out = "$Dir\nvs_$Tag.bin"
esptool.py --chip esp32c2 --port $Port --baud 460800 --after no_reset read_flash $Off $Size $out
$h = Get-FileHash -Algorithm SHA256 $out
"$Tag  $($h.Hash)  $(Get-Date -Format o)" | Tee-Object -FilePath E:\rfcal\nvs_hashes.txt -Append
$h
```

**`E:\rfcal\diff_nvs.py`**
```python
import sys, hashlib
a=open(sys.argv[1],'rb').read(); b=open(sys.argv[2],'rb').read()
print('A', hashlib.sha256(a).hexdigest(), len(a))
print('B', hashlib.sha256(b).hexdigest(), len(b))
if a==b:
    print('IDENTICAL: 整个 NVS 分区一个字节都没变（加分项，不出现属正常）'); sys.exit(0)
SEC=0x1000
for i in range(0, min(len(a),len(b)), SEC):
    if a[i:i+SEC]!=b[i:i+SEC]:
        n=sum(1 for x,y in zip(a[i:i+SEC],b[i:i+SEC]) if x!=y)
        print(f'sector +0x{i:05x} (page {i//SEC}) 有 {n} 字节不同')
```

**`E:\rfcal\calhash.py`** —— 只比 phy 三键（**唯一的主判据**）
```python
import json, sys, hashlib
def cal(p):
    j=json.load(open(p, encoding='utf-8')); out={}
    def walk(o):
        if isinstance(o,dict):
            ns=str(o.get('namespace','')); k=str(o.get('key',''))
            if 'phy' in ns and k in ('cal_version','cal_mac','cal_data'):
                v=o.get('data', o.get('value'))
                s=v if isinstance(v,str) else json.dumps(v,sort_keys=True)
                out[k]=(len(s), hashlib.sha256(s.encode()).hexdigest())
            for x in o.values(): walk(x)
        elif isinstance(o,list):
            for x in o: walk(x)
    walk(j); return out
for p in sys.argv[1:]:
    print(p); [print('  ',k,v) for k,v in sorted(cal(p).items())]
```
> 若 JSON 字段名与脚本假设不符 `[待现场确认]`，直接看 `-d blobs` 文本输出手工比对 base64，同样有效。

## 9.4 关键日志抓取

```powershell
Select-String -Path E:\rfcal\**\log_*.txt -Pattern "phy_version|falling back to full calibration|Saving new calibration data|calibration data MAC check failed|failed to get cal_data|rst:0x"
```

## 9.5 完整命令流（B1 推荐路线，一屏）

```powershell
# ===== 阶段 -1：不可补做的取证（物理存证 → X-ray → 无损物理检查）=====

# ===== 阶段 0：环境与闸门 =====
esptool.py version                                                        # 定命令风格
espefuse.py -p COM7 summary            > E:\rfcal\00_backup\efuse.txt      # 闸门①
esptool.py --chip esp32c2 -p COM7 flash_id ; esptool.py --chip esp32c2 -p COM7 read_mac
esptool.py --chip esp32c2 -p COM7 -b 460800 read_flash 0 ALL E:\rfcal\00_backup\BAD_full.bin
esptool.py --chip esp32c2 -p COM7 -b 460800 read_flash 0 ALL E:\rfcal\00_backup\BAD_full_2.bin
fc /b E:\rfcal\00_backup\BAD_full.bin E:\rfcal\00_backup\BAD_full_2.bin    # 闸门②
python -c "d=open(r'E:\rfcal\00_backup\BAD_full.bin','rb').read(); open(r'E:\rfcal\01_ptable\pt.bin','wb').write(d[0x8000:0x8000+0xC00])"
python $env:IDF_PATH\components\partition_table\gen_esp32part.py E:\rfcal\01_ptable\pt.bin E:\rfcal\01_ptable\pt.csv
esptool.py --chip esp32c2 -p COM7 -b 460800 read_flash 0x9000 0x6000 E:\rfcal\00_backup\nvs_BAD.bin
python $NVSTOOL -i -d all --color never E:\rfcal\00_backup\nvs_BAD.bin     # 闸门③
esptool.py image_info --version 2 E:\rfcal\02_idfver\app.bin               # 定 IDF 版本

# ===== 阶段 0.5：牺牲品闭环预演（整圈跑通才允许继续）=====

# ===== 阶段 1：§5 基线（S0），A/B/A/B ≥5 轮，含 σ_d 空实验 =====

# ===== 阶段 2：B1 重校准（§0.2 四问 → §4.1 环境布置 → 执行）=====
python $PT --port COM7 read_partition  --partition-name=factory --output E:\rfcal\07_recal\cust_app.bin
python $PT --port COM7 write_partition --partition-name=factory --input  E:\rfcal\07_recal\phycal_tool.bin
#   上电 → 串口输入 ERASE → 观察 full cal 日志 → 记录 phy_version / max_tx_power
python $PT --port COM7 write_partition --partition-name=factory --input  E:\rfcal\07_recal\cust_app.bin
esptool.py --chip esp32c2 -p COM7 read_flash 0x9000 0x6000 E:\rfcal\07_recal\nvs_after.bin
python $NVSTOOL -d minimal --color never E:\rfcal\07_recal\nvs_after.bin | Select-String "phy"

# ===== 阶段 3：§5 复测（S1），裸板态 + 整机态各一遍 =====

# ===== 阶段 4：§6 可逆复现（S2→S3→S4，五步回灌，盲测）=====

# ===== 阶段 5：§7 判定 + §4.5.3 向客户提问 + 复发监视 =====
```

---

## 附：本文标注为 `[待现场确认]` 的项（不得当成既定事实）

| 项 | 说明 |
|---|---|
| v4.1~v4.4 分支的写回条件、小写日志串、API 未改名、文件路径迁移 | 本轮核实集中在 v5.0/v5.1/master。若 §1.2 定版落在 v4.x，**暂停日志判据**，按具体 tag 重抓源码核对后再继续 |
| v5.0 私有头 `components/esp_phy/include/phy.h` 与 `ESP_CAL_DATA_CHECK_FAIL` 定义位置 | 工位无需引用此私有头，判定完全依赖已核实的 `Saving new calibration data due to` 日志 |
| `python -m esptool` 模块入口是否可用 | 统一以 `esptool.py version` 结果为准 |
| iperf 例程"只兼容 iperf 2.x、不兼容 iperf3" | 命令与选项已核实可直接用；兼容性工位上两分钟验证即可定论 |
| `esp_tx -c 0` 的语义（不发 / 无限发） | 先用 `-c 100000` 并用 sniffer + 电流表确认，再决定是否用 0 |
| `cert_test` 的 `phy_rx_rssi` 单位 | 头文件**未标注单位**；README 示例 `-527` 推测为 0.1 dBm 刻度，仅作相对量用 |
| ESP8684 数据手册的电流/功率/灵敏度数值 | 未独立核实且内部工况标注不一致；一律降格为"参考量级"，判定只用与良品的相对差 |
| ESPC2-M1 内部 GPIO8 的处理、chip revision (eco 版本) | 上工位前查我方模组内部原理图确认 |
| `calhash.py` 假设的 JSON 字段名 | 不符时改看 `-d blobs` 文本输出手工比对 base64 |
| `parttool --esptool-erase-args=force` 在 C2 上的实际效果 | 未在 C2 上实测 |
| `nvs_tool.py` 从 v5.1 拷到 v5.0 环境使用的兼容性 | 需现场验证 |