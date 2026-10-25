---
name: cloudflare-ops
description: 標準化 Cloudflare 控制平面強化、最小 API Token 權限、部署與唯讀維運；用於 agent／CI 憑證隔離、資源綁定盤查、批次 CIDR 更新、輪替、稽核與事件應變。PA Cafe 僅作範例。
---

# Cloudflare Ops

以台灣繁體中文協作。這是 Cloudflare 通用流程；依實際專案、產品與帳戶方案查證能力。使用者說的 API key 預設採 scoped API Token，不採 Global API Key。只執行已授權的範圍；「先不要改」可查核及產生指定檔案，不能套用線上變更。引用 skill 不等於授權建立 Token、發版或刪除資源。

## 選擇作業路徑

- 權限、部署、查看用 key 與日常維運：讀 [operations.md](references/operations.md)。
- 防止 runtime 入侵一路取得帳戶管理權、CI 被濫用或資料外洩：讀 [control-plane-hardening.md](references/control-plane-hardening.md)。
- 下載上千筆來源 CIDR、更新 Token 條件、建立可套用計畫：讀 [automation.md](references/automation.md)，使用隨附腳本，不逐筆操作 UI。
- 研究事件背景時讀 [zeabur-lessons.md](references/zeabur-lessons.md)；它是來源筆記，不能當成 Cloudflare 有相同漏洞的證據。
- PA Cafe 的名稱與發布路徑只在 [pacafe-example.md](references/pacafe-example.md)，其他專案從自身設定取值。

## 核心授權界線

先辨識環境、用途、執行來源與憑證消費者。唯讀巡檢、讀程式碼、讀資料、部署、改網路及帳戶管理分開授權。部署者的權力包含部署程式可取得的 bindings／runtime secrets；不是看到設定介面讀不出 secret 就沒有外洩風險。

公開 Worker、應用程式資料庫、一般快取及 agent 工作區不保存 Token provisioning／帳戶管理根憑證。需要管理 Token 時使用獨立、短期的管理身分，完成後撤出一般工作路徑。production 的寫入憑證保留在受控發布環境，除非任務明確授權其他方式。只授權指定 Worker，不自動擴大成全部 Workers、zone 或帳戶。綁定能力和產品 resource scope 的支援都需以當前官方文件及實測核對。

最小角色仍可能有高風險：唯讀資料角色可以外洩資料；Editor 可部署、改設定、管理 secrets。Git 分支名稱、OpenAI 共用出口 CIDR、私人 repo、內網位置與應用程式 WAF 都不能替代 Cloudflare 管理 API 的身分與授權。2FA 保護互動登入，不會讓被竊取的 bearer Token 每次呼叫都重新驗證 2FA。

## 唯讀盤查

先讀專案指示，記錄 Git HEAD／dirty 狀態，核對 Wrangler、建置腳本與 CI/CD，再以已授權的 Cloudflare 唯讀 API 比對實際狀態。connector 優先；先讀工具說明及 API schema。只列 secret 名稱，不擷取或回顯值。

逐環境比較帳戶、Worker、域名、routes、有效部署／SHA、build trigger、Token 參考、資料資源 ID、service bindings、登入與第三方服務端點。DO binding/class 同名不表示共用資料，以 namespace ID 判定；同名 secret 無法證明值相同或不同。

找出未宣告的線上 vars、預設 config 指向 production、routes 繼承、共用 Token、過期 consumer、過廣唯讀資料及稽核缺口。權限不足的項目記為 BLOCKED／NOT RUN，不為了消除 403 自動換成 Admin。

## 批次配置與驗證

先產生精確帳戶／資源範圍、角色、期限、來源、預期效果、差異與回復方式的計畫。依既有授權繼續套用；如超出授權，讓使用者核准具體計畫，而非再問籠統問題。API 權限 ID、resource 表示法與 wire 欄位從官方 schema／當前 GET 回應確認，不從名稱猜。

套用前重新 GET 並比對計畫基準，避免覆蓋他人修改；有 drift 就重建計畫。保留既有 policies、TTL、status 與排除網段，除非使用者授權修改它們。CIDR 清單更新用 API 單次完整 request body，不以多次覆蓋 PUT 來假裝逐批追加。若數量上限不支援，保留完整清單、標示限制，改評估固定出口，不擴大 prefix 或刪去一部分網段。

套用後重新讀取比對，並從真正使用憑證的路徑做無副作用的授權讀取。Token verify 不驗證來源 IP 限制。部署成功、應用程式 smoke、越權遭拒和產品驗收分開報告；拒絕寫入測試只用專用可拋棄資源，不在 production 嘗試可能成功的寫入。失敗不自動放寬權限。

## 交付

提供已確認事實、推論、建議與實際完成狀態。每項控制列出執行身分、API／UI／IaC 路徑、方案限制、前後差異、驗證與回復方式。公開 skill 只保存通用流程、公開來源與合成測試，不存真實 Token、帳戶 ID、家用出口、私密部署快照或完整稽核日誌。
