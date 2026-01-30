"""
OrcaSPH 命令行工具

这个模块提供 `orcasph` 命令行工具，用于启动 SPHSimulator。
支持 CPU 核心绑定、OpenMP 线程数设置等功能。
"""
import os
import sys
import subprocess
import signal
import argparse
from pathlib import Path


# ANSI 颜色代码
class Colors:
    """ANSI 颜色代码（兼容 Windows）"""
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    NC = '\033[0m'  # No Color
    
    @staticmethod
    def enabled():
        """检查终端是否支持颜色输出"""
        return sys.stdout.isatty() and os.getenv('TERM') != 'dumb'
    
    @staticmethod
    def colorize(text, color):
        """为文本添加颜色（如果终端支持）"""
        if Colors.enabled():
            return f"{color}{text}{Colors.NC}"
        return text


def find_executable():
    """查找 SPHSimulator 可执行文件路径
    
    查找顺序：
    1. 当前文件所在目录的 bin/SPHSimulator（开发模式）
    2. sys.path 中查找 orcasph_client/bin/SPHSimulator（安装模式）
    """
    # 方法1: 当前文件所在目录（开发模式或安装模式）
    package_dir = Path(__file__).parent
    simulator_bin = package_dir / 'bin' / 'SPHSimulator'
    
    if simulator_bin.exists():
        return simulator_bin
    
    # 方法2: 从 sys.path 查找（安装模式，conda 环境）
    for path in sys.path:
        candidate = Path(path) / 'orcasph_client' / 'bin' / 'SPHSimulator'
        if candidate.exists():
            return candidate
    
    # 如果都找不到，返回第一个候选路径（用于错误提示）
    return simulator_bin


def find_lib_directory():
    """查找库文件目录路径"""
    package_dir = Path(__file__).parent
    lib_dir = package_dir / 'lib'
    
    if lib_dir.exists():
        return lib_dir
    
    # 从 sys.path 查找
    for path in sys.path:
        candidate = Path(path) / 'orcasph_client' / 'lib'
        if candidate.exists():
            return candidate
    
    return lib_dir


def find_default_config():
    """查找默认配置文件路径"""
    # 方法1: 当前文件所在目录
    package_dir = Path(__file__).parent
    default_config = package_dir / 'bin' / 'config.json'
    
    if default_config.exists():
        return default_config
    
    # 方法2: 从 sys.path 查找
    for path in sys.path:
        candidate = Path(path) / 'orcasph_client' / 'bin' / 'config.json'
        if candidate.exists():
            return candidate
    
    return None


def print_help():
    """打印帮助信息"""
    print(Colors.colorize("OrcaSPH - SPH Fluid Simulator", Colors.GREEN))
    print("")
    print(Colors.colorize("用法:", Colors.YELLOW))
    print("  orcasph --scene FILE [选项]")
    print("")
    print(Colors.colorize("选项:", Colors.YELLOW))
    print("  --scene FILE       场景文件路径 (必需)")
    print("  --cpu RANGE        指定 CPU 核心范围")
    print("                     格式: 0-15 (范围) 或 0,2,4,6 (列表)")
    print("  --threads N        指定 OpenMP 线程数")
    print("  --config FILE      gRPC 配置文件路径")
    print("                     默认: ./bin/config.json")
    print("  --gui              启用 GUI 模式运行")
    print("  --help             显示此帮助信息")
    print("")
    print(Colors.colorize("示例:", Colors.YELLOW))
    print("  # 使用核心 0-15 运行")
    print("  orcasph --scene ../data/Scenes/DamBreak.json --cpu 0-15")
    print("")
    print("  # 使用核心 0-15，限制 16 个线程")
    print("  orcasph --scene ../data/Scenes/DamBreak.json --cpu 0-15 --threads 16")
    print("")
    print("  # 使用偶数核心 (避免超线程)")
    print("  orcasph --scene ../data/Scenes/DamBreak.json --cpu 0,2,4,6,8,10,12,14")
    print("")
    print("  # 与 Orca 分离运行 (SPHSimulator 用核心 0-15, Orca 用 16-23)")
    print("  orcasph --scene scene.json --cpu 0-15 &")
    print("  taskset -c 16-23 ./OrcaStudio &")
    print("")
    print(Colors.colorize("系统信息:", Colors.YELLOW))
    try:
        import multiprocessing
        cpu_count = multiprocessing.cpu_count()
        print(f"  CPU 核心数: {cpu_count}")
        print(f"  可用核心: 0-{cpu_count-1}")
    except:
        print("  CPU 核心数: 未知")


def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description='OrcaSPH - SPH Fluid Simulator with OrcaLink Integration',
        add_help=False
    )
    
    parser.add_argument('--scene', type=str, help='场景文件路径 (必需)')
    parser.add_argument('--cpu', type=str, help='指定 CPU 核心范围 (例如: 0-15, 0,2,4,6)')
    parser.add_argument('--threads', type=int, help='指定 OpenMP 线程数')
    parser.add_argument('--config', type=str, help='gRPC 配置文件路径')
    parser.add_argument('--gui', action='store_true', help='启用 GUI 模式运行')
    parser.add_argument('--help', action='store_true', help='显示帮助信息')
    
    # 解析已知参数，保留未知参数
    args, unknown_args = parser.parse_known_args()
    
    return args, unknown_args


