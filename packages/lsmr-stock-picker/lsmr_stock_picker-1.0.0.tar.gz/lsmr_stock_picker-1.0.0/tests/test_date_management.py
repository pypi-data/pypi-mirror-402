"""
날짜 기반 데이터 관리 테스트

요구사항:
- 12.4: 날짜 형식 검증 (YYYY-MM-DD)
- 12.5: 중복 레코드 처리 (upsert)
- 12.6: 날짜 범위 쿼리 및 집계
"""

import pytest
from datetime import date, timedelta
from database.manager import DatabaseManager, validate_date_format, format_date
from utils.error_handling import DatabaseError


class TestDateValidation:
    """날짜 형식 검증 테스트 (요구사항 12.4)"""
    
    def test_valid_date_format(self):
        """유효한 날짜 형식 검증"""
        assert validate_date_format("2024-01-15") is True
        assert validate_date_format("2024-12-31") is True
        assert validate_date_format("2023-06-01") is True
    
    def test_invalid_date_format(self):
        """잘못된 날짜 형식 검증"""
        assert validate_date_format("2024/01/15") is False
        assert validate_date_format("15-01-2024") is False
        assert validate_date_format("2024-1-5") is False
        assert validate_date_format("24-01-15") is False
    
    def test_invalid_date_values(self):
        """잘못된 날짜 값 검증"""
        assert validate_date_format("2024-13-01") is False  # 잘못된 월
        assert validate_date_format("2024-02-30") is False  # 잘못된 일
        assert validate_date_format("2024-00-15") is False  # 잘못된 월
    
    def test_format_date(self):
        """날짜 객체를 문자열로 변환"""
        test_date = date(2024, 1, 15)
        assert format_date(test_date) == "2024-01-15"
        
        test_date = date(2023, 12, 31)
        assert format_date(test_date) == "2023-12-31"


@pytest.mark.asyncio
class TestUpsertLogic:
    """중복 레코드 처리 (upsert) 테스트 (요구사항 12.5)"""
    
    async def test_market_regime_upsert(self, db_manager: DatabaseManager):
        """시장 체제 데이터 upsert 테스트"""
        analysis_date = "2024-01-15"
        
        # 첫 번째 저장
        await db_manager.save_market_regime(
            regime="bull",
            kospi_value=2500.0,
            kosdaq_value=850.0,
            kospi_ma20=2450.0,
            kosdaq_ma20=840.0,
            take_profit_percent=5.0,
            stop_loss_percent=3.0,
            analysis_date=analysis_date
        )
        
        # 동일 날짜에 다시 저장 (업데이트)
        await db_manager.save_market_regime(
            regime="neutral",
            kospi_value=2480.0,
            kosdaq_value=845.0,
            kospi_ma20=2450.0,
            kosdaq_ma20=840.0,
            take_profit_percent=3.0,
            stop_loss_percent=2.5,
            analysis_date=analysis_date
        )
        
        # 결과 확인
        result = await db_manager.get_analysis_by_date(analysis_date)
        market_data = result['market_regime']
        
        assert market_data is not None
        assert market_data['market_regime'] == "neutral"
        assert market_data['kospi_value'] == 2480.0
        assert market_data['take_profit_percent'] == 3.0
    
    async def test_sector_analysis_upsert(self, db_manager: DatabaseManager):
        """섹터 분석 데이터 upsert 테스트"""
        analysis_date = "2024-01-15"
        sector_code = "IT"
        
        # 첫 번째 저장
        await db_manager.save_sector_analysis(
            sector_code=sector_code,
            sector_name="정보기술",
            price_momentum_score=80.0,
            supply_demand_score=75.0,
            breadth_score=70.0,
            relative_strength_score=85.0,
            combined_score=77.5,
            rank=1,
            analysis_date=analysis_date
        )
        
        # 동일 날짜, 동일 섹터에 다시 저장 (업데이트)
        await db_manager.save_sector_analysis(
            sector_code=sector_code,
            sector_name="정보기술",
            price_momentum_score=85.0,
            supply_demand_score=80.0,
            breadth_score=75.0,
            relative_strength_score=90.0,
            combined_score=82.5,
            rank=1,
            analysis_date=analysis_date
        )
        
        # 결과 확인
        result = await db_manager.get_analysis_by_date(analysis_date)
        sector_data = result['sector_analysis']
        
        assert len(sector_data) == 1
        assert sector_data[0]['combined_score'] == 82.5
        assert sector_data[0]['price_momentum_score'] == 85.0
    
    async def test_stock_candidate_upsert(self, db_manager: DatabaseManager):
        """종목 후보 데이터 upsert 테스트"""
        analysis_date = "2024-01-15"
        ticker = "005930"
        
        # 첫 번째 저장
        await db_manager.save_stock_candidate(
            ticker=ticker,
            stock_name="삼성전자",
            sector="반도체",
            z_score=-2.1,
            disparity_ratio=91.5,
            current_price=70000,
            ma20=76500,
            volume=10000000,
            signal_strength=85.0,
            analysis_date=analysis_date
        )
        
        # 동일 날짜, 동일 종목에 다시 저장 (업데이트)
        await db_manager.save_stock_candidate(
            ticker=ticker,
            stock_name="삼성전자",
            sector="반도체",
            z_score=-2.3,
            disparity_ratio=90.0,
            current_price=69000,
            ma20=76500,
            volume=12000000,
            signal_strength=90.0,
            analysis_date=analysis_date
        )
        
        # 결과 확인
        result = await db_manager.get_analysis_by_date(analysis_date)
        stock_data = result['stock_candidates']
        
        assert len(stock_data) == 1
        assert stock_data[0]['z_score'] == -2.3
        assert stock_data[0]['current_price'] == 69000
        assert stock_data[0]['signal_strength'] == 90.0


