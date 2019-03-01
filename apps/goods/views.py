from django.shortcuts import render
from django.views import View

from apps.goods.models import GoodsType, \
    IndexGoodsBanner as IGB, \
    IndexPromotionBanner as IPB, \
    IndexTypeGoodsBanner as ITGB

from django_redis import get_redis_connection

# Create your views here.


class IndexView(View):
    def get(self, request):
        types = GoodsType.objects.all()
        goods_banners = IGB.objects.all().order_by("index")
        promotion_banners = IPB.objects.all().order_by("index")

        for ty in types:
            image_itgb = ITGB.objects.filter(type=ty, display_type=1).order_by("index")
            title_itgb = ITGB.objects.filter(type=ty, display_type=0).order_by("index")
            # 可以给类动态添加类属性
            ty.images = image_itgb
            ty.titles = title_itgb

        user = request.user
        car_count = 0
        if user.is_authenticated:
            conn = get_redis_connection("default")
            car_key = "car_%d" % user.id
            car_count = conn.hlen(car_key)
        return render(request, "index.html", {"types": types,
                                              "goods_banners": goods_banners,
                                              "promotion_banners": promotion_banners,
                                              "car_count": car_count})