"""
WhatsApp Messaging Service via Twilio

Handles:
- WhatsApp message sending
- Business-formatted responses
- Delivery status tracking
- Retry logic with exponential backoff
- Error handling and logging
"""

import os
import time
import logging
from typing import Dict, Optional
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException

logger = logging.getLogger(__name__)


class WhatsAppServiceException(Exception):
    """Custom exception for WhatsApp service errors"""
    pass


class WhatsAppService:
    """
    Service for sending WhatsApp messages via Twilio.
    
    Features:
    - Retry logic (up to 2 attempts)
    - Delivery status logging
    - Professional message formatting
    - Error handling and graceful degradation
    """
    
    def __init__(self):
        """Initialize Twilio client with credentials"""
        self.account_sid = os.getenv("TWILIO_ACCOUNT_SID", "")
        self.auth_token = os.getenv("TWILIO_AUTH_TOKEN", "")
        self.twilio_number = os.getenv("TWILIO_WHATSAPP_NUMBER", "whatsapp:+14155238886")
        
        # Validate credentials
        if not self.account_sid or not self.auth_token:
            logger.warning("Twilio credentials not configured - WhatsApp messages will fail")
        
        try:
            self.client = Client(self.account_sid, self.auth_token)
        except Exception as e:
            logger.error(f"Failed to initialize Twilio client: {e}")
            self.client = None
    
    def send_message(
        self,
        to_number: str,
        message: str,
        max_retries: int = 2,
        retry_delay: int = 2
    ) -> Dict[str, str]:
        """
        Send WhatsApp message with retry logic.
        
        Args:
            to_number: Recipient WhatsApp number (format: whatsapp:+91XXXXXXXXXX)
            message: Message body
            max_retries: Maximum number of retry attempts
            retry_delay: Delay in seconds between retries
        
        Returns:
            dict: {
                "sid": message SID,
                "status": "queued|delivered|failed",
                "error": error message if failed
            }
        
        Raises:
            WhatsAppServiceException: If message fails after all retries
        """
        
        if not self.client:
            logger.warning(f"Twilio client not initialized - cannot send to {to_number}")
            return {
                "sid": "N/A",
                "status": "failed",
                "error": "Twilio client not initialized"
            }
        
        attempt = 0
        last_error = None
        
        while attempt < max_retries:
            attempt += 1
            try:
                logger.info(f"Sending WhatsApp message to {to_number} (attempt {attempt}/{max_retries})")
                
                # Send via Twilio
                msg = self.client.messages.create(
                    from_=self.twilio_number,
                    to=to_number,
                    body=message
                )
                
                # Log success
                logger.info(
                    f"WhatsApp message sent successfully | "
                    f"SID: {msg.sid} | Status: {msg.status} | "
                    f"To: {to_number}"
                )
                
                return {
                    "sid": msg.sid,
                    "status": msg.status,
                    "error": None
                }
                
            except TwilioRestException as e:
                last_error = str(e)
                logger.warning(
                    f"Twilio API error (attempt {attempt}/{max_retries}): "
                    f"{e.code} - {e.msg}"
                )
                
                # Don't retry on auth errors
                if e.code in [20003, 20404, 30003]:  # Auth-related errors
                    raise WhatsAppServiceException(
                        f"Twilio auth error: {e.msg}"
                    )
                
                # Retry on other errors
                if attempt < max_retries:
                    logger.info(f"Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                
            except Exception as e:
                last_error = str(e)
                logger.error(f"Unexpected error sending WhatsApp message: {e}")
                
                if attempt < max_retries:
                    logger.info(f"Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
        
        # All retries failed
        error_msg = f"Failed to send WhatsApp message after {max_retries} attempts: {last_error}"
        logger.error(error_msg)
        
        return {
            "sid": "N/A",
            "status": "failed",
            "error": error_msg
        }
    
    def send_underwriting_result(
        self,
        to_number: str,
        merchant_id: str,
        risk_tier: str,
        decision: str,
        risk_score: int,
        explanation: str
    ) -> Dict[str, str]:
        """
        Send formatted underwriting result via WhatsApp.
        
        Args:
            to_number: Recipient WhatsApp number
            merchant_id: Merchant ID
            risk_tier: Risk tier (Tier 1/2/3)
            decision: Decision (APPROVED/APPROVED_WITH_CONDITIONS/REJECTED)
            risk_score: Risk score (0-100)
            explanation: Explanation text
        
        Returns:
            dict: Send result with SID and status
        """
        
        message = format_underwriting_message(
            merchant_id=merchant_id,
            risk_tier=risk_tier,
            decision=decision,
            risk_score=risk_score,
            explanation=explanation
        )
        
        return self.send_message(to_number, message)


def format_underwriting_message(
    merchant_id: str,
    risk_tier: str,
    decision: str,
    risk_score: int,
    explanation: str
) -> str:
    """
    Format underwriting result in professional WhatsApp message style.
    
    Args:
        merchant_id: Merchant ID
        risk_tier: Risk tier classification
        decision: Final decision
        risk_score: Risk score
        explanation: Explanation for decision
    
    Returns:
        str: Formatted message ready for WhatsApp
    """
    
    # Truncate explanation if too long (WhatsApp has message limits)
    max_explanation_len = 300
    if len(explanation) > max_explanation_len:
        explanation = explanation[:max_explanation_len] + "..."
    
    message = f"""📊 GrabCredit Underwriting Result

Merchant ID: {merchant_id}
Risk Tier: {risk_tier}
Decision: {decision}
Risk Score: {risk_score}/100

Explanation:
{explanation}

Thank you for partnering with Grab."""
    
    return message
