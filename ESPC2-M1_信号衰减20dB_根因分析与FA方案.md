# ESPC2-M1（ESP8684 / ESP32-C2）运行约 2 个月后个别模组 RSSI 下降 ~20 dB — 根因分析与锁定方案

- 客户：途见（Tachintech），经外包厂采购约 2000 片，产品已量产交付上千套
- 现象：投运约 2 个月后个别模组 Wi‑Fi 信号减弱约 20 dB；客户交叉验证（换模组/换板）故障跟随模组走；运行时模组表面 50–70 ℃
- 已寄回故障模组 1–2 片
- 标注：**[已核实]** = 有乐鑫官方文档/源码/GitHub issue 证据；**[推断]** = 工程经验/基于现象的推理

---

## 0. 先说结论

1. **这不是"温度正常工作范围内的老化"，也基本不是晶振漂移。** 正常固件下 PHY 每 1 s 做一次 PLL/校准参数温度跟踪，TX 功率有温补；50–70 ℃ 表面温度、结温 70–90 ℃，远低于芯片 HTOL 125 ℃/1000 h 的可靠性等级，温度效应量级只有 1–2 dB 且可逆 **[已核实机制 + 推断量级]**。晶振 2 个月老化 ±1–3 ppm，即使漂出 ±25 ppm 也表现为 EVM 差/掉线，不会是"RSSI 低 20 dB 但还连着" **[推断，机理已核实]**。
2. **乐鑫公开资料中不存在 C2 "运行一段时间后 RF 衰减" 的已知问题**：ESP32-C2 勘误只有 1 条（v1.0 不支持 40 MHz 晶振）；esp-phy-lib 所有触及 C2 的提交、GitHub esp-idf issue 检索均无此类记录 **[已核实]** → 批量硅片缺陷概率极低，指向**个体级硬件失效或个体级校准数据问题**。
3. **最相似的官方先例**：esp-idf issue #15763（2025-04，ESP32-S3-WROOM，同设计板中个别模组 RSSI 差 40 dB，强制全校准无效，换模组恢复），乐鑫工程师判定"RX 前端很可能被 ESD 损伤，反复 ESD 会逐渐恶化" **[已核实]**。
4. **20 dB、不可逆、个别、跟模组走、2 个月发作**——最吻合的是"互易型（TX/RX 同降）无源通路失效"或"RF 引脚 ESD 潜伏损伤"，其次是助焊剂/湿气电化学迁移、屏蔽罩压迫、NVS 坏校准数据（软件态但也跟模组走）。**必须先分清 TX 方向和 RX 方向各降多少，再进硬件 FA。**

---

## 1. 根因假设清单（按可能性 × 与现象吻合度排序）

