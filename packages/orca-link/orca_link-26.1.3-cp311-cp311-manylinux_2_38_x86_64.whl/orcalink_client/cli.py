"""
OrcaLink 服务端命令行包装器

这个模块提供 `orcalink` 命令行工具，用于启动 OrcaLink 服务端。
直接调用 C++ 可执行文件，转发所有参数。
"""
import os
import sys
import subprocess
import signal
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
    """查找 orcalink 可执行文件路径
    
    查找顺序：
    1. 当前文件所在目录的 bin/orcalink（开发模式）
    2. sys.path 中查找 orcalink_client/bin/orcalink（安装模式）
    """
    # 方法1: 当前文件所在目录（开发模式或安装模式）
    package_dir = Path(__file__).parent
    orcalink_bin = package_dir / 'bin' / 'orcalink'
    
    if orcalink_bin.exists():
        return orcalink_bin
    
    # 方法2: 从 sys.path 查找（安装模式，conda 环境）
    for path in sys.path:
        candidate = Path(path) / 'orcalink_client' / 'bin' / 'orcalink'
        if candidate.exists():
            return candidate
    
    # 如果都找不到，返回第一个候选路径（用于错误提示）
    return orcalink_bin


def find_default_config():
    """查找默认配置文件路径"""
    # 方法1: 当前文件所在目录
    package_dir = Path(__file__).parent
    default_config = package_dir / 'bin' / 'orca_config.json'
    
    if default_config.exists():
        return default_config
    
    # 方法2: 从 sys.path 查找
    for path in sys.path:
        candidate = Path(path) / 'orcalink_client' / 'bin' / 'orca_config.json'
        if candidate.exists():
            return candidate
    
    return None


def main():
    """主函数：启动 OrcaLink 服务端"""
    # 查找可执行文件
    orcalink_bin = find_executable()
    
    if not orcalink_bin.exists():
        print(Colors.colorize(f"❌ 错误: 找不到可执行文件 {orcalink_bin}", Colors.RED), file=sys.stderr)
        print(Colors.colorize("请确保包已正确安装。", Colors.RED), file=sys.stderr)
        print(Colors.colorize("如果是开发模式，请先运行:", Colors.YELLOW), file=sys.stderr)
        print(Colors.colorize("  bash Scripts/build_package.sh", Colors.YELLOW), file=sys.stderr)
        sys.exit(1)
    
    # 查找默认配置文件
    default_config = find_default_config()
    
    # 构建命令：直接转发所有参数给可执行文件
    cmd = [str(orcalink_bin)] + sys.argv[1:]
    
    # 如果没有指定 --config 且默认配置文件存在，添加默认配置
    if '--config' not in sys.argv and default_config:
        cmd.extend(['--config', str(default_config)])
    
    # 显示启动信息（简单版本）
    if Colors.enabled():
        print(Colors.colorize("═══════════════════════════════════════════════════════════", Colors.GREEN))
        print(Colors.colorize("🚀 OrcaLink gRPC 转发服务器", Colors.BLUE))
        print(Colors.colorize("═══════════════════════════════════════════════════════════", Colors.GREEN))
        print()
        print(Colors.colorize("📋 启动配置:", Colors.BLUE))
        print(f"  {Colors.colorize('可执行文件', Colors.BLUE)}: {orcalink_bin}")
        if default_config:
            print(f"  {Colors.colorize('配置文件', Colors.BLUE)}: {default_config}")
        print()
        print(Colors.colorize("────────────────────────────────────────────────────────────", Colors.GREEN))
        print()
        print(Colors.colorize("▶ 启动服务器...", Colors.BLUE))
        print()
    
    # 设置信号处理（优雅处理 Ctrl+C）
    def signal_handler(sig, frame):
        print()
        if Colors.enabled():
            print(Colors.colorize("⏹ 收到停止信号，关闭服务器...", Colors.YELLOW))
        sys.exit(130)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # 执行命令，直接转发 stdout/stderr
        sys.exit(subprocess.call(cmd))
    except KeyboardInterrupt:
        print()
        if Colors.enabled():
            print(Colors.colorize("⏹ 收到停止信号，关闭服务器...", Colors.YELLOW))
        sys.exit(130)
    except FileNotFoundError:
        print(Colors.colorize(f"❌ 错误: 无法执行 {orcalink_bin}", Colors.RED), file=sys.stderr)
        print(Colors.colorize("请确保可执行文件存在且具有执行权限。", Colors.RED), file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(Colors.colorize(f"❌ 错误: 启动服务器时发生异常: {e}", Colors.RED), file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
