import sqlite3
from pathlib import Path
import sys
import os

# 添加项目根目录到 sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from conf import BASE_DIR

def migrate():
    """为 user_info 表添加唯一约束，防止同一平台同一用户名重复"""
    db_path = Path(BASE_DIR / "db" / "database.db")

    if not db_path.exists():
        print(f"❌ 数据库文件不存在: {db_path}")
        return

    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()

        # 检查是否已有重复数据
        cursor.execute('''
            SELECT type, userName, COUNT(*) as cnt
            FROM user_info
            GROUP BY type, userName
            HAVING cnt > 1
        ''')
        duplicates = cursor.fetchall()

        if duplicates:
            print("⚠️  发现重复账号，开始清理...")
            for type_val, username, count in duplicates:
                print(f"  - 平台 {type_val}, 用户 {username}: {count} 条记录")

                # 保留最新的一条（id 最大），删除其他
                cursor.execute('''
                    DELETE FROM user_info
                    WHERE type = ? AND userName = ?
                    AND id NOT IN (
                        SELECT MAX(id) FROM user_info
                        WHERE type = ? AND userName = ?
                    )
                ''', (type_val, username, type_val, username))

            deleted_count = sum(c - 1 for _, _, c in duplicates)
            print(f"✅ 清理完成，删除 {deleted_count} 条重复记录")
            conn.commit()
        else:
            print("✅ 未发现重复账号")

        # 检查唯一索引是否已存在
        cursor.execute('''
            SELECT name FROM sqlite_master
            WHERE type='index' AND name='idx_unique_user'
        ''')

        if cursor.fetchone():
            print("✅ 唯一索引已存在，无需重复创建")
        else:
            # 创建唯一索引
            cursor.execute('''
                CREATE UNIQUE INDEX idx_unique_user
                ON user_info(type, userName)
            ''')
            conn.commit()
            print("✅ 唯一约束已添加")

if __name__ == "__main__":
    migrate()
