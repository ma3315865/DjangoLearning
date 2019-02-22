import re
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from itsdangerous import SignatureExpired

from django.shortcuts import render, redirect
from django.urls import reverse
from django.views import View
from django.core.mail import send_mail

from apps.user.models import User
from dailyfresh import settings

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
            r"^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$",
                email):
            return render(request, "register.html", {"error_msg": "邮箱格式不正确"})

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            user = None
        if user:
            return render(request, "register.html", {"error_msg": "用户名已存在"})

        user = User.objects.create_user(
            username, email=email, password=password)
        user.is_active = False
        user.save()

        ser = Serializer(settings.SECRET_KEY, 3600)
        info = {"user_id": user.id}
        token = ser.dumps(info).decode("utf8")

        subject = "这里是正题"
        message = "邮箱注册链接"
        html_message = "<h1>点击下方链接注册</h1><br/>" \
            "<a href='http://127.0.0.1:8000/user/active/%s'>" \
            "http://127.0.0.1:8000/user/active/%s<a>" % (token, token)
        from_email = settings.EMAIL_FROM
        recipient_list = [email]
        send_mail(
            subject,
            message,
            from_email,
            recipient_list,
            html_message=html_message)

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
        return render(request, "login.html")
