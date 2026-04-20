"""
skill_builder.py — OpenBMC RAG 系統：Agent 技能萃取器
版本：v3.0 (對齊 SDD_RAG.md v3.0)

實作重點：
1. Code Reuse: 完美重用 rag_query.py 的 VectorStore, RAGAgent 與 Prefix Injection。
2. Map-Reduce Architecture: 
   - Map: 提出 5 個 Domain-Specific 全域問題，透過 Hybrid Search 收集各子領域的專業回答。
   - Reduce: 將收集到的回答作為 Context，交由 LLM 進行語意融合與 Markdown 排版。
3. Innovation: 強制 LLM 生成 Mermaid 架構圖與 JSON 設定檔範例。
"""

import argparse
import logging
import os
import sys
from datetime import datetime
from typing import List, Set

import litellm

# 【架構亮點】：直接重用 rag_query.py 的核心模組，遵守 DRY 原則！
from rag_query import (
    VectorStore, 
    RAGAgent, 
    EmbeddingEngine, 
    normalize_model_name, 
    get_api_key
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# 1. Map 階段：全域問題定義 (Domain-Specific Global Queries)
# ─────────────────────────────────────────────────────────────────────────────
# 這些問題經過精心設計，旨在從不同架構層次 (API -> IPC -> Hardware) 榨取 OpenBMC 的核心知識。
GLOBAL_QUERIES = [
    # Q1: 高階架構與 Redfish API
    "Explain the overall software architecture of OpenBMC. Specifically, what is the role of `bmcweb`, and how does it expose the Redfish API to external clients?",
    
    # Q2: 微服務通訊骨幹
    "What is the significance of D-Bus (Inter-Process Communication) in OpenBMC? List 3-5 critical D-Bus interfaces defined in `phosphor-dbus-interfaces` and explain their primary purposes.",
    
    # Q3: 動態硬體配置
    "How does OpenBMC handle dynamic hardware configurations without hardcoding? Describe the purpose of Entity Manager and how its JSON configuration files map hardware components (like sensors) to D-Bus objects.",
    
    # Q4: 底層硬體抽象
    "At the OS and hardware level, how does OpenBMC interact with GPIOs and specific chips (e.g., ASPEED)? Explain the role of the Linux Device Tree (.dts) and services like `phosphor-gpio-monitor`.",
    
    # Q5: 韌體生命週期與安全
    "What are the standard methodologies, security mechanisms, and best practices for firmware code updates and secure boot in OpenBMC?"
]

# ─────────────────────────────────────────────────────────────────────────────
# 2. Reduce 階段：最終合成 Prompt (Synthesis Prompt)
# ─────────────────────────────────────────────────────────────────────────────
SYNTHESIS_PROMPT = """You are an expert technical writer and firmware architect. 
I will provide you with several detailed summaries about OpenBMC extracted from a RAG knowledge base. 
Your task is to synthesize this information into a single, highly structured Markdown file that an AI Agent can use as a "Skill".

**CRITICAL INSTRUCTIONS:**
1. **Synthesize, do not just concatenate:** Merge duplicate information and ensure a logical flow.
2. **Preserve Citations:** You MUST keep the `[Source: ..., Chunk: ...]` citations exactly as they appear in the raw summaries.
3. **Innovation Constraints:** 
   - Under "Core Concepts", you MUST include a `mermaid` graph illustrating the OpenBMC architecture (e.g., bmcweb -> D-Bus -> Entity Manager).
   - Under "Methodology & Best Practices" or "Key Entities", you MUST provide a short JSON snippet example of an Entity Manager configuration.
4. **Strict Formatting:** You MUST output ONLY the Markdown content below, filling in the bracketed sections with the synthesized knowledge. Do not add any conversational filler before or after the Markdown.

# Skill: OpenBMC Firmware Development

## Metadata
- **知識領域**：OpenBMC Firmware Architecture, D-Bus IPC, Hardware Abstraction
- **資料來源數量**：{source_count} 份文件
- **最後更新時間**：{today_date}
- **適用 Agent 類型**：Firmware Engineer Assistant / Architecture Consultant

## Overview（一段話摘要）
[Provide a 200-word max summary of OpenBMC's core capabilities based on the text]

## Core Concepts（核心概念）
[List 5-10 core concepts with 1-2 sentences each. MUST include citations.]
[MUST include a Mermaid.js graph here]

## Key Trends（最新趨勢）
[List 3-5 key trends or architectural directions. MUST include citations.]

## Key Entities（重要實體）
[List important D-Bus interfaces, tools like Entity Manager, etc. MUST include citations.]

## Methodology & Best Practices（方法論與最佳實踐）
[List accepted methods, security principles, and configurations. MUST include citations and a JSON snippet example.]

## Knowledge Gaps & Limitations（知識邊界）
[Critically analyze what specific hardware components or detailed configurations are missing from the provided context]

## Example Q&A（代表性問答）
[Provide 3 representative Q&A pairs that demonstrate what this skill can answer]

## Source References（來源索引）
{source_references}

---
**RAW SUMMARIES TO SYNTHESIZE:**
{raw_summaries}
"""

# ─────────────────────────────────────────────────────────────────────────────
# 3. 主程式
# ─────────────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="OpenBMC RAG — Skill Builder")
    parser.add_argument("--output", type=str, default="skill.md", help="Output file name")
    parser.add_argument("--model", type=str, default="gemma4", help="LLM Model (e.g., gemma4, gemini-2.5-flash)")
    parser.add_argument("--top-k", type=int, default=15, help="Chunks to retrieve per query (default: 15)")
    args = parser.parse_args()

    # 1. 初始化與驗證 (重用 rag_query.py 邏輯)
    model_name = normalize_model_name(args.model)
    api_key = get_api_key(model_name)
    
    conn_str = os.getenv("PGVECTOR_CONNECTION_STRING")
    if not conn_str:
        log.error("PGVECTOR_CONNECTION_STRING not set in .env")
        sys.exit(1)

    log.info(f"Starting Skill Builder | Model: {model_name} | Output: {args.output}")
    
    embedder = EmbeddingEngine()
    db = VectorStore(conn_str)
    
    # 取得資料庫總文件數 (供 Metadata 使用)
    with db.conn.cursor() as cur:
        cur.execute("SELECT COUNT(DISTINCT source) FROM chunks;")
        source_count = cur.fetchone()[0]

    # ==========================================
    # Stage 1: Map (發散收集知識)
    # ==========================================
    log.info("--- STAGE 1: MAP (Global Knowledge Extraction) ---")
    raw_answers: List[str] = []
    unique_sources: Set[str] = set()
    
    for i, query in enumerate(GLOBAL_QUERIES):
        log.info(f"Query {i+1}/{len(GLOBAL_QUERIES)}: {query}")
        
        # 每次查詢都實例化一個新的 Agent，確保記憶體 (History) 是乾淨的
        agent = RAGAgent(model_name)
        
        query_vector = embedder.encode(query)
        chunks = db.hybrid_search(query, query_vector, top_k=args.top_k)
        
        if chunks:
            # 收集背景 Source 供最後的 Reference 使用
            for c in chunks:
                unique_sources.add(c['source'])
                
            answer = agent.generate(query, chunks)
            raw_answers.append(f"### Sub-topic: {query}\n{answer}\n")
        else:
            log.warning(f"No context found for query: {query}")

    db.close()

    # ==========================================
    # Stage 2: Reduce (收斂生成 skill.md)
    # ==========================================
    log.info("--- STAGE 2: REDUCE (Synthesizing skill.md) ---")
    combined_info = "\n".join(raw_answers)
    today_date = datetime.now().strftime("%Y-%m-%d")
    
    # 格式化 Source References
    source_refs_str = "\n".join([f"- `{src}`" for src in sorted(unique_sources)])
    
    final_prompt = SYNTHESIS_PROMPT.format(
        source_count=source_count,
        today_date=today_date,
        source_references=source_refs_str,
        raw_summaries=combined_info
    )

    messages = [
        {"role": "system", "content": "You are a helpful assistant that formats text into strict Markdown."},
        {"role": "user", "content": final_prompt}
    ]

    try:
        log.info("Calling LLM for final synthesis (this may take a minute)...")
        response = litellm.completion(
            model=model_name,
            api_key=api_key,
            api_base=os.getenv("LITELLM_BASE_URL"),
            messages=messages,
            drop_params=True
        )
        final_markdown = response.choices[0].message.content

        # 寫入檔案
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(final_markdown)
        log.info(f"Success! Skill file written to {args.output}")

    except Exception as e:
        log.error(f"Failed to generate skill.md: {e}")

if __name__ == "__main__":
    main()