# finestock
Korean Stock OpenAPI Package (LS, KIS)  
Created by alshin

---

## Table of Contents
1. [설치](#설치)
2. [사용법](#사용법)
3. [Release Notes](#release-notes)
4. [License](#license)

---

## 설치

```bash
pip install finestock
```

---

## 사용법

``` python
from finestock import StockClient

# 클라이언트 생성
client = StockClient(api_key="YOUR_KEY")

# 2025-01-01부터 2025-01-10까지 삼성전자(005930) 분봉 데이터 조회
df = client.get_minute_data("005930", start="2025-01-01", end="2025-01-10")
print(df.head())
```
