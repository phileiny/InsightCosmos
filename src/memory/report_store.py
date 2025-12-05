"""
InsightCosmos Report Store

Provides CRUD operations for daily/weekly reports.

Classes:
    ReportStore: Report data management

Usage:
    from src.memory.database import Database
    from src.memory.report_store import ReportStore

    db = Database.from_config(config)
    store = ReportStore(db)

    # Get last report
    last_report = store.get_last_daily_report()

    # Create new report
    report_id = store.create_daily_report(
        report_date=date.today(),
        period_start=last_period_end,
        period_end=datetime.utcnow(),
        article_count=10,
        top_articles=[1, 2, 3],
        content='{"digest": ...}'
    )
"""

from typing import Optional, Dict, Any, List
from datetime import datetime, date
from sqlalchemy import desc
import json
import logging

from src.memory.models import DailyReport
from src.memory.database import Database
from src.utils.logger import Logger


class ReportStore:
    """
    Report storage management

    Provides CRUD operations for daily reports with support for:
    - Querying last report (for time-based filtering)
    - Creating new reports with period tracking
    - Querying by date

    Attributes:
        database (Database): Database instance
        logger (Logger): Logger instance

    Example:
        >>> store = ReportStore(db)
        >>> last = store.get_last_daily_report()
        >>> if last:
        ...     period_start = last['period_end']
        ... else:
        ...     period_start = datetime.utcnow() - timedelta(days=30)
    """

    def __init__(self, database: Database, logger: Optional[logging.Logger] = None):
        """
        Initialize ReportStore

        Args:
            database: Database instance
            logger: Logger instance (optional)
        """
        self.database = database
        self.logger = logger or Logger.get_logger("ReportStore")

    def get_last_daily_report(self) -> Optional[Dict[str, Any]]:
        """
        Get the most recent daily report

        Returns the last daily report record, which can be used to determine
        the starting time for the next report's article collection.

        Returns:
            Optional[dict]: Last report data with period_end, or None if no reports exist

        Example:
            >>> last = store.get_last_daily_report()
            >>> if last:
            ...     print(f"Last report ended at: {last['period_end']}")
            ... else:
            ...     print("No previous reports found")
        """
        try:
            with self.database.get_session() as session:
                report = session.query(DailyReport)\
                    .order_by(desc(DailyReport.created_at))\
                    .first()

                if report:
                    self.logger.info(
                        f"Found last daily report: {report.report_date}, "
                        f"period_end={report.period_end}"
                    )
                    return report.to_dict()

                self.logger.info("No previous daily reports found")
                return None

        except Exception as e:
            self.logger.error(f"Failed to get last daily report: {e}")
            return None

    def create_daily_report(
        self,
        report_date: date,
        period_start: datetime,
        period_end: datetime,
        article_count: int,
        top_articles: List[int],
        content: str,
        sent_at: Optional[datetime] = None
    ) -> int:
        """
        Create a new daily report record

        Args:
            report_date: Report date (unique per day)
            period_start: Article collection start time
            period_end: Article collection end time
            article_count: Number of articles included
            top_articles: List of article IDs
            content: Report content (JSON string)
            sent_at: Email sent timestamp (optional)

        Returns:
            int: New report ID

        Raises:
            ValueError: If report for this date already exists
            Exception: If database operation fails

        Example:
            >>> report_id = store.create_daily_report(
            ...     report_date=date.today(),
            ...     period_start=datetime(2025, 12, 4, 8, 0),
            ...     period_end=datetime(2025, 12, 5, 8, 0),
            ...     article_count=10,
            ...     top_articles=[101, 102, 103],
            ...     content='{"top_articles": [...], "daily_insight": "..."}'
            ... )
        """
        try:
            # Convert date to datetime for comparison if needed
            if isinstance(report_date, date) and not isinstance(report_date, datetime):
                report_date_dt = datetime.combine(report_date, datetime.min.time())
            else:
                report_date_dt = report_date

            with self.database.get_session() as session:
                # Check if report for this date already exists
                existing = session.query(DailyReport)\
                    .filter(DailyReport.report_date == report_date_dt)\
                    .first()

                if existing:
                    self.logger.warning(
                        f"Daily report for {report_date} already exists (id={existing.id}), "
                        "updating instead"
                    )
                    # Update existing report
                    existing.period_start = period_start
                    existing.period_end = period_end
                    existing.article_count = article_count
                    existing.top_articles = json.dumps(top_articles)
                    existing.content = content
                    existing.sent_at = sent_at
                    session.flush()
                    return existing.id

                # Create new report
                report = DailyReport(
                    report_date=report_date_dt,
                    period_start=period_start,
                    period_end=period_end,
                    article_count=article_count,
                    top_articles=json.dumps(top_articles),
                    content=content,
                    sent_at=sent_at
                )

                session.add(report)
                session.flush()

                report_id = report.id

                self.logger.info(
                    f"Created daily report: id={report_id}, date={report_date}, "
                    f"period={period_start} to {period_end}, articles={article_count}"
                )

                return report_id

        except Exception as e:
            self.logger.error(f"Failed to create daily report: {e}")
            raise

    def get_daily_report_by_date(self, report_date: date) -> Optional[Dict[str, Any]]:
        """
        Get daily report by date

        Args:
            report_date: Report date to query (can be date or datetime)

        Returns:
            Optional[dict]: Report data or None if not found

        Example:
            >>> report = store.get_daily_report_by_date(date(2025, 12, 5))
        """
        try:
            # Convert date to datetime for comparison if needed
            if isinstance(report_date, date) and not isinstance(report_date, datetime):
                from datetime import datetime as dt
                report_date_dt = dt.combine(report_date, dt.min.time())
            else:
                report_date_dt = report_date

            with self.database.get_session() as session:
                report = session.query(DailyReport)\
                    .filter(DailyReport.report_date == report_date_dt)\
                    .first()

                if report:
                    return report.to_dict()
                return None

        except Exception as e:
            self.logger.error(f"Failed to get daily report by date: {e}")
            return None

    def update_sent_at(self, report_id: int, sent_at: datetime) -> bool:
        """
        Update report sent_at timestamp after email is sent

        Args:
            report_id: Report ID
            sent_at: Email sent timestamp

        Returns:
            bool: True if updated successfully

        Example:
            >>> store.update_sent_at(report_id, datetime.utcnow())
        """
        try:
            with self.database.get_session() as session:
                report = session.query(DailyReport)\
                    .filter(DailyReport.id == report_id)\
                    .first()

                if not report:
                    self.logger.warning(f"Daily report not found: {report_id}")
                    return False

                report.sent_at = sent_at
                session.flush()

                self.logger.info(f"Updated daily report {report_id} sent_at: {sent_at}")
                return True

        except Exception as e:
            self.logger.error(f"Failed to update daily report sent_at: {e}")
            return False

    def get_all_daily_reports(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get all daily reports

        Args:
            limit: Maximum number of results (optional)

        Returns:
            List[dict]: List of daily reports ordered by created_at (newest first)

        Example:
            >>> reports = store.get_all_daily_reports(limit=10)
        """
        try:
            with self.database.get_session() as session:
                query = session.query(DailyReport)\
                    .order_by(desc(DailyReport.created_at))

                if limit:
                    query = query.limit(limit)

                reports = query.all()

                return [report.to_dict() for report in reports]

        except Exception as e:
            self.logger.error(f"Failed to get all daily reports: {e}")
            return []
