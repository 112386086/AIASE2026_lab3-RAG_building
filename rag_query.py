# rag_query.py
from __future__ import annotations

import argparse
import os
import sys
import logging
from typing import List, Dict, Any

import psycopg2
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
import litellm

# ─────────────────────────────────────────────────────────────────────────────
# 常數與設定
# ─────────────────────────────────────────────────────────────────────────────
load_dotenv()

# 關閉 LiteLLM 的遙測與過多日誌
litellm.telemetry = False
litellm.suppress_debug_info = True

EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "paraphrase-multilingual-MiniLM-L12-v2")
VECTOR_DIM = 384

# 依據 SDD 6.2.2 定義標準模型名稱
ALLOWED_MODELS = ["openai/gemma4", "gemini/gemini-2.5-flash", "openai/gpt-oss:20b"]

# 設定 Logger
logging.basicConfig(level=logging.WARNING, format="%(levelname)s: %(message)s")
log = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# 1. 模型路由與名稱正規化 (SDD 6.2.1 & 6.2.2)
# ─────────────────────────────────────────────────────────────────────────────
def normalize_model_name(raw_model_name: str) -> str:
    """
    模型名稱正規化 (Dictionary-based Routing)：
    支援簡寫輸入，自動補齊對應的 Provider Prefix。
    """
    prefix_map = {
        "gemma4": "openai/gemma4",
        "gemini-2.5-flash": "gemini/gemini-2.5-flash",
        "gpt-oss:20b": "openai/gpt-oss:20b"
    }

    clean_name = raw_model_name.split("/")[-1]

    if clean_name in prefix_map:
        normalized_name = prefix_map[clean_name]
    else:
        normalized_name = raw_model_name 

    if normalized_name not in ALLOWED_MODELS:
        print(f"Error: Invalid model '{raw_model_name}'.")
        print("Available models: gemma4, gemini-2.5-flash, gpt-oss:20b")
        sys.exit(1)
        
    return normalized_name

def get_api_key(normalized_model_name: str) -> str:
    """根據正規化後的模型名稱取得對應的 API Key"""
    api_key_map = {
        "openai/gemma4":           os.getenv("LITELLM_API_KEY_GEMMA4"),
        "gemini/gemini-2.5-flash": os.getenv("LITELLM_API_KEY_GEMINI"),
        "openai/gpt-oss:20b":      os.getenv("LITELLM_API_KEY_GPT_OSS"),
    }
    key = api_key_map.get(normalized_model_name)
    if not key:
        log.warning(f"API Key for {normalized_model_name} is not set in .env")
    return key


# ─────────────────────────────────────────────────────────────────────────────
# 2. Embedding 層
# ─────────────────────────────────────────────────────────────────────────────
class EmbeddingEngine:
    def __init__(self, model_name: str = EMBEDDING_MODEL):
        print(f"[*] Loading Embedding Model: {model_name} ...")
        self.model = SentenceTransformer(model_name)

    def encode(self, text: str) -> list[float]:
        return self.model.encode(text, show_progress_bar=False).tolist()


# ─────────────────────────────────────────────────────────────────────────────
# 3. Vector DB 層 (Hybrid Search & HNSW - SDD 6.2.3)
# ─────────────────────────────────────────────────────────────────────────────
class VectorStore:
    TABLE_NAME = "chunks"

    def __init__(self, connection_string: str):
        self.conn = psycopg2.connect(connection_string)
        self._configure_session()

    def _configure_session(self):
        """設定 Session-level 的 HNSW 查詢參數 (SDD 6.2.3.1)"""
        with self.conn.cursor() as cur:
            cur.execute("SET hnsw.ef_search = 100;")
        self.conn.commit()

    def hybrid_search(self, query_text: str, query_vector: list[float], top_k: int = 5) -> List[Dict[str, Any]]:
        """
        執行 Hybrid Search (Dense + Sparse) 並透過 RRF 進行重排。
        """
        vec_str = f"[{','.join(map(str, query_vector))}]"
        
        sql = f"""
        WITH dense_results AS (
            SELECT id, chunk_id, source, chunk_index, content,
                   ROW_NUMBER() OVER (ORDER BY embedding <=> %s::vector) as dense_rank
            FROM {self.TABLE_NAME}
            ORDER BY embedding <=> %s::vector
            LIMIT 60
        ),
        sparse_results AS (
            SELECT id, chunk_id, source, chunk_index, content,
                   ROW_NUMBER() OVER (ORDER BY ts_rank(fts_vector, websearch_to_tsquery('english', %s)) DESC) as sparse_rank
            FROM {self.TABLE_NAME}
            WHERE fts_vector @@ websearch_to_tsquery('english', %s)
            ORDER BY ts_rank(fts_vector, websearch_to_tsquery('english', %s)) DESC
            LIMIT 60
        ),
        combined AS (
            SELECT
                COALESCE(d.id, s.id) as id,
                COALESCE(d.chunk_id, s.chunk_id) as chunk_id,
                COALESCE(d.source, s.source) as source,
                COALESCE(d.chunk_index, s.chunk_index) as chunk_index,
                COALESCE(d.content, s.content) as content,
                COALESCE(1.0 / (60 + d.dense_rank), 0.0) +
                COALESCE(1.0 / (60 + s.sparse_rank), 0.0) as rrf_score
            FROM dense_results d
            FULL OUTER JOIN sparse_results s ON d.id = s.id
        )
        SELECT chunk_id, source, chunk_index, content, rrf_score
        FROM combined
        ORDER BY rrf_score DESC
        LIMIT %s;
        """
        
        with self.conn.cursor() as cur:
            cur.execute(sql, (vec_str, vec_str, query_text, query_text, query_text, top_k))
            rows = cur.fetchall()
            
        results = []
        for row in rows:
            results.append({
                "chunk_id": row[0],
                "source": row[1],
                "chunk_index": row[2],
                "content": row[3],
                "score": row[4]
            })
        return results

    def close(self):
        self.conn.close()


