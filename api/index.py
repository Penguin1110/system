# api/index.py
# 目的：Vercel 的入口點（ASGI），把你的 app 暴露出來

import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))  # 讓它找得到根目錄的模組

from main import app  # main.py 裡面要有 app = FastAPI()
# 如果你原本 main.py 把路由都掛在 app 上，這裡不用再做什麼
