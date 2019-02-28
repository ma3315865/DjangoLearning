# DjangoLearning

# 启动
# 本机启动mysql redis:
net start mysql
redis-server
# F:\redis\dailyfresh中启动celery的tasks
cd /d F:\redis\dailyfresh
celery -A celery_tasks.tasks -l info