---
name: cloudflare-sites-selection
description: Choose between ChatGPT Sites and Cloudflare for a new app or an explicitly requested architecture review, and inventory Sites for reuse, consolidation, or retirement recommendations.
license: MIT
---

# Cloudflare / ChatGPT Sites 選型與盤點

簡單 MVP、一次性或有限範圍應用優先考慮 ChatGPT Sites；複雜、長期營運的應用從開始就評估直接使用 Cloudflare，避免需求確定後才被迫搬遷。這是預設偏好，不是平台能力的硬性界線。使用者明確指定平台時保留其選擇，說明具體取捨；未獲授權不搬站、不部署、不改現有官網。

## 選型

1. 確認用途、預期壽命、使用者與身分來源、資料與權限邊界、失敗後果、維運負責人。從已有上下文回答，只詢問會改變決策的缺口。
2. 建立前先用可用的 Sites 唯讀工具查同用途站點；符合需求且有權編輯時優先重用。無法盤點就明確標記，不宣稱沒有既有站點。不能因名稱相似而覆寫不同用途或受眾的站點。
3. 比較下表；對影響決策的未知能力核對當下工具合約、官方文件與帳號可用性。區分「已證實不支援」與「尚未確認」，不要把未列出的能力直接當成不支援。

| 決策面向 | Sites 優先的條件 | 從開始考慮 Cloudflare 的條件 |
| --- | --- | --- |
| 範圍與壽命 | 有限流程、快速驗證、一次性工具 | 長期產品、持續擴充、可預見的搬遷成本高 |
| 基礎設施控制 | 接受受管資源、部署與權限模型 | 需要自己掌握帳號、資源綁定、環境隔離與政策 |
| 背景工作與協調 | 簡單更新，現行受管流程已滿足 | 可靠佇列、重試、持久工作流、多人即時狀態協調 |
| 身分與多租戶 | ChatGPT 登入與簡單的使用者資料隔離 | 外部身分、組織／租戶權限、稽核與複雜授權模型 |
| 發布與維運 | 受管版本與發布已足夠 | 自訂 CI/CD、審核關卡、回滾、告警、追蹤與服務目標 |
| 可攜性與成本 | 接受受管資料存取與匯出方式 | 明確備份還原、資料匯出、供應商退出與成本控制需求 |

Sites 支援 Worker／Vinext 後端、ChatGPT 登入、D1、R2、Git 來源版本、自訂網域及 runtime secrets，也可串接無人值守更新。登入、資料庫、自訂網域或排程本身都不是必選 Cloudflare 的理由。Queues、Durable Objects 等在 Sites 的可用性若未說明，標「需核對現行能力」。Cloudflare 也不會自動完成身分、租戶授權或維運設計，須評估實作與營運成本。

「Sites 是子集」最多是營運控制模型的比喻，不是嚴格功能集合；直接使用 Cloudflare 不會自動重現 Sites 的 ChatGPT 身分與整合。Git 原始碼可攜也不代表登入識別、資料、資源綁定及秘密能一鍵搬走。不要依網域、框架或頁面外觀猜部署方式。

輸出簡短決策：**建議平台、需求依據、仍待核對項目、會改變選擇的門檻、既有站點重用結果**。保留「現有平台繼續用」選項；只有使用者要求遷移才提出遷移執行計畫。需要案例與來源時讀 [決策案例](references/decision-cases.md)。

## Sites 生命週期盤點

使用者要求清理、減少重複站點或定期檢查時，讀 [盤點流程](references/site-lifecycle.md)。本模式只提供建議，不自動刪除、下架或改權限。公開 repo 只能保存通用規則及合成案例，不提交私人站點清單、帳號、憑證或對話內容。
