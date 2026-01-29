"""
REST API 엔드포인트 테스트
작업 11번: REST API 엔드포인트를 사용한 FastAPI 서버 구현
"""

import pytest


class TestAPIEndpointsExist:
    """API 엔드포인트 존재 여부 테스트"""
    
    def test_health_endpoint_defined(self):
        """GET /v1/health 엔드포인트가 정의되어 있는지 확인"""
        # main.py 파일에서 엔드포인트 정의 확인
        with open('strategies/lsmr_stock_picker/main.py', 'r') as f:
            content = f.read()
            assert '@app.get("/v1/health"' in content
            assert 'async def health_check()' in content
    
    def test_latest_analysis_endpoint_defined(self):
        """GET /v1/analysis/latest 엔드포인트가 정의되어 있는지 확인"""
        with open('strategies/lsmr_stock_picker/main.py', 'r') as f:
            content = f.read()
            assert '@app.get("/v1/analysis/latest")' in content
            assert 'async def get_latest_analysis()' in content
    
    def test_analysis_history_endpoint_defined(self):
        """GET /v1/analysis/history 엔드포인트가 정의되어 있는지 확인"""
        with open('strategies/lsmr_stock_picker/main.py', 'r') as f:
            content = f.read()
            assert '@app.get("/v1/analysis/history")' in content
            assert 'async def get_analysis_history(' in content
    
    def test_run_analysis_endpoint_defined(self):
        """POST /v1/analysis/run 엔드포인트가 정의되어 있는지 확인"""
        with open('strategies/lsmr_stock_picker/main.py', 'r') as f:
            content = f.read()
            assert '@app.post("/v1/analysis/run")' in content
            assert 'async def run_analysis()' in content
    
    def test_current_market_regime_endpoint_defined(self):
        """GET /v1/market-regime/current 엔드포인트가 정의되어 있는지 확인"""
        with open('strategies/lsmr_stock_picker/main.py', 'r') as f:
            content = f.read()
            assert '@app.get("/v1/market-regime/current")' in content
            assert 'async def get_current_market_regime()' in content
    
    def test_leading_sectors_endpoint_defined(self):
        """GET /v1/sectors/leading 엔드포인트가 정의되어 있는지 확인"""
        with open('strategies/lsmr_stock_picker/main.py', 'r') as f:
            content = f.read()
            assert '@app.get("/v1/sectors/leading")' in content
            assert 'async def get_leading_sectors_endpoint(' in content
    
    def test_stock_candidates_endpoint_defined(self):
        """GET /v1/stocks/candidates 엔드포인트가 정의되어 있는지 확인"""
        with open('strategies/lsmr_stock_picker/main.py', 'r') as f:
            content = f.read()
            assert '@app.get("/v1/stocks/candidates")' in content
            assert 'async def get_stock_candidates(' in content


class TestEndpointImplementation:
    """엔드포인트 구현 세부사항 테스트"""
    
    def test_latest_analysis_uses_db_manager(self):
        """최신 분석 엔드포인트가 데이터베이스 관리자를 사용하는지 확인"""
        with open('strategies/lsmr_stock_picker/main.py', 'r') as f:
            content = f.read()
            # get_latest_analysis 함수 내에서 db_manager 사용 확인
            assert 'db_manager.get_latest_market_regime()' in content
            assert 'db_manager.get_analysis_by_date_range(' in content
    
    def test_run_analysis_saves_to_database(self):
        """분석 실행 엔드포인트가 결과를 데이터베이스에 저장하는지 확인"""
        with open('strategies/lsmr_stock_picker/main.py', 'r') as f:
            content = f.read()
            # run_analysis 함수 내에서 데이터베이스 저장 확인
            assert 'db_manager.save_market_regime(' in content
            assert 'db_manager.save_sector_analysis(' in content
            assert 'db_manager.save_stock_candidate(' in content
    
    def test_endpoints_have_performance_monitoring(self):
        """엔드포인트들이 성능 모니터링 데코레이터를 사용하는지 확인"""
        with open('strategies/lsmr_stock_picker/main.py', 'r') as f:
            content = f.read()
            # 새로운 엔드포인트들이 @monitor_performance 데코레이터 사용
            assert '@monitor_performance("get_latest_analysis"' in content
            assert '@monitor_performance("get_analysis_history"' in content
            assert '@monitor_performance("run_analysis"' in content
            assert '@monitor_performance("get_current_market_regime"' in content
            assert '@monitor_performance("get_leading_sectors"' in content
            assert '@monitor_performance("get_stock_candidates"' in content
    
    def test_endpoints_have_error_handling(self):
        """엔드포인트들이 오류 처리를 구현하는지 확인"""
        with open('strategies/lsmr_stock_picker/main.py', 'r') as f:
            content = f.read()
            # 오류 처리 패턴 확인
            assert 'except HTTPException:' in content
            assert 'error_logger.log_error(' in content
            assert 'raise HTTPException(status_code=' in content


class TestRootEndpointUpdate:
    """루트 엔드포인트 업데이트 테스트"""
    
    def test_root_endpoint_lists_new_endpoints(self):
        """루트 엔드포인트가 새로운 엔드포인트들을 나열하는지 확인"""
        with open('strategies/lsmr_stock_picker/main.py', 'r') as f:
            content = f.read()
            # 루트 엔드포인트에 새로운 엔드포인트 정보 포함 확인
            assert '"analysis_latest": "/v1/analysis/latest"' in content
            assert '"analysis_history": "/v1/analysis/history"' in content
            assert '"analysis_run": "/v1/analysis/run"' in content
            assert '"market_regime_current": "/v1/market-regime/current"' in content
            assert '"sectors_leading": "/v1/sectors/leading"' in content
            assert '"stocks_candidates": "/v1/stocks/candidates"' in content


class TestDatabaseIntegration:
    """데이터베이스 통합 테스트"""
    
    def test_db_manager_imported(self):
        """DatabaseManager가 import되어 있는지 확인"""
        with open('strategies/lsmr_stock_picker/main.py', 'r') as f:
            content = f.read()
            assert 'from .database.manager import DatabaseManager' in content
    
    def test_db_manager_global_variable(self):
        """db_manager 전역 변수가 선언되어 있는지 확인"""
        with open('strategies/lsmr_stock_picker/main.py', 'r') as f:
            content = f.read()
            assert 'db_manager: DatabaseManager = None' in content
    
    def test_db_manager_initialized_in_lifespan(self):
        """lifespan에서 db_manager가 초기화되는지 확인"""
        with open('strategies/lsmr_stock_picker/main.py', 'r') as f:
            content = f.read()
            assert 'db_manager = DatabaseManager(system_config.database_url)' in content
            assert 'await db_manager.connect()' in content
    
    def test_db_manager_disconnected_in_lifespan(self):
        """lifespan에서 db_manager가 종료되는지 확인"""
        with open('strategies/lsmr_stock_picker/main.py', 'r') as f:
            content = f.read()
            assert 'await db_manager.disconnect()' in content


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

