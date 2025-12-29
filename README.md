# 簡易物流倉儲管理系統 (WMS)


## 後端開發環境
- Python (使用 `uv` 管理)
- 框架: FastAPI
- 資料庫: PostgreSQL (生產環境) / SQLite (開發環境, 可以先不用有資料庫, 站存在記憶體中, 其他合作的同學可以不用先建立資料庫)
- ORM: SQLModel

## 快速啟動-初次 (MacOS)
0. 打開終端機
1. 安裝 uv (若尚未安裝): `curl -LsSf https://astral.sh/uv/install.sh | sh`
2. 到專案目錄下
3. 複製配置檔 `cp .env.example .env`
4. 建立虛擬環境(若尚未建立) `uv venv`
5. 激活虛擬環境 `source ./.venv/bin/activate`
6. 同步依賴: `uv sync`
7. 啟動伺服器: `uv run uvicorn app.main:app --reload`

## 更新
0. 打開終端機
1. 到專案目錄下
2. 將程式碼更新到最新 `git pull origin main`
3. 激活虛擬環境(若尚未激活) `source ./.venv/bin/activate`
4. 同步依賴: `uv sync`
5. 啟動伺服器: `uv run uvicorn app.main:app --reload`

## API 文件
啟動後訪問: `http://127.0.0.1:8000/docs`

## 使用 API 

例如在前端使用原生的 javascript fetch api 拿取商品清單

```javascript
const requestOptions = {
  method: "GET",
  redirect: "follow"
};

fetch("http://127.0.0.1:8000/api/v1/products/", requestOptions)
  .then((response) => response.text())
  .then((result) => console.log(result))
  .catch((error) => console.error(error));
```

## 連線資料庫

.env.example 為範例請直接使用
建立 .env (你自己用) 複製一份 .env.example 改名為 .env。初期開發我們先用 SQLite 即可，設定 APP_ENV=development。

0. 打開終端機
1. 到專案目錄下
```bash
cp .env.example .env
```

開發模式：使用 SQLite (推薦開發初期使用)
在 .env 中設定 APP_ENV=development。 系統會自動在根目錄建立 local_dev.db，無需安裝任何額外軟體。

正式模式：使用 PostgreSQL
在 .env 中設定 APP_ENV=production。 但必須要有資料庫, 如果沒有可以透過專案底下的 docker-compose.yml 安裝

1. (若尚本機未安裝資料庫) 確保已安裝 Docker 與 Docker Compose。
2. 啟動資料庫容器: `docker-compose up -d`