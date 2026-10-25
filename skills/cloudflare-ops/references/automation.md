# Agent 批次配置：CIDR 與 Token IP 政策

隨附工具只處理 CIDR 和單一既有 Token 的 IP 條件。帳戶登入、建立成員、建立 Token 或部署等控制依官方 API／IaC 另外配置，不讓一個泛用腳本暗中擁有全部權力。一般 agent 使用唯讀／部署身分；Token 管理工具在獨立已授權管理工作執行。

工具使用 Python 3 標準函式庫；套用器的檔案鎖使用 POSIX fcntl，適用 Linux／macOS。Windows 請在受控 Linux 工作使用，或透過 connector 執行相同已檢視計畫，不直接假設腳本相容。

## 下載、驗證與輸出

先查 [OpenAI 出口文件](https://developers.openai.com/api/docs/guides/ip-addresses)，確認 Codex Cloud 當前 feed 仍是 `https://openai.com/chatgpt-agents.json`。腳本目前只會從這個公開網址下載，不需要 Cloudflare 憑證。

在 skill 根目錄執行，輸出目錄每次使用新路徑：

```bash
python3 scripts/format_cidrs.py --fetch-openai --output-dir /tmp/cf-egress-new
```

也可在允許網路的環境下載 JSON，再用 `--source-file <file>` 離線轉換。額外已授權的固定出口用 `--add <CIDR>`，可重複指定。輸出 source.json、metadata.json、逐行、逗號與 condition.json；metadata 保存來源時間、下載時間、hash、IPv4／IPv6 與追加網段。來源失敗、空清單、非法 CIDR 不可產生用來清空限制的 payload。工具不擴大網段、預設不覆寫既有輸出。

注意：格式器 condition.json 目前預設 `request_ip`，對應當前 [Account Token API](https://developers.cloudflare.com/api/resources/accounts/subresources/tokens/methods/update/) 的參考格式；部分 [教學文件](https://developers.cloudflare.com/fundamentals/api/how-to/create-via-api/) 仍使用 `request.ip`。以目標端點最新 schema 及實際 GET 為準，可用 `--condition-key request.ip` 選擇舊 wire 格式，兩種不可同時傳。condition.json 只是片段，不是可直接 PUT 的完整 Token。

## 產生單一 Token 更新計畫

1. 用已授權的管理身分 GET 目標 Token 詳情，只保留 metadata／policy 回應到非公開、權限受限的檔案；不是 Token 秘密值。確認 owner、account、token ID 與用途。日常觀察 Token 沒有管理其他 Token 的權限。
2. 先選擇追加或替換。`add` 預設保留原允許網段，可用於第一次增加來源；feed 定期同步要用 `replace`，以本次完整 feed 加明確額外出口取代允許清單，避免舊網段永遠殘留。
3. 產生計畫：

```bash
python3 scripts/token_ip_plan.py --token-file /tmp/token-details.json --cidr-file /tmp/cf-egress-new/allowlist.txt --owner account --account-id <ACCOUNT_ID> --mode replace --output-dir /tmp/cf-token-plan-new
```

如果原 Token 沒有 IP 條件，加入依目標 API 確認過的 `--condition-key request_ip` 或 `--condition-key request.ip`。user-owned Token 使用 `--owner user`，不提供 account-id。

plan.json 明列目標 API 路徑、原政策基準 hash、完整 PUT body、增加／移除 CIDR；request-body.json 可供 connector 或 CLI 使用。腳本保留既有 scope／roles、名稱、status、TTL、not_before 與 `not_in`，不新增管理能力。對未識別 Token 回應欄位停下來查當前 API schema，避免更新時默默捨棄新欄位；目前 schema 允許的 status 保持原值。拒絕 `/0`、空清單、無完整 policies、混合條件欄位與覆寫既有計畫。entry 差異不等於精確 IP 集合差異，重疊網段／排除範圍需另核對。

先檢查新 feed 的 freshness、大小變化、額外出口、原來的特殊允許來源、排除網段是否遮蔽新來源，以及是否仍有獨立管理／復原路徑。清單過大時實際 API 是否接受屬於待驗證能力；不憑空宣稱一定可接受上千筆。

## 套用：只有在已授權改動時

先離線驗證並取得計畫 hash：

```bash
python3 scripts/apply_token_ip_plan.py --plan-file /tmp/cf-token-plan-new/plan.json
```

沒有 `--apply` 時完全不送 API。管理憑證由秘密管理機制注入 `CF_OPS_TOKEN_ADMIN`，不放在命令參數、腳本、stdout 或 repo。依使用者已給的授權執行，不因工具流程自行要求重複確認：

```bash
python3 scripts/apply_token_ip_plan.py --plan-file /tmp/cf-token-plan-new/plan.json --apply --expected-plan-sha256 <REVIEWED_PLAN_SHA256> --owner account --expected-account-id <ACCOUNT_ID> --expected-token-id <TARGET_TOKEN_ID> --exclusive-writer
```

這個命令固定向 `api.cloudflare.com` 呼叫：GET → 比對基準 → 單次 PUT → GET 回讀。拒絕 redirect，不追蹤其他 hostname；不建立／刪除 Token，不改 policies／TTL／status／排除條件，不分批覆蓋清單。也可由 Cloudflare connector 執行相同單一更新，避免讓模型重新輸出上千筆：由可信本機程式讀完整 request-body.json，或使用支援檔案的 API client。

套用時另輸入從工作目標獨立核對的 owner／帳戶／Token ID，不只相信計畫檔。工具以本機每 Token 檔案鎖阻止同工具並行；`--exclusive-writer` 表示已確認其他機器、Dashboard 與管理工具也不會同時修改。這個旗標不是跨系統鎖。前置 GET 能攔截已發生的 drift，但沒有伺服器 compare-and-swap 保證；GET 與 PUT 之間仍可能競爭。無法確保單寫者維護窗口就不要套用，只保留計畫。PUT 超時／回讀不符時可能已寫入，不重試寫入、不自動取消限制；先重新讀取核對，再決定回復。管理憑證必須是另一條仍能使用的路徑，不依賴正被限制的目標 Token。

回復時用當前 GET 為基準重新產生反向計畫，檢查舊網段是否已不可信，再依授權執行；不盲目重送舊 snapshot 覆蓋新政策。管理工作結束後撤出／撤銷臨時管理憑證。

## 驗收與後續維護

工具回讀一致只證明設定相符；從真正的 Codex Cloud／CI consumer 用目標 Token 讀取指定 Worker，才驗證來源可用。Verify Token 不受 IP 限制。無須在正式 Worker 寫入來驗證限制；部署驗證依另行授權的 staging 場景執行。

官方 feed 會更新。已有排程需求時，先盤點既有自動化，使用平台 scheduler 每日抓取並在差異時建立新計畫；未授權自動套用就只通知有意義的變更。已授權自動套用時先跑相同基準／驗證流程，逐 Token 處理，失敗停止並保留證據。這個 skill 不會自行建立排程，也不會因 feed 更新默默擴大其他用途的 Token。
