# -*- coding: utf-8 -*-
"""
# ---------------------------------------------------------------------------------------------------------
# ProjectName:  qlv-helper
# FileName:     ocr_helper.py
# Description:  OCR模块
# Author:       ASUS
# CreateDate:   2025/11/25
# Copyright ©2011-2025. Hunan xxxxxxx Company limited. All rights reserved.
# ---------------------------------------------------------------------------------------------------------
"""
import json
import asyncio
import ddddocr
import requests
from typing import Tuple
from aiohttp import ClientSession
from ocr_helper.core.baidu import ImageContentOCR

# 复用 OCR 实例，不用每次都重新加载模型（更快）
_ocr = ddddocr.DdddOcr(show_ad=False)


def fetch_and_ocr_captcha(url: str) -> Tuple[str, bytes]:
    # 1) 请求验证码图片
    resp = requests.get(url, timeout=10)
    img_bytes = resp.content

    # 2) OCR 识别
    result = _ocr.classification(img_bytes)

    return result, img_bytes


async def async_fetch_and_ocr_captcha(url: str) -> Tuple[str, bytes]:
    async with ClientSession() as session:
        async with session.get(url, timeout=10) as resp:
            img_bytes = await resp.read()

    result = _ocr.classification(img_bytes)
    return result, img_bytes


async def get_image_text(image_path: str, captcha_type: int, api_key, secret_key: str) -> str:
    if captcha_type == 0:
        with open(image_path, "rb") as f:
            img_bytes = f.read()
        for _ in range(100):
            text = _ocr.classification(img_bytes).strip()
            if len(text) == 4:
                return text
        raise RuntimeError("ddddocr识别验证码失败")
    else:
        api = ImageContentOCR(api_key=api_key, secret_key=secret_key)
        response = await api.get_access_token(is_end=False)
        if not response.get("access_token"):
            raise RuntimeError(f"获取百度API的认证Token失败，原因：{response}")
        token = response.get("access_token")
        response = await api.submit_request(
            question='图片中的文字是什么，如果含有运算信息，请将运算结果返回。注意给我返回一个json格式数据包，例如：{"content":"xxxx", result: xxx}, 如果无运算信息，设置为空串就行',
            image_path=image_path,
            token=token,
            is_end=False
        )
        task_id: str = response.get("result", dict()).get("task_id")
        if not task_id:
            raise RuntimeError(f"提交图片至百度API接口失败，原因：{response}")
        await asyncio.sleep(delay=10)
        response = await api.get_result(task_id=task_id, token=token, is_end=True)
        if response.get("result").get("ret_code") == 0 and response.get("result").get("ret_msg") == "success":
            description = response.get("result").get("description")
            description = json.loads(description[description.find("{"):description.find("}") + 1])
            if description.get("result"):
                return str(description.get("result")).strip()
            else:
                return description.get("content").strip()
        else:
            raise RuntimeError(f"调用百度API，获取图片识别结果失败，原因{response}")
