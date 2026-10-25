# PA Cafe：OpenAI 雲端與 Cloudflare 維運標準

這是目標作業標準，不代表線上已完成設定。每次操作先核對儲存庫與線上現況；Token 名稱是命名建議，並非既有憑證。

## 權限配置

| 用途／建議名稱 | 目標資源 | 最小起點 | 放置／使用位置 |
| --- | --- | --- | --- |
| `pacafe-observe-staging-openai` | 指定 staging Worker | Workers Metadata Read-Only | OpenAI 雲端巡檢任務 |
| `pacafe-observe-production-openai` | 指定 production Worker | Workers Metadata Read-Only | OpenAI 雲端正式環境巡檢 |
| `pacafe-source-read-<env>-openai` | 指定 Worker | Workers Content Read-Only，僅在需要讀取線上程式碼時 | 明確需要程式碼比對的任務 |
| `pacafe-deploy-staging-openai` | 指定 staging Worker | Workers Editor | OpenAI 雲端直接部署 staging |
| `pacafe-deploy-staging-builds` | 指定 staging Worker | Workers Editor，確認當前 Builds 支援的 Token 類型 | staging Workers Builds |
| `pacafe-release-production-builds` | 指定 production Worker | Workers Editor，確認當前 Builds 支援的 Token 類型 | production Workers Builds |
| 臨時管理 Token | 任務指定的資源 | 依 API 需求單獨配置 | 初建 Worker、routes、資源建立、Token 管理等管理作業；完成後撤銷 |

單一任務需要兩個環境唯讀時，可明列這兩個 Worker；不要因此放大成帳戶所有 Workers。Metadata Read-Only 可看設定、metrics、logs／traces，但不是「無敏感資訊」：日誌與一般變數仍可能含內容，交付報告應遮蔽。Content Read-Only 的 Worker 程式碼存取不等於 R2、KV 或 D1 資料讀取權限。使用者要求讀取儲存內容時，另配資源特定的唯讀 Token／角色，當場確認產品支援的 scope。

