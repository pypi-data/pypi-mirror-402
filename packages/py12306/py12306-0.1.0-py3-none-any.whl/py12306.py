#!/usr/bin/env python3
"""
China Railway (12306) API Client
================================

A CLI and Python library for querying China Railway (12306) data.

Usage:
    ./railway.py tickets --date 2026-01-25 --from 北京 --to 上海 [options]
    ./railway.py stops G1 --date 2026-01-25
    ./railway.py transfers --date 2026-01-25 --from 成都 --to 杭州 [options]
    ./railway.py stations 杭州

Examples:
    # Find high-speed trains from Beijing to Shanghai, morning departure
    ./railway.py tickets --date 2026-01-25 --from 北京 --to 上海 --trains G --depart-after 8 --depart-before 12

    # Find fastest trains, limit to 5 results
    ./railway.py tickets --date 2026-01-25 --from 长沙 --to 杭州 --sort duration --limit 5

    # Get stops for a specific train
    ./railway.py stops G899 --date 2026-01-25

    # Find transfer options
    ./railway.py transfers --date 2026-01-25 --from 成都 --to 杭州 --trains G --limit 3

    # List all stations in a city
    ./railway.py stations 杭州

Note:
    Station names are auto-resolved. You can use city names (北京, 上海) or 
    specific station names (北京南, 上海虹桥). The API performs city-level
    searches, so using any station in a city returns results for all stations.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from datetime import date, datetime
from functools import lru_cache
from typing import Any

import requests

# ============================================================================
# Constants
# ============================================================================

API = {
    "web_index": "https://www.12306.cn/index/",
    "stations": "https://kyfw.12306.cn/otn/resources/js/framework/station_name.js",
    "train_search": "https://search.12306.cn/search/v1/train/search",
    "train_stops": "https://kyfw.12306.cn/otn/czxx/queryByTrainNo",
    "ticket_init": "https://kyfw.12306.cn/otn/leftTicket/init",
    "ticket_query": "https://kyfw.12306.cn/otn/leftTicket/queryG",
    "interline_init": "https://kyfw.12306.cn/otn/lcQuery/init",
    "interline_query": "https://kyfw.12306.cn/lcquery/queryG",  # Fallback, dynamically discovered
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    "Referer": "https://kyfw.12306.cn/otn/leftTicket/init",
}

SEAT = {
    "9": "商务座",  "P": "特等座",  "M": "一等座",  "D": "优选一等座",
    "O": "二等座",  "S": "二等包座", "6": "高级软卧", "A": "高级动卧",
    "4": "软卧",    "F": "动卧",    "I": "一等卧",  "J": "二等卧",
    "3": "硬卧",    "2": "软座",    "1": "硬座",    "W": "无座",
    "H": "其他",
}

# Seat short names for availability field lookup
SEAT_SHORT = {
    "9": "swz", "P": "tz", "M": "zy", "D": "zy", "O": "ze", "S": "ze",
    "6": "gr", "A": "gr", "4": "rw", "F": "srrb", "I": "rw", "J": "yw",
    "3": "yw", "2": "rz", "1": "yz", "W": "wz", "H": "qt",
}

# Seat availability field indices in ticket response
SEAT_FIELD = {"9": 32, "P": 32, "M": 31, "D": 31, "O": 30, "W": 26, "F": 33, "I": 22, "J": 33, "A": 21, "6": 21, "4": 22, "3": 26, "2": 23, "1": 28}

# Ticket response field indices (the API returns pipe-separated fields)
class TicketField:
    """Named indices for ticket response fields."""
    TRAIN_NO = 2
    TRAIN_CODE = 3
    ORIGIN_CODE = 6
    DEST_CODE = 7
    DEPART_TIME = 8
    ARRIVE_TIME = 9
    DURATION = 10
    BOOKABLE = 11
    PRICE_INFO = 39
    DW_FLAG = 46
    DISCOUNT_INFO = 54


# ============================================================================
# Data Models
# ============================================================================

@dataclass(frozen=True, slots=True)
class Station:
    """A railway station."""
    name: str           # 北京南
    code: str           # VNP (telecode)
    pinyin: str         # beijingnan
    short: str          # bjn
    city: str           # 北京
    city_code: str      # 0357
    index: int          # 3

    def to_dict(self) -> dict[str, Any]:
        return {"name": self.name, "code": self.code, "pinyin": self.pinyin,
                "short": self.short, "city": self.city, "city_code": self.city_code, "index": self.index}


@dataclass(frozen=True, slots=True)
class Seat:
    """Seat availability and pricing."""
    type: str           # 9, M, O
    name: str           # 商务座, 一等座, 二等座
    price: float        # 1748.0
    available: str      # "有", "无", "12"
    discount: int | None = None  # Discount percentage (e.g., 80 = 80% of full price)
    berths: tuple[tuple[str, float], ...] | None = None  # Berth-level prices: (("上铺", 495), ("中铺", 507), ...)

    def to_dict(self) -> dict[str, Any]:
        d = {"type": self.type, "name": self.name, "price": self.price, "available": self.available}
        if self.discount is not None:
            d["discount"] = self.discount
        if self.berths:
            d["berths"] = {name: price for name, price in self.berths}
        return d


@dataclass(frozen=True, slots=True)
class Stop:
    """A stop on a train route."""
    no: int             # 1, 2, 3
    station: str        # 北京南
    arrive: str         # "----" or "07:31"
    depart: str         # "07:00" or "----"
    stop_time: str      # "----" or "2分钟"
    elapsed: str        # "00:00", "00:31" (from origin)

    def to_dict(self) -> dict[str, Any]:
        return {"no": self.no, "station": self.station, "arrive": self.arrive,
                "depart": self.depart, "stop_time": self.stop_time, "elapsed": self.elapsed}


@dataclass(slots=True)
class Train:
    """A train with route and schedule."""
    code: str           # G1
    no: str             # 24000000G10K
    type: str           # 高速
    origin: str         # 北京南
    terminus: str       # 上海
    stops: list[Stop] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {"code": self.code, "no": self.no, "type": self.type,
                "origin": self.origin, "terminus": self.terminus,
                "stops": [s.to_dict() for s in self.stops]}


@dataclass(slots=True)
class Ticket:
    """A ticket for a train journey."""
    train: str          # G1
    train_no: str       # 24000000G10K
    origin: str         # 北京南
    origin_code: str    # VNP
    dest: str           # 上海虹桥
    dest_code: str      # AOH
    depart: str         # 08:00
    arrive: str         # 12:32
    duration: int       # 272 (minutes)
    bookable: bool      # True
    seats: list[Seat] = field(default_factory=list)
    features: list[str] = field(default_factory=list)  # 复兴号, 智能动车组, 静音车厢, etc.

    @property
    def duration_str(self) -> str:
        return f"{self.duration // 60:02d}:{self.duration % 60:02d}"

    def to_dict(self) -> dict[str, Any]:
        d = {
            "train": self.train, "train_no": self.train_no,
            "origin": {"name": self.origin, "code": self.origin_code},
            "dest": {"name": self.dest, "code": self.dest_code},
            "depart": self.depart, "arrive": self.arrive,
            "duration": self.duration_str, "duration_min": self.duration,
            "bookable": self.bookable, "seats": [s.to_dict() for s in self.seats],
        }
        if self.features:
            d["features"] = self.features
        return d


@dataclass(slots=True)
class Transfer:
    """A transfer journey with multiple legs."""
    date: str
    origin: str
    origin_code: str
    via: str
    via_code: str
    dest: str
    dest_code: str
    depart: str         # First leg departure
    arrive: str         # Last leg arrival
    duration: int       # Total minutes
    wait: int           # Transfer wait minutes
    same_station: bool = True   # Same station transfer (同站换乘)
    same_train: bool = False    # Same train transfer (同车换乘)
    legs: list[Ticket] = field(default_factory=list)

    @property
    def duration_str(self) -> str:
        return f"{self.duration // 60:02d}:{self.duration % 60:02d}"
    
    @property
    def transfer_type(self) -> str:
        if self.same_train:
            return "同车换乘"
        elif self.same_station:
            return "同站换乘"
        else:
            return "异站换乘"

    def to_dict(self) -> dict[str, Any]:
        return {
            "date": self.date,
            "origin": {"name": self.origin, "code": self.origin_code},
            "via": {"name": self.via, "code": self.via_code},
            "dest": {"name": self.dest, "code": self.dest_code},
            "depart": self.depart, "arrive": self.arrive,
            "duration": self.duration_str, "duration_min": self.duration,
            "wait_min": self.wait, "transfer_type": self.transfer_type,
            "same_station": self.same_station, "same_train": self.same_train,
            "legs": [leg.to_dict() for leg in self.legs],
        }


# ============================================================================
# Utilities
# ============================================================================

def _hhmm_to_min(t: str) -> int:
    """Convert HH:MM to minutes. Returns -1 on failure."""
    try:
        h, m = t.split(":")
        return int(h) * 60 + int(m)
    except (ValueError, AttributeError):
        return -1


def _min_to_hhmm(m: int) -> str:
    """Convert minutes to HH:MM."""
    return f"{m // 60:02d}:{m % 60:02d}"


def _parse_prices(s: str) -> dict[str, tuple[float, int]]:
    """
    Parse price string from ticket API.
    
    Format varies by train type:
    - G/D trains: {type:1}{price*10:05d}{count:05d} = 11 chars per entry
    - Z/T/K trains: {type:1}{price*10:05d}{count:04d} = 10 chars per entry
    
    Example: "9174800001M093000021O055300021"
    Returns: {seat_type: (price, count)}
    """
    result = {}
    known_types = set("9PMDO6A4FIJ321WHS")
    
    # Try 11-char chunks first: type(1) + price(5) + count(5) - G/D trains format
    matches_11 = []
    for i in range(0, len(s) - 10, 11):
        chunk = s[i:i+11]
        if len(chunk) >= 11:
            t, p, c = chunk[0], chunk[1:6], chunk[6:11]
            if t in known_types and p.isdigit() and c.isdigit():
                matches_11.append((t, int(p) / 10, int(c)))
    
    # Try 10-char chunks: type(1) + price(5) + count(4) - Z/T/K trains format
    matches_10 = []
    for i in range(0, len(s) - 9, 10):
        chunk = s[i:i+10]
        if len(chunk) >= 10:
            t, p, c = chunk[0], chunk[1:6], chunk[6:10]
            if t in known_types and p.isdigit() and c.isdigit():
                matches_10.append((t, int(p) / 10, int(c)))
    
    # Regex fallback for 11-char format (handles non-aligned data)
    matches_11_regex = []
    for m in re.finditer(r"([A-Z])(\d{5})(\d{5})", s):
        t, p, c = m.groups()
        if t in known_types:
            matches_11_regex.append((t, int(p) / 10, int(c)))
    
    # Regex fallback for 10-char format
    matches_10_regex = []
    for m in re.finditer(r"([A-Z])(\d{5})(\d{4})(?!\d)", s):  # Negative lookahead to avoid matching 11-char
        t, p, c = m.groups()
        if t in known_types:
            matches_10_regex.append((t, int(p) / 10, int(c)))
    
    # Choose the best match:
    # 1. Prefer chunk-based parsing if string length matches expected format
    # 2. Fall back to regex if chunk parsing found fewer results
    if len(s) % 11 == 0 and matches_11:
        matches = matches_11
    elif len(s) % 10 == 0 and matches_10:
        matches = matches_10
    else:
        # Use whichever approach found more valid seat types
        all_matches = [matches_11, matches_10, matches_11_regex, matches_10_regex]
        matches = max(all_matches, key=len)
    
    for t, price, count in matches:
        if t not in result:
            result[t] = (price, count)
    
    return result


def _parse_berth_prices(s: str) -> dict[str, dict[str, float]]:
    """
    Parse berth-level price string from ticket API field 53.
    
    Format: {seat_type:1}{berth_type:1}{price*10:05d} repeated
    Berth types: 1=下铺(lower), 2=中铺(middle), 3=上铺(upper)
    
    Example: "33049503105210320507" for 硬卧 with 3 berth types
    Returns: {seat_type: {berth_name: price}}
    
    Example output: {"3": {"上铺": 495.0, "中铺": 507.0, "下铺": 521.0}}
    """
    result: dict[str, dict[str, float]] = {}
    berth_names = {"1": "下铺", "2": "中铺", "3": "上铺"}
    
    # Each entry is 7 chars: seat(1) + berth(1) + price*10(5)
    for i in range(0, len(s) - 6, 7):
        chunk = s[i:i+7]
        if len(chunk) == 7:
            seat_type = chunk[0]
            berth_type = chunk[1]
            price_raw = chunk[2:7]
            
            if price_raw.isdigit() and berth_type in berth_names:
                price = int(price_raw) / 10
                berth_name = berth_names[berth_type]
                
                if seat_type not in result:
                    result[seat_type] = {}
                result[seat_type][berth_name] = price
    
    return result


def _parse_discounts(s: str) -> dict[str, int]:
    """
    Parse discount string from ticket API.
    Format: {type}{discount:04d} repeated (discount is percentage, e.g., 0080 = 80%)
    Example: "M0080O0075" means 一等座 80% off, 二等座 75% off
    Returns: {seat_type: discount_percentage}
    """
    result = {}
    for i in range(0, len(s), 5):
        chunk = s[i:i+5]
        if len(chunk) < 5:
            break
        seat_type = chunk[0]
        try:
            discount = int(chunk[1:5])
            if discount > 0:
                result[seat_type] = discount
        except ValueError:
            continue
    return result


def _parse_features(dw_flag: str) -> list[str]:
    """
    Parse dw_flag string to extract train features.
    
    dw_flag format: values separated by '#'
    - Index 0: "5" = 智能动车组
    - Index 1: "1" = 复兴号
    - Index 2: starts with "Q" = 静音车厢, "R" = 温馨动卧
    - Index 5: "D" = 动感号
    - Index 6: not "z" = 支持选铺
    - Index 7: not "z" = 老年优惠
    
    Example: "5#1#Q##D#z#z" -> ["智能动车组", "复兴号", "静音车厢", "动感号"]
    """
    if not dw_flag:
        return []
    
    parts = dw_flag.split("#")
    features = []
    
    # Index 0: 智能动车组
    if len(parts) > 0 and parts[0] == "5":
        features.append("智能动车组")
    
    # Index 1: 复兴号
    if len(parts) > 1 and parts[1] == "1":
        features.append("复兴号")
    
    # Index 2: 静音车厢 or 温馨动卧
    if len(parts) > 2 and parts[2]:
        if parts[2].startswith("Q"):
            features.append("静音车厢")
        elif parts[2].startswith("R"):
            features.append("温馨动卧")
    
    # Index 5: 动感号
    if len(parts) > 5 and parts[5] == "D":
        features.append("动感号")
    
    # Index 6: 支持选铺
    if len(parts) > 6 and parts[6] and parts[6] != "z":
        features.append("支持选铺")
    
    # Index 7: 老年优惠
    if len(parts) > 7 and parts[7] and parts[7] != "z":
        features.append("老年优惠")
    
    return features


@lru_cache(maxsize=1)
def _session() -> requests.Session:
    """
    Get a session with cookies initialized.
    
    The session is cached to reuse cookies across requests.
    Note: If the session expires, you may need to restart the process.
    """
    s = requests.Session()
    s.headers.update(HEADERS)
    s.get(API["ticket_init"], timeout=30)
    return s


@lru_cache(maxsize=1)
def _discover_interline_api() -> str:
    """
    Dynamically discover the interline query API path from the init page.
    12306 may change this path, so we extract it from the page.
    
    Returns:
        Full URL for interline query API
    """
    try:
        resp = requests.get(API["interline_init"], headers=HEADERS, timeout=30)
        resp.raise_for_status()
        
        # Look for: var lc_search_url = '/lcquery/queryG';
        match = re.search(r"var\s+lc_search_url\s*=\s*['\"]([^'\"]+)['\"]", resp.text)
        if match:
            path = match.group(1)
            # Path might be relative or absolute
            if path.startswith("/"):
                return f"https://kyfw.12306.cn{path}"
            return path
    except (requests.RequestException, AttributeError):
        pass
    
    # Fallback to hardcoded URL
    return API["interline_query"]


# ============================================================================
# Station Functions
# ============================================================================

@lru_cache(maxsize=1)
def _load_stations_cached() -> tuple[Station, ...]:
    """Internal cached loader - returns tuple for hashability."""
    resp = requests.get(API["stations"], headers=HEADERS, timeout=30)
    resp.raise_for_status()
    
    stations = []
    for m in re.finditer(r"@([^@]+)", resp.text):
        p = m.group(1).rstrip("'").split("|")
        if len(p) >= 8:
            stations.append(Station(
                name=p[1], code=p[2], pinyin=p[3], short=p[4],
                city=p[7], city_code=p[6], index=int(p[5]) if p[5].isdigit() else 0
            ))
    return tuple(stations)


def load_stations() -> list[Station]:
    """
    Load all stations from 12306 API. Results are cached.
    
    Returns:
        List of Station objects
    """
    return list(_load_stations_cached())


# ============================================================================
# Pre-built Station Indexes (for O(1) lookups)
# ============================================================================

@lru_cache(maxsize=1)
def _station_indexes() -> dict[str, dict]:
    """
    Build all station indexes in a single pass over the data.
    
    Returns dict with keys:
        - "by_code": {telecode: Station}
        - "by_name": {name: Station}
        - "by_city": {city: [Station, ...]}
        - "city_rep": {city: Station}  (representative station for city)
    """
    stations = _load_stations_cached()
    
    by_code: dict[str, Station] = {}
    by_name: dict[str, Station] = {}
    by_city: dict[str, list[Station]] = {}
    city_rep: dict[str, Station] = {}
    
    for s in stations:
        by_code[s.code] = s
        by_name[s.name] = s
        by_city.setdefault(s.city, []).append(s)
        # Prefer station with same name as city (e.g., "北京" station for "北京" city)
        if s.city not in city_rep or s.name == s.city:
            city_rep[s.city] = s
    
    return {
        "by_code": by_code,
        "by_name": by_name,
        "by_city": by_city,
        "city_rep": city_rep,
    }


def get_current_date() -> str:
    """Get current date as YYYY-MM-DD."""
    return date.today().isoformat()


def get_stations_in_city(city: str) -> list[Station]:
    """
    Get all stations in a city. O(1) lookup.
    
    Args:
        city: City name in Chinese (e.g., "北京")
    
    Returns:
        List of Station objects in that city
    """
    return _station_indexes()["by_city"].get(city, [])


def get_station_by_name(name: str | list[str]) -> Station | None | dict[str, Station | None]:
    """
    Look up station(s) by name. O(1) lookup per name.
    
    Args:
        name: Station name (e.g., "北京南") or list of names
    
    Returns:
        - If single name: Station object or None if not found
        - If list: Dict mapping name to Station (or None if not found)
    
    Examples:
        >>> get_station_by_name("北京南")
        Station(name='北京南', code='VNP', ...)
        
        >>> get_station_by_name(["北京南", "上海虹桥"])
        {'北京南': Station(...), '上海虹桥': Station(...)}
    """
    idx = _station_indexes()["by_name"]
    if isinstance(name, list):
        return {n: idx.get(n) for n in name}
    return idx.get(name)


def get_station_by_code(code: str) -> Station | None:
    """
    Look up a station by telecode. O(1) lookup.
    
    Args:
        code: Station telecode (e.g., "VNP")
    
    Returns:
        Station object or None
    """
    return _station_indexes()["by_code"].get(code)


def get_city_station(city: str) -> Station | None:
    """
    Get the representative station for a city. O(1) lookup.
    
    This returns the station that represents the city (e.g., "北京" -> 北京站).
    Useful when user provides a city name instead of specific station.
    
    Args:
        city: City name in Chinese (e.g., "北京", "上海")
    
    Returns:
        Station object or None
    """
    return _station_indexes()["city_rep"].get(city)


def resolve_station(name: str) -> str:
    """
    Resolve a station/city name to its telecode.
    
    This is a convenience function that tries multiple lookup strategies:
    1. If already a valid telecode (3 uppercase letters), return as-is
    2. Try exact station name match (e.g., "北京南" -> "VNP")
    3. Try city name match (e.g., "北京" -> first station in city)
    
    Args:
        name: Station name, city name, or telecode
    
    Returns:
        Station telecode (e.g., "VNP")
    
    Raises:
        ValueError: If station/city not found
    
    Examples:
        >>> resolve_station("北京南")
        'VNP'
        >>> resolve_station("北京")
        'VAP'
        >>> resolve_station("VNP")
        'VNP'
    """
    # Already a telecode? (3 uppercase letters)
    if len(name) == 3 and name.isalpha() and name.isupper():
        if get_station_by_code(name):
            return name
    
    # Try exact station name match
    station = get_station_by_name(name)
    if station:
        return station.code
    
    # Try city name match
    stations = get_stations_in_city(name)
    if stations:
        return stations[0].code
    
    raise ValueError(f"Unknown station or city: {name}")


def validate_date(date_str: str) -> str:
    """
    Validate and normalize a date string.
    
    Args:
        date_str: Date in YYYY-MM-DD format
    
    Returns:
        Validated date string in YYYY-MM-DD format
    
    Raises:
        ValueError: If date is invalid or in the past
    """
    if not date_str:
        raise ValueError("Date is required")
    
    try:
        parsed = datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        raise ValueError(f"Invalid date format: {date_str} (expected YYYY-MM-DD)")
    
    if parsed < date.today():
        raise ValueError(f"Date {date_str} is in the past")
    
    return date_str


def validate_hour(hour: int | None, name: str) -> int | None:
    """
    Validate an hour value (0-23).
    
    Args:
        hour: Hour value or None
        name: Parameter name for error messages
    
    Returns:
        Validated hour or None
    
    Raises:
        ValueError: If hour is out of range
    """
    if hour is None:
        return None
    if not (0 <= hour <= 23):
        raise ValueError(f"{name} must be between 0 and 23, got {hour}")
    return hour


def validate_hour_range(after: int | None, before: int | None) -> None:
    """
    Validate that depart_after < depart_before when both are specified.
    
    Raises:
        ValueError: If range is invalid
    """
    if after is not None and before is not None and after >= before:
        raise ValueError(f"depart_after ({after}) must be less than depart_before ({before})")


def validate_positive_int(value: int | None, name: str) -> int | None:
    """
    Validate that a value is a positive integer.
    
    Args:
        value: Integer value or None
        name: Parameter name for error messages
    
    Returns:
        Validated value or None
    
    Raises:
        ValueError: If value is not positive
    """
    if value is None:
        return None
    if value <= 0:
        raise ValueError(f"{name} must be positive, got {value}")
    return value


def validate_wait_range(min_wait: int, max_wait: int) -> None:
    """
    Validate that min_wait <= max_wait.
    
    Raises:
        ValueError: If range is invalid
    """
    if min_wait < 0:
        raise ValueError(f"min_wait must be non-negative, got {min_wait}")
    if max_wait < 0:
        raise ValueError(f"max_wait must be non-negative, got {max_wait}")
    if min_wait > max_wait:
        raise ValueError(f"min_wait ({min_wait}) must be <= max_wait ({max_wait})")


def validate_sort(sort: str, valid_options: list[str]) -> str:
    """
    Validate sort option.
    
    Args:
        sort: Sort value
        valid_options: List of valid sort options
    
    Returns:
        Validated sort value
    
    Raises:
        ValueError: If sort is invalid
    """
    if sort not in valid_options:
        raise ValueError(f"sort must be one of {valid_options}, got '{sort}'")
    return sort


# ============================================================================
# Train Functions
# ============================================================================

def _find_train_no(code: str, date: str) -> str | None:
    """Find internal train_no from train code."""
    url = f"{API['train_search']}?keyword={code}&date={date.replace('-', '')}"
    try:
        data = requests.get(url, headers=HEADERS, timeout=30).json()
        for t in data.get("data", []):
            if t.get("station_train_code") == code:
                return t.get("train_no")
        return data["data"][0]["train_no"] if data.get("data") else None
    except (requests.RequestException, KeyError, IndexError):
        return None


def get_train_stops(train: str, date: str) -> Train | None:
    """
    Get full route/stops for a train.
    
    Args:
        train: Train code (e.g., "G1")
        date: Departure date (YYYY-MM-DD)
    
    Returns:
        Train object with stops, or None if not found
    """
    train_no = _find_train_no(train, date)
    if not train_no:
        return None
    
    try:
        resp = requests.get(API["train_stops"], headers=HEADERS, timeout=30, params={
            "train_no": train_no,
            "from_station_telecode": "BBB",
            "to_station_telecode": "BBB",
            "depart_date": date,
        })
        data = resp.json().get("data", {}).get("data", [])
    except (requests.RequestException, KeyError):
        return None
    
    if not data:
        return None
    
    first = data[0]
    origin_depart = _hhmm_to_min(first.get("start_time", ""))
    
    stops = []
    prev_time = origin_depart
    day_offset = 0  # Track midnight crossings
    
    for i, d in enumerate(data):
        arrive = d.get("arrive_time", "----")
        arrive_min = _hhmm_to_min(arrive)
        
        if i == 0:
            elapsed = "00:00"
        elif arrive_min < 0:
            elapsed = "----"
        else:
            # Detect midnight crossing: if arrive time < previous time, we crossed midnight
            if arrive_min < prev_time:
                day_offset += 1440  # Add 24 hours in minutes
            prev_time = arrive_min
            
            total_elapsed = arrive_min + day_offset - origin_depart
            hours, mins = divmod(total_elapsed, 60)
            elapsed = f"{hours:02d}:{mins:02d}"
        
        stops.append(Stop(
            no=int(d.get("station_no", i + 1)),
            station=d.get("station_name", ""),
            arrive=arrive,
            depart=d.get("start_time", "----"),
            stop_time=d.get("stopover_time", "----"),
            elapsed=elapsed,
        ))
    
    return Train(
        code=train,
        no=train_no,
        type=first.get("train_class_name", ""),
        origin=first.get("start_station_name", stops[0].station if stops else ""),
        terminus=first.get("end_station_name", stops[-1].station if stops else ""),
        stops=stops,
    )


# ============================================================================
# Ticket Functions
# ============================================================================

def _parse_ticket(raw: str, station_map: dict[str, str]) -> Ticket | None:
    """Parse a single ticket result string."""
    TF = TicketField
    BERTH_PRICE_FIELD = 53  # Field containing berth-level pricing
    try:
        p = raw.split("|")
        prices = _parse_prices(p[TF.PRICE_INFO]) if len(p) > TF.PRICE_INFO else {}
        discounts = _parse_discounts(p[TF.DISCOUNT_INFO]) if len(p) > TF.DISCOUNT_INFO else {}
        berth_prices = _parse_berth_prices(p[BERTH_PRICE_FIELD]) if len(p) > BERTH_PRICE_FIELD else {}
        
        seats = []
        for t, (price, count) in sorted(prices.items(), key=lambda x: -x[1][0]):
            # Get availability from dedicated field or fall back to count
            idx = SEAT_FIELD.get(t)
            avail = p[idx] if idx and len(p) > idx and p[idx] else (str(count) if count > 0 else "有")
            discount = discounts.get(t)
            # Validate discount is a reasonable percentage (0-100), else ignore
            if discount is not None and (discount <= 0 or discount > 100):
                discount = None
            # Get berth-level prices if available (for sleeper seats)
            berths = None
            if t in berth_prices:
                # Sort berths: 上铺, 中铺, 下铺
                berth_order = {"上铺": 0, "中铺": 1, "下铺": 2}
                sorted_berths = sorted(berth_prices[t].items(), key=lambda x: berth_order.get(x[0], 9))
                berths = tuple(sorted_berths)
            seats.append(Seat(type=t, name=SEAT.get(t, "其他"), price=price, available=avail, discount=discount, berths=berths))
        
        # Parse dw_flag for train features
        dw_flag = p[TF.DW_FLAG] if len(p) > TF.DW_FLAG else ""
        features = _parse_features(dw_flag)
        
        return Ticket(
            train=p[TF.TRAIN_CODE], train_no=p[TF.TRAIN_NO],
            origin=station_map.get(p[TF.ORIGIN_CODE], p[TF.ORIGIN_CODE]), origin_code=p[TF.ORIGIN_CODE],
            dest=station_map.get(p[TF.DEST_CODE], p[TF.DEST_CODE]), dest_code=p[TF.DEST_CODE],
            depart=p[TF.DEPART_TIME], arrive=p[TF.ARRIVE_TIME],
            duration=_hhmm_to_min(p[TF.DURATION]),
            bookable=p[TF.BOOKABLE] == "Y",
            seats=seats,
            features=features,
        )
    except (IndexError, ValueError):
        return None


def _query_tickets_raw(session: requests.Session, date: str, src: str, dst: str) -> tuple[list[str], dict[str, str]]:
    """Query raw ticket results."""
    params = {
        "leftTicketDTO.train_date": date,
        "leftTicketDTO.from_station": src,
        "leftTicketDTO.to_station": dst,
        "purpose_codes": "ADULT",
    }
    try:
        resp = session.get(API["ticket_query"], params=params, timeout=30)
        data = resp.json()
        
        # Handle dynamic endpoint redirect
        if not data.get("status") and data.get("c_url"):
            resp = session.get(f"https://kyfw.12306.cn/otn/{data['c_url']}", params=params, timeout=30)
            data = resp.json()
        
        result_data = data.get("data") or {}
        return result_data.get("result", []), result_data.get("map", {})
    except (requests.RequestException, KeyError, AttributeError, ValueError):
        return [], {}


def get_tickets(
    date: str,
    src: str,
    dst: str,
    *,
    trains: str | None = None,
    depart_after: int | None = None,
    depart_before: int | None = None,
    sort: str = "depart",
    limit: int | None = None,
) -> list[Ticket]:
    """
    Query available tickets between two stations.
    
    Note: The 12306 API performs city-level searches. Any station code will
    return results for ALL stations in that city (both origin and destination).
    For example, querying src="CWQ" (长沙南) returns trains from both 长沙 and 长沙南.
    
    Args:
        date: Travel date (YYYY-MM-DD)
        src: Origin station code (e.g., "VNP") - searches all stations in city
        dst: Destination station code (e.g., "AOH") - searches all stations in city
        trains: Filter by train type (e.g., "G", "GD", "GDCZ")
        depart_after: Earliest departure hour (0-23)
        depart_before: Latest departure hour (0-23, exclusive)
        sort: Sort by "depart", "arrive", or "duration"
        limit: Maximum results (must be positive)
    
    Returns:
        List of Ticket objects (may include different origin/dest stations than queried)
    
    Raises:
        ValueError: If parameters are invalid
    """
    # Validate inputs
    validate_date(date)
    if not src:
        raise ValueError("src (origin station) is required")
    if not dst:
        raise ValueError("dst (destination station) is required")
    validate_hour(depart_after, "depart_after")
    validate_hour(depart_before, "depart_before")
    validate_hour_range(depart_after, depart_before)
    validate_sort(sort, ["depart", "arrive", "duration"])
    validate_positive_int(limit, "limit")
    
    raw, station_map = _query_tickets_raw(_session(), date, src, dst)
    
    tickets = []
    for r in raw:
        t = _parse_ticket(r, station_map)
        if not t:
            continue
        
        # Filter by train type
        if trains and t.train[0].upper() not in trains.upper():
            continue
        
        # Filter by departure time
        depart_hour = _hhmm_to_min(t.depart) // 60
        if depart_after is not None and depart_hour < depart_after:
            continue
        if depart_before is not None and depart_hour >= depart_before:
            continue
        
        tickets.append(t)
    
    # Sort
    key = {"arrive": lambda t: t.arrive, "duration": lambda t: t.duration}.get(sort, lambda t: t.depart)
    tickets.sort(key=key)
    
    return tickets[:limit] if limit else tickets


# ============================================================================
# Transfer Functions (Native 12306 Interline API)
# ============================================================================

def _parse_interline_leg(leg: dict[str, Any]) -> Ticket:
    """Parse a leg from interline API response into a Ticket."""
    # Parse duration from "HH:MM" format
    lishi = leg.get("lishi", "00:00")
    duration = _hhmm_to_min(lishi) if lishi else 0
    
    # Parse discounts
    discounts = _parse_discounts(leg.get("seat_discount_info", ""))
    
    # Parse prices from yp_info field
    seats: list[Seat] = []
    yp_info = leg.get("yp_info", "")
    for i in range(0, len(yp_info), 10):
        chunk = yp_info[i:i+10]
        if len(chunk) < 10:
            break
        seat_type = chunk[0]
        # Handle special case: high count indicates 无座
        try:
            count = int(chunk[6:10])
            if count >= 3000:
                seat_type = "W"
        except ValueError:
            pass
        if seat_type not in SEAT:
            seat_type = "H"  # Other
        try:
            price = int(chunk[1:6]) / 10
        except ValueError:
            continue
        # Get availability from leg fields (ze_num, zy_num, etc.)
        avail_field = f"{SEAT_SHORT.get(seat_type, 'qt')}_num"
        avail = leg.get(avail_field, "--")
        if avail and avail != "--":
            discount = discounts.get(seat_type)
            seats.append(Seat(type=seat_type, name=SEAT[seat_type], price=price, available=avail, discount=discount))
    
    # Parse features
    dw_flag = leg.get("dw_flag", "")
    features = _parse_features(dw_flag)
    
    return Ticket(
        train=leg.get("station_train_code", ""),
        train_no=leg.get("train_no", ""),
        origin=leg.get("from_station_name", ""),
        origin_code=leg.get("from_station_telecode", ""),
        dest=leg.get("to_station_name", ""),
        dest_code=leg.get("to_station_telecode", ""),
        depart=leg.get("start_time", ""),
        arrive=leg.get("arrive_time", ""),
        duration=max(0, duration),
        bookable=True,
        seats=seats,
        features=features,
    )


def _parse_interline(item: dict[str, Any], date: str) -> Transfer | None:
    """Parse an interline result into a Transfer object."""
    try:
        # Parse duration from "X小时Y分钟" format
        all_lishi = item.get("all_lishi", "")
        match = re.match(r"(?:(\d+)小时)?(\d+)分钟", all_lishi)
        if match:
            hours = int(match.group(1) or 0)
            mins = int(match.group(2) or 0)
            duration = hours * 60 + mins
        else:
            duration = item.get("all_lishi_minutes", 0)
        
        # Parse wait time from "Xh Ym" or similar format
        wait_str = item.get("wait_time", "0")
        wait_mins = item.get("wait_time_minutes", 0)
        if not wait_mins:
            # Try parsing "1h 30m" format
            wait_match = re.match(r"(?:(\d+)h\s*)?(\d+)m?", wait_str)
            if wait_match:
                wait_mins = int(wait_match.group(1) or 0) * 60 + int(wait_match.group(2) or 0)
        
        # Parse legs
        legs = [_parse_interline_leg(leg) for leg in item.get("fullList", [])]
        if not legs:
            return None
        
        return Transfer(
            date=date,
            origin=item.get("from_station_name", ""),
            origin_code=item.get("from_station_code", ""),
            via=item.get("middle_station_name", ""),
            via_code=item.get("middle_station_code", ""),
            dest=item.get("end_station_name", ""),
            dest_code=item.get("end_station_code", ""),
            depart=item.get("start_time", ""),
            arrive=item.get("arrive_time", ""),
            duration=duration,
            wait=wait_mins,
            same_station=(item.get("same_station", "1") == "0"),  # "0" means same station
            same_train=(item.get("same_train", "N") == "Y"),
            legs=legs,
        )
    except (KeyError, ValueError, TypeError):
        return None


def get_transfers(
    date: str,
    src: str,
    dst: str,
    *,
    via: str | None = None,
    trains: str | None = None,
    min_wait: int = 30,
    max_wait: int = 180,
    sort: str = "duration",
    limit: int | None = None,
) -> list[Transfer]:
    """
    Query transfer tickets using 12306's native interline API.
    
    Note: Like get_tickets(), the API performs city-level searches for src/dst.
    
    Args:
        date: Travel date (YYYY-MM-DD)
        src: Origin station code - searches all stations in city
        dst: Destination station code - searches all stations in city
        via: Transfer station code (optional, 12306 auto-detects)
        trains: Filter by train type (e.g., "G", "GD")
        min_wait: Minimum transfer wait (minutes, default 30)
        max_wait: Maximum transfer wait (minutes, default 180)
        sort: Sort by "duration", "depart", or "arrive"
        limit: Maximum results (must be positive, default fetches up to 20)
    
    Returns:
        List of Transfer objects with same_station/same_train info
    
    Raises:
        ValueError: If parameters are invalid
    """
    # Validate inputs
    validate_date(date)
    if not src:
        raise ValueError("src (origin station) is required")
    if not dst:
        raise ValueError("dst (destination station) is required")
    validate_wait_range(min_wait, max_wait)
    validate_sort(sort, ["duration", "depart", "arrive"])
    validate_positive_int(limit, "limit")
    
    session = _session()
    results: list[Transfer] = []
    fetch_limit = limit if limit else 20
    
    # Dynamically discover the interline API endpoint
    interline_url = _discover_interline_api()
    
    params = {
        "train_date": date,
        "from_station_telecode": src,
        "to_station_telecode": dst,
        "middle_station": via or "",
        "result_index": "0",
        "can_query": "Y",
        "isShowWZ": "N",
        "purpose_codes": "00",
        "channel": "E",
    }
    
    try:
        while len(results) < fetch_limit:
            resp = session.get(interline_url, params=params, timeout=30)
            data = resp.json()
            
            if not data.get("status") or not isinstance(data.get("data"), dict):
                break
            
            result_data = data["data"]
            for item in result_data.get("middleList", []):
                transfer = _parse_interline(item, date)
                if transfer is None:
                    continue
                
                # Filter by train type
                if trains and transfer.legs:
                    first_train = transfer.legs[0].train
                    if not any(first_train.startswith(t.upper()) for t in trains):
                        continue
                
                # Filter by wait time
                if not (min_wait <= transfer.wait <= max_wait):
                    continue
                
                results.append(transfer)
            
            # Check if more results available
            if result_data.get("can_query") != "Y":
                break
            params["result_index"] = str(result_data.get("result_index", 0))
    
    except (requests.RequestException, KeyError, ValueError):
        pass
    
    # Sort
    key = {"depart": lambda t: t.depart, "arrive": lambda t: t.arrive}.get(sort, lambda t: t.duration)
    results.sort(key=key)
    
    return results[:limit] if limit else results


# ============================================================================
# CLI
# ============================================================================


def _json_out(obj: Any) -> None:
    """Print object as JSON."""
    if obj is None:
        print("null")
    elif isinstance(obj, list):
        print(json.dumps([x.to_dict() if hasattr(x, "to_dict") else x for x in obj], ensure_ascii=False, indent=2))
    elif hasattr(obj, "to_dict"):
        print(json.dumps(obj.to_dict(), ensure_ascii=False, indent=2))
    else:
        print(json.dumps(obj, ensure_ascii=False, indent=2))


def _cmd_tickets(args: argparse.Namespace) -> int:
    """Handle 'tickets' command."""
    try:
        validate_date(args.date)
        validate_hour(args.depart_after, "depart-after")
        validate_hour(args.depart_before, "depart-before")
        validate_hour_range(args.depart_after, args.depart_before)
        validate_positive_int(args.limit, "limit")
        src = resolve_station(args.from_)
        dst = resolve_station(args.to)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    
    tickets = get_tickets(
        date=args.date,
        src=src,
        dst=dst,
        trains=args.trains,
        depart_after=args.depart_after,
        depart_before=args.depart_before,
        sort=args.sort,
        limit=args.limit,
    )
    _json_out(tickets)
    return 0


def _cmd_stops(args: argparse.Namespace) -> int:
    """Handle 'stops' command."""
    try:
        validate_date(args.date)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    
    train = get_train_stops(train=args.train, date=args.date)
    if train is None:
        print(f"Error: Train {args.train} not found on {args.date}", file=sys.stderr)
        return 1
    _json_out(train)
    return 0


def _cmd_transfers(args: argparse.Namespace) -> int:
    """Handle 'transfers' command."""
    try:
        validate_date(args.date)
        validate_wait_range(args.min_wait, args.max_wait)
        validate_positive_int(args.limit, "limit")
        src = resolve_station(args.from_)
        dst = resolve_station(args.to)
        via = resolve_station(args.via) if args.via else None
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    
    transfers = get_transfers(
        date=args.date,
        src=src,
        dst=dst,
        via=via,
        trains=args.trains,
        min_wait=args.min_wait,
        max_wait=args.max_wait,
        sort=args.sort,
        limit=args.limit,
    )
    _json_out(transfers)
    return 0


def _cmd_stations(args: argparse.Namespace) -> int:
    """Handle 'stations' command."""
    query = args.query
    
    # Try as city name first
    stations = get_stations_in_city(query)
    if stations:
        _json_out(stations)
        return 0
    
    # Try as station name
    station = get_station_by_name(query)
    if station:
        _json_out(station)
        return 0
    
    # Try as telecode
    if len(query) == 3 and query.isalpha():
        station = get_station_by_code(query.upper())
        if station:
            _json_out(station)
            return 0
    
    print(f"Error: No station or city found matching '{query}'", file=sys.stderr)
    return 1


TRAIN_TYPES_HELP = """Train type filter. Accepts one or more type prefixes:
  G  - 高铁 (High-speed, 300-350 km/h)
  D  - 动车 (EMU, 200-250 km/h)
  C  - 城际 (Intercity)
  Z  - 直达 (Direct express)
  T  - 特快 (Express)
  K  - 快速 (Fast)
