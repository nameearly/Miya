# 辅助函数
# Helpers

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

logger = logging.getLogger(__name__)

class Helpers:
    def __init__(self):
        pass
    
    def format_timestamp(self, timestamp: datetime) -> str:
        return timestamp.strftime("%Y-%m-%d %H:%M:%S")
    
    def get_time_period(self, hour: int) -> str:
        if 6 <= hour < 12:
            return "morning"
        elif 12 <= hour < 14:
            return "afternoon"
        elif 17 <= hour < 21:
            return "evening"
        else:
            return "night"
    
    def get_weekday_name(self, weekday: int) -> str:
        weekdays = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
        return weekdays[weekday] if 0 <= weekday < 7 else "未知"
    
    def merge_dicts(self, *dicts) -> Dict:
        result = {}
        for d in dicts:
            if d:
                result.update(d)
        return result
