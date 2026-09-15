"""
清空库房数据库所有记录（不删表结构，只清数据）。

涉及表：
  - part_transactions          ← 操作流水（先删，无外键依赖）
  - warehouse_borrow_records   ← 借出记录
  - warehouse_parts            ← 物品主表（最后删）

用法：
  python scripts/clear_warehouse_data.py

安全措施：
  - 执行前要求输入 yes 确认
  - 打印每条 DELETE 语句影响的行数
  - 全程在一个事务中，失败自动回滚
"""
import sys
from pathlib import Path

# ── 将 backend 目录加入 sys.path，使 from app.xxx 能导入 ──
_BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_BACKEND_DIR))

from sqlalchemy import text
from app.core.database import engine


def confirm() -> bool:
    print("⚠️  即将清空库房所有数据！")
    print(f"    涉及表：part_transactions、warehouse_borrow_records、warehouse_parts")
    print(f"    数据库：{engine.url}")
    ans = input("确认请输入 yes 并回车，否则直接回车或输入 no > ").strip().lower()
    return ans == "yes"


def main():
    print("=" * 50)
    print("  库房数据清空脚本")
    print("=" * 50)

    if not confirm():
        print("❌ 已取消，未做任何修改。")
        return

    # SQL 语句（DELETE 无外键约束问题，但按依赖顺序删更安全）
    stmts = [
        ("part_transactions（操作流水）", text("DELETE FROM part_transactions")),
        (
            "warehouse_borrow_records（借出记录）",
            text("DELETE FROM warehouse_borrow_records"),
        ),
        ("warehouse_parts（物品主表）", text("DELETE FROM warehouse_parts")),
    ]

    with engine.begin() as conn:
        for label, stmt in stmts:
            result = conn.execute(stmt)
            print(f"  ✅ {label} → 删除 {result.rowcount} 行")

    print("=" * 50)
    print("  库房数据已全部清空！")
    print("=" * 50)


if __name__ == "__main__":
    main()