@pytest.mark.asyncio
class TestDateRangeQueries:
    """날짜 범위 쿼리 테스트 (요구사항 12.6)"""
    
    async def test_date_range_query(self, db_manager: DatabaseManager):
        """날짜 범위 쿼리 테스트"""
        # 여러 날짜에 데이터 저장
        dates = ["2024-01-15", "2024-01-16", "2024-01-17"]
        
        for i, analysis_date in enumerate(dates):
            await db_manager.save_market_regime(
                regime="bull" if i % 2 == 0 else "neutral",
                kospi_value=2500.0 + i * 10,
                kosdaq_value=850.0 + i * 5,
                kospi_ma20=2450.0,
                kosdaq_ma20=840.0,
                take_profit_percent=5.0,
                stop_loss_percent=3.0,
                analysis_date=analysis_date
            )
        
        # 날짜 범위 쿼리
        result = await db_manager.get_analysis_by_date_range("2024-01-15", "2024-01-17")
        
        assert len(result['market_regime']) == 3
        assert result['market_regime'][0]['analysis_date'].strftime('%Y-%m-%d') in dates
    
    async def test_invalid_date_range_format(self, db_manager: DatabaseManager):
        """잘못된 날짜 형식으로 범위 쿼리 시 오류 발생"""
        with pytest.raises(DatabaseError) as exc_info:
            await db_manager.get_analysis_by_date_range("2024/01/15", "2024-01-17")
        
        assert "잘못된 시작 날짜 형식" in str(exc_info.value)
        
        with pytest.raises(DatabaseError) as exc_info:
            await db_manager.get_analysis_by_date_range("2024-01-15", "2024/01/17")
        
        assert "잘못된 종료 날짜 형식" in str(exc_info.value)


