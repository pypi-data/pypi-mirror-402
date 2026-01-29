"""
자동 분석 워크플로우 테스트
"""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch

from analyzers.workflow import AnalysisWorkflow, WorkflowResult
from analyzers.market_regime_analyzer import MarketAnalysisResult, RiskParameters
from analyzers.sector_filter import SectorAnalysisResult
from analyzers.stock_picker import StockCandidate
from models.data_models import MarketRegime, LeadingSector, IndexData, TradeAction
from kis_api.client import KISClient
from database.manager import DatabaseManager
from config.settings import SystemConfig


@pytest.fixture
def mock_kis_client():
    """Mock KIS API 클라이언트"""
    client = Mock(spec=KISClient)
    client.authenticate = AsyncMock(return_value=True)
    client.get_index_data = AsyncMock()
    client.get_sector_data = AsyncMock()
    client.get_sector_stocks = AsyncMock(return_value=[])
    client.get_historical_data = AsyncMock(return_value=[])
    return client


@pytest.fixture
def mock_db_manager():
    """Mock 데이터베이스 관리자"""
    manager = Mock(spec=DatabaseManager)
    manager.connect = AsyncMock()
    manager.disconnect = AsyncMock()
    manager.save_market_regime = AsyncMock()
    manager.save_sector_analysis = AsyncMock()
    manager.save_stock_candidate = AsyncMock()
    return manager


@pytest.fixture
def mock_config():
    """Mock 시스템 설정"""
    config = Mock(spec=SystemConfig)
    config.risk_config = Mock()
    config.risk_config.default_take_profit = 3.0
    config.risk_config.default_stop_loss = 2.5
    return config


@pytest.fixture
def workflow(mock_kis_client, mock_db_manager, mock_config):
    """워크플로우 인스턴스"""
    return AnalysisWorkflow(
        kis_client=mock_kis_client,
        db_manager=mock_db_manager,
        config=mock_config
    )


