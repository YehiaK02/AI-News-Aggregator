"""
Google Sheets Client Module
Handles reading from and writing to Google Sheets
"""

import os
import json
import logging
from typing import Dict, List, Optional
from datetime import datetime

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

logger = logging.getLogger(__name__)


class SheetsClient:
    """Google Sheets API client"""
    
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
    
    def __init__(
        self,
        credentials_json: Optional[str] = None,
        sheet_id: Optional[str] = None
    ):
        """
        Initialize Sheets client
        
        Args:
            credentials_json: JSON string of service account credentials
            sheet_id: Google Sheet ID
        """
        # Get credentials from argument or environment
        creds_json = credentials_json or os.getenv('GOOGLE_SHEETS_CREDENTIALS')
        if not creds_json:
            raise ValueError(
                "GOOGLE_SHEETS_CREDENTIALS must be provided or set in environment"
            )
        
        # Get sheet ID
        self.sheet_id = sheet_id or os.getenv('GOOGLE_SHEET_ID')
        if not self.sheet_id:
            raise ValueError("GOOGLE_SHEET_ID must be provided or set in environment")
        
        # Parse credentials
        try:
            creds_dict = json.loads(creds_json)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid credentials JSON: {e}")
        
        # Create credentials object
        self.creds = Credentials.from_service_account_info(
            creds_dict,
            scopes=self.SCOPES
        )
        
        # Build service
        self.service = build('sheets', 'v4', credentials=self.creds)
    
    def append_row(
        self,
        data: Dict,
        sheet_name: str = 'Processed Articles'
    ) -> bool:
        """
        Append a row to the specified sheet
        
        Args:
            data: Dictionary with row data
            sheet_name: Name of the sheet tab
            
        Returns:
            True if successful
        """
        try:
            # Build row from data
            row = [
                data.get('date', ''),
                data.get('source', ''),
                data.get('category', ''),
                data.get('title', ''),
                data.get('summary', ''),
                data.get('sources', ''),
                data.get('source_count', 0),
                data.get('confidence', ''),
                datetime.now().isoformat(),
                data.get('duplicate_count', 1)
            ]

            # Append to sheet
            range_name = f"{sheet_name}!A:J"
            
            body = {'values': [row]}
            
            result = self.service.spreadsheets().values().append(
                spreadsheetId=self.sheet_id,
                range=range_name,
                valueInputOption='RAW',
                insertDataOption='INSERT_ROWS',
                body=body
            ).execute()
            
            logger.debug(f"Appended row to {sheet_name}")
            return True
            
        except HttpError as e:
            logger.error(f"HTTP error appending to sheet: {e}")
            return False
        except Exception as e:
            logger.error(f"Error appending to sheet: {e}")
            return False
    
    def save_to_review_tab(
        self,
        articles: List[Dict],
        sheet_name: str = 'Review Queue'
    ) -> bool:
        """
        Save Tier 2 articles to review tab
        
        Args:
            articles: List of classified articles
            sheet_name: Name of review sheet
            
        Returns:
            True if successful
        """
        try:
            rows = []
            
            for item in articles:
                article = item.get('article', {})
                
                row = [
                    article.get('published', ''),
                    article.get('source_name', ''),
                    item.get('category', ''),
                    article.get('title', ''),
                    article.get('summary', ''),
                    item.get('confidence', ''),
                    item.get('reason', ''),
                    article.get('url', '')
                ]
                
                rows.append(row)
            
            if not rows:
                return True
            
            # Append all rows
            range_name = f"{sheet_name}!A:H"
            
            body = {'values': rows}
            
            result = self.service.spreadsheets().values().append(
                spreadsheetId=self.sheet_id,
                range=range_name,
                valueInputOption='RAW',
                insertDataOption='INSERT_ROWS',
                body=body
            ).execute()
            
            logger.info(f"Saved {len(rows)} articles to {sheet_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving to review tab: {e}")
            return False
    
    def save_rejected_log(
        self,
        articles: List[Dict],
        sheet_name: str = 'Rejected Log'
    ) -> bool:
        """
        Save rejected articles to log tab
        
        Args:
            articles: List of rejected articles
            sheet_name: Name of log sheet
            
        Returns:
            True if successful
        """
        try:
            rows = []
            
            for item in articles:
                article = item.get('article', {})
                
                row = [
                    article.get('published', ''),
                    article.get('source_name', ''),
                    article.get('title', ''),
                    item.get('reason', ''),
                    article.get('url', '')
                ]
                
                rows.append(row)
            
            if not rows:
                return True
            
            # Append all rows
            range_name = f"{sheet_name}!A:E"
            
            body = {'values': rows}
            
            result = self.service.spreadsheets().values().append(
                spreadsheetId=self.sheet_id,
                range=range_name,
                valueInputOption='RAW',
                insertDataOption='INSERT_ROWS',
                body=body
            ).execute()
            
            logger.debug(f"Logged {len(rows)} rejected articles")
            return True
            
        except Exception as e:
            logger.error(f"Error saving rejected log: {e}")
            return False
    
    def create_headers(self) -> bool:
        """
        Create header rows for all sheets if they don't exist
        
        Returns:
            True if successful
        """
        headers = {
            'Processed Articles': [
                'Date',
                'Source',
                'Category',
                'Title',
                'Summary',
                'Sources',
                'Source Count',
                'Confidence',
                'Processed At',
                'Duplicate Count'
            ],
            'Review Queue': [
                'Date',
                'Source',
                'Category',
                'Title',
                'Summary',
                'Confidence',
                'Reason',
                'URL'
            ],
            'Rejected Log': [
                'Date',
                'Source',
                'Title',
                'Rejection Reason',
                'URL'
            ]
        }
        
        try:
            for sheet_name, header_row in headers.items():
                range_name = f"{sheet_name}!A1:Z1"
                
                body = {'values': [header_row]}
                
                self.service.spreadsheets().values().update(
                    spreadsheetId=self.sheet_id,
                    range=range_name,
                    valueInputOption='RAW',
                    body=body
                ).execute()
            
            logger.info("Created/updated headers for all sheets")
            return True
            
        except Exception as e:
            logger.error(f"Error creating headers: {e}")
            return False
