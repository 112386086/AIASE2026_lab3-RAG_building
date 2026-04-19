[![Review Assignment Due Date](https://classroom.github.com/assets/deadline-readme-button-22041afd0340ce965d47ae6ef1cefeee28c7c493a6346c4f15d667ab976d596c.svg)](https://classroom.github.com/a/mhxNhwtV)
# Build-Your-Personal-RAG

### HW3 Phase 1

#### multi-turn 對話
節錄自測試用對話:
```
🧑 User: 總結我們剛剛的對話

[*] Embedding query & Searching...

[*] Retrieved Context Sources:
  1. [Source: openbmc-docs/tof/contract.md, Chunk: 2] (Score: 0.0164)
  2. [Source: openbmc-docs/code-of-conduct.md, Chunk: 5] (Score: 0.0161)
  3. [Source: openbmc-docs/security/obmc-security-response-team-guidelines.md, Chunk: 2] (Score: 0.0159)
  4. [Source: openbmc-docs/cpp-style-and-conventions.md, Chunk: 1] (Score: 0.0156)
  5. [Source: openbmc-docs/CONTRIBUTING.md, Chunk: 4] (Score: 0.0154)
  6. [Source: phosphor-dbus-interfaces/yaml/xyz/openbmc_project/Control/Host.interface.yaml, Chunk: 1] (Score: 0.0152)
  7. [Source: openbmc-docs/designs/mctp/mctp-kernel.md, Chunk: 7] (Score: 0.0149)
  8. [Source: openbmc-docs/architecture/redfish-logging-in-bmcweb.md, Chunk: 1] (Score: 0.0147)
  9. [Source: openbmc-docs/process/subproject-maintainership.md, Chunk: 4] (Score: 0.0145)
  10. [Source: openbmc-docs/designs/bmc-service-failure-debug-and-recovery.md, Chunk: 10] (Score: 0.0143)
  11. [Source: openbmc-docs/cpp-style-and-conventions.md, Chunk: 4] (Score: 0.0141)
  12. [Source: openbmc-docs/designs/redfish-eventservice.md, Chunk: 17] (Score: 0.0139)
  13. [Source: openbmc-docs/process/subproject-maintainership.md, Chunk: 7] (Score: 0.0137)
  14. [Source: openbmc-docs/code-of-conduct.md, Chunk: 2] (Score: 0.0135)
  15. [Source: openbmc-docs/designs/uart-mux-support.md, Chunk: 9] (Score: 0.0133)
  16. [Source: openbmc-docs/designs/mctp/mctp-kernel.md, Chunk: 10] (Score: 0.0132)
  17. [Source: openbmc-docs/testing/local-ci-build.md, Chunk: 2] (Score: 0.0130)
  18. [Source: openbmc-docs/process/subproject-maintainership.md, Chunk: 3] (Score: 0.0128)
  19. [Source: openbmc-docs/development/dev-environment.md, Chunk: 4] (Score: 0.0127)
  20. [Source: openbmc-docs/designs/ncsi-coredump.md, Chunk: 1] (Score: 0.0125)

[*] Generating Answer...

============================================================
🤖 Assistant:
好的，我們來總結一下這次對話的主要內容：

**專案概述：**
你是一位研究生，正在準備一個在 OpenBMC 中實作 GPIO 的專案。

**核心問題與解答：**

1.  **是否需要立即購買開發板？**
    *   **不需要。** 你可以先在軟體模擬器 QEMU 中進行大部分的開發和測試。
    *   只有當你需要驗證 GPIO 引腳的實際硬體操作、驅動程式行為以及與物理設備的互動時，才需要考慮購買開發板。

2.  **QEMU 模擬器是什麼？**
    *   QEMU 是一個**軟體模擬器**，它允許你在沒有實際硬體的情況下，運行一個虛擬的 OpenBMC 系統。
    *   它是 OpenBMC 開發環境的核心，提供了編譯、運行和測試你程式碼的平台，並可透過網路介面（如 SSH）與虛擬 BMC 互動。

3.  **如何在 QEMU 中使用 `devtool` 建構和測試變更？**
    *   **設定環境：** 確保已完成開發環境設定，並在 BitBake 環境中執行過 `. setup`。
    *   **提取原始碼：** 使用 `devtool modify <repository_name>` 將目標 repository 的原始碼提取到你的本地工作區。
    *   **修改程式碼：** 在 `workspace/sources/<repository_name>/` 目錄中進行你的 GPIO 相關程式碼修改。
    *   **單獨建構：** 使用 `bitbake <repository_name>` 只重新建構你修改的元件。
    *   **設定 QEMU 檔案系統：** 登入 QEMU 後，設定 overlay 檔案系統，以便你能將新編譯的二進位檔寫入 `/usr/bin`。
    *   **部署到 QEMU：** 使用 `scp` 將你編譯的二進位檔複製到 QEMU 實例中。
    *   **驗證：** 在 QEMU 中運行你的應用程式，並透過日誌或直接執行來驗證你的變更。

4.  **Device Tree GPIO 命名設計文件與開發：**
    *   **文件存在：** 你手邊實際上**有**這份關鍵文件：`openbmc-docs/designs/device-tree-gpio-naming.md`。
    *   **開發方向：** 依據這份文件來指導你的專案開發。

5.  **Modern GPIO Interface (現代 GPIO 介面) 的說明：**
    *   **淘汰 `sysfs`：** Linux 核心已棄用傳統的 `sysfs` 介面來操作 GPIO，因為其限制較多。
    *   **基於描述符的字元設備介面 (Descriptor-based Character Device Interface)：** 這是新的、底層的核心介面，透過檔案描述符來操作 GPIO 線路，提供更精確、原子性的控制。
    *   **`libgpiod` 函式庫：** 這是一套 C/C++ 函式庫和工具，為上述新的字元設備介面提供了高階抽象，讓開發者更容易使用 API 來讀取、寫入、監聽 GPIO 事件等。**你的專案應該基於 `libgpiod` 進行開發。**
    *   **Device Tree 整合：** `libgpiod` 允許你透過在 Device Tree (`.dts` 或 `.dtsi` 檔案) 中為 GPIO 線路定義的名稱 (`gpio-line-names`) 來存取它們，這提供了更好的**可讀性和可移植性**，避免了硬編碼 GPIO 號碼。
    *   **GPIO Hogs：** Device Tree 也支持 GPIO hogging 機制，允許在核心啟動時自動配置 GPIO 到特定狀態。
    *   **OpenBMC 實例：** `phosphor-gpio-monitor` 等服務就是利用 `LineName` 在其配置檔案中定義和監控 GPIO 的良好範例。

**總結開發流程建議：**

1.  **從 QEMU 入門：** 先在 QEMU 中設定開發環境，熟悉 OpenBMC 的工具鏈（Yocto, BitBake, `devtool`）。
2.  **核心邏輯開發：** 使用 `libgpiod` 在 C/C++ 中編寫你的 GPIO 應用程式，並在 QEMU 中進行功能測試。
3.  **參考命名慣例：** 仔細閱讀 `openbmc-docs/designs/device-tree-gpio-naming.md`，並在你的程式碼中遵循其定義的 `gpio-line-names` 慣例。
4.  **硬體驗證（後續階段）：** 當軟體邏輯完善後，再引入實際的開發板進行最終的硬體集成和驗證。

這次對話為你的 OpenBMC GPIO 專案提供了明確的起步指南、必要的工具使用方法，以及關於現代 GPIO 介面的重要概念。
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