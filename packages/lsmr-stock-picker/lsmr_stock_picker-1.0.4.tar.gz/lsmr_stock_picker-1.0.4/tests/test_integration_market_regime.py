"""
Market Regime Analyzer 통합 테스트
전체 시스템과의 통합 및 실제 사용 시나리오 테스트
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch
from datetime import datetime

from lsmr_stock_picker import MarketRegimeAnalyzer, KISClient, SystemConfig
from lsmr_stock_picker.models.data_models import IndexData, MarketRegime


@pytest.fixture
def system_config():
    """시스템 설정"""
    config = SystemConfig.load(validate=False)  # 검증 비활성화
    # 테스트용 설정 오버라이드
    config.kis.app_key = "test_key"
    config.kis.app_secret = "test_secret"
    config.kis.account_number = "12345678901"
    return config

@pytest.fixture
async def kis_client(system_config):
    """KIS API 클라이언트 (Mock)"""
    client = AsyncMock(spec=KISClient)
    client.config = system_config.kis
    return client


@pytest.fixture
def analyzer(kis_client, system_config):
    """Market Regime Analyzer"""
    return MarketRegimeAnalyzer(kis_client, system_config.risk)


class TestSystemIntegration:
    """시스템 통합 테스트"""
    
    @pytest.mark.asyncio
    async def test_full_analysis_workflow(self, analyzer, kis_client):
        """전체 분석 워크플로우 테스트"""
        # Given: Mock 데이터 설정
        kospi_data = IndexData('0001', 2500.0, 2450.0, 2.0, datetime.now())
        kosdaq_data = IndexData('1001', 850.0, 840.0, 1.5, datetime.now())
        kis_client.get_index_data.side_effect = [kospi_data, kosdaq_data]
        
        # When: 전체 분석 실행
        result = await analyzer.analyze_market_regime()
        
        # Then: 완전한 분석 결과 확인
        assert result.regime == MarketRegime.BULL
        assert result.kospi_data.index_code == '0001'
        assert result.kosdaq_data.index_code == '1001'
        assert result.risk_parameters.take_profit_percent == 5.0
        assert result.risk_parameters.stop_loss_percent == 3.0
        assert result.confidence_score > 0
        assert result.analysis_timestamp is not None
        
        # API 호출 확인
        assert kis_client.get_index_data.call_count == 2
        kis_client.get_index_data.assert_any_call('0001')  # KOSPI
        kis_client.get_index_data.assert_any_call('1001')  # KOSDAQ
    
    @pytest.mark.asyncio
    async def test_performance_under_load(self, analyzer, kis_client):
        """부하 상황에서의 성능 테스트"""
        # Given: 빠른 응답 Mock 설정
        kospi_data = IndexData('0001', 2500.0, 2450.0, 2.0, datetime.now())
        kosdaq_data = IndexData('1001', 850.0, 840.0, 1.5, datetime.now())
        kis_client.get_index_data.side_effect = lambda x: (
            kospi_data if x == '0001' else kosdaq_data
        )
        
        # When: 동시 다중 분석 요청
        tasks = [analyzer.analyze_market_regime(use_cache=False) for _ in range(5)]
        results = await asyncio.gather(*tasks)
        
        # Then: 모든 요청이 성공적으로 처리
        assert len(results) == 5
        for result in results:
            assert result.regime == MarketRegime.BULL
            assert result.confidence_score > 0
    
    @pytest.mark.asyncio
    async def test_caching_across_multiple_calls(self, analyzer, kis_client):
        """다중 호출에서의 캐싱 효과 테스트"""
        # Given: Mock 데이터 설정
        kospi_data = IndexData('0001', 2500.0, 2450.0, 2.0, datetime.now())
        kosdaq_data = IndexData('1001', 850.0, 840.0, 1.5, datetime.now())
        kis_client.get_index_data.side_effect = [kospi_data, kosdaq_data]
        
        # When: 여러 번 분석 호출
        result1 = await analyzer.analyze_market_regime(use_cache=True)
        result2 = await analyzer.get_current_regime(use_cache=True)
        result3 = await analyzer.get_current_risk_parameters(use_cache=True)
        
        # Then: 캐시 효과로 API 호출 최소화
        assert kis_client.get_index_data.call_count == 2  # 첫 번째만 실제 호출
        assert result1.regime == result2
        assert result1.risk_parameters.regime == result3.regime
    
    @pytest.mark.asyncio
    async def test_error_recovery_and_fallback(self, analyzer, kis_client):
        """오류 복구 및 폴백 메커니즘 테스트"""
        # Given: 첫 번째 호출은 실패, 두 번째는 성공
        from lsmr_stock_picker.kis_api.client import KISAPIError
        
        kospi_data = IndexData('0001', 2500.0, 2450.0, 2.0, datetime.now())
        kosdaq_data = IndexData('1001', 850.0, 840.0, 1.5, datetime.now())
        
        kis_client.get_index_data.side_effect = [
            KISAPIError("네트워크 오류"),  # 첫 번째 KOSPI 호출 실패
            kosdaq_data  # KOSDAQ은 성공하지만 전체 실패
        ]
        
        # When & Then: 첫 번째 호출은 실패
        with pytest.raises(KISAPIError):
            await analyzer.analyze_market_regime(use_cache=False)
        
        # Given: 두 번째 시도는 성공
        kis_client.get_index_data.side_effect = [kospi_data, kosdaq_data]
        
        # When: 재시도
        result = await analyzer.analyze_market_regime(use_cache=False)
        
        # Then: 성공적으로 복구
        assert result.regime == MarketRegime.BULL
    
    @pytest.mark.asyncio
    async def test_configuration_update_integration(self, analyzer, system_config):
        """설정 업데이트 통합 테스트"""
        # Given: 초기 설정
        initial_take_profit = analyzer.risk_config.default_take_profit
        
        # When: 설정 업데이트
        new_config = system_config.risk
        new_config.default_take_profit = 4.0
        new_config.default_stop_loss = 3.5
        analyzer.update_risk_config(new_config)
        
        # Then: 설정 변경 확인
        assert analyzer.risk_config.default_take_profit == 4.0
        assert analyzer.risk_config.default_stop_loss == 3.5
        assert analyzer.risk_config.default_take_profit != initial_take_profit
        
        # 캐시가 초기화되었는지 확인
        cache_status = analyzer.get_cache_status()
        assert cache_status['cached'] is False


class TestRealWorldScenarios:
    """실제 시나리오 테스트"""
    
    @pytest.mark.asyncio
    async def test_market_transition_scenario(self, analyzer, kis_client):
        """시장 상황 전환 시나리오 테스트"""
        # Given: 강세장 데이터
        bull_kospi = IndexData('0001', 2600.0, 2500.0, 4.0, datetime.now())
        bull_kosdaq = IndexData('1001', 900.0, 850.0, 3.0, datetime.now())
        
        # 약세장 데이터
        bear_kospi = IndexData('0001', 2400.0, 2500.0, -4.0, datetime.now())
        bear_kosdaq = IndexData('1001', 800.0, 850.0, -3.0, datetime.now())
        
        # When: 강세장 분석
        kis_client.get_index_data.side_effect = [bull_kospi, bull_kosdaq]
        bull_result = await analyzer.analyze_market_regime(use_cache=False)
        
        # Then: 강세장 분류 및 매개변수
        assert bull_result.regime == MarketRegime.BULL
        assert bull_result.risk_parameters.take_profit_percent == 5.0
        assert bull_result.risk_parameters.stop_loss_percent == 3.0
        
        # 캐시 초기화 및 최소 간격 리셋
        analyzer.clear_cache()
        analyzer._last_analysis_time = 0
        
        # When: 약세장으로 전환
        kis_client.get_index_data.side_effect = [bear_kospi, bear_kosdaq]
        bear_result = await analyzer.analyze_market_regime(use_cache=False)
        
        # Then: 약세장 분류 및 매개변수 변경
        assert bear_result.regime == MarketRegime.BEAR
        assert bear_result.risk_parameters.take_profit_percent == 2.0
        assert bear_result.risk_parameters.stop_loss_percent == 2.0
    
    @pytest.mark.asyncio
    async def test_mixed_signal_scenario(self, analyzer, kis_client):
        """혼재 신호 시나리오 테스트"""
        # Given: KOSPI 상승, KOSDAQ 하락 (혼재 신호)
        mixed_kospi = IndexData('0001', 2550.0, 2500.0, 2.0, datetime.now())
        mixed_kosdaq = IndexData('1001', 820.0, 850.0, -1.5, datetime.now())
        
        kis_client.get_index_data.side_effect = [mixed_kospi, mixed_kosdaq]
        
        # When: 분석 실행
        result = await analyzer.analyze_market_regime(use_cache=False)
        
        # Then: 중립 분류 및 기본 매개변수
        assert result.regime == MarketRegime.NEUTRAL
        assert result.risk_parameters.take_profit_percent == 3.0  # 기본값
        assert result.risk_parameters.stop_loss_percent == 2.5   # 기본값
        
        # 신뢰도가 상대적으로 낮아야 함
        assert result.confidence_score < 70.0
    
    @pytest.mark.asyncio
    async def test_high_volatility_scenario(self, analyzer, kis_client):
        """고변동성 시나리오 테스트"""
        # Given: 큰 변동폭의 데이터
        volatile_kospi = IndexData('0001', 2700.0, 2400.0, 8.0, datetime.now())
        volatile_kosdaq = IndexData('1001', 950.0, 800.0, 7.5, datetime.now())
        
        kis_client.get_index_data.side_effect = [volatile_kospi, volatile_kosdaq]
        
        # When: 분석 실행
        result = await analyzer.analyze_market_regime(use_cache=False)
        
        # Then: 명확한 강세 신호로 높은 신뢰도
        assert result.regime == MarketRegime.BULL
        assert result.confidence_score > 80.0  # 높은 신뢰도
        
        # 큰 변동폭으로 인한 높은 신뢰도 확인
        kospi_distance = abs(volatile_kospi.current_value - volatile_kospi.ma20) / volatile_kospi.ma20 * 100
        kosdaq_distance = abs(volatile_kosdaq.current_value - volatile_kosdaq.ma20) / volatile_kosdaq.ma20 * 100
        assert kospi_distance > 10.0  # 10% 이상 차이
        assert kosdaq_distance > 15.0  # 15% 이상 차이


if __name__ == '__main__':
    pytest.main([__file__, '-v'])