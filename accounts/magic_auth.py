from django.core.signing import TimestampSigner, BadSignature, SignatureExpired
from django.conf import settings

signer = TimestampSigner()

def generate_token(email):
    """Generate a signed token for the given email."""
    return signer.sign(email)

def verify_token(token, max_age=600):
    """
    Verify the signed token. 
    Returns the email if valid and not expired, otherwise None.
    Default expiry is 10 minutes (600 seconds).
    """
    try:
        return signer.unsign(token, max_age=max_age)
    except (BadSignature, SignatureExpired):
        return None