依 [Workers 官方角色](https://developers.cloudflare.com/workers/authorization/workers/) 查證當前權限。Editor 能部署、改設定、管理 secrets、回滾，不是 deploy-only；現有 bindings 的部署不需額外資料資源權限。個別 Worker 的權限不可用來建立尚未存在的 Worker。單一 scope、角色、API 支援不明時，保留未知，不為了消除 403 升成 Admin。

## 先分清三種憑證

- Worker 部署 Token：供 Wrangler 上傳／部署，細粒度授權使用 account-owned Token，環境變數為 `CLOUDFLARE_API_TOKEN` 與 `CLOUDFLARE_ACCOUNT_ID`。
- Workers Builds 的 build token：綁在 trigger 的 `build_token_uuid`，由建置系統部署。逐環境分開核對，不假設更換 OpenAI 任務憑證就會同步更新它。
- Workers Builds 管理 API Token：管理 trigger／命令／變數，可能間接影響部署，不能混入一般唯讀 key。依 [Builds API 文件](https://developers.cloudflare.com/workers/ci-cd/builds/api-reference/) 當場查證；文件目前要求 user-scoped Token，與 Worker 細粒度部署使用的 account-owned Token 不同。唯讀端點若沒有適當 Read 權限，就標示查核受限，不給「只查看用」憑證加 Edit。

Cloudflare connector 的 OAuth 是另一條身分路徑；它的權限或成功結果不能代替新 Token 的驗證。資料面用的 PA Cafe 管理 API Token 也不同於 Cloudflare 控制面 Token，不能混用。

## 建立 Token 的標準交付

先把以下欄位整理成可檢視的配置，再依使用者已授權範圍建立或提供 UI 步驟：

| 欄位 | 要確認的內容 |
| --- | --- |
| 用途 | 巡檢、看程式碼、部署、發布或管理 |
| 身分 | account-owned／user-owned 與該產品 API 支援狀態 |
| 資源 | 帳戶與明列的 Worker／儲存資源，不用所有帳戶或所有 Workers |
| 角色 | 最小能完成任務的角色與來源文件 |
| 來源 | OpenAI Cloud、本機／VPN、Builds，分別驗證出口 |
| 有效期 | 符合任務期限或 CI 維護週期，記錄輪替時間 |
| 存放 | 任務環境的 secret 管理，避免寫入 repo、命令列輸出、報告或公開 skill |
| 驗證 | 預期可做與不可做的操作、實測狀態 |

建議把 Token 參考名稱、用途、scope、到期日、持有人、存放位置與最後驗證時間列在非公開的憑證清冊，清冊不含 Token 值。建立後的秘密值只送入使用者指定的 secret 位置，不透過聊天反覆顯示。普通任務 Token 不授權建立其他 Token。

## PA Cafe 部署路徑

以下名稱與命令是 PA Cafe 既有路徑提示，使用前以當前程式碼與線上 trigger 核對：

| 環境 | Worker | 部署命令 |
| --- | --- | --- |
| staging | `agent-house-sites-api-staging` | `npx wrangler deploy --config wrangler.hosted.json --env staging` |
| production | `agent-house-sites-api` | `npx wrangler deploy --config wrangler.hosted.json --env=""`，由正式發布管線執行 |

建置與部署是分開步驟；先確認 `npm run build`、相關檢查與輸出已涵蓋本次 commit，再部署。Workers Builds 通常由 staging 分支觸發測試部署；production 經 main 上的 release tag 移動 production 分支觸發。以當前 docs/deployment.md、AGENTS.md 與 workflow 為準，不手推 production、不把 merge main 說成正式上線。

部署前核對 Token 的目標 Worker、明確 config/env、待部署 SHA、目標網域、vars／bindings 與資料隔離。預設 Wrangler 檔可能指向 production，不能依賴操作者記得不要漏參數。staging 與 production 的 DO namespace ID、R2、分析資料集、外部測試端點及 secrets 用途都須核對。

部署後記錄 build／deployment／version ID、SHA、時間與 smoke 結果；API 接受部署不等於 UI 或業務流程驗收。部署失敗先保留原始診斷，辨別來源 IP、身分、role/scope、建置或應用程式問題。避免自動切換到更廣的憑證。

## 日常維運

| 情境 | 標準處理 |
| --- | --- |
| 健康／部署狀態巡檢 | 公開健康／版本端點，加指定 Worker 唯讀 metrics、部署紀錄；對照預期 SHA，先不重啟或重部署 |
| 錯誤調查 | 使用 Metadata Read-Only 查指定時段／Worker 的 logs、traces；限制輸出，遮蔽個資與秘密；需要程式碼才另選 Content Read-Only |
| 建置異常 | 查狀態、logs 與命令／分支／Token 參考；重跑 build 可能部署，視為寫入作業 |
| 設定漂移 | 比對 repo 與線上 vars、bindings、routes，敏感值只核對存在性；先產生差異，依授權將設定納入其所屬來源 |
| Token 輪替 | 在授權範圍建立相同最小 scope 新 Token，更新指定消費者，驗證讀取／部署路徑，確認不再有消費者後撤銷舊 Token；失敗保留可回復路徑 |
| Secret 輪替 | 指定環境與外部服務，確認雙金鑰／資料重加密等既有機制；以 secret 管理注入，驗證依賴功能，避免刪除仍用於解密的舊金鑰 |
| 回滾 | 依專案正式發布規則與 schema／DO migration 相容性執行；程式碼回滾不等於資料回復 |
| 資源刪除／資料修復 | 獨立指定身分、資料範圍、影響與回復方式，不當成一般巡檢的附帶動作 |

## OpenAI 雲端來源限制

依主文件的 CIDR 流程取得當前官方 feed。來源清單只附加到實際由 OpenAI Cloud 使用的 Token；Builds 或本機用的憑證採用其各自來源政策。不要把 OpenAI 共用 CIDR 當成只允許自己的帳號，也不要將 HiNet 配發網段稱為台北專用或完整動態 IP 保證。

唯讀查核可以用 API Token verify 確認狀態，但它不驗證 IP 限制，也不證明 role/scope 正確。從實際執行環境對指定 Worker 做授權讀取，才能證明該路徑可用。拒絕寫入的測試遵循主文件的專用測試資源原則；未測的能力明列 NOT RUN。
