class UserMixin:
    def __init__(self):
        self.is_authenticated = False
        self.is_active = True
        self.is_anonymous = False
        self.id = None

    def get_id(self):
        return str(getattr(self, 'id', None)) if self.id is not None else None