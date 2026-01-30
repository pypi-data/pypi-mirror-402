import asyncio
import datetime
import os
import subprocess
import sys
import re
from pathlib import Path
from typing import Optional

try:
    from mcp.server.fastmcp import FastMCP
except ModuleNotFoundError:
    # 尝试使用虚拟环境中的 python (如果存在)
    venv_python = (Path(__file__).resolve().parent / '.venv' / 'bin' / 'python')
    if venv_python.exists() and Path(sys.executable).resolve() != venv_python.resolve():
        os.execv(str(venv_python), [str(venv_python), str(Path(__file__).resolve())])
    raise

# 创建 MCP 服务实例
server = FastMCP(
    name="jojo-remote-build-server",
)

class PathManager:
    """处理路径兼容性和修复的类"""
    
    @staticmethod
    def validate_and_fix_path(path: str) -> str:
        """
        验证并尝试修复项目路径。
        
        Args:
            path: 输入的路径
            
        Returns:
            修正后的有效路径
            
        Raises:
            ValueError: 当无法找到有效路径时抛出
        """
        path = os.path.abspath(os.path.expanduser(path))
        
        # 1. 检查当前路径是否有效
        if PathManager._is_valid_project_root(path):
            return path
            
        # 2. 向上查找 (检查父目录)
        current = path
        while current != "/":
            parent = os.path.dirname(current)
            if parent == current:
                break
            if PathManager._is_valid_project_root(parent):
                return parent
            current = parent
            
        # 3. 向下查找 (检查子目录)
        # 限制深度为 3 层，避免遍历太多
        for root, dirs, _ in os.walk(path):
            # 计算当前深度
            depth = root[len(path):].count(os.sep)
            if depth > 3:
                del dirs[:]  # 停止遍历子目录
                continue
                
            if 'Aweme' in dirs:
                candidate = os.path.join(root, 'Aweme')
                if PathManager._is_valid_project_root(candidate):
                    return candidate
        
        # 4. 尝试常见的路径补全 (针对用户输入漏了 Aweme/Aweme 的情况)
        # 比如输入了 .../Aweme，但实际项目在 .../Aweme/Aweme
        candidate = os.path.join(path, 'Aweme')
        if PathManager._is_valid_project_root(candidate):
            return candidate
            
        raise ValueError(f"无法在路径 '{path}' 或其附近找到有效的 Aweme 项目根目录 (需包含 'jojo' 工具或 'Aweme.xcodeproj')")

    @staticmethod
    def _is_valid_project_root(path: str) -> bool:
        """检查指定路径是否为有效的 Aweme 项目根目录"""
        if not os.path.exists(path) or not os.path.isdir(path):
            return False
        
        # 关键文件检查：
        # 1. jojo 构建脚本
        has_jojo = os.path.exists(os.path.join(path, 'jojo'))
        # 2. xcodeproj
        has_xcodeproj = os.path.exists(os.path.join(path, 'Aweme', 'Aweme.xcodeproj')) or \
                        os.path.exists(os.path.join(path, 'Aweme.xcodeproj'))
        # 3. Rockfile (Aweme 仓库特征)
        has_rockfile = os.path.exists(os.path.join(path, 'Rockfile')) or \
                       os.path.exists(os.path.join(path, 'Aweme', 'Rockfile'))
        
        return has_jojo or has_xcodeproj or has_rockfile

class JojoFinder:
    """查找 jojo 可执行文件的类"""
    
    @staticmethod
    def find_jojo(project_root: str) -> str:
        """
        在项目根目录查找 jojo。
        
        优先顺序:
        1. ./jojo (根目录直接存在)
        2. .iac/tools/jojo/jojo (iac 目录下)
        3. mbox jojo (回退到 mbox 命令)
        
        Returns:
            可执行的命令前缀，例如 "./jojo" 或 ".iac/tools/jojo/jojo" 或 "mbox jojo"
        """
        # 1. 检查根目录 ./jojo
        jojo_root = os.path.join(project_root, "jojo")
        if os.path.exists(jojo_root) and os.access(jojo_root, os.X_OK):
            return "./jojo"
            
        # 2. 检查 .iac/tools/jojo/jojo
        jojo_iac = os.path.join(project_root, ".iac", "tools", "jojo", "jojo")
        if os.path.exists(jojo_iac) and os.access(jojo_iac, os.X_OK):
            return ".iac/tools/jojo/jojo"
            
        # 3. 回退到 mbox
        return "mbox jojo"

