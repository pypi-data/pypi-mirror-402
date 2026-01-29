"""핵심 데이터 모델"""

from dataclasses import dataclass, asdict
from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum
import json
import re


class MarketRegime(Enum):
    BULL = "bull"
    BEAR = "bear"
    NEUTRAL = "neutral"


class TradeAction(Enum):
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


class VolumeTrend(Enum):
    INCREASING = "increasing"
    DECREASING = "decreasing"
    STABLE = "stable"


class StrategyStatus(Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"


@dataclass
class Strategy:
    id: str
    name: str
    status: str
    return_rate: float
    account: str
    take_profit_percent: float
    stop_loss_percent: float
    message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'name': self.name,
            'status': self.status,
            'returnRate': self.return_rate,
            'account': self.account,
            'takeProfitPercent': self.take_profit_percent,
            'stopLossPercent': self.stop_loss_percent,
            'message': self.message
        }
    
    def validate(self) -> List[str]:
        """데이터 검증 - 요구사항 5.1"""
        errors = []
        
        if not self.id or not isinstance(self.id, str):
            errors.append("Strategy.id는 필수 문자열 필드입니다")
        
        if not self.name or not isinstance(self.name, str):
            errors.append("Strategy.name은 필수 문자열 필드입니다")
        
        if self.status not in ['active', 'inactive', 'error']:
            errors.append("잘못된 상태 값입니다. 'active', 'inactive', 'error' 중 하나여야 합니다")
        
        if not isinstance(self.return_rate, (int, float)):
            errors.append("Strategy.return_rate는 숫자여야 합니다")
        
        if not self.account or not isinstance(self.account, str):
            errors.append("Strategy.account는 필수 문자열 필드입니다")
        
        if not isinstance(self.take_profit_percent, (int, float)) or self.take_profit_percent <= 0:
            errors.append("Strategy.take_profit_percent는 양수여야 합니다")
        
        if not isinstance(self.stop_loss_percent, (int, float)) or self.stop_loss_percent <= 0:
            errors.append("Strategy.stop_loss_percent는 양수여야 합니다")
        
        return errors


@dataclass
class TradeLog:
    timestamp: datetime
    strategy: str
    action: str
    stock_name: str
    ticker: str
    quantity: int
    price: float
    reason: str
    category: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'timestamp': self.timestamp.isoformat(),
            'strategy': self.strategy,
            'action': self.action,
            'stockName': self.stock_name,
            'ticker': self.ticker,
            'quantity': self.quantity,
            'price': self.price,
            'reason': self.reason,
            'category': self.category
        }
    
    def validate(self) -> List[str]:
        """데이터 검증 - 요구사항 5.2, 4.1, 4.2"""
        errors = []
        
        if not isinstance(self.timestamp, datetime):
            errors.append("TradeLog.timestamp는 datetime 객체여야 합니다")
        
        if not self.strategy or not isinstance(self.strategy, str):
            errors.append("TradeLog.strategy는 필수 문자열 필드입니다")
        
        if self.action not in ['BUY', 'SELL', 'SYSTEM', 'EMERGENCY_STOP', 'PARAMETER_UPDATE', 'EMERGENCY_RESET']:
            errors.append("TradeLog.action은 유효한 거래 액션이어야 합니다")
        
        if not self.stock_name or not isinstance(self.stock_name, str):
            errors.append("TradeLog.stock_name은 필수 문자열 필드입니다")
        
        if not self.ticker or not isinstance(self.ticker, str):
            errors.append("TradeLog.ticker는 필수 문자열 필드입니다")
        
        # 티커 형식 검증
        ticker_error = validate_ticker_format(self.ticker)
        if ticker_error:
            errors.append(ticker_error)
        
        if not isinstance(self.quantity, int) or self.quantity < 0:
            errors.append("TradeLog.quantity는 0 이상의 정수여야 합니다")
        
        if not isinstance(self.price, (int, float)) or self.price < 0:
            errors.append("TradeLog.price는 0 이상의 숫자여야 합니다")
        
        if not self.reason or not isinstance(self.reason, str):
            errors.append("TradeLog.reason은 필수 문자열 필드입니다")
        
        # 요구사항 4.2: 이유 코드 형식 검증
        reason_error = validate_reason_code_format(self.reason)
        if reason_error:
            errors.append(reason_error)
        
        # 요구사항 4.1: 카테고리는 항상 "Trade"
        if self.category != "Trade":
            errors.append("카테고리는 'Trade'여야 합니다 (요구사항 4.1)")
        
        return errors


@dataclass
class ProcessStatus:
    name: str
    status: str
    cpu_percent: float
    memory_mb: float


@dataclass
class SystemHealthMetrics:
    cpu_usage: float
    memory_usage: float
    memory_total: float
    processes: List[ProcessStatus]
    timestamp: datetime
    kis_api_connected: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'cpu_usage': self.cpu_usage,
            'memory_usage': self.memory_usage,
            'memory_total': self.memory_total,
            'processes': [asdict(p) for p in self.processes],
            'timestamp': self.timestamp.isoformat(),
            'kis_api_connected': self.kis_api_connected
        }
    
    def validate(self) -> List[str]:
        """데이터 검증 - 요구사항 4.4"""
        errors = []
        
        if not isinstance(self.cpu_usage, (int, float)) or self.cpu_usage < 0 or self.cpu_usage > 100:
            errors.append("SystemHealthMetrics.cpu_usage는 0-100 사이의 숫자여야 합니다")
        
        if not isinstance(self.memory_usage, (int, float)) or self.memory_usage < 0:
            errors.append("SystemHealthMetrics.memory_usage는 0 이상의 숫자여야 합니다")
        
        if not isinstance(self.memory_total, (int, float)) or self.memory_total <= 0:
            errors.append("SystemHealthMetrics.memory_total은 양수여야 합니다")
        
        # 메모리 사용량이 총 메모리보다 클 수 없음
        if self.memory_usage > self.memory_total:
            errors.append("메모리 사용량이 총 메모리보다 클 수 없습니다")
        
        if not isinstance(self.processes, list):
            errors.append("SystemHealthMetrics.processes는 리스트여야 합니다")
        
        if not isinstance(self.timestamp, datetime):
            errors.append("SystemHealthMetrics.timestamp는 datetime 객체여야 합니다")
        
        if not isinstance(self.kis_api_connected, bool):
            errors.append("SystemHealthMetrics.kis_api_connected는 불린 값이어야 합니다")
        
        # 요구사항 4.4: 필수 필드 포함 확인
        required_fields = ['cpu_usage', 'memory_usage', 'kis_api_connected']
        for field in required_fields:
            if not hasattr(self, field):
                errors.append(f"SystemHealthMetrics.{field}는 필수 필드입니다 (요구사항 4.4)")
        
        return errors