| # | 假设 | 机理 / 为何吻合 | TX/RX | 如何证实/排除 | 若成立的对策 |
|---|---|---|---|---|---|
| 1 | **天线馈线 / π 型匹配 0402 元件焊点开裂或元件裂纹；QFN 底部接地焊盘/LNA_IN 焊点空洞裂纹** [推断] | 有工艺缺陷（空洞、锡少、润湿不良、二次回流/返修过温、板弯应力）的个别焊点在几十~几百次开关机温循（ΔT 30–50 ℃）后即可开裂；串联元件裂缝在 2.4 GHz 呈 0.05–0.2 pF 小电容 → 插损 15–30 dB。**个别 / 2 个月 / 20 dB / 双向** 全部吻合 | 双向同降 | X-ray（QFN 底盘空洞率、RF 引脚焊点）、显微裂纹；热风/冷冻剂局部加热看 RSSI **阶跃**、按压恢复；拆罩 LCR 在线测元件值；VNA 探针测馈点 S11 对比良品；**整体重回流一次后恢复即锁定** | 模组厂 SMT：锡量/回流曲线/空洞率管控；要求客户外包厂提供回流曲线与次数（规格 ≤2 次）；已发货按批次统计失效率决定换货范围 |
| 2 | **ESD/EOS 潜伏损伤（LNA_IN 引脚 ESD 钳位管 / LNA 输入管）** [推断，有官方先例 #15763] | PCB 天线暴露于外壳开口/人手/装配静电，累积放电致漏电渐增；钳位管变阻性 → 并联负载馈点 → 双向；仅 LNA 管损伤 → 只 RX。VDD >3.6 V 浪涌（DC-DC 过冲、热插拔）则伤 PA → 只 TX + 电流异常 | 双向或仅 RX | LNA_IN 对 GND 的 DC I‑V 曲线（曲线仪 ±1 V）对比良品出现漏电/软击穿；不随温度阶跃、不随按压/回流恢复；换芯片到良品 PCB 后故障跟芯片走 | 客户端：外壳/装配 ESD 防护、天线净空、产线接地稽核；必要时天线馈点加 ESD 器件（需评估 RF 影响） |
| 3 | **助焊剂残留/湿气 → 电化学迁移（枝晶）/ 腐蚀 / 锡须** [推断] | 免清洗助焊剂残留 + >60–70 %RH + 直流偏压，数周~数月长出枝晶；强依赖局部污染 → 天然"个别"；桥接匹配点到地呈几十~几百 Ω 并联可 >20 dB，常伴时好时坏 | 双向 | 显微/SEM‑EDX 见树枝状析出、白色结晶；离子污染度（ROSE/IC）超标；并联电容对地漏电（正常 >10 MΩ）；IPA 清洗或烘烤后部分恢复 | 外包厂/模组厂清洗与助焊剂选型；客户使用环境湿度评估 |
| 4 | **屏蔽罩变形 / 客户装配压迫使罩壁触碰匹配元件或馈线** [推断] | 压合外壳、螺丝扭矩、跌落 → 短路到地或严重失谐，可 >20 dB | 双向 | 拆罩前后 RSSI 对比、轻敲罩体 RSSI 变化、X-ray 看罩与元件间距、罩下压痕 | 结构复核、装配指导 |
| 5 | **NVS 中 PHY 校准数据异常**（首次校准环境不当 / 校验问题）[已核实机制] | ESP-IDF 默认 partial cal，复用首次 full cal 存于 NVS `phy` 命名空间（cal_version/cal_mac/cal_data）的数据，仅 MAC/PHY 版本变化或校验失败才重做；乐鑫 Kconfig 原文提示"天线断开上电容易校出坏数据"。内嵌 flash 在芯片里 → **换板也跟模组走**。老 phy 版本（<270）有 C2 校准校验失败 bug | 双向 | `esptool read_flash` 备份 NVS 留证 → 调 `esp_phy_erase_cal_data_in_nvs()` 或 menuconfig `CONFIG_ESP_PHY_CALIBRATION_MODE=full` → 重启复测；**恢复即软件问题** | 固件加"擦校准重启"诊断入口；产线首次上电保证天线状态正常；升级 IDF |
| 6 | **MSL3 超时未烘烤 → 封装分层/键合线拉伤后渐变高阻** [推断] | 外包厂多手转运常见；回流"爆米花"当时仍导通，数周~数月温循后间歇开路 | 双向 | C‑SAM 超声看分层、开盖看键合颈裂纹；同批留样抽检评估批量风险 | 核查开袋/烘烤记录（168 h @ 25±5 ℃/60 %RH） |
| 7 | 晶振漂移/失效 [机理已核实，不吻合] | 首年老化 ±1–3 ppm；乐鑫要求 ±10 ppm，802.11 容差 ±25 ppm；表现为 EVM/掉线而非 RSSI | — | 单音 `wifiscwout` 频谱仪测频偏 ppm；冷热喷看跳变 | 排除项（但要测一次闭环） |
| 8 | PA/LNA 本征磨损（热载流子/电迁移）[推断，不吻合] | Tj 70–90 ℃，数年内 0.5–2 dB 且仅 TX、全体一致 | 仅 TX | 温度平滑相关、需芯片级 FA | 排除项 |
| 9 | 电源纹波/欠压、天线区涂覆/吸湿失谐 | 换板后应随板走；涂覆一般装配后立即出现且整批一致 | — | 量模组 3V3 与 TX 纹波闭环 | 排除项 |

---

## 2. 锁定根因的执行流程（先软后硬、先无损后破坏，每步以同批良品同夹具对照）

| 步骤 | 目的 | 做法 | 判定 | 工具 |
|---|---|---|---|---|
| 1 复现 | 确认失效、量化差值 | 屏蔽箱内同一夹具/AP/衰减，故障品 vs 2 片同批良品跑同一诊断固件：打印 phy_version、芯片版本、`esp_wifi_get_max_tx_power`、国家码；每秒打印 rssi/noise_floor/片温 30 min | 差值 ≥10 dB 复现成立 | 屏蔽箱、固定 AP、串口 |
| 2 分方向 | 缩小范围 | AP 端看模组 RSSI（TX 方向）+ 模组端看 AP RSSI（RX 方向）+ PER/速率 | 双向同降 → 无源通路/钳位管/焊点；仅 RX → LNA/RX 校准；仅 TX → PA/供电/功率设置 | 同上 |
| 3 软件排除 | 排除校准数据 | 备份 NVS；`esp_phy_erase_cal_data_in_nvs()` 或 `CONFIG_ESP_PHY_CALIBRATION_MODE=full`；核对 `CONFIG_ESP_PHY_MAX_WIFI_TX_POWER`、`CONFIG_ESP_PHY_REDUCE_TX_POWER`、`CONFIG_ESP_PHY_IMPROVE_RX_11B`、phy_init 分区是否被 PowerLimitTool 限功率 | 恢复 → 校准问题；不恢复 → 硬件 | esptool、nvs_tool |
| 4 传导定量 | 定位 TX/RX/通路 | 拆罩，在天线侧断开最后一个串联元件焊 U.FL/半刚同轴（良品同步改）；EspRFTestTool 或 esp-idf `examples/phy/cert_test`：`esp_tx` 测功率/EVM、`wifiscwout` 测频偏、`esp_rx`+`get_rx_result` 测灵敏度与 -60 dBm 输入下 RSSI 读数；同时记 TX 电流（11b@21 dBm 典型 ~370 mA） | 电流正常但功率低 → PA 之后无源损耗；电流也低 → PA/供电；频偏 >±10 ppm → 查晶振；RX 灵敏度差 20 dB 而 TX 正常 → LNA | 综测仪/频谱仪+信号源、电流表 |
| 5 无损硬件检查 | 找物理证据 | 显微（裂纹、锡须、枝晶、罩压痕）、X-ray（QFN 底盘空洞、RF 引脚焊点、0402 焊点）、LCR/万用表（串联元件通断、并联电容对地 >10 MΩ）、VNA S11 对比、LNA_IN I‑V 曲线对比、局部热风/冷冻剂 + 按压看 RSSI 阶跃 | 阶跃 → 焊点/裂纹/键合；平滑 → 半导体；I‑V 漏电 → ESD | 显微镜、X-ray、LCR、VNA、曲线仪 |
| 6 半破坏 | 二分定位 | 重回流一次复测（恢复 → 焊点类）；逐级换匹配 L/C → 晶振 → 芯片互换到良品 PCB | 故障跟随哪一步即锁定 | 返修台（先在良品练手确认返修不引入变化） |
| 7 破坏/复现 | 定性 + 评估批量 | 切片、SEM‑EDX、离子色谱、C‑SAM、开盖 EMMI；良品做 -40↔105 ℃ 热冲击 100 cyc、85 ℃/85 %RH 168 h 看能否诱发 | 复现 → 批量风险；不复现 → 个体/客户端诱因 | 第三方实验室 |

---

## 3. 需向客户收集的信息（拆解前尽量收齐）

- 失效数 / 总出货数、模组批次日期码、失效模组 MAC、投运到失效时间分布（渐变还是突变，冷机/断电是否恢复）
- **RSSI 测量端**：模组端看 AP（RX）与 AP 端看模组（TX）各降多少；丢包/速率变化
- 固件：IDF 版本、启动日志 `phy_version`、TX 功率设置、国家码、省电模式、是否 OTA 换过 IDF/PHY 版本、复位原因/brownout 记录
- 供电：拓扑、模组 3V3 电压与 TX 突发时纹波、是否 AC‑DC 供电
- 组装：外包厂回流曲线与次数、MSL3 开袋/烘烤记录、清洗剂/助焊剂、返修/手焊记录、是否三防漆/灌胶/**超声波清洗**（乐鑫模组手册明示超声振动可损伤内置晶振）
- 结构/环境：外壳材质、天线净空、开口/人手接触、压合方式、温湿度、现场照片，能否寄回整机

---

## 4. 客户三个问题的建议回复要点

**Q1 内置晶振精度？**
ESPC2-M1 采用 26 MHz 晶振（**研发需从 BOM 确认并写明 ppm / 温漂 / 老化等级**）；乐鑫设计指南要求室温 ±10 ppm，乐鑫自家 ESP8684 模组也用 26 MHz ±10 ppm；802.11 2.4 GHz 容差 ±25 ppm **[已核实]**。老化首年典型 ±1–3 ppm（工程经验值），2 个月内不会漂到影响 RSSI；频偏超差表现为 EVM 差/掉线而非 RSSI 低 20 dB。

**Q2 正常工作温度范围，过热会怎样？**
规格 -40~105 ℃（与乐鑫 ESP8684H2X/H4X 及其模组一致；**需确认封装芯片为 H 版而非早期 85 ℃ 的 N 版**）**[已核实]**。表面 50–70 ℃、结温约高 10–20 ℃，在规格内。过热是**可逆**效应：PHY 带温补，25→85 ℃ TX 功率典型变化 1–2 dB、灵敏度劣化 1–2 dB（经验值；乐鑫 FAQ 确认关闭温补时 80 ℃ 功率明显下降）；不可逆损伤仅在结温长期 >125 ℃ 或短时 >150 ℃ 才需考虑（依据 HTOL 125 ℃/1000 h、HTSL 150 ℃/1000 h）**[已核实]**。

**Q3 过热对时钟漂移、射频放大电路衰减有没有测试数据？**
乐鑫芯片/模组手册所有 RF 指标仅在 25 ℃/3.3 V 给出，无高温衰减曲线与时钟漂移数据；ESPC2-M1 规格书同样没有 **[已核实]**。可承诺：向乐鑫索取芯片级温度特性 + 在良品上按 -20/25/60/85/105 ℃ 温箱实测 TX 功率/EVM/频偏/灵敏度并出报告。
**并强调**：本案 20 dB、不可逆、跟随个体的劣化与温度效应量级不符，根因更可能在焊接/ESD/污染/校准，需按 FA 流程锁定。

---

## 5. 短期遏制与长期预防

- **短期**：客户端对故障品先擦 phy 校准数据重启验证（1 天内可做）；下发诊断固件收集失效率与方向性数据；模组厂对同批留样做 X-ray/离子污染度/温冲抽检；已发货产品按批次风险评估，等 FA 结论定换货范围。
- **来料/生产**：晶振与匹配 L/C 供应商及等级冻结（±10 ppm、C0G）；MSL3 开袋 168 h/烘烤记录强制化；QFN 底盘空洞率抽检；回流 ≤2 次并要求客户外包厂提供曲线；清洗/助焊剂残留管控；ESD 稽核。
- **固件**：建议客户 IDF ≥ v5.1.4 / v5.2.2（C2 phy ≥ 320，含校准校验失败与 PLL track 修复）；产线首次上电保证天线状态正常再校准；应用保留"擦校准重启"诊断入口；启动日志上报 phy_version 便于追溯。

---

## 6. 已核实事实与来源

| 事实 | 来源 |
|---|---|
| ESP32-C2 勘误仅 XTAL-5948（v0.0/v1.0 不能用 40 MHz 晶振），无 RF 劣化条目 | docs.espressif.com/projects/esp-chip-errata/en/latest/esp32c2/ |
| RF 校准：默认 partial；full 触发条件为 NVS 无数据/被擦、MAC 变化、PHY 版本变化、数据损坏；NVS 命名空间 `phy`，键 cal_version/cal_mac/cal_data；`esp_phy_erase_cal_data_in_nvs()`；`CONFIG_ESP_PHY_CALIBRATION_MODE`（0 partial/1 none/2 full）；Kconfig 原文提示天线断开上电易校出坏数据 | docs.espressif.com/projects/esp-idf/en/latest/esp32c2/api-guides/RF_calibration.html；components/esp_phy/src/phy_init.c、Kconfig |
| 运行时温度跟踪：`phy-track-pll-timer` 周期 `CONFIG_ESP_PHY_PLL_TRACK_PERIOD_MS`（默认 1000 ms）调用 `phy_param_track_tot()` | components/esp_phy/src/phy_common.c、Kconfig |
| 乐鑫 FAQ："RF 测试固件默认关温补，80 ℃ 功率下降，`txpwr_track_en 1 1 0` 开启"；"外置天线须在上电前接好，模组上电自校准含功率校准" | docs.espressif.com/projects/esp-faq/en/latest/hardware-related/RF-related.html |
| ESP8684 手册：RF 指标 25 ℃/3.3 V(±5%)；H2X/H4X 环境温度 -40~105 ℃；HTOL 125 ℃/1000 h、HTSL 150 ℃/1000 h；HBM 2 kV/CDM 1 kV；TX 11b 21.5 dBm、RX 1 Mbps -99 dBm；支持 26/40 MHz 晶振 | documentation.espressif.com/esp8684_datasheet_en.html |
| 硬件设计指南：晶振精度 ±10 ppm；"晶振制造缺陷（频偏 >±10 ppm、温度范围内不稳定）可能导致 RF 性能下降"；VDDA3P3 10 µF+0.1 µF；纹波 <80/120 mV | docs.espressif.com/projects/esp-hardware-design-guidelines/en/latest/esp32c2/schematic-checklist.html |
| 乐鑫 ESP8684-WROOM-02C/MINI-1：26 MHz ±10 ppm；MSL3；**仅允许 1 次回流**（ESPC2-M1 允许 2 次）；警告超声波振动损伤晶振 | esp8684-wroom-02c_datasheet_en.pdf、esp8684-mini-1_mini-1u_datasheet_en.pdf |
| esp-phy-lib C2 相关修复：phy 230 低温断连、240 部分芯片灵敏度、270 校准校验失败、280 rx bug、300 BLE CCA、320 随 IDF v5.1.4、340 深睡后校验 NVS 校准值、360/372 RXDC 优化；无"高温 TX 下降/长期衰减"条目（注：闭源库，提交信息极简，"未提及"≠"未修过"） | github.com/espressif/esp-phy-lib/commits/master |
| ESP-IDF 发布说明：v5.2/v5.1.1 "C2 高低温断连修复"（BLE 侧 bt_track_pll_cap）；v5.0.5 26 MHz none 模式校准错误；v5.2.2 频繁开关 PHY 的 PLL track；v5.3/v5.1.3/v5.0.6 BB PLL 未锁定；v5.5/v5.4.2 C2 v2.0 tsens 读数异常 | github.com/espressif/esp-idf/releases |
| 先例 issue #15763：S3 模组个体 RSSI 差 40 dB、擦 flash 强制全校准无效、换模组恢复；乐鑫："RX 很可能 ESD 损伤，反复 ESD 会逐渐恶化" | github.com/espressif/esp-idf/issues/15763 |
| GitHub esp-idf issue 检索（esp32c2/8684 × rssi/tx power/signal weak/sensitivity/temperature）无 C2 运行后 RSSI 衰减报告 | api.github.com/search/issues |
| ESPC2-M1 规格：-40~105 ℃、MSL3、回流 ≤2 次、峰值 240–250 ℃、HBM 2 kV/CDM 500 V、TX 11b 20.5 dBm、RX 11 Mbps -90 dBm、3.3 V/≥500 mA | E:\CC_EMD\模组\ESPC2-M1_User_Manual.pdf |

**推断项**（需以寄回模组的 FA 结果闭环）：各硬件失效机理的时间尺度与 dB 幅度、温度对 RF 的 1–2 dB 经验值、晶振老化速率、根因排序权重、RSSI 受 RX 增益校准影响（基于 ROM 符号命名推测，乐鑫未公开）。
