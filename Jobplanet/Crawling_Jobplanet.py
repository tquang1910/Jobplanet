from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup, Tag
from urllib.parse import quote
import re
from typing import List, Dict, Optional
import pandas as pd
from tqdm import tqdm
import time
import sys
import os
from selenium.webdriver.chrome.service import Service  # 추가


def _get_driver() -> webdriver.Chrome:
    """
    Selenium WebDriver를 생성하여 반환하는 함수.
    DevTools listening 메시지를 숨기기 위해 Service에 log_path를 설정.
    """
    options = Options()
    # 브라우저를 헤드리스 모드로 실행 (UI 없이 백그라운드에서 실행)
    # options.add_argument("--headless")
    # GPU 가속을 비활성화하여 리소스 사용을 줄임
    options.add_argument("--disable-gpu")
    # Selenium 탐지를 방지하기 위해 Blink 엔진의 자동화 관련 기능을 비활성화
    options.add_argument("--disable-blink-features=AutomationControlled")
    # 브라우저 자동화 메시지를 제거하여 탐지를 방지
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    # 자동화 확장 기능을 비활성화하여 탐지를 방지
    options.add_experimental_option("useAutomationExtension", False)
    # 브라우저의 User-Agent를 설정하여 일반적인 브라우저처럼 보이게 함
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
    )
    # 서비스 객체에 로그 경로를 os.devnull로 지정(Windows는 'NUL')
    service = Service(log_path=os.devnull)
    # service_log_path 대신 Service(log_path=…) 사용
    return webdriver.Chrome(service=service, options=options)


def fetch_search_results(company_name: str, wait_seconds: int = 20) -> BeautifulSoup:
    """
    기업명을 검색하여 검색 결과 페이지의 HTML을 BeautifulSoup 객체로 반환.
    Args:
        company_name (str): 검색할 기업명.
        wait_seconds (int): 검색 결과를 기다리는 최대 시간.
    Returns:
        BeautifulSoup: 검색 결과 페이지의 HTML을 파싱한 객체.
    """
    driver = _get_driver()
    try:
        # 검색 URL 생성
        url = f"{BASE_URL}{SEARCH_PATH}{quote(company_name)}"
        driver.get(url)  # URL로 이동
        # URL이 검색 경로를 포함할 때까지 대기
        WebDriverWait(driver, 3).until(EC.url_contains("/search/companies"))
        # 검색 결과가 로드될 때까지 대기
        WebDriverWait(driver, wait_seconds).until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, "div.searchWrap div.grid-cols-2 > a")
            )
        )
        # 페이지 소스를 BeautifulSoup 객체로 반환
        return BeautifulSoup(driver.page_source, "html.parser")
    finally:
        driver.quit()  # 브라우저 종료


def extract_company_list(soup: BeautifulSoup) -> List[Dict[str, Optional[str]]]:
    """
    검색 결과 페이지에서 기업 정보를 추출하여 리스트로 반환.
    Args:
        soup (BeautifulSoup): 검색 결과 페이지의 HTML을 파싱한 객체.
    Returns:
        List[Dict[str, Optional[str]]]: 기업 정보 리스트.
    """
    out: List[Dict[str, Optional[str]]] = []  # 결과를 저장할 리스트
    # 검색 결과 카드 선택
    cards = soup.select("div.searchWrap div.grid-cols-2 > a")
    for a in cards:
        if not isinstance(a, Tag):  # HTML 태그가 아닌 경우 건너뜀
            continue
        href = a.get("href", "")  # 링크 추출
        print("herf=", href)
        # cid = href.replace("https://www.jobplanet.co.kr/companies/", "")
        # print("cid", cid)
        cid_m = re.search(r"/companies/(\d+)", href)  # 기업 ID 추출
        print("cid-m:", cid_m)
        cid = cid_m.group(1) if cid_m else None

        print("cid", cid)
        name = a.select_one("h4").get_text(strip=True) if a.select_one("h4") else None
        rating = (
            a.select_one("div.flex.items-center > span:nth-child(2)").get_text(strip=True) 
            if a.select_one("div.flex.items-center > span:nth-child(2)") else None
        )
        print("name = ", name, "rating = ", rating)
        # 기업 정보를 딕셔너리로 저장
        out.append({"company_id": cid, "name": name, "search_rating": rating})
    return out


