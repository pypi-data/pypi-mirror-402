import os
import re
import subprocess
import sys
import threading
from concurrent.futures import ThreadPoolExecutor
from git_sanity.utils import run

# ================= 配置区域 =================
# 要扫描的文件后缀
EXTENSIONS = {'.cpp', '.c', '.cc', '.cxx', '.h', '.hpp', '.hxx'}
# 忽略的目录
IGNORE_DIRS = {'.git', 'build', 'bin', 'node_modules', 'vendor', 'third_party', 'tests'}

# 敏感词正则（扫描硬编码密码、密钥）
SENSITIVE_PATTERNS = [
    (r'(?i)(password|passwd|pwd|secret|token|api_key|access_key)\s*=\s*["\'][^"\']+["\']', "可能硬编码的敏感信息"),
    (r'(?i)private_key\s*=\s*', "私钥定义风险"),
    (r'https://.*:.*@', "URL中包含凭证"),
]

# 跨平台问题正则
PLATFORM_PATTERNS = [
    (r'#include\s+<windows\.h>', "引用了 Windows 特有头文件 (影响跨平台)"),
    (r'#include\s+<unistd\.h>', "引用了 Unix 特有头文件 (影响跨平台)"),
    (r'system\("pause"\)', "Windows 特有系统调用"),
    (r'\\', "硬编码反斜杠路径 (建议使用 std::filesystem 或 /)"),
]

# 高危函数（命令注入风险）
DANGEROUS_FUNCS = [
    (r'\bsystem\s*\(', "system() 调用 (极高命令注入风险)"),
    (r'\bpopen\s*\(', "popen() 调用 (命令注入风险)"),
    (r'\bexecl\s*\(|\bexecv\s*\(', "exec 系列函数 (命令注入风险)"),
    (r'\bstrcpy\s*\(', "strcpy() (缓冲区溢出风险，建议用 strncpy/std::string)"),
    (r'\bsprintf\s*\(', "sprintf() (缓冲区溢出风险，建议用 snprintf)"),
]

# ================= 颜色输出 =================
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_header(msg):
    print(f"\n{Colors.HEADER}{Colors.BOLD}[*] {msg}{Colors.ENDC}")

def print_warn(msg):
    print(f"{Colors.WARNING}[!] {msg}{Colors.ENDC}")

def print_error(msg):
    print(f"{Colors.FAIL}[x] {msg}{Colors.ENDC}")

def print_success(msg):
    print(f"{Colors.OKGREEN}[+] {msg}{Colors.ENDC}")

# ================= 核心功能 =================

def get_files(root_dir):
    file_list = []
    for root, dirs, files in os.walk(root_dir):
        # 过滤忽略目录
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
        for file in files:
            if os.path.splitext(file)[1] in EXTENSIONS:
                file_list.append(os.path.join(root, file))
    return file_list