Examples: --trains G (G trains only), --trains GD (G and D trains)"""


def main() -> int:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="railway.py",
        description="China Railway (12306) API Client",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # tickets command
    p_tickets = subparsers.add_parser(
        "tickets",
        help="Query available tickets between stations",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=TRAIN_TYPES_HELP,
    )
    p_tickets.add_argument("--date", required=True, help="Travel date (YYYY-MM-DD)")
    p_tickets.add_argument("--from", dest="from_", required=True, metavar="STATION",
                          help="Origin station or city name (e.g., 北京, 北京南)")
    p_tickets.add_argument("--to", required=True, metavar="STATION",
                          help="Destination station or city name")
    p_tickets.add_argument("--trains", metavar="TYPES",
                          help="Filter by train type (e.g., G, GD, GDCZ)")
    p_tickets.add_argument("--depart-after", type=int, metavar="HOUR",
                          help="Earliest departure hour (0-23)")
    p_tickets.add_argument("--depart-before", type=int, metavar="HOUR",
                          help="Latest departure hour (0-23)")
    p_tickets.add_argument("--sort", choices=["depart", "arrive", "duration"], default="depart",
                          help="Sort results by (default: depart)")
    p_tickets.add_argument("--limit", type=int, metavar="N",
                          help="Maximum number of results")
    p_tickets.set_defaults(func=_cmd_tickets)
    
    # stops command
    p_stops = subparsers.add_parser("stops", help="Get all stops for a train")
    p_stops.add_argument("train", help="Train number (e.g., G1, D101, K511)")
    p_stops.add_argument("--date", required=True, help="Date (YYYY-MM-DD)")
    p_stops.set_defaults(func=_cmd_stops)
    
    # transfers command
    p_transfers = subparsers.add_parser(
        "transfers",
        help="Find transfer/connecting routes",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=TRAIN_TYPES_HELP,
    )
    p_transfers.add_argument("--date", required=True, help="Travel date (YYYY-MM-DD)")
    p_transfers.add_argument("--from", dest="from_", required=True, metavar="STATION",
                            help="Origin station or city name")
    p_transfers.add_argument("--to", required=True, metavar="STATION",
                            help="Destination station or city name")
    p_transfers.add_argument("--via", metavar="STATION",
                            help="Transfer via specific station (optional)")
    p_transfers.add_argument("--trains", metavar="TYPES",
                            help="Filter by train type (e.g., G, GD)")
    p_transfers.add_argument("--min-wait", type=int, default=30, metavar="MINS",
                            help="Minimum transfer time in minutes (default: 30)")
    p_transfers.add_argument("--max-wait", type=int, default=180, metavar="MINS",
                            help="Maximum transfer time in minutes (default: 180)")
    p_transfers.add_argument("--sort", choices=["depart", "arrive", "duration"], default="duration",
                            help="Sort results by (default: duration)")
    p_transfers.add_argument("--limit", type=int, metavar="N",
                            help="Maximum number of results")
    p_transfers.set_defaults(func=_cmd_transfers)
    
    # stations command
    p_stations = subparsers.add_parser("stations", help="Look up station information")
    p_stations.add_argument("query", help="City name, station name, or station code")
    p_stations.set_defaults(func=_cmd_stations)
    
    # Parse and execute
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 0
    
    try:
        return args.func(args)
    except requests.RequestException as e:
        print(f"Error: Network request failed: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
