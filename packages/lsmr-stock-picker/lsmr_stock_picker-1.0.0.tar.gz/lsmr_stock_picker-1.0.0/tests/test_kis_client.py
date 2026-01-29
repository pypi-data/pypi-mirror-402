"""
KIS API 클라이언트 테스트
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta

from kis_api.client import (
    KISClient,
    AccountType,
    TokenInfo,
    IndexData,
    StockData,
    PriceData,
)
from config.settings import KISConfig, Environment
from utils.error_handling import (
    AuthenticationError,
    RateLimitError,
    NetworkError,
    KISAPIError,
)


@pytest.fixture
def kis_config():
    """테스트용 KIS 설정"""
    return KISConfig(
        app_key="test_app_key_1234567890",
        app_secret="test_app_secret_1234567890",
        base_url="https://openapivts.koreainvestment.com:29443",
        account_number="12345678-01",
        environment=Environment.TESTING
    )


@pytest.fixture
def kis_client(kis_config):
    """테스트용 KIS 클라이언트"""
    return KISClient(kis_config, AccountType.VIRTUAL)


class TestKISClientInitialization:
    """KIS 클라이언트 초기화 테스트"""
    
    def test_client_initialization_virtual(self, kis_config):
        """모의투자 계정으로 클라이언트 초기화"""
        client = KISClient(kis_config, AccountType.VIRTUAL)
        
        assert client.account_type == AccountType.VIRTUAL
        assert client.base_url == KISClient.VIRTUAL_BASE_URL
        assert client.config == kis_config
    
    def test_client_initialization_real(self, kis_config):
        """실전투자 계정으로 클라이언트 초기화"""
        client = KISClient(kis_config, AccountType.REAL)
        
        assert client.account_type == AccountType.REAL
        assert client.base_url == KISClient.REAL_BASE_URL
    
    def test_endpoint_selection_by_account_type(self, kis_config):
        """
        속성 테스트 16: 계정 유형별 엔드포인트 선택
        Feature: lsmr-stock-picker, Property 16: 계정 유형별 엔드포인트 선택
        
        모든 KIS_ACCOUNT_TYPE 값("real" 또는 "virtual")에 대해,
        시스템은 "real"의 경우 프로덕션 엔드포인트에,
        "virtual"의 경우 모의투자 엔드포인트에 연결해야 한다
        """
        # Real 계정
        real_client = KISClient(kis_config, AccountType.REAL)
        assert real_client.base_url == "https://openapi.koreainvestment.com:9443"
        
        # Virtual 계정
        virtual_client = KISClient(kis_config, AccountType.VIRTUAL)
        assert virtual_client.base_url == "https://openapivts.koreainvestment.com:29443"


class TestTokenManagement:
    """토큰 관리 테스트"""
    
    def test_token_expiration_check(self):
        """토큰 만료 확인"""
        # 만료된 토큰
        expired_token = TokenInfo(
            access_token="test_token",
            token_type="Bearer",
            expires_at=datetime.now() - timedelta(hours=1)
        )
        assert expired_token.is_expired() is True
        
        # 유효한 토큰
        valid_token = TokenInfo(
            access_token="test_token",
            token_type="Bearer",
            expires_at=datetime.now() + timedelta(hours=1)
        )
        assert valid_token.is_expired() is False
        
        # 5분 이내 만료 예정 토큰 (갱신 필요)
        soon_expired_token = TokenInfo(
            access_token="test_token",
            token_type="Bearer",
            expires_at=datetime.now() + timedelta(minutes=3)
        )
        assert soon_expired_token.is_expired() is True
    
    @patch('kis_api.client.requests.Session.post')
    def test_authentication_success(self, mock_post, kis_client):
        """인증 성공 테스트"""
        # Mock 응답 설정
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "access_token": "test_access_token",
            "token_type": "Bearer",
            "access_token_token_expired": "2026-01-17 10:00:00"
        }
        mock_post.return_value = mock_response
        
        # 인증 실행
        result = kis_client.authenticate()
        
        assert result is True
        assert kis_client._token is not None
        assert kis_client._token.access_token == "test_access_token"
    
    @patch('kis_api.client.requests.Session.post')
    def test_authentication_failure(self, mock_post, kis_client):
        """인증 실패 테스트"""
        # Mock 응답 설정 (실패)
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"
        mock_post.return_value = mock_response
        
        # 인증 실행 및 예외 확인
        with pytest.raises(AuthenticationError):
            kis_client.authenticate()


class TestRateLimiting:
    """속도 제한 테스트"""
    
    def test_rate_limit_check(self, kis_client):
        """속도 제한 확인"""
        # 초기 상태
        assert kis_client._request_count == 0
        
        # 속도 제한 확인 (대기 없음)
        kis_client._rate_limit_check()
        assert kis_client._request_count == 1
        
        # 여러 번 호출
        for _ in range(19):
            kis_client._rate_limit_check()
        
        assert kis_client._request_count == 20
    
    def test_rate_limit_exceeded(self, kis_client):
        """속도 제한 초과 시 대기"""
        import time
        
        # 요청 카운트를 20으로 설정
        kis_client._request_count = 20
        kis_client._rate_limit_reset_time = time.time()
        
        # 다음 요청 시 대기 발생
        start_time = time.time()
        kis_client._rate_limit_check()
        elapsed = time.time() - start_time
        
        # 대기 시간이 발생했는지 확인 (최소 0.5초)
        assert elapsed >= 0.5


class TestAPIRequests:
    """API 요청 테스트"""
    
    @patch('kis_api.client.requests.Session.get')
    def test_get_index_data(self, mock_get, kis_client):
        """지수 데이터 조회 테스트"""
        # 토큰 설정
        kis_client._token = TokenInfo(
            access_token="test_token",
            token_type="Bearer",
            expires_at=datetime.now() + timedelta(hours=1)
        )
        
        # Mock 응답 설정
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "rt_cd": "0",
            "output": {
                "bstp_nmix_prpr": "2500.50",
                "bstp_nmix_prdy_vrss_sign": "1.5",
                "acml_vol": "1000000"
            }
        }
        mock_get.return_value = mock_response
        
        # 지수 데이터 조회
        index_data = kis_client.get_index_data("0001")
        
        assert isinstance(index_data, IndexData)
        assert index_data.index_code == "0001"
        assert index_data.current_price == 2500.50
    
    @patch('kis_api.client.requests.Session.get')
    def test_get_stock_data(self, mock_get, kis_client):
        """종목 데이터 조회 테스트"""
        # 토큰 설정
        kis_client._token = TokenInfo(
            access_token="test_token",
            token_type="Bearer",
            expires_at=datetime.now() + timedelta(hours=1)
        )
        
        # Mock 응답 설정
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "rt_cd": "0",
            "output": {
                "prdt_name": "삼성전자",
                "stck_prpr": "70000",
                "prdy_ctrt": "2.5",
                "acml_vol": "5000000"
            }
        }
        mock_get.return_value = mock_response
        
        # 종목 데이터 조회
        stock_data = kis_client.get_stock_data("005930")
        
        assert isinstance(stock_data, StockData)
        assert stock_data.ticker == "005930"
        assert stock_data.stock_name == "삼성전자"
        assert stock_data.current_price == 70000.0
    
    @patch('kis_api.client.requests.Session.get')
    def test_get_historical_data(self, mock_get, kis_client):
        """과거 가격 데이터 조회 테스트"""
        # 토큰 설정
        kis_client._token = TokenInfo(
            access_token="test_token",
            token_type="Bearer",
            expires_at=datetime.now() + timedelta(hours=1)
        )
        
        # Mock 응답 설정
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "rt_cd": "0",
            "output": [
                {
                    "stck_bsop_date": "20260116",
                    "stck_oprc": "70000",
                    "stck_hgpr": "71000",
                    "stck_lwpr": "69000",
                    "stck_clpr": "70500",
                    "acml_vol": "5000000"
                },
                {
                    "stck_bsop_date": "20260115",
                    "stck_oprc": "69500",
                    "stck_hgpr": "70500",
                    "stck_lwpr": "69000",
                    "stck_clpr": "70000",
                    "acml_vol": "4800000"
                }
            ]
        }
        mock_get.return_value = mock_response
        
        # 과거 데이터 조회
        price_data_list = kis_client.get_historical_data("005930", days=2)
        
        assert len(price_data_list) == 2
        assert isinstance(price_data_list[0], PriceData)
        assert price_data_list[0].date == "20260116"
        assert price_data_list[0].close_price == 70500.0


class TestErrorHandling:
    """오류 처리 테스트"""
    
    @patch('kis_api.client.requests.Session.get')
    def test_api_error_handling(self, mock_get, kis_client):
        """API 오류 처리 테스트"""
        # 토큰 설정
        kis_client._token = TokenInfo(
            access_token="test_token",
            token_type="Bearer",
            expires_at=datetime.now() + timedelta(hours=1)
        )
        
        # Mock 응답 설정 (오류)
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "rt_cd": "1",
            "msg_cd": "EGW00123",
            "msg1": "Invalid request"
        }
        mock_get.return_value = mock_response
        
        # API 오류 확인
        with pytest.raises(KISAPIError):
            kis_client.get_index_data("0001")
    
    @patch('kis_api.client.requests.Session.get')
    def test_rate_limit_error(self, mock_get, kis_client):
        """속도 제한 오류 테스트"""
        # 토큰 설정
        kis_client._token = TokenInfo(
            access_token="test_token",
            token_type="Bearer",
            expires_at=datetime.now() + timedelta(hours=1)
        )
        
        # Mock 응답 설정 (429 Too Many Requests)
        mock_response = Mock()
        mock_response.status_code = 429
        mock_response.text = "Too Many Requests"
        mock_get.return_value = mock_response
        
        # 속도 제한 오류 확인
        with pytest.raises(RateLimitError):
            kis_client.get_index_data("0001")
    
    def test_authentication_required(self, kis_client):
        """인증 필요 오류 테스트"""
        # 토큰 없이 API 호출
        with pytest.raises(AuthenticationError):
            kis_client.get_index_data("0001")


class TestContextManager:
    """컨텍스트 매니저 테스트"""
    
    def test_context_manager(self, kis_config):
        """컨텍스트 매니저 사용"""
        with KISClient(kis_config, AccountType.VIRTUAL) as client:
            assert client is not None
            assert client._session is not None
        
        # 컨텍스트 종료 후 세션이 닫혔는지 확인은 어려우므로 생략