@dataclass
class IndexData:
    index_code: str
    current_value: float
    ma20: float
    change_percent: float
    timestamp: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data


@dataclass
class StockData:
    ticker: str
    stock_name: str
    current_price: float
    volume: int
    change_percent: float
    ma20: float = 0.0
    timestamp: Optional[datetime] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data


@dataclass
class Holding:
    ticker: str
    stock_name: str
    account: str
    quantity: int
    avg_price: float
    current_price: float
    profit_rate: float
    weight: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'ticker': self.ticker,
            'stockName': self.stock_name,
            'account': self.account,
            'quantity': self.quantity,
            'avgPrice': self.avg_price,
            'currentPrice': self.current_price,
            'profitRate': self.profit_rate,
            'weight': self.weight
        }
    
    def validate(self) -> List[str]:
        """데이터 검증 - 요구사항 5.3"""
        errors = []
        
        if not self.ticker or not isinstance(self.ticker, str):
            errors.append("Holding.ticker는 필수 문자열 필드입니다")
        
        if not self.stock_name or not isinstance(self.stock_name, str):
            errors.append("Holding.stock_name은 필수 문자열 필드입니다")
        
        if not self.account or not isinstance(self.account, str):
            errors.append("Holding.account는 필수 문자열 필드입니다")
        
        if not isinstance(self.quantity, int) or self.quantity <= 0:
            errors.append("Holding.quantity는 양의 정수여야 합니다")
        
        if not isinstance(self.avg_price, (int, float)) or self.avg_price <= 0:
            errors.append("Holding.avg_price는 양수여야 합니다")
        
        if not isinstance(self.current_price, (int, float)) or self.current_price <= 0:
            errors.append("Holding.current_price는 양수여야 합니다")
        
        if not isinstance(self.profit_rate, (int, float)):
            errors.append("Holding.profit_rate는 숫자여야 합니다")
        
        if not isinstance(self.weight, (int, float)) or self.weight < 0 or self.weight > 100:
            errors.append("Holding.weight는 0-100 사이의 숫자여야 합니다")
        
        return errors


@dataclass
class LeadingSector:
    sector_code: str
    sector_name: str
    combined_score: float
    top_stocks: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class SectorAnalysis:
    sector_code: str
    price_score: float
    supply_demand_score: float
    breadth_score: float
    relative_strength_score: float
    combined_score: float
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class StockAnalysis:
    ticker: str
    stock_name: str
    current_price: float
    ma20: float
    std_dev20: float
    z_score: float
    disparity_ratio: float
    volume_trend: str
    trading_volume: int
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class StockSignal:
    ticker: str
    stock_name: str
    z_score: float
    disparity_ratio: float
    signal_strength: float
    action: TradeAction
    sector_code: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['action'] = self.action.value
        return data


@dataclass
class RiskParameters:
    take_profit_percent: float
    stop_loss_percent: float
    max_position_size: float
    max_sector_exposure: float
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def validate_data_model(model) -> List[str]:
    """데이터 모델 검증 함수"""
    if hasattr(model, 'validate'):
        return model.validate()
    return ["검증 메서드가 없는 객체입니다"]


def serialize_to_json(model) -> str:
    """데이터 모델을 JSON으로 직렬화"""
    if hasattr(model, 'to_dict'):
        return json.dumps(model.to_dict(), ensure_ascii=False, indent=2)
    return json.dumps(asdict(model), ensure_ascii=False, indent=2)


def validate_ticker_format(ticker) -> Optional[str]:
    """티커 형식 검증 - 6자리 숫자여야 함"""
    if not isinstance(ticker, str):
        return "티커는 문자열이어야 합니다"
    
    if len(ticker) != 6:
        return "티커는 6자리 숫자여야 합니다"
    
    if not ticker.isdigit():
        return "티커는 6자리 숫자여야 합니다"
    
    return None


def validate_reason_code_format(reason) -> Optional[str]:
    """이유 코드 형식 검증 - [내용] 형태여야 함"""
    if not isinstance(reason, str):
        return "이유 코드는 문자열이어야 합니다"
    
    if not reason:
        return "이유 코드는 빈 문자열일 수 없습니다"
    
    if not (reason.startswith('[') and reason.endswith(']')):
        return "이유 코드는 [내용] 형태여야 합니다"
    
    return None


def validate_percentage(value, field_name: str) -> Optional[str]:
    """퍼센티지 값 검증 - 0-100 사이여야 함"""
    if not isinstance(value, (int, float)):
        return f"{field_name}는 숫자여야 합니다"
    
    if value < 0 or value > 100:
        return f"{field_name}는 0-100 사이의 값이어야 합니다"
    
    return None