[![Review Assignment Due Date](https://classroom.github.com/assets/deadline-readme-button-22041afd0340ce965d47ae6ef1cefeee28c7c493a6346c4f15d667ab976d596c.svg)](https://classroom.github.com/a/mhxNhwtV)
# Build-Your-Personal-RAG

### HW3 Phase 1

#### multi-turn 對話
節錄自測試用對話:
```
🧑 User: 我剛剛問了哪些問題?請幫我總結方便讓我後續整理

[*] Embedding query & Searching...

[*] Retrieved Context Sources:
  1. [Source: openbmc-docs\code-of-conduct.md, Chunk: 5] (Score: 0.0164)
  2. [Source: openbmc-docs\process\subproject-maintainership.md, Chunk: 3] (Score: 0.0161)
  3. [Source: openbmc-docs\anti-patterns.md, Chunk: 1] (Score: 0.0159)

[*] Generating Answer...

============================================================
🤖 Assistant:
好的，我來幫您總結一下您剛才問的問題，以及這些問題所包含的重點：

1.  **第一個問題：想學習關於 GPIO 的韌體設計，想了解 Device Tree，能不能說明？**
    *   **重點**：詢問 OpenBMC 中 GPIO 的韌體設計原理和 Device Tree 的作用。
    *   **回答概述**：
        *   解釋了 OpenBMC 中 `phosphor-gpio-monitor` 服務如何監控 GPIO。
        *   說明了 GPIO 相關配置參數（`DEVPATH`, `KEY`, `POLARITY`, `TARGET` 等）。
        *   提到了 Device Tree 在 OpenBMC 中描述硬體的作用。
        *   基於通用嵌入式 Linux 知識，推測了 GPIO 在 Device Tree 中的描述方式（GPIO 控制器、引腳定義、`gpio-keys` 節點）。

2.  **第二個問題：作為一個研究生，正在準備 implement GPIO in OpenBMC 的專案，是不是需要購買一塊開發板？**
    *   **重點**：詢問 OpenBMC GPIO 專案是否需要購買實際開發板，以及原因。
    *   **回答概述**：
        *   強烈建議購買支援 OpenBMC 的開發板。
        *   解釋了原因：真實硬體互動、驗證 Device Tree 配置、測試 `phosphor-gpio-monitor`、除錯與診斷、完整的 OpenBMC 體驗、實際專案交付物。
        *   推薦了幾種開發板，如 Google Zaius/Witherspoon (參考平台)、ASRock Rack D4BMC (易取得)。
        *   給出了選擇開發板的考量因素。

3.  **第三個問題：我知道 STM32 有出各種開發板，也能用來 implement OpenBMC repo. 嗎？**
    *   **重點**：詢問 STM32 開發板是否可以直接用於運行或實現 OpenBMC。
    *   **回答概述**：
        *   明確指出 STM32 大多數情況下**不能直接運行完整的 OpenBMC 韌體堆疊**。
        *   解釋了原因：硬體架構差異 (MCU vs. MPU)、作業系統和軟體堆疊差異、專用 BMC 功能的缺乏。
        *   提出了 STM32 在 OpenBMC 專案中可能的角色：作為「智能周邊控制器 (Satellite Controller)」，處理實時控制、低階感測器介面、擴展 GPIO/I2C/SPI 等任務。
        *   說明了 STM32 與主 BMC 協同工作的方式 (通訊介面、軟體設計、Device Tree)。
        *   再次強調，如果專案重心是 OpenBMC 本身，仍需購買專用 OpenBMC 開發板。

### 總結您的學習主線：

您的問題系列形成了一條清晰的學習路徑，從理論概念 (GPIO 韌體設計, Device Tree) 到實踐工具 (開發板選擇, STM32 角色的辨析)：

*   **理解 OpenBMC GPIO 的理論和配置：** 了解其軟體架構 (如 `phosphor-gpio-monitor`) 和硬體描述方式 (Device Tree)。
*   **規劃 OpenBMC GPIO 專案的硬體環境：** 判斷是否需要實體開發板，以及選擇哪種類型的開發板。
*   **辨析不同硬體平台的適用性：** 區分主控級 BMC 晶片與外圍 MCU (如 STM32) 的角色和限制。

這些問題和答案為您的 OpenBMC GPIO 專案奠定了很好的基礎。祝您專案順利！
```


```python
# 1. 確認 Python 版本
python3 --version        # 需顯示 >= 3.10.x

# 2. 建立並啟動虛擬環境
python3 -m venv .venv
source .venv/bin/activate

# 3. 安裝套件
pip install -r requirements.txt

# 4. 設定環境變數
cp .env.example .env
# 請將 .env 中的 LITELLM_API_KEY 和 LITELLM_BASE_URL 填入助教提供的值

# 5. 啟動 Vector DB（使用 pgvector）
docker compose up -d
docker compose ps        # 確認 pgvector 狀態為 running

# 6. 全量重建索引
python data_update.py --rebuild

# 7. 測試 RAG 問答
python rag_query.py --query "請問這個知識庫的核心主題是什麼？"

~# 8. 生成 Skill 文件~
~python skill_builder.py --output skill.md~
```




### 實作過程遇到的問題

**Q：執行 `data_update.py` 時遇到 `psycopg2.errors.UndefinedColumn: column "fts_vector" does not exist` 怎麼辦？**
A：這通常發生在舊版資料庫 Schema 殘留的情況下（例如之前執行過舊版程式，資料表已建立，但缺少新欄位）。
**解法一（推薦，徹底重置環境）：**
請銷毀當前的 Docker 容器與掛載的 Volume 資料，然後重新啟動：
```bash
# 停止容器並刪除掛載的 Volume (清除所有舊資料與 Schema)
docker compose down -v

# 重新啟動乾淨的資料庫
docker compose up -d

# 重新執行全量建置
python data_update.py --rebuild
```

> `psycopg2` 是 Python 與 PostgreSQL 資料庫之間溝通的套件。為了達到最高的執行效率，它的核心部分直接使用 C 語言編寫，以調用 PostgreSQL 的底層 C API (libpq)。使用預先編譯好的版本`psycopg2-binary`可以減少需要額外編譯或是額外設定路徑等流程。