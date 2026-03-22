import re
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
from typing import Tuple, Optional, Dict
from dataclasses import dataclass

@dataclass
class DateRange:
    """Normalized date range"""
    start_date: date
    end_date: date
    
    def to_dict(self) -> Dict:
        return {
            'start_date': self.start_date.isoformat(),
            'end_date': self.end_date.isoformat()
        }


class DateNormalizer:
    """Normalizes natural language date expressions to date ranges"""
    
    def __init__(self):
        self.reference_date = date.today()
    
    def normalize(self, date_expr: str, reference_date: Optional[date] = None) -> Optional[DateRange]:
        """
        Convert natural language date to standardized date range.
        Returns None if date expression cannot be parsed.
        """
        if not date_expr:
            return None
        
        self.reference_date = reference_date or date.today()
        date_expr_lower = date_expr.lower().strip()
        
        # Try all patterns
        patterns = [
            self._handle_last_month,
            self._handle_this_month,
            self._handle_next_month,
            self._handle_last_week,
            self._handle_this_week,
            self._handle_next_week,
            self._handle_year_to_date,
            self._handle_last_n_days,
            self._handle_specific_month,
            self._handle_date_range,
            self._handle_single_date,
            self._handle_quarter,
            self._handle_year,
        ]
        
        for handler in patterns:
            result = handler(date_expr_lower)
            if result:
                return result
        
        return None
    
    def _handle_last_month(self, expr: str) -> Optional[DateRange]:
        """Handle 'last month'"""
        if 'last month' in expr or 'previous month' in expr:
            first_day = (self.reference_date.replace(day=1) - timedelta(days=1)).replace(day=1)
            last_day = self.reference_date.replace(day=1) - timedelta(days=1)
            return DateRange(first_day, last_day)
        return None
    
    def _handle_this_month(self, expr: str) -> Optional[DateRange]:
        """Handle 'this month'"""
        if 'this month' in expr or 'current month' in expr:
            first_day = self.reference_date.replace(day=1)
            last_day = (self.reference_date.replace(day=1) + relativedelta(months=1) - timedelta(days=1))
            return DateRange(first_day, last_day)
        return None
    
    def _handle_next_month(self, expr: str) -> Optional[DateRange]:
        """Handle 'next month'"""
        if 'next month' in expr:
            first_day = (self.reference_date.replace(day=1) + relativedelta(months=1))
            last_day = (first_day + relativedelta(months=1) - timedelta(days=1))
            return DateRange(first_day, last_day)
        return None
    
    def _handle_last_week(self, expr: str) -> Optional[DateRange]:
        """Handle 'last week'"""
        if 'last week' in expr or 'previous week' in expr:
            end_date = self.reference_date - timedelta(days=self.reference_date.weekday() + 1)
            start_date = end_date - timedelta(days=6)
            return DateRange(start_date, end_date)
        return None
    
    def _handle_this_week(self, expr: str) -> Optional[DateRange]:
        """Handle 'this week'"""
        if 'this week' in expr or 'current week' in expr:
            start_date = self.reference_date - timedelta(days=self.reference_date.weekday())
            end_date = start_date + timedelta(days=6)
            return DateRange(start_date, end_date)
        return None
    
    def _handle_next_week(self, expr: str) -> Optional[DateRange]:
        """Handle 'next week'"""
        if 'next week' in expr:
            start_date = self.reference_date + timedelta(days=7 - self.reference_date.weekday())
            end_date = start_date + timedelta(days=6)
            return DateRange(start_date, end_date)
        return None
    
    def _handle_year_to_date(self, expr: str) -> Optional[DateRange]:
        """Handle 'year to date'"""
        if 'year to date' in expr or 'ytd' in expr:
            start_date = self.reference_date.replace(month=1, day=1)
            end_date = self.reference_date
            return DateRange(start_date, end_date)
        return None
    
    def _handle_last_n_days(self, expr: str) -> Optional[DateRange]:
        """Handle 'last N days'"""
        match = re.search(r'last\s+(\d+)\s+days', expr)
        if match:
            n = int(match.group(1))
            start_date = self.reference_date - timedelta(days=n)
            end_date = self.reference_date
            return DateRange(start_date, end_date)
        return None
    
    def _handle_specific_month(self, expr: str) -> Optional[DateRange]:
        """Handle 'March' or 'January'"""
        months = {
            'january': 1, 'february': 2, 'march': 3, 'april': 4,
            'may': 5, 'june': 6, 'july': 7, 'august': 8,
            'september': 9, 'october': 10, 'november': 11, 'december': 12
        }
        
        for month_name, month_num in months.items():
            if month_name in expr:
                # Check if year is specified
                year_match = re.search(r'\d{4}', expr)
                year = int(year_match.group()) if year_match else self.reference_date.year
                
                start_date = date(year, month_num, 1)
                if month_num == 12:
                    end_date = date(year + 1, 1, 1) - timedelta(days=1)
                else:
                    end_date = date(year, month_num + 1, 1) - timedelta(days=1)
                
                return DateRange(start_date, end_date)
        return None
    
    def _handle_date_range(self, expr: str) -> Optional[DateRange]:
        """Handle 'March 15-20' or '15-20 March'"""
        # Pattern: Month Day-Day
        match = re.search(r'([a-z]+)\s+(\d+)\s*-\s*(\d+)', expr, re.IGNORECASE)
        if match:
            month_name, start_day, end_day = match.groups()
            month_num = self._get_month_number(month_name)
            if month_num:
                year = self.reference_date.year
                # Handle year boundary
                if month_num == 1 and int(start_day) < 10 and self.reference_date.month == 12:
                    year += 1
                
                try:
                    start_date = date(year, month_num, int(start_day))
                    end_date = date(year, month_num, int(end_day))
                    return DateRange(start_date, end_date)
                except ValueError:
                    pass
        
        # Pattern: Day-Month or Day-Month-Year
        match = re.search(r'(\d+)[/\s-]+([a-z]+)(?:\s+(\d{4}))?', expr, re.IGNORECASE)
        if match:
            day, month_name, year = match.groups()
            month_num = self._get_month_number(month_name)
            year = int(year) if year else self.reference_date.year
            
            try:
                start_date = date(year, month_num, int(day))
                return DateRange(start_date, start_date)
            except ValueError:
                pass
        
        return None
    
    def _handle_single_date(self, expr: str) -> Optional[DateRange]:
        """Handle single date expressions like 'today', 'yesterday'"""
        if expr == 'today':
            return DateRange(self.reference_date, self.reference_date)
        elif expr == 'yesterday':
            yesterday = self.reference_date - timedelta(days=1)
            return DateRange(yesterday, yesterday)
        elif expr == 'tomorrow':
            tomorrow = self.reference_date + timedelta(days=1)
            return DateRange(tomorrow, tomorrow)
        return None
    
    def _handle_quarter(self, expr: str) -> Optional[DateRange]:
        """Handle 'Q1', 'first quarter', etc."""
        quarter_match = re.search(r'q([1-4])|([a-z]+)\s+quarter', expr, re.IGNORECASE)
        if quarter_match:
            quarter_num = quarter_match.group(1) or quarter_match.group(2)
            quarter_map = {'first': 1, 'second': 2, 'third': 3, 'fourth': 4}
            
            if quarter_num.isdigit():
                quarter = int(quarter_num)
            else:
                quarter = quarter_map.get(quarter_num.lower(), None)
            
            if quarter:
                start_month = (quarter - 1) * 3 + 1
                start_date = date(self.reference_date.year, start_month, 1)
                if start_month + 2 > 12:
                    end_date = date(self.reference_date.year + 1, 1, 1) - timedelta(days=1)
                else:
                    end_date = date(self.reference_date.year, start_month + 3, 1) - timedelta(days=1)
                return DateRange(start_date, end_date)
        return None
    
    def _handle_year(self, expr: str) -> Optional[DateRange]:
        """Handle '2023' or 'last year'"""
        # Specific year
        year_match = re.search(r'\b(20\d{2})\b', expr)
        if year_match:
            year = int(year_match.group(1))
            start_date = date(year, 1, 1)
            end_date = date(year, 12, 31)
            return DateRange(start_date, end_date)
        
        # Last year
        if 'last year' in expr:
            year = self.reference_date.year - 1
            start_date = date(year, 1, 1)
            end_date = date(year, 12, 31)
            return DateRange(start_date, end_date)
        
        return None
    
    def _get_month_number(self, month_name: str) -> Optional[int]:
        """Convert month name to number"""
        months = {
            'jan': 1, 'january': 1,
            'feb': 2, 'february': 2,
            'mar': 3, 'march': 3,
            'apr': 4, 'april': 4,
            'may': 5,
            'jun': 6, 'june': 6,
            'jul': 7, 'july': 7,
            'aug': 8, 'august': 8,
            'sep': 9, 'september': 9,
            'oct': 10, 'october': 10,
            'nov': 11, 'november': 11,
            'dec': 12, 'december': 12
        }
        return months.get(month_name.lower())