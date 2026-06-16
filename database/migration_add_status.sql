-- 数据库迁移脚本：为 production_record 表添加 status 列
-- 问题：BaseModel 定义了 status 字段，但数据库表缺少此列
-- 执行方式：docker exec -i data_manage_system-mysql-1 mysql -uroot -proot production_system < migration_add_status.sql

-- 检查列是否存在，如果不存在则添加
SET @dbname = 'production_system';
SET @tablename = 'production_record';
SET @columnname = 'status';
SET @preparedStatement = (SELECT IF(
    (
        SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = @dbname
        AND TABLE_NAME = @tablename
        AND COLUMN_NAME = @columnname
    ) > 0,
    'SELECT "Column status already exists in production_record" AS message',
    CONCAT('ALTER TABLE ', @tablename, ' ADD COLUMN status TINYINT DEFAULT 1 COMMENT "状态: 0删除/1正常" AFTER record_time')
));
PREPARE alterIfNotExists FROM @preparedStatement;
EXECUTE alterIfNotExists;
DEALLOCATE PREPARE alterIfNotExists;

-- 添加索引
SET @indexname = 'idx_status';
SET @preparedStatement = (SELECT IF(
    (
        SELECT COUNT(*) FROM INFORMATION_SCHEMA.STATISTICS
        WHERE TABLE_SCHEMA = @dbname
        AND TABLE_NAME = @tablename
        AND INDEX_NAME = @indexname
    ) > 0,
    'SELECT "Index idx_status already exists" AS message',
    CONCAT('CREATE INDEX ', @indexname, ' ON ', @tablename, ' (status)')
));
PREPARE addIndexIfNotExists FROM @preparedStatement;
EXECUTE addIndexIfNotExists;
DEALLOCATE PREPARE addIndexIfNotExists;

SELECT 'Migration completed successfully!' AS result;
