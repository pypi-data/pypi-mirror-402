"""
LSMR Stock Picker 메인 애플리케이션
FastAPI 서버 및 시스템 초기화
"""

import asyncio
import os
import time
from contextlib import asynccontextmanager
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

# .env 파일 로드 (여러 위치 시도)
env_paths = [
    Path(__file__).parent / '.env',  # lsmr_stock_picker/.env
    Path(__file__).parent.parent / '.env',  # strategies/.env
    Path(__file__).parent.parent.parent / '.env',  # 프로젝트 루트/.env
]

for env_path in env_paths:
    if env_path.exists():
        load_dotenv(env_path)
        break

from config.settings import SystemConfig
from utils.logging import setup_logging, get_logger, PerformanceLogger, ErrorLogger
from utils.error_handling import (
    error_logger, performance_logger, system_monitor, 
    monitor_performance, handle_api_errors, retry_with_backoff,
    LSMRError, APIError, TradingError, SystemError, graceful_degradation
)
from kis_api.client import KISClient
from models.data_models import (
    SystemHealthMetrics, ProcessStatus, Strategy, TradeLog, 
    StrategyStatus, TradeAction, MarketRegime
)
from analyzers.market_regime_analyzer import MarketRegimeAnalyzer
from analyzers.sector_filter import SectorFilter
from analyzers.stock_picker import StockPicker
from analyzers.risk_manager import RiskManager
from analyzers.workflow import AnalysisWorkflow
from analyzers.scheduler import AnalysisScheduler, ScheduleConfig
from database.manager import DatabaseManager

# 로깅 설정
logger = setup_logging()
app_logger = get_logger(__name__)


# Pydantic 모델들
class ParameterUpdate(BaseModel):
    """매개변수 업데이트 요청 모델"""
    takeProfitPercent: float = None
    stopLossPercent: float = None


class StrategyToggleResponse(BaseModel):
    """전략 토글 응답 모델"""
    strategy_id: str
    status: str
    message: str


class EmergencyStopResponse(BaseModel):
    """긴급 정지 응답 모델"""
    status: str
    message: str
    timestamp: str


class HealthResponse(BaseModel):
    """건강 상태 응답 모델"""
    status: str
    system_running: bool
    kis_api_connected: bool
    timestamp: str


