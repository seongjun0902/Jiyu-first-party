#!/usr/bin/env python3
"""국가법령정보시스템 OPEN API 조회 헬퍼.

국가법령정보 공동활용(OPEN API)을 통해 법령 검색 / 조문 조회 / 법령해석례 검색을 한다.

사전 준비:
  1. https://open.law.go.kr 에서 OPEN API 사용 신청 (이메일 무료).
  2. 발급받은 OC 키(신청한 이메일의 @ 앞부분)를 환경변수로 설정:
        export LAW_OC="your_id"
  3. 실행:
        python3 law_search.py search "부가가치세법"
        python3 law_search.py article --mst 267581 --jo 39
        python3 law_search.py interp "매입세액 불공제"

OC 키가 없으면 안내 메시지를 출력하고 종료한다(그 경우 SKILL.md의 웹 조회 폴백 사용).
"""
import argparse
import json
import os
import sys
import urllib.parse
import urllib.request

BASE_SEARCH = "https://www.law.go.kr/DRF/lawSearch.do"
BASE_SERVICE = "https://www.law.go.kr/DRF/lawService.do"
TIMEOUT = 20


def get_oc():
    oc = os.environ.get("LAW_OC", "").strip()
    if not oc:
        sys.stderr.write(
            "[안내] 환경변수 LAW_OC 가 설정되지 않았습니다.\n"
            "  https://open.law.go.kr 에서 OPEN API 신청 후 발급받은 OC 키를 설정하세요:\n"
            '      export LAW_OC="발급받은ID"\n'
            "  키 없이 진행하려면 SKILL.md의 웹 조회(WebFetch/WebSearch) 폴백을 사용하세요.\n"
        )
        sys.exit(2)
    return oc


def fetch(url, params):
    qs = urllib.parse.urlencode(params, encoding="utf-8")
    full = f"{url}?{qs}"
    req = urllib.request.Request(full, headers={"User-Agent": "tax-law-advisor/1.0"})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        raw = resp.read().decode("utf-8", errors="replace")
    return full, raw


def cmd_search(args):
    """법령 검색 → 법령명 / 법령ID / 법령일련번호(MST) / 공포일자 목록."""
    oc = get_oc()
    params = {
        "OC": oc,
        "target": "law",
        "type": "JSON",
        "query": args.query,
        "display": str(args.display),
    }
    url, raw = fetch(BASE_SEARCH, params)
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        print(f"[요청] {url}\n[원시응답]\n{raw[:3000]}")
        return
    laws = data.get("LawSearch", {}).get("law", [])
    if isinstance(laws, dict):
        laws = [laws]
    if not laws:
        print(f"검색 결과 없음. (요청: {url})")
        return
    print(f"'{args.query}' 검색 결과 {len(laws)}건:\n")
    for it in laws:
        print(
            f"- {it.get('법령명한글','?')} "
            f"[법령ID {it.get('법령ID','?')} / MST {it.get('법령일련번호','?')}] "
            f"공포 {it.get('공포일자','?')} 시행 {it.get('시행일자','?')}"
        )
    print("\n→ 본문/조문 조회: python3 law_search.py article --mst <MST> [--jo <조번호>]")


def cmd_article(args):
    """법령 본문/조문 조회 (MST 또는 ID 기준)."""
    oc = get_oc()
    params = {"OC": oc, "target": "law", "type": "JSON"}
    if args.mst:
        params["MST"] = args.mst
    elif args.law_id:
        params["ID"] = args.law_id
    else:
        sys.stderr.write("--mst 또는 --id 중 하나가 필요합니다.\n")
        sys.exit(1)
    if args.jo:
        # 조번호는 6자리(조4+가지2). 예: 39조 -> 003900
        params["JO"] = f"{int(args.jo):04d}00"
    url, raw = fetch(BASE_SERVICE, params)
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        print(f"[요청] {url}\n[원시응답]\n{raw[:5000]}")
        return
    print(f"[요청] {url}\n")
    print(json.dumps(data, ensure_ascii=False, indent=2)[:8000])


def cmd_interp(args):
    """법령해석례(유권해석) 검색."""
    oc = get_oc()
    params = {
        "OC": oc,
        "target": "expc",  # 법령해석례
        "type": "JSON",
        "query": args.query,
        "display": str(args.display),
    }
    url, raw = fetch(BASE_SEARCH, params)
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        print(f"[요청] {url}\n[원시응답]\n{raw[:3000]}")
        return
    items = data.get("LawSearch", {}).get("expc", [])
    if isinstance(items, dict):
        items = [items]
    if not items:
        print(f"해석례 결과 없음. (요청: {url})")
        return
    print(f"'{args.query}' 법령해석례 {len(items)}건:\n")
    for it in items:
        print(
            f"- {it.get('안건명','?')} "
            f"[{it.get('해석기관명','?')} / {it.get('회신일자','?')}] "
            f"ID {it.get('법령해석례일련번호','?')}"
        )


def main():
    p = argparse.ArgumentParser(description="국가법령정보 OPEN API 조회 헬퍼")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("search", help="법령 검색")
    s.add_argument("query")
    s.add_argument("--display", type=int, default=20)
    s.set_defaults(func=cmd_search)

    a = sub.add_parser("article", help="법령 본문/조문 조회")
    a.add_argument("--mst", help="법령일련번호(MST)")
    a.add_argument("--id", dest="law_id", help="법령ID")
    a.add_argument("--jo", help="조 번호 (예: 39)")
    a.set_defaults(func=cmd_article)

    i = sub.add_parser("interp", help="법령해석례 검색")
    i.add_argument("query")
    i.add_argument("--display", type=int, default=20)
    i.set_defaults(func=cmd_interp)

    args = p.parse_args()
    try:
        args.func(args)
    except urllib.error.URLError as e:
        sys.stderr.write(f"[네트워크 오류] {e}\n국가법령정보시스템 접속 실패 → 웹 조회 폴백을 사용하세요.\n")
        sys.exit(3)


if __name__ == "__main__":
    main()
