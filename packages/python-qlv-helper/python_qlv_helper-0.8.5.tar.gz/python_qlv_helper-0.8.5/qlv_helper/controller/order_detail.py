# -*- coding: utf-8 -*-
"""
# ---------------------------------------------------------------------------------------------------------
# ProjectName:  qlv-helper
# FileName:     order_detail.py
# Description:  订单详情页面控制器
# Author:       ASUS
# CreateDate:   2025/11/29
# Copyright ©2011-2025. Hunan xxxxxxx Company limited. All rights reserved.
# ---------------------------------------------------------------------------------------------------------
"""
import aiohttp
import asyncio
from logging import Logger
from datetime import datetime
from typing import Dict, Any, List, Optional
import qlv_helper.config.url_const as url_const
from qlv_helper.po.order_detail_page import OrderDetailPage
from flight_helper.models.dto.procurement import FillProcurementInputDTO
from flight_helper.utils.exception_utils import RelationOrderConflictError
from qlv_helper.http.order_page import parser_order_info, get_order_page_html, parser_order_flight_table, \
    fill_procurement_dto_with_http
from playwright.async_api import Page, Locator, Error as PlaywrightError, TimeoutError as PlaywrightTimeoutError


async def get_order_info_with_http(
        *, order_id: int, domain: str, protocol: str = "http", retry: int = 1, timeout: int = 5,
        enable_log: bool = True, cookie_jar: Optional[aiohttp.CookieJar] = None, playwright_state: Dict[str, Any] = None
) -> Dict[str, Any]:
    response = await get_order_page_html(
        order_id=order_id, domain=domain, protocol=protocol, retry=retry, timeout=timeout, enable_log=enable_log,
        cookie_jar=cookie_jar, playwright_state=playwright_state
    )
    if response.get("code") != 200:
        return response

    html = response.get("data")
    order_info = parser_order_info(html=html)
    flight_info = parser_order_flight_table(html=html)
    if flight_info:
        order_info["flights"] = flight_info
        order_info["peoples"] = flight_info
    response["data"] = order_info
    return response


async def open_order_detail_page(
        *, page: Page, logger: Logger, protocol: str, domain: str, order_id: int, timeout: float = 20.0
) -> OrderDetailPage:
    url_prefix = f"{protocol}://{domain}"
    current_dtstr: str = datetime.now().strftime("%Y%m%d%H%M%S")
    order_detail_url_suffix = url_const.order_detail_url.format(order_id, current_dtstr)
    order_detail_url = url_prefix + order_detail_url_suffix
    await page.goto(order_detail_url)

    order_detail_po = OrderDetailPage(page=page, url=order_detail_url)
    await order_detail_po.url_wait_for(url=order_detail_url, timeout=timeout)
    logger.info(f"即将劲旅订单详情页面，页面URL<{order_detail_url}>")

    try:
        message: str = await order_detail_po.get_message_content(timeout=1)
        if "关联订单" in message:
            raise RelationOrderConflictError(message)
        confirm_btn = await order_detail_po.get_message_notice_dialog_confirm_btn(timeout=1)
        await confirm_btn.click(button="left")
        logger.info("订单详情页面，消息提醒弹框，【确认】按钮点击完成")
    except (RelationOrderConflictError,):
        raise
    except (PlaywrightTimeoutError, PlaywrightError, RuntimeError, Exception):
        pass
    return order_detail_po


async def add_custom_remark(*, logger: Logger, page: OrderDetailPage, remark: str, timeout: float = 5.0) -> None:
    # 1. 添加自定义备注
    custom_remark_input = await page.get_custom_remark_input(timeout=timeout)
    await custom_remark_input.fill(value=remark)
    logger.info(f"订单详情页面，日志记录栏，自定义备注：{remark}，输入完成")

    # 2. 点击【保存备注】按钮
    custom_remark_save_btn = await page.get_custom_remark_save_btn(timeout=timeout)
    await custom_remark_save_btn.click(button="left")
    logger.info(f"订单详情页面，日志记录栏，【保存备注】按钮点击完成")


async def update_order_policy(
        *, page: OrderDetailPage, logger: Logger, policy: str, order_id: int, timeout: float = 5.0
) -> None:
    # 1. 修改政策代码
    policy_input = await page.get_policy_input(timeout=timeout)
    await policy_input.fill(value=policy)

    # 2. 执行回车按键
    await policy_input.press("Enter")
    logger.info(f"订单<{order_id}>，政策代码已更新成<{policy}>完成")


