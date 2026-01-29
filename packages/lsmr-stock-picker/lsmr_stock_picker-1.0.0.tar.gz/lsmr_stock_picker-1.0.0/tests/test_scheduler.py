"""
분석 스케줄러 테스트
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch

from analyzers.scheduler import (
    AnalysisScheduler,
    ScheduleConfig,
    ScheduleStatus,
    ScheduleExecutionRecord
)


@pytest.fixture
def schedule_config():
    """스케줄 설정"""
    return ScheduleConfig(
        cron_expression="0 9 * * 1-5",  # 평일 오전 9시
        max_retries=3,
        retry_delay_seconds=1,  # 테스트용 짧은 지연
        execution_timeout_seconds=10,
        max_history_records=10,
        enabled=True
    )


@pytest.fixture
async def mock_analysis_function():
    """Mock 분석 함수"""
    async def analysis():
        await asyncio.sleep(0.1)
        return {
            'success': True,
            'analysis_date': datetime.now().strftime('%Y-%m-%d'),
            'execution_time': 0.1,
            'statistics': {
                'total_sectors_analyzed': 10,
                'total_stocks_analyzed': 50,
                'total_candidates_found': 5
            }
        }
    return analysis


@pytest.fixture
async def scheduler(mock_analysis_function, schedule_config):
    """스케줄러 인스턴스"""
    scheduler = AnalysisScheduler(
        analysis_function=mock_analysis_function,
        config=schedule_config
    )
    yield scheduler
    
    # 정리
    if scheduler._is_running:
        await scheduler.stop()


class TestScheduleConfig:
    """스케줄 설정 테스트"""
    
    def test_default_config(self):
        """기본 설정 테스트"""
        config = ScheduleConfig()
        
        assert config.cron_expression == "0 9 * * 1-5"
        assert config.max_retries == 3
        assert config.retry_delay_seconds == 300
        assert config.enabled is True
    
    def test_config_validation_success(self):
        """설정 검증 성공 테스트"""
        config = ScheduleConfig(
            max_retries=5,
            retry_delay_seconds=60,
            execution_timeout_seconds=3600
        )
        
        assert config.validate() is True
    
    def test_config_validation_invalid_retries(self):
        """잘못된 재시도 횟수 검증 테스트"""
        config = ScheduleConfig(max_retries=-1)
        assert config.validate() is False
        
        config = ScheduleConfig(max_retries=20)
        assert config.validate() is False
    
    def test_config_validation_invalid_delay(self):
        """잘못된 재시도 지연 검증 테스트"""
        config = ScheduleConfig(retry_delay_seconds=-10)
        assert config.validate() is False
    
    def test_config_validation_invalid_timeout(self):
        """잘못된 타임아웃 검증 테스트"""
        config = ScheduleConfig(execution_timeout_seconds=30)
        assert config.validate() is False


class TestAnalysisScheduler:
    """분석 스케줄러 테스트"""
    
    @pytest.mark.asyncio
    async def test_scheduler_initialization(self, scheduler, schedule_config):
        """스케줄러 초기화 테스트"""
        assert scheduler.config == schedule_config
        assert scheduler._is_running is False
        assert len(scheduler.execution_history) == 0
        assert scheduler.current_execution is None
    
    @pytest.mark.asyncio
    async def test_scheduler_start_stop(self, scheduler):
        """스케줄러 시작/정지 테스트"""
        # 시작
        await scheduler.start()
        assert scheduler._is_running is True
        
        # 다음 실행 시간 확인
        next_run = scheduler.get_next_run_time()
        assert next_run is not None
        
        # 정지
        await scheduler.stop()
        assert scheduler._is_running is False
    
    @pytest.mark.asyncio
    async def test_scheduler_disabled(self):
        """비활성화된 스케줄러 테스트"""
        config = ScheduleConfig(enabled=False)
        
        async def dummy_func():
            return {}
        
        scheduler = AnalysisScheduler(dummy_func, config)
        
        await scheduler.start()
        assert scheduler._is_running is False
    
    @pytest.mark.asyncio
    async def test_run_now(self, scheduler):
        """즉시 실행 테스트"""
        # 즉시 실행
        record = await scheduler.run_now()
        
        # 실행 기록 확인
        assert record is not None
        assert record.success is True
        assert record.status == ScheduleStatus.COMPLETED
        assert record.retry_count == 0
        assert len(scheduler.execution_history) == 1
    
    @pytest.mark.asyncio
    async def test_run_now_with_failure_and_retry(self):
        """실패 및 재시도 테스트"""
        call_count = 0
        
        async def failing_analysis():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception("분석 실패")
            return {'success': True}
        
        config = ScheduleConfig(
            max_retries=3,
            retry_delay_seconds=0.1
        )
        
        scheduler = AnalysisScheduler(failing_analysis, config)
        
        # 즉시 실행 (2번 실패 후 성공)
        record = await scheduler.run_now()
        
        # 재시도 확인
        assert call_count == 3
        assert record.success is True
        assert record.retry_count == 2
        
        await scheduler.stop()
    
    @pytest.mark.asyncio
    async def test_run_now_max_retries_exceeded(self):
        """최대 재시도 횟수 초과 테스트"""
        async def always_failing_analysis():
            raise Exception("항상 실패")
        
        config = ScheduleConfig(
            max_retries=2,
            retry_delay_seconds=0.1
        )
        
        scheduler = AnalysisScheduler(always_failing_analysis, config)
        
        # 즉시 실행 (모두 실패)
        record = await scheduler.run_now()
        
        # 실패 확인
        assert record.success is False
        assert record.status == ScheduleStatus.FAILED
        assert record.retry_count == 2
        assert record.error_message is not None
        
        await scheduler.stop()
    
    @pytest.mark.asyncio
    async def test_execution_timeout(self):
        """실행 타임아웃 테스트"""
        async def slow_analysis():
            await asyncio.sleep(5)
            return {'success': True}
        
        config = ScheduleConfig(
            execution_timeout_seconds=1,
            max_retries=0
        )
        
        scheduler = AnalysisScheduler(slow_analysis, config)
        
        # 즉시 실행 (타임아웃)
        record = await scheduler.run_now()
        
        # 타임아웃 확인
        assert record.success is False
        assert record.status == ScheduleStatus.FAILED
        assert "타임아웃" in record.error_message
        
        await scheduler.stop()
    
    @pytest.mark.asyncio
    async def test_execution_history(self, scheduler):
        """실행 이력 테스트"""
        # 여러 번 실행
        for _ in range(5):
            await scheduler.run_now()
            await asyncio.sleep(0.1)
        
        # 이력 확인
        history = scheduler.get_execution_history()
        assert len(history) == 5
        
        # 최신순 정렬 확인
        for i in range(len(history) - 1):
            assert history[i].actual_start_time >= history[i + 1].actual_start_time
    
    @pytest.mark.asyncio
    async def test_execution_history_limit(self, scheduler):
        """실행 이력 개수 제한 테스트"""
        # 최대 개수보다 많이 실행
        for _ in range(15):
            await scheduler.run_now()
            await asyncio.sleep(0.05)
        
        # 이력 개수 확인 (최대 10개)
        assert len(scheduler.execution_history) == 10
    
    @pytest.mark.asyncio
    async def test_execution_history_filter(self, scheduler):
        """실행 이력 필터링 테스트"""
        # 실행
        await scheduler.run_now()
        
        # 성공 필터
        success_history = scheduler.get_execution_history(
            status_filter=ScheduleStatus.COMPLETED
        )
        assert len(success_history) == 1
        
        # 실패 필터
        failed_history = scheduler.get_execution_history(
            status_filter=ScheduleStatus.FAILED
        )
        assert len(failed_history) == 0
    
    @pytest.mark.asyncio
    async def test_get_last_execution(self, scheduler):
        """마지막 실행 기록 조회 테스트"""
        # 실행 전
        assert scheduler.get_last_execution() is None
        
        # 실행
        await scheduler.run_now()
        
        # 마지막 실행 확인
        last_execution = scheduler.get_last_execution()
        assert last_execution is not None
        assert last_execution.success is True
    
    @pytest.mark.asyncio
    async def test_execution_statistics(self, scheduler):
        """실행 통계 테스트"""
        # 초기 통계
        stats = scheduler.get_execution_statistics()
        assert stats['total_executions'] == 0
        assert stats['successful_executions'] == 0
        assert stats['failed_executions'] == 0
        assert stats['success_rate'] == 0.0
        
        # 성공 실행
        await scheduler.run_now()
        await scheduler.run_now()
        
        # 통계 확인
        stats = scheduler.get_execution_statistics()
        assert stats['total_executions'] == 2
        assert stats['successful_executions'] == 2
        assert stats['failed_executions'] == 0
        assert stats['success_rate'] == 100.0
        assert stats['average_execution_time'] > 0
    
    @pytest.mark.asyncio
    async def test_scheduler_status(self, scheduler):
        """스케줄러 상태 조회 테스트"""
        # 시작 전
        status = scheduler.get_scheduler_status()
        assert status['is_running'] is False
        assert status['enabled'] is True
        assert status['next_run_time'] is None
        
        # 시작 후
        await scheduler.start()
        status = scheduler.get_scheduler_status()
        assert status['is_running'] is True
        assert status['next_run_time'] is not None
        
        await scheduler.stop()
    
    @pytest.mark.asyncio
    async def test_update_schedule(self, scheduler):
        """스케줄 업데이트 테스트"""
        # 시작
        await scheduler.start()
        
        # 원래 다음 실행 시간
        original_next_run = scheduler.get_next_run_time()
        
        # 스케줄 업데이트 (매일 오후 3시)
        new_cron = "0 15 * * *"
        scheduler.update_schedule(new_cron)
        
        # 업데이트 확인
        assert scheduler.config.cron_expression == new_cron
        new_next_run = scheduler.get_next_run_time()
        assert new_next_run != original_next_run
        
        await scheduler.stop()
    
    @pytest.mark.asyncio
    async def test_clear_history(self, scheduler):
        """이력 초기화 테스트"""
        # 실행
        await scheduler.run_now()
        await scheduler.run_now()
        
        assert len(scheduler.execution_history) == 2
        
        # 초기화
        scheduler.clear_history()
        
        assert len(scheduler.execution_history) == 0
    
    @pytest.mark.asyncio
    async def test_concurrent_execution_prevention(self, scheduler):
        """동시 실행 방지 테스트"""
        async def slow_analysis():
            await asyncio.sleep(1)
            return {'success': True}
        
        scheduler_slow = AnalysisScheduler(slow_analysis, scheduler.config)
        
        # 첫 번째 실행 시작
        task1 = asyncio.create_task(scheduler_slow.run_now())
        await asyncio.sleep(0.1)
        
        # 두 번째 실행 시도 (실패해야 함)
        with pytest.raises(Exception) as exc_info:
            await scheduler_slow.run_now()
        
        assert "이미 분석이 실행 중입니다" in str(exc_info.value)
        
        # 첫 번째 실행 완료 대기
        await task1
        
        await scheduler_slow.stop()


class TestScheduleExecutionRecord:
    """스케줄 실행 기록 테스트"""
    
    def test_execution_record_creation(self):
        """실행 기록 생성 테스트"""
        now = datetime.now()
        record = ScheduleExecutionRecord(
            execution_id="test_001",
            scheduled_time=now,
            actual_start_time=now,
            status=ScheduleStatus.RUNNING
        )
        
        assert record.execution_id == "test_001"
        assert record.status == ScheduleStatus.RUNNING
        assert record.success is False
        assert record.retry_count == 0
    
    def test_execution_record_to_dict(self):
        """실행 기록 딕셔너리 변환 테스트"""
        now = datetime.now()
        record = ScheduleExecutionRecord(
            execution_id="test_001",
            scheduled_time=now,
            actual_start_time=now,
            end_time=now + timedelta(seconds=10),
            status=ScheduleStatus.COMPLETED,
            success=True,
            execution_duration=10.0,
            result_summary={'total_candidates': 5}
        )
        
        record_dict = record.to_dict()
        
        assert record_dict['execution_id'] == "test_001"
        assert record_dict['status'] == "completed"
        assert record_dict['success'] is True
        assert record_dict['execution_duration'] == 10.0
        assert record_dict['result_summary']['total_candidates'] == 5
