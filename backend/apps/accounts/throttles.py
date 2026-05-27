from rest_framework.throttling import SimpleRateThrottle


class SendCodeRateThrottle(SimpleRateThrottle):
    scope = 'send_code'

    def get_cache_key(self, request, view):
        email = request.data.get('email', '')
        if email:
            return f'send_code_{email}'
        return self.get_ident(request)


class LoginRateThrottle(SimpleRateThrottle):
    scope = 'login'

    def get_cache_key(self, request, view):
        return self.get_ident(request)
