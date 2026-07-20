import os
import sys
import subprocess
from datetime import datetime, timedelta
from PIL import Image

# ================= 基础全局配置 =================
IMAGE_DIR = "images"
SIDEBAR_PATH = "_sidebar.md"
ALLOWED_EXTENSIONS = (".png", ".jpg", ".jpeg")
# ===============================================

def create_daily_log():
    """1. 自动新建今日日志，并更新侧边栏链接"""
    print("\n[正在执行] 1. 一键新建今日日志...")
    today_str = datetime.now().strftime("%Y-%m-%d")
    log_file_path = f"daily/{today_str}.md"

    if not os.path.exists("daily"):
        os.makedirs("daily")

    template = f"""# {today_str} 学习日志

---

## 🎯 今日计划
- [ ] 
- [ ] 

---

## 📝 学习记录
### 1. 核心收获
*   

---

## 🤔 今日复盘
*   **🏆 今日最大收获**：
*   **📈 待改进与明日计划**：
"""

    if not os.path.exists(log_file_path):
        with open(log_file_path, "w", encoding="utf-8") as f:
            f.write(template)
        print(f"  [成功] 已生成今日日志模板: {log_file_path}")
    else:
        print(f"  [提示] 今天的日志文件已存在: {log_file_path}")

    if os.path.exists(SIDEBAR_PATH):
        with open(SIDEBAR_PATH, "r", encoding="utf-8") as f:
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

            with open(SIDEBAR_PATH, "w", encoding="utf-8") as f:
                f.writelines(lines)
            print("  [成功] 已将今日日志链接自动添加到 _sidebar.md")
        else:
            print("  [提示] _sidebar.md 中已存在今天的日志链接")

    try:
        subprocess.run(["code", log_file_path], shell=True)
        print("  [成功] 已自动在 VS Code 中打开今日日志！")
    except Exception:
        print(f"  [提示] 请手动在 VS Code 中打开: {log_file_path}")


def compress_image(input_path, output_path):
    """自适应图片压缩算法"""
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
    """递归扫描整个项目，替换 Markdown 中的图片链接"""
    modified_count = 0
    for root, dirs, files in os.walk("."):
        if ".git" in root or "node_modules" in root:
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
                    print(f"    [链接替换] 已成功更新文件: {file_path}")
    return modified_count


def optimize_images():
    """2. 自动检索、压缩图片，并更新 Markdown 中的链接"""
    print("\n[正在执行] 2. 一键智能压缩图片...")
    if not os.path.exists(IMAGE_DIR):
        print(f"  [错误] 未找到 {IMAGE_DIR} 文件夹")
        return

    today_str = datetime.now().strftime("%Y%m%d")
    files = os.listdir(IMAGE_DIR)
    raw_images = [f for f in files if f.lower().endswith(ALLOWED_EXTENSIONS) and not f.startswith("opt_")]

    if not raw_images:
        print("  [提示] 暂无需要优化的原始图片。")
        return

    print(f"  [开始] 发现 {len(raw_images)} 张原始图片，开始进行自适应压缩...")
    for idx, filename in enumerate(raw_images):
        old_path = os.path.join(IMAGE_DIR, filename)
        ext = os.path.splitext(filename)[1].lower()
        new_filename = f"opt_{today_str}_{idx + 1:02d}{ext}"
        new_path = os.path.join(IMAGE_DIR, new_filename)

        old_size = os.path.getsize(old_path) / 1024

        try:
            compress_image(old_path, new_path)
            new_size = os.path.getsize(new_path) / 1024
            ratio = (1 - new_size / old_size) * 100
            print(f"\n  🚀 压缩成功: {filename} -> {new_filename}")
            print(f"     大小变化: {old_size:.1f}KB -> {new_size:.1f}KB (暴减: {ratio:.1f}%)")

            print("     正在全项目扫描并更新 Markdown 图片链接...")
            update_markdown_links(filename, new_filename)

            os.remove(old_path)
            print(f"     [清理] 已安全删除本地大图原图: {filename}")
        except Exception as e:
            print(f"  ❌ 处理图片 {filename} 失败: {e}")
    print("\n[完成] 所有新图片处理完毕！")


