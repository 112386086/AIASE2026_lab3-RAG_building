# data_update.py
from __future__ import annotations

import argparse
import hashlib
import logging
import os
import re
import sys
import shutil
from pathlib import Path
from typing import Generator, Any

import psycopg2
import yaml
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer

# ─────────────────────────────────────────────────────────────────────────────
# 常數與設定
# ─────────────────────────────────────────────────────────────────────────────
load_dotenv()

PROCESSED_DIR = Path("data/processed")

# SDD 5. 語意切分策略設定
CHUNK_SIZE_TOKENS = 512
CHUNK_OVERLAP_TOKENS = 64
CHARS_PER_TOKEN = 4
MAX_CHARS = CHUNK_SIZE_TOKENS * CHARS_PER_TOKEN       # 2048 chars
OVERLAP_CHARS = CHUNK_OVERLAP_TOKENS * CHARS_PER_TOKEN # 256 chars
MIN_CHUNK_CHARS = 30

EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "paraphrase-multilingual-MiniLM-L12-v2")
VECTOR_DIM = 384

SUPPORTED_SUFFIXES = {".md", ".txt", ".yaml", ".yml"}

# 設定 Logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# 1. 資料清理層（DocumentCleaner）
# ─────────────────────────────────────────────────────────────────────────────
class DocumentCleaner:
    """負責抹平格式差異，提取純文字，並輸出至 data/processed/ (Strict Mirror)"""

    @staticmethod
    def clean_markdown(text: str) -> str:
        """保留 Code Fences (```) 與表格 (|)，僅移除 HTML 與圖片連結。"""
        text = re.sub(r"<[^>]+>", " ", text) # 移除 HTML
        text = re.sub(r"!\[([^\]]*)\]\([^\)]*\)", r"\1", text) # 移除圖片，保留 alt
        text = re.sub(r"\[([^\]]+)\]\([^\)]*\)", r"\1", text) # 移除連結，保留 text
        text = re.sub(r"\n{3,}", "\n\n", text) # 正規化空行
        return text.strip()

    @staticmethod
    def _flatten_yaml_node(data: Any, level: int = 0) -> list[str]:
        """遞迴解析 YAML AST 並轉為自然語言條列"""
        lines = []
        indent = "  " * level
        if isinstance(data, dict):
            for k, v in data.items():
                if isinstance(v, (dict, list)):
                    lines.append(f"{indent}- {k}:")
                    lines.extend(DocumentCleaner._flatten_yaml_node(v, level + 1))
                else:
                    lines.append(f"{indent}- {k}: {v}")
        elif isinstance(data, list):
            for item in data:
                if isinstance(item, (dict, list)):
                    lines.extend(DocumentCleaner._flatten_yaml_node(item, level + 1))
                else:
                    lines.append(f"{indent}- {item}")
        else:
            lines.append(f"{indent}{data}")
        return lines

    @staticmethod
    def clean_yaml(text: str, source_path: str) -> str:
        """將 D-Bus YAML 轉換為 LLM 易讀的自然語言描述 (SDD 4.2)"""
        try:
            data = yaml.safe_load(text)
            if not data:
                return ""
            
            # 樣板化描述
            lines = [f"The D-Bus interface specification for '{source_path}' is defined as follows:"]
            
            # 針對 OpenBMC phosphor-dbus-interfaces 的常見結構優化
            if isinstance(data, dict) and "description" in data:
                lines.append(f"Description: {data['description'].strip()}")
            
            lines.extend(DocumentCleaner._flatten_yaml_node(data))
            return "\n".join(lines)
        except yaml.YAMLError as e:
            log.warning(f"YAML parsing error in {source_path}, falling back to raw text: {e}")
            return text.strip()

    def clean(self, raw_text: str, suffix: str, source_path: str) -> str:
        if suffix in {".md"}:
            return self.clean_markdown(raw_text)
        elif suffix in {".yaml", ".yml"}:
            return self.clean_yaml(raw_text, source_path)
        return raw_text.strip()


