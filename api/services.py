import africastalking
from django.conf import settings

def initialize_sms():
    africastalking.initialize(
        username=settings.AFRICASTALKING_USERNAME,
        api_key=settings.AFRICASTALKING_API_KEY
    )
    return africastalking.SMS

def send_sms_notification(phone_number, message):
    sms = initialize_sms()
    try:
        response = sms.send(message, [phone_number])
        return response
    except Exception as e:
        print(f"SMS failed to send: {e}")
        raise