class TestAnalysisWorkflow:
    """자동 분석 워크플로우 테스트"""
    
    @pytest.mark.asyncio
    async def test_workflow_initialization(self, workflow):
        """워크플로우 초기화 테스트"""
        assert workflow.market_analyzer is not None
        assert workflow.sector_filter is not None
        assert workflow.stock_picker is not None
        assert workflow._is_running is False
        assert workflow._last_execution_time is None
        assert workflow._last_result is None
    
    @pytest.mark.asyncio
    async def test_run_full_analysis_success(self, workflow):
        """전체 분석 워크플로우 성공 테스트"""
        # Mock 데이터 설정
        mock_market_result = MarketAnalysisResult(
            regime=MarketRegime.BULL,
            kospi_data=IndexData(
                index_code='0001',
                current_value=2500.0,
                ma20=2450.0,
                change_percent=1.5,
                timestamp=datetime.now()
            ),
            kosdaq_data=IndexData(
                index_code='1001',
                current_value=850.0,
                ma20=840.0,
                change_percent=1.2,
                timestamp=datetime.now()
            ),
            risk_parameters=RiskParameters(
                take_profit_percent=5.0,
                stop_loss_percent=3.0,
                regime=MarketRegime.BULL
            ),
            analysis_timestamp=datetime.now(),
            confidence_score=85.0
        )
        
        mock_sector_results = [
            SectorAnalysisResult(
                sector_code='G80',
                sector_name='전기전자',
                price_momentum_score=85.0,
                supply_demand_score=80.0,
                breadth_score=75.0,
                relative_strength_score=90.0,
                combined_score=82.5,
                rank=1,
                analysis_date='2024-01-15'
            )
        ]
        
        mock_leading_sectors = [
            LeadingSector(
                sector_code='G80',
                sector_name='전기전자',
                combined_score=82.5,
                top_stocks=['005930', '000660']
            )
        ]
        
        mock_stock_candidates = [
            StockCandidate(
                ticker='005930',
                stock_name='삼성전자',
                sector='전기전자',
                z_score=-2.5,
                disparity_ratio=-10.0,
                current_price=70000,
                ma20=77000,
                volume=10000000,
                signal_strength=85.0,
                analysis_date='2024-01-15',
                action=TradeAction.BUY
            )
        ]
        
        # Mock 메서드 설정
        workflow.market_analyzer.analyze_market_regime = AsyncMock(
            return_value=mock_market_result
        )
        workflow.sector_filter.analyze_all_sectors = AsyncMock(
            return_value=mock_sector_results
        )
        workflow.sector_filter.get_leading_sectors = AsyncMock(
            return_value=mock_leading_sectors
        )
        workflow.stock_picker.analyze_sector_stocks = AsyncMock(
            return_value=mock_stock_candidates
        )
        
        # 워크플로우 실행
        result = await workflow.run_full_analysis(use_cache=False, save_to_db=True)
        
        # 검증
        assert result.success is True
        assert result.execution_time > 0
        assert result.market_regime_result is not None
        assert result.sector_analysis_results is not None
        assert result.leading_sectors is not None
        assert result.stock_candidates is not None
        assert result.total_sectors_analyzed == 1
        assert result.total_candidates_found >= 0
        assert result.error_message is None
        assert result.failed_step is None
    
    @pytest.mark.asyncio
    async def test_run_full_analysis_already_running(self, workflow):
        """워크플로우 중복 실행 방지 테스트"""
        workflow._is_running = True
        
        result = await workflow.run_full_analysis()
        
        assert result.success is False
        assert "이미 실행 중" in result.error_message
        assert result.failed_step == "startup"
    
    @pytest.mark.asyncio
    async def test_run_market_regime_only(self, workflow):
        """시장 체제 분석 단독 실행 테스트"""
        mock_result = MarketAnalysisResult(
            regime=MarketRegime.BULL,
            kospi_data=IndexData(
                index_code='0001',
                current_value=2500.0,
                ma20=2450.0,
                change_percent=1.5,
                timestamp=datetime.now()
            ),
            kosdaq_data=IndexData(
                index_code='1001',
                current_value=850.0,
                ma20=840.0,
                change_percent=1.2,
                timestamp=datetime.now()
            ),
            risk_parameters=RiskParameters(
                take_profit_percent=5.0,
                stop_loss_percent=3.0,
                regime=MarketRegime.BULL
            ),
            analysis_timestamp=datetime.now(),
            confidence_score=85.0
        )
        
        workflow.market_analyzer.analyze_market_regime = AsyncMock(
            return_value=mock_result
        )
        
        result = await workflow.run_market_regime_only()
        
        assert result is not None
        assert result.regime == MarketRegime.BULL
    
    @pytest.mark.asyncio
    async def test_run_sector_analysis_only(self, workflow):
        """섹터 분석 단독 실행 테스트"""
        mock_leading_sectors = [
            LeadingSector(
                sector_code='G80',
                sector_name='전기전자',
                combined_score=82.5,
                top_stocks=['005930']
            )
        ]
        
        workflow.sector_filter.analyze_all_sectors = AsyncMock(return_value=[])
        workflow.sector_filter.get_leading_sectors = AsyncMock(
            return_value=mock_leading_sectors
        )
        
        result = await workflow.run_sector_analysis_only()
        
        assert result is not None
        assert len(result) == 1
        assert result[0].sector_name == '전기전자'
    
    @pytest.mark.asyncio
    async def test_partial_failure_recovery(self, workflow):
        """부분 실패 복구 테스트 (요구사항 13.5)"""
        # 시장 체제 분석은 성공
        mock_market_result = MarketAnalysisResult(
            regime=MarketRegime.BULL,
            kospi_data=IndexData(
                index_code='0001',
                current_value=2500.0,
                ma20=2450.0,
                change_percent=1.5,
                timestamp=datetime.now()
            ),
            kosdaq_data=IndexData(
                index_code='1001',
                current_value=850.0,
                ma20=840.0,
                change_percent=1.2,
                timestamp=datetime.now()
            ),
            risk_parameters=RiskParameters(
                take_profit_percent=5.0,
                stop_loss_percent=3.0,
                regime=MarketRegime.BULL
            ),
            analysis_timestamp=datetime.now(),
            confidence_score=85.0
        )
        
        workflow.market_analyzer.analyze_market_regime = AsyncMock(
            return_value=mock_market_result
        )
        
        # 섹터 분석은 실패
        workflow.sector_filter.analyze_all_sectors = AsyncMock(
            side_effect=Exception("섹터 분석 실패")
        )
        workflow.sector_filter.get_leading_sectors = AsyncMock(
            side_effect=Exception("섹터 분석 실패")
        )
        
        # 워크플로우 실행 (예외가 발생하지 않아야 함)
        result = await workflow.run_full_analysis(use_cache=False, save_to_db=False)
        
        # 부분 성공 확인
        assert result.market_regime_result is not None
        assert result.sector_analysis_results is None
        assert result.leading_sectors is None
    
    @pytest.mark.asyncio
    async def test_get_workflow_status(self, workflow):
        """워크플로우 상태 조회 테스트"""
        status = workflow.get_workflow_status()
        
        assert 'is_running' in status
        assert 'last_execution_time' in status
        assert 'last_result_success' in status
        assert 'last_result_date' in status
        assert status['is_running'] is False
    
    @pytest.mark.asyncio
    async def test_validate_workflow_components(self, workflow):
        """워크플로우 컴포넌트 검증 테스트"""
        validation_results = await workflow.validate_workflow_components()
        
        assert 'kis_client' in validation_results
        assert 'database' in validation_results
        assert 'market_analyzer' in validation_results
        assert 'sector_filter' in validation_results
        assert 'stock_picker' in validation_results
        
        # Mock 객체이므로 일부는 True여야 함
        assert validation_results['kis_client'] is True
        assert validation_results['database'] is True
    
    @pytest.mark.asyncio
    async def test_cleanup(self, workflow):
        """워크플로우 정리 테스트"""
        # Mock 메서드 설정
        workflow.market_analyzer.clear_cache = Mock()
        workflow.sector_filter.clear_cache = Mock()
        workflow.stock_picker.clear_cache = Mock()
        
        await workflow.cleanup()
        
        # 캐시 초기화 호출 확인
        workflow.market_analyzer.clear_cache.assert_called_once()
        workflow.sector_filter.clear_cache.assert_called_once()
        workflow.stock_picker.clear_cache.assert_called_once()
        
        # 데이터베이스 연결 종료 확인
        workflow.db_manager.disconnect.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_workflow_result_to_dict(self):
        """워크플로우 결과 딕셔너리 변환 테스트"""
        result = WorkflowResult(
            success=True,
            execution_time=5.5,
            analysis_date='2024-01-15',
            total_sectors_analyzed=10,
            total_stocks_analyzed=50,
            total_candidates_found=5
        )
        
        result_dict = result.to_dict()
        
        assert result_dict['success'] is True
        assert result_dict['execution_time'] == 5.5
        assert result_dict['analysis_date'] == '2024-01-15'
        assert result_dict['statistics']['total_sectors_analyzed'] == 10
        assert result_dict['statistics']['total_stocks_analyzed'] == 50
        assert result_dict['statistics']['total_candidates_found'] == 5
    
    def test_flatten_stock_candidates(self, workflow):
        """종목 후보 평탄화 테스트"""
        candidates_by_sector = {
            '전기전자': [
                StockCandidate(
                    ticker='005930',
                    stock_name='삼성전자',
                    sector='전기전자',
                    z_score=-2.5,
                    disparity_ratio=-10.0,
                    current_price=70000,
                    ma20=77000,
                    volume=10000000,
                    signal_strength=85.0,
                    analysis_date='2024-01-15'
                )
            ],
            '화학': [
                StockCandidate(
                    ticker='051910',
                    stock_name='LG화학',
                    sector='화학',
                    z_score=-2.2,
                    disparity_ratio=-9.0,
                    current_price=400000,
                    ma20=440000,
                    volume=500000,
                    signal_strength=80.0,
                    analysis_date='2024-01-15'
                )
            ]
        }
        
        flattened = workflow._flatten_stock_candidates(candidates_by_sector)
        
        assert len(flattened) == 2
        # 신호 강도로 정렬되어야 함
        assert flattened[0].signal_strength >= flattened[1].signal_strength
        assert flattened[0].ticker == '005930'  # 더 높은 신호 강도


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
