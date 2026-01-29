# -*- coding: utf-8 -*-
"""
# ---------------------------------------------------------------------------------------------------------
# ProjectName:  qlv-helper
# FileName:     main_page.py
# Description:  首页控制器
# Author:       ASUS
# CreateDate:   2025/11/29
# Copyright ©2011-2025. Hunan xxxxxxx Company limited. All rights reserved.
# ---------------------------------------------------------------------------------------------------------
"""
import aiohttp
from logging import Logger
from playwright.async_api import Page
from typing import Dict, Any, Optional
from qlv_helper.po.main_page import MainPage
from qlv_helper.http.main_page import get_main_page_html, parser_head_title


async def open_main_page(
        *, page: Page, logger: Logger, qlv_protocol: str, qlv_domain: str, timeout: float = 60.0, **kwargs: Any
) -> MainPage:
    url_prefix = f"{qlv_protocol}://{qlv_domain}"
    main_url = url_prefix + "/"
    await page.goto(main_url)

    main_po = MainPage(page=page, url=main_url)
    await main_po.url_wait_for(url=main_url, timeout=timeout)
    logger.info(f"即将进入首页，页面URL<{main_url}>")
    return main_po


async def get_main_info_with_http(
        domain: str, protocol: str = "http", retry: int = 1, timeout: int = 5, enable_log: bool = True,
        cookie_jar: Optional[aiohttp.CookieJar] = None, playwright_state: Dict[str, Any] = None, **kwargs: Any
) -> Dict[str, Any]:
    response = await get_main_page_html(
        domain=domain, protocol=protocol, retry=retry, timeout=timeout, enable_log=enable_log,
        cookie_jar=cookie_jar, playwright_state=playwright_state
    )
    if response.get("code") != 200:
        return response

    html = response.get("data")
    response["message"] = parser_head_title(html=html)
    return response
