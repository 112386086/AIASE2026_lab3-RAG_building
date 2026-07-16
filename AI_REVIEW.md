# HW3 AI 評分回饋

> 本份回饋由 **Anthropic Claude Opus 4.7** 與 **OpenAI GPT-5.5** 兩個獨立模型，分別針對 Phase 1 與 Phase 2 程式碼與文件進行評分；最終加權分數為兩模型平均後，進行全班性的 Normalize，以及老師加分。
 
---

## 本次公布的兩個分數

本次 HW3 作業，每位同學會公布**兩個分數**，計算方式為下列三個候選值中**最高的兩個**：

| 候選 | 來源 | 計算 | 值 |
|---|---|---|---:|
| A | Max(Phase 1 兩模型評分) | max(Opus 93.5, GPT 98.0) | 98.00 |
| B | Max(Phase 2 兩模型評分) | max(Opus 91.9, GPT 93.6) | 93.56 |
| C | 最終加權分數 | 詳見下方加權計算 | 96.95 |

### 你的兩個分數

### **98.00**　／　**96.95**

_（A：Max(Phase 1 兩模型評分) = 98.00；C：最終加權分數 = 96.95）_

## 最終加權分數（候選 C）的計算

| 來源 | Phase 1 (40%) | Phase 2 (60%) | 加權平均 |
|---|---:|---:|---:|
| Anthropic Claude Opus 4.7 | 93.5 | 91.9 | 92.56 |
| OpenAI GPT-5.5 | 98.0 | 93.6 | 95.34 |
| **兩模型平均** | **95.8** | **92.8** | **93.95** |
| 老師加分 (professor_bonus) | | | +3 |
| **最終分數** | | | **96.95** |

## 計算公式

```
Phase 1 平均  = (Opus_P1 + GPT_P1) / 2
Phase 2 平均  = (Opus_P2 + GPT_P2) / 2
加權平均      = 0.4 × Phase 1 平均 + 0.6 × Phase 2 平均
Normalize 後  = 依全班分布做校準
最終分數      = min(100, Normalize 後 + 老師加分)
```

## 專案基本資料

- **github_id**：`112386086-1`
- **領域**（Haiku 抽取）：`openbmc_firmware_architecture`
- **領域分類**（taxonomy）：`semiconductor_industry`
- **Phase 1 CI**：✓ 通過
- **Phase 2 CI**：✓ 通過

## Phase 1 分項評語（40% 權重）

| 面向 | Opus 分數 | Opus 評語 | GPT 分數 | GPT 評語 |
|---|---:|---|---:|---|
| 資料收集 | 95 | data/processed 含 1114 份檔案，data/raw 達 1164 份，遠超 high anchor 標準。格式多元（.md 178、.json 306、.txt 6 與 YAML/DTS 等），涵蓋 OpenBMC 官方 docs、D-Bus YAML、Entity Manager JSON、Device Tree。README 雖較簡短但 .env.example 與 docker-compose 齊備，授權合規 signal 為 clear。 | 98 | data/ 原始 1164、processed 1114，遠高於 Phase1 高標；含 .md/.json/.txt 與 YAML/DTS 等多格式，README 有環境、主題與操作說明。 |
| RAG 系統完整度 | 92 | data_update.py 461 行實作多格式解析（MD/YAML/JSON/DTS）、Strict Mirror、Context-Enriched chunking（512 tokens、64 overlap，保留 code fence/table）。rag_query.py 342 行實作 Hybrid Search（Dense HNSW + Sparse tsvector + RRF k=60）、Session-level ef_search 設定、LiteLLM 多模型路由與 citation 顯示。架構成熟度高於同領域 high anchor。 | 97 | data_update.py 支援多格式清理、512 token chunk/overlap、context prefix、SentenceTransformer embedding 與 pgvector/HNSW/FTS schema；rag_query.py 有 hybrid top-k、來源顯示與 LiteLLM。 |
| 冪等性 | 95 | 明確採用 File-level SHA-256 hash 比對 + Orphan Cleanup（DELETE+INSERT on change），README 範例展示 --rebuild 旗標，docker compose down -v 重置流程說明清楚。增量更新與孤兒清理機制完整，超越多數同儕。 | 100 | data_update.py 明確支援 --rebuild，並實作檔案級 SHA-256 比對、變更時 DELETE+INSERT、孤兒清理，增量與全量重建設計完整。 |

