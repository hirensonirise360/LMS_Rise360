from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model

class CaseInsensitiveEmailBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        UserModel = get_user_model()
        if username is None:
            username = kwargs.get(UserModel.USERNAME_FIELD) or kwargs.get("email")
        if not username or not password:
            return None
        
        email_clean = str(username).strip()
        user = UserModel.objects.filter(email__iexact=email_clean).first()
        if not user:
            user = UserModel.objects.filter(username__iexact=email_clean).first()
            
        if user and user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None