class LogProcessor:
    """处理日志优化和错误提取的类"""
    
    @staticmethod
    def process_log(content: str) -> str:
        """
        处理构建日志，提取错误信息。
        
        Args:
            content: 原始日志内容
            
        Returns:
            格式化后的错误摘要
        """
        lines = content.split('\n')
        extracted_errors = []
        
        # 状态机变量
        collecting_block = False
        current_block = []
        block_type = "" # "undefined_symbols" or "other"
        
        # 常见错误模式
        error_pattern = re.compile(r'error:', re.IGNORECASE)
        undefined_symbol_start = re.compile(r'Undefined symbols for architecture', re.IGNORECASE)
        
        for line in lines:
            line_stripped = line.strip()
            
            # 1. 处理 Undefined Symbols 块
            if undefined_symbol_start.search(line):
                collecting_block = True
                block_type = "undefined_symbols"
                current_block = [line]
                continue
            
            if collecting_block:
                if block_type == "undefined_symbols":
                    # 如果遇到空行或新的 ld: 警告，可能块结束了，但通常 undefined symbols 会缩进
                    # 这里简化处理：如果行不缩进且不是以 "  " 开头，可能结束了
                    if not line.startswith(' ') and not line.startswith('\t') and line_stripped:
                         # 块结束
                        LogProcessor._add_error_block(extracted_errors, current_block, "Linker Error")
                        collecting_block = False
                        current_block = []
                        # 继续处理当前行，因为它可能包含其他错误
                    else:
                        current_block.append(line)
                        continue

        # 1.5 处理 Remote Install 错误
            if "FailedToRemoteInstall" in line:
                extracted_errors.append(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [Remote Install Error] 远程安装步骤失败，但这可能不影响构建产物的使用。")

            # 2. 处理单行 Error
            if error_pattern.search(line):
                # 尝试提取位置信息
                # 格式如: /path/to/file:line:col: error: message
                match = re.search(r'([^:\s]+):(\d+):(\d+):\s*error:\s*(.*)', line)
                if match:
                    file_path, line_no, col_no, msg = match.groups()
                    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") # 模拟时间戳
                    extracted_errors.append(f"[{timestamp}] [Compile Error] {file_path}:{line_no} - {msg}")
                else:
                    # 普通错误
                    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    extracted_errors.append(f"[{timestamp}] [Error] {line_stripped}")

        # 处理最后可能遗留的块
        if collecting_block and current_block:
             LogProcessor._add_error_block(extracted_errors, current_block, "Linker Error")

        # 去重
        unique_errors = list(dict.fromkeys(extracted_errors))
        
        # 限制数量，防止输出爆炸
        if len(unique_errors) > 50:
            unique_errors = unique_errors[:50]
            unique_errors.append("... (更多错误已省略)")
            
        if not unique_errors:
            # 如果没有提取到特定错误，但返回码非0，尝试返回最后几行
            return "未检测到明确的错误模式。以下是日志的最后部分：\n" + "\n".join(lines[-20:])
            
        return "\n".join(unique_errors)

    @staticmethod
    def _add_error_block(error_list, block, error_type):
        """辅助方法：添加错误块"""
        if not block:
            return
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # 提取块中的关键信息，比如符号名
        summary = "\n".join(block[:10]) # 只保留前10行
        if len(block) > 10:
            summary += "\n..."
        error_list.append(f"[{timestamp}] [{error_type}]\n{summary}")


@server.tool()
async def get_mbox_project_info(project_root: str) -> str:
    """
    通过 `mbox status` 获取当前 Aweme 项目的根目录路径和 Container 信息。
    
    Args:
        project_root: 当前工程所在的根目录路径，mbox status 将在此目录下执行。
    
    返回 JSON 格式的字符串，包含:
    - project_path: 项目的绝对路径 (Root + Container Path)
    - container_name: Container 名称 (如 "Aweme", "AwemeDS" 等)
    - recommended_scheme: 推荐的构建 scheme (ContainerName + InhouseDebug)
    
    AI 应该先调用此工具获取信息，然后将 project_path 和 recommended_scheme 填入 `run_aweme_remote_build` 工具的参数中。
    """
    try:
        # 验证路径是否存在
        if not os.path.exists(project_root) or not os.path.isdir(project_root):
            return f"❌ 提供的路径不存在或不是目录: {project_root}"

        process = await asyncio.create_subprocess_shell(
            "mbox status",
            cwd=project_root,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
             return f"❌ mbox status 执行失败: {stderr.decode('utf-8')}"

        output = stdout.decode('utf-8')
        root_path = None
        container_name = None
        container_rel_path = None
        
        lines = output.split('\n')
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("[Root]:"):
                root_path = stripped.split(":", 1)[1].strip()
            
            if "=>" in line:
                parts = line.split("=>", 1)[1].strip().split()
                if len(parts) >= 1:
                    container_name = parts[0]
                if len(parts) >= 3:
                    container_rel_path = parts[-1]
        
        if root_path and container_name and container_rel_path:
            full_path = os.path.join(root_path, container_rel_path)
            scheme = f"{container_name}InhouseDebug"
            
            import json
            result = {
                "project_path": full_path,
                "container_name": container_name,
                "recommended_scheme": scheme
            }
            return json.dumps(result, ensure_ascii=False, indent=2)
        
        return f"⚠️ 无法完全解析 mbox 信息。\nRoot: {root_path}\nContainer: {container_name}\nPath: {container_rel_path}"
        
    except Exception as e:
        return f"❌ 获取 mbox 信息时发生异常: {e}"


@server.tool()
async def run_aweme_remote_build(
    project_path: str,
    scheme: str,
    clean: bool = False
) -> str:
    """
    执行 Aweme 项目的远程构建命令 (arm64, Debug)。
    
    Args:
        project_path: 项目根目录路径 (必填，请先通过 get_mbox_project_info 获取)
        scheme: 构建 Scheme (必填，请先通过 get_mbox_project_info 获取推荐值)
        clean: 是否在构建前清理缓存，默认为 False
    
    此工具将执行以下命令：
    [可选] mbox jojo clean
    cd {project_path} && \
    JOJO_ENABLE_JPM=true ./jojo build \
    --archs arm64 \
    --target Aweme \
    --scheme {scheme} \
    --use-cache \
    --xcode_version 26.0.0 \
    --keep_going \
    --mode Debug \
    --other_linker_flags '-awe_reserve_debug_notes bazel-out/ -awe_reserve_debug_notes ./' \
    --plugin ../.iac/tools/jojo/jojo_plugin.py \
    --project_yaml Aweme/Aweme.xcodeproj
    """
    
    # 1. 路径验证与修正
    try:
        valid_path = PathManager.validate_and_fix_path(project_path)
        if valid_path != project_path:
            print(f"路径已修正: {project_path} -> {valid_path}")
        cwd = valid_path
    except ValueError as e:
        return f"❌ 路径错误: {str(e)}"

    # 查找 jojo
    jojo_cmd = JojoFinder.find_jojo(cwd)

    # 如果需要清理
    if clean:
        clean_cmd = f"{jojo_cmd} clean"
        print(f"正在清理: {clean_cmd}")
        try:
             process = await asyncio.create_subprocess_shell(
                clean_cmd,
                cwd=cwd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
             await process.communicate()
        except Exception as e:
            print(f"清理失败: {e}")

    # 注意：命令中的相对路径 ../.iac/... 是基于 cwd 的
    command = (
        f"JOJO_ENABLE_JPM=true {jojo_cmd} build "
        "--archs arm64 "
        "--target Aweme "
        f"--scheme {scheme} "
        "--use-cache "
        "--xcode_version 26.0.0 "
        "--keep_going "
        "--mode Debug "
        "--other_linker_flags '-awe_reserve_debug_notes bazel-out/ -awe_reserve_debug_notes ./' "
        "--plugin ../.iac/tools/jojo/jojo_plugin.py "
        "--project_yaml Aweme/Aweme.xcodeproj"
    )

    try:
        # 使用 shell=True 来处理环境变量和命令参数
        process = await asyncio.create_subprocess_shell(
            command,
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # 等待命令完成
        stdout, stderr = await process.communicate()
        
        output = stdout.decode("utf-8", errors='replace') + "\n" + stderr.decode("utf-8", errors='replace')
        
        # 保存原始日志
        log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
        os.makedirs(log_dir, exist_ok=True)
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file_path = os.path.join(log_dir, f"aweme_remote_build_{timestamp}.log")
        
        with open(log_file_path, "w", encoding="utf-8") as f:
            f.write(output)

        # 构造返回结果
        result_msg = []
        if process.returncode == 0:
            result_msg.append("✅ 构建成功！")
            result_msg.append(f"日志路径: {log_file_path}")
            # 成功时只返回最后几行
            result_msg.append("\n=== 输出摘要 ===\n")
            result_msg.append("\n".join(output.split('\n')[-20:]))
        else:
            result_msg.append(f"❌ 构建失败 (Exit Code: {process.returncode})")
            result_msg.append(f"日志路径: {log_file_path}")
            
            # 尝试从 .jojo/build_raw.log 读取（如果有）
            build_raw_path = os.path.join(cwd, ".jojo", "build_raw.log")
            if os.path.exists(build_raw_path):
                 result_msg.append(f"原始日志: {build_raw_path}")
                 try:
                     with open(build_raw_path, "r", encoding="utf-8", errors="replace") as f:
                         build_raw_content = f.read()
                         # 使用 LogProcessor 处理 build_raw.log
                         error_summary = LogProcessor.process_log(build_raw_content)
                         result_msg.append("\n=== 错误智能分析 ===\n")
                         result_msg.append(error_summary)
                 except Exception as e:
                     result_msg.append(f"\n[无法读取 build_raw.log: {e}]")
            else:
                # 如果没有 build_raw.log，尝试从 stdout/stderr 分析
                error_summary = LogProcessor.process_log(output)
                result_msg.append("\n=== 错误智能分析 ===\n")
                result_msg.append(error_summary)
        
        return "\n".join(result_msg)
            
    except Exception as e:
        return f"执行构建命令时发生异常: {e}"

# @server.tool()
# async def init_remote_build_environment(
#     project_path: str = "/Volumes/SN770-2TB/im_alog_size_optimize/Aweme/Aweme",
#     device_udid: str = "00008140-000564A83C2B001C"
# ) -> str:
#     """
#     初始化 Remote Build 环境。
    
#     依次执行：
#     1. mbox jojo install --remote
#     2. mbox jojo recodesign --save_info --codesign_in_remote [--device-udid <UDID>]
#     3. mbox jojo remote_mode --build-in-shell

#     Args:
#         project_path: 项目根目录路径，默认为 "/Volumes/SN770-2TB/im_alog_size_optimize/Aweme/Aweme"
#         device_udid: 指定设备的 UDID，用于 codesign。如果不提供，默认尝试选择第一个设备。
#     """
#     # 1. 路径验证
#     try:
#         valid_path = PathManager.validate_and_fix_path(project_path)
#         cwd = valid_path
#     except ValueError as e:
#         return f"❌ 路径错误: {str(e)}"

#     # 构造 recodesign 命令
#     recodesign_cmd = "mbox jojo recodesign --save_info --codesign_in_remote"
#     if device_udid:
#         recodesign_cmd += f" --device-udid {device_udid}"
#     else:
#         # 如果没有提供 UDID，尝试使用 echo "1" 自动选择第一个（兼容旧逻辑，但不推荐）
#         # 或者我们可以更智能一点，先不加 echo "1"，如果失败提示用户提供 UDID
#         # 这里为了保持向后兼容性，且避免卡死，我们还是保留 echo "1" 作为兜底，
#         # 但强烈建议用户提供 UDID
#         recodesign_cmd = f'echo "1" | {recodesign_cmd}'

#     commands = [
#         ("Remote Install", "mbox jojo install --remote"),
#         ("Codesign Setup", recodesign_cmd),
#         ("Enable Build-in-Shell", "mbox jojo remote_mode --build-in-shell")
#     ]

#     result_log = []
#     result_log.append(f"开始在 {cwd} 初始化 Remote Build 环境...\n")
    
#     # 设置环境变量
#     env = os.environ.copy()
#     # 强制 PATH 包含常见路径，以防 mbox 找不到
#     env["PATH"] = f"/opt/homebrew/bin:/usr/local/bin:{env.get('PATH', '')}"

#     # 1.5 Git 检查与推送
#     try:
#         # 获取当前分支名
#         proc = await asyncio.create_subprocess_shell(
#             "git rev-parse --abbrev-ref HEAD",
#             cwd=cwd,
#             stdout=subprocess.PIPE,
#             stderr=subprocess.PIPE,
#             env=env
#         )
#         stdout, _ = await proc.communicate()
#         branch_name = stdout.decode('utf-8').strip()

#         if branch_name:
#             result_log.append(f"👉 检查 Git 分支状态 (当前分支: {branch_name}) ...")
#             # 检查远端是否存在该分支
#             proc = await asyncio.create_subprocess_shell(
#                 f"git ls-remote --exit-code --heads origin {branch_name}",
#                 cwd=cwd,
#                 stdout=subprocess.PIPE,
#                 stderr=subprocess.PIPE,
#                 env=env
#             )
#             await proc.wait()
            
#             if proc.returncode != 0:
#                 result_log.append(f"   远端不存在分支 {branch_name}，正在执行 push ...")
#                 push_proc = await asyncio.create_subprocess_shell(
#                     f"git push --set-upstream origin {branch_name}",
#                     cwd=cwd,
#                     stdout=subprocess.PIPE,
#                     stderr=subprocess.PIPE,
#                     env=env
#                 )
#                 p_out, p_err = await push_proc.communicate()
                
#                 if push_proc.returncode == 0:
#                     result_log.append(f"✅ Git Push 成功")
#                 else:
#                     result_log.append(f"⚠️ Git Push 失败 (Exit Code: {push_proc.returncode})")
#                     result_log.append(f"   错误输出: {p_err.decode('utf-8', errors='replace').strip()}")
#                     # 即使 push 失败，我们通常也继续尝试后续步骤，或者这里可以选择 return 终止
#             else:
#                 result_log.append(f"✅ 远端已存在分支 {branch_name}，跳过 Push")
#     except Exception as e:
#         result_log.append(f"⚠️ Git 检查步骤发生异常: {e} (将继续执行后续步骤)")

#     for step_name, cmd in commands:
#         result_log.append(f"👉 正在执行: {step_name} ...")
        
#         try:
#             # 简单的重试逻辑 (仅针对 Remote Install)
#             max_retries = 3 if step_name == "Remote Install" else 1
            
#             for attempt in range(max_retries):
#                 # 使用 shell=True 且传入 env
#                 process = await asyncio.create_subprocess_shell(
#                     cmd,
#                     cwd=cwd,
#                     stdout=subprocess.PIPE,
#                     stderr=subprocess.PIPE,
#                     env=env
#                 )
#                 stdout, stderr = await process.communicate()
#                 output = stdout.decode("utf-8", errors='replace') + stderr.decode("utf-8", errors='replace')
                
#                 if process.returncode == 0:
#                     result_log.append(f"✅ {step_name} 成功")
#                     break
#                 else:
#                     # 特殊处理 Remote Install 的非致命错误
#                     # 比如 176, 96 可能只是部分组件下载失败，不影响整体流程
#                     if step_name == "Remote Install" and process.returncode in [96, 176]:
#                          result_log.append(f"⚠️ {step_name} 完成，但存在警告 (Exit Code: {process.returncode})。通常这不影响后续构建。")
#                          break
                    
#                     if attempt < max_retries - 1:
#                         result_log.append(f"⚠️ {step_name} 失败 (Exit Code: {process.returncode})，正在重试 ({attempt + 1}/{max_retries})...")
#                         await asyncio.sleep(2) # 等待几秒后重试
#                     else:
#                         result_log.append(f"❌ {step_name} 失败 (Exit Code: {process.returncode})")
#                         result_log.append(f"错误输出:\n{output[-2000:]}") 
#                         return "\n".join(result_log)
#         except Exception as e:
#             return f"❌ 执行 {step_name} 时发生异常: {e}"

#     result_log.append("\n🎉 所有初始化步骤完成！Remote Build 环境已就绪。")
#     return "\n".join(result_log)

if __name__ == "__main__":
    server.run(transport='stdio')
