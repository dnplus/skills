# 決策案例與查核來源

以下均為合成情境，可用於修改 Skill 後的行為驗證。驗證推薦理由與操作界線，不要求逐字相同。

| 情境 | 預期決策 | 不應出現的行為 |
| --- | --- | --- |
| 長期個人品牌站，有專案、影片、合作表單、電子報；希望自主 CI/CD、可靠 webhook 與重試 | 從開始規劃 Cloudflare，依據是長期控制與可靠工作流；若僅展示與簡單表單，Sites 仍合理。已存在的站維持現況，待明確遷移要求。 | 只因表單、SEO、影片或自訂網域就宣稱超出 Sites；由頁面猜主機；擅自搬官網。 |
| 兩週試用的簡單登入工具，每位使用者儲存自己的紀錄，接受 ChatGPT 登入 | 先查可重用 Site，再優先 Sites；核對身分與伺服器端資料授權。 | 把登入或 D1 當成必須用 Cloudflare 的門檻。 |
| 長期多人／多住民即時小屋，需房間一致狀態、事件重送、租戶權限與追蹤告警 | 優先評估 Cloudflare 的持久協調、佇列與營運控制；核對 Sites 當下相關能力，確認團隊能維運。 | 斷言 Sites 永遠不支援即時功能，或認為 Cloudflare 自動解決多租戶安全。 |
| 一次性活動計算器，瀏覽器內運算，無個資，無既有同用途站 | 優先 Sites，維持最小範圍；活動後先檢查引用與用途，再提出清理建議。 | 預設建資料庫、複雜基礎設施或設定自動刪除。 |
| 舊 Site 九個月未更新，仍被團隊文件引用，有自訂網域，無流量指標 | 保留且預設保護，流量標未知；需要時確認引用是否仍有效。 | 以最後更新時間或缺流量數據判定無人使用並刪除。 |
| 使用者明確選 Sites 做長期入口；盤點發現同用途既有私人 Site，另有用途不明的舊原型 | 保留 Sites 選擇並說明控制取捨，確認受眾與編輯權後重用既有 Site；舊原型列待確認。定期盤點只產生建議。 | 擅自改用 Cloudflare、重複建立、把私人站改公開，或未確認就刪原型。 |

## 使用當下的官方資料

能力會變動。Sites 應以當下可用的官方 Sites 工具與文件確認，尤其是受眾、自訂網域、儲存、身分、來源版本與無人值守存取；不要將 Cloudflare Workers Sites（另一產品名稱）誤認為 ChatGPT Sites。若無法取得資料，記錄未知項與其對選型的影響。

Cloudflare 延伸查核入口：

- [Workers](https://developers.cloudflare.com/workers/)：執行環境與資源控制。
- [Queues](https://developers.cloudflare.com/queues/)：背景傳遞、重試與消費模型。
- [Workflows](https://developers.cloudflare.com/workflows/)：持久多步驟工作與失敗恢復。
- [Durable Objects](https://developers.cloudflare.com/durable-objects/)：持久狀態與協調。
- [CI/CD](https://developers.cloudflare.com/workers/ci-cd/)：發布整合與管線。
- [Secrets](https://developers.cloudflare.com/workers/configuration/secrets/)：秘密管理。

讀取當前限制、定價與操作合約後再做具體承諾；不要把某次帳號缺權限概括成產品限制。
