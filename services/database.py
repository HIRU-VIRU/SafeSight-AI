"""
Database service for SafeSight AI.
Manages SQLite database for violation logging and analytics.
"""

import sqlite3
import csv
from typing import List, Dict, Any, Optional
from datetime import datetime, date
from pathlib import Path
from config.settings import DATABASE_PATH


class DatabaseService:
    """
    SQLite database service for violation storage and queries.
    """
    
    def __init__(self, db_path: str = DATABASE_PATH):
        """
        Initialize database service.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """Create database and tables if they don't exist."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS violations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                camera_id TEXT NOT NULL,
                person_id INTEGER NOT NULL,
                helmet_violation INTEGER NOT NULL,
                vest_violation INTEGER NOT NULL,
                boots_violation INTEGER NOT NULL,
                gloves_violation INTEGER NOT NULL,
                goggles_violation INTEGER NOT NULL,
                image_path TEXT
            )
        """)
        
        # Create index for faster queries
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_timestamp 
            ON violations(timestamp)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_camera_id 
            ON violations(camera_id)
        """)
        
        conn.commit()
        conn.close()
        
        print(f"✅ Database initialized: {self.db_path}")
    
    def insert_violation(self, violation: Dict[str, Any], 
                        camera_id: str, 
                        image_path: str) -> int:
        """
        Insert a violation record into the database.
        
        Args:
            violation: Violation dictionary with person_id and violation flags
            camera_id: Camera identifier
            image_path: Path to saved violation image
            
        Returns:
            ID of inserted record
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        timestamp = datetime.now().isoformat()
        
        cursor.execute("""
            INSERT INTO violations (
                timestamp, camera_id, person_id,
                helmet_violation, vest_violation, boots_violation,
                gloves_violation, goggles_violation, image_path
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            timestamp,
            camera_id,
            violation["person_id"],
            int(violation.get("helmet_violation", False)),
            int(violation.get("vest_violation", False)),
            int(violation.get("boots_violation", False)),
            int(violation.get("gloves_violation", False)),
            int(violation.get("goggles_violation", False)),
            image_path
        ))
        
        violation_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return violation_id
    
    def get_today_violations(self, camera_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get all violations from today.
        
        Args:
            camera_id: Optional filter by camera ID
            
        Returns:
            List of violation records
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        today = date.today().isoformat()
        
        if camera_id:
            cursor.execute("""
                SELECT * FROM violations 
                WHERE date(timestamp) = ? AND camera_id = ?
                ORDER BY timestamp DESC
            """, (today, camera_id))
        else:
            cursor.execute("""
                SELECT * FROM violations 
                WHERE date(timestamp) = ?
                ORDER BY timestamp DESC
            """, (today,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def get_violation_count(self, start_date: Optional[str] = None,
                           end_date: Optional[str] = None,
                           camera_id: Optional[str] = None) -> int:
        """
        Get total violation count within date range.
        
        Args:
            start_date: Start date (ISO format)
            end_date: End date (ISO format)
            camera_id: Optional filter by camera ID
            
        Returns:
            Total violation count
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        query = "SELECT COUNT(*) FROM violations WHERE 1=1"
        params = []
        
        if start_date:
            query += " AND date(timestamp) >= ?"
            params.append(start_date)
        
        if end_date:
            query += " AND date(timestamp) <= ?"
            params.append(end_date)
        
        if camera_id:
            query += " AND camera_id = ?"
            params.append(camera_id)
        
        cursor.execute(query, params)
        count = cursor.fetchone()[0]
        conn.close()
        
        return count
    
    def get_hourly_stats(self, target_date: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get hourly violation statistics for a specific date.
        
        Args:
            target_date: Date in ISO format (default: today)
            
        Returns:
            List of hourly statistics:
            [
                {"hour": 0, "count": 5},
                {"hour": 1, "count": 3},
                ...
            ]
        """
        if target_date is None:
            target_date = date.today().isoformat()
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                CAST(strftime('%H', timestamp) AS INTEGER) as hour,
                COUNT(*) as count
            FROM violations
            WHERE date(timestamp) = ?
            GROUP BY hour
            ORDER BY hour
        """, (target_date,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [{"hour": row[0], "count": row[1]} for row in rows]
    
    def export_csv(self, output_path: str, 
                  start_date: Optional[str] = None,
                  end_date: Optional[str] = None) -> bool:
        """
        Export violations to CSV file.
        
        Args:
            output_path: Path to output CSV file
            start_date: Optional start date filter
            end_date: Optional end date filter
            
        Returns:
            True if export successful
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            query = "SELECT * FROM violations WHERE 1=1"
            params = []
            
            if start_date:
                query += " AND date(timestamp) >= ?"
                params.append(start_date)
            
            if end_date:
                query += " AND date(timestamp) <= ?"
                params.append(end_date)
            
            query += " ORDER BY timestamp DESC"
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            if len(rows) == 0:
                print("No data to export")
                return False
            
            # Write to CSV
            with open(output_path, 'w', newline='') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=rows[0].keys())
                writer.writeheader()
                for row in rows:
                    writer.writerow(dict(row))
            
            conn.close()
            print(f"✅ Exported {len(rows)} records to {output_path}")
            return True
            
        except Exception as e:
            print(f"❌ Error exporting CSV: {e}")
            return False
    
    def get_recent_violations(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get most recent violations."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM violations 
            ORDER BY timestamp DESC 
            LIMIT ?
        """, (limit,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]

    # ------------------------------------------------------------------ new helpers

    def get_filtered_violations(
        self,
        camera_id: Optional[str] = None,
        date_str: Optional[str] = None,
        severity: Optional[str] = None,
        limit: int = 200,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """
        Get violations with combined filters.

        Args:
            camera_id: Optional camera filter
            date_str: Optional date filter (YYYY-MM-DD)
            severity: 'critical' (helmet+vest), 'warning' (any but not both), or None
            limit: Max rows
            offset: Pagination offset

        Returns:
            List of violation dicts
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        query = "SELECT * FROM violations WHERE 1=1"
        params: list = []

        if camera_id:
            query += " AND camera_id = ?"
            params.append(camera_id)

        if date_str:
            query += " AND date(timestamp) = ?"
            params.append(date_str)

        if severity == "critical":
            query += " AND helmet_violation = 1 AND vest_violation = 1"
        elif severity == "warning":
            query += (
                " AND (helmet_violation = 1 OR vest_violation = 1 OR "
                "boots_violation = 1 OR gloves_violation = 1 OR goggles_violation = 1)"
                " AND NOT (helmet_violation = 1 AND vest_violation = 1)"
            )

        query += " ORDER BY timestamp DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    def get_distinct_cameras(self) -> List[str]:
        """Return list of unique camera IDs in the database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT camera_id FROM violations ORDER BY camera_id")
        cameras = [row[0] for row in cursor.fetchall()]
        conn.close()
        return cameras

    def get_distinct_dates(self) -> List[str]:
        """Return list of unique violation dates (YYYY-MM-DD), newest first."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT DISTINCT date(timestamp) as d FROM violations ORDER BY d DESC"
        )
        dates = [row[0] for row in cursor.fetchall()]
        conn.close()
        return dates

    def get_severity_counts(
        self,
        camera_id: Optional[str] = None,
        date_str: Optional[str] = None,
    ) -> Dict[str, int]:
        """
        Return counts broken down by severity.

        Returns:
            {"critical": N, "warning": N, "normal": N, "total": N}
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        where = "WHERE 1=1"
        params: list = []
        if camera_id:
            where += " AND camera_id = ?"
            params.append(camera_id)
        if date_str:
            where += " AND date(timestamp) = ?"
            params.append(date_str)

        # critical = helmet AND vest
        cursor.execute(
            f"SELECT COUNT(*) FROM violations {where} AND helmet_violation=1 AND vest_violation=1",
            params,
        )
        critical = cursor.fetchone()[0]

        # warning = any violation but NOT (helmet AND vest)
        cursor.execute(
            f"SELECT COUNT(*) FROM violations {where} "
            "AND (helmet_violation=1 OR vest_violation=1 OR boots_violation=1 OR gloves_violation=1 OR goggles_violation=1) "
            "AND NOT (helmet_violation=1 AND vest_violation=1)",
            params,
        )
        warning = cursor.fetchone()[0]

        cursor.execute(f"SELECT COUNT(*) FROM violations {where}", params)
        total = cursor.fetchone()[0]

        conn.close()
        return {
            "critical": critical,
            "warning": warning,
            "total": total,
        }
