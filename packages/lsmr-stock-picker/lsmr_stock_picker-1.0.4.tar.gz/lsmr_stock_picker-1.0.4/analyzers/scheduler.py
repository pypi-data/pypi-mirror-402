"""
분석 스케줄러 (Analysis Scheduler)
cron 기반 스케줄링을 사용하여 자동 일별 분석 실행

요구사항 13.7: 예약된 분석이 구성되면, 시스템은 자동 일별 실행을 위한 cron 기반 스케줄링을 지원한다
"""

import asyncio
import logging
from datetime import datetime, time
from typing import Optional, Callable, Dict, Any, List
from dataclasses import dataclass, field
from enum import Enum

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR, JobExecutionEvent

try:
    from utils.error_handling import LSMRError, handle_error_with_retry
except ImportError:
    # 테스트 환경에서는 간단한 예외 클래스 사용
    class LSMRError(Exception):
        pass


logger = logging.getLogger(__name__)


class ScheduleStatus(Enum):
    """스케줄 상태"""
    IDLE = "idle"  # 대기 중
    RUNNING = "running"  # 실행 중
    COMPLETED = "completed"  # 완료
    FAILED = "failed"  # 실패
    RETRYING = "retrying"  # 재시도 중


@dataclass
class ScheduleExecutionRecord:
    """스케줄 실행 기록"""
    execution_id: str
    scheduled_time: datetime
    actual_start_time: datetime
    end_time: Optional[datetime] = None
    status: ScheduleStatus = ScheduleStatus.RUNNING
    success: bool = False
    error_message: Optional[str] = None
    retry_count: int = 0
    execution_duration: float = 0.0
    result_summary: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            'execution_id': self.execution_id,
            'scheduled_time': self.scheduled_time.isoformat(),
            'actual_start_time': self.actual_start_time.isoformat(),
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'status': self.status.value,
            'success': self.success,
            'error_message': self.error_message,
            'retry_count': self.retry_count,
            'execution_duration': self.execution_duration,
            'result_summary': self.result_summary
        }


@dataclass
class ScheduleConfig:
    """스케줄 설정"""
    # Cron 표현식 (기본값: 평일 오전 9시)
    cron_expression: str = "0 9 * * 1-5"
    
    # 재시도 설정
    max_retries: int = 3
    retry_delay_seconds: int = 300  # 5분
    
    # 타임아웃 설정
    execution_timeout_seconds: int = 3600  # 1시간
    
    # 실행 이력 보관 설정
    max_history_records: int = 100
    
    # 스케줄 활성화 여부
    enabled: bool = True
    
    def validate(self) -> bool:
        """설정 검증"""
        if self.max_retries < 0 or self.max_retries > 10:
            logger.error(f"잘못된 max_retries 값: {self.max_retries}")
            return False
        
        if self.retry_delay_seconds < 0:
            logger.error(f"잘못된 retry_delay_seconds 값: {self.retry_delay_seconds}")
            return False
        
        if self.execution_timeout_seconds < 1:
            logger.error(f"잘못된 execution_timeout_seconds 값: {self.execution_timeout_seconds}")
            return False
        
        return True


