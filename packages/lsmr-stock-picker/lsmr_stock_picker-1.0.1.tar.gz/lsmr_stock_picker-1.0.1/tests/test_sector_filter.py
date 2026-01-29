"""
섹터 필터 테스트
"""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch

from lsmr_stock_picker.analyzers.sector_filter import SectorFilter, SectorAnalysisResult
from lsmr_stock_picker.kis_api.client import KISClient
from lsmr_stock_picker.config.settings import SystemConfig


@pytest.fixture
def mock_kis_client():
    """Mock KIS API 클라이언트"""
    client = Mock(spec=KISClient)
    
    # get_sector_data 모의 응답
    async def mock_get_sector_data(sector_code):
        return {
            'sector_code': sector_code,
            'current_price': 1000.0,
            'change_rate': 2.5,
            'ma5': 980.0,
            'ma20': 950.0,
            'ma60': 920.0,
            'high_52week': 1050.0,
            'advancing_stocks': 30,
            'declining_stocks': 10,
            'foreign_net_buy_days': [100.0, 150.0, 200.0],
            'institution_net_buy_days': [50.0, 75.0, 100.0],
            'return_rate': 2.5,
            'market_return': 1.0,
        }
    
    client.get_sector_data = AsyncMock(side_effect=mock_get_sector_data)
    
    # get_sector_stocks 모의 응답
    async def mock_get_sector_stocks(sector_code, limit=5):
        from lsmr_stock_picker.models.data_models import StockData
        return [
            StockData(
                ticker=f"{i:06d}",
                stock_name=f"종목{i}",
                current_price=10000.0,
                change_rate=1.5,
                volume=1000000
            )
            for i in range(1, limit + 1)
        ]
    
    client.get_sector_stocks = AsyncMock(side_effect=mock_get_sector_stocks)
    
    # get_index_data 모의 응답
    async def mock_get_index_data(index_code):
        from lsmr_stock_picker.kis_api.client import IndexData
        return IndexData(
            index_code=index_code,
            index_name="KOSPI",
            current_price=2500.0,
            change_rate=1.0,
            volume=1000000,
            timestamp=datetime.now(),
            ma20=2450.0
        )
    
    client.get_index_data = AsyncMock(side_effect=mock_get_index_data)
    
    return client


@pytest.fixture
def mock_db_manager():
    """Mock 데이터베이스 관리자"""
    db = Mock()
    db.save_sector_analysis = AsyncMock()
    return db


@pytest.fixture
def sector_filter(mock_kis_client, mock_db_manager):
    """SectorFilter 인스턴스"""
    return SectorFilter(
        kis_client=mock_kis_client,
        db_manager=mock_db_manager
    )


