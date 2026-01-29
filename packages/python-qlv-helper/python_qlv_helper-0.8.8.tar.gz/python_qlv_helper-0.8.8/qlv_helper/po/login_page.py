# -*- coding: utf-8 -*-
"""
# ---------------------------------------------------------------------------------------------------------
# ProjectName:  qlv-helper
# FileName:     login.py
# Description:  登录页
# Author:       ASUS
# CreateDate:   2025/11/25
# Copyright ©2011-2025. Hunan xxxxxxx Company limited. All rights reserved.
# ---------------------------------------------------------------------------------------------------------
"""
from typing import Tuple, Union
from playwright_helper.libs.base_po import BasePo
from playwright.async_api import Page, TimeoutError as PlaywrightTimeoutError, Locator, ElementHandle


class LoginPage(BasePo):
    __page: Page

    def __init__(self, page: Page, url: str = "/Home/Login") -> None:
        super().__init__(page, url)
        self.__page = page

    async def get_login_username_input(self, timeout: float = 5.0) -> Locator:
        """
        获取登录页面的用户名输入框
        :param timeout: 超时时间（秒）
        :return: (是否存在, 错误信息|元素对象)
        """
        selector: str = '//input[@id="UserName"]'
        return await self.get_locator(selector=selector, timeout=timeout)

    async def get_login_password_input(self, timeout: float = 5.0) -> Locator:
        """
        获取登录页面的密码输入框
        :param timeout: 超时时间（秒）
        :return: (是否存在, 错误信息|元素对象)
        """
        selector: str = '//input[@id="Password"]'
        return await self.get_locator(selector=selector, timeout=timeout)

    async def get_captcha(self, timeout: float = 5.0) -> Locator:
        """
        获取验证码Locator对象
        :param timeout: 超时时间（秒）
        :return: (是否存在, 错误信息|元素对象)
        """
        selector: str = 'xpath=//div[@class="form_row"]/img[@onclick="this.src=this.src+\'?\'"]'
        return await self.get_locator(selector=selector, timeout=timeout)

    @staticmethod
    async def get_captcha_type(locator: Locator, timeout: float = 5.0) -> int:
        """
        获取验证码的类型
        :param locator: 验证码Locator对象
        :param timeout: 超时时间（秒）
        :return: (是否存在, 错误信息|元素对象)
        """
        img_src: str = await locator.get_attribute(name="src", timeout=timeout)
        img_src_slice = img_src.split("=")
        return int(img_src_slice[-1][0])

    async def get_captcha_image(self, timeout: float = 5.0) -> ElementHandle:
        selector: str = '//div[@id="signup_forms"]//img'
        locator: Locator = await self.get_locator(selector=selector, timeout=timeout)
        return await locator.element_handle(timeout=timeout * 1000)

    async def get_login_captcha_input(self, timeout: float = 5.0) -> Locator:
        """
        获取登录页面的验证码输入框
        :param timeout: 超时时间（秒）
        :return: (是否存在, 错误信息|元素对象)
        """
        selector: str = '//input[@id="Code"]'
        return await self.get_locator(selector=selector, timeout=timeout)

    async def get_login_btn(self, timeout: float = 5.0) -> Locator:
        """
        获取登录页面的登录按钮
        :param timeout: 超时时间（秒）
        :return: (是否存在, 错误信息|元素对象)
        """
        selector: str = '//input[@class="login-btn"]'
        return await self.get_locator(selector=selector, timeout=timeout)

    async def get_wechat_entrance(self, timeout: float = 5.0) -> Tuple[bool, Union[Locator, str]]:
        selector: str = '//img[@src="/images/weixin.png"]'
        try:
            locator = self.__page.locator(selector)
            if locator:
                await locator.wait_for(state='visible', timeout=timeout * 1000)
                return True, locator
            else:
                return False, '没有找到登录页面中的【微信】快捷登录入口'
        except PlaywrightTimeoutError:
            return False, f"元素 '{selector}' 未在 {timeout} 秒内找到"
        except Exception as e:
            return False, f"检查元素时发生错误: {str(e)}"
