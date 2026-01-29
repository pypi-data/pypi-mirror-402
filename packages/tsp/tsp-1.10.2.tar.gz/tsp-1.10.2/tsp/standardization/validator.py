import re
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional


class Severity(Enum):
    ERROR = "error"
    WARNING = "warning"


@dataclass
class ValidationIssue:
    severity: Severity
    line_num: Optional[int]
    message: str

    def __str__(self):
        line_info = f"Line {self.line_num}: " if self.line_num else ""
        return f"[{self.severity.value.upper()}] {line_info}{self.message}"


class TSPValidator:
    def __init__(self, filepath: Path):
        self.filepath = filepath
        self.issues: list[ValidationIssue] = []
        self.lines: list[str] = []
        self.metadata_lines: list[str] = []
        self.header_line: Optional[str] = None
        self.header_idx: Optional[int] = None
        self.data_lines: list[str] = []

    def validate(self) -> list[ValidationIssue]:
        self._validate_file_extension()
        self._read_file()
        self._parse_structure()
        self._validate_encoding()
        self._validate_metadata()
        self._validate_header()
        self._validate_data_format()
        self._validate_timestamps()
        self._validate_missing_data()
        return self.issues

    def _error(self, message: str, line_num: Optional[int] = None):
        self.issues.append(ValidationIssue(Severity.ERROR, line_num, message))

    def _warning(self, message: str, line_num: Optional[int] = None):
        self.issues.append(ValidationIssue(Severity.WARNING, line_num, message))

    def _validate_file_extension(self):
        if self.filepath.suffix.lower() != '.csv':
            self._warning(f"File should use .csv extension (found: {self.filepath.suffix})")

    def _read_file(self):
        try:
            with open(self.filepath, 'r', encoding='utf-8') as f:
                self.lines = f.read().splitlines()
        except UnicodeDecodeError:
            self._error("File must use UTF-8 encoding")
            return
        except Exception as e:
            self._error(f"Could not read file: {e}")

    def _parse_structure(self):
        if not self.lines:
            return

        for idx, line in enumerate(self.lines):
            if line.startswith('#'):
                self.metadata_lines.append(line)
            elif self.header_line is None:
                self.header_line = line
                self.header_idx = idx
            else:
                if line.strip() == '':
                    self._error("File must not have blank lines", idx)
                else:
                    self.data_lines.append(line)

        if self.header_line is None:
            self._error("File must contain a header line")

    def _validate_encoding(self):
        try:
            with open(self.filepath, 'rb') as f:
                raw = f.read(3)
                if raw.startswith(b'\xef\xbb\xbf'):
                    self._error("File must use UTF-8 without BOM")
        except Exception:
            pass

    def _validate_metadata(self):
        key_pattern = re.compile(r'^[a-z][a-z0-9_]*$')
        
        for line in self.metadata_lines:
            if '=' in line:
                cleaned = line.lstrip('#').strip()
                if '=' in cleaned:
                    parts = cleaned.split('=', 1)
                    key = parts[0].strip()
                    if not key_pattern.match(key):
                        self._warning(f"Metadata key should be lowercase with underscores: {key}")

    def _validate_header(self):
        if not self.header_line:
            return

        if ',' not in self.header_line and self.header_line.strip():
            self._error("Header must use comma separator", self.header_idx)
            return

        headers = self.header_line.split(',')

        if headers[0] != 'timestamp':
            self._error("First column must be 'timestamp'", self.header_idx)

        if any(h.strip() == '' for h in headers):
            self._error("Header values must not be blank", self.header_idx)

        if self.header_line.rstrip().endswith(','):
            self._error("Header must not have trailing comma", self.header_idx)

        if len(headers) != len(set(headers)):
            self._error("Header values must be unique", self.header_idx)

        column_name_pattern = re.compile(r'^[a-z][a-z0-9_]*$')
        for h in headers[1:]:
            if not self._is_depth_value(h) and not column_name_pattern.match(h):
                self._error(f"Invalid column name (must start with letter, use lowercase/underscore): {h}", self.header_idx)

    def _is_depth_value(self, value: str) -> bool:
        try:
            float(value)
            return bool(re.match(r'^-?[0-9]+(\.[0-9]+)?$', value))
        except ValueError:
            return False

    def _is_numeric(self, value: str) -> bool:
        if value.strip() == '':
            return True
        try:
            float(value)
            return True
        except ValueError:
            return False

    def _normalize_timestamp(self, ts: str) -> str:
        """Normalize timestamp for comparison by padding to full ISO format"""
        ts = ts.strip()
        
        if 'T' not in ts:
            ts = ts + 'T00:00:00'
        
        # Check if timezone info is present at the end
        has_tz = ts.endswith('Z') or re.search(r'[+-]\d{2}:\d{2}$', ts)
        if not has_tz:
            ts = ts + 'Z'
        
        return ts

    def _extract_timezone(self, ts: str) -> Optional[str]:
        """Extract timezone from timestamp, returns None if no timezone"""
        ts = ts.strip()
        if ts.endswith('Z'):
            return 'Z'
        match = re.search(r'([+-]\d{2}:\d{2})$', ts)
        if match:
            return match.group(1)
        return None

    def _validate_wide_format(self, headers: list[str]):
        depths = []
        for h in headers[1:]:
            try:
                depths.append(float(h))
            except ValueError:
                self._error(f"Invalid depth value in header: {h}", self.header_idx)
        
        if depths and depths != sorted(depths):
            self._error("Depth values must be in ascending order", self.header_idx)

        if len(depths) != len(set(depths)):
            self._error("Depth values must be unique", self.header_idx)

        timestamps = []
        timezones = []
        
        for idx, line in enumerate(self.data_lines, start=self.header_idx + 1):
            values = line.split(',')
            
            if len(values) != len(headers):
                self._error(f"Row has {len(values)} values but header has {len(headers)} columns", idx)
                continue

            timestamp = values[0]
            timestamps.append(timestamp)
            
            tz = self._extract_timezone(timestamp)
            if tz:
                timezones.append(tz)

            for i, val in enumerate(values[1:], start=1):
                if not self._is_numeric(val):
                    self._error(f"Temperature value must be numeric or empty: '{val}'", idx)

        normalized = [self._normalize_timestamp(ts) for ts in timestamps]
        if normalized != sorted(normalized):
            self._error("Timestamps must be in chronological order")

        if len(timestamps) != len(set(timestamps)):
            self._error("Timestamps must be unique in wide format")

        self._check_timezone_consistency(timezones)

    def _check_timezone_consistency(self, timezones: list[str]):
        """Check that timezones are consistent and preferably UTC"""
        if not timezones:
            return
        
        unique_tzs = set(timezones)
        if len(unique_tzs) > 1:
            self._warning(f"Mixed timezones found: {unique_tzs}. Timestamps should use consistent timezone.")
        
        non_utc_count = sum(1 for tz in timezones if tz != 'Z')
        if non_utc_count > 0 and non_utc_count == len(timezones):
            self._warning(f"Timestamps with timezone should preferably use UTC (Z)")

    def _validate_data_format(self):
        if not self.header_line or not self.data_lines:
            return

        headers = self.header_line.split(',')
        
        if self._is_wide_format(headers):
            self._validate_wide_format(headers)
        elif self._is_long_format(headers):
            self._validate_long_format(headers)
        else:
            self._error("Could not determine format (wide or long)")

    def _is_wide_format(self, headers: list[str]) -> bool:
        return len(headers) > 1 and all(self._is_depth_value(h) for h in headers[1:])

    def _is_long_format(self, headers: list[str]) -> bool:
        return 'depth' in headers or ('depth_from' in headers and 'depth_to' in headers)

    def _validate_long_format(self, headers: list[str]):
        has_temp = 'temperature' in headers
        has_depth = 'depth' in headers
        has_depth_from = 'depth_from' in headers
        has_depth_to = 'depth_to' in headers
        has_site_id = 'site_id' in headers

        if has_depth and (has_depth_from or has_depth_to):
            self._error("Cannot have both 'depth' and 'depth_from'/'depth_to' columns")

        if not has_depth and not (has_depth_from and has_depth_to):
            self._error("Long format must have 'depth' or 'depth_from'/'depth_to' columns")

        if has_depth_from != has_depth_to:
            self._error("Both 'depth_from' and 'depth_to' required for intervals")

        is_extended = has_depth_from and has_depth_to
        
        if not has_temp and not is_extended:
            self._error("Long format must include 'temperature' column")
        elif not has_temp and is_extended:
            measurement_cols = [h for h in headers if h not in 
                            ['timestamp', 'depth', 'depth_from', 'depth_to', 'site_id'] 
                            and not h.endswith('_flag') and not h.endswith('_id')]
            if not measurement_cols:
                self._error("Extended format must have at least one measurement column when temperature is omitted")

        seen_combinations = set()
        site_groups = {}
        timezones = []

        for idx, line in enumerate(self.data_lines, start=self.header_idx + 1):
            values = line.split(',')
            
            if len(values) > len(headers):
                if not (len(values) == len(headers) + 1 and values[-1].strip() == ''):
                    self._error(f"Row has {len(values)} values but header has {len(headers)} columns", idx)
            elif len(values) < len(headers):
                self._error(f"Row has {len(values)} values but header has {len(headers)} columns", idx)
                continue

            row_dict = dict(zip(headers, values[:len(headers)]))
            
            timestamp = row_dict.get('timestamp', '')
            site_id = row_dict.get('site_id', '')
            
            tz = self._extract_timezone(timestamp)
            if tz:
                timezones.append(tz)

            if has_depth:
                depth = row_dict.get('depth', '')
                if depth.strip() == '':
                    self._error("Depth values must not be missing", idx)
                elif not self._is_numeric(depth):
                    self._error(f"Depth must be numeric: '{depth}'", idx)
                
                combo_key = (timestamp, depth, site_id) if has_site_id else (timestamp, depth)
            else:
                depth_from = row_dict.get('depth_from', '')
                depth_to = row_dict.get('depth_to', '')
                
                if depth_from.strip() == '' or depth_to.strip() == '':
                    self._error("Depth interval values must not be missing", idx)
                    continue
                
                if not self._is_numeric(depth_from) or not self._is_numeric(depth_to):
                    self._error(f"Depth values must be numeric", idx)
                    continue
                    
                try:
                    df = float(depth_from)
                    dt = float(depth_to)
                    if df > dt:
                        self._error(f"depth_from ({df}) must be <= depth_to ({dt})", idx)
                except ValueError:
                    pass
                
                combo_key = (timestamp, depth_from, depth_to, site_id) if has_site_id else (timestamp, depth_from, depth_to)

            if combo_key in seen_combinations:
                self._error(f"Duplicate combination found", idx)
            seen_combinations.add(combo_key)

            group_key = site_id if has_site_id else '_default'
            if group_key not in site_groups:
                site_groups[group_key] = []
            
            # Store both timestamp and depth for ordering validation
            if has_depth:
                depth_value = row_dict.get('depth', '')
                site_groups[group_key].append((timestamp, depth_value, idx))
            else:
                depth_from = row_dict.get('depth_from', '')
                site_groups[group_key].append((timestamp, depth_from, idx))

            if has_temp:
                temp = row_dict.get('temperature', '')
                if temp.strip() != '' and not self._is_numeric(temp):
                    self._error(f"Temperature must be numeric or empty: '{temp}'", idx)

        # Validate ordering
        for group_key, entries in site_groups.items():
            if has_site_id:
                self._validate_site_group_ordering(entries, group_key)
            else:
                # Without site_id, just check chronological order
                timestamps = [self._normalize_timestamp(ts) for ts, _, _ in entries]
                if timestamps != sorted(timestamps):
                    self._error("Timestamps must be in chronological order")

        if has_depth_from and has_depth_to:
            self._check_interval_overlaps(headers)

        self._check_timezone_consistency(timezones)

    def _validate_site_group_ordering(self, entries: list[tuple[str, str, int]], site_id: str):
        """
        Validate that entries within a site_id group are ordered either:
        (a) by depth, with timestamps chronological within each depth, or
        (b) by timestamp, with depths ascending within each timestamp
        """
        if len(entries) <= 1:
            return
        
        # Try to determine which ordering pattern is used
        # Pattern (a): grouped by depth
        depth_groups = {}
        for timestamp, depth, idx in entries:
            try:
                depth_val = float(depth)
                if depth_val not in depth_groups:
                    depth_groups[depth_val] = []
                depth_groups[depth_val].append((timestamp, idx))
            except ValueError:
                continue
        
        # Check if pattern (a) is valid: depths in order, timestamps chronological within depths
        pattern_a_valid = True
        sorted_depths = sorted(depth_groups.keys())
        current_pos = 0
        
        for depth in sorted_depths:
            timestamps_at_depth = depth_groups[depth]
            # Check if this depth group appears contiguously in the data
            depth_positions = [idx for ts, idx in timestamps_at_depth]
            if depth_positions != list(range(min(depth_positions), max(depth_positions) + 1)):
                pattern_a_valid = False
                break
            
            # Check if timestamps are chronological within this depth
            timestamps = [self._normalize_timestamp(ts) for ts, _ in timestamps_at_depth]
            if timestamps != sorted(timestamps):
                pattern_a_valid = False
                break
            
            # Check that this depth group comes after previous depths
            if min(depth_positions) < current_pos:
                pattern_a_valid = False
                break
            current_pos = max(depth_positions) + 1
        
        # Pattern (b): grouped by timestamp
        timestamp_groups = {}
        for timestamp, depth, idx in entries:
            norm_ts = self._normalize_timestamp(timestamp)
            if norm_ts not in timestamp_groups:
                timestamp_groups[norm_ts] = []
            try:
                depth_val = float(depth)
                timestamp_groups[norm_ts].append((depth_val, idx))
            except ValueError:
                continue
        
        # Check if pattern (b) is valid: timestamps in order, depths ascending within timestamps
        pattern_b_valid = True
        sorted_timestamps = sorted(timestamp_groups.keys())
        current_pos = 0
        
        for timestamp in sorted_timestamps:
            depths_at_timestamp = timestamp_groups[timestamp]
            # Check if this timestamp group appears contiguously in the data
            ts_positions = [idx for depth, idx in depths_at_timestamp]
            if ts_positions != list(range(min(ts_positions), max(ts_positions) + 1)):
                pattern_b_valid = False
                break
            
            # Check if depths are ascending within this timestamp
            depths = [d for d, _ in depths_at_timestamp]
            if depths != sorted(depths):
                pattern_b_valid = False
                break
            
            # Check that this timestamp group comes after previous timestamps
            if min(ts_positions) < current_pos:
                pattern_b_valid = False
                break
            current_pos = max(ts_positions) + 1
        
        if not pattern_a_valid and not pattern_b_valid:
            self._error(
                f"Rows within site_id '{site_id}' must be ordered either: "
                "(a) by depth with timestamps chronological within each depth, or "
                "(b) by timestamp with depths ascending within each timestamp"
            )

    def _check_interval_overlaps(self, headers: list[str]):
        has_site_id = 'site_id' in headers
        intervals_by_timestamp = {}

        for line in self.data_lines:
            values = line.split(',')
            row_dict = dict(zip(headers, values[:len(headers)]))
            
            timestamp = row_dict.get('timestamp', '')
            site_id = row_dict.get('site_id', '') if has_site_id else '_default'
            depth_from = row_dict.get('depth_from', '')
            depth_to = row_dict.get('depth_to', '')

            if not depth_from or not depth_to:
                continue

            try:
                df = float(depth_from)
                dt = float(depth_to)
            except ValueError:
                continue

            key = (timestamp, site_id)
            if key not in intervals_by_timestamp:
                intervals_by_timestamp[key] = []
            intervals_by_timestamp[key].append((df, dt))

        for key, intervals in intervals_by_timestamp.items():
            sorted_intervals = sorted(intervals)
            for i in range(len(sorted_intervals) - 1):
                curr_start, curr_end = sorted_intervals[i]
                next_start, next_end = sorted_intervals[i + 1]
                if curr_end > next_start:
                    self._error(f"Overlapping intervals at timestamp {key[0]}: [{curr_start}, {curr_end}] and [{next_start}, {next_end}]")

    def _validate_timestamps(self):
        iso_pattern = re.compile(
            r'^\d{4}-\d{2}-\d{2}(T\d{2}:\d{2}:\d{2}(\.\d+)?(Z|[+-]\d{2}:\d{2})?)?$'
        )
        
        for idx, line in enumerate(self.data_lines, start=self.header_idx + 1):
            timestamp = line.split(',')[0]
            if timestamp.strip() == '':
                self._error("Timestamp values must not be missing", idx)
            elif not iso_pattern.match(timestamp):
                self._error(f"Invalid ISO 8601 timestamp: '{timestamp}'", idx)

    def _validate_missing_data(self):
        placeholders = ['NA', 'NaN', 'NULL', '-999', 'na', 'nan', 'null', '-9999']
        
        for idx, line in enumerate(self.data_lines, start=self.header_idx + 1):
            values = line.split(',')
            for val in values:
                if val.strip() in placeholders:
                    self._error(f"Placeholder values not allowed (use empty string): '{val}'", idx)


def validate_tsp_file(filepath: str | Path) -> list[ValidationIssue]:
    validator = TSPValidator(Path(filepath))
    return validator.validate()


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python tsp_validator.py <file.csv>")
        sys.exit(1)
    
    issues = validate_tsp_file(sys.argv[1])
    
    if not issues:
        print("✓ File is valid")
        sys.exit(0)
    
    for issue in issues:
        print(issue)
    
    error_count = sum(1 for i in issues if i.severity == Severity.ERROR)
    sys.exit(1 if error_count > 0 else 0)