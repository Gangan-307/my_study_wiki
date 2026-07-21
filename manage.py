import os
import sys
import json
import re
import shutil
import subprocess
from datetime import datetime, timedelta
from PIL import Image

# ================= 颜色配置 (ANSI Escape Codes) =================
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BLUE = "\033[94m"
CYAN = "\033[96m"
RESET = "\033[0m"

# ================= 辅助日志输出函数 =================
def log_success(msg): print(f"  {GREEN}[成功]{RESET} {msg}")
def log_info(msg): print(f"  {BLUE}[正在执行]{RESET} {msg}")
def log_warn(msg): print(f"  {YELLOW}[提示]{RESET} {msg}")
def log_error(msg): print(f"  {RED}[错误]{RESET} {msg}")

# ================= 动态配置管理 =================
CONFIG_FILE = "wiki_config.json"

DEFAULT_CONFIG = {
    "image_dir": "images",
    "backup_dir": "backup/images_raw",
    "sidebar_path": "_sidebar.md",
    "allowed_extensions": [".png", ".jpg", ".jpeg"],
    "daily_template": "# {date} 学习日志\n\n---\n\n## 🎯 今日计划\n- [ ] \n- [ ] \n\n---\n\n## 📝 学习记录\n### 1. 核心收获\n*   \n\n---\n\n## 🤔 今日复盘\n*   **🏆 今日最大收获**：\n*   **📈 待改进与明日计划**：\n",
    "weekly_template_header": "# 📊 本周技术周报总结 ({start_date} 至 {end_date})\n\n> **💡 系统提示**：本周报由 Wiki 自动化运维中枢通过自动读取日志汇编提炼生成。\n\n---\n\n## 💻 本周技术输入汇总\n",
    "tasks_json_content": "{\n    \"version\": \"2.0.0\",\n    \"tasks\": [\n        {\n            \"label\": \"启动 Docsify 网页服务器\",\n            \"type\": \"shell\",\n            \"command\": \"npx docsify-cli serve .\",\n            \"runOptions\": {\n                \"runOn\": \"folderOpen\"\n            },\n            \"presentation\": {\n                \"reveal\": \"always\",\n                \"panel\": \"new\"\n            },\n            \"problemMatcher\": []\n        }\n    ]\n}"
}

def load_config():
    """读取或初始化配置文件"""
    if not os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(DEFAULT_CONFIG, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"写入配置文件失败: {e}")
        return DEFAULT_CONFIG
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return DEFAULT_CONFIG

# 加载配置
CONFIG = load_config()

# ================= 依赖自检 (2.1) =================
def check_dependencies():
    """环境依赖项检查"""
    print(f"\n{CYAN}=================== 环境依赖自检 ==================={RESET}")
    dependencies = {
        "Git 版本管理": "git",
        "VS Code 命令行 (code)": "code",
        "Node.js 运行时 (npx)": "npx"
    }
    all_clear = True
    for name, cmd in dependencies.items():
        path = shutil.which(cmd)
        if path:
            print(f"  [√] {name:<22}: {GREEN}已就绪{RESET}")
        else:
            print(f"  [×] {name:<22}: {YELLOW}未检测到 (相关功能可能受限){RESET}")
            all_clear = False
    print(f"{CYAN}==================================================={RESET}\n")
    return all_clear

# ================= 核心业务模块 =================