def main():
    """主函数：启动 SPHSimulator"""
    # 解析参数
    args, extra_args = parse_arguments()
    
    # 显示帮助
    if args.help or '--help' in sys.argv:
        print_help()
        sys.exit(0)
    
    # 检查场景文件
    if not args.scene:
        print(Colors.colorize("错误: 未指定场景文件，请使用 --scene 参数", Colors.RED), file=sys.stderr)
        print("", file=sys.stderr)
        print_help()
        sys.exit(1)
    
    scene_file = Path(args.scene)
    if not scene_file.exists():
        print(Colors.colorize(f"错误: 场景文件不存在: {scene_file}", Colors.RED), file=sys.stderr)
        sys.exit(1)
    
    # 转换为绝对路径
    scene_file_abs = scene_file.resolve()
    
    # 查找可执行文件
    simulator_bin = find_executable()
    
    if not simulator_bin.exists():
        print(Colors.colorize(f"错误: 找不到可执行文件 {simulator_bin}", Colors.RED), file=sys.stderr)
        print(Colors.colorize("请确保包已正确安装。", Colors.RED), file=sys.stderr)
        print(Colors.colorize("如果是开发模式，请先运行:", Colors.YELLOW), file=sys.stderr)
        print(Colors.colorize("  bash Scripts/build_package.sh", Colors.YELLOW), file=sys.stderr)
        sys.exit(1)
    
    # 查找库目录并设置 LD_LIBRARY_PATH
    lib_dir = find_lib_directory()
    if lib_dir.exists():
        lib_path = str(lib_dir.resolve())
        current_ld_path = os.environ.get('LD_LIBRARY_PATH', '')
        os.environ['LD_LIBRARY_PATH'] = f"{lib_path}:{current_ld_path}" if current_ld_path else lib_path
        if Colors.enabled():
            print(Colors.colorize(f"库路径: {lib_path}", Colors.BLUE))
    
    # 查找默认配置文件
    default_config = find_default_config()
    config_file = None
    
    if args.config:
        config_file = Path(args.config)
        if not config_file.exists():
            print(Colors.colorize(f"警告: 配置文件不存在: {config_file}", Colors.YELLOW), file=sys.stderr)
            config_file = None
        else:
            config_file = config_file.resolve()
    elif default_config:
        config_file = default_config.resolve()
    
    # 构建命令
    cmd = [str(simulator_bin.resolve())]
    
    # 添加配置文件
    if config_file:
        cmd.extend(['--config', str(config_file)])
        if Colors.enabled():
            print(Colors.colorize(f"配置文件: {config_file}", Colors.BLUE))
    elif not args.config:
        # 用户没有指定 --config，且默认配置不存在，给出警告
        if Colors.enabled():
            print(Colors.colorize("警告: 配置文件不存在，使用默认配置", Colors.YELLOW))
    
    # 添加场景文件
    cmd.append(str(scene_file_abs))
    if Colors.enabled():
        print(Colors.colorize(f"场景文件: {scene_file_abs}", Colors.BLUE))
    
    # 添加 GUI 模式参数
    if args.gui:
        cmd.append('--gui')
        if Colors.enabled():
            print(Colors.colorize("GUI 模式: 启用", Colors.BLUE))
    
    # 添加额外参数
    cmd.extend(extra_args)
    
    # 设置 OpenMP 线程数
    if args.threads:
        os.environ['OMP_NUM_THREADS'] = str(args.threads)
        if Colors.enabled():
            print(Colors.colorize(f"OpenMP 线程数: {args.threads} (通过环境变量)", Colors.BLUE))
    
    # 设置 CPU 亲和性
    if args.cpu:
        # 设置 GOMP_CPU_AFFINITY 以确保 OpenMP 也遵守
        os.environ['GOMP_CPU_AFFINITY'] = args.cpu
        
        # 使用 taskset 绑定 CPU 核心
        cmd = ['taskset', '-c', args.cpu] + cmd
        
        if Colors.enabled():
            print(Colors.colorize(f"CPU 核心绑定: {args.cpu}", Colors.BLUE))
    
    # 显示启动信息
    if Colors.enabled():
        print("")
        print(Colors.colorize("═══════════════════════════════════════════════════════════", Colors.GREEN))
        print(Colors.colorize("🚀 OrcaSPH - SPH Fluid Simulator", Colors.BLUE))
        print(Colors.colorize("═══════════════════════════════════════════════════════════", Colors.GREEN))
        print("")
        print(Colors.colorize("执行命令:", Colors.GREEN))
        print(f"  {' '.join(cmd)}")
        print("")
    
    # 设置信号处理（优雅处理 Ctrl+C）
    def signal_handler(sig, frame):
        print()
        if Colors.enabled():
            print(Colors.colorize("⏹ 收到停止信号，关闭模拟器...", Colors.YELLOW))
        sys.exit(130)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # 执行命令，直接转发 stdout/stderr
        sys.exit(subprocess.call(cmd))
    except KeyboardInterrupt:
        print()
        if Colors.enabled():
            print(Colors.colorize("⏹ 收到停止信号，关闭模拟器...", Colors.YELLOW))
        sys.exit(130)
    except FileNotFoundError:
        print(Colors.colorize(f"错误: 无法执行 {simulator_bin}", Colors.RED), file=sys.stderr)
        print(Colors.colorize("请确保可执行文件存在且具有执行权限。", Colors.RED), file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(Colors.colorize(f"错误: 启动模拟器时发生异常: {e}", Colors.RED), file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()