def run_cppcheck(root_dir):
    """运行 Cppcheck 检测内存泄露、空指针、越界、未使用函数等"""
    print_header("正在运行 Cppcheck (静态分析)...")
    
    # 检查 cppcheck 是否安装
    try:
        subprocess.run(['cppcheck', '--version'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except FileNotFoundError:
        print_error("未找到 'cppcheck' 命令。请先安装: sudo apt install cppcheck 或 brew install cppcheck")
        return

    # --enable=all: 开启所有检查 (style, performance, portability, unusedFunction 等)
    # --inconclusive: 即使不确定也报告（稍微增加误报，但能发现更多隐患）
    # --std=c++17: 假设标准，可以根据需要改
    cmd = [
        'cppcheck',
        '--enable=warning,performance,portability,style', 
        '--inconclusive',
        '--quiet',
        '--template={file}:{line}: [{id}] {message}',
        f'-j {os.cpu_count()}', # 多核并行
        root_dir
    ]
    
    # 注意：unusedFunction 检查需要分析所有文件，不能多线程，且速度较慢，若项目巨大建议去掉
    # 如果要检查未使用函数，添加 '--enable=unusedFunction'
    
    print(f"执行命令: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, stderr=subprocess.PIPE, text=True)
        output = result.stderr
        
        if not output:
            print_success("Cppcheck 未发现明显问题。")
            return

        for line in output.splitlines():
            if "error" in line or "leak" in line.lower():
                print(f"{Colors.FAIL}{line}{Colors.ENDC}") # 严重错误标红
            elif "portability" in line:
                print(f"{Colors.OKCYAN}{line}{Colors.ENDC}") # 移植性问题标青
            else:
                print(f"{Colors.WARNING}{line}{Colors.ENDC}")
    except Exception as e:
        print_error(f"Cppcheck 运行失败: {e}")

def run_flawfinder(root_dir):
    """运行 Flawfinder 检测安全漏洞"""
    print_header("正在运行 Flawfinder (安全审计)...")
    
    try:
        subprocess.run(['flawfinder', '--version'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except FileNotFoundError:
        print_error("未找到 'flawfinder'。请运行: pip install flawfinder")
        return

    # level=1 表示报告所有风险等级
    cmd = ['flawfinder', '--minlevel=1', '--quiet', '--dataonly', root_dir]
    
    try:
        result = subprocess.run(cmd, stdout=subprocess.PIPE, text=True)
        output = result.stdout
        
        if not output:
            print_success("Flawfinder 未发现安全漏洞。")
            return

        for line in output.splitlines():
            # Flawfinder 格式通常为 File:Line:  [Level] (Category) Message
            if "[4]" in line or "[5]" in line:
                print(f"{Colors.FAIL}{line}{Colors.ENDC}") # 高危漏洞
            else:
                print(f"{Colors.WARNING}{line}{Colors.ENDC}")
    except Exception as e:
        print_error(f"Flawfinder 运行失败: {e}")

def scan_file_content(file_path):
    """基于正则扫描文件内容 (补充工具扫不到的)"""
    issues = []
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            lines = content.splitlines()

            for i, line in enumerate(lines):
                line_num = i + 1
                
                # 1. 扫描敏感数据
                for pattern, desc in SENSITIVE_PATTERNS:
                    if re.search(pattern, line):
                        issues.append((line_num, f"[敏感数据] {desc}: {line.strip()[:50]}..."))

                # 2. 扫描跨平台硬伤
                for pattern, desc in PLATFORM_PATTERNS:
                    if re.search(pattern, line):
                        issues.append((line_num, f"[跨平台] {desc}"))

                # 3. 扫描高危函数（简易版，做二次确认）
                for pattern, desc in DANGEROUS_FUNCS:
                    if re.search(pattern, line):
                        issues.append((line_num, f"[高危函数] {desc}"))

    except Exception as e:
        print_error(f"无法读取文件 {file_path}: {e}")
    
    return issues

def run_regex_scan(root_dir):
    print_header("正在运行自定义正则扫描 (敏感数据/平台兼容性)...")
    files = get_files(root_dir)
    
    found_issues = False
    
    for file_path in files:
        issues = scan_file_content(file_path)
        if issues:
            found_issues = True
            print(f"\n文件: {Colors.OKBLUE}{file_path}{Colors.ENDC}")
            for line, msg in issues:
                color = Colors.FAIL if "敏感数据" in msg or "高危函数" in msg else Colors.WARNING
                print(f"  Line {line}: {color}{msg}{Colors.ENDC}")
    
    if not found_issues:
        print_success("自定义扫描未发现问题。")


def cppcheck_impl(args):
    if run(["which", "cppcheck"]).returncode:
        print_error("请先安装 cppcheck: sudo apt install cppcheck")
        sys.exit(1)

    if not os.path.isdir(args.directory):
        print_error(f"目录不存在: {args.directory}")
        sys.exit(1)

    print(f"开始分析目录: {os.path.abspath(args.directory)}")

    # 1. 运行 Cppcheck (逻辑、资源泄露、未初始化、无用函数)
    run_cppcheck(args.directory)

    # 3. 运行自定义正则 (密钥泄露、特定跨平台Header、危险System调用)
    run_regex_scan(args.directory)

    print_header("cppcheck 分析结束。请人工复核以上报告...")
