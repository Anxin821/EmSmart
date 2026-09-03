/* ============================================================
   一次性数据清洗脚本 —— 去除 MES 枚举列两端的 | 和空白字符
   ------------------------------------------------------------
   数据库 : SQL Server (WorkTaskDB)
   目标列 : bugs.status, bugs.severity,
            dev_requests.priority, dev_requests.status
   背景   : 这些列历史数据是脏值（如 "|开发中|"），后端 routers/mes.py 的
            _req_to_dict / _bug_to_dict 返回前会 .strip().lstrip('|').rstrip('|').strip()
            清洗显示，但 crud 过滤/排序曾按精确匹配而失效。清洗后即可全部走精确匹配。
   清洗规则: 去掉所有 | 、TAB(9)、LF(10)、CR(13)，再 LTRIM/RTRIM 去首尾空格
            （等价于上面 Python 的清洗逻辑）
   兼容   : 仅用 LTRIM/RTRIM/REPLACE/CHAR/CROSS APPLY/DATALENGTH，全 SQL Server 版本可用
   ⚠ 执行前请先备份数据库或相关表！建议逐段执行、核对行数无误再 COMMIT。
   ============================================================ */


/* ---------- 第 0 步（可选）：备份两张表，便于回滚 ----------
SELECT * INTO bugs_backup_20260903         FROM bugs;
SELECT * INTO dev_requests_backup_20260903 FROM dev_requests;
------------------------------------------------------------ */


/* ---------- 第 1 步：预览将被修改的脏值（只查不改，先核对 old→new）---------- */
SELECT 'bugs.status' AS col_name, b.id, b.status AS old_val, c.clean AS new_val
FROM bugs b
CROSS APPLY (SELECT LTRIM(RTRIM(REPLACE(REPLACE(REPLACE(REPLACE(b.status,'|',''),CHAR(9),''),CHAR(10),''),CHAR(13),''))) AS clean) c
WHERE DATALENGTH(b.status) <> DATALENGTH(c.clean)
UNION ALL
SELECT 'bugs.severity', b.id, b.severity, c.clean
FROM bugs b
CROSS APPLY (SELECT LTRIM(RTRIM(REPLACE(REPLACE(REPLACE(REPLACE(b.severity,'|',''),CHAR(9),''),CHAR(10),''),CHAR(13),''))) AS clean) c
WHERE DATALENGTH(b.severity) <> DATALENGTH(c.clean)
UNION ALL
SELECT 'dev_requests.priority', d.id, d.priority, c.clean
FROM dev_requests d
CROSS APPLY (SELECT LTRIM(RTRIM(REPLACE(REPLACE(REPLACE(REPLACE(d.priority,'|',''),CHAR(9),''),CHAR(10),''),CHAR(13),''))) AS clean) c
WHERE DATALENGTH(d.priority) <> DATALENGTH(c.clean)
UNION ALL
SELECT 'dev_requests.status', d.id, d.status, c.clean
FROM dev_requests d
CROSS APPLY (SELECT LTRIM(RTRIM(REPLACE(REPLACE(REPLACE(REPLACE(d.status,'|',''),CHAR(9),''),CHAR(10),''),CHAR(13),''))) AS clean) c
WHERE DATALENGTH(d.status) <> DATALENGTH(c.clean);


/* ---------- 第 2 步：在事务中执行清洗，核对影响行数与预览一致后 COMMIT ---------- */
BEGIN TRAN;

UPDATE b SET status = c.clean
FROM bugs b
CROSS APPLY (SELECT LTRIM(RTRIM(REPLACE(REPLACE(REPLACE(REPLACE(b.status,'|',''),CHAR(9),''),CHAR(10),''),CHAR(13),''))) AS clean) c
WHERE DATALENGTH(b.status) <> DATALENGTH(c.clean);

UPDATE b SET severity = c.clean
FROM bugs b
CROSS APPLY (SELECT LTRIM(RTRIM(REPLACE(REPLACE(REPLACE(REPLACE(b.severity,'|',''),CHAR(9),''),CHAR(10),''),CHAR(13),''))) AS clean) c
WHERE DATALENGTH(b.severity) <> DATALENGTH(c.clean);

UPDATE d SET priority = c.clean
FROM dev_requests d
CROSS APPLY (SELECT LTRIM(RTRIM(REPLACE(REPLACE(REPLACE(REPLACE(d.priority,'|',''),CHAR(9),''),CHAR(10),''),CHAR(13),''))) AS clean) c
WHERE DATALENGTH(d.priority) <> DATALENGTH(c.clean);

UPDATE d SET status = c.clean
FROM dev_requests d
CROSS APPLY (SELECT LTRIM(RTRIM(REPLACE(REPLACE(REPLACE(REPLACE(d.status,'|',''),CHAR(9),''),CHAR(10),''),CHAR(13),''))) AS clean) c
WHERE DATALENGTH(d.status) <> DATALENGTH(c.clean);

-- ✅ 核对上面 4 条 UPDATE 的影响行数与第 1 步预览一致后，执行提交：
COMMIT TRAN;
-- ❌ 若发现异常，改为回滚： ROLLBACK TRAN;


/* ---------- 第 3 步：验证已无脏值（下面查询应返回 0 行）---------- */
SELECT 'bugs.status' AS col_name, id, status AS val FROM bugs
WHERE status LIKE '%|%' OR DATALENGTH(status) <> DATALENGTH(LTRIM(RTRIM(status)))
UNION ALL
SELECT 'bugs.severity', id, severity FROM bugs
WHERE severity LIKE '%|%' OR DATALENGTH(severity) <> DATALENGTH(LTRIM(RTRIM(severity)))
UNION ALL
SELECT 'dev_requests.priority', id, priority FROM dev_requests
WHERE priority LIKE '%|%' OR DATALENGTH(priority) <> DATALENGTH(LTRIM(RTRIM(priority)))
UNION ALL
SELECT 'dev_requests.status', id, status FROM dev_requests
WHERE status LIKE '%|%' OR DATALENGTH(status) <> DATALENGTH(LTRIM(RTRIM(status)));


/* ============================================================
   可选：work_orders 表（_order_to_dict 未做剥离，通常数据是干净的）
   若下面预览查出脏值，再执行对应的 UPDATE；否则无需处理。
   ------------------------------------------------------------
SELECT 'work_orders.priority' AS col_name, w.id, w.priority AS old_val, c.clean AS new_val
FROM work_orders w
CROSS APPLY (SELECT LTRIM(RTRIM(REPLACE(REPLACE(REPLACE(REPLACE(w.priority,'|',''),CHAR(9),''),CHAR(10),''),CHAR(13),''))) AS clean) c
WHERE DATALENGTH(w.priority) <> DATALENGTH(c.clean)
UNION ALL
SELECT 'work_orders.status', w.id, w.status, c.clean
FROM work_orders w
CROSS APPLY (SELECT LTRIM(RTRIM(REPLACE(REPLACE(REPLACE(REPLACE(w.status,'|',''),CHAR(9),''),CHAR(10),''),CHAR(13),''))) AS clean) c
WHERE DATALENGTH(w.status) <> DATALENGTH(c.clean)
UNION ALL
SELECT 'work_orders.order_type', w.id, w.order_type, c.clean
FROM work_orders w
CROSS APPLY (SELECT LTRIM(RTRIM(REPLACE(REPLACE(REPLACE(REPLACE(w.order_type,'|',''),CHAR(9),''),CHAR(10),''),CHAR(13),''))) AS clean) c
WHERE DATALENGTH(w.order_type) <> DATALENGTH(c.clean);
   ============================================================ */
