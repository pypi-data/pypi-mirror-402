"""构建知识库的命令行入口"""
import os
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

def main():
    """构建知识库"""
    # 设置数据库路径（优先使用用户目录）
    user_db_path = Path.home() / ".ise_agent" / "db"
    user_db_path.mkdir(parents=True, exist_ok=True)
    
    # 临时修改环境变量
    os.environ["VECTOR_DB_DIR"] = str(user_db_path)
    
    try:
        import config as config_module
        config_module.VECTOR_DB_DIR = str(user_db_path)
    except ImportError:
        pass
    
    from scripts.build_kb import main as build_main
    build_main()

if __name__ == "__main__":
    main()