def open_project_in_vscode_and_server():
    """4. 自动在 VS Code 中打开项目，并通过 VS Code 自动任务在内部终端启动服务器"""
    print("\n[正在执行] 4. 一键开启开发工作空间...")
    
    vscode_dir = ".vscode"
    tasks_json_path = os.path.join(vscode_dir, "tasks.json")
    if not os.path.exists(vscode_dir):
        os.makedirs(vscode_dir)
        
    tasks_json_content = """{
    "version": "2.0.0",
    "tasks": [
        {
            "label": "启动 Docsify 网页服务器",
            "type": "shell",
            "command": "npx docsify-cli serve .",
            "runOptions": {
                "runOn": "folderOpen"
            },
            "presentation": {
                "reveal": "always",
                "panel": "new"
            },
            "problemMatcher": []
        }
    ]
}"""
    
    if not os.path.exists(tasks_json_path):
        with open(tasks_json_path, "w", encoding="utf-8") as f:
            f.write(tasks_json_content)
        print("  [配置] 自动为您创建了 VS Code 内部终端自动启动任务配置文件。")

    try:
        print("  -> 正在唤醒 VS Code...")
        subprocess.run(["code", "."], shell=True)
        print("  [🎉 成功] 已成功唤醒 VS Code 并载入项目！")
    except Exception as e:
        print(f"  ❌ 打开 VS Code 失败，请确保 code 命令已加入环境变量。错误: {e}")


def extract_section(file_path):
    """解析每日日志，精准提取其中的【📝 学习记录】与【🤔 今日复盘】内容"""
    if not os.path.exists(file_path):
        return "", ""
        
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
        
    record = ""
    review = ""
    
    record_start = content.find("## 📝 学习记录")
    review_start = content.find("## 🤔 今日复盘")
    
    if record_start != -1:
        rest_of_content = content[record_start + len("## 📝 学习记录"):]
        end_idx = rest_of_content.find("---")
        if end_idx == -1:
            end_idx = rest_of_content.find("## 🤔 今日复盘")
        
        if end_idx != -1:
            record = rest_of_content[:end_idx].strip()
        else:
            record = rest_of_content.strip()
            
    if review_start != -1:
        rest_of_content = content[review_start + len("## 🤔 今日复盘"):]
        end_idx = rest_of_content.find("---")
        if end_idx != -1:
            review = rest_of_content[:end_idx].strip()
        else:
            review = rest_of_content.strip()
            
    return record, review


def generate_weekly_report():
    """5. 一键获取过去 7 天的每日日志，自动编译并生成周报，精准写入归档目录"""
    print("\n[正在执行] 5. 开始一键提炼生成本周周报...")
    
    today = datetime.now()
    today_str = today.strftime("%Y-%m-%d")
    weekly_dir = "weekly"
    weekly_file_path = f"{weekly_dir}/{today_str}_weekly.md"

    if not os.path.exists(weekly_dir):
        os.makedirs(weekly_dir)

    # 1. 查找过去 7 天内存在的所有日记文件
    valid_logs = []
    for i in range(7):
        check_date = today - timedelta(days=i)
        date_str = check_date.strftime("%Y-%m-%d")
        log_path = f"daily/{date_str}.md"
        if os.path.exists(log_path):
            valid_logs.append((date_str, log_path))

    valid_logs.reverse()

    if not valid_logs:
        print("  [错误提示] 过去 7 天未发现任何每日学习日志，无法生成周报！")
        return

    print(f"  [发现] 在过去 7 天内共找到 {len(valid_logs)} 篇日记，正在提取内容并生成周报...")

    # 2. 构造周报内容
    start_date = valid_logs[0][0]
    end_date = valid_logs[-1][0]
    
    weekly_content = f"""# 📊 本周技术周报总结 ({start_date} 至 {end_date})

> **💡 系统提示**：本周报由 Wiki 自动化运维中枢通过自动读取过去 7 天内的每日学习日志汇编提炼生成。

---

## 💻 本周技术输入汇总
"""

    for date_str, log_path in valid_logs:
        record, review = extract_section(log_path)
        
        weekly_content += f"\n### 📅 {date_str} 学习日志\n"
        
        if record:
            weekly_content += f"\n#### 📝 核心技术输入：\n{record}\n"
        else:
            weekly_content += "\n*(当天无技术输入记录)*\n"
            
        if review:
            indented_review = "\n".join([f"> {line}" for line in review.split("\n")])
            weekly_content += f"\n#### 🤔 当日总结复盘：\n{indented_review}\n"
            
        weekly_content += "\n---\n"

    # 3. 写入周报文件
    with open(weekly_file_path, "w", encoding="utf-8") as f:
        f.write(weekly_content)
    print(f"  [成功] 周报已成功生成: {weekly_file_path}")

    # 4. 自动将周报链接写入 _sidebar.md 的“阶段周报总结”目录下
    if os.path.exists(SIDEBAR_PATH):
        with open(SIDEBAR_PATH, "r", encoding="utf-8") as f:
            lines = f.readlines()

        # 定义三级菜单缩进格式：4个空格，比二级菜单更深一级
        new_link_line = f"    * [{today_str} 周报](weekly/{today_str}_weekly.md)\n"
        link_exists = any(f"{today_str}_weekly" in line for line in lines)

        if not link_exists:
            # A. 先检查 _sidebar.md 里有没有 "📊 阶段周报总结" 目录大项
            section_idx = -1
            for idx, line in enumerate(lines):
                if "📊 阶段周报总结" in line:
                    section_idx = idx
                    break

            if section_idx != -1:
                # 如果已存在“📊 阶段周报总结”目录，直接在它下方插入最新的周报链接
                lines.insert(section_idx + 1, new_link_line)
                print("  [成功] 已将本期周报自动添加至 📊 阶段周报总结 目录下！")
            else:
                # B. 如果不存在该目录，寻找“scratchpad.md”作为锚点，在其下方初始化该目录和第一条链接
                anchor_idx = -1
                for idx, line in enumerate(lines):
                    if "scratchpad.md" in line:
                        anchor_idx = idx
                        break
                
                if anchor_idx != -1:
                    # 依次插入：二级大项“  * 📊 阶段周报总结” 和 三级子链接 “    * [xxxx] 周报”
                    lines.insert(anchor_idx + 1, f"  * 📊 阶段周报总结\n{new_link_line}")
                    print("  [配置] 侧边栏未发现周报目录，已自动创建 [📊 阶段周报总结] 并完成归档！")
                else:
                    # 备用防错：直接追加到侧边栏末尾
                    lines.append(f"  * 📊 阶段周报总结\n{new_link_line}")

            # 写回 _sidebar.md
            with open(SIDEBAR_PATH, "w", encoding="utf-8") as f:
                f.writelines(lines)
        else:
            print("  [提示] _sidebar.md 中已存在本期周报的链接")

    # 5. 自动在 VS Code 中打开该周报
    try:
        subprocess.run(["code", weekly_file_path], shell=True)
        print("  [成功] 已在 VS Code 中为您打开本周周报！")
    except Exception:
        print(f"  [提示] 请手动在 VS Code 中打开: {weekly_file_path}")


