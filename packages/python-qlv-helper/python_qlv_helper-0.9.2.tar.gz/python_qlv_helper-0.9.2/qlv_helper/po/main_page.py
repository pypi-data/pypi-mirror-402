# -*- coding: utf-8 -*-
"""
# ---------------------------------------------------------------------------------------------------------
# ProjectName:  qlv-helper
# FileName:     main_page.py
# Description:  首页页面对象
# Author:       ASUS
# CreateDate:   2025/11/25
# Copyright ©2011-2025. Hunan xxxxxxx Company limited. All rights reserved.
# ---------------------------------------------------------------------------------------------------------
"""
from playwright.async_api import Page, Locator
from playwright_helper.libs.base_po import BasePo


class MainPage(BasePo):
    url: str = "/"
    __page: Page

    def __init__(self, page: Page, url: str = "/") -> None:
        super().__init__(page, url)
        self.url = url
        self.__page = page

    async def get_confirm_btn_with_system_notice_dialog(self, timeout: float = 5.0) -> Locator:
        """
        获取系统通知弹框中的确认按钮，注意这个地方，存在多个叠加的弹框，因此用last()方法，只需定位到最上面的那个弹框就行
        :return:
        """
        selector: str = "//div[@class='CommonAlert'][last()]//a[@class='CommonAlertBtnConfirm']"
        return await self.get_locator(selector=selector, timeout=timeout)

    async def get_level1_menu_order_checkout(self, timeout: float = 5.0) -> Locator:
        selector: str = "//span[contains(normalize-space(), '订单出票')]"
        return await self.get_locator(selector=selector, timeout=timeout)

    async def get_level2_menu_order_checkout(self, timeout: float = 5.0) -> Locator:
        selector: str = "//a[@menuname='国内活动订单']"
        return await self.get_locator(selector=selector, timeout=timeout)
