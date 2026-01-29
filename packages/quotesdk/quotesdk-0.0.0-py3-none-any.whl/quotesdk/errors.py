class QuoteSDKError(Exception):
    pass

class APIError(QuoteSDKError):
    pass

__all__ = ['QuoteSDKError', 'APIError']