def git_push_assets():
    """6. 一键打包并推送到 GitHub 远程仓库"""
    print("\n[正在执行] 6. 一键同步推送到远程 Git 仓库...")
    
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    commit_msg = f"Wiki Auto-Update: {now_str}"
    
    try:
        print("  -> 运行: git add .")
        subprocess.run(["git", "add", "."], check=True)
        
        print(f"  -> 运行: git commit -m \"{commit_msg}\"")
        result = subprocess.run(["git", "commit", "-m", commit_msg], capture_output=True, text=True)
        
        if "nothing to commit" in result.stdout or "无文件要提交" in result.stdout:
            print("  [提示] 检查完毕：本地内容无任何改动，无需提交。")
        else:
            print("  [成功] 本地代码版本提交成功！")
            
            print("  -> 运行: git push")
            subprocess.run(["git", "push"], check=True)
            print("  [🎉 成功] 您的最新 Wiki 已成功部署至 GitHub Pages！")
            
    except subprocess.CalledProcessError as e:
        print(f"  ❌ Git 命令执行失败，请检查网络或配置: {e}")
    except Exception as e:
        print(f"  ❌ 发生未知错误: {e}")


def show_menu():
    """显示极客感十足的控制台菜单"""
    os.system('cls' if os.name == 'nt' else 'clear')
    print("=====================================================")
    print("                 🚀 Wiki控制台")
    print("=====================================================")
    print("   1. 📅 一键新建今日日志 (自动同步侧边栏/打开VS Code)")
    print("   2. 📸 一键智能压缩图片 (自动更新全局 Markdown 链接)")
    print("   3. 🔄 运行全部 (新建今日日志 + 压缩优化图片)")
    print("   4. 💻 一键开启开发沙盒 (VS Code 内部集成终端跑服务器)")
    print("   5. 📊 一键提炼生成本周周报 (自动汇总过去7天日志)")
    print("   6. 🚀 一键打包推送到 GitHub (自动部署静态网页)")
    print("   7. ❌ 退出管理系统")
    print("=====================================================")


def main():
    while True:
        show_menu()
        choice = input("请选择操作 [1-7] 并回车: ").strip()
        if choice == "1":
            create_daily_log()
            input("\n按回车键返回主菜单...")
        elif choice == "2":
            optimize_images()
            input("\n按回车键返回主菜单...")
        elif choice == "3":
            create_daily_log()
            optimize_images()
            input("\n按回车键返回主菜单...")
        elif choice == "4":
            open_project_in_vscode_and_server()
            input("\n按回车键返回主菜单...")
        elif choice == "5":
            generate_weekly_report()
            input("\n按回车键返回主菜单...")
        elif choice == "6":
            git_push_assets()
            input("\n按回车键返回主菜单...")
        elif choice == "7":
            print("\n感谢使用，祝您备战面试顺利，代码无 Bug！👋")
            break
        else:
            input("\n[输入错误] 请输入 1~7 之间的数字。按回车继续...")

if __name__ == "__main__":
    main()