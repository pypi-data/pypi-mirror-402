# -*- coding: utf-8 -*-
"""
# ---------------------------------------------------------------------------------------------------------
# ProjectName:  qlv-helper
# FileName:     user_login.py
# Description:  用户登录页面控制器
# Author:       ASUS
# CreateDate:   2025/11/25
# Copyright ©2011-2025. Hunan xxxxxxx Company limited. All rights reserved.
# ---------------------------------------------------------------------------------------------------------
"""
import os
import asyncio
import traceback
from logging import Logger
from datetime import datetime
from typing import Dict, Any, Optional
from qlv_helper.po.login_page import LoginPage
import qlv_helper.config.url_const as url_const
from playwright.async_api import Page, ElementHandle
from qlv_helper.utils.ocr_helper import get_image_text

async def _username_login(
        *, login_po: LoginPage, logger: Logger, username: str, password: str, screenshot_dir: str, api_key: str,
        secret_key: str, timeout: float = 5.0, attempt: int = 10
) -> Optional[Dict[str, Any]]:
    for index in range(1, attempt + 1):
        try:
            # 1. 输入用户名
            username_input = await login_po.get_login_username_input(timeout=timeout)
            await username_input.fill(value=username)
            logger.info(f"登录页面，用户名<{username}>输入完成")
        except (Exception,):
            pass
        try:
            # 2. 输入密码
            password_input = await login_po.get_login_password_input(timeout=timeout)
            await password_input.fill(value=password)
            logger.info(f"登录页面，用户密码<{password}>输入完成")
        except (Exception,):
            pass
        try:
            # 3. 首次获取验证码，并点击
            # captcha_1 = await login_po.get_captcha(timeout=timeout)
            # await captcha_1.click(button="left")
            # await asyncio.sleep(delay=3)

            # 4. 再次获取验证码
            captcha_2 = await login_po.get_captcha(timeout=timeout)
            # 4.1 获取验证码类型
            captcha_type: int = await login_po.get_captcha_type(locator=captcha_2, timeout=timeout)
            logger.info(f"登录页面，验证码类型<{captcha_type}>获取成功")
            # 4.2 获取验证码图片，直接截图获取原始图片字节，不刷新图片
            image: ElementHandle = await login_po.get_captcha_image(timeout=timeout)
            dt_str: str = datetime.now().strftime("%Y%m%d%H%M%S")
            fn: str = os.path.join(screenshot_dir, f"captcha_{username}_{captcha_type}_{dt_str}.png")
            await image.screenshot(path=fn, timeout=timeout * 1000)
            logger.info(f"登录页面，验证码图片已经生成，图片路径：{fn}")
            # 4.3 获取验证码内容
            capthcha_text = await get_image_text(
                image_path=fn, captcha_type=captcha_type, api_key=api_key, secret_key=secret_key
            )
            logger.info(f"登录页面，验证码内容：<{capthcha_text}>识别成功")

            # 5. 获取验证码输入框
            captcha_input = await login_po.get_login_captcha_input(timeout=timeout)
            await captcha_input.fill(value=capthcha_text)
            logger.info(f"登录页面，验证码<{capthcha_text}>输入完成")

            # 6. 点击登录
            login_btn = await login_po.get_login_btn(timeout=timeout)
            await login_btn.click(button="left")
            logger.info(f"登录页面，【登录】按钮点击完成")
            await asyncio.sleep(delay=3)

            # 7. 验证登录是否成功
            result = login_po.is_current_page()
            if result is False:
                logger.info(f"用户<{username}>登录成功，登录流程结束")

                # 9. 获取当前cookie，不指定 path，Playwright 会返回 JSON 字符串
                return await login_po.get_page().context.storage_state()
            else:
                raise RuntimeError("登录失败")
        except (RuntimeError,):
            if index == attempt:
                logger.error(f"尝试登录<{attempt}>次，均失败，登录结束")
            else:
                logger.error(f"第<{index}>次登录失败，等待下一次登录")
        except (Exception,):
            logger.error(traceback.format_exc())
            if index == attempt:
                logger.error(f"尝试登录<{attempt}>次，均失败，登录结束")
            else:
                logger.error(f"第<{index}>次登录失败，等待下一次登录")


async def open_login_page(
        *, page: Page, logger: Logger, qlv_protocol: str, qlv_domain: str, timeout: float = 60.0
) -> LoginPage:
    url_prefix = f"{qlv_protocol}://{qlv_domain}"
    login_url = url_prefix + url_const.login_url
    await page.goto(login_url)

    login_po = LoginPage(page=page, url=login_url)
    await login_po.url_wait_for(url=login_url, timeout=timeout)
    logger.info(f"即将进入登录页，页面URL<{login_url}>")
    return login_po


async def username_login(
        *, page: Page, logger: Logger, qlv_protocol: str, qlv_domain: str, username: str, screenshot_dir: str,
        password: str, api_key: str, secret_key: str, timeout: float = 60.0, attempt: int = 10, **kwargs: Any
) -> Dict[str, Any]:
    # 1. 打开登录页面
    login_po = await open_login_page(
        page=page, logger=logger, qlv_domain=qlv_domain, qlv_protocol=qlv_protocol, timeout=timeout
    )
    # 2. 一次全流程的登录
    return await _username_login(
        login_po=login_po, logger=logger, username=username, password=password, screenshot_dir=screenshot_dir,
        timeout=timeout, api_key=api_key, secret_key=secret_key, attempt=attempt
    )
