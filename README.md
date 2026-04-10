[![Review Assignment Due Date](https://classroom.github.com/assets/deadline-readme-button-22041afd0340ce965d47ae6ef1cefeee28c7c493a6346c4f15d667ab976d596c.svg)](https://classroom.github.com/a/mhxNhwtV)
# Build-Your-Personal-RAG




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