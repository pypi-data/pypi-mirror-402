# MSSQL 資料庫連線資訊

## 主要連線資訊 (已驗證可用)

| 項目 | 值 |
|------|-----|
| Server | ecs2022.ltc |
| Database | LT_ECS_LTCCore |
| User ID | ecs_user |
| Password | happyecs |
| Encrypt | false |

## 連線字串

```
Data Source=ecs2022.ltc;Initial Catalog=LT_ECS_LTCCore;User ID=ecs_user;Password=happyecs;Encrypt=false
```

## 命令列測試

```bash
sqlcmd -S ecs2022.ltc -d LT_ECS_LTCCore -U ecs_user -P 'happyecs' -C -N o -Q "SELECT @@VERSION"
```

## 其他相關資料庫

| 資料庫名稱 | 用途 |
|-----------|------|
| LT_ECS_LTCCore | 主要 ECS 系統資料庫 |
| LT_ImportData_ltc | 匯入資料 |
| LT_SourceData_ltc | 來源資料 |

## 舊的連線資訊 (無法使用)

以下為原始記錄但經測試無法連線的資訊：
- User: ecs-reader
- Password: JFY2epXMpv86

---

*更新日期: 2026-01-21*
*備註: 正確的連線資訊從原始碼 appsettings.lt.json 中取得*
