# app/services/candlestick_analyzer.py

from typing import Dict, Any, Tuple, Optional

def is_doji(candle: Dict[str, Any]) -> bool:
    """
    Doji gyertyaformáció felismerése
    """
    open_price = candle["open"]
    close = candle["close"]
    high = candle["high"]
    low = candle["low"]
    
    body_size = abs(close - open_price)
    total_range = high - low
    
    # Ha a test mérete nagyon kicsi a teljes tartományhoz képest
    return body_size / total_range < 0.1 if total_range > 0 else False

def is_hammer(candle: Dict[str, Any]) -> bool:
    """
    Hammer (kalapács) gyertyaformáció felismerése
    """
    open_price = candle["open"]
    close = candle["close"]
    high = candle["high"]
    low = candle["low"]
    
    body_size = abs(close - open_price)
    total_range = high - low
    
    if total_range == 0:
        return False
    
    body_position = (min(open_price, close) - low) / total_range
    lower_shadow = min(open_price, close) - low
    upper_shadow = high - max(open_price, close)
    
    # Kalapács: kis test a gyertya felső részén, hosszú alsó árnyék
    return (body_position > 0.6 and  # Test a felső 40%-ban
            lower_shadow > 2 * body_size and  # Alsó árnyék legalább 2x test
            upper_shadow < 0.2 * lower_shadow)  # Felső árnyék kicsi

def is_shooting_star(candle: Dict[str, Any]) -> bool:
    """
    Shooting Star gyertyaformáció felismerése
    """
    open_price = candle["open"]
    close = candle["close"]
    high = candle["high"]
    low = candle["low"]
    
    body_size = abs(close - open_price)
    total_range = high - low
    
    if total_range == 0:
        return False
    
    body_position = (high - max(open_price, close)) / total_range
    lower_shadow = min(open_price, close) - low
    upper_shadow = high - max(open_price, close)
    
    # Shooting Star: kis test a gyertya alsó részén, hosszú felső árnyék
    return (body_position > 0.6 and  # Test az alsó 40%-ban
            upper_shadow > 2 * body_size and  # Felső árnyék legalább 2x test
            lower_shadow < 0.2 * upper_shadow)  # Alsó árnyék kicsi

def is_bullish_engulfing(current: Dict[str, Any], previous: Dict[str, Any]) -> bool:
    """
    Bullish Engulfing gyertyaformáció felismerése
    """
    curr_open = current["open"]
    curr_close = current["close"]
    prev_open = previous["open"]
    prev_close = previous["close"]
    
    # Bullish Engulfing: előző medve gyertya, jelenlegi bika gyertya ami teljesen magába foglalja
    return (prev_close < prev_open and  # Előző medve
            curr_close > curr_open and  # Jelenlegi bika
            curr_open <= prev_close and  # Jelenlegi nyitás <= előző zárás
            curr_close >= prev_open)  # Jelenlegi zárás >= előző nyitás

def is_bearish_engulfing(current: Dict[str, Any], previous: Dict[str, Any]) -> bool:
    """
    Bearish Engulfing gyertyaformáció felismerése
    """
    curr_open = current["open"]
    curr_close = current["close"]
    prev_open = previous["open"]
    prev_close = previous["close"]
    
    # Bearish Engulfing: előző bika gyertya, jelenlegi medve gyertya ami teljesen magába foglalja
    return (prev_close > prev_open and  # Előző bika
            curr_close < curr_open and  # Jelenlegi medve
            curr_open >= prev_close and  # Jelenlegi nyitás >= előző zárás
            curr_close <= prev_open)  # Jelenlegi zárás <= előző nyitás

def detect_patterns(candle: Dict[str, Any], previous_candle: Optional[Dict[str, Any]] = None) -> Tuple[Optional[str], int]:
    """
    Gyertyaformációk felismerése és értékelése
    
    Returns:
        Tuple[str, int]: (formáció neve, erősség pontszám 1-5)
    """
    patterns = []
    score = 0
    
    # Egyszerű formációk (egy gyertya)
    if is_doji(candle):
        patterns.append("Doji")
        score += 1
    
    if is_hammer(candle):
        patterns.append("Hammer")
        score += 3
    
    if is_shooting_star(candle):
        patterns.append("Shooting Star")
        score += 3
    
    # Összetett formációk (két gyertya)
    if previous_candle:
        if is_bullish_engulfing(candle, previous_candle):
            patterns.append("Bullish Engulfing")
            score += 4
        
        if is_bearish_engulfing(candle, previous_candle):
            patterns.append("Bearish Engulfing")
            score += 4
    
    # Ha több formáció is van, a legerősebbet választjuk
    if patterns:
        strongest_pattern = max(patterns, key=lambda p: {
            "Doji": 1,
            "Hammer": 3,
            "Shooting Star": 3,
            "Bullish Engulfing": 4,
            "Bearish Engulfing": 4
        }.get(p, 0))
        
        return strongest_pattern, score
    
    return None, 0
