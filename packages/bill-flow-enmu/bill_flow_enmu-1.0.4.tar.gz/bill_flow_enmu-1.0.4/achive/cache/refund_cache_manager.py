import logging
import os
import json

CACHE_FILE = "orders_map.json"

class OrderCache:
    def __init__(self):
        self.data = self._load()

    def _load(self):
        if os.path.exists(CACHE_FILE):
            try:
                with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logging.error(f"读取文件出错: {e}")
                return {}
        return {}

    def save_order(self, order_id, account):
        # 1. 检查输入
        if not order_id or not account:
            logging.error("save_order 被调用，但参数为空")
            return

        # 2. 更新内存
        self.data[order_id] = account

        # 3. 写入文件
        try:
            with open(CACHE_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
                f.flush() # 强制刷新缓冲区
                os.fsync(f.fileno()) # 强制写入硬盘
            logging.info(f"成功写入: {order_id} -> {account}")
        except Exception as e:
            logging.error(f"写入文件失败: {e}")

    def get_account(self, order_id):
        with open(CACHE_FILE, 'r', encoding='utf-8') as f:
            orders = json.load(f)
            account = orders.get(order_id)
            if not account:
                return None
            return account

# 确保只实例化一次
order_cache = OrderCache()
