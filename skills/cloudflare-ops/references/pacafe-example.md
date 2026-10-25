# 範例：PA Cafe

此範例只示範如何套用通用流程，不代表目前已配置完成。Worker 名稱、分支與命令使用前都要重新核對。

## PA Cafe 部署路徑

以下名稱與命令是 PA Cafe 既有路徑提示，使用前以當前程式碼與線上 trigger 核對：

| 環境 | Worker | 部署命令 |
| --- | --- | --- |
| staging | `agent-house-sites-api-staging` | `npx wrangler deploy --config wrangler.hosted.json --env staging` |
| production | `agent-house-sites-api` | `npx wrangler deploy --config wrangler.hosted.json --env=""`，由正式發布管線執行 |

建置與部署是分開步驟；先確認 `npm run build`、相關檢查與輸出已涵蓋本次 commit，再部署。Workers Builds 通常由 staging 分支觸發測試部署；production 經 main 上的 release tag 移動 production 分支觸發。以當前 docs/deployment.md、AGENTS.md 與 workflow 為準，不手推 production、不把 merge main 說成正式上線。

部署前核對 Token 的目標 Worker、明確 config/env、待部署 SHA、目標網域、vars／bindings 與資料隔離。預設 Wrangler 檔可能指向 production，不能依賴操作者記得不要漏參數。staging 與 production 的 DO namespace ID、R2、分析資料集、外部測試端點及 secrets 用途都須核對。

部署後記錄 build／deployment／version ID、SHA、時間與 smoke 結果；API 接受部署不等於 UI 或業務流程驗收。部署失敗先保留原始診斷，辨別來源 IP、身分、role/scope、建置或應用程式問題。避免自動切換到更廣的憑證。