@pytest.mark.asyncio
class TestDailyAggregates:
    """날짜별 집계 테스트 (요구사항 12.6)"""
    
    async def test_daily_aggregates(self, db_manager: DatabaseManager):
        """날짜별 집계 데이터 조회 테스트"""
        # 테스트 데이터 저장
        dates = ["2024-01-15", "2024-01-16"]
        
        for analysis_date in dates:
            # 시장 체제
            await db_manager.save_market_regime(
                regime="bull",
                kospi_value=2500.0,
                kosdaq_value=850.0,
                kospi_ma20=2450.0,
                kosdaq_ma20=840.0,
                take_profit_percent=5.0,
                stop_loss_percent=3.0,
                analysis_date=analysis_date
            )
            
            # 섹터 분석
            await db_manager.save_sector_analysis(
                sector_code="IT",
                sector_name="정보기술",
                price_momentum_score=80.0,
                supply_demand_score=75.0,
                breadth_score=70.0,
                relative_strength_score=85.0,
                combined_score=77.5,
                rank=1,
                analysis_date=analysis_date
            )
            
            # 종목 후보
            await db_manager.save_stock_candidate(
                ticker="005930",
                stock_name="삼성전자",
                sector="반도체",
                z_score=-2.1,
                disparity_ratio=91.5,
                current_price=70000,
                ma20=76500,
                volume=10000000,
                signal_strength=85.0,
                analysis_date=analysis_date
            )
        
        # 집계 데이터 조회
        aggregates = await db_manager.get_daily_aggregates("2024-01-15", "2024-01-16")
        
        # 시장 체제 분포 확인
        assert 'market_regime_distribution' in aggregates
        assert len(aggregates['market_regime_distribution']) > 0
        
        # 평균 섹터 점수 확인
        assert 'avg_sector_scores' in aggregates
        assert len(aggregates['avg_sector_scores']) == 2
        
        # 평균 종목 지표 확인
        assert 'avg_stock_metrics' in aggregates
        assert len(aggregates['avg_stock_metrics']) == 2
        
        # 일별 레코드 수 확인
        assert 'daily_counts' in aggregates
        assert len(aggregates['daily_counts']) == 2


@pytest.mark.asyncio
class TestDateValidationInSave:
    """저장 시 날짜 검증 테스트 (요구사항 12.4)"""
    
    async def test_invalid_date_in_market_regime_save(self, db_manager: DatabaseManager):
        """시장 체제 저장 시 잘못된 날짜 형식 오류"""
        with pytest.raises(DatabaseError) as exc_info:
            await db_manager.save_market_regime(
                regime="bull",
                kospi_value=2500.0,
                kosdaq_value=850.0,
                kospi_ma20=2450.0,
                kosdaq_ma20=840.0,
                take_profit_percent=5.0,
                stop_loss_percent=3.0,
                analysis_date="2024/01/15"  # 잘못된 형식
            )
        
        assert "잘못된 날짜 형식" in str(exc_info.value)
    
    async def test_invalid_date_in_sector_save(self, db_manager: DatabaseManager):
        """섹터 분석 저장 시 잘못된 날짜 형식 오류"""
        with pytest.raises(DatabaseError) as exc_info:
            await db_manager.save_sector_analysis(
                sector_code="IT",
                sector_name="정보기술",
                price_momentum_score=80.0,
                supply_demand_score=75.0,
                breadth_score=70.0,
                relative_strength_score=85.0,
                combined_score=77.5,
                rank=1,
                analysis_date="15-01-2024"  # 잘못된 형식
            )
        
        assert "잘못된 날짜 형식" in str(exc_info.value)
    
    async def test_invalid_date_in_stock_save(self, db_manager: DatabaseManager):
        """종목 후보 저장 시 잘못된 날짜 형식 오류"""
        with pytest.raises(DatabaseError) as exc_info:
            await db_manager.save_stock_candidate(
                ticker="005930",
                stock_name="삼성전자",
                sector="반도체",
                z_score=-2.1,
                disparity_ratio=91.5,
                current_price=70000,
                ma20=76500,
                volume=10000000,
                signal_strength=85.0,
                analysis_date="2024-1-5"  # 잘못된 형식
            )
        
        assert "잘못된 날짜 형식" in str(exc_info.value)
