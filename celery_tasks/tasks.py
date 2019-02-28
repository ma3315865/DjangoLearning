from celery import Celery
from django.core.mail import send_mail
from dailyfresh import settings

# worker端需复制项目，并打开下面的注释
# import os
# import django
# os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dailyfresh.settings')
# django.setup()

# redis
# BROKER_IP_PORT_NUM = "127.0.0.1:6379/数据库index"

BROKER_IP_PORT_NUM = settings.BROKER_IP_PORT_NUM
cel = Celery("celery_tasks.tasks", broker="redis://%s" % BROKER_IP_PORT_NUM)


@cel.task
def send_email_celery(email, token):
    subject = "这里是正题"
    message = "邮箱注册链接"
    from_email = settings.EMAIL_FROM
    html_message = "<h1>点击下方链接注册</h1><br/>" \
                   "<a href='http://127.0.0.1:8000/user/active/%s'>" \
                   "http://127.0.0.1:8000/user/active/%s<a>" % (token, token)
    recipient_list = [email]

    send_mail(
        subject,
        message,
        from_email,
        recipient_list,
        html_message=html_message)