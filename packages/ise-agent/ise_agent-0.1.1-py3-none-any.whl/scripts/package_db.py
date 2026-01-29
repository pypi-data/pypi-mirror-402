"""打包知识库脚本 - 用于创建 GitHub Releases 资源文件"""
import os
import zipfile
import tarfile
from pathlib import Path
from config import VECTOR_DB_DIR

def package_knowledge_base(output_format: str = "zip"):
    """
    将知识库打包为压缩文件
    
    Args:
        output_format: 输出格式，'zip' 或 'tar.gz'
    """
    db_path = Path(VECTOR_DB_DIR)
    
    if not db_path.exists() or not list(db_path.iterdir()):
        print(f"❌ 知识库不存在: {db_path}")
        return False
    
    # 输出文件名
    output_name = "knowledge_base"
    if output_format == "zip":
        output_file = Path(f"{output_name}.zip")
    elif output_format == "tar.gz":
        output_file = Path(f"{output_name}.tar.gz")
    else:
        print(f"❌ 不支持的格式: {output_format}")
        return False
    
    print(f"📦 正在打包知识库...")
    print(f"📁 源目录: {db_path}")
    print(f"📄 输出文件: {output_file}")
    
    try:
        if output_format == "zip":
            with zipfile.ZipFile(output_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, dirs, files in os.walk(db_path):
                    for file in files:
                        file_path = Path(root) / file
                        # 计算相对路径，只保留 db/ 目录下的结构
                        # 这样解压后会在目标目录直接得到 db 的内容
                        arcname = file_path.relative_to(db_path.parent)
                        zipf.write(file_path, arcname)
                        print(f"  添加: {arcname}")
        else:  # tar.gz
            with tarfile.open(output_file, 'w:gz') as tar:
                # 添加整个 db 目录，保留目录名
                tar.add(db_path, arcname=db_path.name, recursive=True)
        
        file_size = output_file.stat().st_size / (1024 * 1024)  # MB
        print(f"✓ 打包完成！")
        print(f"📊 文件大小: {file_size:.2f} MB")
        print(f"📄 文件位置: {output_file.absolute()}")
        print(f"\n💡 提示：将此文件上传到 GitHub Releases 供用户下载")
        
        return True
    except Exception as e:
        print(f"❌ 打包失败: {e}")
        return False

if __name__ == "__main__":
    import sys
    
    format_type = "zip"
    if len(sys.argv) > 1:
        format_type = sys.argv[1]
    
    package_knowledge_base(format_type)

