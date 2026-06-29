# 情感标注系统数据库脚本

本项目使用SQLite数据库存储情感标注数据和用户排序信息，提供更好的数据管理和查询性能。

## 文件说明

### 核心管理脚本
- `unified_db_manager.py` - **统一数据库管理器**，管理合并后的统一数据库的所有操作

### 安全和维护工具
- `security_check.py` - 安全配置检查脚本，检查系统的安全配置是否正确

## 项目初始化（首次运行）

### 🚀 使用统一数据库管理器

```bash
# 初始化统一数据库
python scripts/unified_db_manager.py
```

**注意**：首次运行必须执行数据库初始化，否则应用启动时数据库将为空。

这些命令会自动完成：
- 创建 `database/unified_emotion_system.db` 统一数据库文件
- 创建所有必要的表结构（用户、管理员、情感标注、分组等）
- 创建默认管理员账户
- 创建所有必要的索引和触发器

### 📊 验证数据库创建

数据库创建完成后，可以通过Web应用界面或直接查看数据库文件来验证：

```bash
# 检查数据库文件是否存在
ls -la database/unified_emotion_system.db
```

## 数据库表结构

### emotion_labels 表（情感标注数据）

| 字段名 | 类型 | 说明 |
|--------|------|------|
| id | INTEGER | 主键，自增 |
| audio_file | TEXT | 音频文件名 |
| speaker | TEXT | 说话人ID |
| username | TEXT | 标注用户名 |
| v_value | REAL | 情感效价值 |
| a_value | REAL | 情感激活值 |
| emotion_type | TEXT | 情感类型（neutral/non-neutral） |
| discrete_emotion | TEXT | 离散情感标签 |
| patient_status | TEXT | 患者状态（patient/non-patient） |
| audio_duration | REAL | 音频时长（秒） |
| va_complete | BOOLEAN | VA标注是否完整 |
| discrete_complete | BOOLEAN | 离散情感标注是否完整 |
| timestamp | DATETIME | 创建时间 |
| updated_at | DATETIME | 更新时间 |

### user_speaker_orders 表（用户说话人排序）

| 字段名 | 类型 | 说明 |
|--------|------|------|
| id | INTEGER | 主键，自增 |
| username | TEXT | 用户名 |
| speaker_order | TEXT | 说话人排序（JSON格式） |
| group_id | INTEGER | 分组ID，外键关联 group_status 表 |
| created_at | DATETIME | 创建时间 |
| updated_at | DATETIME | 更新时间 |

### user_audio_orders 表（用户音频文件排序）

| 字段名 | 类型 | 说明 |
|--------|------|------|
| id | INTEGER | 主键，自增 |
| username | TEXT | 用户名 |
| speaker | TEXT | 说话人ID |
| audio_order | TEXT | 音频文件排序（JSON格式） |
| group_id | INTEGER | 分组ID，外键关联 group_status 表 |
| created_at | DATETIME | 创建时间 |
| updated_at | DATETIME | 更新时间 |

## 项目启动

数据库初始化完成后，可以启动应用：

```bash
python start_server.py
```

## 数据库管理功能

### 统一数据库管理器 (unified_db_manager.py)

```bash
# 初始化统一数据库
python scripts/unified_db_manager.py

# 查看数据库信息和统计
# 可以通过管理员界面查看系统状态和数据统计

# 备份数据库
cp database/unified_emotion_system.db database/backup_$(date +%Y%m%d_%H%M%S).db

# 导出数据（可通过管理员界面进行）
# 支持CSV格式导出标注数据
```

### 分组管理功能

```bash
# 查看分组数据和标注情况
python utils/group_data_viewer.py
```

### 数据管理

通过管理员界面可以进行：
- 用户管理和状态查看
- 数据导出（CSV格式）
- 系统状态监控
- 分组分配管理

### 安全检查

```bash
# 检查系统安全配置
python scripts/security_check.py
```

## 数据库优势

1. **性能提升**：数据库查询比JSON文件读取更快
2. **数据完整性**：支持事务和约束，确保数据一致性
3. **并发支持**：多用户同时标注时更安全
4. **查询功能**：支持复杂的数据查询和统计
5. **扩展性**：便于后续添加新功能和字段
6. **用户体验**：支持个性化排序，提升标注效率

## 注意事项

- **⚠️ 首次运行**：必须先执行 `python scripts/unified_db_manager.py` 初始化数据库，否则应用启动时数据库将为空
- **数据库位置**：
  - 统一数据库：`database/unified_emotion_system.db`（包含所有数据表）
- **环境配置**：
  - 确保设置了 `SECRET_KEY` 环境变量（至少32个字符）
  - 建议在激活的虚拟环境中运行所有命令
  - 使用 `python3` 命令执行脚本
- **数据管理**：
  - 定期备份数据库文件（使用 `cp` 命令备份 `unified_emotion_system.db`）
  - 通过管理员界面可以安全管理数据
  - 支持数据导出功能，便于数据分析
- **安全性**：
  - 系统支持多级权限管理（超级管理员、普通管理员、用户）
  - 使用 `security_check.py` 定期检查安全配置
  - 管理员密码支持复杂度要求和安全验证
- **故障恢复**：如遇问题，可删除数据库文件重新初始化