def fetch_company_detail(company_id: str, wait_seconds: int = 20) -> BeautifulSoup:
    """
    기업 상세 페이지를 가져와 BeautifulSoup 객체로 반환.
    Args:
        company_id (str): 기업 ID.
        wait_seconds (int): 페이지 로드를 기다리는 최대 시간.
    Returns:
        BeautifulSoup: 기업 상세 페이지의 HTML을 파싱한 객체.
    """
    driver = _get_driver()
    try:
        # 상세 페이지 URL 생성
        url = f"{BASE_URL}/companies/{company_id}"
        driver.get(url)  # URL로 이동
        # 상세 정보가 로드될 때까지 대기
        WebDriverWait(driver, wait_seconds).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "h2.stats_ttl"))
        )
        # 페이지 소스를 BeautifulSoup 객체로 반환
        return BeautifulSoup(driver.page_source, "html.parser")
    finally:
        driver.quit()  # 브라우저 종료


def extract_company_stats(soup: BeautifulSoup) -> Dict[str, Optional[str]]:
    """
    기업 상세 페이지에서 통계 정보를 추출하여 딕셔너리로 반환.
    Args:
        soup (BeautifulSoup): 기업 상세 페이지의 HTML을 파싱한 객체.
    Returns:
        Dict[str, Optional[str]]: 기업 통계 정보 딕셔너리.
    """
    stats: Dict[str, Optional[str]] = {}  # 결과를 저장할 딕셔너리
    ttl = soup.select_one("h2.stats_ttl")  # 리뷰 수가 포함된 제목 선택
    print("ttl.get_text():", ttl.get_text())
    m_cnt = re.search(r"\((\d+)명\)", ttl.get_text()) if ttl else None
    print("m_cnt:", m_cnt)
    stats["review_count"] = m_cnt.group(1) if m_cnt else None
    print("m_cnt.group(1):", m_cnt.group(1))

    #다른 방법(replace 이용)
    '''
    ttl_text = ttl.get_text()
    m_cnt = ttl_text.replace("전체 리뷰 통계 (", "").replace("명)", "")
    print(m_cnt)
    '''
    overall = soup.select_one("div.rate_star_top span.rate_point")  # 전체 평점 선택
    stats["overall_rating"] = overall.get_text(strip=True) if overall else None
    # 세부 평점 정보 추출
    for bar in soup.select("div.rate_bar_group > div"):
        title_tag = bar.select_one("div.rate_bar_title")
        point_tag = bar.select_one("span.txt_point")
        if title_tag and point_tag:
            key = title_tag.get_text(strip=True)
            stats[key] = point_tag.get_text(strip=True)
    # 추가 평점 정보 추출
    for pie in soup.select("div.rate_pie_set"):
        label_tag = pie.select_one("div.rate_label")
        point_tag = pie.select_one("span.txt_point")
        if label_tag and point_tag:
            stats[label_tag.get_text(strip=True)] = point_tag.get_text(strip=True)
    return stats


def save_progress(data: List[Dict], filename: str = "jobplanet_crawling_progress.csv"):
    """
    크롤링 진행 데이터를 CSV 파일로 저장.
    Args:
        data (List[Dict]): 저장할 데이터 리스트.
        filename (str): 저장할 파일 이름.
    """
    df = pd.DataFrame(data)  # 데이터를 DataFrame으로 변환
    df.to_csv(filename, index=False, encoding="utf-8-sig")  # CSV 파일로 저장