class WebSocketManager:
    """WebSocket 연결 관리 및 실시간 데이터 브로드캐스팅"""
    
    def __init__(self):
        self.active_connections: list[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        """WebSocket 연결 수락"""
        await websocket.accept()
        self.active_connections.append(websocket)
        app_logger.info(f"WebSocket 연결 수락: {len(self.active_connections)}개 활성 연결")
    
    def disconnect(self, websocket: WebSocket):
        """WebSocket 연결 해제"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        app_logger.info(f"WebSocket 연결 해제: {len(self.active_connections)}개 활성 연결")
    
    async def broadcast(self, message: Dict[str, Any]):
        """모든 연결된 클라이언트에 메시지 브로드캐스트"""
        if not self.active_connections:
            return
        
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                app_logger.warning(f"WebSocket 메시지 전송 실패: {e}")
                error_logger.log_error(
                    'WEBSOCKET_CONNECTION_LOST',
                    f"WebSocket 메시지 전송 실패: {str(e)}",
                    {'connection_count': len(self.active_connections)}
                )
                disconnected.append(connection)
        
        # 끊어진 연결 정리
        for connection in disconnected:
            self.disconnect(connection)
    
    async def broadcast_trade_log(self, trade_log: TradeLog):
        """거래 로그 브로드캐스트"""
        message = {
            "type": "trade_log",
            "data": trade_log.to_dict()
        }
        await self.broadcast(message)
        app_logger.info(f"거래 로그 브로드캐스트: {trade_log.action} {trade_log.ticker}")
    
    async def broadcast_health_metrics(self, metrics: SystemHealthMetrics):
        """건강 상태 메트릭 브로드캐스트"""
        message = {
            "type": "health_metrics",
            "data": metrics.to_dict()
        }
        await self.broadcast(message)


class StrategyManager:
    """전략 상태 관리"""
    
    def __init__(self):
        self.strategies: Dict[str, Strategy] = {}
        self.initialize_default_strategy()
    
    def initialize_default_strategy(self):
        """기본 전략 초기화"""
        default_strategy = Strategy(
            id="lsmr-001",
            name="LSMR Stock Picker",
            status=StrategyStatus.INACTIVE.value,
            return_rate=0.0,
            account="DEFAULT",
            take_profit_percent=3.0,
            stop_loss_percent=2.5,
            message="시스템 초기화 완료"
        )
        self.strategies[default_strategy.id] = default_strategy
    
    def get_strategy(self, strategy_id: str) -> Strategy:
        """전략 조회"""
        if strategy_id not in self.strategies:
            raise HTTPException(status_code=404, detail=f"전략을 찾을 수 없습니다: {strategy_id}")
        return self.strategies[strategy_id]
    
    def toggle_strategy(self, strategy_id: str) -> Strategy:
        """전략 활성화/비활성화 토글"""
        strategy = self.get_strategy(strategy_id)
        
        if strategy.status == StrategyStatus.ACTIVE.value:
            strategy.status = StrategyStatus.INACTIVE.value
            strategy.message = "전략이 비활성화되었습니다"
        elif strategy.status == StrategyStatus.INACTIVE.value:
            strategy.status = StrategyStatus.ACTIVE.value
            strategy.message = "전략이 활성화되었습니다"
        else:  # ERROR 상태
            strategy.status = StrategyStatus.INACTIVE.value
            strategy.message = "오류 상태에서 비활성화로 변경되었습니다"
        
        return strategy
    
    def update_parameters(self, strategy_id: str, params: Dict[str, Any]) -> Strategy:
        """전략 매개변수 업데이트"""
        strategy = self.get_strategy(strategy_id)
        
        if 'takeProfitPercent' in params:
            strategy.take_profit_percent = params['takeProfitPercent']
        if 'stopLossPercent' in params:
            strategy.stop_loss_percent = params['stopLossPercent']
        
        strategy.message = "매개변수가 업데이트되었습니다"
        return strategy
    
    def set_error_status(self, strategy_id: str, error_message: str):
        """전략 오류 상태 설정"""
        if strategy_id in self.strategies:
            self.strategies[strategy_id].status = StrategyStatus.ERROR.value
            self.strategies[strategy_id].message = error_message
    
    def emergency_stop_all(self):
        """모든 전략 긴급 정지"""
        for strategy in self.strategies.values():
            strategy.status = StrategyStatus.INACTIVE.value
            strategy.message = "긴급 정지로 인한 비활성화"


# 전역 변수
websocket_manager = WebSocketManager()
strategy_manager = StrategyManager()
system_config: SystemConfig = None
kis_client: KISClient = None
market_regime_analyzer: MarketRegimeAnalyzer = None
sector_filter: SectorFilter = None
stock_picker: StockPicker = None
risk_manager: RiskManager = None
db_manager: DatabaseManager = None
analysis_workflow: AnalysisWorkflow = None
analysis_scheduler: AnalysisScheduler = None
system_running = False
emergency_stop_active = False
trading_engine_task: Optional[asyncio.Task] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """애플리케이션 생명주기 관리"""
    global system_config, kis_client, market_regime_analyzer, sector_filter, stock_picker, risk_manager, db_manager, analysis_workflow, analysis_scheduler, system_running, emergency_stop_active, trading_engine_task
    
    try:
        # 시스템 초기화
        app_logger.info("LSMR Stock Picker 시스템 초기화 중...")
        
        # 설정 로드
        try:
            system_config = SystemConfig.load(validate=True)  # 프로덕션에서는 검증 활성화
            if not system_config.validate():
                raise ValueError("시스템 설정이 유효하지 않습니다. KIS API 자격 증명을 확인하세요.")
        except Exception as e:
            error_logger.log_error(
                'CONFIG_ERROR',
                f"시스템 설정 로드 실패: {str(e)}",
                {'function': 'lifespan_startup'}
            )
            raise
        
        # 데이터베이스 관리자 초기화
        try:
            db_manager = DatabaseManager(system_config.database_url)
            await db_manager.connect()
            app_logger.info("데이터베이스 연결 완료")
        except Exception as e:
            error_logger.log_error(
                'DB_CONNECTION_ERROR',
                f"데이터베이스 연결 실패: {str(e)}",
                {'function': 'lifespan_startup'}
            )
            raise
        
        # KIS API 클라이언트 초기화
        try:
            kis_client = KISClient(system_config.kis)
            await kis_client.initialize()
            app_logger.info("KIS API 클라이언트 초기화 완료")
        except Exception as e:
            error_logger.log_error(
                'API_AUTH_ERROR',
                f"KIS API 클라이언트 초기화 실패: {str(e)}",
                {'function': 'lifespan_startup'}
            )
            raise
        
        # 핵심 분석 컴포넌트 초기화
        try:
            market_regime_analyzer = MarketRegimeAnalyzer(kis_client, system_config.risk)
            sector_filter = SectorFilter(kis_client)
            stock_picker = StockPicker(kis_client)
            risk_manager = RiskManager(system_config, kis_client)
            
            # 리스크 매니저 초기화
            await risk_manager.initialize()
            
            app_logger.info("핵심 분석 컴포넌트 초기화 완료")
        except Exception as e:
            error_logger.log_error(
                'SYSTEM_ERROR',
                f"분석 컴포넌트 초기화 실패: {str(e)}",
                {'function': 'lifespan_startup'}
            )
            raise
        
        # 분석 워크플로우 초기화
        try:
            analysis_workflow = AnalysisWorkflow(
                kis_client=kis_client,
                db_manager=db_manager,
                config=system_config
            )
            app_logger.info("분석 워크플로우 초기화 완료")
        except Exception as e:
            error_logger.log_error(
                'SYSTEM_ERROR',
                f"분석 워크플로우 초기화 실패: {str(e)}",
                {'function': 'lifespan_startup'}
            )
            raise
        
        # 분석 스케줄러 초기화 (요구사항 13.7)
        try:
            # 환경 변수에서 스케줄 설정 로드
            schedule_config = ScheduleConfig(
                cron_expression=os.getenv('ANALYSIS_SCHEDULE', '0 9 * * 1-5'),  # 기본값: 평일 오전 9시
                max_retries=int(os.getenv('SCHEDULE_MAX_RETRIES', '3')),
                retry_delay_seconds=int(os.getenv('SCHEDULE_RETRY_DELAY', '300')),
                enabled=os.getenv('SCHEDULE_ENABLED', 'true').lower() == 'true'
            )
            
            # 스케줄러 생성
            analysis_scheduler = AnalysisScheduler(
                analysis_function=analysis_workflow.run_full_analysis,
                config=schedule_config
            )
            
            # 스케줄러 시작
            if schedule_config.enabled:
                await analysis_scheduler.start()
                app_logger.info(f"분석 스케줄러 시작 완료 (cron: {schedule_config.cron_expression})")
            else:
                app_logger.info("분석 스케줄러가 비활성화되어 있습니다")
                
        except Exception as e:
            error_logger.log_error(
                'SYSTEM_ERROR',
                f"분석 스케줄러 초기화 실패: {str(e)}",
                {'function': 'lifespan_startup'}
            )
            # 스케줄러 실패는 치명적이지 않으므로 계속 진행
            app_logger.warning("분석 스케줄러 없이 시스템을 시작합니다")
        
        # 시스템 시작 시 자동 분석 워크플로우 실행 (요구사항 13.1, 13.4)
        try:
            auto_run_analysis = os.getenv('AUTO_RUN_ANALYSIS_ON_STARTUP', 'true').lower() == 'true'
            
            if auto_run_analysis:
                app_logger.info("시스템 시작 시 자동 분석 워크플로우 실행 중...")
                analysis_start = datetime.now()
                
                try:
                    # 전체 분석 워크플로우 실행
                    analysis_result = await analysis_workflow.run_full_analysis()
                    
                    analysis_duration = (datetime.now() - analysis_start).total_seconds()
                    
                    if analysis_result.get('success'):
                        app_logger.info(
                            f"자동 분석 워크플로우 완료 (소요시간: {analysis_duration:.1f}초)\n"
                            f"  - 시장 체제: {analysis_result.get('market_regime', 'N/A')}\n"
                            f"  - 주도 섹터: {analysis_result.get('leading_sectors_count', 0)}개\n"
                            f"  - 종목 후보: {analysis_result.get('stock_candidates_count', 0)}개"
                        )
                    else:
                        app_logger.warning(
                            f"자동 분석 워크플로우 부분 실패: {analysis_result.get('error_message', '알 수 없는 오류')}"
                        )
                        
                except Exception as e:
                    error_logger.log_error(
                        'DATA_PROCESSING_ERROR',
                        f"자동 분석 워크플로우 실행 오류: {str(e)}",
                        {'function': 'lifespan_startup', 'stage': 'auto_analysis'}
                    )
                    # 분석 실패는 치명적이지 않으므로 계속 진행
                    app_logger.warning(f"자동 분석 워크플로우 실패 - 시스템은 계속 시작됩니다: {e}")
            else:
                app_logger.info("자동 분석 워크플로우가 비활성화되어 있습니다 (AUTO_RUN_ANALYSIS_ON_STARTUP=false)")
                
        except Exception as e:
            error_logger.log_error(
                'SYSTEM_ERROR',
                f"자동 분석 워크플로우 설정 오류: {str(e)}",
                {'function': 'lifespan_startup'}
            )
            # 설정 오류는 치명적이지 않으므로 계속 진행
            app_logger.warning("자동 분석 워크플로우 설정 오류 - 시스템은 계속 시작됩니다")
        
        # 건강 상태 모니터링 시작
        try:
            asyncio.create_task(health_monitoring_task())
        except Exception as e:
            error_logger.log_error(
                'SYSTEM_ERROR',
                f"건강 상태 모니터링 시작 실패: {str(e)}",
                {'function': 'lifespan_startup'}
            )
            raise
        
        # 거래 엔진 시작
        try:
            trading_engine_task = asyncio.create_task(trading_engine())
            app_logger.info("거래 엔진 시작")
        except Exception as e:
            error_logger.log_error(
                'SYSTEM_ERROR',
                f"거래 엔진 시작 실패: {str(e)}",
                {'function': 'lifespan_startup'}
            )
            raise
        
        system_running = True
        emergency_stop_active = False
        app_logger.info("LSMR Stock Picker 시스템 초기화 완료")
        
        yield
        
    except Exception as e:
        error_logger.log_error(
            'SYSTEM_ERROR',
            f"시스템 초기화 실패: {str(e)}",
            {'function': 'lifespan_startup'}
        )
        # 초기화 실패 시 전략을 오류 상태로 설정
        strategy_manager.set_error_status("lsmr-001", f"SYSTEM_INIT_ERROR: {str(e)}")
        raise
    finally:
        # 시스템 종료
        try:
            system_running = False
            
            # 스케줄러 정지
            if analysis_scheduler:
                try:
                    await analysis_scheduler.stop()
                    app_logger.info("분석 스케줄러 정지 완료")
                except Exception as e:
                    app_logger.error(f"스케줄러 정지 오류: {e}")
            
            # 거래 엔진 종료
            if trading_engine_task and not trading_engine_task.done():
                trading_engine_task.cancel()
                try:
                    await trading_engine_task
                except asyncio.CancelledError:
                    pass
            
            # 워크플로우 정리
            if analysis_workflow:
                try:
                    await analysis_workflow.cleanup()
                    app_logger.info("분석 워크플로우 정리 완료")
                except Exception as e:
                    app_logger.error(f"워크플로우 정리 오류: {e}")
            
            # 데이터베이스 연결 종료
            if db_manager:
                await db_manager.disconnect()
            
            # KIS 클라이언트 종료
            if kis_client:
                await kis_client.close()
            
            app_logger.info("LSMR Stock Picker 시스템 종료")
        except Exception as e:
            error_logger.log_error(
                'SYSTEM_ERROR',
                f"시스템 종료 오류: {str(e)}",
                {'function': 'lifespan_shutdown'}
            )


# FastAPI 애플리케이션 생성
app = FastAPI(
    title="LSMR Stock Picker",
    description="Leading Sector Mean Reversion 주식 선택 시스템",
    version="1.0.0",
    lifespan=lifespan
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 프로덕션에서는 특정 도메인으로 제한
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@monitor_performance("health_monitoring", 5.0)
async def health_monitoring_task():
    """시스템 건강 상태 모니터링 태스크 - 5초마다 브로드캐스트"""
    import psutil
    from datetime import datetime
    
    while system_running:
        try:
            # 시스템 메트릭 수집
            cpu_usage = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            
            # KIS API 연결 상태 확인
            kis_connected = False
            if kis_client and not emergency_stop_active:
                try:
                    kis_connected = await kis_client.health_check()
                except Exception as e:
                    app_logger.warning(f"KIS API 건강 상태 확인 실패: {e}")
                    kis_connected = False
            
            # 프로세스 상태 수집 (상위 5개)
            processes = []
            try:
                for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_info']):
                    try:
                        if 'python' in proc.info['name'].lower():
                            processes.append(ProcessStatus(
                                name=proc.info['name'],
                                status='running',
                                cpu_percent=proc.info['cpu_percent'] or 0,
                                memory_mb=proc.info['memory_info'].rss / 1024 / 1024 if proc.info['memory_info'] else 0
                            ))
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue
                
                # CPU 사용률 기준으로 정렬하여 상위 5개만 선택
                processes.sort(key=lambda x: x.cpu_percent, reverse=True)
                processes = processes[:5]
                
            except Exception as e:
                app_logger.warning(f"프로세스 정보 수집 실패: {e}")
                processes = []
            
            # 건강 상태 메트릭 생성
            health_metrics = SystemHealthMetrics(
                cpu_usage=cpu_usage,
                memory_usage=memory.used / 1024 / 1024 / 1024,  # GB
                memory_total=memory.total / 1024 / 1024 / 1024,  # GB
                processes=processes,
                timestamp=datetime.now(),
                kis_api_connected=kis_connected
            )
            
            # 데이터 검증
            validation_errors = health_metrics.validate()
            if validation_errors:
                app_logger.warning(f"건강 상태 메트릭 검증 오류: {validation_errors}")
            
            # WebSocket으로 브로드캐스트
            await websocket_manager.broadcast_health_metrics(health_metrics)
            
            # 5초 대기 (요구사항 4.3)
            await asyncio.sleep(system_config.health_broadcast_interval if system_config else 5)
            
        except Exception as e:
            error_logger.log_error(
                'DATA_PROCESSING_ERROR',
                f"건강 상태 모니터링 오류: {str(e)}",
                {'function': 'health_monitoring_task'}
            )
            await asyncio.sleep(5)


@monitor_performance("trading_engine", 60.0)
async def trading_engine():
    """
    핵심 거래 엔진 - Market Regime Analyzer → Sector Filter → Stock Picker → Risk Manager 플로우
    """
    app_logger.info("거래 엔진 시작")
    
    while system_running:
        try:
            # 긴급 정지 또는 패닉 모드 확인
            if emergency_stop_active:
                app_logger.debug("긴급 정지 활성화 - 거래 엔진 대기")
                await asyncio.sleep(10)
                continue
            
            # 활성화된 전략 확인
            active_strategies = [s for s in strategy_manager.strategies.values() 
                               if s.status == StrategyStatus.ACTIVE.value]
            
            if not active_strategies:
                app_logger.debug("활성화된 전략 없음 - 거래 엔진 대기")
                await asyncio.sleep(30)
                continue
            
            app_logger.info("거래 엔진 사이클 시작")
            cycle_start = datetime.now()
            
            # 1단계: 시장 상황 분석
            try:
                app_logger.info("1단계: 시장 상황 분석")
                market_analysis = await market_regime_analyzer.analyze_market_regime()
                
                # 리스크 매개변수 업데이트
                risk_manager.update_risk_parameters(market_analysis.regime)
                
                # 전략 매개변수 업데이트
                for strategy in active_strategies:
                    strategy.take_profit_percent = market_analysis.risk_parameters.take_profit_percent
                    strategy.stop_loss_percent = market_analysis.risk_parameters.stop_loss_percent
                
                app_logger.info(f"시장 상황: {market_analysis.regime.value.upper()} "
                              f"(신뢰도: {market_analysis.confidence_score:.1f}%)")
                
            except Exception as e:
                error_logger.log_error(
                    'DATA_PROCESSING_ERROR',
                    f"시장 상황 분석 오류: {str(e)}",
                    {'function': 'trading_engine', 'stage': 'market_analysis'}
                )
                await asyncio.sleep(60)
                continue
            
            # 2단계: 주도 섹터 식별
            try:
                app_logger.info("2단계: 주도 섹터 식별")
                leading_sectors = await sector_filter.get_leading_sectors(count=3)
                
                if not leading_sectors:
                    app_logger.warning("주도 섹터를 찾을 수 없습니다")
                    await asyncio.sleep(60)
                    continue
                
                app_logger.info(f"주도 섹터 {len(leading_sectors)}개 식별: "
                              f"{[s.sector_name for s in leading_sectors]}")
                
            except Exception as e:
                error_logger.log_error(
                    'DATA_PROCESSING_ERROR',
                    f"주도 섹터 식별 오류: {str(e)}",
                    {'function': 'trading_engine', 'stage': 'sector_analysis'}
                )
                await asyncio.sleep(60)
                continue
            
            # 3단계: 종목 선택 및 신호 생성
            try:
                app_logger.info("3단계: 종목 선택 및 신호 생성")
                buy_candidates = await stock_picker.get_buy_candidates(leading_sectors)
                
                if not buy_candidates:
                    app_logger.info("매수 후보 종목이 없습니다")
                    await asyncio.sleep(60)
                    continue
                
                app_logger.info(f"매수 후보 {len(buy_candidates)}개 발견")
                
                # 분석 요약 로그
                analysis_summary = stock_picker.get_analysis_summary(buy_candidates)
                app_logger.info(f"분석 요약: {analysis_summary}")
                
            except Exception as e:
                error_logger.log_error(
                    'DATA_PROCESSING_ERROR',
                    f"종목 선택 오류: {str(e)}",
                    {'function': 'trading_engine', 'stage': 'stock_selection'}
                )
                await asyncio.sleep(60)
                continue
            
            # 4단계: 리스크 관리 및 거래 실행
            try:
                app_logger.info("4단계: 리스크 관리 및 거래 실행")
                
                # 패닉 모드 확인
                if await risk_manager.check_panic_mode_conditions():
                    app_logger.warning("패닉 모드 활성화 - 거래 중단")
                    continue
                
                # 현재 보유 종목 확인 및 손절매 처리
                current_holdings = await risk_manager.get_current_holdings()
                stop_loss_orders = await risk_manager.check_stop_loss_conditions(current_holdings)
                
                # 손절매 주문 실행
                for stop_order in stop_loss_orders:
                    try:
                        result = await kis_client.execute_order(
                            ticker=stop_order.ticker,
                            action='SELL',
                            quantity=stop_order.quantity,
                            order_type='MARKET'
                        )
                        
                        # 거래 로그 생성
                        await log_trade_event(
                            strategy_id="lsmr-001",
                            action="SELL",
                            ticker=stop_order.ticker,
                            stock_name=stop_order.stock_name,
                            quantity=stop_order.quantity,
                            price=result.get('price', stop_order.current_price),
                            reason=stop_order.reason
                        )
                        
                        app_logger.info(f"손절매 실행: {stop_order.stock_name}")
                        
                    except Exception as e:
                        app_logger.error(f"손절매 실행 오류 ({stop_order.ticker}): {e}")
                
                # 신규 매수 주문 처리
                executed_trades = []
                for candidate in buy_candidates:
                    try:
                        # 포지션 제한 확인
                        can_trade, reason = await risk_manager.validate_position_limits(candidate)
                        if not can_trade:
                            app_logger.info(f"거래 제한: {candidate.ticker} - {reason}")
                            continue
                        
                        # 거래 실행
                        trade_result = await stock_picker.execute_trade(candidate)
                        
                        if trade_result.get('status') == 'SUCCESS':
                            executed_trades.append(trade_result)
                            
                            # 거래 로그 브로드캐스트
                            trade_log = trade_result.get('trade_log')
                            if trade_log:
                                await websocket_manager.broadcast_trade_log(trade_log)
                            
                            app_logger.info(f"매수 실행: {candidate.stock_name}")
                        
                        # API 요청 간격 조절
                        await asyncio.sleep(0.1)
                        
                    except Exception as e:
                        app_logger.error(f"거래 실행 오류 ({candidate.ticker}): {e}")
                
                app_logger.info(f"거래 실행 완료: {len(executed_trades)}건")
                
            except Exception as e:
                error_logger.log_error(
                    'DATA_PROCESSING_ERROR',
                    f"리스크 관리 및 거래 실행 오류: {str(e)}",
                    {'function': 'trading_engine', 'stage': 'risk_management'}
                )
            
            # 사이클 완료
            cycle_duration = (datetime.now() - cycle_start).total_seconds()
            app_logger.info(f"거래 엔진 사이클 완료 (소요시간: {cycle_duration:.1f}초)")
            
            # 다음 사이클까지 대기 (최소 60초)
            await asyncio.sleep(max(60 - cycle_duration, 10))
            
        except Exception as e:
            error_logger.log_error(
                'SYSTEM_ERROR',
                f"거래 엔진 오류: {str(e)}",
                {'function': 'trading_engine'}
            )
            await asyncio.sleep(60)
    
    app_logger.info("거래 엔진 종료")


@monitor_performance("trade_logging", 0.05)
async def log_trade_event(strategy_id: str, action: str, ticker: str, stock_name: str, 
                         quantity: int, price: float, reason: str):
    """거래 이벤트 로깅 및 브로드캐스트"""
    try:
        # 거래 로그 생성 (요구사항 4.1, 4.2)
        trade_log = TradeLog(
            timestamp=datetime.now(),
            strategy=strategy_id,
            action=action,
            stock_name=stock_name,
            ticker=ticker,
            quantity=quantity,
            price=price,
            reason=reason,
            category="Trade"  # 항상 "Trade"로 설정 (요구사항 4.1)
        )
        
        # 데이터 검증
        validation_errors = trade_log.validate()
        if validation_errors:
            error_logger.log_error(
                'DATA_PROCESSING_ERROR',
                f"거래 로그 검증 오류: {validation_errors}",
                {'trade_log': trade_log.to_dict()}
            )
            return
        
        # WebSocket으로 브로드캐스트
        await websocket_manager.broadcast_trade_log(trade_log)
        
        app_logger.info(f"거래 로그 생성: {action} {ticker} {quantity}주 @ {price}원, 이유: {reason}")
        
    except Exception as e:
        error_logger.log_error(
            'DATA_PROCESSING_ERROR',
            f"거래 로그 생성 실패: {str(e)}",
            {'strategy_id': strategy_id, 'action': action, 'ticker': ticker}
        )


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket 엔드포인트"""
    await websocket_manager.connect(websocket)
    try:
        while True:
            # 클라이언트로부터 메시지 대기 (연결 유지용)
            await websocket.receive_text()
    except WebSocketDisconnect:
        websocket_manager.disconnect(websocket)


@app.get("/v1/health", response_model=HealthResponse)
@monitor_performance("health_check", 0.1)
async def health_check():
    """시스템 건강 상태 확인"""
    try:
        kis_connected = False
        if kis_client and not emergency_stop_active:
            try:
                kis_connected = await kis_client.health_check()
            except Exception:
                kis_connected = False
        
        # 시스템 건강 상태 확인
        is_healthy = system_monitor.is_system_healthy()
        
        # 핵심 컴포넌트 상태 확인
        components_healthy = all([
            market_regime_analyzer is not None,
            sector_filter is not None,
            stock_picker is not None,
            risk_manager is not None
        ])
        
        status = "healthy"
        if emergency_stop_active:
            status = "emergency_stop"
        elif not system_running or not kis_connected or not is_healthy or not components_healthy:
            status = "degraded"
        
        return HealthResponse(
            status=status,
            system_running=system_running,
            kis_api_connected=kis_connected,
            timestamp=datetime.now().isoformat()
        )
    except Exception as e:
        error_logger.log_error(
            'DATA_PROCESSING_ERROR',
            f"건강 상태 확인 오류: {str(e)}",
            {'function': 'health_check'}
        )
        raise HTTPException(status_code=500, detail="HEALTH_CHECK_ERROR")


@app.post("/v1/strategies/{strategy_id}/toggle", response_model=StrategyToggleResponse)
@monitor_performance("strategy_toggle", 0.1)
async def toggle_strategy(strategy_id: str):
    """전략 활성화/비활성화 토글"""
    try:
        if emergency_stop_active:
            raise HTTPException(status_code=423, detail="EMERGENCY_STOP_ACTIVE")
        
        # 전략 토글
        strategy = strategy_manager.toggle_strategy(strategy_id)
        
        app_logger.info(f"전략 토글: {strategy_id} -> {strategy.status}")
        
        # 거래 로그 생성 (전략 상태 변경)
        await log_trade_event(
            strategy_id=strategy_id,
            action="SYSTEM",
            ticker="000000",
            stock_name="시스템",
            quantity=0,
            price=0.0,
            reason=f"[전략 {strategy.status}]"
        )
        
        return StrategyToggleResponse(
            strategy_id=strategy_id,
            status=strategy.status,
            message=strategy.message
        )
    except HTTPException:
        raise
    except Exception as e:
        error_logger.log_error(
            'DATA_PROCESSING_ERROR',
            f"전략 토글 오류: {str(e)}",
            {'strategy_id': strategy_id}
        )
        strategy_manager.set_error_status(strategy_id, f"STRATEGY_TOGGLE_ERROR: {str(e)}")
        raise HTTPException(status_code=500, detail="STRATEGY_TOGGLE_ERROR")


@app.post("/v1/system/emergency-stop", response_model=EmergencyStopResponse)
@monitor_performance("emergency_stop", 0.5)
async def emergency_stop():
    """긴급 정지 - 0.5초 내 모든 거래 중단 (요구사항 4.5)"""
    global emergency_stop_active
    
    try:
        start_time = time.time()
        app_logger.warning("긴급 정지 요청 수신")
        
        # 긴급 정지 플래그 설정
        emergency_stop_active = True
        
        # 모든 전략 비활성화
        strategy_manager.emergency_stop_all()
        
        # 실제 구현에서는 다음 작업들을 수행:
        # 1. 진행 중인 주문 취소
        # 2. 포지션 청산 명령
        # 3. 시스템 안전 모드 진입
        
        # 긴급 정지 브로드캐스트
        emergency_message = {
            "type": "emergency_stop",
            "data": {
                "timestamp": datetime.now().isoformat(),
                "message": "긴급 정지가 실행되었습니다",
                "response_time": time.time() - start_time
            }
        }
        await websocket_manager.broadcast(emergency_message)
        
        # 거래 로그 생성
        await log_trade_event(
            strategy_id="system",
            action="EMERGENCY_STOP",
            ticker="000000",
            stock_name="시스템",
            quantity=0,
            price=0.0,
            reason="[긴급 정지 실행]"
        )
        
        response_time = time.time() - start_time
        app_logger.warning(f"긴급 정지 완료 - 응답 시간: {response_time:.3f}초")
        
        # 응답 시간이 0.5초를 초과하면 경고
        if response_time > 0.5:
            error_logger.log_error(
                'EMERGENCY_STOP_TIMEOUT',
                f"긴급 정지 응답 시간 초과: {response_time:.3f}초",
                {'threshold': 0.5, 'actual_time': response_time}
            )
        
        return EmergencyStopResponse(
            status="emergency_stop_executed",
            message="긴급 정지가 실행되었습니다",
            timestamp=datetime.now().isoformat()
        )
    except Exception as e:
        error_logger.log_error(
            'EMERGENCY_STOP_ERROR',
            f"긴급 정지 오류: {str(e)}",
            {'function': 'emergency_stop'}
        )
        raise HTTPException(status_code=500, detail="EMERGENCY_STOP_ERROR")


@app.patch("/v1/strategies/{strategy_id}/parameters")
@monitor_performance("parameter_update", 0.1)
async def update_parameters(strategy_id: str, parameters: ParameterUpdate):
    """전략 매개변수 실시간 업데이트 - 시스템 재시작 없이 적용 (요구사항 4.6)"""
    try:
        if emergency_stop_active:
            raise HTTPException(status_code=423, detail="EMERGENCY_STOP_ACTIVE")
        
        # 매개변수 딕셔너리 생성
        params_dict = {}
        if parameters.takeProfitPercent is not None:
            if parameters.takeProfitPercent <= 0 or parameters.takeProfitPercent > 50:
                raise HTTPException(status_code=400, detail="INVALID_TAKE_PROFIT_PERCENT")
            params_dict['takeProfitPercent'] = parameters.takeProfitPercent
        
        if parameters.stopLossPercent is not None:
            if parameters.stopLossPercent <= 0 or parameters.stopLossPercent > 50:
                raise HTTPException(status_code=400, detail="INVALID_STOP_LOSS_PERCENT")
            params_dict['stopLossPercent'] = parameters.stopLossPercent
        
        if not params_dict:
            raise HTTPException(status_code=400, detail="NO_PARAMETERS_TO_UPDATE")
        
        # 전략 매개변수 업데이트
        strategy = strategy_manager.update_parameters(strategy_id, params_dict)
        
        app_logger.info(f"매개변수 업데이트: {strategy_id}, {params_dict}")
        
        # 거래 로그 생성
        param_str = ", ".join([f"{k}={v}" for k, v in params_dict.items()])
        await log_trade_event(
            strategy_id=strategy_id,
            action="PARAMETER_UPDATE",
            ticker="000000",
            stock_name="시스템",
            quantity=0,
            price=0.0,
            reason=f"[매개변수 업데이트: {param_str}]"
        )
        
        return {
            "strategy_id": strategy_id,
            "updated_parameters": params_dict,
            "message": strategy.message,
            "current_strategy": strategy.to_dict()
        }
    except HTTPException:
        raise
    except Exception as e:
        error_logger.log_error(
            'PARAMETER_UPDATE_ERROR',
            f"매개변수 업데이트 오류: {str(e)}",
            {'strategy_id': strategy_id, 'parameters': parameters.dict()}
        )
        strategy_manager.set_error_status(strategy_id, f"PARAMETER_UPDATE_ERROR: {str(e)}")
        raise HTTPException(status_code=500, detail="PARAMETER_UPDATE_ERROR")


@app.get("/v1/system/status")
@monitor_performance("get_system_status", 0.1)
async def get_system_status():
    """전체 시스템 상태 조회"""
    try:
        # 핵심 컴포넌트 상태
        components_status = {
            'market_regime_analyzer': market_regime_analyzer is not None,
            'sector_filter': sector_filter is not None,
            'stock_picker': stock_picker is not None,
            'risk_manager': risk_manager is not None,
            'kis_client': kis_client is not None
        }
        
        # 현재 시장 상황 (가능한 경우)
        market_regime = None
        if market_regime_analyzer:
            try:
                current_regime = await market_regime_analyzer.get_current_regime()
                market_regime = current_regime.value
            except Exception as e:
                app_logger.warning(f"시장 상황 조회 실패: {e}")
        
        # 리스크 상태 (가능한 경우)
        risk_status = None
        if risk_manager:
            try:
                risk_status = risk_manager.get_risk_status()
            except Exception as e:
                app_logger.warning(f"리스크 상태 조회 실패: {e}")
        
        # 현재 보유 종목 수
        holdings_count = 0
        if risk_manager:
            try:
                holdings = await risk_manager.get_current_holdings()
                holdings_count = len(holdings)
            except Exception as e:
                app_logger.warning(f"보유 종목 조회 실패: {e}")
        
        return {
            'system_running': system_running,
            'emergency_stop_active': emergency_stop_active,
            'components_status': components_status,
            'market_regime': market_regime,
            'risk_status': risk_status,
            'holdings_count': holdings_count,
            'trading_engine_active': trading_engine_task is not None and not trading_engine_task.done(),
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        error_logger.log_error(
            'DATA_PROCESSING_ERROR',
            f"시스템 상태 조회 오류: {str(e)}",
            {'function': 'get_system_status'}
        )
        raise HTTPException(status_code=500, detail="SYSTEM_STATUS_ERROR")


@app.get("/v1/system/components")
@monitor_performance("get_components_status", 0.1)
async def get_components_status():
    """핵심 컴포넌트 상세 상태 조회"""
    try:
        components = {}
        
        # Market Regime Analyzer 상태
        if market_regime_analyzer:
            try:
                cache_status = market_regime_analyzer.get_cache_status()
                components['market_regime_analyzer'] = {
                    'status': 'active',
                    'cache_status': cache_status
                }
            except Exception as e:
                components['market_regime_analyzer'] = {
                    'status': 'error',
                    'error': str(e)
                }
        else:
            components['market_regime_analyzer'] = {'status': 'not_initialized'}
        
        # Sector Filter 상태
        if sector_filter:
            try:
                cache_stats = sector_filter.get_cache_stats()
                components['sector_filter'] = {
                    'status': 'active',
                    'cache_stats': cache_stats
                }
            except Exception as e:
                components['sector_filter'] = {
                    'status': 'error',
                    'error': str(e)
                }
        else:
            components['sector_filter'] = {'status': 'not_initialized'}
        
        # Stock Picker 상태
        if stock_picker:
            components['stock_picker'] = {
                'status': 'active',
                'z_score_threshold': stock_picker.z_score_threshold,
                'disparity_threshold': stock_picker.disparity_threshold
            }
        else:
            components['stock_picker'] = {'status': 'not_initialized'}
        
        # Risk Manager 상태
        if risk_manager:
            try:
                risk_status = risk_manager.get_risk_status()
                components['risk_manager'] = {
                    'status': 'active',
                    'risk_status': risk_status
                }
            except Exception as e:
                components['risk_manager'] = {
                    'status': 'error',
                    'error': str(e)
                }
        else:
            components['risk_manager'] = {'status': 'not_initialized'}
        
        # KIS Client 상태
        if kis_client:
            try:
                is_connected = await kis_client.health_check()
                components['kis_client'] = {
                    'status': 'active',
                    'connected': is_connected
                }
            except Exception as e:
                components['kis_client'] = {
                    'status': 'error',
                    'error': str(e)
                }
        else:
            components['kis_client'] = {'status': 'not_initialized'}
        
        return {
            'components': components,
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        error_logger.log_error(
            'DATA_PROCESSING_ERROR',
            f"컴포넌트 상태 조회 오류: {str(e)}",
            {'function': 'get_components_status'}
        )
        raise HTTPException(status_code=500, detail="COMPONENTS_STATUS_ERROR")


@app.post("/v1/system/trading-engine/start")
@monitor_performance("start_trading_engine", 0.1)
async def start_trading_engine():
    """거래 엔진 시작"""
    global trading_engine_task
    
    try:
        if emergency_stop_active:
            raise HTTPException(status_code=423, detail="EMERGENCY_STOP_ACTIVE")
        
        if trading_engine_task and not trading_engine_task.done():
            return {
                'status': 'already_running',
                'message': '거래 엔진이 이미 실행 중입니다',
                'timestamp': datetime.now().isoformat()
            }
        
        # 거래 엔진 시작
        trading_engine_task = asyncio.create_task(trading_engine())
        
        app_logger.info("거래 엔진 수동 시작")
        
        return {
            'status': 'started',
            'message': '거래 엔진이 시작되었습니다',
            'timestamp': datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        error_logger.log_error(
            'SYSTEM_ERROR',
            f"거래 엔진 시작 오류: {str(e)}",
            {'function': 'start_trading_engine'}
        )
        raise HTTPException(status_code=500, detail="TRADING_ENGINE_START_ERROR")


@app.post("/v1/system/trading-engine/stop")
@monitor_performance("stop_trading_engine", 0.1)
async def stop_trading_engine():
    """거래 엔진 정지"""
    global trading_engine_task
    
    try:
        if not trading_engine_task or trading_engine_task.done():
            return {
                'status': 'already_stopped',
                'message': '거래 엔진이 이미 정지되어 있습니다',
                'timestamp': datetime.now().isoformat()
            }
        
        # 거래 엔진 정지
        trading_engine_task.cancel()
        
        try:
            await trading_engine_task
        except asyncio.CancelledError:
            pass
        
        app_logger.info("거래 엔진 수동 정지")
        
        return {
            'status': 'stopped',
            'message': '거래 엔진이 정지되었습니다',
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        error_logger.log_error(
            'SYSTEM_ERROR',
            f"거래 엔진 정지 오류: {str(e)}",
            {'function': 'stop_trading_engine'}
        )
        raise HTTPException(status_code=500, detail="TRADING_ENGINE_STOP_ERROR")


@app.get("/v1/system/performance")
@monitor_performance("get_system_performance", 0.1)
async def get_system_performance():
    """시스템 성능 메트릭 조회 - 요구사항 8.1, 8.2"""
    try:
        performance_summary = performance_logger.get_performance_summary()
        error_summary = system_monitor.get_error_summary()
        recent_alerts = system_monitor.get_recent_performance_alerts(10)
        
        # 성능 임계값 확인
        signal_avg = performance_logger.get_average_time("신호 생성")
        data_processing_avg = performance_logger.get_average_time("데이터 처리")
        
        performance_status = {
            'signal_generation_compliant': signal_avg <= 0.1,  # 요구사항 8.1: 100ms 미만
            'data_processing_compliant': data_processing_avg <= 0.05,  # 요구사항 8.2: 50ms 미만
            'signal_generation_avg_ms': signal_avg * 1000,
            'data_processing_avg_ms': data_processing_avg * 1000
        }
        
        return {
            "uptime_seconds": system_monitor.get_uptime(),
            "is_healthy": system_monitor.is_system_healthy(),
            "performance_metrics": performance_summary,
            "performance_status": performance_status,
            "error_counts": error_summary,
            "recent_performance_alerts": recent_alerts,
            "degraded_services": list(graceful_degradation.degraded_services),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        error_logger.log_error(
            'DATA_PROCESSING_ERROR',
            f"성능 메트릭 조회 오류: {str(e)}",
            {'function': 'get_system_performance'}
        )
        raise HTTPException(status_code=500, detail="PERFORMANCE_METRICS_ERROR")


@app.get("/v1/system/errors")
@monitor_performance("get_error_summary", 0.1)
async def get_error_summary():
    """오류 요약 정보 조회"""
    try:
        error_summary = system_monitor.get_error_summary()
        recent_alerts = system_monitor.get_recent_performance_alerts(30)
        
        # 오류 분류별 통계
        api_errors = sum(count for code, count in error_summary.items() if 'API' in code)
        trading_errors = sum(count for code, count in error_summary.items() if code in ['INSUFFICIENT_CASH', 'POSITION_LIMIT_EXCEEDED', 'ORDER_REJECTED'])
        system_errors = sum(count for code, count in error_summary.items() if 'SYSTEM' in code or 'MEMORY' in code)
        
        return {
            "total_errors": sum(error_summary.values()),
            "error_breakdown": {
                "api_errors": api_errors,
                "trading_errors": trading_errors,
                "system_errors": system_errors
            },
            "error_details": error_summary,
            "recent_performance_alerts": recent_alerts,
            "system_healthy": system_monitor.is_system_healthy(),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        error_logger.log_error(
            'DATA_PROCESSING_ERROR',
            f"오류 요약 조회 오류: {str(e)}",
            {'function': 'get_error_summary'}
        )
        raise HTTPException(status_code=500, detail="ERROR_SUMMARY_ERROR")


@app.get("/v1/system/degraded-services")
@monitor_performance("get_degraded_services", 0.1)
async def get_degraded_services():
    """성능 저하 서비스 목록 조회"""
    try:
        degraded_services = {}
        for service_name in graceful_degradation.degraded_services:
            fallback_data = graceful_degradation.get_fallback_data(service_name)
            degraded_services[service_name] = {
                "status": "degraded",
                "has_fallback": fallback_data is not None,
                "fallback_type": type(fallback_data).__name__ if fallback_data else None
            }
        
        return {
            "degraded_services": degraded_services,
            "total_degraded": len(degraded_services),
            "system_healthy": system_monitor.is_system_healthy(),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        error_logger.log_error(
            'DATA_PROCESSING_ERROR',
            f"성능 저하 서비스 조회 오류: {str(e)}",
            {'function': 'get_degraded_services'}
        )
        raise HTTPException(status_code=500, detail="DEGRADED_SERVICES_ERROR")


@app.post("/v1/system/restore-service/{service_name}")
@monitor_performance("restore_service", 0.1)
async def restore_service(service_name: str):
    """성능 저하 서비스 복구"""
    try:
        if service_name not in graceful_degradation.degraded_services:
            raise HTTPException(status_code=404, detail=f"서비스 '{service_name}'는 성능 저하 상태가 아닙니다")
        
        graceful_degradation.restore_service(service_name)
        
        app_logger.info(f"서비스 복구 완료: {service_name}")
        
        return {
            "service_name": service_name,
            "status": "restored",
            "message": f"서비스 '{service_name}'가 정상 상태로 복구되었습니다",
            "timestamp": datetime.now().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        error_logger.log_error(
            'DATA_PROCESSING_ERROR',
            f"서비스 복구 오류: {str(e)}",
            {'service_name': service_name, 'function': 'restore_service'}
        )
        raise HTTPException(status_code=500, detail="SERVICE_RESTORE_ERROR")


@app.post("/v1/system/reset-performance")
@monitor_performance("reset_performance_metrics", 0.1)
async def reset_performance_metrics():
    """성능 메트릭 초기화"""
    try:
        # 성능 메트릭 초기화
        performance_logger.performance_metrics.clear()
        system_monitor.error_counts.clear()
        system_monitor.performance_alerts.clear()
        
        app_logger.info("성능 메트릭이 초기화되었습니다")
        
        return {
            "status": "performance_metrics_reset",
            "message": "성능 메트릭이 초기화되었습니다",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        error_logger.log_error(
            'DATA_PROCESSING_ERROR',
            f"성능 메트릭 초기화 오류: {str(e)}",
            {'function': 'reset_performance_metrics'}
        )
        raise HTTPException(status_code=500, detail="PERFORMANCE_RESET_ERROR")
@app.get("/v1/strategies")
@monitor_performance("get_strategies", 0.1)
async def get_strategies():
    """모든 전략 조회"""
    try:
        strategies = [strategy.to_dict() for strategy in strategy_manager.strategies.values()]
        return {"strategies": strategies}
    except Exception as e:
        error_logger.log_error(
            'DATA_PROCESSING_ERROR',
            f"전략 조회 오류: {str(e)}",
            {'function': 'get_strategies'}
        )
        raise HTTPException(status_code=500, detail="STRATEGIES_QUERY_ERROR")


@app.get("/v1/strategies/{strategy_id}")
async def get_strategy(strategy_id: str):
    """특정 전략 조회"""
    try:
        strategy = strategy_manager.get_strategy(strategy_id)
        return strategy.to_dict()
    except HTTPException:
        raise
    except Exception as e:
        app_logger.error(f"전략 조회 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# 분석 결과 API 엔드포인트 (작업 11번)
# ============================================================================

@app.get("/v1/analysis/latest")
@monitor_performance("get_latest_analysis", 0.1)
async def get_latest_analysis():
    """
    최신 분석 결과 조회 (요구사항 13.6)
    
    Returns:
        Dict: 최신 시장 체제, 주도 섹터, 종목 후보 정보
    """
    try:
        if not db_manager or not db_manager.is_connected():
            raise HTTPException(status_code=503, detail="데이터베이스가 연결되지 않았습니다")
        
        # 최신 시장 체제 조회
        market_regime = await db_manager.get_latest_market_regime()
        
        if not market_regime:
            return {
                "status": "no_data",
                "message": "분석 결과가 없습니다. 분석을 먼저 실행해주세요.",
                "timestamp": datetime.now().isoformat()
            }
        
        analysis_date = market_regime['analysis_date'].isoformat() if isinstance(market_regime['analysis_date'], datetime) else str(market_regime['analysis_date'])
        
        # 해당 날짜의 섹터 분석 및 종목 후보 조회
        analysis_data = await db_manager.get_analysis_by_date_range(analysis_date, analysis_date)
        
        # 응답 데이터 구성
        result = {
            "analysis_date": analysis_date,
            "market_regime": {
                "regime": market_regime['market_regime'],
                "kospi_value": float(market_regime['kospi_value']),
                "kosdaq_value": float(market_regime['kosdaq_value']),
                "kospi_ma20": float(market_regime['kospi_ma20']),
                "kosdaq_ma20": float(market_regime['kosdaq_ma20']),
                "take_profit_percent": float(market_regime['take_profit_percent']) if market_regime.get('take_profit_percent') else None,
                "stop_loss_percent": float(market_regime['stop_loss_percent']) if market_regime.get('stop_loss_percent') else None
            },
            "leading_sectors": [],
            "stock_candidates": [],
            "timestamp": datetime.now().isoformat()
        }
        
        # 섹터 분석 데이터 추가 (상위 3개)
        if analysis_data['sector_analysis']:
            for sector in analysis_data['sector_analysis'][:3]:
                result["leading_sectors"].append({
                    "sector_code": sector['sector_code'],
                    "sector_name": sector['sector_name'],
                    "combined_score": float(sector['combined_score']),
                    "rank": sector['rank'],
                    "price_momentum_score": float(sector['price_momentum_score']),
                    "supply_demand_score": float(sector['supply_demand_score']),
                    "breadth_score": float(sector['breadth_score']),
                    "relative_strength_score": float(sector['relative_strength_score'])
                })
        
        # 종목 후보 데이터 추가
        if analysis_data['stock_candidates']:
            for stock in analysis_data['stock_candidates']:
                result["stock_candidates"].append({
                    "ticker": stock['ticker'],
                    "stock_name": stock['stock_name'],
                    "sector": stock['sector'],
                    "z_score": float(stock['z_score']),
                    "disparity_ratio": float(stock['disparity_ratio']),
                    "current_price": float(stock['current_price']),
                    "ma20": float(stock['ma20']),
                    "volume": int(stock['volume']),
                    "signal_strength": float(stock['signal_strength'])
                })
        
        app_logger.info(f"최신 분석 결과 조회 완료: {analysis_date}")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        error_logger.log_error(
            'DATA_PROCESSING_ERROR',
            f"최신 분석 결과 조회 오류: {str(e)}",
            {'function': 'get_latest_analysis'}
        )
        raise HTTPException(status_code=500, detail="LATEST_ANALYSIS_ERROR")


@app.get("/v1/analysis/history")
@monitor_performance("get_analysis_history", 0.2)
async def get_analysis_history(start_date: str = None, end_date: str = None, limit: int = 30):
    """
    과거 분석 이력 조회 (요구사항 13.6)
    
    Args:
        start_date: 시작 날짜 (YYYY-MM-DD), 기본값: 30일 전
        end_date: 종료 날짜 (YYYY-MM-DD), 기본값: 오늘
        limit: 최대 결과 수 (기본값: 30)
    
    Returns:
        Dict: 날짜 범위 내 분석 결과 목록
    """
    try:
        if not db_manager or not db_manager.is_connected():
            raise HTTPException(status_code=503, detail="데이터베이스가 연결되지 않았습니다")
        
        # 기본 날짜 설정
        from datetime import timedelta
        if not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')
        if not start_date:
            start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        
        # 날짜 형식 검증
        try:
            datetime.strptime(start_date, '%Y-%m-%d')
            datetime.strptime(end_date, '%Y-%m-%d')
        except ValueError:
            raise HTTPException(status_code=400, detail="날짜 형식이 올바르지 않습니다. YYYY-MM-DD 형식을 사용하세요.")
        
        # 분석 이력 조회
        analysis_data = await db_manager.get_analysis_by_date_range(start_date, end_date)
        
        # 날짜별로 그룹화
        history_by_date = {}
        
        # 시장 체제 데이터 그룹화
        for market in analysis_data['market_regime'][:limit]:
            date_key = market['analysis_date'].isoformat() if isinstance(market['analysis_date'], datetime) else str(market['analysis_date'])
            if date_key not in history_by_date:
                history_by_date[date_key] = {
                    "analysis_date": date_key,
                    "market_regime": None,
                    "leading_sectors": [],
                    "stock_candidates": []
                }
            
            history_by_date[date_key]["market_regime"] = {
                "regime": market['market_regime'],
                "kospi_value": float(market['kospi_value']),
                "kosdaq_value": float(market['kosdaq_value']),
                "kospi_ma20": float(market['kospi_ma20']),
                "kosdaq_ma20": float(market['kosdaq_ma20'])
            }
        
        # 섹터 분석 데이터 그룹화
        for sector in analysis_data['sector_analysis']:
            date_key = sector['analysis_date'].isoformat() if isinstance(sector['analysis_date'], datetime) else str(sector['analysis_date'])
            if date_key in history_by_date and sector['rank'] <= 3:
                history_by_date[date_key]["leading_sectors"].append({
                    "sector_name": sector['sector_name'],
                    "combined_score": float(sector['combined_score']),
                    "rank": sector['rank']
                })
        
        # 종목 후보 데이터 그룹화
        for stock in analysis_data['stock_candidates']:
            date_key = stock['analysis_date'].isoformat() if isinstance(stock['analysis_date'], datetime) else str(stock['analysis_date'])
            if date_key in history_by_date:
                history_by_date[date_key]["stock_candidates"].append({
                    "ticker": stock['ticker'],
                    "stock_name": stock['stock_name'],
                    "z_score": float(stock['z_score']),
                    "signal_strength": float(stock['signal_strength'])
                })
        
        # 리스트로 변환 및 정렬
        history_list = sorted(history_by_date.values(), key=lambda x: x['analysis_date'], reverse=True)
        
        app_logger.info(f"분석 이력 조회 완료: {start_date} ~ {end_date}, {len(history_list)}건")
        
        return {
            "start_date": start_date,
            "end_date": end_date,
            "total_count": len(history_list),
            "history": history_list,
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        error_logger.log_error(
            'DATA_PROCESSING_ERROR',
            f"분석 이력 조회 오류: {str(e)}",
            {'function': 'get_analysis_history', 'start_date': start_date, 'end_date': end_date}
        )
        raise HTTPException(status_code=500, detail="ANALYSIS_HISTORY_ERROR")


@app.post("/v1/analysis/run")
@monitor_performance("run_analysis", 60.0)
async def run_analysis():
    """
    수동 분석 실행 트리거 (요구사항 13.6)
    
    Returns:
        Dict: 분석 실행 결과
    """
    try:
        if emergency_stop_active:
            raise HTTPException(status_code=423, detail="긴급 정지 상태에서는 분석을 실행할 수 없습니다")
        
        if not all([market_regime_analyzer, sector_filter, stock_picker, db_manager]):
            raise HTTPException(status_code=503, detail="시스템 컴포넌트가 초기화되지 않았습니다")
        
        app_logger.info("수동 분석 실행 시작")
        analysis_start = datetime.now()
        
        # 1단계: 시장 체제 분석
        try:
            app_logger.info("1단계: 시장 체제 분석")
            market_analysis = await market_regime_analyzer.analyze_market_regime()
            
            # 데이터베이스에 저장
            await db_manager.save_market_regime(
                regime=market_analysis.regime.value,
                kospi_value=market_analysis.kospi_value,
                kosdaq_value=market_analysis.kosdaq_value,
                kospi_ma20=market_analysis.kospi_ma20,
                kosdaq_ma20=market_analysis.kosdaq_ma20,
                take_profit_percent=market_analysis.risk_parameters.take_profit_percent,
                stop_loss_percent=market_analysis.risk_parameters.stop_loss_percent,
                analysis_date=datetime.now().strftime('%Y-%m-%d')
            )
            
            app_logger.info(f"시장 체제: {market_analysis.regime.value.upper()}")
            
        except Exception as e:
            error_logger.log_error(
                'DATA_PROCESSING_ERROR',
                f"시장 체제 분석 오류: {str(e)}",
                {'function': 'run_analysis', 'stage': 'market_analysis'}
            )
            raise HTTPException(status_code=500, detail=f"시장 체제 분석 실패: {str(e)}")
        
        # 2단계: 주도 섹터 식별
        try:
            app_logger.info("2단계: 주도 섹터 식별")
            leading_sectors = await sector_filter.get_leading_sectors(count=3)
            
            if not leading_sectors:
                app_logger.warning("주도 섹터를 찾을 수 없습니다")
                return {
                    "status": "completed_with_warnings",
                    "message": "주도 섹터를 찾을 수 없습니다",
                    "market_regime": market_analysis.regime.value,
                    "leading_sectors": [],
                    "stock_candidates": [],
                    "execution_time": (datetime.now() - analysis_start).total_seconds(),
                    "timestamp": datetime.now().isoformat()
                }
            
            # 섹터 분석 결과 저장
            for idx, sector in enumerate(leading_sectors, 1):
                await db_manager.save_sector_analysis(
                    sector_code=sector.sector_code,
                    sector_name=sector.sector_name,
                    price_momentum_score=0.0,  # 실제 점수는 sector_filter에서 계산
                    supply_demand_score=0.0,
                    breadth_score=0.0,
                    relative_strength_score=0.0,
                    combined_score=sector.combined_score,
                    rank=idx,
                    analysis_date=datetime.now().strftime('%Y-%m-%d')
                )
            
            app_logger.info(f"주도 섹터 {len(leading_sectors)}개 식별")
            
        except Exception as e:
            error_logger.log_error(
                'DATA_PROCESSING_ERROR',
                f"주도 섹터 식별 오류: {str(e)}",
                {'function': 'run_analysis', 'stage': 'sector_analysis'}
            )
            raise HTTPException(status_code=500, detail=f"주도 섹터 식별 실패: {str(e)}")
        
        # 3단계: 종목 선정
        try:
            app_logger.info("3단계: 종목 선정")
            buy_candidates = await stock_picker.get_buy_candidates(leading_sectors)
            
            # 종목 후보 저장
            for candidate in buy_candidates:
                await db_manager.save_stock_candidate(
                    ticker=candidate.ticker,
                    stock_name=candidate.stock_name,
                    sector=candidate.sector_code,
                    z_score=candidate.z_score,
                    disparity_ratio=candidate.disparity_ratio,
                    current_price=candidate.current_price,
                    ma20=candidate.ma20,
                    volume=candidate.trading_volume,
                    signal_strength=candidate.signal_strength,
                    analysis_date=datetime.now().strftime('%Y-%m-%d')
                )
            
            app_logger.info(f"매수 후보 {len(buy_candidates)}개 발견")
            
        except Exception as e:
            error_logger.log_error(
                'DATA_PROCESSING_ERROR',
                f"종목 선정 오류: {str(e)}",
                {'function': 'run_analysis', 'stage': 'stock_selection'}
            )
            raise HTTPException(status_code=500, detail=f"종목 선정 실패: {str(e)}")
        
        # 분석 완료
        execution_time = (datetime.now() - analysis_start).total_seconds()
        app_logger.info(f"수동 분석 실행 완료 (소요시간: {execution_time:.1f}초)")
        
        return {
            "status": "completed",
            "message": "분석이 성공적으로 완료되었습니다",
            "analysis_date": datetime.now().strftime('%Y-%m-%d'),
            "market_regime": market_analysis.regime.value,
            "leading_sectors_count": len(leading_sectors),
            "stock_candidates_count": len(buy_candidates),
            "execution_time": execution_time,
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        error_logger.log_error(
            'DATA_PROCESSING_ERROR',
            f"수동 분석 실행 오류: {str(e)}",
            {'function': 'run_analysis'}
        )
        raise HTTPException(status_code=500, detail="ANALYSIS_RUN_ERROR")


@app.get("/v1/market-regime/current")
@monitor_performance("get_current_market_regime", 0.1)
async def get_current_market_regime():
    """
    현재 시장 체제 조회 (요구사항 13.6)
    
    Returns:
        Dict: 현재 시장 체제 정보
    """
    try:
        if not db_manager or not db_manager.is_connected():
            raise HTTPException(status_code=503, detail="데이터베이스가 연결되지 않았습니다")
        
        # 최신 시장 체제 조회
        market_regime = await db_manager.get_latest_market_regime()
        
        if not market_regime:
            return {
                "status": "no_data",
                "message": "시장 체제 데이터가 없습니다. 분석을 먼저 실행해주세요.",
                "timestamp": datetime.now().isoformat()
            }
        
        analysis_date = market_regime['analysis_date'].isoformat() if isinstance(market_regime['analysis_date'], datetime) else str(market_regime['analysis_date'])
        
        result = {
            "analysis_date": analysis_date,
            "regime": market_regime['market_regime'],
            "kospi": {
                "value": float(market_regime['kospi_value']),
                "ma20": float(market_regime['kospi_ma20']),
                "above_ma": float(market_regime['kospi_value']) > float(market_regime['kospi_ma20'])
            },
            "kosdaq": {
                "value": float(market_regime['kosdaq_value']),
                "ma20": float(market_regime['kosdaq_ma20']),
                "above_ma": float(market_regime['kosdaq_value']) > float(market_regime['kosdaq_ma20'])
            },
            "risk_parameters": {
                "take_profit_percent": float(market_regime['take_profit_percent']) if market_regime.get('take_profit_percent') else None,
                "stop_loss_percent": float(market_regime['stop_loss_percent']) if market_regime.get('stop_loss_percent') else None
            },
            "timestamp": datetime.now().isoformat()
        }
        
        app_logger.info(f"현재 시장 체제 조회: {market_regime['market_regime']}")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        error_logger.log_error(
            'DATA_PROCESSING_ERROR',
            f"현재 시장 체제 조회 오류: {str(e)}",
            {'function': 'get_current_market_regime'}
        )
        raise HTTPException(status_code=500, detail="MARKET_REGIME_ERROR")


@app.get("/v1/sectors/leading")
@monitor_performance("get_leading_sectors", 0.1)
async def get_leading_sectors_endpoint(count: int = 3):
    """
    주도 섹터 조회 (요구사항 13.6)
    
    Args:
        count: 조회할 섹터 수 (기본값: 3)
    
    Returns:
        Dict: 주도 섹터 목록
    """
    try:
        if not db_manager or not db_manager.is_connected():
            raise HTTPException(status_code=503, detail="데이터베이스가 연결되지 않았습니다")
        
        if count < 1 or count > 10:
            raise HTTPException(status_code=400, detail="count는 1-10 사이여야 합니다")
        
        # 최신 시장 체제 조회 (날짜 확인용)
        market_regime = await db_manager.get_latest_market_regime()
        
        if not market_regime:
            return {
                "status": "no_data",
                "message": "분석 데이터가 없습니다. 분석을 먼저 실행해주세요.",
                "timestamp": datetime.now().isoformat()
            }
        
        analysis_date = market_regime['analysis_date'].isoformat() if isinstance(market_regime['analysis_date'], datetime) else str(market_regime['analysis_date'])
        
        # 해당 날짜의 섹터 분석 조회
        analysis_data = await db_manager.get_analysis_by_date_range(analysis_date, analysis_date)
        
        # 상위 N개 섹터 추출
        leading_sectors = []
        for sector in analysis_data['sector_analysis'][:count]:
            leading_sectors.append({
                "rank": sector['rank'],
                "sector_code": sector['sector_code'],
                "sector_name": sector['sector_name'],
                "combined_score": float(sector['combined_score']),
                "scores": {
                    "price_momentum": float(sector['price_momentum_score']),
                    "supply_demand": float(sector['supply_demand_score']),
                    "breadth": float(sector['breadth_score']),
                    "relative_strength": float(sector['relative_strength_score'])
                }
            })
        
        app_logger.info(f"주도 섹터 조회: {len(leading_sectors)}개")
        
        return {
            "analysis_date": analysis_date,
            "count": len(leading_sectors),
            "leading_sectors": leading_sectors,
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        error_logger.log_error(
            'DATA_PROCESSING_ERROR',
            f"주도 섹터 조회 오류: {str(e)}",
            {'function': 'get_leading_sectors_endpoint'}
        )
        raise HTTPException(status_code=500, detail="LEADING_SECTORS_ERROR")


@app.get("/v1/stocks/candidates")
@monitor_performance("get_stock_candidates", 0.1)
async def get_stock_candidates(limit: int = 20, min_signal_strength: float = 0.0):
    """
    종목 후보 조회 (요구사항 13.6)
    
    Args:
        limit: 최대 결과 수 (기본값: 20)
        min_signal_strength: 최소 신호 강도 (기본값: 0.0)
    
    Returns:
        Dict: 종목 후보 목록
    """
    try:
        if not db_manager or not db_manager.is_connected():
            raise HTTPException(status_code=503, detail="데이터베이스가 연결되지 않았습니다")
        
        if limit < 1 or limit > 100:
            raise HTTPException(status_code=400, detail="limit는 1-100 사이여야 합니다")
        
        if min_signal_strength < 0 or min_signal_strength > 100:
            raise HTTPException(status_code=400, detail="min_signal_strength는 0-100 사이여야 합니다")
        
        # 최신 시장 체제 조회 (날짜 확인용)
        market_regime = await db_manager.get_latest_market_regime()
        
        if not market_regime:
            return {
                "status": "no_data",
                "message": "분석 데이터가 없습니다. 분석을 먼저 실행해주세요.",
                "timestamp": datetime.now().isoformat()
            }
        
        analysis_date = market_regime['analysis_date'].isoformat() if isinstance(market_regime['analysis_date'], datetime) else str(market_regime['analysis_date'])
        
        # 해당 날짜의 종목 후보 조회
        analysis_data = await db_manager.get_analysis_by_date_range(analysis_date, analysis_date)
        
        # 필터링 및 정렬
        candidates = []
        for stock in analysis_data['stock_candidates']:
            signal_strength = float(stock['signal_strength'])
            if signal_strength >= min_signal_strength:
                candidates.append({
                    "ticker": stock['ticker'],
                    "stock_name": stock['stock_name'],
                    "sector": stock['sector'],
                    "current_price": float(stock['current_price']),
                    "ma20": float(stock['ma20']),
                    "z_score": float(stock['z_score']),
                    "disparity_ratio": float(stock['disparity_ratio']),
                    "volume": int(stock['volume']),
                    "signal_strength": signal_strength
                })
        
        # 신호 강도 기준 정렬
        candidates.sort(key=lambda x: x['signal_strength'], reverse=True)
        candidates = candidates[:limit]
        
        app_logger.info(f"종목 후보 조회: {len(candidates)}개")
        
        return {
            "analysis_date": analysis_date,
            "count": len(candidates),
            "candidates": candidates,
            "filters": {
                "limit": limit,
                "min_signal_strength": min_signal_strength
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        error_logger.log_error(
            'DATA_PROCESSING_ERROR',
            f"종목 후보 조회 오류: {str(e)}",
            {'function': 'get_stock_candidates'}
        )
        raise HTTPException(status_code=500, detail="STOCK_CANDIDATES_ERROR")


# ============================================================================
# 기존 엔드포인트들
# ============================================================================

@app.get("/v1/strategies")
@monitor_performance("get_strategies", 0.1)
async def get_strategies():
    """모든 전략 조회"""
    try:
        strategies = [strategy.to_dict() for strategy in strategy_manager.strategies.values()]
        return {"strategies": strategies}
    except Exception as e:
        error_logger.log_error(
            'DATA_PROCESSING_ERROR',
            f"전략 조회 오류: {str(e)}",
            {'function': 'get_strategies'}
        )
        raise HTTPException(status_code=500, detail="STRATEGIES_QUERY_ERROR")


@app.get("/v1/strategies/{strategy_id}")
async def get_strategy(strategy_id: str):
    """특정 전략 조회"""
    try:
        strategy = strategy_manager.get_strategy(strategy_id)
        return strategy.to_dict()
    except HTTPException:
        raise
    except Exception as e:
        app_logger.error(f"전략 조회 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/v1/system/reset-emergency")
async def reset_emergency_stop():
    """긴급 정지 해제"""
    global emergency_stop_active
    
    try:
        if not emergency_stop_active:
            raise HTTPException(status_code=400, detail="긴급 정지 상태가 아닙니다")
        
        emergency_stop_active = False
        app_logger.info("긴급 정지 해제")
        
        # 거래 로그 생성
        await log_trade_event(
            strategy_id="system",
            action="EMERGENCY_RESET",
            ticker="000000",
            stock_name="시스템",
            quantity=0,
            price=0.0,
            reason="[긴급 정지 해제]"
        )
        
        return {
            "status": "emergency_stop_reset",
            "message": "긴급 정지가 해제되었습니다",
            "timestamp": datetime.now().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        app_logger.error(f"긴급 정지 해제 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/")
async def root():
    """루트 엔드포인트"""
    try:
        system_health = system_monitor.is_system_healthy()
        uptime = system_monitor.get_uptime()
        
        return {
            "name": "LSMR Stock Picker",
            "version": "1.0.0",
            "description": "Leading Sector Mean Reversion 주식 선택 시스템",
            "status": "emergency_stop" if emergency_stop_active else ("running" if system_running else "stopped"),
            "system_healthy": system_health,
            "uptime_seconds": uptime,
            "endpoints": {
                "health": "/v1/health",
                "strategies": "/v1/strategies",
                "websocket": "/ws",
                "emergency_stop": "/v1/system/emergency-stop",
                "reset_emergency": "/v1/system/reset-emergency",
                "performance": "/v1/system/performance",
                "errors": "/v1/system/errors",
                "degraded_services": "/v1/system/degraded-services",
                "reset_performance": "/v1/system/reset-performance",
                "system_status": "/v1/system/status",
                "components_status": "/v1/system/components",
                "trading_engine_start": "/v1/system/trading-engine/start",
                "trading_engine_stop": "/v1/system/trading-engine/stop",
                "analysis_latest": "/v1/analysis/latest",
                "analysis_history": "/v1/analysis/history",
                "analysis_run": "/v1/analysis/run",
                "market_regime_current": "/v1/market-regime/current",
                "sectors_leading": "/v1/sectors/leading",
                "stocks_candidates": "/v1/stocks/candidates"
            }
        }
    except Exception as e:
        error_logger.log_error(
            'DATA_PROCESSING_ERROR',
            f"루트 엔드포인트 오류: {str(e)}",
            {'function': 'root'}
        )
        # 루트 엔드포인트는 항상 응답해야 하므로 기본 정보 반환
        return {
            "name": "LSMR Stock Picker",
            "version": "1.0.0",
            "status": "error",
            "message": "시스템 오류 발생"
        }


def main():
    """메인 실행 함수"""
    # 환경 변수에서 설정 로드
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    environment = os.getenv("ENVIRONMENT", "development")
    
    # 로그 레벨 설정
    log_level = os.getenv("LOG_LEVEL", "info").lower()
    
    app_logger.info(f"LSMR Stock Picker 서버 시작: {host}:{port}")
    app_logger.info(f"환경: {environment}, 로그 레벨: {log_level}")
    
    # 필수 환경 변수 확인 (개발 환경에서는 경고만)
    required_env_vars = ['KIS_APP_KEY', 'KIS_APP_SECRET', 'KIS_ACCOUNT_NUMBER']
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    
    if missing_vars:
        if environment == "production":
            app_logger.error(f"필수 환경 변수가 설정되지 않았습니다: {missing_vars}")
            raise SystemExit(1)
        else:
            app_logger.warning(f"개발 환경: 일부 환경 변수가 설정되지 않았습니다: {missing_vars}")
    
    # CPU 및 메모리 사용량 모니터링 시작
    import psutil
    process = psutil.Process()
    app_logger.info(f"시작 시 메모리 사용량: {process.memory_info().rss / 1024 / 1024:.1f}MB")
    app_logger.info(f"시작 시 CPU 코어 수: {psutil.cpu_count()}")
    
    try:
        uvicorn.run(
            "lsmr_stock_picker.main:app",
            host=host,
            port=port,
            reload=environment == "development",
            log_level=log_level,
            access_log=True,
            # 성능 최적화 설정
            loop="asyncio",
            http="httptools",
            # 요구사항 8.5: 시스템 건강 모니터링
            timeout_keep_alive=30,
            timeout_graceful_shutdown=10
        )
    except KeyboardInterrupt:
        app_logger.info("사용자에 의한 서버 종료")
    except Exception as e:
        app_logger.error(f"서버 실행 오류: {e}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()


# ============================================================================
# 스케줄러 API 엔드포인트 (작업 12번)
# ============================================================================

@app.get("/v1/scheduler/status")
@monitor_performance("get_scheduler_status", 0.1)
async def get_scheduler_status():
    """
    스케줄러 상태 조회
    
    Returns:
        Dict: 스케줄러 상태 정보
    """
    try:
        if not analysis_scheduler:
            return {
                "status": "not_initialized",
                "message": "스케줄러가 초기화되지 않았습니다",
                "timestamp": datetime.now().isoformat()
            }
        
        status = analysis_scheduler.get_scheduler_status()
        
        app_logger.info("스케줄러 상태 조회")
        return {
            "status": "ok",
            "scheduler": status,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        error_logger.log_error(
            'DATA_PROCESSING_ERROR',
            f"스케줄러 상태 조회 오류: {str(e)}",
            {'function': 'get_scheduler_status'}
        )
        raise HTTPException(status_code=500, detail="SCHEDULER_STATUS_ERROR")


@app.get("/v1/scheduler/history")
@monitor_performance("get_scheduler_history", 0.1)
async def get_scheduler_history(limit: int = 10):
    """
    스케줄 실행 이력 조회
    
    Args:
        limit: 최대 결과 수 (기본값: 10)
    
    Returns:
        Dict: 실행 이력 목록
    """
    try:
        if not analysis_scheduler:
            raise HTTPException(status_code=503, detail="스케줄러가 초기화되지 않았습니다")
        
        if limit < 1 or limit > 100:
            raise HTTPException(status_code=400, detail="limit는 1-100 사이여야 합니다")
        
        history = analysis_scheduler.get_execution_history(limit=limit)
        
        app_logger.info(f"스케줄 실행 이력 조회: {len(history)}건")
        
        return {
            "count": len(history),
            "history": [record.to_dict() for record in history],
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        error_logger.log_error(
            'DATA_PROCESSING_ERROR',
            f"스케줄 실행 이력 조회 오류: {str(e)}",
            {'function': 'get_scheduler_history'}
        )
        raise HTTPException(status_code=500, detail="SCHEDULER_HISTORY_ERROR")


@app.get("/v1/scheduler/statistics")
@monitor_performance("get_scheduler_statistics", 0.1)
async def get_scheduler_statistics():
    """
    스케줄 실행 통계 조회
    
    Returns:
        Dict: 실행 통계
    """
    try:
        if not analysis_scheduler:
            raise HTTPException(status_code=503, detail="스케줄러가 초기화되지 않았습니다")
        
        statistics = analysis_scheduler.get_execution_statistics()
        
        app_logger.info("스케줄 실행 통계 조회")
        
        return {
            "statistics": statistics,
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        error_logger.log_error(
            'DATA_PROCESSING_ERROR',
            f"스케줄 실행 통계 조회 오류: {str(e)}",
            {'function': 'get_scheduler_statistics'}
        )
        raise HTTPException(status_code=500, detail="SCHEDULER_STATISTICS_ERROR")


@app.post("/v1/scheduler/run-now")
@monitor_performance("run_scheduled_analysis_now", 60.0)
async def run_scheduled_analysis_now():
    """
    즉시 분석 실행 (스케줄과 무관하게)
    
    Returns:
        Dict: 실행 결과
    """
    try:
        if not analysis_scheduler:
            raise HTTPException(status_code=503, detail="스케줄러가 초기화되지 않았습니다")
        
        if emergency_stop_active:
            raise HTTPException(status_code=423, detail="긴급 정지 상태에서는 분석을 실행할 수 없습니다")
        
        app_logger.info("즉시 분석 실행 요청")
        
        # 즉시 실행
        record = await analysis_scheduler.run_now()
        
        app_logger.info(f"즉시 분석 실행 완료: {record.execution_id}")
        
        return {
            "status": "completed",
            "message": "분석이 즉시 실행되었습니다",
            "execution_record": record.to_dict(),
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        error_logger.log_error(
            'DATA_PROCESSING_ERROR',
            f"즉시 분석 실행 오류: {str(e)}",
            {'function': 'run_scheduled_analysis_now'}
        )
        raise HTTPException(status_code=500, detail="SCHEDULER_RUN_NOW_ERROR")


@app.post("/v1/scheduler/start")
@monitor_performance("start_scheduler", 0.1)
async def start_scheduler():
    """
    스케줄러 시작
    
    Returns:
        Dict: 시작 결과
    """
    try:
        if not analysis_scheduler:
            raise HTTPException(status_code=503, detail="스케줄러가 초기화되지 않았습니다")
        
        await analysis_scheduler.start()
        
        next_run = analysis_scheduler.get_next_run_time()
        next_run_str = next_run.strftime('%Y-%m-%d %H:%M:%S') if next_run else "없음"
        
        app_logger.info(f"스케줄러 시작 완료 (다음 실행: {next_run_str})")
        
        return {
            "status": "started",
            "message": "스케줄러가 시작되었습니다",
            "next_run_time": next_run.isoformat() if next_run else None,
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        error_logger.log_error(
            'SYSTEM_ERROR',
            f"스케줄러 시작 오류: {str(e)}",
            {'function': 'start_scheduler'}
        )
        raise HTTPException(status_code=500, detail="SCHEDULER_START_ERROR")


@app.post("/v1/scheduler/stop")
@monitor_performance("stop_scheduler", 0.1)
async def stop_scheduler():
    """
    스케줄러 정지
    
    Returns:
        Dict: 정지 결과
    """
    try:
        if not analysis_scheduler:
            raise HTTPException(status_code=503, detail="스케줄러가 초기화되지 않았습니다")
        
        await analysis_scheduler.stop()
        
        app_logger.info("스케줄러 정지 완료")
        
        return {
            "status": "stopped",
            "message": "스케줄러가 정지되었습니다",
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        error_logger.log_error(
            'SYSTEM_ERROR',
            f"스케줄러 정지 오류: {str(e)}",
            {'function': 'stop_scheduler'}
        )
        raise HTTPException(status_code=500, detail="SCHEDULER_STOP_ERROR")


@app.patch("/v1/scheduler/schedule")
@monitor_performance("update_schedule", 0.1)
async def update_schedule(cron_expression: str):
    """
    스케줄 업데이트
    
    Args:
        cron_expression: 새로운 cron 표현식
    
    Returns:
        Dict: 업데이트 결과
    """
    try:
        if not analysis_scheduler:
            raise HTTPException(status_code=503, detail="스케줄러가 초기화되지 않았습니다")
        
        if not cron_expression:
            raise HTTPException(status_code=400, detail="cron_expression이 필요합니다")
        
        # 스케줄 업데이트
        analysis_scheduler.update_schedule(cron_expression)
        
        next_run = analysis_scheduler.get_next_run_time()
        next_run_str = next_run.strftime('%Y-%m-%d %H:%M:%S') if next_run else "없음"
        
        app_logger.info(f"스케줄 업데이트 완료: {cron_expression} (다음 실행: {next_run_str})")
        
        return {
            "status": "updated",
            "message": "스케줄이 업데이트되었습니다",
            "cron_expression": cron_expression,
            "next_run_time": next_run.isoformat() if next_run else None,
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        error_logger.log_error(
            'SYSTEM_ERROR',
            f"스케줄 업데이트 오류: {str(e)}",
            {'function': 'update_schedule', 'cron_expression': cron_expression}
        )
        raise HTTPException(status_code=500, detail="SCHEDULE_UPDATE_ERROR")


@app.delete("/v1/scheduler/history")
@monitor_performance("clear_scheduler_history", 0.1)
async def clear_scheduler_history():
    """
    스케줄 실행 이력 초기화
    
    Returns:
        Dict: 초기화 결과
    """
    try:
        if not analysis_scheduler:
            raise HTTPException(status_code=503, detail="스케줄러가 초기화되지 않았습니다")
        
        analysis_scheduler.clear_history()
        
        app_logger.info("스케줄 실행 이력 초기화 완료")
        
        return {
            "status": "cleared",
            "message": "스케줄 실행 이력이 초기화되었습니다",
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        error_logger.log_error(
            'DATA_PROCESSING_ERROR',
            f"스케줄 실행 이력 초기화 오류: {str(e)}",
            {'function': 'clear_scheduler_history'}
        )
        raise HTTPException(status_code=500, detail="SCHEDULER_HISTORY_CLEAR_ERROR")


# ============================================================================
# 메인 실행
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    
    # 환경 변수에서 호스트 및 포트 로드
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    
    app_logger.info(f"LSMR Stock Picker 서버 시작: {host}:{port}")
    
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info"
    )
