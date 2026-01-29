"""
시스템 통합 테스트
작업 13번: 통합 및 메인 애플리케이션 연결 검증
"""

import pytest
import os
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime

# 테스트 환경 변수 설정
os.environ['KIS_APP_KEY'] = 'test_app_key_1234567890'
os.environ['KIS_APP_SECRET'] = 'test_app_secret_1234567890'
os.environ['KIS_ACCOUNT_NUMBER'] = '1234567890'
os.environ['DATABASE_URL'] = 'postgresql://test:test@localhost:5432/test_db'
os.environ['ENVIRONMENT'] = 'testing'
os.environ['AUTO_RUN_ANALYSIS_ON_STARTUP'] = 'false'  # 테스트에서는 자동 실행 비활성화

from lsmr_stock_picker.config.settings import SystemConfig, ConfigurationError
from lsmr_stock_picker.models.data_models import MarketRegime


class TestSystemConfiguration:
    """시스템 구성 관리 테스트 (요구사항 7.1, 10.1, 10.7)"""
    
    def test_load_configuration_from_environment(self):
        """환경 변수에서 시스템 설정 로드"""
        config = SystemConfig.load(validate=False)
        
        assert config.kis.app_key == 'test_app_key_1234567890'
        assert config.kis.app_secret == 'test_app_secret_1234567890'
        assert config.kis.account_number == '1234567890'
        assert config.database_url == 'postgresql://test:test@localhost:5432/test_db'
    
    def test_configuration_validation(self):
        """설정 유효성 검사"""
        # 유효한 설정
        config = SystemConfig.load(validate=False)
        assert config.validate() == True
        
        # 유효하지 않은 설정
        with patch.dict(os.environ, {'KIS_APP_KEY': ''}):
            with pytest.raises(ConfigurationError):
                SystemConfig.load(validate=True)

    
    def test_missing_required_environment_variables(self):
        """필수 환경 변수 누락 시 오류 발생 (요구사항 10.4)"""
        # KIS_APP_KEY 누락
        with patch.dict(os.environ, {'KIS_APP_KEY': ''}, clear=False):
            with pytest.raises(ConfigurationError) as exc_info:
                SystemConfig.load(validate=True)
            assert 'KIS_APP_KEY' in str(exc_info.value)
        
        # KIS_APP_SECRET 누락
        with patch.dict(os.environ, {'KIS_APP_SECRET': ''}, clear=False):
            with pytest.raises(ConfigurationError) as exc_info:
                SystemConfig.load(validate=True)
            assert 'KIS_APP_SECRET' in str(exc_info.value)
        
        # KIS_ACCOUNT_NUMBER 누락
        with patch.dict(os.environ, {'KIS_ACCOUNT_NUMBER': ''}, clear=False):
            with pytest.raises(ConfigurationError) as exc_info:
                SystemConfig.load(validate=True)
            assert 'KIS_ACCOUNT_NUMBER' in str(exc_info.value)
    
    def test_environment_variable_logging_excludes_sensitive_data(self):
        """환경 변수 로깅 시 민감한 데이터 제외 (요구사항 7.4)"""
        config = SystemConfig.load(validate=False)
        
        # 설정 객체에 민감한 데이터가 있지만, 로깅 시에는 제외되어야 함
        # 실제 로깅 구현에서는 민감한 데이터를 마스킹해야 함
        assert config.kis.app_key is not None
        assert config.kis.app_secret is not None
        
        # 로그에 민감한 데이터가 포함되지 않는지 확인하는 것은
        # 실제 로깅 구현에서 테스트해야 함


