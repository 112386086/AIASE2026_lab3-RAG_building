[![Review Assignment Due Date](https://classroom.github.com/assets/deadline-readme-button-22041afd0340ce965d47ae6ef1cefeee28c7c493a6346c4f15d667ab976d596c.svg)](https://classroom.github.com/a/mhxNhwtV)
# Build-Your-Personal-RAG


`psycopg2` 是 Python 與 PostgreSQL 資料庫之間溝通的套件。為了達到最高的執行效率，它的核心部分直接使用 C 語言編寫，以調用 PostgreSQL 的底層 C API (libpq)。使用預先編譯好的版本`psycopg2-binary`可以減少需要額外編譯或是額外設定路徑等流程。

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