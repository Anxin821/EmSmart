"""
全量修复仓库数据：
1. PartTransaction.borrow_time 为空的 → 从 BorrowRecord 补上
2. PartTransaction.return_time 为空的 → 已归还的 BorrowRecord 对应补上
3. WarehousePart.available_qty 超过 total_qty 的 → 修正回来
4. 所有已归还 BorrowRecord 但 PartTransaction 没有 return_time 的 → 补齐
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.core.database import SessionLocal
from app.models.warehouse import BorrowRecord, PartTransaction, WarehousePart
from app.core.timeutil import beijing_now


def main():
    db = SessionLocal()
    try:
        # ─── 1. 修复 PartTransaction.borrow_time 为空 ───
        txs_no_time = db.query(PartTransaction).filter(
            PartTransaction.borrow_time.is_(None),
            PartTransaction.tx_type == "借出",
        ).all()
        fixed_tx_bt = 0
        for tx in txs_no_time:
            # 找对应的 BorrowRecord
            br = db.query(BorrowRecord).filter(
                BorrowRecord.part_id == tx.part_id,
                BorrowRecord.borrower == tx.operator,
            ).order_by(BorrowRecord.id.desc()).first()
            if br and br.borrow_time:
                tx.borrow_time = br.borrow_time
                fixed_tx_bt += 1
                print(f"  [补borrow_time] PartTransaction id={tx.id} part_id={tx.part_id} "
                      f"borrow_time → {br.borrow_time}")
            elif tx.part_id == 385 and tx.operator == "湛":
                # 特殊修复：湛的记录 borrow_time 在 BorrowRecord 有
                br_zhan = db.query(BorrowRecord).filter(
                    BorrowRecord.part_id == 385,
                    BorrowRecord.borrower == "湛",
                ).first()
                if br_zhan and br_zhan.borrow_time:
                    tx.borrow_time = br_zhan.borrow_time
                    fixed_tx_bt += 1
                    print(f"  [特殊补borrow_time] PartTransaction id={tx.id} → {br_zhan.borrow_time}")

        # ─── 2. 修复 PartTransaction.return_time（已归还但没补的） ───
        returned_brs = db.query(BorrowRecord).filter(
            BorrowRecord.status.in_(["已归还", "维修", "丢失", "损坏"]),
        ).all()
        fixed_rt = 0
        for br in returned_brs:
            if not br.borrow_time:
                continue
            borrow_tx = db.query(PartTransaction).filter(
                PartTransaction.part_id == br.part_id,
                PartTransaction.tx_type == "借出",
                PartTransaction.operator == br.borrower,
                PartTransaction.borrow_time == br.borrow_time,
                PartTransaction.return_time.is_(None),
            ).order_by(PartTransaction.id.desc()).first()
            if borrow_tx:
                borrow_tx.return_time = beijing_now()
                fixed_rt += 1
                print(f"  [补return_time] PartTransaction id={borrow_tx.id} part_id={br.part_id} borrower={br.borrower}")

        # ─── 3. 修复 available_qty > total_qty 的治具 ───
        bad_parts = db.query(WarehousePart).filter(
            WarehousePart.part_type == "治具",
            WarehousePart.available_qty > WarehousePart.total_qty,
        ).all()
        fixed_avail = 0
        for p in bad_parts:
            old_avail = p.available_qty
            p.available_qty = p.total_qty
            fixed_avail += 1
            print(f"  [修available] {p.name} id={p.id} available: {old_avail} → {p.total_qty} (total={p.total_qty})")

        # ─── 4. 检查 available_qty < 0 的治具 ───
        neg_parts = db.query(WarehousePart).filter(
            WarehousePart.part_type == "治具",
            WarehousePart.available_qty < 0,
        ).all()
        for p in neg_parts:
            old_avail = p.available_qty
            p.available_qty = 0
            fixed_avail += 1
            print(f"  [修负available] {p.name} id={p.id} available: {old_avail} → 0")

        db.commit()
        print(f"\n结果：修 borrow_time={fixed_tx_bt} 条，补 return_time={fixed_rt} 条，修 available={fixed_avail} 条")
    finally:
        db.close()


if __name__ == "__main__":
    main()