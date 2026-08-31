-- 修复 WiFi AP 的 ap_id 字段
-- 将空字符串的 ap_id 更新为 'AP-' 加上 id 的格式

USE WorkTaskDB;
GO

UPDATE wifi_aps 
SET ap_id = 'AP-' + CAST(id AS NVARCHAR(10))
WHERE ap_id IS NULL OR ap_id = '';

-- 验证修复结果
SELECT id, ap_id, ssid, production_line, status 
FROM wifi_aps;
