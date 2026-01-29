"""
KIS API 클라이언트
한국투자증권 API와의 통합을 위한 자체 구현 클라이언트
참조: /Users/harvey/workspace/lsmr-quant-strategy/open-trading-api
"""

import json
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from config.settings import KISConfig
from utils.error_handling import (
    KISAPIError,
    AuthenticationError,
    RateLimitError,
    NetworkError,
    DataProcessingError,
    retry_with_backoff
)


logger = logging.getLogger(__name__)


class AccountType(Enum):
    """계정 유형"""
    REAL = "real"      # 실전투자
    VIRTUAL = "virtual"  # 모의투자


@dataclass
class TokenInfo:
    """토큰 정보"""
    access_token: str
    token_type: str
    expires_at: datetime
    
    def is_expired(self) -> bool:
        """토큰 만료 여부 확인"""
        # 만료 5분 전에 갱신하도록 여유 시간 설정
        return datetime.now() >= (self.expires_at - timedelta(minutes=5))


@dataclass
class IndexData:
    """지수 데이터"""
    index_code: str
    index_name: str
    current_price: float
    change_rate: float
    volume: int
    timestamp: datetime
    ma20: float = 0.0  # 20일 이동평균 추가
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            'index_code': self.index_code,
            'index_name': self.index_name,
            'current_price': self.current_price,
            'change_rate': self.change_rate,
            'volume': self.volume,
            'timestamp': self.timestamp.isoformat(),
            'ma20': self.ma20
        }


@dataclass
class StockData:
    """종목 데이터"""
    ticker: str
    stock_name: str
    current_price: float
    change_rate: float
    volume: int
    market_cap: Optional[float] = None
    sector: Optional[str] = None
    timestamp: Optional[datetime] = None


@dataclass
class PriceData:
    """가격 데이터 (과거 데이터용)"""
    date: str
    open_price: float
    high_price: float
    low_price: float
    close_price: float
    volume: int


