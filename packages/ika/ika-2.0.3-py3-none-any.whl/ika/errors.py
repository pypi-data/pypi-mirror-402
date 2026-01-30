class IKAError(Exception):
    """
    General IKA error
    """

    def __init__(self, msg=None):
        self.msg = msg

    def __str__(self):
        return self.msg
