---
title: 'Software Design Document (SDD): OpenBMC RAG Knowledge System'

---

# Software Design Document (SDD): OpenBMC RAG Knowledge System

## 1. 專案概覽 (Project Overview)
*   **系統名稱：** OpenBMC RAG 開發助手 (OpenBMC RAG Knowledge System)
*   **版本：** v3.0
*   **Elevator Pitch：** 實踐「資料即規格」理念，針對 OpenBMC 韌體架構打造自動化的 RAG 知識檢索系統。透過高度解耦的 Data Pipeline 將複雜的 D-Bus YAML 規格與 Markdown 文件轉化為 LLM 可理解的語意向量，最終將知識濃縮為 Agent 可直接呼叫的 Skill 模組，大幅降低開發者的學習曲線。
*   **目標使用者：** 進行 OpenBMC 相關 Side Project 的開發者、韌體工程師。
*   **核心技術堆疊：**
    *   **Vector DB:** `pgvector` (PostgreSQL)
        *   use docker-compose.yml to construct env and use docker-compose up -d to execute yaml file.
    *   **Embedding Model:** `sentence-transformers` (`paraphrase-multilingual-MiniLM-L12-v2`)
    *   **LLM Gateway:** `LiteLLM` (support`gpt-oss:20b`,`gemma4` and `gemini-2.5-flash`)
   

## 2. 系統架構與資料管線 (System Architecture & Data Pipeline)
嚴格確保資料收集、清理、向量化與檢索的獨立性與冪等性（Idempotency）。
### Directory Tree

```text
AIASE2026-HW3/
├── data/
│   ├── raw/     *collect_data.sh 的輸出目標*
│   │   ├── openbmc-docs/                
│   │   ├── phosphor-dbus-interfaces/   
│   │   ├── bmcweb/                      
│   │   └── supplementary/     *外部補充資料*
│   │       └── ibm_power10_openbmc.md   指令文件
│   └── processed/          *DocumentCleaner 的輸出目標*
│       ├── openbmc-docs/   *結構與 raw 完全對應*
│       │   └── ... (皆為 .txt)
│       └── ...
├── collect_data.sh
├── data_update.py
├── rag_query.py
├── skill_builder.py
└── skill.md

```

### Flowchart
```mermaid
graph TD
    %% 1. Data Collection Layer
    subgraph "Data Collection Layer"
        A1[Git Repos\nSparse Checkout] -->|collect_data.sh| A[data/raw/]
        A2[Web Scraping\ncurl + pandoc] -->|collect_data.sh| A
    end

    %% 2. ETL Pipeline Layer (data_update.py)
    subgraph "ETL Pipeline (data_update.py)"
        A -->|Idempotent Upsert| B1{DocumentCleaner}
        B1 -->|Markdown / Text| B2[Standard Clean]
        B1 -->|YAML / JSON5| B3[AST Semantic Flattening]
        B1 -->|DTS| B4[Device Tree Header]
        
        B2 & B3 & B4 --> C[data/processed/]
        
        C --> D{Context-Enriched\nChunking}
        note1[Inject Source Path\nDynamic Token Budget] -.-> D
        
        D --> E[sentence-transformers\nMiniLM-L12]
    end

    %% 3. Storage Layer
    subgraph "Vector Database (pgvector)"
        E -->|384-dim Vector| F[(chunks table)]
        D -->|Raw Text| F
        F -.->|HNSW Index| F1[Dense Retrieval]
        F -.->|GIN Index| F2[Sparse Retrieval\ntsvector]
    end

    %% 4. Retrieval & Application Layer
    subgraph "Application Layer"
        F1 & F2 -->|Reciprocal Rank Fusion\nRRF SQL| G[rag_query.py]
        
        G <-->|Prompt Assembly\nSliding Window Memory| H[LiteLLM Gateway]
        H -.->|Model Routing| H1(gemma4 / gemini)
        
        G -->|Map: Global Queries| I[skill_builder.py]
        I <-->|Reduce: Synthesis Prompt| H
    end

    %% 5. Output
    I -->|Markdown Generation| J[skill.md]

    %% Styling
    classDef db fill:#dbeafe,stroke:#3b82f6,stroke-width:2px;
    classDef script fill:#fef3c7,stroke:#eab308,stroke-width:2px;
    classDef output fill:#dcfce7,stroke:#22c55e,stroke-width:2px;
    
    class F db;
    class A,C,J output;
    class B1,D,G,I script;
```

