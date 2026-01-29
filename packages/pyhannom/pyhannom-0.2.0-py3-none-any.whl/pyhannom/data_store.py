# 内部缓存（用户无法直接访问）
_cache = {}

class DataHandle:
    def __init__(self, key):
        self._key = key
    def __repr__(self):
        return f"<DataHandle id={self._key}>"

def store_data(data):
    """存储数据并返回句柄"""
    key = id(data)
    _cache[key] = data
    return DataHandle(key)

def get_data(handle):
    """根据句柄取数据（仅库内部使用）"""
    return _cache.get(handle._key)