# ─────────────────────────────────────────────────────────────────────────────
# 4. RAG Agent (Prompt 組裝與記憶體管理 - SDD 6.2.4 & 6.2.5)
# ─────────────────────────────────────────────────────────────────────────────
class RAGAgent:
    def __init__(self, model_name: str):
        self.model_name = model_name
        self.api_key = get_api_key(model_name)
        self.api_base = os.getenv("LITELLM_BASE_URL")
        
        if not self.api_base:
            log.error("LITELLM_BASE_URL is not set in .env")
            sys.exit(1)

        # Sliding Window Memory
        self.history: List[Dict[str, str]] = []
        self.max_history_turns = 3
        
        # 動態載入 AGENT.md 作為 System Prompt
        self.system_prompt = self._load_agent_prompt()

    def _load_agent_prompt(self) -> str:
        """從專案根目錄讀取 AGENT.md 作為 System Prompt"""
        # 取得目前腳本所在目錄（假設為專案根目錄）
        base_dir = os.path.dirname(os.path.abspath(__file__))
        prompt_path = os.path.join(base_dir, "AGENT.md")
        
        try:
            with open(prompt_path, "r", encoding="utf-8") as f:
                # 移除可能存在的 Markdown Frontmatter (--- title: AGENT ---)
                content = f.read()
                if content.startswith("---"):
                    parts = content.split("---", 2)
                    if len(parts) >= 3:
                        return parts[2].strip()
                return content.strip()
        except FileNotFoundError:
            log.error(f"AGENT.md not found at {prompt_path}. Please create it.")
            sys.exit(1)

    def _build_system_prompt(self) -> str:
        """回傳載入的 System Prompt"""
        return self.system_prompt

    def _build_user_prompt(self, query: str, chunks: List[Dict[str, Any]]) -> str:
        context_blocks = []
        for c in chunks:
            block = f"[Source: {c['source']}, Chunk: {c['chunk_index']}]\n{c['content']}"
            context_blocks.append(block)
        
        context_str = "\n\n---\n\n".join(context_blocks)
        
        return (
            f"Context Information:\n---\n{context_str}\n---\n\n"
            f"User Question: {query}"
        )

    def generate(self, query: str, chunks: List[Dict[str, Any]]) -> str:
        system_prompt = self._build_system_prompt()
        user_prompt_with_context = self._build_user_prompt(query, chunks)

        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(self.history)
        messages.append({"role": "user", "content": user_prompt_with_context})

        try:
            response = litellm.completion(
                model=self.model_name,
                api_key=self.api_key,
                api_base=self.api_base,
                messages=messages
            )
            answer = response.choices[0].message.content

            # Token 成本控制：只存乾淨的 Query
            self.history.append({"role": "user", "content": query})
            self.history.append({"role": "assistant", "content": answer})
            
            if len(self.history) > self.max_history_turns * 2:
                self.history = self.history[-(self.max_history_turns * 2):]

            return answer

        except Exception as e:
            log.error(f"LiteLLM API Error: {e}")
            return "Error: Unable to generate response from LLM."


# ─────────────────────────────────────────────────────────────────────────────
# 5. 主程式與 CLI 邏輯
# ─────────────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="OpenBMC RAG Query Interface")
    parser.add_argument("--query", type=str, help="執行單次查詢")
    parser.add_argument("--top-k", type=int, default=5, help="設定檢索的 Chunk 數量")
    parser.add_argument("--model", type=str, default="gemma4", help="指定 LLM 模型 (預設: gemma4)")
    args = parser.parse_args()

    # 1. 模型名稱正規化與驗證
    model_name = normalize_model_name(args.model)
    
    # 2. 初始化基礎設施
    connection_str = os.getenv("PGVECTOR_CONNECTION_STRING")
    if not connection_str:
        print("Error: PGVECTOR_CONNECTION_STRING not set in .env")
        sys.exit(1)

    embedder = EmbeddingEngine()
    db = VectorStore(connection_str)
    agent = RAGAgent(model_name)

    print(f"[*] System Ready. Routing to model: {model_name}")
    print("-" * 60)

    # 3. 執行查詢邏輯
    def process_query(user_query: str):
        print("\n[*] Embedding query & Searching...")
        query_vector = embedder.encode(user_query)
        chunks = db.hybrid_search(user_query, query_vector, top_k=args.top_k)

        if not chunks:
            print("\n[!] No relevant context found in the database.")
            return

        print("\n[*] Retrieved Context Sources:")
        for i, c in enumerate(chunks):
            print(f"  {i+1}. [Source: {c['source']}, Chunk: {c['chunk_index']}] (Score: {c['score']:.4f})")

        print("\n[*] Generating Answer...")
        answer = agent.generate(user_query, chunks)
        
        print("\n" + "="*60)
        print("🤖 Assistant:")
        print(answer)
        print("="*60 + "\n")

    # 單次查詢模式
    if args.query:
        process_query(args.query)
    # 互動式模式
    else:
        print("Type 'exit' or 'quit' to stop.")
        while True:
            try:
                user_input = input("🧑 User: ").strip()
                if user_input.lower() in ['exit', 'quit']:
                    break
                if not user_input:
                    continue
                process_query(user_input)
            except KeyboardInterrupt:
                break
            except EOFError:
                break

    db.close()
    print("\nGoodbye!")

if __name__ == "__main__":
    main()