class KISClient:
    """
    KIS API 클라이언트
    
    요구사항:
    - 9.1: 참조 라이브러리 패턴 기반 자체 구현
    - 9.2: 토큰 기반 인증
    - 9.3: REST 엔드포인트 구현
    - 9.6: JSON 응답 파싱 및 오류 처리
    - 9.7: 속도 제한 및 재시도 메커니즘
    - 10.2, 10.3: 계정 유형별 엔드포인트 선택
    """
    
    # API 엔드포인트 (요구사항 10.2, 10.3)
    REAL_BASE_URL = "https://openapi.koreainvestment.com:9443"
    VIRTUAL_BASE_URL = "https://openapivts.koreainvestment.com:29443"
    
    # TR ID 매핑
    TR_IDS = {
        # 지수 조회
        "kospi_index": "FHKUP03500100",      # KOSPI 지수 시세
        "kosdaq_index": "FHKUP03500100",     # KOSDAQ 지수 시세 (동일 TR, 파라미터로 구분)
        
        # 종목 조회
        "stock_price": "FHKST01010100",      # 주식 현재가 시세
        "stock_daily": "FHKST01010400",      # 주식 일별 시세
        
        # 섹터 조회
        "sector_stocks": "FHKST01010900",    # 업종별 종목 시세
        "sector_index": "FHKUP03500100",     # 업종 지수 시세
        
        # 거래량 순위
        "volume_rank": "FHKST01010800",      # 거래량 순위
    }
    
    def __init__(self, config: KISConfig, account_type: AccountType = AccountType.VIRTUAL):
        """
        KIS API 클라이언트 초기화
        
        Args:
            config: KIS API 설정
            account_type: 계정 유형 (real/virtual)
        """
        self.config = config
        self.account_type = account_type
        self._token: Optional[TokenInfo] = None
        self._session = self._create_session()
        
        # 계정 유형에 따른 base URL 설정 (요구사항 10.2, 10.3)
        self.base_url = (
            self.REAL_BASE_URL if account_type == AccountType.REAL 
            else self.VIRTUAL_BASE_URL
        )
        
        # 속도 제한 관리 (요구사항 9.7)
        self._last_request_time = 0
        self._min_request_interval = 0.05  # 50ms (초당 20회)
        self._request_count = 0
        self._rate_limit_reset_time = time.time()
        
        logger.info(
            f"KIS API 클라이언트 초기화 완료 - "
            f"계정 유형: {account_type.value}, "
            f"Base URL: {self.base_url}"
        )
    
    def _create_session(self) -> requests.Session:
        """HTTP 세션 생성 (재시도 로직 포함)"""
        session = requests.Session()
        
        # 재시도 전략 설정 (요구사항 9.7)
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST"]
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        
        return session
    
    def _get_headers(self, tr_id: str, tr_cont: str = "") -> Dict[str, str]:
        """API 요청 헤더 생성"""
        if not self._token or self._token.is_expired():
            raise AuthenticationError("토큰이 만료되었거나 존재하지 않습니다. authenticate()를 먼저 호출하세요.")
        
        return {
            "Content-Type": "application/json",
            "authorization": f"Bearer {self._token.access_token}",
            "appkey": self.config.app_key,
            "appsecret": self.config.app_secret,
            "tr_id": tr_id,
            "custtype": "P",  # 개인
            "tr_cont": tr_cont,
        }
    
    def _rate_limit_check(self):
        """속도 제한 확인 및 대기 (요구사항 9.7)"""
        current_time = time.time()
        
        # 1초당 요청 수 제한 (초당 20회)
        if current_time - self._rate_limit_reset_time >= 1.0:
            self._request_count = 0
            self._rate_limit_reset_time = current_time
        
        if self._request_count >= 20:
            sleep_time = 1.0 - (current_time - self._rate_limit_reset_time)
            if sleep_time > 0:
                logger.debug(f"속도 제한 도달, {sleep_time:.2f}초 대기")
                time.sleep(sleep_time)
                self._request_count = 0
                self._rate_limit_reset_time = time.time()
        
        # 최소 요청 간격 확인
        elapsed = current_time - self._last_request_time
        if elapsed < self._min_request_interval:
            sleep_time = self._min_request_interval - elapsed
            time.sleep(sleep_time)
        
        self._last_request_time = time.time()
        self._request_count += 1
    
    @retry_with_backoff(max_retries=3, base_delay=1.0)
    def authenticate(self) -> bool:
        """
        KIS API 인증 및 토큰 발급 (요구사항 9.2)
        
        Returns:
            인증 성공 여부
        
        Raises:
            AuthenticationError: 인증 실패 시
        """
        try:
            url = f"{self.base_url}/oauth2/tokenP"
            
            payload = {
                "grant_type": "client_credentials",
                "appkey": self.config.app_key,
                "appsecret": self.config.app_secret,
            }
            
            headers = {
                "Content-Type": "application/json",
            }
            
            logger.info("KIS API 인증 시도...")
            response = self._session.post(
                url,
                data=json.dumps(payload),
                headers=headers,
                timeout=10
            )
            
            if response.status_code != 200:
                raise AuthenticationError(
                    f"인증 실패 - 상태 코드: {response.status_code}, "
                    f"응답: {response.text}"
                )
            
            data = response.json()
            
            # 토큰 정보 저장
            self._token = TokenInfo(
                access_token=data["access_token"],
                token_type=data.get("token_type", "Bearer"),
                expires_at=datetime.strptime(
                    data["access_token_token_expired"],
                    "%Y-%m-%d %H:%M:%S"
                )
            )
            
            logger.info(
                f"KIS API 인증 성공 - "
                f"토큰 만료: {self._token.expires_at.strftime('%Y-%m-%d %H:%M:%S')}"
            )
            
            return True
            
        except requests.exceptions.RequestException as e:
            raise NetworkError(f"네트워크 오류: {e}")
        except KeyError as e:
            raise AuthenticationError(f"응답 파싱 오류: {e}")
        except Exception as e:
            raise AuthenticationError(f"인증 중 예상치 못한 오류: {e}")
    
    def _make_request(
        self,
        method: str,
        endpoint: str,
        tr_id: str,
        params: Optional[Dict] = None,
        data: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        API 요청 실행 (공통 로직)
        
        Args:
            method: HTTP 메서드 (GET/POST)
            endpoint: API 엔드포인트
            tr_id: TR ID
            params: 쿼리 파라미터
            data: 요청 본문
        
        Returns:
            API 응답 데이터
        
        Raises:
            KISAPIError: API 오류 시
        """
        # 속도 제한 확인
        self._rate_limit_check()
        
        # 토큰 만료 확인 및 재인증
        if not self._token or self._token.is_expired():
            logger.info("토큰 만료, 재인증 시도...")
            self.authenticate()
        
        url = f"{self.base_url}{endpoint}"
        headers = self._get_headers(tr_id)
        
        try:
            if method.upper() == "GET":
                response = self._session.get(
                    url,
                    headers=headers,
                    params=params,
                    timeout=10
                )
            else:
                response = self._session.post(
                    url,
                    headers=headers,
                    data=json.dumps(data) if data else None,
                    timeout=10
                )
            
            # 응답 상태 코드 확인
            if response.status_code == 429:
                raise RateLimitError("API 속도 제한 초과")
            elif response.status_code != 200:
                raise KISAPIError(
                    f"API 오류 - 상태 코드: {response.status_code}, "
                    f"응답: {response.text}"
                )
            
            # JSON 파싱 (요구사항 9.6)
            result = response.json()
            
            # 응답 코드 확인
            rt_cd = result.get("rt_cd", "")
            if rt_cd != "0":
                msg_cd = result.get("msg_cd", "")
                msg1 = result.get("msg1", "")
                raise KISAPIError(
                    f"API 오류 - rt_cd: {rt_cd}, msg_cd: {msg_cd}, msg: {msg1}"
                )
            
            return result
            
        except requests.exceptions.Timeout:
            raise NetworkError("요청 시간 초과")
        except requests.exceptions.RequestException as e:
            raise NetworkError(f"네트워크 오류: {e}")
        except json.JSONDecodeError as e:
            raise DataProcessingError(f"JSON 파싱 오류: {e}")
    
    async def get_index_data(self, index_code: str) -> IndexData:
        """
        지수 데이터 조회 (요구사항 9.3)
        
        Args:
            index_code: 지수 코드 (0001: KOSPI, 1001: KOSDAQ)
        
        Returns:
            지수 데이터 (20일 이동평균 포함)
        """
        try:
            # 현재 지수 데이터 조회
            endpoint = "/uapi/domestic-stock/v1/quotations/inquire-index-price"
            tr_id = self.TR_IDS["kospi_index"]
            
            params = {
                "fid_cond_mrkt_div_code": "U",  # 업종
                "fid_input_iscd": index_code,
            }
            
            result = self._make_request("GET", endpoint, tr_id, params=params)
            
            # 응답 데이터 파싱
            output = result.get("output", {})
            current_price = float(output.get("bstp_nmix_prpr", 0))
            
            # 20일 이동평균 계산을 위한 과거 데이터 조회
            historical_data = await self.get_index_historical_data(index_code, days=20)
            
            # 20일 이동평균 계산
            if len(historical_data) >= 20:
                ma20 = sum(data.close_price for data in historical_data[:20]) / 20
            else:
                # 데이터가 부족한 경우 현재가 사용
                ma20 = current_price
                logger.warning(f"지수 {index_code} 과거 데이터 부족, 현재가를 MA20으로 사용")
            
            return IndexData(
                index_code=index_code,
                index_name=output.get("bstp_nmix_prpr", ""),
                current_price=current_price,
                change_rate=float(output.get("bstp_nmix_prdy_vrss_sign", 0)),
                volume=int(output.get("acml_vol", 0)),
                timestamp=datetime.now(),
                ma20=ma20
            )
            
        except Exception as e:
            logger.error(f"지수 데이터 조회 오류 ({index_code}): {e}")
            raise
    
    def get_stock_data(self, ticker: str) -> StockData:
        """
        종목 데이터 조회 (요구사항 9.3)
        
        Args:
            ticker: 종목 코드
        
        Returns:
            종목 데이터
        """
        try:
            endpoint = "/uapi/domestic-stock/v1/quotations/inquire-price"
            tr_id = self.TR_IDS["stock_price"]
            
            params = {
                "fid_cond_mrkt_div_code": "J",  # 주식
                "fid_input_iscd": ticker,
            }
            
            result = self._make_request("GET", endpoint, tr_id, params=params)
            
            # 응답 데이터 파싱
            output = result.get("output", {})
            
            return StockData(
                ticker=ticker,
                stock_name=output.get("prdt_name", ""),
                current_price=float(output.get("stck_prpr", 0)),
                change_rate=float(output.get("prdy_ctrt", 0)),
                volume=int(output.get("acml_vol", 0)),
                timestamp=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"종목 데이터 조회 오류 ({ticker}): {e}")
            raise
    
    def get_historical_data(self, ticker: str, days: int = 20) -> List[PriceData]:
        """
        과거 가격 데이터 조회 (요구사항 9.3)
        
        Args:
            ticker: 종목 코드
            days: 조회 일수
        
        Returns:
            과거 가격 데이터 리스트
        """
        try:
            endpoint = "/uapi/domestic-stock/v1/quotations/inquire-daily-price"
            tr_id = self.TR_IDS["stock_daily"]
            
            params = {
                "fid_cond_mrkt_div_code": "J",
                "fid_input_iscd": ticker,
                "fid_period_div_code": "D",  # 일별
                "fid_org_adj_prc": "0",      # 수정주가 미적용
            }
            
            result = self._make_request("GET", endpoint, tr_id, params=params)
            
            # 응답 데이터 파싱
            output_list = result.get("output", [])
            
            price_data_list = []
            for item in output_list[:days]:
                price_data_list.append(PriceData(
                    date=item.get("stck_bsop_date", ""),
                    open_price=float(item.get("stck_oprc", 0)),
                    high_price=float(item.get("stck_hgpr", 0)),
                    low_price=float(item.get("stck_lwpr", 0)),
                    close_price=float(item.get("stck_clpr", 0)),
                    volume=int(item.get("acml_vol", 0))
                ))
            
            return price_data_list
            
        except Exception as e:
            logger.error(f"과거 가격 데이터 조회 오류 ({ticker}): {e}")
            raise
    
    async def get_index_historical_data(self, index_code: str, days: int = 20) -> List[PriceData]:
        """
        지수 과거 데이터 조회
        
        Args:
            index_code: 지수 코드 (0001: KOSPI, 1001: KOSDAQ)
            days: 조회 일수
        
        Returns:
            과거 가격 데이터 리스트
        """
        try:
            endpoint = "/uapi/domestic-stock/v1/quotations/inquire-daily-indexchartprice"
            tr_id = "FHKUP03500100"
            
            params = {
                "fid_cond_mrkt_div_code": "U",
                "fid_input_iscd": index_code,
                "fid_input_date_1": "",  # 시작일 (빈 값이면 최근부터)
                "fid_input_date_2": "",  # 종료일
                "fid_period_div_code": "D",  # 일별
            }
            
            result = self._make_request("GET", endpoint, tr_id, params=params)
            
            # 응답 데이터 파싱
            output_list = result.get("output2", [])
            
            price_data_list = []
            for item in output_list[:days]:
                price_data_list.append(PriceData(
                    date=item.get("stck_bsop_date", ""),
                    open_price=float(item.get("bstp_nmix_oprc", 0)),
                    high_price=float(item.get("bstp_nmix_hgpr", 0)),
                    low_price=float(item.get("bstp_nmix_lwpr", 0)),
                    close_price=float(item.get("bstp_nmix_clpr", 0)),
                    volume=int(item.get("acml_vol", 0))
                ))
            
            return price_data_list
            
        except Exception as e:
            logger.error(f"지수 과거 데이터 조회 오류 ({index_code}): {e}")
            raise
    
    def get_sector_stocks(
        self,
        sector_code: str,
        sort_by: str = "volume",
        limit: int = 5
    ) -> List[StockData]:
        """
        섹터별 종목 조회 (요구사항 9.3)
        
        Args:
            sector_code: 섹터 코드
            sort_by: 정렬 기준 (volume: 거래량, price: 가격)
            limit: 조회 개수
        
        Returns:
            종목 데이터 리스트
        """
        try:
            endpoint = "/uapi/domestic-stock/v1/quotations/inquire-sector-price"
            tr_id = self.TR_IDS["sector_stocks"]
            
            params = {
                "fid_cond_mrkt_div_code": "U",
                "fid_input_iscd": sector_code,
            }
            
            result = self._make_request("GET", endpoint, tr_id, params=params)
            
            # 응답 데이터 파싱
            output_list = result.get("output", [])
            
            stock_list = []
            for item in output_list[:limit]:
                stock_list.append(StockData(
                    ticker=item.get("stck_shrn_iscd", ""),
                    stock_name=item.get("hts_kor_isnm", ""),
                    current_price=float(item.get("stck_prpr", 0)),
                    change_rate=float(item.get("prdy_ctrt", 0)),
                    volume=int(item.get("acml_vol", 0)),
                    sector=sector_code
                ))
            
            # 정렬
            if sort_by == "volume":
                stock_list.sort(key=lambda x: x.volume, reverse=True)
            
            return stock_list[:limit]
            
        except Exception as e:
            logger.error(f"섹터 종목 조회 오류 ({sector_code}): {e}")
            raise
    
    def get_volume_rank(self, market: str = "ALL", limit: int = 100) -> List[StockData]:
        """
        거래량 순위 조회 (요구사항 9.3)
        
        Args:
            market: 시장 구분 (KOSPI/KOSDAQ/ALL)
            limit: 조회 개수
        
        Returns:
            종목 데이터 리스트 (거래량 순)
        """
        try:
            endpoint = "/uapi/domestic-stock/v1/quotations/volume-rank"
            tr_id = self.TR_IDS["volume_rank"]
            
            # 시장 구분 코드 매핑
            market_code_map = {
                "KOSPI": "0",
                "KOSDAQ": "1",
                "ALL": ""
            }
            
            params = {
                "fid_cond_mrkt_div_code": "J",
                "fid_cond_scr_div_code": "20171",
                "fid_input_iscd": "0000",
                "fid_div_cls_code": "0",
                "fid_blng_cls_code": market_code_map.get(market, ""),
                "fid_trgt_cls_code": "111111111",
                "fid_trgt_exls_cls_code": "000000",
                "fid_input_price_1": "",
                "fid_input_price_2": "",
                "fid_vol_cnt": "",
                "fid_input_date_1": "",
            }
            
            result = self._make_request("GET", endpoint, tr_id, params=params)
            
            # 응답 데이터 파싱
            output_list = result.get("output", [])
            
            stock_list = []
            for item in output_list[:limit]:
                stock_list.append(StockData(
                    ticker=item.get("stck_shrn_iscd", ""),
                    stock_name=item.get("hts_kor_isnm", ""),
                    current_price=float(item.get("stck_prpr", 0)),
                    change_rate=float(item.get("prdy_ctrt", 0)),
                    volume=int(item.get("acml_vol", 0))
                ))
            
            return stock_list
            
        except Exception as e:
            logger.error(f"거래량 순위 조회 오류: {e}")
            raise
    
    async def get_sector_data(self, sector_code: str) -> Dict[str, Any]:
        """
        섹터 데이터 조회 (4-way 분석용)
        
        Args:
            sector_code: 섹터 코드
        
        Returns:
            섹터 분석 데이터 (가격, 수급, 확산, 상대강도 정보 포함)
        """
        try:
            # 섹터 지수 데이터 조회
            endpoint = "/uapi/domestic-stock/v1/quotations/inquire-index-price"
            tr_id = "FHKUP03500100"
            
            params = {
                "fid_cond_mrkt_div_code": "U",
                "fid_input_iscd": sector_code,
            }
            
            result = self._make_request("GET", endpoint, tr_id, params=params)
            output = result.get("output", {})
            
            # 현재가 및 변화율
            current_price = float(output.get("bstp_nmix_prpr", 0))
            change_rate = float(output.get("prdy_ctrt", 0))
            
            # 과거 데이터 조회 (이동평균 계산용)
            historical_data = await self._get_sector_historical_data(sector_code, days=60)
            
            # 이동평균 계산
            ma5 = self._calculate_moving_average(historical_data, 5)
            ma20 = self._calculate_moving_average(historical_data, 20)
            ma60 = self._calculate_moving_average(historical_data, 60)
            
            # 52주 고점
            high_52week = max([d.high_price for d in historical_data]) if historical_data else current_price
            
            # 섹터 내 종목 데이터 조회
            sector_stocks = self.get_sector_stocks(sector_code, limit=50)
            
            # 확산 분석 (상승/하락 종목 수)
            advancing_stocks = sum(1 for s in sector_stocks if s.change_rate > 0)
            declining_stocks = sum(1 for s in sector_stocks if s.change_rate < 0)
            
            # 외국인/기관 순매수 데이터 (모의 데이터 - 실제 API 엔드포인트 필요)
            foreign_net_buy_days = await self._get_foreign_net_buy_days(sector_code)
            institution_net_buy_days = await self._get_institution_net_buy_days(sector_code)
            
            # 시장 대비 수익률 (KOSPI 대비)
            market_index = await self.get_index_data("0001")  # KOSPI
            market_return = market_index.change_rate
            
            return {
                'sector_code': sector_code,
                'current_price': current_price,
                'change_rate': change_rate,
                'ma5': ma5,
                'ma20': ma20,
                'ma60': ma60,
                'high_52week': high_52week,
                'advancing_stocks': advancing_stocks,
                'declining_stocks': declining_stocks,
                'foreign_net_buy_days': foreign_net_buy_days,
                'institution_net_buy_days': institution_net_buy_days,
                'return_rate': change_rate,
                'market_return': market_return,
            }
            
        except Exception as e:
            logger.error(f"섹터 데이터 조회 오류 ({sector_code}): {e}")
            raise
    
    async def _get_sector_historical_data(self, sector_code: str, days: int = 60) -> List[PriceData]:
        """
        섹터 과거 데이터 조회
        
        Args:
            sector_code: 섹터 코드
            days: 조회 일수
        
        Returns:
            과거 가격 데이터 리스트
        """
        try:
            endpoint = "/uapi/domestic-stock/v1/quotations/inquire-daily-indexchartprice"
            tr_id = "FHKUP03500100"
            
            params = {
                "fid_cond_mrkt_div_code": "U",
                "fid_input_iscd": sector_code,
                "fid_input_date_1": "",
                "fid_input_date_2": "",
                "fid_period_div_code": "D",
            }
            
            result = self._make_request("GET", endpoint, tr_id, params=params)
            output_list = result.get("output2", [])
            
            price_data_list = []
            for item in output_list[:days]:
                price_data_list.append(PriceData(
                    date=item.get("stck_bsop_date", ""),
                    open_price=float(item.get("bstp_nmix_oprc", 0)),
                    high_price=float(item.get("bstp_nmix_hgpr", 0)),
                    low_price=float(item.get("bstp_nmix_lwpr", 0)),
                    close_price=float(item.get("bstp_nmix_clpr", 0)),
                    volume=int(item.get("acml_vol", 0))
                ))
            
            return price_data_list
            
        except Exception as e:
            logger.warning(f"섹터 과거 데이터 조회 실패 ({sector_code}): {e}")
            return []
    
    def _calculate_moving_average(self, price_data: List[PriceData], period: int) -> float:
        """
        이동평균 계산
        
        Args:
            price_data: 가격 데이터 리스트
            period: 이동평균 기간
        
        Returns:
            이동평균 값
        """
        if len(price_data) < period:
            return 0.0
        
        prices = [d.close_price for d in price_data[:period]]
        return sum(prices) / period
    
    async def _get_foreign_net_buy_days(self, sector_code: str) -> List[float]:
        """
        외국인 순매수 데이터 조회 (최근 3일)
        
        Args:
            sector_code: 섹터 코드
        
        Returns:
            외국인 순매수 금액 리스트 (최신순)
        """
        try:
            # 실제 API 엔드포인트 구현 필요
            # 현재는 모의 데이터 반환
            logger.debug(f"외국인 순매수 데이터 조회 (섹터: {sector_code})")
            
            # TODO: 실제 KIS API 엔드포인트 구현
            # 임시로 랜덤 데이터 반환 (양수: 순매수, 음수: 순매도)
            import random
            return [random.uniform(-1000, 1000) for _ in range(3)]
            
        except Exception as e:
            logger.warning(f"외국인 순매수 데이터 조회 실패: {e}")
            return [0.0, 0.0, 0.0]
    
    async def _get_institution_net_buy_days(self, sector_code: str) -> List[float]:
        """
        기관 순매수 데이터 조회 (최근 3일)
        
        Args:
            sector_code: 섹터 코드
        
        Returns:
            기관 순매수 금액 리스트 (최신순)
        """
        try:
            # 실제 API 엔드포인트 구현 필요
            # 현재는 모의 데이터 반환
            logger.debug(f"기관 순매수 데이터 조회 (섹터: {sector_code})")
            
            # TODO: 실제 KIS API 엔드포인트 구현
            # 임시로 랜덤 데이터 반환
            import random
            return [random.uniform(-1000, 1000) for _ in range(3)]
            
        except Exception as e:
            logger.warning(f"기관 순매수 데이터 조회 실패: {e}")
            return [0.0, 0.0, 0.0]
    
    def close(self):
        """세션 종료"""
        if self._session:
            self._session.close()
            logger.info("KIS API 클라이언트 세션 종료")
    
    def __enter__(self):
        """컨텍스트 매니저 진입"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """컨텍스트 매니저 종료"""
        self.close()