# ─────────────────────────────────────────────────────────────────────────────
# 2. 語意切分層（TextChunker）
# ─────────────────────────────────────────────────────────────────────────────
class TextChunker:
    """Markdown-Aware Chunking 策略與 Context Enrichment (SDD 5.1 & 5.2)"""

    def chunk(self, text: str, source_path: str) -> list[dict]:
        # Context Enrichment Prefix
        context_prefix = f"[Context: {source_path}]\n\n"
        effective_chunk_budget = MAX_CHARS - len(context_prefix)
        
        if effective_chunk_budget <= 0:
            log.warning(f"Context prefix too long for {source_path}. Falling back to minimal context.")
            context_prefix = f"[{Path(source_path).name}]\n"
            effective_chunk_budget = MAX_CHARS - len(context_prefix)

        paragraphs = [p.strip() for p in re.split(r"\n{2,}", text) if p.strip()]
        chunks = []
        current_chunk = ""
        chunk_idx = 0
        in_code_block = False

        for para in paragraphs:
            if para.count("```") % 2 != 0:
                in_code_block = not in_code_block

            is_table = "|" in para and "\n" in para

            # 規則 1: Code fence 或 Table 盡量不切斷
            if len(para) > effective_chunk_budget and not in_code_block and not is_table:
                if current_chunk.strip():
                    chunks.append(self._make_chunk(current_chunk, context_prefix, source_path, chunk_idx))
                    chunk_idx += 1
                    current_chunk = ""
                
                for sub_chunk in self._force_split(para, effective_chunk_budget):
                    chunks.append(self._make_chunk(sub_chunk, context_prefix, source_path, chunk_idx))
                    chunk_idx += 1
                continue

            # 正常累積
            if len(current_chunk) + len(para) + 2 <= effective_chunk_budget:
                current_chunk = (current_chunk + "\n\n" + para).strip()
            else:
                # 規則 2: 若在 Code block 內，允許超過預算獨立成一個 chunk
                if in_code_block or is_table:
                    current_chunk = (current_chunk + "\n\n" + para).strip()
                else:
                    if current_chunk.strip():
                        chunks.append(self._make_chunk(current_chunk, context_prefix, source_path, chunk_idx))
                        chunk_idx += 1
                    overlap_text = current_chunk[-OVERLAP_CHARS:] if OVERLAP_CHARS > 0 else ""
                    current_chunk = (overlap_text + "\n\n" + para).strip()

        if current_chunk.strip():
            chunks.append(self._make_chunk(current_chunk, context_prefix, source_path, chunk_idx))

        # 規則 3: 過濾無意義短文本 (< 30 chars)
        return [c for c in chunks if len(c["text"]) >= MIN_CHUNK_CHARS]

    def _force_split(self, text: str, budget: int) -> Generator[str, None, None]:
        start = 0
        while start < len(text):
            end = start + budget
            yield text[start:end]
            start += budget - OVERLAP_CHARS

    @staticmethod
    def _make_chunk(text: str, prefix: str, source: str, idx: int) -> dict:
        chunk_id = f"{source}_{idx}"
        enriched_text = f"{prefix}{text.strip()}"
        return {"chunk_id": chunk_id, "text": enriched_text, "source": source, "chunk_index": idx}


# ─────────────────────────────────────────────────────────────────────────────
# 3. Embedding 層
# ─────────────────────────────────────────────────────────────────────────────
class EmbeddingEngine:
    def __init__(self, model_name: str = EMBEDDING_MODEL):
        log.info(f"Loading embedding model: {model_name} ...")
        self.model = SentenceTransformer(model_name)
        log.info(f"Model loaded. Dimension: {VECTOR_DIM}")

    def encode(self, texts: list[str]) -> list[list[float]]:
        vectors = self.model.encode(texts, batch_size=32, show_progress_bar=False)
        return vectors.tolist()


