import os
import sys

# Clear SOCKS proxy from environment to prevent 'Unknown scheme for proxy URL' errors
for proxy_var in ['http_proxy', 'https_proxy', 'all_proxy', 'HTTP_PROXY', 'HTTPS_PROXY', 'ALL_PROXY']:
    if proxy_var in os.environ and os.environ[proxy_var].startswith('socks://'):
        os.environ[proxy_var] = os.environ[proxy_var].replace('socks://', 'socks5://')
        print(f"Replaced scheme for {proxy_var}: {os.environ[proxy_var]}")

try:
    import socks
except ImportError:
    print("Warning: PySocks is not installed. If you still encounter proxy errors, please run: pip install PySocks")

from huggingface_hub import snapshot_download

# 定义模型信息
repo_id = "lerobot/xvla-base"
# 下载到当前脚本所在目录下的同名文件夹中
current_dir = os.path.dirname(os.path.abspath(__file__))
local_dir = os.path.join(current_dir, "xvla_base")

print(f"准备下载模型: {repo_id}")
print(f"目标本地路径: {local_dir}")

try:
    snapshot_download(
        repo_id=repo_id,
        local_dir=local_dir,
    )
    print("\n✅ 下载完成！")
    print(f"你可以直接打包传输这个文件夹: {local_dir}")
except Exception as e:
    print(f"\n❌ 下载过程中出错: {e}")
