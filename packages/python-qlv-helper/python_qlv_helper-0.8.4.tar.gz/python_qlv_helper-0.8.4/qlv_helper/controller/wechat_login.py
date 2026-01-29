# -*- coding: utf-8 -*-
"""
# ---------------------------------------------------------------------------------------------------------
# ProjectName:  qlv-helper
# FileName:     wechat_login.py
# Description:  微信登录模块
# Author:       ASUS
# CreateDate:   2025/12/31
# Copyright ©2011-2025. Hunan xxxxxxx Company limited. All rights reserved.
# ---------------------------------------------------------------------------------------------------------
"""
from typing import Tuple
from qlv_helper.po.login_page import LoginPage
from playwright.async_api import BrowserContext

from qlv_helper.utils.po_utils import on_click_locator
from qlv_helper.po.wechat_auth_page import WechatAuthPage
from qlv_helper.utils.browser_utils import switch_for_table_window


async def _wechat_login(browser: BrowserContext, login_po: LoginPage, timeout: float = 5.0) -> Tuple[bool, str]:
    # 1. 点击微信登录快捷入口
    is_success, wechat_entrance = await login_po.get_wechat_entrance(timeout=timeout)
    if is_success is False:
        return is_success, wechat_entrance
    await on_click_locator(locator=wechat_entrance)

    page_new = await switch_for_table_window(browser=browser, url_keyword="open.weixin.qq.com", wait_time=int(timeout))
    wachat_po = WechatAuthPage(page=page_new)

    # 2. 点击【微信快捷登录】按钮
    is_success, wechat_quick_login_btn = await wachat_po.get_wechat_quick_login_btn(timeout=timeout)
    if is_success is False:
        return is_success, wechat_quick_login_btn
    await on_click_locator(locator=wechat_quick_login_btn)

    # 3. 点击微信弹框的中【允许】按钮
    return await wachat_po.on_click_allow_btn(timeout=int(timeout) * 3)


async def wechat_login(
        *, browser: BrowserContext, login_po: LoginPage, timeout: float = 5.0, retry: int = 3
) -> Tuple[bool, str]:
    for index in range(1, retry + 1):
        # 全流程的登录
        is_success, message = await _wechat_login(browser=browser, login_po=login_po, timeout=timeout)

        # 判断是否为当前页
        if is_success is True or index == retry:
            return is_success, message
