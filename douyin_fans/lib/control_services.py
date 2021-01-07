#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
# Copyright 2019 黎慧剑
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""
后台控制服务模块

@module control_services
@file control_services.py
"""

import os
import sys
import json
import time
import math
import re
import random
import threading
import sqlite3
import traceback
import subprocess
from flask import request
from appium.webdriver.common.mobileby import MobileBy
from HiveNetLib.simple_restful.server import FlaskTool, FlaskServer
from HandLessRobot.lib.controls.appium.android import AppDevice as AndroidDevice, AppElement as AndroidElement
# 根据当前文件路径将包路径纳入，在非安装的情况下可以引用到
sys.path.append(os.path.abspath(os.path.join(
    os.path.dirname(__file__), os.path.pardir, os.path.pardir)))


__MOUDLE__ = 'control_services'  # 模块名
__DESCRIPT__ = u'后台控制服务模块'  # 模块描述
__VERSION__ = '0.1.0'  # 版本
__AUTHOR__ = u'黎慧剑'  # 作者
__PUBLISH__ = '2020.12.11'  # 发布日期


class DyControlApi(object):
    """
    抖音后台控制Api接口
    """

    #############################
    # 构造函数
    #############################
    def __init__(self, **kwargs):
        """
        抖音后台控制Api接口

        @param {str} config_path=None - 配置文件所在目录(sqlite文件)
        """
        self.kwargs = kwargs
        # 配置目录
        self.config_path = os.path.abspath(
            os.path.join(os.path.dirname(__file__), os.path.pardir, 'config')
        ) if self.kwargs.get('config_path', None) is None else self.kwargs['config_path']

        # 内部的控制变量
        self._db_lock = threading.RLock()  # 数据访问锁，保证单线程访问

        # 连接配置库, 需要允许多线程访问
        self.db_conn = sqlite3.connect(
            os.path.join(self.config_path, 'info.db'), check_same_thread=False
        )
        # 创建所需的配置表
        self._exec_sql(
            'create table if not exists t_para(p_name varchar(30) primary key, p_type varchar(30), p_value varchar(500))'
        )  # 系统参数表
        self._exec_sql(
            'create table if not exists t_bg_para(p_name varchar(30) primary key, p_type varchar(30), p_value varchar(500))'
        )  # 后台参数表
        self._exec_sql("""
            create table if not exists t_device_list(
                device_name varchar(100) primary key,
                use_anonymous varchar(10),
                user_name varchar(100),
                remark varchar(200),
                platform_name varchar(20),
                platform_version varchar(20),
                brand varchar(50),
                model varchar(50),
                use_wifi varchar(10),
                wlan_ip varchar(30),
                wlan_port varchar(20),
                app_version varchar(20)
            )
        """)  # 终端设备跟抖音用户关联配置
        # 设备表字段映射清单
        self._devices_col_list = [
            'device_name', 'user_name', 'platform_name', 'platform_version', 'brand', 'model',
            'use_wifi', 'wlan_ip', 'wlan_port', 'use_anonymous', 'remark', 'app_version'
        ]
        # 设备表字段类型映射字典
        self._devices_col_type = {
            'use_wifi': 'bool', 'use_anonymous': 'bool'
        }

        # 获取系统初始化参数
        _fetchs = self._exec_sql('select * from t_para', is_fetchall=True)
        self.para = {
            # Web服务器配置
            'site': '127.0.0.1',
            'host': '127.0.0.1',
            'port': 5000,
            'threaded': True,
            'processes': 1,
            'json_as_ascii': False,
            'use_wsgi': True,
            # 设备检测配置
            'adb': 'adb',
            'shell_encoding': 'utf-8',  # GBK
            'wifi_port': '5555',
            # 应用自动化参数
            'auto_into_line': True,  # 自动进入直播间
            'into_line_err_exit': True,  # 自动进入直播间失败退出
            'is_into_wait': True,  # 批量进入直播间是否随机间隔时长（防风控）
            'into_line_wait_min': 0.5,  # 批量进入直播间间隔最小时长
            'into_line_wait_max': 2.0,  # 批量进入直播间间隔最大时长
            # Appium设置
            'appium_server': 'http://localhost:4723/wd/hub',
            'implicitly_wait': 20.0,  # 查找元素最长等待时间
            'android_restore_ime': 'com.microvirt.memuime/.MemuIME',  # 多控统一恢复输入法
            # 安卓控制参数 - 启动
            'android_apk': 'ADBKeyboard.apk',  # 安装apk，放在 config 目录中
            'android_appPackage': 'com.ss.android.ugc.aweme',  # 抖音应用
            'android_appActivity': '.splash.SplashActivity',  # 抖音首页
            'android_search_appActivity': '.search.activity.SearchResultActivity',  # 抖音搜索页
            'android_line_appActivity': '.live.LivePlayActivity|.detail.ui.LiveDetailActivity',  # 抖音直播页面
            'android_desired_caps': """{
                \"noReset\": true,
                \"unicodeKeyboard\": false,
                \"resetKeyboard\": false,
                \"dontStopOnReset\": true,
                \"fullReset\": false,
                \"automationName\": \"UiAutomator2\",
                \"newCommandTimeout\":20000,
                \"noSign\": true
            }""",
            # 安卓控制参数 - 脚本
            'android_chat_wait_input': 1,  # 等待输入框弹出的时间
            'android_script_version_mapping': """{
                \"14.*\": \"aweme_14.1.0.json\",
                \"13.*\": \"aweme_13.5.0.json\"
            }""",
            # 点赞设置参数
            'give_thumbs_up_offset_x': 0.01,  # 点赞操作从屏幕中心偏移比例(可以为负数)
            'give_thumbs_up_offset_y': 0.01,  # 点赞操作从屏幕中心偏移比例(可以为负数)
            'give_thumbs_up_random_x': 0.01,  # 点赞操作点击点的随机位置范围大小
            'give_thumbs_up_random_y': 0.01,  # 点赞操作点击点的随机位置范围大小
            'give_thumbs_up_random_seed': 5,  # 点赞操作点击点的随机位置种子数量
            'give_thumbs_up_tap_max': 5,  # 点赞操作每次命令点击次数上限
            'give_thumbs_up_tap_random': True,  # 点赞操作是否每次随机点击次数
            'give_thumbs_up_random_wait': True,  # 点赞点击之间是否随机等待时长
            'give_thumbs_up_wait_min': 0.0,  # 点赞点击之间是否随机最小时长
            'give_thumbs_up_wait_max': 0.5,  # 点赞点击之间是否随机最大时长
        }  # 默认值
        self._dbrows_to_para(_fetchs, self.para)
        # 刷新回数据库
        self._update_db_para(self.para, 't_para')

        # 获取后台初始化参数
        _fetchs = self._exec_sql('select * from t_bg_para', is_fetchall=True)
        self.bg_para = {
            'line_name': '直播间',  # 直播间名
            'send_bt_wait_min': 0.5,  # 多人操作间隔最小时长
            'send_bt_wait_max': 2.0,  # 多人操作间隔最大时长
            'give_thumbs_self_define': 20,  # 自定义点赞时长(秒)
            'tap_to_main': '0.5,0.25',  # 点击屏幕
        }
        self._dbrows_to_para(_fetchs, self.bg_para)
        # 刷新回数据库
        self._update_db_para(self.bg_para, 't_bg_para')

        # 加载脚本和版本映射关系
        self._version_script_mapping = dict()  # 配置的版本号跟脚本配置文件的关系
        self._script_info = dict()  # 脚本配置文件与脚本配置的关系
        self._load_script_version_mapping()

        # 获取设备清单, key 为 device_name, value 为整体设备信息
        self.devices = dict()
        self._get_devices_from_db()  # 获取故障清单
        self._reflesh_devices_status()  # 刷新设备状态

        # 设备连接应用的映射字典, key 为 device_name, value 为连接信息字典
        # app - 设备连接上的 AppDevice 对象
        # app_package - 当前连接的应用包名
        # activit_type - 连接页面的类型, line - 直播, user_name - 用户名称
        self.apps = dict()

        # 批量任务处理交互临时字典, 格式为
        # {
        #     interface_id: {
        #         device_name: {
        #             'type': '',  # 任务类型
        #             'para': obj, # 执行任务参数
        #             'is_success': False,  # 是否执行成功
        #             'msg': ''  # 结果信息
        #         },
        #         ...
        #     },
        #     ...
        # }
        self._batch_task = dict()
        # 批量任务执行的函数映射, key 为 type, value 为执行函数对象
        self._batch_fun_mapping = {
            'into_app_line': self._into_app_line_batch_fun,
            'app_send_chat': self._app_send_chat_batch_fun,
            'app_send_heart': self._app_send_heart_batch_fun,
            'app_click_car': self._app_click_car_batch_fun,
            'app_give_thumbs_up': self._app_give_thumbs_up_batch_fun,
            'app_tap_screen': self._app_tap_screen_batch_fun,
        }

    #############################
    # API - config配置
    #############################
    @FlaskTool.log(get_logger_fun=FlaskServer.get_logger_fun, get_logger_para={'app_name': 'dy_control_server'})
    @FlaskTool.support_object_resp
    def get_config(self, methods=['POST'], **kwargs):
        """
        获取系统配置

        @api {post} {json} /api/DyControlApi/get_config get_config
        @body-in {str} interface_id - 接口id

        @body-out {str} interface_id - 接口id
        @body-out {str} status - 处理状态, 定义如下
            00000 - 成功
            21599 - 应用服务处理其他失败
        @body-out {str} msg - 处理状态对应的描述
        @body-out {str} site - 访问IP或域名
        @body-out {str} host - 监听IP
        @body-out {int} port - 监听端口
        @body-out {int} processes - 进程数
        @body-out {bool} use_wsgi - 是否使用WSGI服务器
        @body-out {bool} json_as_ascii - JSON兼容ASCII编码
        @body-out {bool} threaded - 是否使用多线程
        """
        # 日志对象获取
        _logger = kwargs.get('logger', None)
        _logging_level = kwargs.get('logging_level', None)
        _logger_extra = kwargs.get('logger_extra', None)

        # 设置返回的字典
        _resp = {
            'interface_id': request.json.get('interface_id', ''),
            'status': '00000',
            'msg': '成功'
        }
        try:
            _resp.update(self.para)
            return _resp
        except Exception as e:
            _resp['status'] = '21599'
            _resp['msg'] = str(e)
            if _logger is not None:
                _logger.log(
                    _logging_level,
                    '[EX][interface_id:%s]%s' % (_resp['interface_id'], traceback.format_exc()),
                    extra=_logger_extra
                )
            return _resp

    @FlaskTool.log(get_logger_fun=FlaskServer.get_logger_fun, get_logger_para={'app_name': 'dy_control_server'})
    @FlaskTool.support_object_resp
    def set_config(self, methods=['POST'], **kwargs):
        """
        更新系统配置

        @api {post} {json} /api/DyControlApi/set_config set_config
        @body-in {str} interface_id - 接口id
        @body-in {str} site - 访问IP或域名
        @body-in {str} host - 监听IP
        @body-in {int} port - 监听端口
        @body-in {int} processes - 进程数
        @body-in {bool} use_wsgi - 是否使用WSGI服务器
        @body-in {bool} json_as_ascii - JSON兼容ASCII编码
        @body-in {bool} threaded - 是否使用多线程

        @body-out {str} interface_id - 接口id
        @body-out {str} status - 处理状态, 定义如下
            00000 - 成功
            21599 - 应用服务处理其他失败
        @body-out {str} msg - 处理状态对应的描述
        """
        # 日志对象获取
        _logger = kwargs.get('logger', None)
        _logging_level = kwargs.get('logging_level', None)
        _logger_extra = kwargs.get('logger_extra', None)

        # 设置返回的字典
        _resp = {
            'interface_id': request.json.get('interface_id', ''),
            'status': '00000',
            'msg': '成功'
        }
        try:
            _para: dict = request.json
            _para.pop('interface_id')
            self.para.update(_para)
            self._update_db_para(self.para, 't_para')
            return _resp
        except Exception as e:
            _resp['status'] = '21599'
            _resp['msg'] = str(e)
            if _logger is not None:
                _logger.log(
                    _logging_level,
                    '[EX][interface_id:%s]%s' % (_resp['interface_id'], traceback.format_exc()),
                    extra=_logger_extra
                )
            return _resp

    @FlaskTool.log(get_logger_fun=FlaskServer.get_logger_fun, get_logger_para={'app_name': 'dy_control_server'})
    @FlaskTool.support_object_resp
    def get_bg_config(self, methods=['POST'], **kwargs):
        """
        后去后台配置

        @api {post} {json} /api/DyControlApi/get_bg_config get_bg_config
        @body-in {str} interface_id - 接口id

        @body-out {str} interface_id - 接口id
        @body-out {str} status - 处理状态, 定义如下
            00000 - 成功
            21599 - 应用服务处理其他失败
        @body-out {str} msg - 处理状态对应的描述
            ...
        """
        # 日志对象获取
        _logger = kwargs.get('logger', None)
        _logging_level = kwargs.get('logging_level', None)
        _logger_extra = kwargs.get('logger_extra', None)

        # 设置返回的字典
        _resp = {
            'interface_id': request.json.get('interface_id', ''),
            'status': '00000',
            'msg': '成功'
        }
        try:
            _resp.update(self.bg_para)
            return _resp
        except Exception as e:
            _resp['status'] = '21599'
            _resp['msg'] = str(e)
            if _logger is not None:
                _logger.log(
                    _logging_level,
                    '[EX][interface_id:%s]%s' % (_resp['interface_id'], traceback.format_exc()),
                    extra=_logger_extra
                )
            return _resp

    @FlaskTool.log(get_logger_fun=FlaskServer.get_logger_fun, get_logger_para={'app_name': 'dy_control_server'})
    @FlaskTool.support_object_resp
    def set_bg_config(self, methods=['POST'], **kwargs):
        """
        更新系统配置

        @api {post} {json} /api/DyControlApi/set_bg_config set_bg_config
        @body-in {str} interface_id - 接口id
        ...

        @body-out {str} interface_id - 接口id
        @body-out {str} status - 处理状态, 定义如下
            00000 - 成功
            21599 - 应用服务处理其他失败
        @body-out {str} msg - 处理状态对应的描述
        """
        # 日志对象获取
        _logger = kwargs.get('logger', None)
        _logging_level = kwargs.get('logging_level', None)
        _logger_extra = kwargs.get('logger_extra', None)

        # 设置返回的字典
        _resp = {
            'interface_id': request.json.get('interface_id', ''),
            'status': '00000',
            'msg': '成功'
        }
        try:
            _para: dict = request.json
            _para.pop('interface_id')
            self.bg_para.update(_para)
            self._update_db_para(self.bg_para, 't_bg_para')
            # 重置mapping
            self._load_script_version_mapping()
            return _resp
        except Exception as e:
            _resp['status'] = '21599'
            _resp['msg'] = str(e)
            if _logger is not None:
                _logger.log(
                    _logging_level,
                    '[EX][interface_id:%s]%s' % (_resp['interface_id'], traceback.format_exc()),
                    extra=_logger_extra
                )
            return _resp

    #############################
    # ADB相关操作
    #############################
    @FlaskTool.log(get_logger_fun=FlaskServer.get_logger_fun, get_logger_para={'app_name': 'dy_control_server'})
    @FlaskTool.support_object_resp
    def get_devcies(self, methods=['POST'], **kwargs):
        """
        获取设备清单

        @api {post} {json} /api/DyControlApi/get_devcies get_devcies
        @body-in {str} interface_id - 接口id

        @body-out {str} interface_id - 接口id
        @body-out {str} status - 处理状态, 定义如下
            00000 - 成功
            21599 - 应用服务处理其他失败
        @body-out {str} msg - 处理状态对应的描述
        @body-out {list} devices - 找到的设备清单
            [
                {
                    'device_name': '',  # 可连接的设备名
                    'platform_name': 'Android',  # 手机平台名
                    'platform_version': '',  # 手机平台版本
                    'use_wifi': false,  # 是否使用wifi连接方式
                    'wlan_ip': '',  # 手机连接的 wifi ip
                    'wlan_port': '',  # 手机连接的 wifi 端口
                    'brand': '',  # 手机的品牌
                    'model': '',  # 手机的产品名称
                    'use_anonymous': false,  # 是否使用匿名
                    'user_name': '',  # 绑定的抖音用户
                    'remark': '',  # 备注信息
                    'app_version': '',  # app版本
                    'connnect_status': ''  # 连接状态, unconnect, connected, started
                },
                ...
            ]
        """
        # 日志对象获取
        _logger = kwargs.get('logger', None)
        _logging_level = kwargs.get('logging_level', None)
        _logger_extra = kwargs.get('logger_extra', None)

        # 设置返回的字典
        _resp = {
            'interface_id': request.json.get('interface_id', ''),
            'status': '00000',
            'msg': '成功'
        }
        try:
            _resp['devices'] = list()

            # 刷新状态
            self._reflesh_devices_status()

            # 组装返回
            for _device_name in self.devices.keys():
                _resp['devices'].append(
                    self.devices[_device_name]
                )
            # 返回结果
            return _resp
        except Exception as e:
            _resp['status'] = '21599'
            _resp['msg'] = str(e)
            if _logger is not None:
                _logger.log(
                    _logging_level,
                    '[EX][interface_id:%s]%s' % (_resp['interface_id'], traceback.format_exc()),
                    extra=_logger_extra
                )
            return _resp

    @FlaskTool.log(get_logger_fun=FlaskServer.get_logger_fun, get_logger_para={'app_name': 'dy_control_server'})
    @FlaskTool.support_object_resp
    def auto_add_devices(self, methods=['POST'], **kwargs):
        """
        自动将已连接的设备加入到清单

        @api {post} {json} /api/DyControlApi/auto_add_devices auto_add_devices
        @body-in {str} interface_id - 接口id

        @body-out {str} interface_id - 接口id
        @body-out {str} status - 处理状态, 定义如下
            00000 - 成功
            21599 - 应用服务处理其他失败
        @body-out {str} msg - 处理状态对应的描述
        @body-out {list} devices - 返回全部设备清单
            [
                {
                    'device_name': '',  # 可连接的设备名
                    'platform_name': 'Android',  # 手机平台名
                    'platform_version': '',  # 手机平台版本
                    'use_wifi': false,  # 是否使用wifi连接方式
                    'wlan_ip': '',  # 手机连接的 wifi ip
                    'wlan_port': '',  # 手机连接的 wifi 端口
                    'brand': '',  # 手机的品牌
                    'model': '',  # 手机的产品名称
                    'use_anonymous': false,  # 是否使用匿名
                    'user_name': '',  # 绑定的抖音用户
                    'remark': '',  # 备注信息
                    'app_version': '',  # app版本
                    'connnect_status': ''  # 连接状态, unconnect, connected, started
                },
                ...
            ]
        """
        # 日志对象获取
        _logger = kwargs.get('logger', None)
        _logging_level = kwargs.get('logging_level', None)
        _logger_extra = kwargs.get('logger_extra', None)

        # 设置返回的字典
        _resp = {
            'interface_id': request.json.get('interface_id', ''),
            'status': '00000',
            'msg': '成功'
        }
        try:
            _resp['devices'] = list()

            # 先获取已连接的设备清单
            _connected_devices = self._get_connected_devices()

            # 逐个检查是否在清单中
            for _device_name in _connected_devices.keys():
                if _device_name not in self.devices.keys():
                    # 添加设备到数据库
                    self._update_db_device(_connected_devices[_device_name])

            # 更新设备状态
            self._reflesh_devices_status()

            # 组装返回
            for _device_name in self.devices.keys():
                _resp['devices'].append(
                    self.devices[_device_name]
                )
            # 返回结果
            return _resp
        except Exception as e:
            _resp['status'] = '21599'
            _resp['msg'] = str(e)
            if _logger is not None:
                _logger.log(
                    _logging_level,
                    '[EX][interface_id:%s]%s' % (_resp['interface_id'], traceback.format_exc()),
                    extra=_logger_extra
                )
            return _resp

    @FlaskTool.log(get_logger_fun=FlaskServer.get_logger_fun, get_logger_para={'app_name': 'dy_control_server'})
    @FlaskTool.support_object_resp
    def get_device_info(self, methods=['POST'], **kwargs):
        """
        获取特定设备信息

        @api {post} {json} /api/DyControlApi/get_device_info get_device_info
        @body-in {str} interface_id - 接口id
        @body-in {str} device_name - 可选, 如果不传入设备名, 则自动获取不在已有设备列表中的第一个设备名

        @body-out {str} interface_id - 接口id
        @body-out {str} status - 处理状态, 定义如下
            00000 - 成功
            21599 - 应用服务处理其他失败
        @body-out {str} msg - 处理状态对应的描述
        @body-out {dict} info - 设备信息字典
            {
                    'device_name': '',  # 可连接的设备名
                    'platform_name': 'Android',  # 手机平台名
                    'platform_version': '',  # 手机平台版本
                    'use_wifi': false,  # 是否使用wifi连接方式
                    'wlan_ip': '',  # 手机连接的 wifi ip
                    'wlan_port': '',  # 手机连接的 wifi 端口
                    'brand': '',  # 手机的品牌
                    'model': '',  # 手机的产品名称
                    'use_anonymous': false,  # 是否使用匿名
                    'user_name': '',  # 绑定的抖音用户
                    'remark': '',  # 备注信息
                    'app_version': '',  # app版本
                    'connnect_status': ''  # 连接状态, unconnect, connected, started
            }
        """
        # 日志对象获取
        _logger = kwargs.get('logger', None)
        _logging_level = kwargs.get('logging_level', None)
        _logger_extra = kwargs.get('logger_extra', None)

        # 设置返回的字典
        _resp = {
            'interface_id': request.json.get('interface_id', ''),
            'status': '00000',
            'msg': '成功'
        }
        try:
            # 获取设备名
            _device_name = request.json.get('device_name', '')
            if _device_name == '':
                _connected_devices = self._get_connected_devices()
                for _name in _connected_devices.keys():
                    if _name not in self.devices.keys():
                        _device_name = _name
                        break

            if _device_name == '':
                raise RuntimeError('ADB连接清单中未找到未添加设备')

            # 获取设备信息
            _resp['info'] = {
                'platform_name': 'Android',  # 手机平台名
                'platform_version': '',  # 手机平台版本
                'use_wifi': False,  # 是否使用wifi连接方式
                'wlan_ip': '',  # 手机连接的 wifi ip
                'wlan_port': '',  # 手机连接的 wifi 端口
                'brand': '',  # 手机的品牌
                'model': '',  # 手机的产品名称
                'use_anonymous': False,  # 是否使用匿名
                'user_name': '',  # 绑定的抖音用户
                'remark': '',  # 备注信息
                'app_version': '',  # app版本
                'connnect_status': 'unconnect'  # 连接状态, unconnect, connected, started
            }
            _resp['info'].update(self._get_device_info(_device_name))

            # 返回结果
            return _resp
        except Exception as e:
            _resp['status'] = '21599'
            _resp['msg'] = str(e)
            if _logger is not None:
                _logger.log(
                    _logging_level,
                    '[EX][interface_id:%s]%s' % (_resp['interface_id'], traceback.format_exc()),
                    extra=_logger_extra
                )
            return _resp

    @FlaskTool.log(get_logger_fun=FlaskServer.get_logger_fun, get_logger_para={'app_name': 'dy_control_server'})
    @FlaskTool.support_object_resp
    def add_device(self, methods=['POST'], **kwargs):
        """
        添加或替换清单中的设备

        @api {post} {json} /api/DyControlApi/add_device add_device
        @body-in {str} interface_id - 接口id
        @body-in {str} device_name - 设备名
        @body-in {bool} auto_connect - 自动连接
        @body-in {bool} use_wifi - 是否使用wifi连接方式
        @body-in {str} wlan_ip - 手机连接的 wifi ip
        @body-in {str} wlan_port - 手机连接的 wifi 端口
        @body-in {bool} use_anonymous - 是否使用匿名
        @body-in {str} user_name - 绑定的抖音用户
        @body-in {str} remark - 备注信息, 可选

        @body-out {str} interface_id - 接口id
        @body-out {str} status - 处理状态, 定义如下
            00000 - 成功
            21599 - 应用服务处理其他失败
        @body-out {str} msg - 处理状态对应的描述
        """
        # 日志对象获取
        _logger = kwargs.get('logger', None)
        _logging_level = kwargs.get('logging_level', None)
        _logger_extra = kwargs.get('logger_extra', None)

        # 设置返回的字典
        _resp = {
            'interface_id': request.json.get('interface_id', ''),
            'status': '00000',
            'msg': '成功'
        }
        try:
            _req_info = request.json
            _device_name = _req_info['device_name']
            if _req_info['auto_connect']:
                # 要求自动进行连接
                _info = self._connect_device(
                    _device_name, use_wifi=_req_info['use_wifi'],
                    wlan_ip=_req_info['wlan_ip'], wlan_port=_req_info['wlan_port']
                )
                _info['connnect_status'] = 'connected'
                _info['use_anonymous'] = _req_info['use_anonymous']
                _info['user_name'] = _req_info['user_name']
                _info['remark'] = _req_info.get('remark', '')
            else:
                # 没有要求自动连接，直接组成信息
                _info = {
                    'device_name': _device_name if not _req_info['use_wifi'] else '%s:%s' % (
                        _req_info['wlan_ip'], str(_req_info['wlan_port'])
                    ),
                    'platform_name': 'Android',  # 手机平台名
                    'platform_version': '',  # 手机平台版本
                    'use_wifi': _req_info['use_wifi'],  # 是否使用wifi连接方式
                    'wlan_ip': _req_info['wlan_ip'],  # 手机连接的 wifi ip
                    'wlan_port': _req_info['wlan_port'],  # 手机连接的 wifi 端口
                    'brand': '',  # 手机的品牌
                    'model': '',  # 手机的产品名称
                    'use_anonymous': _req_info['use_anonymous'],  # 是否使用匿名
                    'user_name': _req_info['user_name'],  # 绑定的抖音用户
                    'remark': _req_info.get('remark', ''),  # 备注信息
                    'app_version': '',  # app版本
                    'connnect_status': 'unconnect'  # 连接状态, unconnect, connected, started
                }

            # wifi模式涉及要删除原来的记录
            if _info['use_wifi']:
                if _device_name in self.devices.keys():
                    # 删除原来的记录
                    self._remove_db_device(_device_name)

            # 添加或替换记录
            self._update_db_device(_info)

            # 返回结果
            return _resp
        except Exception as e:
            _resp['status'] = '21599'
            _resp['msg'] = str(e)
            if _logger is not None:
                _logger.log(
                    _logging_level,
                    '[EX][interface_id:%s]%s' % (_resp['interface_id'], traceback.format_exc()),
                    extra=_logger_extra
                )
            return _resp

    @FlaskTool.log(get_logger_fun=FlaskServer.get_logger_fun, get_logger_para={'app_name': 'dy_control_server'})
    @FlaskTool.support_object_resp
    def device_bind_user(self, methods=['POST'], **kwargs):
        """
        更新设备绑定抖音用户

        @api {post} {json} /api/DyControlApi/device_bind_user device_bind_user
        @body-in {str} interface_id - 接口id
        @body-in {str} device_name - 设备名
        @body-in {bool} use_anonymous - 是否使用匿名
        @body-in {str} user_name - 绑定的抖音用户
        @body-in {str} remark - 备注信息

        @body-out {str} interface_id - 接口id
        @body-out {str} status - 处理状态, 定义如下
            00000 - 成功
            21599 - 应用服务处理其他失败
        @body-out {str} msg - 处理状态对应的描述
        """
        # 日志对象获取
        _logger = kwargs.get('logger', None)
        _logging_level = kwargs.get('logging_level', None)
        _logger_extra = kwargs.get('logger_extra', None)

        # 设置返回的字典
        _resp = {
            'interface_id': request.json.get('interface_id', ''),
            'status': '00000',
            'msg': '成功'
        }
        try:
            _req_info = request.json
            _device_name = _req_info['device_name']
            if _device_name in self.devices.keys():
                # 更新信息
                self.devices[_device_name]['use_anonymous'] = _req_info['use_anonymous']
                self.devices[_device_name]['user_name'] = _req_info['user_name']
                self.devices[_device_name]['remark'] = _req_info['remark']
                self._update_db_device(self.devices[_device_name])
            else:
                raise RuntimeError('设备 [%s] 不在设备清单中!' % _device_name)

            # 返回结果
            return _resp
        except Exception as e:
            _resp['status'] = '21599'
            _resp['msg'] = str(e)
            if _logger is not None:
                _logger.log(
                    _logging_level,
                    '[EX][interface_id:%s]%s' % (_resp['interface_id'], traceback.format_exc()),
                    extra=_logger_extra
                )
            return _resp

    @FlaskTool.log(get_logger_fun=FlaskServer.get_logger_fun, get_logger_para={'app_name': 'dy_control_server'})
    @FlaskTool.support_object_resp
    def remove_devices(self, methods=['POST'], **kwargs):
        """
        从清单中删除设备(支持多个设备的删除)

        @api {post} {json} /api/DyControlApi/remove_devices remove_devices
        @body-in {str} interface_id - 接口id
        @body-in {list} devices - 设备清单, 例如 ['设备名', '设备名']

        @body-out {str} interface_id - 接口id
        @body-out {str} status - 处理状态, 定义如下
            00000 - 成功
            21599 - 应用服务处理其他失败
        @body-out {str} msg - 处理状态对应的描述
        """
        # 日志对象获取
        _logger = kwargs.get('logger', None)
        _logging_level = kwargs.get('logging_level', None)
        _logger_extra = kwargs.get('logger_extra', None)

        # 设置返回的字典
        _resp = {
            'interface_id': request.json.get('interface_id', ''),
            'status': '00000',
            'msg': '成功'
        }
        try:
            for _device_name in request.json.get('devices', []):
                # 删除记录
                self._remove_db_device(_device_name)

            # 返回结果
            return _resp
        except Exception as e:
            _resp['status'] = '21599'
            _resp['msg'] = str(e)
            if _logger is not None:
                _logger.log(
                    _logging_level,
                    '[EX][interface_id:%s]%s' % (_resp['interface_id'], traceback.format_exc()),
                    extra=_logger_extra
                )
            return _resp

    @FlaskTool.log(get_logger_fun=FlaskServer.get_logger_fun, get_logger_para={'app_name': 'dy_control_server'})
    @FlaskTool.support_object_resp
    def connect_devices(self, methods=['POST'], **kwargs):
        """
        主动连接指定设备清单

        @api {post} {json} /api/DyControlApi/connect_devices connect_devices
        @body-in {str} interface_id - 接口id
        @body-in {list} devices - 设备清单, ['设备名', '设备名', ...]

        @body-out {str} interface_id - 接口id
        @body-out {str} status - 处理状态, 定义如下
            00000 - 成功
            21599 - 应用服务处理其他失败
        @body-out {str} msg - 处理状态对应的描述
        @body-out {list} error_info - 连接失败的设备清单和失败信息
            [
                {
                    'device_name': '',
                    'error': ''
                },
                ...
            ]
        """
        # 日志对象获取
        _logger = kwargs.get('logger', None)
        _logging_level = kwargs.get('logging_level', None)
        _logger_extra = kwargs.get('logger_extra', None)

        # 设置返回的字典
        _resp = {
            'interface_id': request.json.get('interface_id', ''),
            'status': '00000',
            'msg': '成功',
            'error_info': list()
        }
        try:
            for _device_name in request.json.get('devices', []):
                # 逐个进行连接处理
                if _device_name not in self.devices.keys():
                    _resp['error_info'].append({
                        'device_name': _device_name,
                        'error': '设备不在已添加的清单中'
                    })
                    continue

                # 进行连接处理
                try:
                    if self.devices[_device_name].get('connnect_status', 'unconnect') == 'unconnect':
                        _info = self._connect_device(
                            _device_name, use_wifi=self.devices[_device_name]['use_wifi'],
                            wlan_ip=self.devices[_device_name]['wlan_ip'], wlan_port=self.devices[_device_name]['wlan_port']
                        )
                        _info.pop('use_anonymous', None)
                        _info.pop('user_name', None)
                        _info.pop('remark', None)

                        # 连接成功, 更新连接状态
                        self.devices[_device_name].update(_info)
                        if self.devices[_device_name].get('connnect_status', 'unconnect') != 'started':
                            self.devices[_device_name]['connnect_status'] = 'connected'
                except Exception as e:
                    _resp['error_info'].append({
                        'device_name': _device_name,
                        'error': str(e)
                    })

            # 返回结果
            return _resp
        except Exception as e:
            _resp['status'] = '21599'
            _resp['msg'] = str(e)
            if _logger is not None:
                _logger.log(
                    _logging_level,
                    '[EX][interface_id:%s]%s' % (_resp['interface_id'], traceback.format_exc()),
                    extra=_logger_extra
                )
            return _resp

    @FlaskTool.log(get_logger_fun=FlaskServer.get_logger_fun, get_logger_para={'app_name': 'dy_control_server'})
    @FlaskTool.support_object_resp
    def disconnect_devices(self, methods=['POST'], **kwargs):
        """
        断开指定设备清单的连接

        @api {post} {json} /api/DyControlApi/disconnect_devices disconnect_devices
        @body-in {str} interface_id - 接口id
        @body-in {list} devices - 设备清单, ['设备名', '设备名', ...]

        @body-out {str} interface_id - 接口id
        @body-out {str} status - 处理状态, 定义如下
            00000 - 成功
            21599 - 应用服务处理其他失败
        @body-out {str} msg - 处理状态对应的描述
        @body-out {list} error_info - 断开连接失败的设备清单和失败信息
            [
                {
                    'device_name': '',
                    'error': ''
                },
                ...
            ]
        """
        # 日志对象获取
        _logger = kwargs.get('logger', None)
        _logging_level = kwargs.get('logging_level', None)
        _logger_extra = kwargs.get('logger_extra', None)

        # 设置返回的字典
        _resp = {
            'interface_id': request.json.get('interface_id', ''),
            'status': '00000',
            'msg': '成功',
            'error_info': list()
        }
        try:
            for _device_name in request.json.get('devices', []):
                # 逐个进行断开连接处理
                if _device_name not in self.devices.keys():
                    _resp['error_info'].append({
                        'device_name': _device_name,
                        'error': '设备不在已添加的清单中'
                    })
                    continue

                # 进行断开连接处理
                try:
                    self._disconnect_device(_device_name)

                    # 断开连接成功, 更新连接状态
                    self.devices[_device_name]['connnect_status'] = 'unconnect'
                except Exception as e:
                    _resp['error_info'].append({
                        'device_name': _device_name,
                        'error': str(e)
                    })

            # 返回结果
            return _resp
        except Exception as e:
            _resp['status'] = '21599'
            _resp['msg'] = str(e)
            if _logger is not None:
                _logger.log(
                    _logging_level,
                    '[EX][interface_id:%s]%s' % (_resp['interface_id'], traceback.format_exc()),
                    extra=_logger_extra
                )
            return _resp

    @FlaskTool.log(get_logger_fun=FlaskServer.get_logger_fun, get_logger_para={'app_name': 'dy_control_server'})
    @FlaskTool.support_object_resp
    def install_app(self, methods=['POST'], **kwargs):
        """
        向设备安装App

        @api {post} {json} /api/DyControlApi/install_app install_app
        @body-in {str} interface_id - 接口id
        @body-in {str} device_name - 设备名

        @body-out {str} interface_id - 接口id
        @body-out {str} status - 处理状态, 定义如下
            00000 - 成功
            21599 - 应用服务处理其他失败
        @body-out {str} msg - 处理状态对应的描述
        """
        # 日志对象获取
        _logger = kwargs.get('logger', None)
        _logging_level = kwargs.get('logging_level', None)
        _logger_extra = kwargs.get('logger_extra', None)

        # 设置返回的字典
        _resp = {
            'interface_id': request.json.get('interface_id', ''),
            'status': '00000',
            'msg': '成功'
        }
        try:
            _device_name = request.json['device_name']
            if _device_name in self.apps.keys():
                raise RuntimeError('设备[%s]正被控制中, 请先关闭直播或等待控制结束！' % _device_name)

            # 安装设备
            self._install_app(_device_name)
            _resp['msg'] = '设备[%s]的App应用安装成功!' % _device_name

            # 返回结果
            return _resp
        except Exception as e:
            _resp['status'] = '21599'
            _resp['msg'] = str(e)
            if _logger is not None:
                _logger.log(
                    _logging_level,
                    '[EX][interface_id:%s]%s' % (_resp['interface_id'], traceback.format_exc()),
                    extra=_logger_extra
                )
            return _resp

    @FlaskTool.log(get_logger_fun=FlaskServer.get_logger_fun, get_logger_para={'app_name': 'dy_control_server'})
    @FlaskTool.support_object_resp
    def restore_ime(self, methods=['POST'], **kwargs):
        """
        恢复设备输入法

        @api {post} {json} /api/DyControlApi/restore_ime restore_ime
        @body-in {str} interface_id - 接口id
        @body-in {list} devices - 设备清单, ['设备名', '设备名', ...]

        @body-out {str} interface_id - 接口id
        @body-out {str} status - 处理状态, 定义如下
            00000 - 成功
            21599 - 应用服务处理其他失败
        @body-out {str} msg - 处理状态对应的描述
        @body-out {list} error_info - 连接失败的设备清单和失败信息
            [
                {
                    'device_name': '',
                    'error': ''
                },
                ...
            ]
        """
        # 日志对象获取
        _logger = kwargs.get('logger', None)
        _logging_level = kwargs.get('logging_level', None)
        _logger_extra = kwargs.get('logger_extra', None)

        # 设置返回的字典
        _resp = {
            'interface_id': request.json.get('interface_id', ''),
            'status': '00000',
            'msg': '成功',
            'error_info': list()
        }
        try:
            for _device_name in request.json.get('devices', []):
                # 逐个进行连接处理
                if _device_name not in self.devices.keys():
                    _resp['error_info'].append({
                        'device_name': _device_name,
                        'error': '设备不在已添加的清单中'
                    })
                    continue

                # 进行输入法的恢复处理
                try:
                    if self.devices[_device_name].get('connnect_status', 'unconnect') == 'unconnect':
                        _resp['error_info'].append({
                            'device_name': _device_name,
                            'error': '设备未连接'
                        })
                        continue

                    # 变更输入法
                    _cmd = '%s -s %s shell ime set %s' % (
                        self.para['adb'], _device_name, self.para['android_restore_ime']
                    )
                    _code, _cmd_info = self._exec_sys_cmd(_cmd)
                    if _code != 0 and not _cmd_info[0].startswith('Input method'):
                        raise RuntimeError('设置输入法失败，请手工执行变更处理！')
                except Exception as e:
                    _resp['error_info'].append({
                        'device_name': _device_name,
                        'error': str(e)
                    })

            # 返回结果
            return _resp
        except Exception as e:
            _resp['status'] = '21599'
            _resp['msg'] = str(e)
            if _logger is not None:
                _logger.log(
                    _logging_level,
                    '[EX][interface_id:%s]%s' % (_resp['interface_id'], traceback.format_exc()),
                    extra=_logger_extra
                )
            return _resp

    #############################
    # 手机控制，抖音APP操作
    #############################
    @FlaskTool.log(get_logger_fun=FlaskServer.get_logger_fun, get_logger_para={'app_name': 'dy_control_server'})
    @FlaskTool.support_object_resp
    def get_app_user(self, methods=['POST'], **kwargs):
        """
        获取抖音用户名

        @api {post} {json} /api/DyControlApi/get_app_user get_app_user
        @body-in {str} interface_id - 接口id
        @body-in {str} device_name - 设备名

        @body-out {str} interface_id - 接口id
        @body-out {str} status - 处理状态, 定义如下
            00000 - 成功
            21599 - 应用服务处理其他失败
        @body-out {str} msg - 处理状态对应的描述
        @body-out {str} user_name - 抖音用户名, 如果获取不到返回 ''
        """
        # 日志对象获取
        _logger = kwargs.get('logger', None)
        _logging_level = kwargs.get('logging_level', None)
        _logger_extra = kwargs.get('logger_extra', None)

        # 设置返回的字典
        _resp = {
            'interface_id': request.json.get('interface_id', ''),
            'status': '00000',
            'msg': '成功',
            'user_name': ''
        }
        try:
            _device_name = request.json['device_name']
            _resp['user_name'] = self._get_app_user(_device_name)

            # 返回结果
            return _resp
        except Exception as e:
            _resp['status'] = '21599'
            _resp['msg'] = str(e)
            if _logger is not None:
                _logger.log(
                    _logging_level,
                    '[EX][interface_id:%s]%s' % (_resp['interface_id'], traceback.format_exc()),
                    extra=_logger_extra
                )
            return _resp

    @FlaskTool.log(get_logger_fun=FlaskServer.get_logger_fun, get_logger_para={'app_name': 'dy_control_server'})
    @FlaskTool.support_object_resp
    def into_app_line(self, methods=['POST'], **kwargs):
        """
        指定设备进入直播间

        @api {post} {json} /api/DyControlApi/into_app_line into_app_line
        @body-in {str} interface_id - 接口id
        @body-in {list} devices - 设备清单, ['设备名', '设备名', ...]

        @body-out {str} interface_id - 接口id
        @body-out {str} status - 处理状态, 定义如下
            00000 - 成功
            21599 - 应用服务处理其他失败
        @body-out {str} msg - 处理状态对应的描述
        @body-out {list} error_info - 进入失败的设备清单和失败信息
            [
                {
                    'device_name': '',
                    'error': ''
                },
                ...
            ]
        @body-out {list} warning_info - 启动成功但自动进入直播间失败的情况
            [
                {
                    'device_name': '',
                    'error': ''
                },
                ...
            ]
        """
        # 日志对象获取
        _logger = kwargs.get('logger', None)
        _logging_level = kwargs.get('logging_level', None)
        _logger_extra = kwargs.get('logger_extra', None)

        # 设置返回的字典
        _interface_id = request.json.get('interface_id', '')
        _resp = {
            'interface_id': _interface_id,
            'status': '00000',
            'msg': '成功',
            'error_info': list(),
            'warning_info': list()
        }
        try:
            # 生成批量任务字典
            self._batch_task[_interface_id] = dict()

            # 逐个进行进入直播间处理
            for _device_name in request.json.get('devices', []):
                if _device_name not in self.devices.keys():
                    _resp['error_info'].append({
                        'device_name': _device_name,
                        'error': '设备不在已添加的清单中'
                    })
                    continue

                # 添加到批量任务 unconnect, connected, started
                if self.devices[_device_name]['connnect_status'] == 'connected':
                    self._batch_task[_interface_id][_device_name] = {
                        'type': 'into_app_line',
                        'para': None
                    }
                elif self.devices[_device_name]['connnect_status'] == 'unconnect':
                    _resp['error_info'].append({
                        'device_name': _device_name,
                        'error': '设备必须先进行连接'
                    })
                    continue

            # 执行批量任务
            self._run_batch_task(
                _interface_id, run_bt_wait=self.para['is_into_wait'],
                min_wait_time=self.para['into_line_wait_min'],
                max_wait_time=self.para['into_line_wait_max']
            )

            # 检查执行结果
            for _device_name in self._batch_task[_interface_id].keys():
                if not self._batch_task[_interface_id][_device_name]['is_success']:
                    _resp['error_info'].append({
                        'device_name': _device_name,
                        'error': self._batch_task[_interface_id][_device_name]['msg']
                    })
                    continue
                elif self._batch_task[_interface_id][_device_name]['msg'] != '成功':
                    # 启动成功, 但是自动进入失败
                    _resp['warning_info'].append({
                        'device_name': _device_name,
                        'error': self._batch_task[_interface_id][_device_name]['msg']
                    })

                # 启动成功，变更状态
                self.devices[_device_name]['connnect_status'] = 'started'

            # 返回结果
            return _resp
        except Exception as e:
            _resp['status'] = '21599'
            _resp['msg'] = str(e)
            if _logger is not None:
                _logger.log(
                    _logging_level,
                    '[EX][interface_id:%s]%s' % (_resp['interface_id'], traceback.format_exc()),
                    extra=_logger_extra
                )
            return _resp
        finally:
            # 删除临时任务清单
            self._batch_task.pop(_interface_id, None)

    @FlaskTool.log(get_logger_fun=FlaskServer.get_logger_fun, get_logger_para={'app_name': 'dy_control_server'})
    @FlaskTool.support_object_resp
    def out_app_line(self, methods=['POST'], **kwargs):
        """
        退出直播间

        @api {post} {json} /api/DyControlApi/out_app_line out_app_line
        @body-in {str} interface_id - 接口id
        @body-in {list} devices - 设备清单, ['设备名', '设备名', ...]

        @body-out {str} interface_id - 接口id
        @body-out {str} status - 处理状态, 定义如下
            00000 - 成功
            21599 - 应用服务处理其他失败
        @body-out {str} msg - 处理状态对应的描述
        @body-out {list} error_info - 断开连接失败的设备清单和失败信息
            [
                {
                    'device_name': '',
                    'error': ''
                },
                ...
            ]
        """
        # 日志对象获取
        _logger = kwargs.get('logger', None)
        _logging_level = kwargs.get('logging_level', None)
        _logger_extra = kwargs.get('logger_extra', None)

        # 设置返回的字典
        _resp = {
            'interface_id': request.json.get('interface_id', ''),
            'status': '00000',
            'msg': '成功',
            'error_info': list()
        }
        try:
            for _device_name in request.json.get('devices', []):
                # 逐个进行退出直播间处理
                if _device_name not in self.devices.keys():
                    _resp['error_info'].append({
                        'device_name': _device_name,
                        'error': '设备不在已添加的清单中'
                    })
                    continue

                if _device_name in self.apps.keys():
                    self._close_app(_device_name)

                # 修改状态
                if self.devices[_device_name]['connnect_status'] == 'started':
                    self.devices[_device_name]['connnect_status'] = 'connected'

            # 返回结果
            return _resp
        except Exception as e:
            _resp['status'] = '21599'
            _resp['msg'] = str(e)
            if _logger is not None:
                _logger.log(
                    _logging_level,
                    '[EX][interface_id:%s]%s' % (_resp['interface_id'], traceback.format_exc()),
                    extra=_logger_extra
                )
            return _resp

    @FlaskTool.log(get_logger_fun=FlaskServer.get_logger_fun, get_logger_para={'app_name': 'dy_control_server'})
    @FlaskTool.support_object_resp
    def app_send_chat(self, methods=['POST'], **kwargs):
        """
        发送聊天文本

        @api {post} {json} /api/DyControlApi/into_app_line into_app_line
        @body-in {str} interface_id - 接口id
        @body-in {list} devices - 设备清单, ['设备名', '设备名', ...]
        @body-in {str} text - 要发送的文本
        @body-in {bool} wait_bt_device - 多人操作是否间隔时间

        @body-out {str} interface_id - 接口id
        @body-out {str} status - 处理状态, 定义如下
            00000 - 成功
            21599 - 应用服务处理其他失败
        @body-out {str} msg - 处理状态对应的描述
        @body-out {list} error_info - 发送失败的设备清单和失败信息
            [
                {
                    'device_name': '',
                    'error': ''
                },
                ...
            ]
        """
        # 日志对象获取
        _logger = kwargs.get('logger', None)
        _logging_level = kwargs.get('logging_level', None)
        _logger_extra = kwargs.get('logger_extra', None)

        # 设置返回的字典
        _interface_id = request.json.get('interface_id', '')
        _resp = {
            'interface_id': _interface_id,
            'status': '00000',
            'msg': '成功',
            'error_info': list()
        }
        try:
            # 生成批量任务字典
            self._batch_task[_interface_id] = dict()

            # 逐个设备进行处理
            for _device_name in request.json.get('devices', []):
                if _device_name not in self.apps.keys():
                    _resp['error_info'].append({
                        'device_name': _device_name,
                        'error': '设备未进入直播间'
                    })
                    continue

                self._batch_task[_interface_id][_device_name] = {
                    'type': 'app_send_chat',
                    'para': request.json['text']
                }

            # 执行批量任务
            self._run_batch_task(
                _interface_id, run_bt_wait=request.json['wait_bt_device'],
                min_wait_time=self.bg_para['send_bt_wait_min'],
                max_wait_time=self.bg_para['send_bt_wait_max']
            )

            # 检查执行结果
            for _device_name in self._batch_task[_interface_id].keys():
                if not self._batch_task[_interface_id][_device_name]['is_success']:
                    _resp['error_info'].append({
                        'device_name': _device_name,
                        'error': self._batch_task[_interface_id][_device_name]['msg']
                    })

            # 返回结果
            return _resp
        except Exception as e:
            _resp['status'] = '21599'
            _resp['msg'] = str(e)
            if _logger is not None:
                _logger.log(
                    _logging_level,
                    '[EX][interface_id:%s]%s' % (_resp['interface_id'], traceback.format_exc()),
                    extra=_logger_extra
                )
            return _resp
        finally:
            # 删除临时任务清单
            self._batch_task.pop(_interface_id, None)

    @FlaskTool.log(get_logger_fun=FlaskServer.get_logger_fun, get_logger_para={'app_name': 'dy_control_server'})
    @FlaskTool.support_object_resp
    def app_send_heart(self, methods=['POST'], **kwargs):
        """
        送小心心

        @api {post} {json} /api/DyControlApi/app_send_heart app_send_heart
        @body-in {str} interface_id - 接口id
        @body-in {list} devices - 设备清单, ['设备名', '设备名', ...]
        @body-in {bool} wait_bt_device - 多人操作是否间隔时间

        @body-out {str} interface_id - 接口id
        @body-out {str} status - 处理状态, 定义如下
            00000 - 成功
            21599 - 应用服务处理其他失败
        @body-out {str} msg - 处理状态对应的描述
        @body-out {list} error_info - 发送失败的设备清单和失败信息
            [
                {
                    'device_name': '',
                    'error': ''
                },
                ...
            ]
        """
        # 日志对象获取
        _logger = kwargs.get('logger', None)
        _logging_level = kwargs.get('logging_level', None)
        _logger_extra = kwargs.get('logger_extra', None)

        # 设置返回的字典
        _interface_id = request.json.get('interface_id', '')
        _resp = {
            'interface_id': _interface_id,
            'status': '00000',
            'msg': '成功',
            'error_info': list()
        }
        try:
            # 生成批量任务字典
            self._batch_task[_interface_id] = dict()

            # 逐个设备进行处理
            for _device_name in request.json.get('devices', []):
                if _device_name not in self.apps.keys():
                    _resp['error_info'].append({
                        'device_name': _device_name,
                        'error': '设备未进入直播间'
                    })
                    continue

                self._batch_task[_interface_id][_device_name] = {
                    'type': 'app_send_heart',
                    'para': None
                }

            # 执行批量任务
            self._run_batch_task(
                _interface_id, run_bt_wait=request.json['wait_bt_device'],
                min_wait_time=self.bg_para['send_bt_wait_min'],
                max_wait_time=self.bg_para['send_bt_wait_max']
            )

            # 检查执行结果
            for _device_name in self._batch_task[_interface_id].keys():
                if not self._batch_task[_interface_id][_device_name]['is_success']:
                    _resp['error_info'].append({
                        'device_name': _device_name,
                        'error': self._batch_task[_interface_id][_device_name]['msg']
                    })

            # 返回结果
            return _resp
        except Exception as e:
            _resp['status'] = '21599'
            _resp['msg'] = str(e)
            if _logger is not None:
                _logger.log(
                    _logging_level,
                    '[EX][interface_id:%s]%s' % (_resp['interface_id'], traceback.format_exc()),
                    extra=_logger_extra
                )
            return _resp
        finally:
            # 删除临时任务清单
            self._batch_task.pop(_interface_id, None)

    @FlaskTool.log(get_logger_fun=FlaskServer.get_logger_fun, get_logger_para={'app_name': 'dy_control_server'})
    @FlaskTool.support_object_resp
    def app_click_car(self, methods=['POST'], **kwargs):
        """
        点击购物车

        @api {post} {json} /api/DyControlApi/app_send_heart app_send_heart
        @body-in {str} interface_id - 接口id
        @body-in {list} devices - 设备清单, ['设备名', '设备名', ...]
        @body-in {bool} wait_bt_device - 多人操作是否间隔时间

        @body-out {str} interface_id - 接口id
        @body-out {str} status - 处理状态, 定义如下
            00000 - 成功
            21599 - 应用服务处理其他失败
        @body-out {str} msg - 处理状态对应的描述
        @body-out {list} error_info - 发送失败的设备清单和失败信息
            [
                {
                    'device_name': '',
                    'error': ''
                },
                ...
            ]
        """
        # 日志对象获取
        _logger = kwargs.get('logger', None)
        _logging_level = kwargs.get('logging_level', None)
        _logger_extra = kwargs.get('logger_extra', None)

        # 设置返回的字典
        _interface_id = request.json.get('interface_id', '')
        _resp = {
            'interface_id': _interface_id,
            'status': '00000',
            'msg': '成功',
            'error_info': list()
        }
        try:
            # 生成批量任务字典
            self._batch_task[_interface_id] = dict()

            # 逐个设备进行处理
            for _device_name in request.json.get('devices', []):
                if _device_name not in self.apps.keys():
                    _resp['error_info'].append({
                        'device_name': _device_name,
                        'error': '设备未进入直播间'
                    })
                    continue

                self._batch_task[_interface_id][_device_name] = {
                    'type': 'app_click_car',
                    'para': None
                }

            # 执行批量任务
            self._run_batch_task(
                _interface_id, run_bt_wait=request.json['wait_bt_device'],
                min_wait_time=self.bg_para['send_bt_wait_min'],
                max_wait_time=self.bg_para['send_bt_wait_max']
            )

            # 检查执行结果
            for _device_name in self._batch_task[_interface_id].keys():
                if not self._batch_task[_interface_id][_device_name]['is_success']:
                    _resp['error_info'].append({
                        'device_name': _device_name,
                        'error': self._batch_task[_interface_id][_device_name]['msg']
                    })

            # 返回结果
            return _resp
        except Exception as e:
            _resp['status'] = '21599'
            _resp['msg'] = str(e)
            if _logger is not None:
                _logger.log(
                    _logging_level,
                    '[EX][interface_id:%s]%s' % (_resp['interface_id'], traceback.format_exc()),
                    extra=_logger_extra
                )
            return _resp
        finally:
            # 删除临时任务清单
            self._batch_task.pop(_interface_id, None)

    @FlaskTool.log(get_logger_fun=FlaskServer.get_logger_fun, get_logger_para={'app_name': 'dy_control_server'})
    @FlaskTool.support_object_resp
    def app_give_thumbs_up(self, methods=['POST'], **kwargs):
        """
        点赞

        @api {post} {json} /api/DyControlApi/app_give_thumbs_up app_give_thumbs_up
        @body-in {str} interface_id - 接口id
        @body-in {list} devices - 设备清单, ['设备名', '设备名', ...]
        @body-in {bool} wait_bt_device - 多人操作是否间隔时间
        @body-in {float} seconds - 要点赞的时长，单位为秒

        @body-out {str} interface_id - 接口id
        @body-out {str} status - 处理状态, 定义如下
            00000 - 成功
            21599 - 应用服务处理其他失败
        @body-out {str} msg - 处理状态对应的描述
        @body-out {list} error_info - 发送失败的设备清单和失败信息
            [
                {
                    'device_name': '',
                    'error': ''
                },
                ...
            ]
        """
        # 日志对象获取
        _logger = kwargs.get('logger', None)
        _logging_level = kwargs.get('logging_level', None)
        _logger_extra = kwargs.get('logger_extra', None)

        # 设置返回的字典
        _interface_id = request.json.get('interface_id', '')
        _resp = {
            'interface_id': _interface_id,
            'status': '00000',
            'msg': '成功',
            'error_info': list()
        }
        try:
            # 生成批量任务字典
            self._batch_task[_interface_id] = dict()

            # 逐个设备进行处理
            for _device_name in request.json.get('devices', []):
                if _device_name not in self.apps.keys():
                    _resp['error_info'].append({
                        'device_name': _device_name,
                        'error': '设备未进入直播间'
                    })
                    continue

                self._batch_task[_interface_id][_device_name] = {
                    'type': 'app_give_thumbs_up',
                    'para': request.json.get('seconds', 5.0)
                }

            # 执行批量任务
            self._run_batch_task(
                _interface_id, run_bt_wait=request.json['wait_bt_device'],
                min_wait_time=self.bg_para['send_bt_wait_min'],
                max_wait_time=self.bg_para['send_bt_wait_max']
            )

            # 检查执行结果
            for _device_name in self._batch_task[_interface_id].keys():
                if not self._batch_task[_interface_id][_device_name]['is_success']:
                    _resp['error_info'].append({
                        'device_name': _device_name,
                        'error': self._batch_task[_interface_id][_device_name]['msg']
                    })

            # 返回结果
            return _resp
        except Exception as e:
            _resp['status'] = '21599'
            _resp['msg'] = str(e)
            if _logger is not None:
                _logger.log(
                    _logging_level,
                    '[EX][interface_id:%s]%s' % (_resp['interface_id'], traceback.format_exc()),
                    extra=_logger_extra
                )
            return _resp
        finally:
            # 删除临时任务清单
            self._batch_task.pop(_interface_id, None)

    @FlaskTool.log(get_logger_fun=FlaskServer.get_logger_fun, get_logger_para={'app_name': 'dy_control_server'})
    @FlaskTool.support_object_resp
    def app_tap_screen(self, methods=['POST'], **kwargs):
        """
        点击屏幕

        @api {post} {json} /api/DyControlApi/app_tap_screen app_tap_screen
        @body-in {str} interface_id - 接口id
        @body-in {list} devices - 设备清单, ['设备名', '设备名', ...]
        @body-in {bool} wait_bt_device - 多人操作是否间隔时间

        @body-out {str} interface_id - 接口id
        @body-out {str} status - 处理状态, 定义如下
            00000 - 成功
            21599 - 应用服务处理其他失败
        @body-out {str} msg - 处理状态对应的描述
        @body-out {list} error_info - 发送失败的设备清单和失败信息
            [
                {
                    'device_name': '',
                    'error': ''
                },
                ...
            ]
        """
        # 日志对象获取
        _logger = kwargs.get('logger', None)
        _logging_level = kwargs.get('logging_level', None)
        _logger_extra = kwargs.get('logger_extra', None)

        # 设置返回的字典
        _interface_id = request.json.get('interface_id', '')
        _resp = {
            'interface_id': _interface_id,
            'status': '00000',
            'msg': '成功',
            'error_info': list()
        }
        try:
            # 生成批量任务字典
            self._batch_task[_interface_id] = dict()

            # 逐个设备进行处理
            for _device_name in request.json.get('devices', []):
                if _device_name not in self.apps.keys():
                    _resp['error_info'].append({
                        'device_name': _device_name,
                        'error': '设备未进入直播间'
                    })
                    continue

                self._batch_task[_interface_id][_device_name] = {
                    'type': 'app_tap_screen',
                    'para': None
                }

            # 执行批量任务
            self._run_batch_task(
                _interface_id, run_bt_wait=request.json['wait_bt_device'],
                min_wait_time=self.bg_para['send_bt_wait_min'],
                max_wait_time=self.bg_para['send_bt_wait_max']
            )

            # 检查执行结果
            for _device_name in self._batch_task[_interface_id].keys():
                if not self._batch_task[_interface_id][_device_name]['is_success']:
                    _resp['error_info'].append({
                        'device_name': _device_name,
                        'error': self._batch_task[_interface_id][_device_name]['msg']
                    })

            # 返回结果
            return _resp
        except Exception as e:
            _resp['status'] = '21599'
            _resp['msg'] = str(e)
            if _logger is not None:
                _logger.log(
                    _logging_level,
                    '[EX][interface_id:%s]%s' % (_resp['interface_id'], traceback.format_exc()),
                    extra=_logger_extra
                )
            return _resp
        finally:
            # 删除临时任务清单
            self._batch_task.pop(_interface_id, None)

    #############################
    # 需要置为API黑名单的函数
    #############################

    #############################
    # ADB的内部处理函数
    #############################

    def _get_connected_devices(self) -> dict:
        """
        获取已经连接上的设备清单字典

        @returns {dict} - 设备清单字典
            {
                '设备名称': {
                    ...
                },
                ...
            }
        """
        _devices = dict()
        _cmd = '%s devices -l' % self.para['adb']
        _code, _info = self._exec_sys_cmd(_cmd)
        if _code != 0:
            raise RuntimeError('run sys cmd [%s] error: %s' % (str(_code), '\n'.join(_info)))

        for _str in _info:
            if not _str.startswith('List of'):
                # 找到设备连接号
                _device_name = (_str[0: _str.find(' ')]).strip()

                if _device_name == '':
                    # 非法数据，不处理
                    continue

                # 获取设备信息
                _devices[_device_name] = self._get_device_info(_device_name)

        # 返回结果字典
        return _devices

    def _get_device_info(self, device_name: str) -> dict:
        """
        获取设备信息

        @param {str} device_name - 设备名称（注意需已连接adb）

        @returns {dict} - 设备信息字典, 注意如果没有连接上也能正常返回，只是相应key值不存在
            {
                'device_name': '',  # 设备名称
                'platform_name': 'Android',  # 手机平台名
                'platform_version': '',  # 手机平台版本
                'wlan_ip': '',  # 手机连接的 wifi ip
                'wlan_port': '',  # 手机连接的 wifi 端口
                'brand': '',  # 手机的品牌
                'model': ''  # 手机的产品名称
                'app_version': '',  # app版本
            }
        """
        _device_info = {
            'device_name': device_name,
            'platform_name': 'Android'
        }

        # 获取版本
        _platform_version = ''
        _cmd = '%s -s %s shell getprop ro.build.version.release' % (self.para['adb'], device_name)
        _code, _cmd_info = self._exec_sys_cmd(_cmd)
        if _code == 0:
            _platform_version = _cmd_info[0]
        _device_info['platform_version'] = _platform_version

        # 获取手机厂商品牌
        _brand = ''
        _cmd = '%s -s %s shell getprop ro.product.brand' % (self.para['adb'], device_name)
        _code, _cmd_info = self._exec_sys_cmd(_cmd)
        if _code == 0:
            _brand = _cmd_info[0]
        _device_info['brand'] = _brand

        # 获取手机产品名称
        _model = ''
        _cmd = '%s -s %s shell getprop ro.product.model' % (self.para['adb'], device_name)
        _code, _cmd_info = self._exec_sys_cmd(_cmd)
        if _code == 0:
            _model = _cmd_info[0]
        _device_info['model'] = _model

        # 获取WIFI地址
        _wlan_ip = ''
        _cmd = '%s -s %s shell ifconfig wlan0' % (self.para['adb'], device_name)
        _code, _cmd_info = self._exec_sys_cmd(_cmd)
        if _code == 0:
            for _line in _cmd_info:
                _line = _line.strip()
                if _line.startswith('inet addr:'):
                    _temp_len = len('inet addr:')
                    _wlan_ip = _line[_temp_len: _line.find(' ', _temp_len)]
                    break
        _device_info['wlan_ip'] = _wlan_ip

        # app版本
        _device_info['app_version'] = self._get_app_version(device_name)

        return _device_info

    def _get_devices_from_db(self):
        """
        从数据库获取设备清单并更新到信息字典
        """
        _fetchs = self._exec_sql(
            'select %s from t_device_list' % ','.join(self._devices_col_list),
            is_fetchall=True
        )
        _col_num = len(self._devices_col_list)
        for _row in _fetchs:
            _info = dict()
            for _index in range(_col_num):
                # 将行数组转换为字典
                _col_name = self._devices_col_list[_index]
                _info[_col_name] = _row[_index]
                if _col_name in self._devices_col_type.keys():
                    _info[_col_name] = self._dbtype_to_python(
                        _info[_col_name], self._devices_col_type[_col_name]
                    )

            # 存入内存字典
            self.devices[_info['device_name']] = _info

    def _update_db_device(self, device_info: dict):
        """
        更新或添加设备信息到数据库

        @param {dict} device_info - 要添加的设备信息字典
        """
        # 设置默认值
        _device_info = {
            'platform_name': 'Android',  # 手机平台名
            'platform_version': '',  # 手机平台版本
            'use_wifi': False,  # 是否使用wifi连接方式
            'wlan_ip': '',  # 手机连接的 wifi ip
            'wlan_port': '',  # 手机连接的 wifi 端口
            'brand': '',  # 手机的品牌
            'model': '',  # 手机的产品名称
            'use_anonymous': False,  # 是否使用匿名
            'user_name': '',  # 绑定的抖音用户
            'remark': '',  # 备注信息
            'app_version': '',  # app版本
            'connnect_status': 'unconnect'  # 连接状态, unconnect, connected, started
        }
        _device_info.update(device_info)
        _device_name = _device_info['device_name']

        # 更新至内存变量参数
        if _device_name in self.devices.keys():
            self.devices[_device_name].update(_device_info)
        else:
            self.devices[_device_name] = _device_info

        # 更新至数据库
        _para = list()
        _holder = list()
        for _index in range(len(self._devices_col_list)):
            _holder.append('?')
            _col_name = self._devices_col_list[_index]
            if _col_name in self._devices_col_type.keys():
                _para.append(
                    self._python_to_dbtype(
                        self.devices[_device_name][_col_name], self._devices_col_type[_col_name]
                    )
                )
            else:
                _para.append(self.devices[_device_name][_col_name])

        self._exec_sql(
            "replace into t_device_list(" + ','.join(self._devices_col_list) +
            ") values(" + ','.join(_holder) + ")",
            para=_para
        )

    def _remove_db_device(self, device_name: str):
        """
        删除指定设备

        @param {str} device_name - 设备名称
        """
        if device_name not in self.devices.keys():
            # 设备本来就不存在
            return

        # 先移除应用
        self._close_app(device_name)

        # 再删除数据库
        self._exec_sql(
            "delete from t_device_list where device_name=?",
            para=(device_name,)
        )

        # 再删除清单
        self.devices.pop(device_name, None)

    def _reflesh_devices_status(self):
        """
        更新设备列表中每个设备的状态
        """
        # 先获取已连接的设备清单
        _connected_devices = self._get_connected_devices()

        # 逐个检查并刷新连接状态
        for _device_name in self.devices.keys():
            if _device_name in _connected_devices.keys():
                # 更新值和状态, 需要判断wifi连接模式, 删除掉自动获取的IP和端口等信息
                if self.devices[_device_name]['use_wifi']:
                    _connected_devices[_device_name].pop('use_wifi', None)
                    _connected_devices[_device_name].pop('wlan_ip', None)
                    _connected_devices[_device_name].pop('wlan_port', None)

                # 删除抖音用户信息的更新
                _connected_devices[_device_name].pop('use_anonymous', None)
                _connected_devices[_device_name].pop('user_name', None)
                _connected_devices[_device_name].pop('remark', None)

                self.devices[_device_name].update(_connected_devices[_device_name])
                if self.devices[_device_name].get('connnect_status', 'unconnect') != 'started':
                    self.devices[_device_name]['connnect_status'] = 'connected'
            else:
                self.devices[_device_name]['connnect_status'] = 'unconnect'

    def _connect_device(self, device_name: str, use_wifi: bool = False, wlan_ip: str = '', wlan_port: str = '') -> dict:
        """
        连接指定设备

        @param {str} device_name - 要连接的设备名称
        @param {bool} use_wifi=False - 是否通过wifi连接
        @param {str} wlan_ip='' - wifi ip
        @param {str} wlan_port='' - wifi port

        @returns {dict} - 返回已连接设备的信息字典

        @throws {RuntimeError} - 连接失败抛出异常
        """
        # 内部复用函数定义
        def _adb_connect_by_name(dname, err_raise=False):
            _cmd = '%s connect %s' % (self.para['adb'], dname)
            _code, _back = self._exec_sys_cmd(_cmd)
            if _code != 0:
                raise RuntimeError('run sys cmd error[%s]: %s' % (str(_code), '\n'.join(_back)))

            # 检查连接成功结果
            if not(_back[0].startswith('connected') or _back[0].startswith('already connected')):
                if err_raise:
                    # 失败抛出异常
                    raise RuntimeError('connect error[%s]: %s' % (str(_code), '\n'.join(_back)))
                else:
                    return False

            # 连接成功
            return True

        # 进行连接
        if not use_wifi:
            # USB方式连接
            _adb_connect_by_name(device_name, err_raise=True)
            _devices_new_name = device_name
        else:
            # WIFI方式连接, 先尝试直接连接IP
            _devices_new_name = '%s:%s' % (wlan_ip, str(wlan_port))
            _conn_result = _adb_connect_by_name(_devices_new_name, err_raise=False)
            if not _conn_result:
                # 直接连接失败, 重新按步骤连接
                _adb_connect_by_name(device_name, err_raise=True)
                _cmd = '%s -s %s tcpip %s' % (self.para['adb'], device_name, str(wlan_port))
                self._exec_sys_cmd(_cmd)

                # 再连接一次
                _adb_connect_by_name(_devices_new_name, err_raise=True)

        # 连接成功, 获取设备信息
        _info = self._get_device_info(_devices_new_name)
        _info['use_wifi'] = use_wifi
        if use_wifi:
            # IP和端口使用传入的值
            _info['wlan_ip'] = wlan_ip
            _info['wlan_port'] = wlan_port

        # 返回结果
        return _info

    def _disconnect_device(self, device_name: str):
        """
        断开设备连接

        @param {str} device_name - 要断开连接的设备名称

        @throws {RuntimeError} - 连接失败抛出异常
        """
        # 先移除应用
        self._close_app(device_name)

        # 执行断开连接命令
        _cmd = '%s disconnect %s' % (self.para['adb'], device_name)
        _code, _back = self._exec_sys_cmd(_cmd)
        if _code != 0:
            raise RuntimeError('run sys cmd error[%s]: %s' % (str(_code), '\n'.join(_back)))

        # 检查连接成功结果
        if not(_back[0].startswith('disconnected') or _back[0].startswith('error: no such device')):
            # 失败抛出异常
            raise RuntimeError('connect error[%s]: %s' % (str(_code), '\n'.join(_back)))

    def _load_script_version_mapping(self):
        """
        加载版本和脚本文件的映射
        """
        self._version_script_mapping = json.loads(
            self.para['android_script_version_mapping']
        )
        self._script_info = dict()
        for _file in self._version_script_mapping.values():
            _json_file = os.path.join(self.config_path, _file)
            with open(_json_file, 'r', encoding='utf8') as _f:
                _json = _f.read()
                _json = _json.replace('{$=直播间=$}', self.bg_para['line_name'])
                self._script_info[_file] = json.loads(_json)

    def _get_mapping_file_by_version(self, ver: str) -> str:
        """
        通过版本号获取脚本映射文件

        @param {str} ver - 版本号

        @returns {str} - 返回匹配到的配置文件名
        """
        for _key in self._version_script_mapping.keys():
            _regex = '^' + _key.replace('.', '\\.').replace('*', '.*') + '$'
            _match = re.match(_regex, ver)
            if _match is not None:
                return self._version_script_mapping[_key]

        # 没有找到，返回第一个
        return self._version_script_mapping.values()[0]

    #############################
    # 抖音控制的内部函数
    #############################
    def _install_app(self, device_name: str):
        """
        安装APP

        @param {str} device_name - 要安装到的设备号
        """
        _apks = self.para['android_apk'].split(',')
        for _apk in _apks:
            if _apk == '':
                continue

            _path = os.path.abspath(
                os.path.join(self.config_path, _apk)
            )
            _cmd = '%s -s %s install -r %s' % (
                self.para['adb'], device_name, _path
            )
            _code, _back = self._exec_sys_cmd(_cmd)
            if _code != 0:
                raise RuntimeError('run sys cmd error[%s]: %s' % (str(_code), '\n'.join(_back)))

            if len(_back) <= 1 or not _back[1].startswith('Success'):
                raise RuntimeError('install error[%s]: %s' % (str(_code), '\n'.join(_back)))

    def _get_app_version(self, device_name: str) -> str:
        """
        获取抖音应用版本

        @param {str} device_name - 设备名

        @returns {str} - 版本号，找不到返回''
        """
        _version = ''
        _para_name = 'versionName'
        _cmd = '%s -s %s shell pm dump %s | %s "%s"' % (
            self.para['adb'], device_name, self.para['android_appPackage'],
            'findstr' if sys.platform == 'win32' else 'grep',
            _para_name
        )
        _code, _back = self._exec_sys_cmd(_cmd)
        if _code == 0:
            _temp = _back[0].strip()
            if _temp.startswith(_para_name):
                _version = _temp[len(_para_name) + 1:]

        return _version

    def _close_app(self, device_name: str):
        """
        停止应用控制

        @param {str} device_name - 要停止的设备名
        """
        _app = self.apps.pop(device_name, None)
        if _app is not None:
            # 检查是否要恢复输入法
            if _app.get('default_ime', None) is not None:
                try:
                    _app['app'].adb_set_default_ime(_app['default_ime'])
                except:
                    pass

            # 删除应用
            _app['app'].__del__()
            del _app['app']

    def _start_app(self, device_name: str, activit_type: str):
        """
        启动APP控制

        @param {str} device_name - 设备名
        @param {str} activit_type - 页面类型
            line - 直播
            user_name - 用户名称

        @throws {RuntimeError} - App已启动或设备名不在清单，将抛出异常
        """
        # 检查当前是否允许启动
        if device_name in self.apps.keys():
            raise RuntimeError('设备[%s]正被控制中, 请先关闭直播或等待控制结束！' % device_name)
        if device_name not in self.devices.keys():
            raise RuntimeError('设备名[%s]不在设备清单中！' % device_name)

        # 启动app
        _device_info = self.devices[device_name]
        _desired_caps = json.loads(self.para['android_desired_caps'])  # 启动参数
        _desired_caps.update({
            'platformName': _device_info['platform_name'],
            'platformVersion': _device_info['platform_version'],
            'deviceName': device_name,
            'appPackage': self.para['android_appPackage'],
            'appActivity': self.para['android_appActivity'],
        })

        _app = AndroidDevice(
            appium_server=self.para['appium_server'],
            desired_caps=_desired_caps
        )

        # 设置元素查找等待时长
        _app.implicitly_wait(self.para['implicitly_wait'])

        # 启动通过，加入字典
        self.apps[device_name] = {
            'app': _app,
            'app_package': self.para['android_appPackage'],
            'activit_type': activit_type,
            'app_version': _device_info['app_version'],
            'script': self._script_info[self._get_mapping_file_by_version(_device_info['app_version'])]
        }

    def _get_app_user(self, device_name: str) -> str:
        """
        获取抖音用户名

        @param {str} device_name - 设备名称

        @returns {str} - 返回抖音用户名
        """
        _user_name = ''
        # 启动应用
        self._start_app(device_name, activit_type='user_name')

        # 查找用户昵称
        _steps = self.apps[device_name]['script']['android_user_getName_script']
        try:
            _el = self._exec_appium_steps(device_name, _steps)
            _user_name = _el.text
        except:
            pass

        # 关闭应用
        self._close_app(device_name)

        return _user_name

    def _into_app_line_batch_fun(self, device_name: str, para):
        """
        进入直播的批量线程操作函数

        @param {str} device_name - 设备名称
        @param {object} para - 执行参数

        @returns {tuple(bool, msg)} - 返回处理结果，(是否成功, 结果信息)
        """
        # 先启动APP
        self._start_app(device_name, 'line')

        # 保存默认输入法
        self.apps[device_name]['default_ime'] = self.apps[device_name]['app'].adb_get_default_ime()

        # 设置输入法为 AdbKeyboard
        self.apps[device_name]['app'].adb_set_adbime()

        # 尝试自动进入直播间
        if self.para['auto_into_line']:
            try:
                _steps = self.apps[device_name]['script']['android_line_script']
                # 执行进入操作
                self._exec_appium_steps(device_name, _steps)
            except Exception as e:
                if self.para['into_line_err_exit']:
                    # 进入失败自动退出
                    self._close_app(device_name)
                    return (False, str(e))
                else:
                    # 进入失败不退出，允许手工进入
                    return (True, '失败: %s' % str(e))

        return (True, '成功')

    def _app_send_chat_batch_fun(self, device_name: str, para):
        """
        发送聊天的批量线程操作函数

        @param {str} device_name - 设备名称
        @param {object} para - 要发送的文本

        @returns {tuple(bool, msg)} - 返回处理结果，(是否成功, 结果信息)
        """
        _app_info = self.apps[device_name]
        _app: AndroidDevice = _app_info['app']
        _current_activity = _app.current_activity_adb
        if _current_activity not in self.para['android_line_appActivity'].split('|'):
            raise RuntimeError('当前[%s]不在直播间，请先手工进入直播间！' % _current_activity)

        # 尝试获取位置信息
        if 'chat_obj_pos' not in _app_info.keys():
            _chat_obj_steps = _app_info['script']['android_chat_obj_script']
            _chat_obj = self._exec_appium_steps(device_name, _chat_obj_steps)
            _rect = _chat_obj.rect
            _app_info['chat_obj_pos'] = [
                _rect[0] + 10, _rect[1] + math.ceil(_rect[3] / 2.0)  # 靠左边点击
            ]

        # 执行点击动作
        _app.tap_adb(x=_app_info['chat_obj_pos'][0], y=_app_info['chat_obj_pos'][1], count=1)

        # 等待1秒，让输入框跳出来
        time.sleep(self.para['android_chat_wait_input'])

        # 发送内容
        _app.adb_keyboard_text(para)

        if 'chat_send_pos' not in _app_info.keys():
            _chat_send_steps = _app_info['script']['android_chat_send_script']
            _chat_send = self._exec_appium_steps(device_name, _chat_send_steps)
            _rect = _chat_send.rect
            _app_info['chat_send_pos'] = [
                _rect[0] + 10, _rect[1] + math.ceil(_rect[3] / 2.0)  # 靠左边点击
            ]

        # 执行发送点击动作
        _app.tap_adb(x=_app_info['chat_send_pos'][0], y=_app_info['chat_send_pos'][1], count=1)

        return (True, '成功')

    def _app_send_heart_batch_fun(self, device_name: str, para):
        """
        送小心心的批量线程操作函数

        @param {str} device_name - 设备名称
        @param {object} para - 参数

        @returns {tuple(bool, msg)} - 返回处理结果，(是否成功, 结果信息)
        """
        _app_info = self.apps[device_name]
        _app: AndroidDevice = _app_info['app']
        _current_activity = _app.current_activity_adb
        if _current_activity not in self.para['android_line_appActivity'].split('|'):
            raise RuntimeError('当前[%s]不在直播间，请先手工进入直播间！' % _current_activity)

        # 先尝试获取直播室的发言位置对象, 点击
        _heart_obj = _app_info.get('heart_obj', None)
        _heart_obj_steps = _app_info['script']['android_heart_script']
        try:
            if _heart_obj is None:
                _heart_obj = self._exec_appium_steps(device_name, _heart_obj_steps)
            # 执行点击操作
            _heart_obj.click()
        except:
            # 出现异常做多一次, 先点击一下屏幕中间，尝试恢复正常界面
            print('get heart_obj exception: %s' % traceback.format_exc())
            _heart_obj = self._exec_appium_steps(device_name, _heart_obj_steps)
            _heart_obj.click()

        # 成功执行，保留对象提升速度
        _app_info['heart_obj'] = _heart_obj

        return (True, '成功')

    def _app_click_car_batch_fun(self, device_name: str, para):
        """
        点击购物车的批量线程操作函数

        @param {str} device_name - 设备名称
        @param {object} para - 参数

        @returns {tuple(bool, msg)} - 返回处理结果，(是否成功, 结果信息)
        """
        _app_info = self.apps[device_name]
        _app: AndroidDevice = _app_info['app']
        _current_activity = _app.current_activity_adb
        if _current_activity not in self.para['android_line_appActivity'].split('|'):
            raise RuntimeError('当前[%s]不在直播间，请先手工进入直播间！' % _current_activity)

        # 先尝试获取直播室的发言位置对象, 点击
        _heart_obj = _app_info.get('car_obj', None)
        _heart_obj_steps = _app_info['script']['android_car_script']
        try:
            if _heart_obj is None:
                _heart_obj = self._exec_appium_steps(device_name, _heart_obj_steps)
            # 执行点击操作
            _heart_obj.click()
        except:
            # 出现异常做多一次, 先点击一下屏幕中间，尝试恢复正常界面
            print('get car_obj exception: %s' % traceback.format_exc())
            _heart_obj = self._exec_appium_steps(device_name, _heart_obj_steps)
            _heart_obj.click()

        # 成功执行，保留对象提升速度
        _app_info['car_obj'] = _heart_obj

        return (True, '成功')

    def _app_give_thumbs_up_batch_fun(self, device_name: str, para):
        """
        点赞的批量线程操作函数

        @param {str} device_name - 设备名称
        @param {object} para - 点赞的时长

        @returns {tuple(bool, msg)} - 返回处理结果，(是否成功, 结果信息)
        """
        # 计算中心点，减少每次点击的计算量
        _app_info = self.apps[device_name]
        _app: AndroidDevice = _app_info['app']
        _current_activity = _app.current_activity_adb
        if _current_activity not in self.para['android_line_appActivity'].split('|'):
            raise RuntimeError('当前[%s]不在直播间，请先手工进入直播间！' % _current_activity)

        if _app_info.get('size', None) is None:
            _app_info['size'] = _app.size_adb

        # 计算点击位置
        _x = math.ceil(_app_info['size'][0] / 2.0)
        _y = math.ceil(_app_info['size'][1] / 2.0)
        _x = _x + math.ceil(_app_info['size'][0] * self.para['give_thumbs_up_offset_x'])
        _y = _y + math.ceil(_app_info['size'][1] * self.para['give_thumbs_up_offset_y'])

        # 生成随机点击种子
        _random_x = None
        if self.para['give_thumbs_up_random_x'] > 0:
            _random_x = math.ceil(_app_info['size'][0] * self.para['give_thumbs_up_random_x'])
        _random_y = None
        if self.para['give_thumbs_up_random_y'] > 0:
            _random_y = math.ceil(_app_info['size'][1] * self.para['give_thumbs_up_random_y'])

        _pos_seed = list()
        for i in range(self.para['give_thumbs_up_random_seed']):
            _pos_seed.append((
                _x + math.ceil(random.uniform(0 - _random_x, _random_x)),
                _y + math.ceil(random.uniform(0 - _random_y, _random_y))
            ))

        # 执行点击操作
        _app.tap_adb_continuity(_pos_seed, para, thread_count=self.para['give_thumbs_up_tap_max'])

        return (True, '成功')

    def _app_tap_screen_batch_fun(self, device_name: str, para):
        """
        点击屏幕的批量线程操作函数

        @param {str} device_name - 设备名称
        @param {object} para - 暂时没有用

        @returns {tuple(bool, msg)} - 返回处理结果，(是否成功, 结果信息)
        """
        # 计算位置
        _app_info = self.apps[device_name]
        _app: AndroidDevice = _app_info['app']
        _current_activity = _app.current_activity_adb
        if _current_activity not in self.para['android_line_appActivity'].split('|'):
            raise RuntimeError('当前[%s]不在直播间，请先手工进入直播间！' % _current_activity)

        if _app_info.get('size', None) is None:
            _app_info['size'] = _app.size_adb

        _pos = self.bg_para['tap_to_main'].split(',')
        _x = math.ceil(_app_info['size'][0] * float(_pos[0]))
        _y = math.ceil(_app_info['size'][1] * float(_pos[1]))

        # 点击处理
        _app.tap_adb(x=_x, y=_y)

        return (True, '成功')

    #############################
    # 通用的批量任务内部函数
    #############################

    def _run_batch_task(self, interface_id: str, run_bt_wait: bool = False,
                        min_wait_time: float = 0.0, max_wait_time: float = 1.0):
        """
        按接口id多线程执行批量任务

        @param {str} interface_id - 要执行的接口ID
        @param {bool} run_bt_wait=False - 任务执行之间是否要间隔时长
        @param {float} min_wait_time=0.0 - 间隔最小等待时长, 单位为秒
        @param {float} max_wait_time=1.0 - 间隔最大等待时长, 单位为秒
        """
        _devices = list(self._batch_task.get(interface_id, {}).keys())
        _task_num = len(_devices)
        if _task_num == 0:
            # 没有任务，直接返回
            return
        elif _task_num == 1:
            # 只有一个任务，当前函数执行即可
            self._batch_task_thread_fun(interface_id, _devices[0])
            return

        # 启动多线程执行
        for _device_name in _devices:
            # 每个设备启动一条新线程
            _running_thread = threading.Thread(
                target=self._batch_task_thread_fun,
                name='Thread-Batch-Running %s' % interface_id,
                args=(interface_id, _device_name)
            )
            _running_thread.setDaemon(True)
            _running_thread.start()

            # 间隔随机时间
            if run_bt_wait:
                _time = random.uniform(min_wait_time, max_wait_time)
                time.sleep(_time)

        # 等待多线程的处理结果
        while True:
            _is_end = True
            for _device_name in _devices:
                if self._batch_task[interface_id][_device_name].get('is_success', None) is None:
                    _is_end = False
                    break

            # 检查是否可以退出
            if _is_end:
                break
            else:
                time.sleep(0.01)

    def _batch_task_thread_fun(self, interface_id: str, device_name: str):
        """
        执行批量任务的通用线程函数

        @param {str} interface_id - 接口ID
        @param {str} device_name - 设备名称
        """
        try:
            # 执行具体的逻辑代码
            _info = self._batch_task[interface_id][device_name]
            _is_success, _msg = self._batch_fun_mapping[
                _info['type']
            ](device_name, _info['para'])

            # 更新结果
            self._batch_task[interface_id][device_name]['is_success'] = _is_success
            self._batch_task[interface_id][device_name]['msg'] = _msg
        except Exception as e:
            self._batch_task[interface_id][device_name]['is_success'] = False
            self._batch_task[interface_id][device_name]['msg'] = str(e)

    #############################
    # 内部函数
    #############################

    def _exec_sql(self, sql: str, para: tuple = None, is_fetchall: bool = False):
        """
        执行指定SQL

        @param {str} sql - 要执行的SQL
        @param {tuple} para=None - 传入的SQL参数字典(支持?占位)
        @param {bool} is_fetchall=False - 是否返回执行结果数据

        @param {list} - 如果is_fetchall为True则返回fetchall获取的结果数据, 否则返回None
        """
        self._db_lock.acquire()
        _cursor = self.db_conn.cursor()
        try:
            if para is None:
                _cursor.execute(sql)
            else:
                _cursor.execute(sql, para)

            # 是否查询结果
            if is_fetchall:
                return _cursor.fetchall()
            else:
                # 非查询语句要提交
                self.db_conn.commit()
                return None
        finally:
            _cursor.close()
            self._db_lock.release()

    def _dbrows_to_para(self, fetchs, para: dict):
        """
        通用的将数据库查询记录存入字典的函数

        @param {list} fetchs - fetchall 获取的行数组
        @param {dict} para - 要存入的参数字典
        """
        for _item in fetchs:
            if _item[1] == 'bool':
                # python boo 和 str 的转换不能使用 bool('False') 的方式
                para[_item[0]] = (_item[2] == 'True')
            elif _item[1] == 'str':
                para[_item[0]] = _item[2]
            else:
                para[_item[0]] = eval('%s("%s")' % (_item[1], _item[2]))

    def _dbtype_to_python(self, val, type_str: str = None):
        """
        转换数据库类型为Python类型

        @param {object} val - 数据库存储值
        @param {str} type_str=None - 转换类型
            'bool' - 布尔值

        @returns {object} - 转换后的值
        """
        _val = val
        if type_str == 'bool':
            _val = (val == 'true')

        return _val

    def _python_to_dbtype(self, val, type_str: str = None):
        """
        转换python类型为数据库类型

        @param {object} val - 数据库存储值
        @param {str} type_str=None - 转换类型
            'bool' - 布尔值

        @returns {object} - 转换后的值
        """
        _val = val
        if type_str == 'bool':
            _val = 'true' if val else 'false'

        return _val

    def _update_db_para(self, para: dict, table_name: str):
        """
        将参数更新回数据库

        @param {dict} para - 参数字典
        @param {str} table_name - 要刷回的数据库名
        """
        for _key, _value in para.items():
            self._exec_sql(
                "replace into %s values(?, ?, ?)" % table_name,
                para=(_key, type(_value).__name__, str(_value))
            )

    def _exec_sys_cmd(self, cmd: str, shell_encoding: str = None):
        """
        执行系统命令

        @param {str} cmd - 要执行的命令
        @param {str} shell_encoding=None - 传入指定的编码

        @returns {(int, list)} - 返回命令执行结果数组, 第一个为 exit_code, 0代表成功; 第二个为输出信息行数组
        """
        _shell_encoding = self.para['shell_encoding'] if shell_encoding is None else shell_encoding
        _sp = subprocess.Popen(
            cmd, close_fds=True,
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            shell=True
        )

        # 循环等待执行完成
        _exit_code = None
        _info = list()  # 数据出信息的行数组
        while True:
            # 获取输出信息
            _info.append(_sp.stdout.readline().decode(
                _shell_encoding).replace('\r', '').replace('\n', ''))

            _exit_code = _sp.poll()
            if _exit_code is not None:
                # 结束，打印异常日志
                _info.append(_sp.stdout.read().decode(
                    _shell_encoding).replace('\r', '').replace('\n', ''))
                if _exit_code != 0:
                    _info.append(_sp.stdout.read().decode(
                        _shell_encoding).replace('\r', '').replace('\n', ''))

                break

            # 释放一下CPU
            time.sleep(0.01)

        return (_exit_code, _info)

    def _exec_appium_steps(self, device_name: str, steps: list, init_el: AndroidElement = None):
        """
        执行appium的步骤脚本

        @param {str} device_name - 设备名称
        @param {list} steps - 步骤脚本数组
        @param {AndroidElement} first_el=None - 开始执行的元素对象

        @returns {AndroidElement} - 返回执行结果元素
        """
        if device_name not in self.apps.keys():
            raise RuntimeError('设备名[%s]不在设备清单中！' % device_name)

        _app = self.apps[device_name]['app']
        _init_el = init_el
        for _script in steps:
            # 逐步执行
            try:
                _init_el = self._exec_appium_script(_app, _script, _init_el)
            except Exception as e:
                raise RuntimeError('%s: %s' % (_script.get('tips', ''), str(e)))

        # 返回执行结果
        return _init_el

    def _exec_appium_script(self, app: AndroidDevice, script: dict, init_el: AndroidElement):
        """
        执行

        @param {AndroidDevice} app - 已连接的设备对象
        @param {dict} script - 脚本字典
        @param {AndroidElement} init_el - 初始化元素

        @returns {AndroidElement} - 返回执行结果元素
        """
        _end_el = init_el
        if script['action'] in ('find', 'subfind'):
            # 处理参数
            if 'id' in script.keys():
                _by = MobileBy.ID
                _value = script['id']
            elif 'image' in script.keys():
                _by = MobileBy.IMAGE
                _value = script['image']
            else:
                _by = MobileBy.XPATH
                _value = script.get('xpath', None)

            # 查找对象
            _pos = script.get('pos', None)
            if _pos is None:
                # 查找单一对象
                if script['action'] == 'subfind':
                    # 子查询
                    _end_el = init_el.find_element(by=_by, value=_value)
                else:
                    # 当前页面查询
                    _end_el = app.find_element(by=_by, value=_value)
            else:
                # 查找多个对象
                if script['action'] == 'subfind':
                    # 子查询
                    _els = init_el.find_elements(by=_by, value=_value)
                else:
                    # 当前页面查询
                    _els = app.find_elements(by=_by, value=_value)

                _pos = script.get('pos', 0)
                _end_el = _els[_pos]
        elif script['action'] == 'click':
            # 点击对象
            init_el.click()
        elif script['action'] == 'wait_activity':
            # 等待加载页面
            app.wait_activity_adb(
                script.get('activity'), script.get('timeout'), script.get('interval', 0.1)
            )
        elif script['action'] == 'wait':
            # 等待一会
            time.sleep(script.get('time', 1.0))
        elif script['action'] == 'send_keys':
            # 发送文本
            app.adb_keyboard_text(script.get('keys'))
        elif script['action'] == 'send_adb_keyboard_keycode':
            # 发送按键按键
            app.adb_keyboard_keycode(*script['keycode'])
        elif script['action'] == 'send_adb_keycode':
            # 通过adb发送按键
            app.adb_keycode(*script['keycode'])
        elif script['action'] == 'set_ime':
            # 切换输入法
            app.adb_set_default_ime(script['ime'])
        elif script['action'] == 'tap':
            # 点击指定坐标
            app.tap_adb(x=script['pos'][0], y=script['pos'][1])

        # 返回对象
        return _end_el


if __name__ == '__main__':
    # 当程序自己独立运行时执行的操作
    # 打印版本信息
    print(('模块名：%s  -  %s\n'
           '作者：%s\n'
           '发布日期：%s\n'
           '版本：%s' % (__MOUDLE__, __DESCRIPT__, __AUTHOR__, __PUBLISH__, __VERSION__)))

    # _api = DyControlApi()
    # _code, lines = _api._exec_sys_cmd('xy_adb connect 127.0.0.1:21513', 'utf-8')
    # print(_code, lines)

    # print(random.uniform(10.0, -10.0))
