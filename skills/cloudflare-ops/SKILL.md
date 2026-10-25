---
name: cloudflare-ops
description: 標準化 OpenAI 雲端環境操作 PA Cafe 的 Cloudflare 最小權限 API Token、staging 部署、production 發布、唯讀查核與日常維運；包含來源 CIDR 與憑證輪替。
---

# Cloudflare Ops

使用台灣繁體中文。依使用者指定的盤查、產生檔案或實際變更範圍執行；「先不要改」僅進行唯讀查核與要求的本機輸出。建立此 skill 不授權未來部署、建立 Token 或改動線上資源。

## 依用途選擇作業方式

本 skill 的主體是 OpenAI 雲端環境與 PA Cafe 的 Cloudflare 部署及維運權限標準化，CIDR 是輔助來源限制。使用 scoped API Token；使用者口中的 API key 預設指此 Token，不採用 Global API Key。

先讀 [PA Cafe 權限與維運標準](references/pacafe-operations.md)，選擇唯讀巡檢、staging 部署、production 發布或臨時管理用途。依「環境 × 用途 × 執行來源」分開 Token，從唯讀開始，只在任務需要時選用部署憑證。OpenAI 雲端環境只注入目前任務所需的 Token；production 寫入憑證留在正式發布管線，除非使用者明確授權其他使用方式。

## 部署與資源盤查

從目前儲存庫的 AGENTS.md、Git 狀態、Wrangler 設定、建置腳本與 CI/CD 開始。記錄原始碼 HEAD 與 dirty 狀態，對照實際部署來源，不以本機 main 當成線上版本。

優先使用 Cloudflare connector 的唯讀 API；先讀工具說明並搜尋 API schema，再呼叫端點。工具不支援才使用已授權的 CLI 或瀏覽器。只列 secrets 名稱，避免讀取、列印或發布內容。

逐環境核對：

- 帳戶、Worker 名稱、網址、routes／custom domains 與 workers.dev。
- 實際生效部署、版本、時間，以及建置來源分支、build／deploy 命令。
- R2 bucket、DO namespace ID、KV、D1、Queues、service bindings、Analytics Engine、限流、AI 及靜態資產。
- 公開變數與外部服務的正式／測試端點、回呼網址及登入環境。
- Workers Builds trigger 使用的 Token ID 是否共用；必要時只讀取其政策，不取得 Token 值。

設定檔證明預期，線上 settings 證明當前綁定，部署／建置紀錄證明發布狀態。DO class 或 binding 同名不表示共用資料，要比對 namespace ID；兩邊 secret 同名也無法證明值相同或不同。

找出線上 vars 未納入部署設定、繼承到正式 routes、預設 Wrangler 檔案指向 production、共用部署 Token 等缺口。依當前 Wrangler 官方文件確認各設定的繼承與覆蓋語意。遇到 403，記錄不可讀取的項目，繼續其餘盤查，不以未知代替已隔離。

## Token 只能部署 staging

先即時查閱 [Workers 權限](https://developers.cloudflare.com/workers/authorization/workers/) 與 [Wrangler 授權](https://developers.cloudflare.com/workers/authorization/)，確認目前支援與限制。

若 staging 是獨立且已存在的 Worker，使用 account-owned API Token，範圍為 Specified Workers，只選 staging，選足以部署的 Editor。staging／production 的本機或 CI 憑證分開；保留明確的 config 與 env 部署參數。不要為了部署現有 bindings 就順手加入帳戶層級 Workers、R2、KV、Pages 或 zone routes 寫入權限。

說明 Editor 除了部署也可修改設定與管理 secrets；Git 分支／release 規則不是 API Token 的授權邊界。Worker scope 限制部署目標，不足以自行證明無法改綁同帳戶正式資源或透過程式存取正式資料。依文件與實測結果標示邊界；若要求強資料隔離，評估獨立帳戶或受控部署流程，不先承諾同帳戶完全隔離。

新 Token 的有效性、staging 部署成功、production 操作遭拒是不同證據。只有使用者授權變更後才驗證部署；拒絕測試使用專用可拋棄 Worker，或有明確無副作用保證的授權檢查，避免對正式環境嘗試可能成功的寫入。

## CIDR 白名單

先識別真正發出請求的位置：本機 shell、遠端開發機、Codex Cloud、遠端 connector 或 Workers Builds。查詢 IP 必須從相同執行路徑進行；本機的出口不代表其他執行環境。

Codex Cloud 出口來源以 [OpenAI 官方出口文件](https://developers.openai.com/api/docs/guides/ip-addresses) 當前指定的 feed 為準，目前是 `https://openai.com/chatgpt-agents.json`。每次重新下載，保留原始 JSON、creationTime、抓取時間、SHA-256 與 IPv4／IPv6 筆數，不把這次的筆數、IP 或網段快照硬編碼進 skill。

下載到暫存檔後執行：

```bash
python3 scripts/format_cidrs.py --source-file /tmp/chatgpt-agents.json --output-dir /tmp/cloudflare-allowlist
```

使用者要求加入額外出口時，以 `--add <CIDR>` 加在清單末尾；可重複指定。腳本產生每行一筆、逗號分隔、API condition JSON 與來源摘要，只寫輸出目錄，不呼叫 Cloudflare。

本機單一 IPv4 使用 `/32`，IPv6 使用 `/128`。用公開 IP 回顯服務查出當前出口；需要 ISP 範圍時查 [APNIC RDAP](https://rdap.apnic.net/ip/)，核對持有人與 cidr0_cidrs。公司登記地址在台北不代表配發網段只在台北使用；一筆 HiNet 配發也不是全部 HiNet 網段或使用者日後一定取得的動態 IP 範圍。

使用者要求 ISP 網段時，提供有來源的範圍，說明涵蓋量與動態 IP 的不確定性；只把已授權的範圍加入檔案，避免默認擴大成全部 ISP。需要涵蓋完整 ISP 時，另外查證配發／路由資料與完整性，不能把少數例子冒充完整清單。合併網段只可在涵蓋 IP 集合完全相同時進行。

Cloudflare 支援 CIDR 的 `condition.request.ip.in`；參閱 [Token 限制](https://developers.cloudflare.com/fundamentals/api/how-to/restrict-tokens/) 與 [API 格式](https://developers.cloudflare.com/fundamentals/api/how-to/create-via-api/)。UI 接受逗號分隔時提供對應檔案；實際欄位限制與大量貼入是否成功需另行確認。Verify Token 端點不套用 IP 過濾，不能以它成功就宣稱來源 IP 通過限制。

IP 白名單識別共用網路出口，無法識別使用者或 workspace；搭配 Worker 權限限制。來源 feed 可能更新；本機動態 IP 可能變更。固定 VPN／NAT 出口可作為要求穩定來源時的選項，不能將其當成已配置。

## 交付

盤查時提供環境比較、缺口、最小調整方案，以及 PASS／PARTIAL／BLOCKED／NOT RUN 的證據界線。產生 CIDR 時提供可複製檔案、來源時間、筆數、額外網段與是否已套用。公開儲存庫只放通用流程與工具；帳戶 ID、家用出口、Token、secrets 與部署快照留在使用者指定的非公開位置。