## Phase 2 分項評語（60% 權重）

| 面向 | Opus 分數 | Opus 評語 | GPT 分數 | GPT 評語 |
|---|---:|---|---:|---|
| 資料收集深度 | 92 | 資料規模 1115 份遠超 20 門檻，涵蓋 OpenBMC 5 個官方 repo 與 IBM Power10 文檔，多元格式 (.md/.yaml/.json/.dts) 完整覆蓋韌體技術棧。README §Data Sources Statement 明確標示 Apache 2.0/GPL 2.0 授權，合規清晰。略扣分於資料來源以官方文檔為主，缺第三方教學資源。 | 94 | data/raw 1165、processed 1115，遠超 ≥20；涵蓋官方 docs、YAML/JSON/DTS/CPP 與 IBM 文件。README §Data Sources 清楚列 Apache/GPL/IBM，但少數社群來源授權較泛。 |
| skill.md 品質 | 90 | 8 個必要章節齊全，Core Concepts 列 9 條且含 Mermaid 架構圖；Key Entities 含具體 D-Bus interface 路徑（如 xyz.openbmc_project.Sensor.Purpose）與檔名引用；Methodology 附 JSON 設定範例；Knowledge Gaps 誠實點出 Secure Boot 與硬體 pinout 限制。整體呈現資深韌體工程師整理的領域指南。 | 93 | skill.md 章節齊全且約 19k 字；§Core Concepts 有 9 項與架構圖，§Key Entities 含 bmcweb、Entity Manager、D-Bus 介面等具體實體，內容像專家整理。 |
| README 設計決策 | 95 | README §Design Decisions 完整回答 chunking（Markdown-Aware + Context Enrichment）、embedding、pgvector + HNSW vs ChromaDB 取捨、Hybrid RRF retrieval、Sliding Window prompt、SHA-256 + Orphan Cleanup 冪等性、skill_builder 全域問題設計，每項皆具體說明取捨理由，深度遠超 anchor。 | 95 | README §Design Decisions 完整回答 chunking、embedding、pgvector、hybrid RRF、prompt、idempotency、skill_builder；理由與 OpenBMC 資料特性連結明確。 |
| skill_builder 品質 | 92 | skill_builder.py 設計 5 個 Domain-Specific 全域問題，跨 API/IPC/Entity Manager/Device Tree/韌體生命週期，覆蓋 Overview/Trends/Entities 三類知識；Map-Reduce 架構透過 Synthesis Prompt 強制 LLM 整合並要求 Mermaid + JSON 範例，重用 rag_query 模組符合 DRY，整合度高非機械拼貼。 | 93 | skill_builder.py 以 5 個 domain-specific global queries 覆蓋 API、D-Bus、硬體抽象、更新安全；Map-Reduce 合成 skill.md，非單純拼貼，但 RRF k 缺調參分析。 |

## 整體評語

### 亮點

- 完整的Hybrid Search實作，同時支援語意與精確字串檢索
- 嚴格的冪等性設計，檔案級Hash比對與孤兒清理確保DB一致性
- Context-Enriched Chunking強制注入來源路徑，提升Embedding錨定精度
- 精心設計的5個Domain-Specific全域問題，跨越API/IPC/硬體層次
- 完整的多輪對話支援與Sliding Window記憶體管理

### 改進建議

- OpenBMC規格書上下文語意關聯度不高，導致部分查詢LLM無法回答
- 資料來源主要為官方文檔，缺乏網路技術手冊與教學資源
- Markdown-Aware切分邏輯複雜，維護成本較高
- RRF融合演算法參數(k=60)未見敏感性分析或調優依據

---

_本份評分回饋由自動化評分管線（Anthropic + OpenAI 雙模型獨立評分 → 平均 → rescale → 老師加分）產出，僅作為個人學習參考。若對評分有疑問請於課堂或 office hour 提出。_
