# scripts

## law_search.py — 국가법령정보 OPEN API 헬퍼

### OC 키 발급 (1회, 무료)
1. https://open.law.go.kr 접속 → 회원가입/로그인
2. "OPEN API 신청" → 이메일로 신청
3. **OC 키 = 신청한 이메일의 `@` 앞부분** (예: `hong@abc.com` → `hong`)

### 환경변수 설정
```bash
export LAW_OC="발급받은ID"   # ~/.zshrc 또는 ~/.bashrc 에 추가하면 편함
```

### 사용
```bash
python3 law_search.py search "부가가치세법"          # 법령 검색
python3 law_search.py article --mst <MST> --jo 39    # 특정 조문 조회
python3 law_search.py interp "매입세액 불공제"        # 법령해석례 검색
```

`LAW_OC` 미설정 시 안내 후 종료 → 그 경우 웹 조회(WebFetch/WebSearch) 폴백 사용.
의존성 없음(Python 3 표준 라이브러리만 사용).