# ─────────────────────────────────────────────────────────────────────────────
# 4. Vector DB 層（pgvector）
# ─────────────────────────────────────────────────────────────────────────────
class VectorStore:
    TABLE_NAME = "chunks"

    def __init__(self, connection_string: str):
        self.conn = psycopg2.connect(connection_string)
        self._ensure_extension()
        self._ensure_table()

    def _ensure_extension(self) -> None:
        with self.conn.cursor() as cur:
            cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
        self.conn.commit()

    def _ensure_table(self) -> None:
        """Auto-Migration: 依據 SDD 6.1.1 建立 Schema，包含 fts_vector 供 Hybrid Search 使用"""
        with self.conn.cursor() as cur:
            # 1. 建立基本 Table (若完全不存在)
            cur.execute(f"""
                CREATE TABLE IF NOT EXISTS {self.TABLE_NAME} (
                    id          SERIAL PRIMARY KEY,
                    chunk_id    TEXT UNIQUE NOT NULL,
                    source      TEXT NOT NULL,
                    file_hash   TEXT NOT NULL,
                    chunk_index INT,
                    content     TEXT,
                    embedding   vector({VECTOR_DIM}),
                    created_at  TIMESTAMP DEFAULT NOW()
                );
            """)
            
            # 2. 執行 Schema Migration: 確保 fts_vector 欄位存在 (相容舊版 DB)
            cur.execute(f"""
                ALTER TABLE {self.TABLE_NAME} 
                ADD COLUMN IF NOT EXISTS fts_vector tsvector 
                GENERATED ALWAYS AS (to_tsvector('english', content)) STORED;
            """)

            # 3. 建立 IVFFLAT 向量索引 (SDD 建議 lists=20)
            cur.execute(f"""
                CREATE INDEX IF NOT EXISTS {self.TABLE_NAME}_embedding_idx
                ON {self.TABLE_NAME} USING ivfflat (embedding vector_cosine_ops)
                WITH (lists = 20);
            """)
            
            # 4. 建立 GIN 索引供全文檢索
            cur.execute(f"""
                CREATE INDEX IF NOT EXISTS {self.TABLE_NAME}_fts_idx
                ON {self.TABLE_NAME} USING gin (fts_vector);
            """)
        self.conn.commit()

    def clear_all(self) -> None:
        with self.conn.cursor() as cur:
            cur.execute(f"TRUNCATE TABLE {self.TABLE_NAME} RESTART IDENTITY;")
        self.conn.commit()
        log.info("Vector DB cleared.")

    def delete_by_source(self, source: str) -> None:
        with self.conn.cursor() as cur:
            cur.execute(f"DELETE FROM {self.TABLE_NAME} WHERE source = %s;", (source,))
        self.conn.commit()

    def insert_chunks(self, chunks: list[dict], vectors: list[list[float]], file_hash: str) -> None:
        with self.conn.cursor() as cur:
            for chunk, vector in zip(chunks, vectors):
                vec_str = f"[{','.join(map(str, vector))}]"
                cur.execute(f"""
                    INSERT INTO {self.TABLE_NAME} (chunk_id, source, file_hash, chunk_index, content, embedding)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (chunk_id) DO UPDATE
                        SET content = EXCLUDED.content,
                            embedding = EXCLUDED.embedding,
                            file_hash = EXCLUDED.file_hash,
                            created_at = NOW();
                """, (chunk["chunk_id"], chunk["source"], file_hash, chunk["chunk_index"], chunk["text"], vec_str))
        self.conn.commit()

    def get_existing_hashes(self) -> dict[str, str]:
        with self.conn.cursor() as cur:
            cur.execute(f"SELECT source, MAX(file_hash) FROM {self.TABLE_NAME} GROUP BY source;")
            return {row[0]: row[1] for row in cur.fetchall()}

    def get_all_sources(self) -> set[str]:
        with self.conn.cursor() as cur:
            cur.execute(f"SELECT DISTINCT source FROM {self.TABLE_NAME};")
            return {row[0] for row in cur.fetchall()}

    def close(self) -> None:
        self.conn.close()