## 3. 資料收集策略 (Data Collection Strategy)
為確保知識庫的資訊密度（Information Density）並避免引入無關的原始碼雜訊，本系統採用 Sparse Checkout 策略，精準提取 OpenBMC 核心知識域：
1.  **架構與 API 文件 (`.md`)：** 提取自 `openbmc/docs` 與 `openbmc/bmcweb`，涵蓋系統高階設計與 RESTful API 規範。
2.  **D-Bus 介面規格 (`.yaml`)：** 提取自 `phosphor-dbus-interfaces`，定義進程間通訊（IPC）的合約與屬性。
    > phosphor-dbus-interfaces 的 YAML 檔案分佈在深層目錄（yaml/xyz/openbmc_project/...），sparse-checkout 路徑要設為 yaml/ 而非根目錄
3.  **IBM Power10 OpenBMC 文件:** 提取自 [Link](https://www.ibm.com/docs/zh-tw/power10/7063-CR2?topic=tool-basic-commands-functionality-openbmc#task_a2l_nw2_sdb__title__1)，
    由於是 Web HTML，無法用 git clone。因此在 collect_data.sh 中加入一段 Web Scraping 腳本，利用 curl 抓取並透過工具 pandoc 轉成 Markdown，存入data/raw/supplementary/

> Post-condition:
> - 不存在 `.git/` 子目錄（避免雜訊進入 processed）
> - `data/raw/` 下總檔案數 ≥ 20


### 3.1 Data Lineage & Versioning
韌體規格與 API 隨版本變動頻繁，為確保 RAG 回答的準確性與可溯源性：
*   **來源標記 (Source Metadata)：** 每個 Chunk 寫入 Vector DB 時，`source` 欄位必須保留相對路徑（如 `phosphor-dbus-interfaces/yaml/xyz/openbmc_project/State/Host.interface.yaml`），讓 LLM 回答時能精準指出是哪個 D-Bus 介面。
*   **自動化收集腳本：** 透過 `collect_data.sh` 封裝 `git sparse-checkout`，確保每次拉取的原始資料不包含 `.git` 雜訊，且能隨時對齊 OpenBMC upstream 的最新 commit。

### 3.2 `collect_data.sh` 執行規格
#### Pre-conditions（執行前環境要求）
`collect_data.sh` 為 Shell 腳本，依賴以下**系統工具**（非 Python 套件）：

| 工具 | 最低版本 | 用途 | 安裝指令（Ubuntu） |
|---|---|---|---|
| `git` | >= 2.25 | sparse-checkout 支援 | `sudo apt install git` |
| `curl` | 任意 | IBM 文件抓取 | `sudo apt install curl` |
| `pandoc` | 任意 | HTML → Markdown 轉換 | `sudo apt install pandoc` |

#### 執行步驟（Ordered）

1. **Git Repos（Sparse Checkout 策略）**
   為確保知識庫專注於 OpenBMC 韌體設計，排除無關的原始碼實作細節，本系統針對不同架構層級的 Repository 制定了精確的 Sparse Checkout 規則。

   **【Common Execution Policy】**
   *   **獲取策略:** 統一採用 `git clone --depth 1 --filter=blob:none --sparse` 搭配 `git sparse-checkout init --no-cone`，以支援精確到單一檔案的提取。
   *   **輸出路徑:** 統一輸出至 `data/raw/<repo_name>/`。
   *   **環境清理:** 執行完畢後，強制刪除 `.git/` 子目錄（`rm -rf data/raw/<repo_name>/.git`），避免 Git metadata 污染後續的 Data Pipeline。

   **【目標 Repositories 與格式對應】**

   | 架構層級 | 目標 Repo | 提取路徑 (Sparse Paths) | 檔案格式 | 對應的 Chunking / 清理策略 |
   | :--- | :--- | :--- | :--- | :--- |
   | **高階架構與 API** | `openbmc/docs`<br>`openbmc/bmcweb` | `/` (docs 全文)<br>`docs/`, `README.md` | `.md`, `.txt` | **Markdown-Aware Chunking:** 保留 Code fences 與表格結構。 |
   | **IPC 通訊合約** | `openbmc/phosphor-dbus-interfaces` | `yaml/`, `README.md` | `.yaml`, `.md` | **Semantic Flattening:** 透過 PyYAML 解析 AST，轉為自然語言描述。 |
   | **動態硬體配置** | `openbmc/entity-manager` | `configurations/`, `docs/` | `.json`, `.md` | **JSON AST Flattening:** 展平 JSON 鍵值對，提取 GPIO/I2C/Sensor 映射關係。 |
   | **底層硬體與 OS** | `openbmc/linux` | `arch/arm/boot/dts/aspeed/`<br>`Documentation/devicetree/bindings/gpio/` | `.dts`, `.dtsi`, `.txt` | **Context-Enriched Chunking:** 視為程式碼區塊，強制注入檔案路徑作為 Context Prefix。<br>*(⚠️ 警告: Linux repo 極大，嚴格依賴 Sparse Checkout)* |
   | **硬體事件監控** | `openbmc/phosphor-gpio-monitor` | `README.md` | `.md`, `.json` | 依據副檔名套用 Markdown 或 JSON 處理策略。 |

2. **Web Scraping（IBM Power10 文件）**
   - 執行：`curl -L <URL> | pandoc -f html -t markdown -o data/raw/supplementary/ibm_power10_openbmc.md`
   - Fallback：若 `curl` 或 `pandoc` 失敗，印出 Warning 並繼續，不中斷腳本。

3. **冪等性保證**
   - 若目標目錄已存在且非空，則 skip（`[ -d "data/raw/openbmc-docs" ] && echo "skip"`）。
   - 提供 `--force` 旗標可強制清空 `data/raw/` 並重新拉取。

## 4. Data Preprocessing & Canonicalization
原始資料格式（特別是 YAML）包含大量結構性雜訊，會嚴重干擾 Embedding 模型的語意空間映射。為此，我們在 `DocumentCleaner` 模組中實作了專屬的正規化策略。

### 4.1 DocumentCleaner I/O 契約 (Producer-Consumer Contract)
為確保資料管線的解耦與冪等性，系統定義了嚴格的檔案 I/O 契約：
*   **輸入 (Producer)：** `collect_data.sh` 負責將多源資料（Git Repo, Web HTML）統一收集至 `data/raw/`。
*   **處理 (Processor)：** `DocumentCleaner` 負責抹平格式差異（移除 HTML 標籤、展開 YAML 語意），提取純文字。
*   **輸出 (Consumer)：** 清理後的文本必須寫入 `data/processed/`，且**嚴格保持與 raw 目錄相同的相對路徑**，副檔名統一轉換為 `.txt`。此設計確保了發生錯誤時可快速定位原始檔案。

### 4.2 D-Bus YAML 語意展平 (Semantic Flattening)
*   **設計挑戰：** D-Bus YAML 具有嚴格的階層結構（Interfaces $\rightarrow$ Methods/Properties/Signals）。傳統基於 Regex 的清理方式會破壞階層關係，導致 LLM 無法辨識特定屬性隸屬於哪個介面。
*   **實作策略：** 引入 `PyYAML` 套件，使用 parser將 YAML 解析為抽象語法樹（AST / Python Dictionary），並透過樣板化描述（Template-based Canonicalization）將其轉換為自然語言。
*   **轉換範例：**
    *   *原始 YAML 結構：* 某 Interface 包含 `CurrentHostState` Property。
    *   *正規化輸出：* `"The D-Bus interface '[Name]' is defined as follows: [Description]. It contains a property named 'CurrentHostState' of type 'string'. Description: [Property Description]."`
*   **效益：** 確保結構化資料完美對齊 LLM 的預訓練語意空間，大幅提升檢索（Retrieval）的精準度。

### 4.3 JSON 設定檔寬鬆解析與展平 (JSON5 Lenient Parsing & Flattening)
*   **設計挑戰：** OpenBMC 的 `entity-manager` 大量使用 JSON 定義底層硬體配置（如 GPIO、Sensor 映射）。由於 OpenBMC 底層採用 C++ 開發，其使用的 JSON 解析器（如 `nlohmann/json`）允許寬鬆的語法，導致官方設定檔中充斥著 **C 語言風格註解 (`//`, `/* */`)**、**結尾逗號 (Trailing Commas)** 與單引號。Python 內建的標準 `json` 函式庫嚴格遵守 RFC 8259，遇到此類檔案會直接拋出 `JSONDecodeError` 導致管線中斷。
*   **實作策略：** 捨棄 Python 內建的 `json`，全面導入支援 JSON5 標準的解析器（`json5` 套件）。JSON5 作為 JSON 的超集，能完美兼容 OpenBMC C++ 解析器的寬鬆特性。解析為 AST 後，套用與 YAML 相同的遞迴展平邏輯。
*   **轉換範例：**
    *   *原始 JSON 結構：* 
        ```json
        {
            // ADC Sensor for 12V
            "Name": "P12V",
            "Type": "ADC",
        }
        ```
    *   *正規化輸出：* 
        ```text
        Hardware Configuration (Entity Manager) for '.../catalina_adc.json':
          - Name: P12V
          - Type: ADC
        ```

### 4.4 Markdown Structure Retention
傳統的清理方式會將 Markdown 轉為純文字，但對於 OpenBMC 文件，程式碼與表格是核心知識：
*   **保留 Code Fences：** 不移除 ` ```cpp ` 或 ` ```bash ` 等圍欄符號。LLM 對 Markdown 語法有極高的理解力，保留圍欄能讓 LLM 明確區分「自然語言描述」與「程式碼實作」。
*   **表格線性化 (Table Linearization)：** 若遇到 Markdown 表格，盡量保持 `|` 分隔符，或將其轉換為 `Key: Value` 形式，避免 Chunking 時表格被從中截斷導致欄位錯位。

### 4.5 Error Handling & Fallback
若 YAML/JSON5 檔案格式嚴重損毀或為空，`DocumentCleaner` 應記錄 Warning Log 並安全跳過 (Skip)，退化為保留原始純文字 (`return text.strip()`)，不可導致整個 Data Pipeline Crash。

#### DocumentCleaner 模組介面契約

#### 輸入規格
- 掃描目錄：`data/raw/`（遞迴）
- 支援副檔名：`.md`,`.yaml`, `.yml`,`.txt`, `.json`, `.dts`（其他格式 skip + warn）
- 檔案編碼：UTF-8（非 UTF-8 以 `errors='replace'` 容錯）

#### 輸出規格
- 輸出目錄：`data/processed/`
- 命名規則：**嚴格鏡像 (Strict Mirror) 原始目錄結構**，僅將副檔名替換為 `.txt`。
  - 範例：`data/raw/yaml/xyz/Host.interface.yaml`
         → `data/processed/yaml/xyz/Host.interface.txt`
- 輸出格式：純 UTF-8 文字，保留 Markdown fences。
- 設計考量：OpenBMC 的 D-Bus 規格目錄極深，採用鏡像結構可避免作業系統單一檔名長度限制 (255 chars)，並完美保持 Data Lineage 的直覺性。

#### 冪等性保證
- 若 `processed/` 已存在且 hash 未變動，則 skip（不重寫）
- `--rebuild` 旗標：清空 `data/processed/` 後全量重跑

## 5. Context-Enriched Chunking

### 5.1 Context Chunking
為避免破壞技術文件的上下文完整性，本系統揚棄單純的固定長度切分，改採 **Markdown-Aware Chunking** 混合策略：
*  **結構優先切分：** 優先依據 Markdown 的標題階層（`#`, `##`）與段落邊界（`\n\n`）進行切分，確保表格與程式碼區塊不被從中截斷。
*  **長度限制與重疊 (Overlap)：** 當單一語意區塊超過 Token 限制時，才啟動字元級強制切分。設定 $C_{size} = 512$, $C_{overlap} = 64$，透過保留尾部重疊來防止跨 Chunk 的上下文遺忘（Catastrophic Forgetting）。
*  **無意義短文本過濾：** 清理後若文本長度小於 30 字元（例如只有標題沒有內容的佔位文件），則直接丟棄，避免污染 Vector DB 的語意空間。
*  Chunker 邊界條件與特殊規則:
    | 情境 | 處理規則 |
    |---|---|
    | Code fence 跨越 chunk 邊界 | 整個 code block 視為不可分割單元，若超過 C_size 則獨立成一個 chunk |
    | YAML 展平後的單一介面描述 | 視為原子單元，不做跨介面合併 |
    | 表格超過 C_size | 優先在行邊界切分，不在 `\|` 中間截斷 |
    | 單一 chunk 的 token 計算方式 | 以字元數 / 4 估算（避免引入 tokenizer 依賴） |

> **Dynamic Token Reservatio:** Chunker 在切分時，不以裸文本長度直接對照 `C_size`，而是先計算即將注入的 Context Prefix 長度
（例如 `[Context: <source> | <section>]`），再以`effective_chunk_budget = C_size - len(context_prefix)`作為該 chunk 可承載的正文長度上限。
若 `effective_chunk_budget <= 0`，則應記錄 Warning，並退化為只保留最關鍵的 Context 欄位（例如 `source`）。

### 5.2 Context Enrichment
為解決傳統 Chunking 導致的 Semantic Fragmentation（例如 Chunk 內僅包含 "Returns the current state"，導致 Embedding 模型無法辨識其隸屬哪個模組），本系統導入 Contextual Retrieval 概念：
*   **Metadata Injection:** 在執行 Embedding 之前，系統會強制將文件的來源路徑與全局上下文（如 D-Bus 介面名稱或 Markdown H1 標題）前綴於 Chunk 內容之上。
*   **格式範例:** `[Context: bmcweb/README.md] \n\n {Original_Chunk_Text}`
*   **效益:** 確保每一個獨立的 Chunk 在高維度語意空間中，都能緊緊錨定 (Anchor) 在其所屬的 OpenBMC 子系統領域

### 5.3 Vector Index Selection

本系統預設採用 **HNSW (Hierarchical Navigable Small World)** 作為 `pgvector` 的向量索引演算法。

**HNSW 參數設定：**

| 參數 | 設定值 | 說明 |
|---|---|---|
| `m` | `16` | 每層最大連接數 |
| `ef_construction` | `64` | 建索引時的 candidate list 大小 |
| `ef_search` | `40` | 查詢時的 candidate list 大小；可於 session-level 動態調整 |


## 6. 核心模組介面設計 (Core Module Interfaces)

### 6.1 `data_update.py` (資料索引引擎)
負責執行 Data Pipeline，具備冪等性（Idempotent）設計，支援增量更新與全量重建。
#### CLI 介面

```
python data_update.py [--rebuild] [--source-dir data/raw] [--verbose]
```

| 參數 | 預設值 | 說明 |
|---|---|---|
| `--rebuild` | False | 全量重建：清空 `processed/` 與 DB，重跑所有步驟 |
| `--source-dir` | `data/raw` | 原始資料目錄 |
| `--verbose` | False | 印出每個檔案的處理狀態 |
| `--help` | - | CI 第一階段驗證用，必須不報錯 |

#### data_update.py 冪等性實作策略

- 冪等性與增量更新策略: 系統採用 **File-level Upsert** 策略來保證 `data_update.py` 的冪等性：
    1.  掃描 `data/raw/` 時，計算每個檔案的 SHA-256 Hash。接著比對本地快取（或 DB 內的 `file_hash`），若 Hash 未改變則 Skip；若 Hash 改變（檔案被修改），則利用 `DELETE FROM chunks WHERE source = ?` 刪除該檔案舊有的所有 Chunks。最後重新執行 Chunking 與 Embedding，並 `INSERT` 新資料。
    2.  **孤兒清理 (Orphan Cleanup):** 查詢 DB 中所有現存的 `source` 清單。若某個 `source` 存在於 DB 中，但其對應的實體檔案已從 `data/raw/` 中被刪除，則執行 `DELETE FROM chunks WHERE source = ?` 進行清理。

- 全量重建流程（`--rebuild`）
    1. `TRUNCATE TABLE chunks` will quickly removes all rows from a set of tables
    2. 清空 `data/processed/`
    3. 執行全量 DocumentCleaner → Chunker → Embedder


- pgvector Table Schema
    ```sql
    CREATE TABLE chunks (
        id          SERIAL PRIMARY KEY,
        chunk_id    TEXT UNIQUE NOT NULL,   -- 用於去重
        source      TEXT NOT NULL,
        file_hash   TEXT NOT NULL,
        chunk_index INT NOT NULL,
        content     TEXT NOT NULL,
        embedding   vector(384)             -- MiniLM-L12 維度
        fts_vector  tsvector GENERATED ALWAYS AS (to_tsvector('english', content)) STORED,
        created_at  TIMESTAMP DEFAULT NOW()
    );
    CREATE INDEX IF NOT EXISTS chunks_embedding_hnsw_idx ON chunks USING hnsw (embedding vector_cosine_ops) WITH (m = 16, ef_construction = 64);
    CREATE INDEX IF NOT EXISTS chunks_fts_gin_idx ON chunks USING gin (fts_vector);
    ```

### 6.2 `rag_query.py` (檢索與生成介面)
封裝 RAG 完整流程（Embed Query $\rightarrow$ Retrieve $\rightarrow$ Generate），並透過 LiteLLM 統一呼叫介面。
```python
from litellm import completion
# 系統啟動時，動態從根目錄載入 AGENT.md 作為 system_prompt
response = completion(
    model="gemini-2.5-flash",       # 可透過 --model 參數切換
    messages=[
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt_with_context}
    ]
)
```
> 導入 Prompt as Configuration 的設計模式，將 system_prompt 從程式碼中抽離，獨立維護於專案根目錄的 AGENT.md 中

### 6.2.1 CLI 介面 
#### Sequence Diagram of RAG Query Pipeline
```mermaid
sequenceDiagram
  autonumber
  participant U as CLI User
  participant E as EmbeddingEngine
  participant V as VectorStore
  participant P as PromptBuilder
  participant L as LiteLLM

  U->>E: encode(query)
  E-->>U: query_vector [384-dim]

  U->>V: similarity_search(query_vector, top_k)
  V-->>U: retrieved_chunks[] (with source metadata)

  U->>P: build(system_prompt, user_query, retrieved_chunks)
  P-->>U: messages (system + user content)

  U->>L: completion(model, messages, api_key, api_base)
  L-->>U: LLM response text

  U->>U: print(response + citations)
```
```python
# 互動式模式
python rag_query.py

# 單次查詢模式
python rag_query.py [--query text] [--top-k int] [--model name]
```

| 參數 | 型別| 預設值 | 說明 |
|---|---|---|---| 
| `--query` |text| - | 執行單次查詢 |
| `--top-k` | int | 5 | 設定檢索的 Chunk 數量 |
| `--model` | name | openai/gemma4 |動態切換 LLM 模型。支援簡寫輸入（如 gemma4, gemini-2.5-flash），系統會自動解析對應的 Provider Prefix。無效輸入將提示重選|
|`-h`,`--help`| Flag | N/A |CI 第一階段驗證用|

>output constraint: 必須附帶引用來源（Source References）與 chunk_index，確保回答的可溯源性。
#### *error handling*: 
- Whitelist Validation: 若使用者傳入不支援的 model name，立即印出錯誤訊息並提示`Invalid model. Available models: gemma4, gemini-2.5-flash, gpt-oss:20b` 不可將錯誤拋給底層 LiteLLM 處理。
- Prefix Injection: 若使用者輸入的 `--model` 參數不包含 `/`（eg.`gemma4`），系統應自動將其補齊為 `openai/gemma4`。

### 6.2.2 Model mapping
Because LiteLLM utilizes the provider/model_name convention to construct provider-specific API request payloads, a Mapping Table component was introduced. This component is responsible for automatic prefix completion and secure API key association prior to request routing.

```python
ALLOWED_MODELS = ["openai/gemma4", "gemini/gemini-2.5-flash", "openai/gpt-oss:20b"]

API_KEY_MAP = {
    "gemma4":           os.getenv("LITELLM_API_KEY_GEMMA4"),
    "gemini-2.5-flash": os.getenv("LITELLM_API_KEY_GEMINI"),
    "gpt-oss:20b":      os.getenv("LITELLM_API_KEY_GPT_OSS"),
}

response = litellm.completion(
    model=model_name,
    api_key=API_KEY_MAP[model_name],
    api_base=os.getenv("LITELLM_BASE_URL"),
    messages=messages
)
```
### 6.2.3 Hybrid Search Pipeline
針對 OpenBMC 韌體文件包含大量「精確變數名稱」、「D-Bus 路徑」與「錯誤代碼」的特性，單純的語意檢索 (Dense Retrieval) 容易因 Out-of-Vocabulary (OOV) 問題而失效。為此，系統採用 **Hybrid Search** 架構：

1.  **Dense Retrieval:** 透過 `pgvector` 的 `<=>` 運算子計算 Cosine Similarity，捕捉自然語言的語意關聯（如 "How to manage power"）。
2.  **Sparse / Lexical Retrieval:** 
    *   **機制:** 採用 PostgreSQL 內建的 `tsvector` 與 `tsquery` 進行全文檢索。
    *   **計分:** 使用 `ts_rank` 函數。這個函數基於 Term Frequency - Inverse Document Frequency 原理，作為本系統中 BM25 的等效替代方案，能精準賦予罕見字（如特定的 D-Bus Interface 名稱）較高的權重，彌補語意向量對精確字串匹配的不足。
3.  **Reciprocal Rank Fusion (RRF):** 為避免 BM25 與 Cosine Similarity 分數尺度不一導致的正規化難題，本系統揚棄傳統的線性加權 (`α*BM25 + (1-α)*Dense`)，改採基於排名的 RRF 演算法。
    *   **數學模型:** $RRF(d) = \sum \frac{1}{k + rank_i(d)}$ （設定平滑常數 $k=60$）
    *   **實作方式:** 直接於 PostgreSQL 中透過 CTE (Common Table Expressions) 執行 `FULL OUTER JOIN` 與 RRF 計算，將運算下推 (Push-down) 至資料庫層，最大化檢索效能。

#### 6.2.3.1 HNSW Session-level Query Configuration

若系統採用 `HNSW` 作為 `pgvector` 的向量索引，`rag_query.py` 在建立 PostgreSQL 連線後，
應於該 session 內設定查詢參數：

```python
with conn.cursor() as cur:
    cur.execute("SET hnsw.ef_search = 40")
```

### 6.2.4 Prompt Engineering 與上下文組裝
為最大限度地減少模型幻覺並確保可溯源性，系統將檢索到的 Chunks 與使用者問題進行嚴格的結構化組裝。
*   **System Prompt:** 要求 LLM 必須使用 `[Source: <source_file>, Chunk: <chunk_index>]` 格式進行引用。
    ```
    You are a senior firmware engineer specializing in the OpenBMC \
    architecture. Your primary function is to answer technical questions based \
    *exclusively* on the provided context documents.

    ## Core Rules

    1. **Grounding**: Answers MUST be grounded in the provided context only.
       Do not use external knowledge.
    2. **Citation**: For every piece of information, append:
       `[Source: <source_file>, Chunk: <chunk_index>]`
    3. **"I Don't Know" Policy**: If context lacks the answer, state:
       "Based on the provided documents, I cannot answer this question."
    4. **Formatting**: Use Markdown for code blocks, lists, and tables.

    ## Code Modification Rules

    5. **Minimal diff**: Modify only the smallest necessary scope.
       State the modification boundary before showing code.
    6. **API existence check**: Every function, D-Bus interface, or property name
       used MUST have a corresponding definition in the context.
       Mark unverified items as `[UNVERIFIED - not found in context]`.
    7. **Before/After format**: Always show changes as a diff or paired
       before/after code blocks. Never provide only the final version.

    ## Code Design Rules

    8. **Spec-constrained design**: All design proposals must respect the D-Bus
       interface contracts defined in the context. Do not assume methods or
       signals that are not documented.
    9. **Dependency declaration**: List every external component (service name,
       interface, property) the design depends on, each with a `[Source: ...]`.
    10. **Alternative paths**: If multiple design approaches exist in the context,
        list all with their trade-offs. Do not give a single answer without
        acknowledging alternatives.

    ## Architecture Analysis Rules

    11. **Hierarchical grounding**: Explain top-down, with each layer supported
        by at least one context chunk citation before proceeding deeper.
    12. **Scope boundary statement**: Begin architecture answers with:
        "This answer is based on: <list of source files used>."
    13. **Uncertainty quantification**: If a detail is only partially covered
        in context, mark it as `[Partial - based on limited context]`
        rather than inferring from general knowledge.
    ```
*   **User Prompt:** 將 Top-K Chunks 格式化為 `Context Information` 區塊，附加於使用者問題之前。

### 6.2.5 Multi-turn 對話與記憶體管理 (Sliding Window Memory)
在互動式模式下，系統必須保留對話歷史以支援上下文追問。
*   **記憶體策略:** 採用滑動視窗 (Sliding Window) 策略，僅保留最近 3 輪 (3 User + 3 Assistant) 的對話歷史。
*   **Token 成本控制:** 歷史紀錄中僅保存「乾淨的 User Query」與「LLM 回答」，**不保存**過去檢索到的龐大 Context，避免 Token 數量無限膨脹。
*   **檢索策略:** 在互動式模式下，每一輪新的 User Query 都必須重新執行 Query Embedding 與 Top-K Retrieval；歷史對話僅用於提供語境，不可直接重用上一輪檢索到的 Context Chunks。

### 6.3 `skill_builder.py` (Agent 技能萃取器)
將 RAG 系統的被動問答能力「升維」為主動知識萃取。系統採用 **Map-Reduce for RAG** 架構，自動掃描知識庫並生成符合 Agent 讀取標準的 `skill.md`。

#### 6.3.1 執行流程 (Map-Reduce Architecture)
1.  **Map 階段 (Domain-Specific 全域掃描):** 
    *   系統預先定義一組針對 OpenBMC 深度定製的 Global Queries（例如：Entity Manager 與 D-Bus 的映射關係、韌體更新流程等）。
        ```
        # Map 階段：全域問題定義 (Domain-Specific Global Queries)
        # 這些問題經過精心設計，旨在從不同架構層次 (API -> IPC -> Hardware) 榨取 OpenBMC 的核心知識。
        GLOBAL_QUERIES = [
        # Q1: 高階架構與 Redfish API (對應 bmcweb 與 docs)
        "Explain the overall software architecture of OpenBMC. Specifically, what is the role of `bmcweb`, and how does it expose the Redfish API to external clients?",

        # Q2: 微服務通訊骨幹 (對應 phosphor-dbus-interfaces)
        "What is the significance of D-Bus (Inter-Process Communication) in OpenBMC? List 3-5 critical D-Bus interfaces defined in `phosphor-dbus-interfaces` and explain their primary purposes.",

        # Q3: 動態硬體配置 (對應 entity-manager)
        "How does OpenBMC handle dynamic hardware configurations without hardcoding? Describe the purpose of Entity Manager and how its JSON configuration files map hardware components (like sensors) to D-Bus objects.",

        # Q4: 底層硬體抽象 (對應 linux devicetree 與 phosphor-gpio-monitor)
        "At the OS and hardware level, how does OpenBMC interact with GPIOs and specific chips (e.g., ASPEED)? Explain the role of the Linux Device Tree (.dts) and services like `phosphor-gpio-monitor`.",

        # Q5: 韌體生命週期與安全 (對應 docs)
        "What are the standard methodologies, security mechanisms, and best practices for firmware code updates and secure boot in OpenBMC?"]
        ```
    *   針對每個問題，重複利用 `rag_query.py` 中的 `HybridRetriever` 檢索 Top-K Chunks，並交由 `RAGAgent` 生成該子領域的專業回答。
2.  **Reduce 階段 (知識收斂與格式化):** 
    *   將 Map 階段收集到的所有回答拼接為一個巨大的 Context。
    *   透過嚴格的 Synthesis Prompt，指示 LLM 進行語意融合。
    *   **創新約束 (Innovation Constraints):** Prompt 中強制要求 LLM 在適當章節生成 **Mermaid.js 架構圖** 或 **JSON 設定檔範例**，以提升 Skill 文件的技術深度。
    *   **引用約束 (Citation Policy):** 考量不同 LLM 遵循指令的能力差異，內文的內聯引用 (`[Source: ...]`) 設為鼓勵但不強制；但程式必須在背景聚合所有被檢索到的 Source 檔案，並統一條列於 `## Source References` 章節，確保 100% 的可溯源性。
3.  **Output:** 將生成的結果寫入 `skill.md`。

#### 6.3.2 CLI 介面
```bash
python skill_builder.py [--output skill.md] [--model openai/gemma4] [--top-k 15] [--help]

## 7. Infrastructure & Database Deployment

為確保開發環境的一致性與可移植性，採用 Docker Compose 統一管理 Vector DB 與視覺化除錯工具。

### 7.1 容器化架構設計 (`docker-compose.yml`)

系統依賴以下兩個核心服務：

1. **pgvector (Database)：** 基於 `pgvector/pgvector:pg16`（官方維護，版本明確），提供向量儲存與相似度檢索能力。
2. **pgAdmin (GUI Tool)：** 提供 Web 介面，方便開發者直接檢視 Chunking 結果、驗證 Metadata 與執行 SQL 除錯。

**Volume 掛載規範（HW3 要求）：**
必須使用**相對路徑**（如 `./docker/pgdata`）進行 Volume 掛載，確保專案在任何機器上 `git clone` 後皆可直接啟動，避免絕對路徑造成的環境依賴問題。



> **`.gitignore` 必須包含：** `docker/pgdata/`，避免資料庫資料被 commit。


### 7.2 啟動與初始化生命週期 (Startup Lifecycle)

系統啟動遵循嚴格的先後順序以確保冪等性：

1. **基礎設施啟動 (Infrastructure Provisioning)：**
   - 開發者執行 `docker compose up -d`。
   - Docker 拉取映像檔、建立 Network、掛載 Volume，並啟動 PostgreSQL（Port 5432）。

2. **應用程式連線與自動建表 (Auto-Migration)：**
   - 執行 `python data_update.py` 時，`VectorStore` 模組於 Step 0 自動執行 `CREATE EXTENSION IF NOT EXISTS vector` 與 `CREATE TABLE IF NOT EXISTS chunks`。
   - 確保全新的資料庫環境能自動完成 Schema 初始化，無需人工介入。

3. **資料寫入 (Data Ingestion)：**
   - 執行 `docker compose ps` 確認 pgvector 狀態為 `running` 後，`data_update.py` 才開始執行 File-level Upsert，將向量資料寫入 DB。

### 7.3 pgAdmin 除錯指南 (Debugging Guide)

*   **存取方式：** 瀏覽器開啟 `http://localhost:5050`（帳號：`admin@admin.com`，密碼：`root`）。
*   **連線設定：** Host 填入 `db`（即 `docker-compose.yml` 中的 hostname），Port `5432`，User `raguser`。
*   **主要用途：**
    *   **Chunk 驗證：** 檢視 `content` 欄位，確認 Markdown Code Fences 與 YAML 展平結果是否如預期保留。
    *   **Lineage 追蹤：** 執行 `SELECT * FROM chunks WHERE source LIKE '%Host.interface%'` 快速定位特定 D-Bus 介面的切分狀況。
    *   **向量維度確認：** 執行 `SELECT chunk_id, vector_dims(embedding) FROM chunks LIMIT 5` 確認 embedding 欄位成功寫入 384 維。




