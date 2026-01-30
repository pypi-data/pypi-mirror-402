"""
Birthday Calculator Utility

Real-time birthday countdown calculations with precision timing.
Handles timezone-aware calculations and various date formats.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, date, timedelta
from typing import Optional, Tuple
from enum import Enum
import re


class BirthdayStatus(Enum):
    """Birthday proximity status."""
    TODAY = "today"
    TOMORROW = "tomorrow"
    THIS_WEEK = "this_week"  # Within 7 days
    THIS_MONTH = "this_month"  # Within 30 days
    UPCOMING = "upcoming"  # More than 30 days
    JUST_PASSED = "just_passed"  # Within last 7 days


@dataclass
class BirthdayInfo:
    """
    Complete birthday information with countdown details.
    
    Attributes:
        name: Person's name
        birth_date: Original birth date
        next_birthday: Next upcoming birthday date
        age_turning: Age they will turn on next birthday
        current_age: Current age
        status: Birthday proximity status
        days_remaining: Days until birthday
        hours_remaining: Additional hours after days
        minutes_remaining: Additional minutes after hours
        seconds_remaining: Additional seconds after minutes
        total_seconds: Total seconds until birthday
        is_leap_year_baby: Born on Feb 29
        formatted_countdown: Human-readable countdown string
    """
    name: str
    birth_date: date
    next_birthday: date
    age_turning: int
    current_age: int
    status: BirthdayStatus
    days_remaining: int
    hours_remaining: int
    minutes_remaining: int
    seconds_remaining: int
    total_seconds: int
    is_leap_year_baby: bool
    formatted_countdown: str
    formatted_date: str


class BirthdayCalculator:
    """
    Enterprise-grade birthday calculator with real-time precision.
    
    Features:
    - Real-time countdown to the second
    - Handles leap year birthdays (Feb 29)
    - Multiple date format parsing
    - Age calculation
    - Status categorization
    """
    
    # Supported date formats
    DATE_FORMATS = [
        "%d/%m/%Y",      # 25/12/2003
        "%d/%m/%y",      # 25/12/03
        "%d-%m-%Y",      # 25-12-2003
        "%d-%m-%y",      # 25-12-03
        "%Y-%m-%d",      # 2003-12-25
        "%d %b %Y",      # 25 Dec 2003
        "%d %B %Y",      # 25 December 2003
        "%m/%d/%Y",      # 12/25/2003 (US format - try last)
    ]
    
    @classmethod
    def parse_date(cls, date_str: str) -> Optional[date]:
        """
        Parse date string in various formats.
        
        Args:
            date_str: Date string to parse
            
        Returns:
            Parsed date or None if parsing fails
        """
        if not date_str:
            return None
            
        # Clean the string
        date_str = date_str.strip()
        
        # Handle formats like "1/10/2003" (single digit day/month)
        # Normalize to consistent format first
        parts = re.split(r'[/\-]', date_str)
        if len(parts) == 3:
            try:
                # Assume DD/MM/YYYY or D/M/YYYY format
                day = int(parts[0])
                month = int(parts[1])
                year = int(parts[2])
                
                # Handle 2-digit years
                if year < 100:
                    year = 2000 + year if year < 50 else 1900 + year
                
                # Validate and swap if month > 12 (might be US format)
                if month > 12 and day <= 12:
                    day, month = month, day
                
                return date(year, month, day)
            except (ValueError, IndexError):
                pass
        
        # Try standard formats
        for fmt in cls.DATE_FORMATS:
            try:
                parsed = datetime.strptime(date_str, fmt).date()
                return parsed
            except ValueError:
                continue
        
        return None
    
    @classmethod
    def calculate(cls, name: str, birth_date: date, now: Optional[datetime] = None) -> BirthdayInfo:
        """
        Calculate complete birthday information.
        
        Args:
            name: Person's name
            birth_date: Birth date
            now: Current datetime (defaults to now, useful for testing)
            
        Returns:
            BirthdayInfo with all countdown details
        """
        if now is None:
            now = datetime.now()
        
        today = now.date()
        current_year = today.year
        
        # Check for leap year birthday
        is_leap_baby = birth_date.month == 2 and birth_date.day == 29
        
        # Calculate this year's birthday
        try:
            this_year_birthday = date(current_year, birth_date.month, birth_date.day)
        except ValueError:
            # Leap year baby on non-leap year - use Feb 28
            if is_leap_baby:
                this_year_birthday = date(current_year, 2, 28)
            else:
                raise
        
        # Determine next birthday
        if this_year_birthday < today:
            # Birthday passed this year, calculate for next year
            try:
                next_birthday = date(current_year + 1, birth_date.month, birth_date.day)
            except ValueError:
                # Leap year baby
                next_birthday = date(current_year + 1, 2, 28)
        else:
            next_birthday = this_year_birthday
        
        # Calculate ages
        current_age = today.year - birth_date.year
        if (today.month, today.day) < (birth_date.month, birth_date.day):
            current_age -= 1
        
        age_turning = next_birthday.year - birth_date.year
        
        # Calculate time remaining with precision
        birthday_datetime = datetime(
            next_birthday.year, 
            next_birthday.month, 
            next_birthday.day,
            0, 0, 0  # Midnight of birthday
        )
        
        delta = birthday_datetime - now
        total_seconds = max(0, int(delta.total_seconds()))
        
        # Break down the time
        days = total_seconds // 86400
        remaining = total_seconds % 86400
        hours = remaining // 3600
        remaining = remaining % 3600
        minutes = remaining // 60
        seconds = remaining % 60
        
        # Determine status
        if days == 0 and today == next_birthday:
            status = BirthdayStatus.TODAY
        elif days == 0 or (days == 1 and hours < 24):
            # Check if it's actually tomorrow
            tomorrow = today + timedelta(days=1)
            if next_birthday == tomorrow:
                status = BirthdayStatus.TOMORROW
            elif next_birthday == today:
                status = BirthdayStatus.TODAY
            else:
                status = BirthdayStatus.THIS_WEEK
        elif days <= 7:
            status = BirthdayStatus.THIS_WEEK
        elif days <= 30:
            status = BirthdayStatus.THIS_MONTH
        else:
            status = BirthdayStatus.UPCOMING
        
        # Check if birthday just passed (within 7 days ago)
        days_since = (today - this_year_birthday).days
        if 0 < days_since <= 7:
            status = BirthdayStatus.JUST_PASSED
        
        # Format countdown string
        formatted_countdown = cls._format_countdown(days, hours, minutes, seconds, status)
        
        # Format birth date nicely
        formatted_date = birth_date.strftime("%B %d, %Y")
        
        return BirthdayInfo(
            name=name,
            birth_date=birth_date,
            next_birthday=next_birthday,
            age_turning=age_turning,
            current_age=current_age,
            status=status,
            days_remaining=days,
            hours_remaining=hours,
            minutes_remaining=minutes,
            seconds_remaining=seconds,
            total_seconds=total_seconds,
            is_leap_year_baby=is_leap_baby,
            formatted_countdown=formatted_countdown,
            formatted_date=formatted_date,
        )
    
    @classmethod
    def _format_countdown(
        cls, 
        days: int, 
        hours: int, 
        minutes: int, 
        seconds: int,
        status: BirthdayStatus
    ) -> str:
        """Format countdown as human-readable string."""
        
        if status == BirthdayStatus.TODAY:
            return "🎂 TODAY IS YOUR BIRTHDAY! 🎂"
        
        if status == BirthdayStatus.JUST_PASSED:
            return "🎈 Birthday was recently! Hope it was great! 🎈"
        
        parts = []
        
        if days > 0:
            parts.append(f"{days} day{'s' if days != 1 else ''}")
        
        if hours > 0 or days > 0:
            parts.append(f"{hours} hour{'s' if hours != 1 else ''}")
        
        if minutes > 0 or hours > 0 or days > 0:
            parts.append(f"{minutes} minute{'s' if minutes != 1 else ''}")
        
        parts.append(f"{seconds} second{'s' if seconds != 1 else ''}")
        
        if status == BirthdayStatus.TOMORROW:
            return f"🎉 TOMORROW! Only {', '.join(parts)} left! 🎉"
        
        return f"{', '.join(parts)} until birthday"
    
    @classmethod
    def get_zodiac_sign(cls, birth_date: date) -> Tuple[str, str]:
        """
        Get zodiac sign for birth date.
        
        Returns:
            Tuple of (sign_name, emoji)
        """
        month = birth_date.month
        day = birth_date.day
        
        zodiac_dates = [
            ((1, 20), "Aquarius", "♒"),
            ((2, 19), "Pisces", "♓"),
            ((3, 21), "Aries", "♈"),
            ((4, 20), "Taurus", "♉"),
            ((5, 21), "Gemini", "♊"),
            ((6, 21), "Cancer", "♋"),
            ((7, 23), "Leo", "♌"),
            ((8, 23), "Virgo", "♍"),
            ((9, 23), "Libra", "♎"),
            ((10, 23), "Scorpio", "♏"),
            ((11, 22), "Sagittarius", "♐"),
            ((12, 22), "Capricorn", "♑"),
            ((12, 32), "Capricorn", "♑"),  # End of year
        ]
        
        for (end_month, end_day), sign, emoji in zodiac_dates:
            if month < end_month or (month == end_month and day < end_day):
                return sign, emoji
        
        return "Capricorn", "♑"