class TestSectorFilter:
    """섹터 필터 테스트"""
    
    @pytest.mark.asyncio
    async def test_analyze_single_sector(self, sector_filter):
        """개별 섹터 분석 테스트"""
        result = await sector_filter._analyze_single_sector("G25", "음식료품")
        
        assert isinstance(result, SectorAnalysisResult)
        assert result.sector_code == "G25"
        assert result.sector_name == "음식료품"
        assert 0 <= result.combined_score <= 100
        assert result.analysis_date == datetime.now().strftime('%Y-%m-%d')
    
    @pytest.mark.asyncio
    async def test_price_momentum_evaluation(self, sector_filter):
        """가격 모멘텀 평가 테스트"""
        sector_data = {
            'ma5': 1000.0,
            'ma20': 950.0,
            'ma60': 900.0,
            'current_price': 1020.0,
            'high_52week': 1050.0
        }
        
        score, details = await sector_filter._evaluate_price_momentum(sector_data)
        
        # 5/20/60일 상승 순서 확인
        assert score > 0
        assert details['ma5'] == 1000.0
        assert details['ma20'] == 950.0
        assert details['ma60'] == 900.0
    
    @pytest.mark.asyncio
    async def test_supply_demand_evaluation(self, sector_filter):
        """수급 분석 테스트"""
        sector_data = {
            'foreign_net_buy_days': [100.0, 150.0, 200.0],  # 3일 연속 순매수
            'institution_net_buy_days': [50.0, 75.0, 100.0]  # 3일 연속 순매수
        }
        
        score, details = await sector_filter._evaluate_supply_demand(sector_data)
        
        # 외국인 + 기관 3일 연속 순매수 시 만점
        assert score == 100
        assert details['foreign_net_buy_days'] == 3
        assert details['institution_net_buy_days'] == 3
    
    @pytest.mark.asyncio
    async def test_breadth_evaluation(self, sector_filter):
        """확산 분석 테스트"""
        # 3:1 비율 (상승 30개, 하락 10개)
        sector_data = {
            'advancing_stocks': 30,
            'declining_stocks': 10
        }
        
        score, details = await sector_filter._evaluate_breadth(sector_data)
        
        # 3:1 비율이면 만점
        assert score == 100
        assert details['advancing_stocks'] == 30
        assert details['declining_stocks'] == 10
    
    @pytest.mark.asyncio
    async def test_relative_strength_evaluation(self, sector_filter):
        """상대강도 평가 테스트"""
        # 시장 대비 +2% 이상 (상위 20%)
        sector_data = {
            'return_rate': 3.5,
            'market_return': 1.0
        }
        
        score, details = await sector_filter._evaluate_relative_strength(sector_data)
        
        # 상위 20% 기준 충족 시 만점
        assert score == 100
        assert details['market_relative_return'] == 2.5
    
    def test_combined_score_calculation(self, sector_filter):
        """종합 점수 계산 테스트"""
        score = sector_filter._calculate_combined_score(
            price_score=80.0,
            supply_score=90.0,
            breadth_score=70.0,
            strength_score=85.0
        )
        
        # 가중 평균 (각 25%)
        expected = (80 + 90 + 70 + 85) / 4
        assert score == expected
    
    def test_is_leading_sector(self, sector_filter):
        """주도 섹터 판정 테스트"""
        # 모든 기준 충족
        result = SectorAnalysisResult(
            sector_code="G25",
            sector_name="음식료품",
            price_momentum_score=75.0,
            supply_demand_score=75.0,
            breadth_score=75.0,
            relative_strength_score=85.0,
            combined_score=77.5,
            rank=1,
            analysis_date="2024-01-01"
        )
        
        assert sector_filter._is_leading_sector(result) is True
        
        # 한 기준 미달
        result.breadth_score = 60.0
        assert sector_filter._is_leading_sector(result) is False
    
    def test_count_consecutive_positive(self, sector_filter):
        """연속 양수 일수 계산 테스트"""
        # 3일 연속 양수
        values = [100.0, 150.0, 200.0]
        assert sector_filter._count_consecutive_positive(values) == 3
        
        # 2일 연속 양수, 1일 음수
        values = [100.0, 150.0, -50.0]
        assert sector_filter._count_consecutive_positive(values) == 2
        
        # 모두 음수
        values = [-100.0, -150.0, -200.0]
        assert sector_filter._count_consecutive_positive(values) == 0
    
    @pytest.mark.asyncio
    async def test_analyze_all_sectors(self, sector_filter, mock_db_manager):
        """전체 섹터 분석 테스트"""
        # 캐시 비활성화하여 실제 분석 실행
        results = await sector_filter.analyze_all_sectors(use_cache=False, save_to_db=True)
        
        # 결과 검증
        assert len(results) > 0
        assert all(isinstance(r, SectorAnalysisResult) for r in results)
        
        # 순위 확인 (1부터 시작)
        assert results[0].rank == 1
        
        # 점수 순 정렬 확인
        for i in range(len(results) - 1):
            assert results[i].combined_score >= results[i + 1].combined_score
        
        # 데이터베이스 저장 확인
        assert mock_db_manager.save_sector_analysis.called
    
    @pytest.mark.asyncio
    async def test_get_leading_sectors(self, sector_filter):
        """상위 주도 섹터 조회 테스트"""
        leading_sectors = await sector_filter.get_leading_sectors(count=3, use_cache=False)
        
        # 상위 3개 반환 확인
        assert len(leading_sectors) <= 3
        
        # LeadingSector 객체 확인
        for sector in leading_sectors:
            assert hasattr(sector, 'sector_code')
            assert hasattr(sector, 'sector_name')
            assert hasattr(sector, 'combined_score')
            assert hasattr(sector, 'top_stocks')
    
    @pytest.mark.asyncio
    async def test_cache_functionality(self, sector_filter):
        """캐시 기능 테스트"""
        # 첫 번째 호출 (캐시 없음)
        results1 = await sector_filter.analyze_all_sectors(use_cache=True)
        
        # 두 번째 호출 (캐시 사용)
        results2 = await sector_filter.analyze_all_sectors(use_cache=True)
        
        # 같은 결과 반환 확인
        assert len(results1) == len(results2)
        assert results1[0].sector_code == results2[0].sector_code
        
        # 캐시 상태 확인
        cache_status = sector_filter.get_cache_status()
        assert cache_status['cached'] is True
        assert cache_status['cache_valid'] is True
        
        # 캐시 초기화
        sector_filter.clear_cache()
        cache_status = sector_filter.get_cache_status()
        assert cache_status['cached'] is False
    
    def test_update_thresholds(self, sector_filter):
        """임계값 업데이트 테스트"""
        # 초기 임계값
        assert sector_filter._price_momentum_threshold == 70.0
        
        # 임계값 업데이트
        sector_filter.update_thresholds(
            price_momentum=80.0,
            supply_demand=75.0
        )
        
        assert sector_filter._price_momentum_threshold == 80.0
        assert sector_filter._supply_demand_threshold == 75.0
        
        # 캐시 초기화 확인
        cache_status = sector_filter.get_cache_status()
        assert cache_status['cached'] is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
