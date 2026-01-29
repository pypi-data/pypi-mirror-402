"""知识库下载模块 - 从 GitHub Releases 或其他源下载预构建的向量数据库"""
import os
import shutil
import zipfile
import tarfile
from pathlib import Path

try:
    import requests
    from tqdm import tqdm
except ImportError:
    # 如果导入失败，提供友好的错误提示
    print("⚠️  需要安装 requests 和 tqdm 才能下载知识库")
    print("   运行: pip install requests tqdm")
    requests = None
    tqdm = None

# GitHub Releases 配置
GITHUB_REPO = "likelihood333/ISE3309-AI-Intelligent-Teaching-Assistant"
DB_RELEASE_TAG = "v0.1.0"  # 可以跟随版本号更新
DB_FILENAME = "knowledge_base.zip"  # 或 knowledge_base.tar.gz

def get_latest_release_info():
    """获取最新 release 信息"""
    url = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"⚠️  无法获取最新 release 信息: {e}")
        return None

def download_file(url: str, dest_path: Path, description: str = "下载中"):
    """下载文件并显示进度"""
    if requests is None or tqdm is None:
        raise ImportError("需要安装 requests 和 tqdm")
    
    try:
        response = requests.get(url, stream=True, timeout=30)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        block_size = 8192
        
        with open(dest_path, 'wb') as f:
            pbar = tqdm(
                desc=description,
                total=total_size,
                unit='B',
                unit_scale=True,
                unit_divisor=1024,
            )
            for data in response.iter_content(block_size):
                f.write(data)
                pbar.update(len(data))
            pbar.close()
        
        return True
    except Exception as e:
        print(f"❌ 下载失败: {e}")
        return False

def extract_archive(archive_path: Path, extract_to: Path):
    """解压归档文件"""
    try:
        extract_to.mkdir(parents=True, exist_ok=True)
        
        if archive_path.suffix == '.zip':
            with zipfile.ZipFile(archive_path, 'r') as zip_ref:
                zip_ref.extractall(extract_to)
        elif archive_path.suffix in ['.tar', '.gz'] or archive_path.suffixes == ['.tar', '.gz']:
            with tarfile.open(archive_path, 'r:gz') as tar_ref:
                tar_ref.extractall(extract_to)
        else:
            print(f"❌ 不支持的文件格式: {archive_path.suffix}")
            return False
        
        return True
    except Exception as e:
        print(f"❌ 解压失败: {e}")
        return False

def download_knowledge_base(target_dir: Path = None, force_download: bool = False) -> bool:
    """
    下载预构建的知识库到用户目录
    
    Args:
        target_dir: 目标目录，默认为 ~/.ise_agent/db
        force_download: 是否强制重新下载
    
    Returns:
        bool: 下载是否成功
    """
    if target_dir is None:
        target_dir = Path.home() / ".ise_agent" / "db"
    
    # 检查数据库是否已存在
    if not force_download and target_dir.exists() and list(target_dir.iterdir()):
        print(f"✓ 知识库已存在于: {target_dir}")
        return True
    
    print(f"\n📥 开始下载知识库...")
    print(f"📁 保存位置: {target_dir}")
    
    # 创建临时目录
    temp_dir = Path.home() / ".ise_agent" / "temp"
    temp_dir.mkdir(parents=True, exist_ok=True)
    archive_path = temp_dir / DB_FILENAME
    
    try:
        # 获取 release 信息
        release_info = get_latest_release_info()
        if not release_info:
            # 如果无法获取最新 release，尝试使用固定 tag
            download_url = f"https://github.com/{GITHUB_REPO}/releases/download/{DB_RELEASE_TAG}/{DB_FILENAME}"
        else:
            # 查找知识库文件
            download_url = None
            for asset in release_info.get('assets', []):
                if asset['name'] == DB_FILENAME or 'knowledge' in asset['name'].lower():
                    download_url = asset['browser_download_url']
                    break
            
            if not download_url:
                # 如果 release 中没有，尝试使用固定 URL
                download_url = f"https://github.com/{GITHUB_REPO}/releases/download/{release_info['tag_name']}/{DB_FILENAME}"
        
        if not download_url:
            print(f"❌ 无法找到知识库下载链接")
            print(f"💡 提示：请手动运行 'ise-agent-build' 构建知识库")
            return False
        
        # 下载文件
        print(f"🔗 下载地址: {download_url}")
        if not download_file(download_url, archive_path, "下载知识库"):
            return False
        
        # 解压到目标目录
        print(f"📦 正在解压...")
        if not extract_archive(archive_path, target_dir):
            return False
        
        # 清理临时文件
        archive_path.unlink()
        
        print(f"✓ 知识库下载完成！")
        print(f"📁 位置: {target_dir}")
        return True
        
    except Exception as e:
        print(f"❌ 下载过程中出错: {e}")
        print(f"💡 提示：请手动运行 'ise-agent-build' 构建知识库")
        return False
    finally:
        # 清理临时目录（如果为空）
        try:
            if temp_dir.exists() and not list(temp_dir.iterdir()):
                temp_dir.rmdir()
        except:
            pass

def check_and_download_knowledge_base(target_dir: Path = None) -> Path:
    """
    检查知识库是否存在，如果不存在则下载
    
    Returns:
        Path: 知识库目录路径
    """
    if target_dir is None:
        target_dir = Path.home() / ".ise_agent" / "db"
    
    # 检查数据库是否存在
    if target_dir.exists() and list(target_dir.iterdir()):
        return target_dir
    
    # 尝试下载
    print(f"\n⚠️  未检测到知识库")
    print(f"💡 正在尝试从官方源下载预构建的知识库...")
    
    if download_knowledge_base(target_dir):
        return target_dir
    
    # 如果下载失败，返回 None，让调用者处理
    return None

