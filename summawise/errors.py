class NotSupportedError(Exception):
    def __init__(self, append: str = ""):
        msg = "Failed to vectorize data. Your input is not yet supported" + (": " if append else ".")
        msg += (": " if append else ".") + append
        super().__init__(msg)