async def order_unlock(
        *, logger: Logger, page: OrderDetailPage, remark: str, order_id: int, is_force: bool = False,
        qlv_user_id: Optional[str] = None, timeout: float = 5.0
) -> None:
    try:
        confirm_btn = await page.get_message_notice_dialog_confirm_btn(timeout=3)
        await confirm_btn.click(button="left")
        logger.info("订单详情页面，消息提醒弹框，【确认】按钮点击完成")
        await asyncio.sleep(2)
    except (Exception,):
        pass
    # 1. 获取订单操作锁的状态
    lock_state, lock_btn = await page.get_order_lock_state_btn(timeout=timeout)
    if "强制解锁" in lock_state:
        if is_force is False:
            raise EnvironmentError(f"被他人锁定，无需解锁处理")
        await lock_btn.click(button="left")
        logger.info(f"订单详情页面，用户操作【{lock_state}】按钮点击完成")
        try:
            confirm_btn = await page.get_message_notice_dialog_confirm_btn(timeout=5)
            await confirm_btn.click(button="left")
            logger.info("订单详情页面，强制解锁弹框确认，【确认】按钮点击完成")
            await asyncio.sleep(2)
        except (PlaywrightTimeoutError, PlaywrightError, RuntimeError, Exception):
            pass
        logger.warning(f"订单<{order_id}>，已被用户<{qlv_user_id or '无记录'}>强制解锁")
        # 再次获取订单操作锁的状态
        lock_state, lock_btn = await page.get_order_lock_state_btn(timeout=timeout)
    elif "锁定" in lock_state:
        logger.info(f"订单<{order_id}>，处于无锁状态，无需解锁处理")
        return
    elif "操作" in lock_state:
        await lock_btn.click(button="left")
        logger.info(f"订单详情页面，日志记录栏，【{lock_state}】按钮点击完成")
        try:
            confirm_btn = await page.get_message_notice_dialog_confirm_btn(timeout=3)
            await confirm_btn.click(button="left")
            logger.info("订单详情页面，消息提醒弹框，【确认】按钮点击完成")
            await asyncio.sleep(2)
        except (Exception,):
            pass
        lock_state, lock_btn = await page.get_order_lock_state_btn(timeout=timeout)
        logger.info(f"订单详情页面，页面刷新后，【{lock_state}】按钮获取完成")
        if "操作" in lock_state:
            await lock_btn.click(button="left")
            logger.info(f"订单详情页面，日志记录栏，【{lock_state}】按钮点击完成")
            try:
                confirm_btn = await page.get_message_notice_dialog_confirm_btn(timeout=3)
                await confirm_btn.click(button="left")
                logger.info("订单详情页面，消息提醒弹框，【确认】按钮点击完成")
                await asyncio.sleep(2)
            except (Exception,):
                pass
            lock_state, lock_btn = await page.get_order_lock_state_btn(timeout=timeout)
    if remark:
        # 2. 添加解锁备注
        await add_custom_remark(logger=logger, page=page, remark=remark, timeout=timeout)

    # 3. 点击【解锁返回】按钮
    await lock_btn.click(button="left")
    await asyncio.sleep(2)
    logger.info(f"订单详情页面，日志记录栏，【{lock_state}】按钮点击完成")


async def order_locked(
        *, logger: Logger, page: OrderDetailPage, order_id: int, is_force: bool = False, timeout: float = 5.0,
        qlv_user_id: Optional[str] = None
) -> None:
    # 1. 获取订单操作锁的状态
    lock_state, lock_btn = await page.get_order_lock_state_btn(timeout=timeout)
    if "强制解锁" in lock_state:
        if is_force is False:
            raise EnvironmentError(f"被他人锁定，不做加锁处理")
        await lock_btn.click(button="left")
        logger.info(f"订单详情页面，用户操作【{lock_state}】按钮点击完成")
        try:
            confirm_btn = await page.get_message_notice_dialog_confirm_btn(timeout=1)
            await confirm_btn.click(button="left")
            logger.info("订单详情页面，强制解锁弹框确认，【确认】按钮点击完成")
            await asyncio.sleep(2)
        except (PlaywrightTimeoutError, PlaywrightError, RuntimeError, Exception):
            pass
        logger.warning(f"订单<{order_id}>，已被用户<{qlv_user_id or '无记录'}>强制解锁")
        return
    elif "解锁返回" in lock_state:
        logger.warning(f"订单<{order_id}>，处于锁定状态，不做加锁处理")
        return
    # 2. 点击【锁定|操作】按钮
    await lock_btn.click(button="left")
    logger.info(f"订单详情页面，日志记录栏，【{lock_state}】按钮点击完成")
    try:
        confirm_btn = await page.get_message_notice_dialog_confirm_btn(timeout=1)
        await confirm_btn.click(button="left")
        logger.info("订单详情页面，强制解锁弹框确认，【确认】按钮点击完成")
        await asyncio.sleep(2)
    except (PlaywrightTimeoutError, PlaywrightError, RuntimeError, Exception):
        pass