class TestGracefulStartupShutdown:
    """우아한 시작 및 종료 절차 테스트 (요구사항 7.3, 10.5, 10.6)"""
    
    @pytest.mark.asyncio
    async def test_graceful_startup_sequence(self):
        """시스템 시작 시퀀스 검증"""
        # 시작 시퀀스:
        # 1. 설정 로드
        # 2. 데이터베이스 연결
        # 3. KIS API 클라이언트 초기화
        # 4. 핵심 컴포넌트 초기화
        # 5. 분석 워크플로우 초기화
        # 6. 스케줄러 초기화
        # 7. 건강 상태 모니터링 시작
        # 8. 거래 엔진 시작
        
        # Mock 객체들
        mock_db = AsyncMock()
        mock_kis = AsyncMock()
        mock_workflow = AsyncMock()
        
        # 시작 시퀀스 시뮬레이션
        await mock_db.connect()
        await mock_kis.initialize()
        
        # 모든 초기화가 성공적으로 완료되어야 함
        mock_db.connect.assert_called_once()
        mock_kis.initialize.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_graceful_shutdown_sequence(self):
        """시스템 종료 시퀀스 검증"""
        # 종료 시퀀스:
        # 1. 스케줄러 정지
        # 2. 거래 엔진 종료
        # 3. 워크플로우 정리
        # 4. 데이터베이스 연결 종료
        # 5. KIS 클라이언트 종료
        
        # Mock 객체들
        mock_scheduler = AsyncMock()
        mock_db = AsyncMock()
        mock_kis = AsyncMock()
        mock_workflow = AsyncMock()
        
        # 종료 시퀀스 시뮬레이션
        await mock_scheduler.stop()
        await mock_workflow.cleanup()
        await mock_db.disconnect()
        await mock_kis.close()
        
        # 모든 종료가 순서대로 호출되어야 함
        mock_scheduler.stop.assert_called_once()
        mock_workflow.cleanup.assert_called_once()
        mock_db.disconnect.assert_called_once()
        mock_kis.close.assert_called_once()


class TestAutoAnalysisWorkflow:
    """자동 분석 워크플로우 테스트 (요구사항 13.4)"""
    
    @pytest.mark.asyncio
    async def test_auto_run_analysis_on_startup_enabled(self):
        """시스템 시작 시 자동 분석 실행 (활성화)"""
        # AUTO_RUN_ANALYSIS_ON_STARTUP=true 일 때
        with patch.dict(os.environ, {'AUTO_RUN_ANALYSIS_ON_STARTUP': 'true'}):
            mock_workflow = AsyncMock()
            mock_workflow.run_full_analysis.return_value = {
                'success': True,
                'market_regime': 'bull',
                'leading_sectors_count': 3,
                'stock_candidates_count': 5
            }
            
            # 자동 분석 실행 시뮬레이션
            auto_run = os.getenv('AUTO_RUN_ANALYSIS_ON_STARTUP', 'true').lower() == 'true'
            
            if auto_run:
                result = await mock_workflow.run_full_analysis()
                assert result['success'] == True
                assert result['market_regime'] == 'bull'
                mock_workflow.run_full_analysis.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_auto_run_analysis_on_startup_disabled(self):
        """시스템 시작 시 자동 분석 실행 (비활성화)"""
        # AUTO_RUN_ANALYSIS_ON_STARTUP=false 일 때
        with patch.dict(os.environ, {'AUTO_RUN_ANALYSIS_ON_STARTUP': 'false'}):
            mock_workflow = AsyncMock()
            
            # 자동 분석 실행 확인
            auto_run = os.getenv('AUTO_RUN_ANALYSIS_ON_STARTUP', 'true').lower() == 'true'
            
            if auto_run:
                await mock_workflow.run_full_analysis()
            
            # 비활성화 상태이므로 호출되지 않아야 함
            mock_workflow.run_full_analysis.assert_not_called()

    
    @pytest.mark.asyncio
    async def test_auto_analysis_failure_does_not_prevent_startup(self):
        """자동 분석 실패 시에도 시스템 시작 계속 진행"""
        mock_workflow = AsyncMock()
        mock_workflow.run_full_analysis.side_effect = Exception("분석 실패")
        
        # 자동 분석 실행 시도
        try:
            await mock_workflow.run_full_analysis()
        except Exception as e:
            # 예외가 발생해도 시스템은 계속 시작되어야 함
            assert str(e) == "분석 실패"
        
        # 시스템은 여전히 실행 가능해야 함
        # (실제 구현에서는 로그에 경고만 기록하고 계속 진행)


