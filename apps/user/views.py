import re
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from itsdangerous import SignatureExpired

from django.shortcuts import render, redirect
from django.urls import reverse
from django.views import View
from django.contrib.auth import authenticate, login, logout
# from django.core.mail import send_mail

from apps.user.models import User, Address
from apps.goods.models import GoodsSKU
from celery_tasks.tasks import send_email_celery
from dailyfresh import settings
from utils.mixin import LoginRequiredMixin
from django_redis import get_redis_connection

# Create your views here.


# /user/register
class RegisterView(View):
    def get(self, request):
        return render(request, "register.html")

    def post(self, request):
        username = request.POST.get("user_name")
        password = request.POST.get("pwd")
        cpassword = request.POST.get("cpwd")
        email = request.POST.get("email")
        allow = request.POST.get("allow")

        if not all([username, password, email]):
            return render(request, "register.html", {"error_msg": "数据不完整"})

        if allow != "on":
            return render(
                request, "register.html", {
                    "error_msg": "同意协议才可以完成注册"})

        if not (password == cpassword):
            return render(request, "register.html", {"error_msg": "两次输入密码不同"})

        if not re.match(
                r"^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$", email):
            return render(request, "register.html", {"error_msg": "邮箱格式不正确"})

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            user = None
        if user:
            return render(request, "register.html", {"error_msg": "用户名已存在"})

        # 创建用户
        user = User.objects.create_user(
            username, email=email, password=password)
        user.is_active = False
        user.save()

        # 给用户info加密token
        ser = Serializer(settings.SECRET_KEY, 3600)
        info = {"user_id": user.id}
        token = ser.dumps(info).decode("utf8")

        # 异步发送邮件
        send_email_celery.delay(email, token)

        # subject = "这里是正题"
        # message = "邮箱注册链接"
        # from_email = settings.EMAIL_FROM
        # html_message = "<h1>点击下方链接注册</h1><br/>" \
        #                "<a href='http://127.0.0.1:8000/user/active/%s'>" \
        #                "http://127.0.0.1:8000/user/active/%s<a>" % (token, token)
        # recipient_list = [email]

        # send_mail(
        #     subject,
        #     message,
        #     from_email,
        #     recipient_list,
        #     html_message=html_message)

        return redirect(reverse("goods:index"))


# user/active/token
class ActiveView(View):
    def get(self, request, token):
        ser = Serializer(settings.SECRET_KEY, 3600)
        try:
            user_id = ser.loads(token)["user_id"]
            user = User.objects.get(id=user_id)
            user.is_active = True
            user.save()
            return redirect(reverse("user:login"))
        except SignatureExpired:
            return render(request, "register.html", {"error_msg": "验证已过期"})


# user/login
class LoginView(View):
    def get(self, request):
        if "username" in request.COOKIES:
            username = request.COOKIES["username"]
            checked = "checked"
        else:
            username = ""
            checked = ""
        return render(
            request, "login.html", {
                "username": username, "checked": checked})

    def post(self, request):
        username = request.POST.get("username")
        password = request.POST.get("pwd")
        user = authenticate(request, username=username, password=password)
        if user is not None:
            if user.is_active:
                login(request, user)
                # 如果url里有next，则返回一个值，为反向解析的地址
                next_url = request.GET.get("next", reverse("goods:index"))
                response = redirect(next_url)
                if request.POST.get("remember") == "on":
                    response.set_cookie(
                        "username", username, max_age=7 * 24 * 3600)
                else:
                    response.delete_cookie("username")
                return response
            else:
                return render(request, "login.html", {"error_msg": "用户未激活"})
        else:
            return render(request, "login.html", {"error_msg": "用户名或密码不正确"})


# user/logout
class LogoutView(View):
    def get(self, request):
        logout(request)
        return redirect(reverse("goods:index"))


# user/user
class UserInfoView(LoginRequiredMixin, View):
    def get(self, request):
        user = request.user
        address = Address.objects.get_default_address(user)

        history_key = "history_%d" % user.id
        con = get_redis_connection("default")
        sku_ids = con.lrange(history_key, 0, 4)
        goods_list = list()
        for sku_id in sku_ids:
            temp = GoodsSKU.objects.get(id=sku_id)
            goods_list.append(temp)

        return render(request, "user_center_info.html", {"page": "user",
                                                         "user": user,
                                                         "address": address,
                                                         "goods_list": goods_list})


# user/order
class UserOrderView(LoginRequiredMixin, View):
    def get(self, request):
        return render(request, "user_center_order.html", {"page": "order"})


# user/address
class UserAddressView(LoginRequiredMixin, View):
    def get(self, request):
        user = request.user
        address = Address.objects.get_default_address(user)
        return render(request, "user_center_site.html", {"page": "address",
                                                         "address": address})

    def post(self, request):
        receiver = request.POST.get("receiver")
        addr = request.POST.get("address")
        zip_code = request.POST.get("zip_code")
        phone = request.POST.get("phone")

        if not all([receiver, addr, phone]):
            return render(request, "user_center_site.html", {"error_msg": "信息输入不完整"})

        if not re.match(r'^1[3|4|5|7|8][0-9]{9}$', phone):
            return render(request, "user_center_site.html", {"error_msg": "手机号错误"})

        user = request.user
        address = Address.objects.get_default_address(user)
        if address:
            is_default = False
        else:
            is_default = True

        Address.objects.create(user=user,
                               receiver=receiver,
                               addr=addr,
                               zip_code=zip_code,
                               phone=phone,
                               is_default=is_default)
        return redirect(reverse("user:address"))