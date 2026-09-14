"""
一次性修复：将 BorrowRecord.borrow_time 与 PartTransaction 同步，并补全已归还记录的 return_time。

修复内容：
1. 修复未归还（status=借出）的 BorrowRecord → 与 PartTransaction 时间对齐
2. 已归还但 PartTransaction.return_time 为空的 → 追补归还时间
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.core.database import SessionLocal
from app.models.warehouse import BorrowRecord, PartTransaction
from app.core.timeutil import beijing_now


def main():
    db = SessionLocal()
    try:
        # ─── 1. 修复未归还的 BorrowRecord ───
        txs = db.query(PartTransaction).filter(
            PartTransaction.tx_type == "借出"
        ).all()
        fixed_borrow = 0
        for tx in txs:
            records = db.query(BorrowRecord).filter(
                BorrowRecord.part_id == tx.part_id,
                BorrowRecord.borrower == tx.operator,
                BorrowRecord.status == "借出",
                BorrowRecord.borrow_time != tx.borrow_time,
            ).order_by(BorrowRecord.id.desc()).all()
            for r in records:
                old_time = r.borrow_time
                r.borrow_time = tx.borrow_time
                fixed_borrow += 1
                print(f"  [未归还] {tx.part_name} borrower={r.borrower} "
                      f"{old_time.strftime('%Y-%m-%d %H:%M:%S')} → "
                      f"{r.borrow_time.strftime('%Y-%m-%d %H:%M:%S')}")

        # ─── 2. 已归还但 PartTransaction 没补 return_time ───
        returned_records = db.query(BorrowRecord).filter(
            BorrowRecord.status == "已归还"
        ).all()
        fixed_return = 0
        for r in returned_records:
            # 找对应的 PartTransaction：无 return_time 的借出记录
            borrow_tx = db.query(PartTransaction).filter(
                PartTransaction.part_id == r.part_id,
                PartTransaction.tx_type == "借出",
                PartTransaction.operator == r.borrower,
                PartTransaction.borrow_time == r.borrow_time,
                PartTransaction.return_time.is_(None),
            ).order_by(PartTransaction.id.desc()).first()
            if borrow_tx:
                borrow_tx.return_time = beijing_now()
                fixed_return += 1
                print(f"  [补归还时间] {borrow_tx.part_name} operator={r.borrower} "
                      f"borrow_time={borrow_tx.borrow_time}")

        # ─── 3. 还检查旧版直接创建的 "归还" 记录（无对应借出记录的） ───
        # 这些记录已经有 return_time 了，不需要修复

        db.commit()
        print(f"\n结果：修复未归还 {fixed_borrow} 条，补归还时间 {fixed_return} 条，重启后端后生效。")
    finally:
        db.close()


if __name__ == "__main__":
    main()