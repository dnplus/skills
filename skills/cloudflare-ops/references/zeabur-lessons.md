# Zeabur 2026 事件：對 Cloudflare 控制平面的可用教訓

**資料範圍。** 本整理依 Zeabur 於 2026-09-07 發布的八月事件調查，以及 2026-10-19 發布、明示仍在調查中的十月初步報告。這些是 Zeabur 自述的調查結果，不是 Cloudflare 事件或 Cloudflare 控制平面的弱點證據。時間使用原報告 UTC。

## 官方報告確認了什麼

### 八月事件

Zeabur 說明，2026-08-27 的入侵從共享叢集上一個公開的 NextChat v2.16.1 服務開始。攻擊者利用該服務的 MCP 授權漏洞取得容器內程式執行，再經共享叢集內網讀取 routing cache。Cache 同時存放路由資料與舊式、無權限 scope／期限的 Legacy API Keys；攻擊者從中取得管理金鑰後，讀取內部管理服務環境變數，取得長期 AWS root key，進入 AWS 與東京共享叢集。共享叢集上的維護工作又同時擁有核心正式環境私網連線與超出工作需求的資料庫讀取憑證，使攻擊者得以讀取正式資料庫內的專案環境變數。Zeabur 確認部分帳號資料與包含第三方金鑰、資料庫密碼等環境變數遭讀取。[Zeabur 八月事件調查](https://zeabur.com/blogs/august-2026-security-incident)

### 十月事件

Zeabur 2026-10-19 初步報告表示，已知攻擊者於 10/14 至 10/15 使用明文保存在私有配置庫的內部 AWS 金鑰及集群管理令牌；令牌建立於 2024-01，沒有期限，管理介面可從公網存取。另一條路徑使用舊 GCP 金鑰讀取伺服器初始化配置中的 root 密碼。兩路在 10/15 匯合：遭入侵主機持有的內網憑證讓節點加入內網，而內網規則允許連到平台資料庫，攻擊者再以內部只讀資料庫帳號讀取平台資料。報告指出，此帳號雖是唯讀，仍可讀取所有資料；系統有些存取記錄不完整，故不能確認所有下載範圍。[Zeabur 十月事件初步報告](https://zeabur.cn/zh-CN/blogs/october-2026-security-incident)

**調查限制要保留。** 初始金鑰如何外洩仍未確認；八月 GitHub App 私鑰是否導致十月配置庫外洩是推測。部分備份、物件儲存、GCP 讀取與特定雲商操作因記錄不足而無法確認。Zeabur 明確表示，八月輪替沒有包含十月使用的明文 AWS 金鑰與集群管理令牌。這顯示輪替清單若不以完整憑證清冊和來源追蹤，可能只換到已知入口的一部分。

## 控制平面設計檢查

以下是將上述攻擊鏈映射到 Cloudflare 帳戶／Workers 管理時可執行的控制，不表示 Cloudflare 會自動提供所有隔離或具備 Zeabur 類似問題。

| 攻擊鏈暴露的控制缺口 | Cloudflare 控制平面檢查與 agent 動作 |
| --- | --- |
| 公開服務遭利用後，能探測或呼叫內部管理面 | 把公開 Worker、使用者資料處理服務與管理端點當成不同信任邊界。逐一盤點 Workers service binding、網路出口、內部 API 與管理 hostname；管理端點前加 Access／身份驗證與專用 Service Auth policy。不要將 Cloudflare 私網／Workers 網路本身視為呼叫端授權。檢查 Worker 入侵後是否可直接呼叫部署、Secrets Store、帳戶 API 或內部管理服務。 |
| Token 長期有效、缺少 scope、撤銷覆蓋不全 | 每個操作者與自動化用途分開建立 API Token；使用當前可用的資源級 scope、最小角色、期限和來源 IP 條件。建立 Token 清冊，記錄用途、consumer、資源、角色、到期、最後使用與撤銷狀態。撤銷時搜尋 CI、Workers Builds、OpenAI Cloud 和本機所有 consumer；不要只輪替最近確認外洩的那枚。 |
| 秘密與設定、快取、備份同處或明文留存 | Cloudflare 控制 Token 不得放進 Worker vars、程式碼、一般 KV/R2、部署日誌、prompt、公開 repo 或可被應用程式讀取的資料庫。Worker runtime secret 僅供其所綁 Worker 讀取；若採 Secrets Store，可利用 secret scope 限制消費服務、以部署者角色控制綁定，並確認其 Read 只讀 metadata、不讀 secret 值。查核備份與 log 是否包含秘密；輪替後確認舊值不再被備份或復原流程重新帶回。 |
| 唯讀帳號可讀過多資料 | 分開 Metadata Read-Only、Content Read-Only 與資料資源的唯讀角色。Metadata 適合看設定、指標與 logs；Content 可看 Worker 程式碼或資料內容，擴大暴露面。為 R2、D1 等按實際支援 scope 給特定資源唯讀權限，不將 account-wide read 當安全預設。 |
| 服務身分與資源 scope 過廣 | 盤點 Workers Editor 可部署到哪些 Worker、哪些資源可直接操作、綁定會讓程式存取哪些資料。部署 Worker 通常不需要額外的直接 R2／KV／D1 權限，但新程式會取得該 Worker bindings 所代表的 runtime 能力；因此 staging bindings 必須指向 staging 資料，並限制不可信 Worker 的 outbound access。 |
| 內網 ACL 只驗節點或網段，未驗用途 | 對 Access service token 指定單一應用程式與 Service Auth policy；確認 strict service-token authentication，拒絕時回 401/403，並定期輪替／停用閒置 Token。來源 IP 白名單只辨識網路出口，不代替 Token、resource scope 或 API 授權。 |
| 長時間未偵測、日誌缺漏 | 啟用並保留 Cloudflare Audit Logs，集中備份日誌；告警新建／擴大 Token、權限變動、路由／DNS 變更、Secrets Store 變更、部署、Access policy 變更與大量資料讀取。將 actor、auth method、source IP、API／dashboard、resource、operation、result、時間和部署版本關聯。驗證查詢權限與實際 retention，不以目前 API 讀得到當成長期完整保存。 |

Cloudflare Workers 目前提供 Workers 角色與個別 Worker scope。官方定義 Metadata Read-Only 可看 metadata、settings 與 observability，但不能讀取 script source 或 secret values；Content Read-Only 可看程式碼；Editor 可更新、部署、改設定及管理 secrets。Routes／Custom Domains 變更還需 zone 層級 Workers Routes Write。這些是不同操作，不能把一個泛稱的 read key 當成通用最小權限。[Workers roles and permissions](https://developers.cloudflare.com/workers/authorization/workers/)

Cloudflare Secrets Store 另有 secret resource scope 與角色檢查；API Token 的 Secrets Store Read 只讀 metadata，不讀取 secret value。注意把 Secrets Store secret 綁到 Worker 仍是寫入操作，部署者可能需要 Edit；這需要在最小權限設計中單獨評估。[Secrets Store access control](https://developers.cloudflare.com/secrets-store/access-control/) · [Manage account secrets](https://developers.cloudflare.com/secrets-store/manage-secrets/)

Cloudflare Audit Logs v2 說明帳戶層級的使用者操作會被記錄，包含 API 與 dashboard，保留 18 個月；需要更長期保存時 Enterprise 可用 Logpush。agent 應檢查帳戶實際可見的事件種類、token 權限與輸出完整性，並把紀錄匯到不與管理憑證共用的地方。[Audit Logs v2](https://developers.cloudflare.com/fundamentals/account/account-security/audit-logs/)

## CIDR 大清單的操作方式

不要手動把一千多筆 IP 複製到每枚 Token，也不要為了好貼而合併成更大的涵蓋範圍。先確認是哪個網路路徑真正呼叫 Cloudflare API：OpenAI Cloud、Workers Builds 與使用者 Mac 是不同 caller。從官方當前 feed 生成檔案，保存 feed 的建立時間與 hash，驗證 CIDR 及數量，輸出逗號格式並自動檢查更新。部署憑證留在 Workers Builds，唯讀／Codex 操作憑證才限制到 Codex Cloud；若平台 UI/API 對 CIDR 數量或更新方式不適合，優先採用固定受控 NAT／egress 或只在受控 relay 執行，而非擴大為 ISP 大網段。

OpenAI 官方 IP egress 文件提供 Codex Cloud 專用 feed，並提醒 ranges 可能改變，應定期取回及更新。Cloudflare API Token 的 IP 過濾可使用 CIDR，但每個 Token 還需自己的 permission policies；官方指出 Verify Token endpoint 不受 IP 範圍過濾。[OpenAI IP egress ranges](https://developers.openai.com/api/docs/guides/ip-addresses) · [Cloudflare token restrictions](https://developers.cloudflare.com/fundamentals/api/how-to/restrict-tokens/)

## Agent 快速執行規則

1. **盤查先行：** 輸出資源、Token、部署、bindings、secret 名稱、CIDR caller、audit coverage 清單；所有 secret 值一律不回顯。
2. **按用途建權限提案：** 查看 metadata、讀程式碼、直接讀資料、部署、改網路／route、帳戶管理分開列；超出當前工作需要的角色不加入。
3. **批次處理 CIDR：** 取官方 feed，保留原始檔與雜湊，程式驗證 IP 版本、CIDR、重複項與額外網段；先產生可檢視計畫，再依授權使用 API 批次套用；不為方便擴大 prefix。
4. **先驗 staging：** 使用獨立 Token 和 staging Worker／資料；記錄允許操作及預期遭拒操作。不可在 production 用可能成功的寫入來測試拒絕。
5. **維運可回溯：** 每次改動記錄操作者、目的、精確 scope、來源 IP、時間、部署 commit/version、前後差異、驗證結果及回復方法；輪替後追蹤每個 consumer，確認舊憑證失效與備份／日誌處理結果。
6. **保持證據界線：** 區分 repo 預期設定、線上 API 當前設定、成功的實際部署、存取日誌與產品驗收。未能讀取或缺少保留期證據，明列 BLOCKED／NOT RUN，不宣稱已完成強化。