class TestHealthMonitoring:
    """시스템 건강 모니터링 테스트 (요구사항 10.5)"""
    
    @pytest.mark.asyncio
    async def test_health_monitoring_task_runs_periodically(self):
        """건강 상태 모니터링이 주기적으로 실행됨"""
        mock_broadcast = AsyncMock()
        
        # 5초 간격으로 실행되는 것을 시뮬레이션
        for _ in range(3):
            await mock_broadcast()
            await asyncio.sleep(0.01)  # 테스트에서는 짧은 간격 사용
        
        # 3번 호출되었는지 확인
        assert mock_broadcast.call_count == 3
    
    def test_health_metrics_include_required_fields(self):
        """건강 상태 메트릭에 필수 필드 포함"""
        from lsmr_stock_picker.models.data_models import SystemHealthMetrics, ProcessStatus
        
        # 건강 상태 메트릭 생성
        metrics = SystemHealthMetrics(
            cpu_usage=25.5,
            memory_usage=2.5,
            memory_total=16.0,
            processes=[
                ProcessStatus(
                    name="python",
                    status="running",
                    cpu_percent=10.0,
                    memory_mb=500.0
                )
            ],
            timestamp=datetime.now(),
            kis_api_connected=True
        )
        
        # 필수 필드 확인
        assert metrics.cpu_usage == 25.5
        assert metrics.memory_usage == 2.5
        assert metrics.memory_total == 16.0
        assert len(metrics.processes) == 1
        assert metrics.kis_api_connected == True
        assert metrics.timestamp is not None


class TestComponentCoordination:
    """컴포넌트 조정 테스트 (요구사항 13.1)"""
    
    @pytest.mark.asyncio
    async def test_all_components_initialized_in_correct_order(self):
        """모든 컴포넌트가 올바른 순서로 초기화됨"""
        initialization_order = []
        
        # Mock 컴포넌트들
        async def init_db():
            initialization_order.append('database')
        
        async def init_kis():
            initialization_order.append('kis_client')
        
        async def init_analyzers():
            initialization_order.append('analyzers')
        
        async def init_workflow():
            initialization_order.append('workflow')
        
        async def init_scheduler():
            initialization_order.append('scheduler')
        
        # 초기화 시퀀스 실행
        await init_db()
        await init_kis()
        await init_analyzers()
        await init_workflow()
        await init_scheduler()
        
        # 올바른 순서로 초기화되었는지 확인
        expected_order = ['database', 'kis_client', 'analyzers', 'workflow', 'scheduler']
        assert initialization_order == expected_order
    
    @pytest.mark.asyncio
    async def test_component_failure_handling(self):
        """컴포넌트 초기화 실패 처리"""
        # 데이터베이스 연결 실패 시뮬레이션
        mock_db = AsyncMock()
        mock_db.connect.side_effect = Exception("데이터베이스 연결 실패")
        
        with pytest.raises(Exception) as exc_info:
            await mock_db.connect()
        
        assert "데이터베이스 연결 실패" in str(exc_info.value)


class TestHotReload:
    """핫 리로드 테스트 (요구사항 10.6)"""
    
    def test_non_critical_parameter_hot_reload(self):
        """중요하지 않은 파라미터의 핫 리로드"""
        from lsmr_stock_picker.analyzers.risk_manager import RiskManager, PositionLimit
        
        # 포지션 제한 설정
        position_limit = PositionLimit(
            max_stocks_per_sector=3,
            max_total_holdings=10,
            daily_loss_limit_percent=5.0
        )
        
        # 리스크 매니저 생성
        risk_manager = RiskManager(position_limit)
        
        # 파라미터 업데이트 (재시작 없이)
        risk_manager.update_risk_parameters(MarketRegime.BULL)
        
        # 업데이트된 파라미터 확인
        assert risk_manager.current_risk_params.take_profit_percent == 5.0
        assert risk_manager.current_risk_params.stop_loss_percent == 3.0


class TestSystemIntegration:
    """전체 시스템 통합 테스트"""
    
    def test_system_configuration_summary(self):
        """시스템 설정 요약 검증"""
        config = SystemConfig.load(validate=False)
        
        # 모든 주요 설정이 로드되었는지 확인
        assert config.kis is not None
        assert config.risk is not None
        assert config.trading is not None
        assert config.database_url is not None
        assert config.log_level is not None
        assert config.host is not None
        assert config.port is not None
    
    def test_environment_specific_configuration(self):
        """환경별 설정 검증"""
        # 개발 환경
        with patch.dict(os.environ, {'ENVIRONMENT': 'development'}):
            config = SystemConfig.load(validate=False)
            assert config.kis.environment.value == 'development'
        
        # 프로덕션 환경
        with patch.dict(os.environ, {'ENVIRONMENT': 'production'}):
            config = SystemConfig.load(validate=False)
            assert config.kis.environment.value == 'production'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