def create_daily_log_and_sandbox():
    """1. 一键新建今日日志并开启开发沙盒 (合并 5.1)"""
    log_info("1. 开始一键创建今日日志并配置开发环境...")
    today_str = datetime.now().strftime("%Y-%m-%d")
    log_file_path = f"daily/{today_str}.md"

    # 1.1 生成日志文件
    if not os.path.exists("daily"):
        os.makedirs("daily")

    if not os.path.exists(log_file_path):
        template = CONFIG.get("daily_template", "").format(date=today_str)
        with open(log_file_path, "w", encoding="utf-8") as f:
            f.write(template)
        log_success(f"已生成今日日志模板: {log_file_path}")
    else:
        log_warn(f"今日日志文件已存在: {log_file_path}")

    # 1.2 同步侧边栏
    sidebar_path = CONFIG.get("sidebar_path", "_sidebar.md")
    if os.path.exists(sidebar_path):
        with open(sidebar_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        new_link_line = f"  * [{today_str} 日志](daily/{today_str}.md)\n"
        link_exists = any(today_str in line for line in lines)

        if not link_exists:
            inserted = False
            for idx, line in enumerate(lines):
                if "📅 每日学习日志" in line:
                    lines.insert(idx + 1, new_link_line)
                    inserted = True
                    break
            if not inserted:
                lines.append(new_link_line)

            with open(sidebar_path, "w", encoding="utf-8") as f:
                f.writelines(lines)
            log_success("已自动将今日日志链接添加至侧边栏。")
        else:
            log_warn("侧边栏中已存在今天的日志链接。")

    # 1.3 自动创建 VS Code 沙盒环境启动任务
    vscode_dir = ".vscode"
    tasks_json_path = os.path.join(vscode_dir, "tasks.json")
    if not os.path.exists(vscode_dir):
        os.makedirs(vscode_dir)
    
    if not os.path.exists(tasks_json_path):
        with open(tasks_json_path, "w", encoding="utf-8") as f:
            f.write(CONFIG.get("tasks_json_content", ""))
        log_success("已配置 VS Code 自动启动 Docsify 任务。")

    # 1.4 打开整个项目空间及当前日志
    try:
        log_info("正在启动 VS Code 并加载项目服务...")
        # 打开项目根目录以加载 Task
        subprocess.run(["code", "."], shell=True)
        # 打开特定编辑文件
        subprocess.run(["code", log_file_path], shell=True)
        log_success("VS Code 及沙盒后台运行就绪！")
    except Exception as e:
        log_error(f"无法自动调起 VS Code: {e}")


def compress_image(input_path, output_path):
    """底层自适应压缩核心"""
    img = Image.open(input_path)
    ext = os.path.splitext(input_path)[1].lower()
    if ext == ".png":
        if img.mode != 'P':
            img = img.convert('P', palette=Image.ADAPTIVE, colors=256)
        img.save(output_path, "PNG", optimize=True)
    else:
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
        img.save(output_path, "JPEG", quality=80, optimize=True)


def update_markdown_links(old_name, new_name):
    """遍历全站更新 Markdown 的图片路径链接"""
    modified_count = 0
    for root, dirs, files in os.walk("."):
        if any(ignored in root for ignored in [".git", "node_modules", "backup"]):
            continue
        for file in files:
            if file.endswith(".md"):
                file_path = os.path.join(root, file)
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                
                if old_name in content:
                    new_content = content.replace(old_name, new_name)
                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write(new_content)
                    modified_count += 1
                    print(f"    [替换链接] -> 修改文件: {file_path}")
    return modified_count


def optimize_images():
    """2. 智能压缩图片与原图交互式清理/备份 (新增 y/n 交互)"""
    log_info("2. 开始一键智能图像优化与备份...")
    img_dir = CONFIG.get("image_dir", "images")
    backup_dir = CONFIG.get("backup_dir", "backup/images_raw")

    if not os.path.exists(img_dir):
        log_error(f"未检测到图片目录: {img_dir}")
        return

    allowed_ext = tuple(CONFIG.get("allowed_extensions", []))
    files = os.listdir(img_dir)
    raw_images = [f for f in files if f.lower().endswith(allowed_ext) and not f.startswith("opt_")]

    if not raw_images:
        log_warn("图片目录干净，无需进行增量压缩优化。")
        return

    today_str = datetime.now().strftime("%Y%m%d")
    log_info(f"检测到 {len(raw_images)} 张原始图片，执行压缩中...")

    for idx, filename in enumerate(raw_images):
        old_path = os.path.join(img_dir, filename)
        ext = os.path.splitext(filename)[1].lower()
        new_filename = f"opt_{today_str}_{idx + 1:02d}{ext}"
        new_path = os.path.join(img_dir, new_filename)

        old_size = os.path.getsize(old_path) / 1024

        try:
            # 压缩保存
            compress_image(old_path, new_path)
            new_size = os.path.getsize(new_path) / 1024
            ratio = (1 - new_size / old_size) * 100

            print(f"\n  🚀 优化率: {filename} -> {new_filename} | 缩小: {ratio:.1f}% ({old_size:.1f}KB -> {new_size:.1f}KB)")
            
            # 替换 Markdown 链接
            update_markdown_links(filename, new_filename)

            # 新增删除原图 y/n 交互
            confirm = input(f"  ❓ 压缩完成，是否彻底删除本地原图 {filename}？\n     [y: 彻底删除 / n: 保留原图并归档至备份区] (y/n, 默认 n): ").strip().lower()
            if confirm == 'y':
                os.remove(old_path)
                log_success(f"原图已安全彻底删除: {filename}")
            else:
                # 创建备份安全区
                if not os.path.exists(backup_dir):
                    os.makedirs(backup_dir)
                backup_path = os.path.join(backup_dir, filename)
                shutil.move(old_path, backup_path)
                log_success(f"原图已安全移至备份区: {backup_path}")

        except Exception as e:
            log_error(f"处理图片 {filename} 异常: {e}")
    print(f"\n{GREEN}[处理完成] 所有图片优化及清理流程就绪！{RESET}")


def extract_section_robust(file_path):
    """利用正则高容错性读取日志模块 (优化 2.2)"""
    if not os.path.exists(file_path):
        return "", ""
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # 使用正则模糊匹配类似 "## 📝 学习记录" 的区块
    record_match = re.search(r'##\s*(?:[^\n]*?)学习记录\s*\n(.*?)(?=\n##|\n---|\Z)', content, re.DOTALL | re.IGNORECASE)
    review_match = re.search(r'##\s*(?:[^\n]*?)今日复盘\s*\n(.*?)(?=\n##|\n---|\Z)', content, re.DOTALL | re.IGNORECASE)

    record = record_match.group(1).strip() if record_match else ""
    review = review_match.group(1).strip() if review_match else ""

    return record, review


def generate_weekly_report():
    """3. 自适应区间生成本周周报 (优化 2.2 & 3.2)"""
    log_info("3. 准备生成本周阶段性周报...")
    print("   [1] 汇总过去 7 天内的全部日志 (滚动模式)")
    print("   [2] 汇总本周日志 (自本周一至今)")
    sub_choice = input("   请选择周报提取模式 [1-2] (默认 1): ").strip()

    today = datetime.now()
    target_dates = []

    if sub_choice == "2":
        # 自本周一至今天 (3.2)
        days_to_subtract = today.weekday()  # 周一是 0
        target_dates = [today - timedelta(days=i) for i in range(days_to_subtract + 1)]
    else:
        # 默认滚动 7 天
        target_dates = [today - timedelta(days=i) for i in range(7)]

    target_dates.reverse()  # 恢复正序时间流

    valid_logs = []
    for d in target_dates:
        date_str = d.strftime("%Y-%m-%d")
        log_path = f"daily/{date_str}.md"
        if os.path.exists(log_path):
            valid_logs.append((date_str, log_path))

    if not valid_logs:
        log_error("该时间区间内未发现任何学习日志，无法提取并生成周报。")
        return

    # 生成周报内容
    weekly_dir = "weekly"
    if not os.path.exists(weekly_dir):
        os.makedirs(weekly_dir)

    start_date = valid_logs[0][0]
    end_date = valid_logs[-1][0]
    weekly_file_path = f"{weekly_dir}/{end_date}_weekly.md"

    header_template = CONFIG.get("weekly_template_header", "").format(start_date=start_date, end_date=end_date)
    weekly_content = header_template

    for date_str, log_path in valid_logs:
        record, review = extract_section_robust(log_path)
        weekly_content += f"\n### 📅 {date_str} 学习日志\n"
        if record:
            weekly_content += f"\n#### 📝 核心技术输入：\n{record}\n"
        else:
            weekly_content += "\n*(当天无匹配的核心技术输入记录)*\n"
        if review:
            indented_review = "\n".join([f"> {line}" for line in review.split("\n")])
            weekly_content += f"\n#### 🤔 当日总结复盘：\n{indented_review}\n"
        weekly_content += "\n---\n"

    with open(weekly_file_path, "w", encoding="utf-8") as f:
        f.write(weekly_content)
    log_success(f"周报已聚合编译完成: {weekly_file_path}")

    # 同步侧边栏目录
    sidebar_path = CONFIG.get("sidebar_path", "_sidebar.md")
    if os.path.exists(sidebar_path):
        with open(sidebar_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        new_link_line = f"    * [{end_date} 周报](weekly/{end_date}_weekly.md)\n"
        link_exists = any(f"{end_date}_weekly" in line for line in lines)

        if not link_exists:
            section_idx = -1
            for idx, line in enumerate(lines):
                if "📊 阶段周报总结" in line:
                    section_idx = idx
                    break

            if section_idx != -1:
                lines.insert(section_idx + 1, new_link_line)
                log_success("侧边栏 [📊 阶段周报总结] 已完成周报挂载！")
            else:
                anchor_idx = -1
                for idx, line in enumerate(lines):
                    if "scratchpad.md" in line:
                        anchor_idx = idx
                        break
                if anchor_idx != -1:
                    lines.insert(anchor_idx + 1, f"  * 📊 阶段周报总结\n{new_link_line}")
                    log_success("侧边栏未发现周报目录，已自动初始化并完成周报挂载。")
                else:
                    lines.append(f"  * 📊 阶段周报总结\n{new_link_line}")

            with open(sidebar_path, "w", encoding="utf-8") as f:
                f.writelines(lines)

    # 用编辑器载入生成的周报
    try:
        subprocess.run(["code", weekly_file_path], shell=True)
    except Exception:
        log_warn(f"建议使用 VS Code 预览生成的周报: {weekly_file_path}")


def git_push_assets():
    """4. 一键部署 Git 仓库 (优化 1.2)"""
    log_info("4. 开始与远程 Git 仓库同步备份...")
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    commit_msg = f"Wiki Auto-Update: {now_str}"

    try:
        # 执行 pull 防冲突合并 (1.2)
        log_info("正在执行本地合并抓取 (git pull --rebase)...")
        subprocess.run(["git", "pull", "--rebase"], check=True)

        log_info("正在暂存更改 (git add .)...")
        subprocess.run(["git", "add", "."], check=True)

        log_info("正在构建本地版本...")
        result = subprocess.run(["git", "commit", "-m", commit_msg], capture_output=True, text=True)

        if "nothing to commit" in result.stdout or "无文件要提交" in result.stdout:
            log_warn("检测完毕：本地库没有任何文件修改，无需提交。")
        else:
            log_success("本地代码版本递交成功！")
            log_info("正在安全推送到远程仓库 (git push)...")
            subprocess.run(["git", "push"], check=True)
            log_success("Wiki 项目资源已完美部署同步至 GitHub 仓库！")

    except subprocess.CalledProcessError as e:
        log_error(f"Git 命令运行异常，请确认本地是否存在分支冲突或网络异常。细节: {e}")
    except Exception as e:
        log_error(f"处理同步流程异常: {e}")


def show_menu():
    """全新精简合并菜单"""
    os.system('cls' if os.name == 'nt' else 'clear')
    print(f"{CYAN}====================================================={RESET}")
    print(f"                 🚀 {GREEN}Wiki控制台 {RESET}")
    print(f"{CYAN}====================================================={RESET}")
    print(f"   1. 📅 {GREEN}一键新建今日日志并开启沙盒{RESET} ")
    print(f"   2. 📸 {YELLOW}一键智能压缩图片{RESET} ")
    print(f"   3. 📊 {BLUE}一键提炼生成阶段周报{RESET} ")
    print(f"   4. 🚀 {CYAN}一键安全同步到 GitHub{RESET} ")
    print(f"   5. ❌ {RED}退出管理系统{RESET}")
    print(f"{CYAN}====================================================={RESET}")


def main():
    # 启用 Windows 虚拟终端转义字符支持 (保证 cmd 色彩正常)
    if os.name == 'nt':
        os.system('')

    # 启动进行自检
    check_dependencies()
    input("按回车键正式进入控制台菜单...")

    while True:
        show_menu()
        choice = input("请选择操作 [1-5] 并回车: ").strip()
        if choice == "1":
            create_daily_log_and_sandbox()
            input("\n按回车键返回主菜单...")
        elif choice == "2":
            optimize_images()
            input("\n按回车键返回主菜单...")
        elif choice == "3":
            generate_weekly_report()
            input("\n按回车键返回主菜单...")
        elif choice == "4":
            git_push_assets()
            input("\n按回车键返回主菜单...")
        elif choice == "5":
            print(f"\n{GREEN}感谢使用，祝您备战顺利，代码无 Bug！👋{RESET}\n")
            break
        else:
            input(f"\n{RED}[输入错误]{RESET} 菜单范围 [1-5]。按回车继续...")


if __name__ == "__main__":
    main()