async def first_open_page_order_locked(
        *, logger: Logger, page: Page, protocol: str, domain: str, order_id: int, is_force: bool = False,
        qlv_user_id: Optional[str] = None, timeout: float = 5.0, **kwargs
) -> OrderDetailPage:
    # 1. 打开页面
    order_detail_po = await open_order_detail_page(
        page=page, logger=logger, protocol=protocol, domain=domain, order_id=order_id, timeout=timeout
    )

    # 2. 锁定订单
    await order_locked(
        logger=logger, page=order_detail_po, order_id=order_id, timeout=timeout, is_force=is_force,
        qlv_user_id=qlv_user_id
    )
    return order_detail_po


async def fill_itinerary(
        *, logger: Logger, page: OrderDetailPage, order_id: int, passengers_itinerary: Dict[str, Any],
        timeout: float = 5.0
) -> None:
    # 1. 获取订单操作锁的状态
    passenger_itinerary_locators: List[Dict[str, Any]] = await page.get_passenger_itinerary_locators(timeout=timeout)
    if not passenger_itinerary_locators:
        logger.warning(f"订单<{order_id}>，没有需要填写票号的乘客，直接跳过")
        return
    current_passengers = set([x.get("username") for x in passenger_itinerary_locators])
    kwargs_passengers = set(passengers_itinerary.keys())
    diff = kwargs_passengers.difference(current_passengers)
    if diff:
        raise RuntimeError(
            f"传递回填票号的乘客证件信息<{kwargs_passengers}>与订单实际乘客信息<{current_passengers}>不一致"
        )
    for passenger_locator in passenger_itinerary_locators:
        current_passenger = passenger_locator.get("username")
        passenger_itinerary = passengers_itinerary.get(current_passenger)
        if passenger_itinerary:
            passenger_itinerary_locator: Locator = passenger_locator.get("locator")
            await passenger_itinerary_locator.fill(value=passenger_itinerary)
            await passenger_itinerary_locator.press("Enter")
            logger.info(f"订单<{order_id}>，乘客<{current_passenger}>的票号<{passenger_itinerary}>填写完成")
            await asyncio.sleep(1)
        else:
            logger.warning(f"订单<{order_id}>，乘客<{current_passenger}>的票号没有获取到，本次回填跳过，等待下一次")


async def first_open_page_fill_itinerary(
        *, page: Page, logger: Logger, protocol: str, domain: str, order_id: int,
        passengers_itinerary: Dict[str, Any], timeout: float = 20.0, **kwargs: Any
) -> OrderDetailPage:
    # 1. 开发页面
    order_detail_po = await open_order_detail_page(
        page=page, logger=logger, protocol=protocol, domain=domain, order_id=order_id, timeout=timeout
    )

    # 2. 回填票号
    await fill_itinerary(
        logger=logger, page=order_detail_po, order_id=order_id, timeout=timeout,
        passengers_itinerary=passengers_itinerary
    )
    logger.info(f"订单<{order_id}>，票号回填流程结束")

    # 3. 解锁订单
    await order_unlock(
        logger=logger, page=order_detail_po, order_id=order_id, timeout=timeout, is_force=True, remark=""
    )
    logger.info(f"订单<{order_id}>，订单解锁成功")
    return order_detail_po


async def first_open_page_my_order_unlock(
        *, page: Page, logger: Logger, protocol: str, domain: str, order_id: int, qlv_user_id: str,
        policy: Optional[str] = None, remark: Optional[str] = None, timeout: float = 20.0, is_force: bool = False,
        **kwargs: Any
) -> None:
    # 1. 打开页面
    order_detail_po = await open_order_detail_page(
        page=page, logger=logger, protocol=protocol, domain=domain, order_id=order_id, timeout=timeout
    )

    if policy:
        # 2. 更新订单政策代码
        await update_order_policy(
            logger=logger, page=order_detail_po, order_id=order_id, timeout=timeout, policy=policy
        )

    # 3. 获取订单操作锁的状态
    await order_unlock(
        logger=logger, page=order_detail_po, remark=remark, order_id=order_id, is_force=is_force,
        qlv_user_id=qlv_user_id, timeout=timeout
    )


async def fill_procurement_with_http_callback(
        *, fill_procurement_dto: FillProcurementInputDTO, retry: int = 1, timeout: int = 5, enable_log: bool = True,
        cookie_jar: Optional[aiohttp.CookieJar] = None, playwright_state: Dict[str, Any] = None,
        data_list: Optional[List[Dict[str, Any]]] = None, **kwargs: Any
) -> Dict[str, Any]:
    return await fill_procurement_dto_with_http(
        fill_procurement_dto=fill_procurement_dto, retry=retry, timeout=timeout, enable_log=enable_log,
        cookie_jar=cookie_jar, playwright_state=playwright_state, data_list=data_list
    )
