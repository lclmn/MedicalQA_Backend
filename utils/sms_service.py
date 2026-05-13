# -*- coding: utf-8 -*-
import random
from utils.logger import logger

# ===================== Mock 模拟短信服务 =====================
class AliyunSmsService:
    def __init__(self):
        logger.info("模拟短信服务初始化成功（本地测试模式）")

    # 生成6位验证码
    def generate_verification_code(self, length=6):
        return "".join(random.choices("0123456789", k=length))

    # 模拟发送验证码（不真发短信）
    def send_verify_code(self, phone: str, code: str):
        try:
            logger.info(f"模拟发送验证码 → {phone}，验证码：{code}")
            return True, "发送成功"
        except Exception as e:
            logger.error(f"发送失败：{str(e)}")
            return False, str(e)

# 对外提供实例（你原来的代码完全不用改）
sms_service = AliyunSmsService()