class AnalysisScheduler:
    """
    분석 스케줄러
    
    cron 기반 스케줄링을 사용하여 자동 일별 분석 실행을 관리합니다.
    
    요구사항:
    - 13.7: 자동 일별 실행을 위한 cron 기반 스케줄링 지원
    
    주요 기능:
    - Cron 표현식 기반 스케줄링
    - 자동 일별 분석 실행
    - 실패 시 재시도 로직
    - 스케줄 실행 이력 로깅
    """
    
    def __init__(
        self,
        analysis_function: Callable,
        config: Optional[ScheduleConfig] = None
    ):
        """
        초기화
        
        Args:
            analysis_function: 실행할 분석 함수 (async 함수)
            config: 스케줄 설정 (선택사항)
        """
        self.analysis_function = analysis_function
        self.config = config or ScheduleConfig()
        
        # 설정 검증
        if not self.config.validate():
            raise ValueError("잘못된 스케줄 설정입니다")
        
        # APScheduler 초기화
        self.scheduler = AsyncIOScheduler()
        
        # 실행 이력
        self.execution_history: List[ScheduleExecutionRecord] = []
        
        # 현재 실행 중인 작업
        self.current_execution: Optional[ScheduleExecutionRecord] = None
        
        # 스케줄러 상태
        self._is_running = False
        self._job_id = "analysis_job"
        
        # 이벤트 리스너 등록
        self.scheduler.add_listener(
            self._on_job_executed,
            EVENT_JOB_EXECUTED | EVENT_JOB_ERROR
        )
        
        logger.info(
            f"Analysis Scheduler 초기화 완료 "
            f"(cron: {self.config.cron_expression}, "
            f"max_retries: {self.config.max_retries})"
        )
    
    async def start(self) -> None:
        """
        스케줄러 시작
        
        cron 표현식에 따라 자동 분석 실행을 시작합니다.
        """
        if self._is_running:
            logger.warning("스케줄러가 이미 실행 중입니다")
            return
        
        if not self.config.enabled:
            logger.info("스케줄러가 비활성화되어 있습니다")
            return
        
        try:
            # Cron 트리거 생성
            trigger = CronTrigger.from_crontab(self.config.cron_expression)
            
            # 작업 추가
            self.scheduler.add_job(
                self._execute_scheduled_analysis,
                trigger=trigger,
                id=self._job_id,
                name="자동 분석 실행",
                replace_existing=True,
                max_instances=1  # 동시 실행 방지
            )
            
            # 스케줄러 시작
            self.scheduler.start()
            self._is_running = True
            
            # 다음 실행 시간 조회
            next_run = self.get_next_run_time()
            next_run_str = next_run.strftime('%Y-%m-%d %H:%M:%S') if next_run else "없음"
            
            logger.info(
                f"스케줄러 시작 완료 "
                f"(cron: {self.config.cron_expression}, "
                f"다음 실행: {next_run_str})"
            )
            
        except Exception as e:
            logger.error(f"스케줄러 시작 실패: {e}", exc_info=True)
            raise LSMRError(f"스케줄러 시작 실패: {e}")
    
    async def stop(self) -> None:
        """
        스케줄러 정지
        
        실행 중인 작업이 완료될 때까지 대기한 후 스케줄러를 정지합니다.
        """
        if not self._is_running:
            logger.warning("스케줄러가 실행 중이 아닙니다")
            return
        
        try:
            logger.info("스케줄러 정지 중...")
            
            # 현재 실행 중인 작업 대기
            if self.current_execution:
                logger.info("현재 실행 중인 작업 완료 대기 중...")
                # 최대 60초 대기
                for _ in range(60):
                    if not self.current_execution or self.current_execution.status in [
                        ScheduleStatus.COMPLETED,
                        ScheduleStatus.FAILED
                    ]:
                        break
                    await asyncio.sleep(1)
            
            # 스케줄러 종료
            self.scheduler.shutdown(wait=True)
            self._is_running = False
            
            logger.info("스케줄러 정지 완료")
            
        except Exception as e:
            logger.error(f"스케줄러 정지 오류: {e}", exc_info=True)
            raise LSMRError(f"스케줄러 정지 오류: {e}")
    
    async def _execute_scheduled_analysis(self) -> None:
        """
        예약된 분석 실행
        
        실패 시 재시도 로직을 포함합니다.
        """
        execution_id = f"exec_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        scheduled_time = datetime.now()
        
        # 실행 기록 생성
        record = ScheduleExecutionRecord(
            execution_id=execution_id,
            scheduled_time=scheduled_time,
            actual_start_time=datetime.now(),
            status=ScheduleStatus.RUNNING
        )
        
        self.current_execution = record
        
        logger.info("=" * 80)
        logger.info(f"예약된 분석 실행 시작: {execution_id}")
        logger.info("=" * 80)
        
        retry_count = 0
        last_error = None
        
        # 재시도 로직
        while retry_count <= self.config.max_retries:
            try:
                # 분석 함수 실행
                start_time = datetime.now()
                
                # 타임아웃 설정
                result = await asyncio.wait_for(
                    self.analysis_function(),
                    timeout=self.config.execution_timeout_seconds
                )
                
                # 실행 시간 계산
                execution_duration = (datetime.now() - start_time).total_seconds()
                
                # 성공 처리
                record.end_time = datetime.now()
                record.status = ScheduleStatus.COMPLETED
                record.success = True
                record.retry_count = retry_count
                record.execution_duration = execution_duration
                record.result_summary = self._extract_result_summary(result)
                
                logger.info("=" * 80)
                logger.info(
                    f"예약된 분석 실행 완료: {execution_id} "
                    f"(소요시간: {execution_duration:.1f}초, "
                    f"재시도: {retry_count}회)"
                )
                logger.info("=" * 80)
                
                break  # 성공 시 루프 종료
                
            except asyncio.TimeoutError:
                last_error = f"실행 타임아웃 ({self.config.execution_timeout_seconds}초)"
                logger.error(f"분석 실행 타임아웃: {execution_id}")
                
            except Exception as e:
                last_error = str(e)
                logger.error(f"분석 실행 오류: {e}", exc_info=True)
            
            # 재시도 처리
            retry_count += 1
            
            if retry_count <= self.config.max_retries:
                record.status = ScheduleStatus.RETRYING
                record.retry_count = retry_count
                
                logger.warning(
                    f"분석 실행 실패 - {self.config.retry_delay_seconds}초 후 재시도 "
                    f"({retry_count}/{self.config.max_retries})"
                )
                
                await asyncio.sleep(self.config.retry_delay_seconds)
            else:
                # 최대 재시도 횟수 초과
                record.end_time = datetime.now()
                record.status = ScheduleStatus.FAILED
                record.success = False
                record.retry_count = retry_count - 1
                record.error_message = last_error
                record.execution_duration = (
                    datetime.now() - record.actual_start_time
                ).total_seconds()
                
                logger.error("=" * 80)
                logger.error(
                    f"예약된 분석 실행 실패: {execution_id} "
                    f"(재시도 {retry_count - 1}회 후 실패)"
                )
                logger.error(f"오류: {last_error}")
                logger.error("=" * 80)
        
        # 실행 이력에 추가
        self._add_to_history(record)
        
        # 현재 실행 초기화
        self.current_execution = None
    
    def _extract_result_summary(self, result: Any) -> Dict[str, Any]:
        """
        분석 결과에서 요약 정보 추출
        
        Args:
            result: 분석 함수 실행 결과
            
        Returns:
            Dict[str, Any]: 요약 정보
        """
        try:
            if hasattr(result, 'to_dict'):
                result_dict = result.to_dict()
            elif isinstance(result, dict):
                result_dict = result
            else:
                return {'raw_result': str(result)}
            
            # 주요 정보만 추출
            summary = {
                'success': result_dict.get('success', False),
                'analysis_date': result_dict.get('analysis_date'),
                'execution_time': result_dict.get('execution_time'),
            }
            
            # 통계 정보 추가
            if 'statistics' in result_dict:
                summary['statistics'] = result_dict['statistics']
            
            # 시장 체제 정보 추가
            if 'market_regime' in result_dict:
                market_regime = result_dict['market_regime']
                if isinstance(market_regime, dict):
                    summary['market_regime'] = market_regime.get('regime')
                else:
                    summary['market_regime'] = str(market_regime)
            
            return summary
            
        except Exception as e:
            logger.warning(f"결과 요약 추출 오류: {e}")
            return {'error': str(e)}
    
    def _add_to_history(self, record: ScheduleExecutionRecord) -> None:
        """
        실행 기록을 이력에 추가
        
        Args:
            record: 실행 기록
        """
        self.execution_history.append(record)
        
        # 최대 이력 개수 제한
        if len(self.execution_history) > self.config.max_history_records:
            self.execution_history = self.execution_history[-self.config.max_history_records:]
        
        # 로그 출력
        logger.info(
            f"실행 이력 추가: {record.execution_id} "
            f"(상태: {record.status.value}, 성공: {record.success})"
        )
    
    def _on_job_executed(self, event: JobExecutionEvent) -> None:
        """
        작업 실행 이벤트 리스너
        
        Args:
            event: 작업 실행 이벤트
        """
        if event.exception:
            logger.error(f"스케줄 작업 실행 오류: {event.exception}")
        else:
            logger.debug(f"스케줄 작업 실행 완료: {event.job_id}")
    
    async def run_now(self) -> ScheduleExecutionRecord:
        """
        즉시 분석 실행 (스케줄과 무관하게)
        
        Returns:
            ScheduleExecutionRecord: 실행 기록
        """
        logger.info("수동 분석 실행 요청")
        
        # 현재 실행 중인 작업이 있는지 확인
        if self.current_execution and self.current_execution.status == ScheduleStatus.RUNNING:
            logger.warning("이미 분석이 실행 중입니다")
            raise LSMRError("이미 분석이 실행 중입니다")
        
        # 분석 실행
        await self._execute_scheduled_analysis()
        
        # 마지막 실행 기록 반환
        if self.execution_history:
            return self.execution_history[-1]
        else:
            raise LSMRError("실행 기록을 찾을 수 없습니다")
    
    def get_execution_history(
        self,
        limit: Optional[int] = None,
        status_filter: Optional[ScheduleStatus] = None
    ) -> List[ScheduleExecutionRecord]:
        """
        실행 이력 조회
        
        Args:
            limit: 최대 결과 수 (선택사항)
            status_filter: 상태 필터 (선택사항)
            
        Returns:
            List[ScheduleExecutionRecord]: 실행 이력 리스트
        """
        history = self.execution_history
        
        # 상태 필터 적용
        if status_filter:
            history = [r for r in history if r.status == status_filter]
        
        # 최신순 정렬
        history = sorted(history, key=lambda x: x.actual_start_time, reverse=True)
        
        # 개수 제한
        if limit:
            history = history[:limit]
        
        return history
    
    def get_last_execution(self) -> Optional[ScheduleExecutionRecord]:
        """
        마지막 실행 기록 조회
        
        Returns:
            Optional[ScheduleExecutionRecord]: 마지막 실행 기록
        """
        if self.execution_history:
            return self.execution_history[-1]
        return None
    
    def get_execution_statistics(self) -> Dict[str, Any]:
        """
        실행 통계 조회
        
        Returns:
            Dict[str, Any]: 실행 통계
        """
        if not self.execution_history:
            return {
                'total_executions': 0,
                'successful_executions': 0,
                'failed_executions': 0,
                'success_rate': 0.0,
                'average_execution_time': 0.0,
                'total_retries': 0
            }
        
        total = len(self.execution_history)
        successful = sum(1 for r in self.execution_history if r.success)
        failed = total - successful
        
        total_duration = sum(r.execution_duration for r in self.execution_history)
        avg_duration = total_duration / total if total > 0 else 0.0
        
        total_retries = sum(r.retry_count for r in self.execution_history)
        
        return {
            'total_executions': total,
            'successful_executions': successful,
            'failed_executions': failed,
            'success_rate': (successful / total * 100) if total > 0 else 0.0,
            'average_execution_time': avg_duration,
            'total_retries': total_retries,
            'average_retries': total_retries / total if total > 0 else 0.0
        }
    
    def get_next_run_time(self) -> Optional[datetime]:
        """
        다음 실행 예정 시간 조회
        
        Returns:
            Optional[datetime]: 다음 실행 시간
        """
        if not self._is_running:
            return None
        
        job = self.scheduler.get_job(self._job_id)
        if job and job.next_run_time:
            return job.next_run_time
        
        return None
    
    def get_scheduler_status(self) -> Dict[str, Any]:
        """
        스케줄러 상태 정보
        
        Returns:
            Dict[str, Any]: 상태 정보
        """
        next_run = self.get_next_run_time()
        last_execution = self.get_last_execution()
        
        return {
            'is_running': self._is_running,
            'enabled': self.config.enabled,
            'cron_expression': self.config.cron_expression,
            'next_run_time': next_run.isoformat() if next_run else None,
            'current_execution': self.current_execution.to_dict() if self.current_execution else None,
            'last_execution': last_execution.to_dict() if last_execution else None,
            'total_executions': len(self.execution_history),
            'max_retries': self.config.max_retries,
            'retry_delay_seconds': self.config.retry_delay_seconds
        }
    
    def update_schedule(self, cron_expression: str) -> None:
        """
        스케줄 업데이트
        
        Args:
            cron_expression: 새로운 cron 표현식
        """
        if not self._is_running:
            logger.warning("스케줄러가 실행 중이 아닙니다")
            return
        
        try:
            # 기존 작업 제거
            self.scheduler.remove_job(self._job_id)
            
            # 새로운 트리거로 작업 추가
            trigger = CronTrigger.from_crontab(cron_expression)
            self.scheduler.add_job(
                self._execute_scheduled_analysis,
                trigger=trigger,
                id=self._job_id,
                name="자동 분석 실행",
                replace_existing=True,
                max_instances=1
            )
            
            # 설정 업데이트
            self.config.cron_expression = cron_expression
            
            next_run = self.get_next_run_time()
            next_run_str = next_run.strftime('%Y-%m-%d %H:%M:%S') if next_run else "없음"
            
            logger.info(
                f"스케줄 업데이트 완료 "
                f"(새 cron: {cron_expression}, 다음 실행: {next_run_str})"
            )
            
        except Exception as e:
            logger.error(f"스케줄 업데이트 실패: {e}", exc_info=True)
            raise LSMRError(f"스케줄 업데이트 실패: {e}")
    
    def clear_history(self) -> None:
        """실행 이력 초기화"""
        self.execution_history.clear()
        logger.info("실행 이력 초기화 완료")
