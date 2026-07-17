# C8 fix: apps 包缺失 __init__.py 导致 manage.py test 报 0 tests（CI 假阴性）。
# 加上后 Django 的 test runner 才能把 apps.<app>.tests 当成可发现模块。