def load_progress(
    info_file="jobplanet_crawling_progress.csv",
    error_file="jobplanet_crawling_error.csv",
):
    """
    이전 크롤링 진행 데이터를 로드.
    Args:
        info_file (str): 진행 데이터 파일 이름.
        error_file (str): 에러 데이터 파일 이름.
    Returns:
        Tuple[List[Dict], List[Dict]]: 진행 데이터와 에러 데이터 리스트.
    """
    all_companies_info = []  # 진행 데이터 초기화
    error_list = []  # 에러 데이터 초기화
    if os.path.exists(info_file):  # 진행 데이터 파일이 존재하면 로드
        all_companies_info = (
            pd.read_csv(info_file, dtype=str).fillna("").to_dict(orient="records")
        )
    if os.path.exists(error_file):  # 에러 데이터 파일이 존재하면 로드
        error_list = (
            pd.read_csv(error_file, dtype=str).fillna("").to_dict(orient="records")
        )
    return all_companies_info, error_list



if __name__ == "__main__":
    
    # JobPlanet 웹사이트의 기본 URL
    BASE_URL = "https://www.jobplanet.co.kr"
    # 검색 경로를 정의 (기업명 검색 시 사용)
    SEARCH_PATH = "/search/companies?query="

    # 대상 기업 데이터를 읽어옴
    target_companies = pd.read_csv("enterprise_df_10k_utf8_data.csv", encoding="utf-8")
    # 기업명만 추출하여 중복 제거
    target_companies_name = target_companies[target_companies['담당'] == '1번']['기업명'].dropna().unique().tolist()
    # 기업명을 데이터프레임으로 변환
    target_companies_name = pd.DataFrame(target_companies_name, columns=["기업명"])
    # 메인 실행 코드: 크롤링 진행
    # 최초에는 all_comoanies_info = [], error_list = []
    all_companies_info, error_list = load_progress()  # 기존 데이터 로드
    done_names = (
        set([d["검색기업명"] for d in all_companies_info])
        if all_companies_info
        else set()
    )
    done_names.update([d["기업명"] for d in error_list])  # 에러로 끝난 기업도 스킵

    save_every = 10  # 진행상황 저장 주기

    tqdm_out = sys.stdout if sys.stdout.isatty() else open("progress.log", "a")
    for idx, row in tqdm(
        target_companies_name.iterrows(),
        total=len(target_companies_name),
        desc="기업별 크롤링",
        file=tqdm_out,
    ):
        company = row["기업명"]  #LG전자
        if company in done_names:
            continue  # 이미 처리된 기업은 건너뜀
        try:
            search_soup = fetch_search_results(company)  # 검색 결과 가져오기
            companies = extract_company_list(
                search_soup
            )  # 검색 결과에서 기업 리스트 추출
            if not companies:
                error_list.append({"기업명": company, "error": "검색결과 없음"})
                continue
            # 첫 번째 검색 결과만 사용 (정확도 우선)
            info = companies[0]
            cid = info.get("company_id")
            if cid:
                detail_soup = fetch_company_detail(cid)  # 상세 정보 가져오기
                stats = extract_company_stats(detail_soup)  # 상세 정보에서 통계 추출
                info.update(stats)
            info["검색기업명"] = company
            all_companies_info.append(info)
        except Exception as e:
            error_list.append({"기업명": company, "error": str(e)})
        # 주기적으로 저장
        if (idx + 1) % save_every == 0:
            save_progress(all_companies_info, "jobplanet_crawling_progress.csv")
            save_progress(error_list, "jobplanet_crawling_error.csv")
        # 중간저장: 강제 종료 대비
        if (idx + 1) % 50 == 0:
            save_progress(
                all_companies_info, f"jobplanet_crawling_progress_{idx+1}.csv"
            )
            save_progress(error_list, f"jobplanet_crawling_error_{idx+1}.csv")
        time.sleep(1)  # 서버 부하 방지

    # 마지막 저장
    save_progress(all_companies_info, "jobplanet_crawling_progress.csv")
    save_progress(error_list, "jobplanet_crawling_error.csv")
