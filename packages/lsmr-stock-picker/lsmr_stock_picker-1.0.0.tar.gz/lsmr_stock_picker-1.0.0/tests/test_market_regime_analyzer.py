"""
Market Regime Analyzer 테스트
시장 상황 분석기의 핵심 기능 검증
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from lsmr_stock_picker.analyzers.market_regime_analyzer import (
    MarketRegimeAnalyzer, 
    RiskParameters, 
    MarketAnalysisResult
)
from lsmr_stock_picker.models.data_models import MarketRegime, IndexData
from lsmr_stock_picker.config.settings import RiskConfig
from lsmr_stock_picker.kis_api.client import KISAPIError


@pytest.fixture
def mock_kis_client():
    """Mock KIS API 클라이언트"""
    client = AsyncMock()
    return client


@pytest.fixture
def risk_config():
    """테스트용 리스크 설정"""
    return RiskConfig(
        default_take_profit=3.0,
        default_stop_loss=2.5
    )


@pytest.fixture
def analyzer(mock_kis_client, risk_config):
    """Market Regime Analyzer 인스턴스"""
    return MarketRegimeAnalyzer(mock_kis_client, risk_config)


@pytest.fixture
def sample_kospi_data():
    """샘플 KOSPI 데이터"""
    return IndexData(
        index_code='0001',
        current_value=2500.0,
        ma20=2450.0,
        change_percent=1.5,
        timestamp=datetime.now()
    )


@pytest.fixture
def sample_kosdaq_data():
    """샘플 KOSDAQ 데이터"""
    return IndexData(
        index_code='1001',
        current_value=850.0,
        ma20=840.0,
        change_percent=1.2,
        timestamp=datetime.now()
    )


class TestMarketRegimeClassification:
    """시장 상황 분류 테스트"""
    
    @pytest.mark.asyncio
    async def test_bull_market_classification(self, analyzer, mock_kis_client):
        """강세장 분류 테스트 - 양 지수 모두 20MA 상위"""
        # Given: 양 지수 모두 20일 이동평균 상위
        kospi_data = IndexData('0001', 2500.0, 2450.0, 2.0, datetime.now())
        kosdaq_data = IndexData('1001', 850.0, 840.0, 1.5, datetime.now())
        
        mock_kis_client.get_index_data.side_effect = [kospi_data, kosdaq_data]
        
        # When: 시장 분석 실행
        result = await analyzer.analyze_market_regime(use_cache=False)
        
        # Then: 강세장으로 분류
        assert result.regime == MarketRegime.BULL
        assert result.risk_parameters.take_profit_percent == 5.0
        assert result.risk_parameters.stop_loss_percent == 3.0
    
    @pytest.mark.asyncio
    async def test_bear_market_classification(self, analyzer, mock_kis_client):
        """약세장 분류 테스트 - 양 지수 모두 20MA 하위"""
        # Given: 양 지수 모두 20일 이동평균 하위
        kospi_data = IndexData('0001', 2400.0, 2450.0, -2.0, datetime.now())
        kosdaq_data = IndexData('1001', 830.0, 840.0, -1.2, datetime.now())
        
        mock_kis_client.get_index_data.side_effect = [kospi_data, kosdaq_data]
        
        # When: 시장 분석 실행
        result = await analyzer.analyze_market_regime(use_cache=False)
        
        # Then: 약세장으로 분류
        assert result.regime == MarketRegime.BEAR
        assert result.risk_parameters.take_profit_percent == 2.0
        assert result.risk_parameters.stop_loss_percent == 2.0
    
    @pytest.mark.asyncio
    async def test_neutral_market_classification(self, analyzer, mock_kis_client):
        """중립 시장 분류 테스트 - 지수간 혼재 신호"""
        # Given: KOSPI는 상위, KOSDAQ은 하위
        kospi_data = IndexData('0001', 2500.0, 2450.0, 2.0, datetime.now())
        kosdaq_data = IndexData('1001', 830.0, 840.0, -1.2, datetime.now())
        
        mock_kis_client.get_index_data.side_effect = [kospi_data, kosdaq_data]
        
        # When: 시장 분석 실행
        result = await analyzer.analyze_market_regime(use_cache=False)
        
        # Then: 중립으로 분류
        assert result.regime == MarketRegime.NEUTRAL
        assert result.risk_parameters.take_profit_percent == 3.0  # 기본값
        assert result.risk_parameters.stop_loss_percent == 2.5   # 기본값


class TestRiskParameterMapping:
    """리스크 매개변수 매핑 테스트"""
    
    def test_bull_market_risk_parameters(self, analyzer):
        """강세장 리스크 매개변수 테스트"""
        # When: 강세장 리스크 매개변수 조회
        params = analyzer._get_risk_parameters(MarketRegime.BULL)
        
        # Then: 강세장 매개변수 적용
        assert params.take_profit_percent == 5.0
        assert params.stop_loss_percent == 3.0
        assert params.regime == MarketRegime.BULL
    
    def test_bear_market_risk_parameters(self, analyzer):
        """약세장 리스크 매개변수 테스트"""
        # When: 약세장 리스크 매개변수 조회
        params = analyzer._get_risk_parameters(MarketRegime.BEAR)
        
        # Then: 약세장 매개변수 적용
        assert params.take_profit_percent == 2.0
        assert params.stop_loss_percent == 2.0
        assert params.regime == MarketRegime.BEAR
    
    def test_neutral_market_risk_parameters(self, analyzer):
        """중립 시장 리스크 매개변수 테스트"""
        # When: 중립 시장 리스크 매개변수 조회
        params = analyzer._get_risk_parameters(MarketRegime.NEUTRAL)
        
        # Then: 기본 매개변수 적용
        assert params.take_profit_percent == 3.0
        assert params.stop_loss_percent == 2.5
        assert params.regime == MarketRegime.NEUTRAL


class TestCachingAndPerformance:
    """캐싱 및 성능 테스트"""
    
    @pytest.mark.asyncio
    async def test_caching_mechanism(self, analyzer, mock_kis_client, sample_kospi_data, sample_kosdaq_data):
        """캐싱 메커니즘 테스트"""
        # Given: Mock 데이터 설정
        mock_kis_client.get_index_data.side_effect = [sample_kospi_data, sample_kosdaq_data]
        
        # When: 첫 번째 분석 (캐시 없음)
        result1 = await analyzer.analyze_market_regime(use_cache=True)
        
        # Then: API 호출 확인
        assert mock_kis_client.get_index_data.call_count == 2
        
        # When: 두 번째 분석 (캐시 사용)
        result2 = await analyzer.analyze_market_regime(use_cache=True)
        
        # Then: 추가 API 호출 없음, 같은 결과
        assert mock_kis_client.get_index_data.call_count == 2  # 여전히 2
        assert result1.regime == result2.regime
        assert result1.analysis_timestamp == result2.analysis_timestamp
    
    @pytest.mark.asyncio
    async def test_cache_expiry(self, analyzer, mock_kis_client, sample_kospi_data, sample_kosdaq_data):
        """캐시 만료 테스트"""
        # Given: 캐시 지속시간과 최소 분석 간격을 매우 짧게 설정
        analyzer._cache_duration = timedelta(milliseconds=10)
        analyzer._min_analysis_interval = 0.01  # 10ms로 설정
        mock_kis_client.get_index_data.side_effect = [
            sample_kospi_data, sample_kosdaq_data,  # 첫 번째 호출
            sample_kospi_data, sample_kosdaq_data   # 두 번째 호출
        ]
        
        # When: 첫 번째 분석
        await analyzer.analyze_market_regime(use_cache=True)
        
        # 캐시 만료 및 최소 간격 대기
        await asyncio.sleep(0.02)
        
        # 두 번째 분석
        await analyzer.analyze_market_regime(use_cache=True)
        
        # Then: 캐시 만료로 인한 재호출
        assert mock_kis_client.get_index_data.call_count == 4
    
    @pytest.mark.asyncio
    async def test_performance_requirement(self, analyzer, mock_kis_client, sample_kospi_data, sample_kosdaq_data):
        """성능 요구사항 테스트 (100ms 이하)"""
        # Given: 빠른 응답을 위한 Mock 설정
        mock_kis_client.get_index_data.side_effect = [sample_kospi_data, sample_kosdaq_data]
        
        # When: 성능 검증 실행
        performance_result = await analyzer.validate_analysis_performance()
        
        # Then: 100ms 이하 응답시간 확인
        assert performance_result['performance_requirement_met'] is True
        assert performance_result['response_time_ms'] < 100.0


class TestErrorHandling:
    """오류 처리 테스트"""
    
    @pytest.mark.asyncio
    async def test_kospi_data_error(self, analyzer, mock_kis_client, sample_kosdaq_data):
        """KOSPI 데이터 조회 오류 처리"""
        # Given: KOSPI 조회 실패, KOSDAQ 성공
        mock_kis_client.get_index_data.side_effect = [
            KISAPIError("KOSPI 조회 실패"), 
            sample_kosdaq_data
        ]
        
        # When & Then: 예외 발생 확인
        with pytest.raises(KISAPIError, match="KOSPI 데이터 조회 실패"):
            await analyzer.analyze_market_regime(use_cache=False)
    
    @pytest.mark.asyncio
    async def test_kosdaq_data_error(self, analyzer, mock_kis_client, sample_kospi_data):
        """KOSDAQ 데이터 조회 오류 처리"""
        # Given: KOSPI 성공, KOSDAQ 조회 실패
        mock_kis_client.get_index_data.side_effect = [
            sample_kospi_data,
            KISAPIError("KOSDAQ 조회 실패")
        ]
        
        # When & Then: 예외 발생 확인
        with pytest.raises(KISAPIError, match="KOSDAQ 데이터 조회 실패"):
            await analyzer.analyze_market_regime(use_cache=False)
    
    @pytest.mark.asyncio
    async def test_fallback_to_neutral_on_classification_error(self, analyzer):
        """분류 오류시 중립으로 폴백 테스트"""
        # Given: 실제 오류를 발생시키는 데이터 (None 값)
        invalid_kospi = IndexData('0001', None, 2450.0, 1.5, datetime.now())
        invalid_kosdaq = IndexData('1001', 850.0, None, 1.2, datetime.now())
        
        # When: 분류 실행
        regime = analyzer._classify_market_regime(invalid_kospi, invalid_kosdaq)
        
        # Then: 오류 발생시에도 중립 반환 (예외 없음)
        assert regime == MarketRegime.NEUTRAL


class TestUtilityMethods:
    """유틸리티 메서드 테스트"""
    
    @pytest.mark.asyncio
    async def test_get_current_regime(self, analyzer, mock_kis_client, sample_kospi_data, sample_kosdaq_data):
        """현재 시장 상황 간단 조회 테스트"""
        # Given
        mock_kis_client.get_index_data.side_effect = [sample_kospi_data, sample_kosdaq_data]
        
        # When
        regime = await analyzer.get_current_regime()
        
        # Then
        assert isinstance(regime, MarketRegime)
    
    @pytest.mark.asyncio
    async def test_get_current_risk_parameters(self, analyzer, mock_kis_client, sample_kospi_data, sample_kosdaq_data):
        """현재 리스크 매개변수 간단 조회 테스트"""
        # Given
        mock_kis_client.get_index_data.side_effect = [sample_kospi_data, sample_kosdaq_data]
        
        # When
        params = await analyzer.get_current_risk_parameters()
        
        # Then
        assert isinstance(params, RiskParameters)
        assert params.take_profit_percent > 0
        assert params.stop_loss_percent > 0
    
    def test_cache_status(self, analyzer):
        """캐시 상태 정보 테스트"""
        # When
        status = analyzer.get_cache_status()
        
        # Then
        assert 'cached' in status
        assert 'cache_valid' in status
        assert 'last_analysis_time' in status
    
    def test_clear_cache(self, analyzer):
        """캐시 초기화 테스트"""
        # Given: 캐시 설정
        analyzer._cache = MagicMock()
        analyzer._cache_expiry = datetime.now()
        
        # When: 캐시 초기화
        analyzer.clear_cache()
        
        # Then: 캐시 제거 확인
        assert analyzer._cache is None
        assert analyzer._cache_expiry is None
    
    def test_update_risk_config(self, analyzer):
        """리스크 설정 업데이트 테스트"""
        # Given: 새로운 설정
        new_config = RiskConfig(default_take_profit=4.0, default_stop_loss=3.0)
        analyzer._cache = MagicMock()  # 기존 캐시 설정
        
        # When: 설정 업데이트
        analyzer.update_risk_config(new_config)
        
        # Then: 설정 변경 및 캐시 초기화 확인
        assert analyzer.risk_config.default_take_profit == 4.0
        assert analyzer.risk_config.default_stop_loss == 3.0
        assert analyzer._cache is None


class TestConfidenceScoreCalculation:
    """신뢰도 점수 계산 테스트"""
    
    def test_high_confidence_bull_market(self, analyzer):
        """강세장 고신뢰도 테스트"""
        # Given: 명확한 강세 신호 (큰 거리, 같은 방향)
        kospi_data = IndexData('0001', 2600.0, 2400.0, 3.0, datetime.now())  # 8.3% 상위
        kosdaq_data = IndexData('1001', 900.0, 840.0, 2.5, datetime.now())   # 7.1% 상위
        
        # When
        confidence = analyzer._calculate_confidence_score(kospi_data, kosdaq_data, MarketRegime.BULL)
        
        # Then: 높은 신뢰도
        assert confidence > 70.0
    
    def test_low_confidence_neutral_market(self, analyzer):
        """중립 시장 저신뢰도 테스트"""
        # Given: 애매한 신호 (작은 거리, 반대 방향)
        kospi_data = IndexData('0001', 2460.0, 2450.0, 0.5, datetime.now())   # 0.4% 상위
        kosdaq_data = IndexData('1001', 835.0, 840.0, -0.3, datetime.now())   # 0.6% 하위
        
        # When
        confidence = analyzer._calculate_confidence_score(kospi_data, kosdaq_data, MarketRegime.NEUTRAL)
        
        # Then: 낮은 신뢰도
        assert confidence < 60.0
    
    def test_confidence_score_bounds(self, analyzer):
        """신뢰도 점수 범위 테스트 (0-100)"""
        # Given: 극단적인 데이터
        extreme_kospi = IndexData('0001', 3000.0, 2000.0, 10.0, datetime.now())
        extreme_kosdaq = IndexData('1001', 1000.0, 700.0, 8.0, datetime.now())
        
        # When
        confidence = analyzer._calculate_confidence_score(extreme_kospi, extreme_kosdaq, MarketRegime.BULL)
        
        # Then: 0-100 범위 내
        assert 0 <= confidence <= 100


if __name__ == '__main__':
    pytest.main([__file__, '-v'])