# ─────────────────────────────────────────────────────────────────────────────
# 5. Pipeline 主控制器
# ─────────────────────────────────────────────────────────────────────────────
class DataUpdatePipeline:
    def __init__(self, source_dir: str, verbose: bool):
        self.source_dir = Path(source_dir)
        self.verbose = verbose
        
        connection_str = os.getenv("PGVECTOR_CONNECTION_STRING")
        if not connection_str:
            log.error("PGVECTOR_CONNECTION_STRING not set in .env")
            sys.exit(1)

        self.cleaner  = DocumentCleaner()
        self.chunker  = TextChunker()
        self.embedder = EmbeddingEngine()
        self.db       = VectorStore(connection_str)

    def _iter_raw_files(self) -> Generator[Path, None, None]:
        if not self.source_dir.exists():
            return
        for path in sorted(self.source_dir.rglob("*")):
            if path.is_file() and path.suffix.lower() in SUPPORTED_SUFFIXES:
                yield path

    def _get_processed_path(self, raw_path: Path) -> Path:
        """Strict Mirror: 嚴格保持與 raw 目錄相同的相對路徑 (SDD 4.1)"""
        relative = raw_path.relative_to(self.source_dir)
        processed_path = PROCESSED_DIR / relative.with_suffix(".txt")
        # 確保父目錄存在
        processed_path.parent.mkdir(parents=True, exist_ok=True)
        return processed_path

    def _compute_hash(self, file_path: Path) -> str:
        return hashlib.sha256(file_path.read_bytes()).hexdigest()

    def run(self, rebuild: bool = False) -> None:
        if rebuild:
            log.info("=== REBUILD MODE: Clearing DB and processed/ ===")
            self.db.clear_all()
            if PROCESSED_DIR.exists():
                shutil.rmtree(PROCESSED_DIR)
        else:
            log.info("=== INCREMENTAL UPDATE MODE ===")

        PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
        existing_hashes = self.db.get_existing_hashes()
        
        raw_files = list(self._iter_raw_files())
        if not raw_files:
            log.warning(f"No supported files found in {self.source_dir}/")
            return

        total_chunks = 0
        updated_files = 0
        current_sources = set()

        for raw_path in raw_files:
            source_label = str(raw_path.relative_to(self.source_dir))
            current_sources.add(source_label)
            current_hash = self._compute_hash(raw_path)

            if not rebuild and existing_hashes.get(source_label) == current_hash:
                if self.verbose:
                    log.debug(f"  [SKIP] {source_label} (unchanged)")
                continue

            if self.verbose:
                log.info(f"  [PROCESS] {source_label}")
                
            try:
                raw_text = raw_path.read_text(encoding="utf-8", errors="replace")
                cleaned_text = self.cleaner.clean(raw_text, raw_path.suffix.lower(), source_label)
                
                processed_path = self._get_processed_path(raw_path)
                processed_path.write_text(cleaned_text, encoding="utf-8")

                chunks = self.chunker.chunk(cleaned_text, source_label)
                if not chunks:
                    if self.verbose:
                        log.warning(f"    → Skipped (no valid chunks after cleaning)")
                    self.db.delete_by_source(source_label)
                    continue

                texts = [c["text"] for c in chunks]
                vectors = self.embedder.encode(texts)

                self.db.delete_by_source(source_label)
                self.db.insert_chunks(chunks, vectors, current_hash)

                total_chunks += len(chunks)
                updated_files += 1
                if self.verbose:
                    log.info(f"    → {len(chunks)} chunks written")

            except Exception as e:
                log.error(f"    → ERROR processing {source_label}: {e}")

        # 孤兒清理 (Orphan Cleanup) - SDD 6.1.1
        db_sources = self.db.get_all_sources()
        orphans = db_sources - current_sources
        if orphans:
            log.info(f"Cleaning up {len(orphans)} orphan sources from DB...")
            for orphan in orphans:
                self.db.delete_by_source(orphan)
                if self.verbose:
                    log.info(f"  [DELETED ORPHAN] {orphan}")

        self.db.close()
        log.info("=" * 50)
        log.info(f"Done. Updated {updated_files} file(s), wrote {total_chunks} new chunks.")


# ─────────────────────────────────────────────────────────────────────────────
# 6. CLI 入口
# ─────────────────────────────────────────────────────────────────────────────
def main() -> None:
    parser = argparse.ArgumentParser(description="OpenBMC RAG System — Data Update Pipeline")
    parser.add_argument("--rebuild", action="store_true", help="清空 DB 與 processed/ 並全量重建")
    parser.add_argument("--source-dir", type=str, default="data/raw", help="原始資料目錄 (預設: data/raw)")
    parser.add_argument("--verbose", action="store_true", help="印出每個檔案的處理狀態")
    args = parser.parse_args()

    pipeline = DataUpdatePipeline(source_dir=args.source_dir, verbose=args.verbose)
    pipeline.run(rebuild=args.rebuild)

if __name__ == "__main__":
    main()