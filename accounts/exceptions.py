class AccessNotGrantedError(Exception):
    """
    Wird geworfen wenn ein eingeloggter User technisch authentifiziert ist,
    aber sein Konto noch nicht vollständig eingerichtet wurde.
    """
    REASON_NO_PERSON = 'no_person'
    REASON_NO_PERSONNEL = 'no_personnel'
    REASON_NO_STUDENT = 'no_student'

    def __init__(self, reason):
        self.reason = reason
        super().__init__(reason)
