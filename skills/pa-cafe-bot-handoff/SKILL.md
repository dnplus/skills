---
name: pa-cafe-bot-handoff
description: Use whenever one PA Cafe resident hands work to another resident or reports back on a handed-off task, so every handoff carries the same six fields. Also use when composing send kind=task body or status complete/fail result so members (who cannot read the bookshelf) still get the full brief.
license: MIT
---

# PA Cafe bot-handoff（派工交接六欄）

幕僚長派工、隊員／住民回報，同一套六欄。對應 Grok Bot 隊 skill `bot-handoff`；本包加上與小屋 `send`／`status` 的對應。

## 六欄（固定順序）

1. **任務（Task）**：這一切片一句話是什麼。
2. **完成標準（Done when）**：怎樣算過關（測試過、頁面起來、檔案在某路徑、PR 開出）。
3. **現況（Status）**：實際做了什麼——commit、路徑、連結；不要寫打算。
4. **證據（Evidence）**：怎麼知道有用（指令輸出、截圖路徑、檢查通過）。沒驗證就寫「尚無」，不要猜。
5. **阻塞（Blocked on）**：卡在哪、要誰解。沒卡就寫「nothing」。
6. **下一手（Next hand）**：下一個接手是誰；看板／狀態要不要更新。

## 規則

- 一次交接只切一片；多片就多則 handoff。
- 只有狀態負責人寫共用看板／追蹤器；執行者回報事實給幕僚長，不自己改總表。
- 要對方立刻做事 → 叫醒（priority／task）；純 FYI 不叫醒。
- 金鑰、token、密碼不准寫進交接。
- 同一件事的追問用 `parentId` 併回原任務討論串，不要每則訊息都新開卡。

## 跟小屋工具怎麼對

| 時機 | 怎麼用 |
| --- | --- |
| 幕僚長 `send kind=task` | `body` 用六欄骨架填好；可附書櫃相關摘要 |
| 隊員／住民回報 | 回覆或 `status complete`／`fail` 的 `result` 也用六欄 |
| 派給隊員（member） | 隊員讀不到書櫃 → 幕僚長搜到後**把要點貼進 body** |
| 派工前 | 先 `library_search`／`library_read`；相關內容一起附進派工單 |

## 派工 body 骨架（可直接貼）

```
1. 任務：
2. 完成標準：
3. 現況：尚無／…
4. 證據：尚無／…
5. 阻塞：nothing／…
6. 下一手：
```

## 預設技能候選

試用穩定後，屋主可把本包列入店長推薦／預設書單。住民不能自行 `library_import`；只能屋主從公開 GitHub 匯入。
