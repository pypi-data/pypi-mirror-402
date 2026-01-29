import re


def is_mostly_chinese(text, threshold=0.5):
    if not text:
        return False
    chinese_chars = re.findall(r"[\u4e00-\u9fff]", text)
    chinese_count = len(chinese_chars)
    return (chinese_count / len(text)) > threshold and len(text) >= 20


def is_mostly_pinduoduo(text):
    if not text:
        return False
    match = re.search(r"^商户单号XP", text)
    if match:
        return True
    return False


def is_mostly_meituan(text):
    if not text:
        return False
    match = re.search("^美团订单", text)
    if match:
        return True
    return False
