# Cloudflare：權限、部署與日常維運標準

這是目標作業標準，不代表線上已完成設定。每次操作先核對儲存庫與線上現況；Token 名稱是命名建議，並非既有憑證。

## 權限配置

| 用途／建議名稱 | 目標資源 | 最小起點 | 放置／使用位置 |
| --- | --- | --- | --- |
| `<project>-observe-staging-openai` | 指定 staging Worker | Workers Metadata Read-Only | OpenAI 雲端巡檢任務 |
| `<project>-observe-production-openai` | 指定 production Worker | Workers Metadata Read-Only | OpenAI 雲端正式環境巡檢 |
| `<project>-source-read-<env>-openai` | 指定 Worker | Workers Content Read-Only，僅在需要讀取線上程式碼時 | 明確需要程式碼比對的任務 |
| `<project>-deploy-staging-openai` | 指定 staging Worker | Workers Editor | OpenAI 雲端直接部署 staging |
| `<project>-deploy-staging-builds` | 指定 staging Worker | Workers Editor，確認當前 Builds 支援的 Token 類型 | staging Workers Builds |
| `<project>-release-production-builds` | 指定 production Worker | Workers Editor，確認當前 Builds 支援的 Token 類型 | production Workers Builds |
| 臨時管理 Token | 任務指定的資源 | 依 API 需求單獨配置 | 初建 Worker、routes、資源建立、Token 管理等管理作業；完成後撤銷 |

單一任務需要兩個環境唯讀時，可明列這兩個 Worker；不要因此放大成帳戶所有 Workers。Metadata Read-Only 可看設定、metrics、logs／traces，但不是「無敏感資訊」：日誌與一般變數仍可能含內容，交付報告應遮蔽。Content Read-Only 的 Worker 程式碼存取不等於 R2、KV 或 D1 資料讀取權限。使用者要求讀取儲存內容時，另配資源特定的唯讀 Token／角色，當場確認產品支援的 scope。

依 [Workers 官方角色](https://developers.cloudflare.com/workers/authorization/workers/) 查證當前權限。Editor 能部署、改設定、管理 secrets、回滾，不是 deploy-only；現有 bindings 的部署不需額外資料資源權限。個別 Worker 的權限不可用來建立尚未存在的 Worker。單一 scope、角色、API 支援不明時，保留未知，不為了消除 403 升成 Admin。

## 跨產品範圍

上表用 Workers 示範角色切分，其他 Cloudflare 產品也以「操作 × 實際支援的資源 scope × 來源 × 期限」規劃，不把 Workers 的角色／scope 名稱照抄過去。

| 類別 | 配置時要另外查證 |
| --- | --- |
| DNS／Routes／Custom Domains | zone scope 與各 API 所需權限；不可假設能細分到單筆 DNS record，也不把 DNS Edit 加入普通部署 Token |
| Pages | Pages 專用權限和 production／preview 部署行為；不能套用個別 Worker 的角色當成 Pages 專案隔離 |
| R2／KV／D1／Queues／其他資料服務 | 產品當前是否支援 bucket／namespace／database 層級 scope，以及控制面與資料面憑證的差異；唯讀內容也是資料外洩能力 |
| Access／Gateway／Tunnel | 管理 API Token 與執行服務的 service token／tunnel credential 分開；權限能改 policy 或 connector 時視為高權力 |
| Audit Logs／Logpush | 查事件和管理輸出工作的權限不同；即使 HTTP GET 也可能要求 Edit，不能只按 HTTP verb 宣稱唯讀 |

每個目標端點先搜尋官方 API schema，發現產品限制時記錄並選擇分帳戶／受控流程等真正可執行替代方案，不為追求統一格式而虛構 resource scope。

## 先分清三種憑證

- Worker 部署 Token：供 Wrangler 上傳／部署，細粒度授權使用 account-owned Token，環境變數為 `CLOUDFLARE_API_TOKEN` 與 `CLOUDFLARE_ACCOUNT_ID`。
- Workers Builds 的 build token：綁在 trigger 的 `build_token_uuid`，由建置系統部署。逐環境分開核對，不假設更換 OpenAI 任務憑證就會同步更新它。
- Workers Builds 管理 API Token：管理 trigger／命令／變數，可能間接影響部署，不能混入一般唯讀 key。依 [Builds API 文件](https://developers.cloudflare.com/workers/ci-cd/builds/api-reference/) 當場查證；文件目前要求 user-scoped Token，與 Worker 細粒度部署使用的 account-owned Token 不同。唯讀端點若沒有適當 Read 權限，就標示查核受限，不給「只查看用」憑證加 Edit。

Cloudflare connector 的 OAuth 是另一條身分路徑；它的權限或成功結果不能代替新 Token 的驗證。資料面用的應用程式自己的管理 API Token 也不同於 Cloudflare 控制面 Token，不能混用。

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

## 專案部署路徑

將實際專案的環境、Worker 名稱、config/env、建置命令、來源 SHA、發布門檻與資料綁定記錄成環境表；參考 [PA Cafe 範例](pacafe-example.md)，不套用其名稱或發布規則到其他專案。

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

依 [批次配置流程](automation.md)取得當前官方 feed。來源清單只附加到實際由 OpenAI Cloud 使用的 Token；Builds 或本機用的憑證採用其各自來源政策。不要把 OpenAI 共用 CIDR 當成只允許自己的帳號，也不要將 HiNet 配發網段稱為台北專用或完整動態 IP 保證。

唯讀查核可以用 API Token verify 確認狀態，但它不驗證 IP 限制，也不證明 role/scope 正確。從實際執行環境對指定 Worker 做授權讀取，才能證明該路徑可用。拒絕寫入的測試遵循主文件的專用測試資源原則；未測的能力明列 NOT RUN。
