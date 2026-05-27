import threading


def send_mail_async(subject, message, recipient_list, **kwargs):
    def _send():
        from django.db import connection
        # Close inherited parent connection before doing anything in this thread
        if connection.connection:
            connection.close()
        try:
            from django.core.mail import send_mail
            send_mail(
                subject=subject,
                message=message,
                from_email=None,
                recipient_list=recipient_list,
                fail_silently=True,
                **kwargs,
            )
        finally:
            # Close the connection we may have opened during email sending
            connection.close()

    t = threading.Thread(target=_send, daemon=True)
    t.start()
