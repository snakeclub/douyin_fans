#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
# Copyright 2019 黎慧剑
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""
抖音粉丝手机群控后台服务
@module server
@file server.py
"""

import os
import sys
if sys.platform == 'win32':
    import win32com.client
import HiveNetLib.simple_log as simple_log
from HiveNetLib.simple_restful.server import FlaskServer
# 根据当前文件路径将包路径纳入，在非安装的情况下可以引用到
sys.path.append(os.path.abspath(os.path.join(
    os.path.dirname(__file__), os.path.pardir)))
from douyin_fans.lib.control_services import DyControlApi


def run_server(**kwargs):
    """
    运行群控后台服务
    """
    # 基本参数
    _root_path = os.path.abspath(os.path.dirname(__file__))
    _static_folder = 'website'

    # 日志对象
    _logger = simple_log.Logger(
        conf_file_name=os.path.join(_root_path, 'config/logger.json'),
        logger_name=simple_log.EnumLoggerName.ConsoleAndFile,
        config_type=simple_log.EnumLoggerConfigType.JSON_FILE,
        logfile_path=os.path.join(_root_path, 'log/server.log'),
        is_create_logfile_by_day=True
    )

    # 初始化控制API实例对象
    _dy_control_api = DyControlApi()

    # 创建网站快捷方式
    if sys.platform == 'win32':
        _ws = win32com.client.Dispatch("wscript.shell")
        _scut = _ws.CreateShortcut(
            os.path.join(_root_path, '群控管理后台.url')
        )
        _scut.TargetPath = 'http://%s:%d/index.html' % (
            _dy_control_api.para['site'], _dy_control_api.para['port']
        )
        _scut.Save()

    # 初始化FlaskServer
    _server_config = {
        'app_config': {
            'root_path': _root_path,
            'static_folder': _static_folder,
            'static_url_path': '',
        },
        'flask_run': {
            'host': _dy_control_api.para['host'],
            'port': _dy_control_api.para['port'],
            'threaded': _dy_control_api.para['threaded'],
            'processes': _dy_control_api.para['processes']
        },
        'json_as_ascii': _dy_control_api.para['json_as_ascii'],
        'use_wsgi': _dy_control_api.para['use_wsgi']
    }
    _server = FlaskServer(
        'dy_control_server', server_config=_server_config, logger=_logger
    )

    # 装载Restful Api
    _server.add_route_by_class(
        [_dy_control_api, ]
    )

    # 启动FlaskServer
    _server.start()


if __name__ == '__main__':
    # 当程序自己独立运行时执行的操作
    run_server()
