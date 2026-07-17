import hashlib

from rest_framework.throttling import SimpleRateThrottle


def _norm_email(raw):
    """稳定化 email：strip + casefold，作为 throttle key 的输入。"""
    return (raw or '').strip().casefold()


class SendCodeRateThrottle(SimpleRateThrottle):
    """对 /send-code/、/send-reset-code/ 端点限流。key 用 email 而非 IP，
    以阻止从不同 IP 同时挤兑某个邮箱的发送频次。"""
    scope = 'send_code'

    def get_cache_key(self, request, view):
        email = _norm_email(request.data.get('email', ''))
        if email:
            return f'send_code_{email}'
        return self.get_ident(request)


class LoginRateThrottle(SimpleRateThrottle):
    """H3 fix: 用 (ip, email) 双维度 key，防御 NAT 共享 LAN 同时多用户锁死、
    以及单个 IP 被 botnet 用来枚举多封号。
    """
    scope = 'login'

    def get_cache_key(self, request, view):
        ip = self.get_ident(request)
        # login body 一般含 {email, password}
        email = _norm_email(request.data.get('email') or '')
        if email:
            digest = hashlib.sha256(email.encode('utf-8')).hexdigest()[:16]
            return f'login_{ip}_{digest}'
        return f'login_{ip}'


class ChangePasswordRateThrottle(SimpleRateThrottle):
    """对 change_password 端点限流（认证用户）。"""
    scope = 'change_password'

    def get_cache_key(self, request, view):
        if request.user and request.user.is_authenticated:
            return self.get_ident(request) + ':' + str(request.user.pk)
        return self.get_ident(request)


class VerifyCodeRateThrottle(SimpleRateThrottle):
    """对 /register/、/reset-password/ 等消费验证码的端点限流。

    key = (email, IP) 双维度 —— 仅 IP 容易被 botnet 绕过；仅 email 会被
    attacker 用同 IP 打多个邮箱。hex 截断避免 key 过长。
    """
    scope = 'verify_code'

    def get_cache_key(self, request, view):
        email = _norm_email(request.data.get('email', ''))
        ip = self.get_ident(request)
        if not email:
            # 缺 email 时退化为纯 IP key
            return f'verify_ip_{ip}'
        digest = hashlib.sha256(email.encode('utf-8')).hexdigest()[:16]
        return f'verify_{digest}_{ip}'


class SendResetCodeRateThrottle(SimpleRateThrottle):
    """与 SendCodeRateThrottle 共用 key 算法但独立 scope，
    防止 register / reset 互相挤兑同一用户的 throttle 配额。"""
    scope = 'send_reset_code'

    def get_cache_key(self, request, view):
        email = _norm_email(request.data.get('email', ''))
        if email:
            return f'send_reset_code_{email}'
        return self.get_ident(request)


class SendCodeDailyCap(SimpleRateThrottle):
    """H19 fix: 防止 attacker 借 throttle 1/min 的间隙一日发 1440 封邮件。
    与 SendCodeRateThrottle / SendResetCodeRateThrottle 串联，单一邮箱上限 20/天。
    """
    scope = 'send_code_day'

    def get_cache_key(self, request, view):
        email = _norm_email(request.data.get('email', ''))
        if email:
            return f'send_code_day_{email}'
        return self.get_ident(request)


class RefreshRateThrottle(SimpleRateThrottle):
    """M4 fix: 限制 /refresh/ 端的暴力 / 滥用调用。
    Key 仅用 IP —— refresh 端点没有 email 输入，没法做 email+IP 双维度。"""
    scope = 'refresh'

    def get_cache_key(self, request, view):
        return self.get_ident(request)


class UserDefaultRateThrottle(SimpleRateThrottle):
    """M14 fix: 已认证用户的全局 throttle。
    注意：这是全局兜底；具体 endpoint 仍可以用自己的 throttle_classes 收紧。"""
    scope = 'user'

    def get_cache_key(self, request, view):
        if request.user and request.user.is_authenticated:
            return str(request.user.pk)
        return self.get_ident(request)
