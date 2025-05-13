import africastalking
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class SMSService:
    @staticmethod
    def initialize():
        if not all([settings.AFRICASTALKING_USERNAME, settings.AFRICASTALKING_API_KEY]):
            raise ValueError("Africa's Talking credentials not configured")
        
        africastalking.initialize(
            settings.AFRICASTALKING_USERNAME,
            settings.AFRICASTALKING_API_KEY
        )
        return africastalking.SMS

    @staticmethod
    def send(phone_number, message):
        if not settings.ENABLE_SMS:
            logger.info(f"[SMS MOCK] To: {phone_number} - Message: {message}")
            return {"status": "mock_success"}
            
        try:
            sms = SMSService.initialize()
            response = sms.send(message, [phone_number])
            logger.info(f"SMS sent to {phone_number} - Cost: {response.get('SMSMessageData', {}).get('TotalAmount')}")
            return response
        except Exception as e:
            logger.error(f"SMS failed to {phone_number}: {str(e)}")
            return {"status": "failed", "error": str(e)}