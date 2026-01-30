from .models import UserMixin

class LoginManager:
    def __init__(self):
        self.user_callback = None
        self._current_user = None

    def user_loader(self, callback):
        self.user_callback = callback
        return callback

    def login_user(self, user):
        user.is_authenticated = True
        self._current_user = user
        return True

    def logout_user(self):
        if self._current_user:
            self._current_user.is_authenticated = False
        self._current_user = None

    @property
    def current_user(self):
        return self._current_user if self._current_user else AnonymousUser()

class AnonymousUser(UserMixin):
    def __init__(self):
        super().__init__()
        self.is_anonymous = True
        self.is_authenticated = False
        self.is_active = False
        self.id = None