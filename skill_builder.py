"""
skill_builder.py — OpenBMC RAG 系統：Agent 技能萃取器
版本：v3.1 (對齊 SDD_RAG.md v3.0 & HW3 規範)

實作重點：
1. 移除 --top-k 參數，固定掃描深度以確保產出品質穩定。
2. 放寬 Synthesis Prompt 對內文 Citation 的強制要求，適應不同 LLM 的能力差異，
   僅要求於文末 Source References 統整來源。
"""

import argparse
import logging
import sys
import re
from datetime import datetime
from typing import List

import litellm

# 重用 rag_query.py 的核心模組
from rag_query import (
    VectorStore, 
    RAGAgent, 
    EmbeddingEngine, 
    normalize_model_name, 
    get_api_key
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

# 內部常數：全域掃描時的檢索深度 (不開放 CLI 修改)
SCAN_TOP_K = 15

# ─────────────────────────────────────────────────────────────────────────────
# 1. Map 階段：全域問題定義 (Global Queries)
# ─────────────────────────────────────────────────────────────────────────────
GLOBAL_QUERIES = [
    "What is OpenBMC? Provide a high-level overview of its architecture and core concepts.",
    "What are the most important D-Bus interfaces defined in phosphor-dbus-interfaces? List their purposes.",
    "How does OpenBMC handle hardware configurations, GPIO, and Device Tree? Explain the role of Entity Manager.",
    "What are the best practices, methodologies, and security mechanisms for OpenBMC development?",
    "What are the key trends, recent developments, and important entities (tools/repos) in OpenBMC?"
]

# ─────────────────────────────────────────────────────────────────────────────
# 2. Reduce 階段：最終合成 Prompt (Synthesis Prompt)
# ─────────────────────────────────────────────────────────────────────────────
SYNTHESIS_PROMPT = """You are an expert technical writer and firmware architect. 
I will provide you with several detailed summaries about OpenBMC extracted from a RAG knowledge base. 
Your task is to synthesize this information into a single, highly structured Markdown file that an AI Agent can use as a "Skill".

**CRITICAL INSTRUCTIONS:**
1. **Synthesize, do not just concatenate:** Merge duplicate information and ensure a logical flow.
2. **Strict Formatting:** You MUST output ONLY the Markdown content below, filling in the bracketed sections with the synthesized knowledge. Do not add any conversational filler before or after the Markdown.

# Skill: OpenBMC Firmware Development

## Metadata
- **知識領域**：OpenBMC Firmware Architecture, D-Bus IPC, Hardware Abstraction
- **資料來源數量**：{source_count} 份文件
- **最後更新時間**：{today_date}
- **適用 Agent 類型**：Firmware Engineer Assistant / Architecture Consultant

## Overview（一段話摘要）
[Provide a 200-word max summary of OpenBMC's core capabilities based on the text]

## Core Concepts（核心概念）
[List 5-10 core concepts with 1-2 sentences each.]

## Key Trends（最新趨勢）
[List 3-5 key trends or architectural directions.]

## Key Entities（重要實體）
[List important D-Bus interfaces, tools like Entity Manager, etc.]

## Methodology & Best Practices（方法論與最佳實踐）
[List accepted methods, security principles, and configurations.]

## Knowledge Gaps & Limitations（知識邊界）
[State what is NOT covered or what is missing based on the provided text]

## Example Q&A（代表性問答）
[Provide 3 representative Q&A pairs that demonstrate what this skill can answer]

## Source References（來源索引）
[List the unique source files mentioned in the RAW SUMMARIES below. Format as a bulleted list.]

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
    args = parser.parse_args()

    # 1. 初始化與驗證
    model_name = normalize_model_name(args.model)
    api_key = get_api_key(model_name)
    
    import os
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
    
    for i, query in enumerate(GLOBAL_QUERIES):
        log.info(f"Query {i+1}/{len(GLOBAL_QUERIES)}: {query}")
        
        agent = RAGAgent(model_name)
        query_vector = embedder.encode(query)
        # 使用內部常數 SCAN_TOP_K
        chunks = db.hybrid_search(query, query_vector, top_k=SCAN_TOP_K)
        
        if chunks:
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
    
    final_prompt = SYNTHESIS_PROMPT.format(
        source_count=source_count,
        today_date=today_date,
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

        # 簡單的後處理：移除 LLM 可能產生的 ```markdown 標籤
        final_markdown = re.sub(r"^```markdown\n", "", final_markdown)
        final_markdown = re.sub(r"\n```$", "", final_markdown)

        # 寫入檔案
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(final_markdown.strip() + "\n")
        log.info(f"Success! Skill file written to {args.output}")

    except Exception as e:
        log.error(f"Failed to generate skill.md: {e}")

if __name__ == "__main__":
    main()