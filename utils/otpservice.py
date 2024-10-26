from .service import AuthService
from datetime import datetime, timedelta
import logging
from models import OtpVerification
from db import db

logger = logging.getLogger(__name__)

def handle_otp(phone_number):
    try:
        current_time = datetime.now()
        logger.info(f"Processing OTP for phone number: {phone_number}")

        # Check for existing OTP
        otp_verification = OtpVerification.query.filter_by(phone_number=phone_number).first()
        logger.info(f"OTP verification record: {otp_verification}")

        # Generate a new OTP
        otp = AuthService.generate_4_digit_code()
        logger.info(f"Generated OTP: {otp}")

        if otp_verification:
            # If OTP is expired, send a new OTP
            if otp_verification.expires_at < current_time:
                otp_verification.otp = otp
                otp_verification.sent_at = current_time
                otp_verification.expires_at = current_time + timedelta(minutes=2)
                logger.info(f"OTP expired. New OTP generated and sent: {otp}")
            else:
                # OTP is still valid, return the existing one
                logger.info(f"OTP is still valid. Returning existing OTP: {otp_verification.otp}")
                return otp_verification.otp
        else:
            # No OTP entry exists, create a new one
            otp_verification = OtpVerification(
                phone_number=phone_number,
                otp=otp,
                sent_at=current_time,
                expires_at=current_time + timedelta(minutes=2)
            )
            db.session.add(otp_verification)
            logger.info(f"New OTP entry created for phone number: {phone_number}, OTP: {otp}")

        # Save the OTP to the database
        db.session.commit()
        logger.info("OTP successfully committed to the database.")
        
        return otp

    except Exception as e:
        logger.error(f"An error occurred while handling OTP: {str(e)}", exc_info=True)
        raise e

    finally:
        db.session.close()
        logger.info("Database session closed after OTP handling.")
