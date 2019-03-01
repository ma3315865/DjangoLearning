from celery import Celery
from django.core.mail import send_mail

# worker端需复制项目，并打开下面的注释
import os
# import django
# os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dailyfresh.settings')
# django.setup()

from dailyfresh import settings

from apps.goods.models import GoodsType, \
    IndexGoodsBanner as IGB, \
    IndexPromotionBanner as IPB, \
    IndexTypeGoodsBanner as ITGB
from django.template import loader


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


@cel.task
def generate_static_index_html():
    types = GoodsType.objects.all()
    goods_banners = IGB.objects.all().order_by("index")
    promotion_banners = IPB.objects.all().order_by("index")

    for ty in types:
        image_itgb = ITGB.objects.filter(type=ty, display_type=1).order_by("index")
        title_itgb = ITGB.objects.filter(type=ty, display_type=0).order_by("index")
        # 可以给类动态添加类属性
        ty.images = image_itgb
        ty.titles = title_itgb

    context = {"types": types,
               "goods_banners": goods_banners,
               "promotion_banners": promotion_banners}

    temp = loader.get_template("index_static.html")
    static_index_html = temp.render(context)

    static_index_html_path = os.path.join(settings.BASE_DIR, "static/index.html")
    with open(static_index_html_path, "w") as f:
        f.write(static_index_html)