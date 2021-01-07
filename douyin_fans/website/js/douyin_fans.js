/**
 * Copyright 2018 黎慧剑
 *
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/.
 */

/**
 * 抖音后台群控管理专用JS文件
 * @file (douyin_fans.js)
 * @author (黎慧剑)
 * @version (0.1.0)
 */

;

$.debug = true;

/**
 * 自定义休眠时长函数
 * @param {int} numberMillis - 休眠时长，单位为毫秒
 */
function sleep(numberMillis) {
    var now = new Date();
    var exitTime = now.getTime() + numberMillis;
    while (true) {
        now = new Date();
        if (now.getTime() > exitTime)
            return;
    }
};

;
(function ($) {

    /**
     * 定义插件名称，避免不同插件之间相互干扰
     * @class douyin_fans
     */
    $.douyin_fans = new Object();

    // 用于控制加载中界面的关闭处理
    $.douyin_fans.loading_ui_enable = false;

    // 当前最新的系统参数
    $.douyin_fans.sysconfig = null;

    // 当前最新的后台参数
    $.douyin_fans.bgconfig = null;

    // 已选中的在线用户设备号数组
    $.douyin_fans.selected_online_user = [];

    // 设备连接状态的图片
    $.douyin_fans.devices_status_html = '<svg width="16" height="16" viewBox="0 0 16 16" class="bi" fill="currentColor" style="color:{$=color=$};" xmlns="http://www.w3.org/2000/svg" focusable="false">' +
        '<use xlink:href="./img/bootstrap-icons.svg#circle-fill" />' +
        '</svg>';

    /**
     * 配置信息界面配置字典
     * 字典定义如下:
     * 1. 数组的每个项属于一组输入控件, group_name定义了显示的组名, 可以不设置组名; inputs 定义了每一个输入项的数组;
     * 2. 每个输入项的固定配置说明如下:
     * id - 输入项的唯一标识, 用于生成控件的真实id (格式为'{form_id}_{id}'), 同时也会在输入控件上设置为 v_name 的值，用于匹配更新值的字典;
     * show_name - 控件显示名称
     * v_type - 控件的数据类型, 支持 str int bool
     * ctrl_type - 控件类型, 默认为 text, 支持 text - 输入框, textarea - 多行输入框, checkbox - 复选框, newline - 换行
     * width - 控件占布局宽度单位, 默认为4, 总宽度为12, 如果一行的布局宽度大于 12 则将控件放在下一行
     * plaintext - 值设置为null, 指定控件仅显示文本(例如不显示输入框样式, 只有文本值), 可以与readonly配套使用
     * max_width - 用于指定输入对象的最大宽度(比如布局占用12, 但最大宽度可以设置为100px)
     * 3. 不同控件类型的个性配置项说明如下:
     * (1)checkbox
     * group - 分组名, 指示相邻的 checkbox 对象分配在同一个组显示 (分组名必须一样)
     * group_show - 分组显示, 如果不传则不显示分组名
     * inline - 指示同一组的 checkbox 对象防止在同一行中 (否则将垂直对齐显示)
     * (2)textarea
     * rows - 指定输入框显示行数
     * 4. 除以上的标准输入项和不同类型的特定配置以外, 其余参数都会直接添加到输入控件的属性中(attr), 如果值为 null 代表只添加属性名;
     * 5. bootstap 常用的标准属性值参考如下:
     * value - 输入控件当前设置值, 可用于 text, checkbox 控件
     * readonly - 输入控件值不可编辑, 值设置为null
     * disabled - 禁用输入控件, 值设置为null
     * placeholder - 输入框没有值时的提示文本
     *
     */
    $.douyin_fans.config_ui_json = [{
            'group_name': 'Web服务器配置',
            'inputs': [{
                    'id': 'site',
                    'show_name': '访问IP或域名',
                    'ctrl_type': 'text',
                    'width': '3',
                    'value': '127.0.0.1'
                },
                {
                    'id': 'host',
                    'show_name': '监听IP',
                    'ctrl_type': 'text',
                    'width': '3',
                    'value': '127.0.0.1'
                },
                {
                    'id': 'port',
                    'show_name': '监听端口',
                    'v_type': 'int',
                    'ctrl_type': 'text',
                    'width': '3',
                    'value': '5000'
                },
                {
                    'id': 'processes',
                    'show_name': '进程数',
                    'v_type': 'int',
                    'ctrl_type': 'text',
                    'width': '3',
                    'value': '1'
                },
                {
                    'ctrl_type': 'newline'
                },
                {
                    'id': 'use_wsgi',
                    'show_name': '使用WSGI服务',
                    'v_type': 'bool',
                    'ctrl_type': 'checkbox',
                    'width': '2',
                    'checked': 'checked'
                },
                {
                    'id': 'json_as_ascii',
                    'show_name': 'JSON兼容ASCII编码',
                    'v_type': 'bool',
                    'ctrl_type': 'checkbox',
                    'width': '2'
                },
                {
                    'id': 'threaded',
                    'show_name': '使用多线程',
                    'v_type': 'bool',
                    'ctrl_type': 'checkbox',
                    'width': '2',
                    'checked': 'checked'
                }
            ]
        },
        {
            'group_name': '设备检测配置',
            'inputs': [{
                    'id': 'adb',
                    'show_name': 'adb命令名',
                    'v_type': 'str',
                    'ctrl_type': 'text',
                    'width': '3',
                    'value': 'adb'
                },
                {
                    'id': 'shell_encoding',
                    'show_name': '命令窗口编码',
                    'v_type': 'str',
                    'ctrl_type': 'text',
                    'width': '3',
                    'value': 'GBK',
                    'placeholder': '通常windows为GBK，linux为utf-8'
                },
                {
                    'id': 'wifi_port',
                    'show_name': '默认Wifi连接端口',
                    'v_type': 'str',
                    'ctrl_type': 'text',
                    'width': '3',
                    'value': '5555'
                },
            ]
        },
        {
            'group_name': '应用自动化参数',
            'inputs': [{
                'id': 'auto_into_line',
                'show_name': '自动进入直播间',
                'v_type': 'bool',
                'ctrl_type': 'checkbox',
                'width': '2',
                'checked': 'checked'
            },{
                'id': 'into_line_err_exit',
                'show_name': '进入失败自动退出',
                'v_type': 'bool',
                'ctrl_type': 'checkbox',
                'width': '2',
                'checked': 'checked'
            },
            {
                'id': 'is_into_wait',
                'show_name': '进入随机间隔',
                'v_type': 'bool',
                'ctrl_type': 'checkbox',
                'width': '2',
                'checked': 'checked'
            },
            {
                'id': 'into_line_wait_min',
                'show_name': '进入最小间隔时间(秒)',
                'v_type': 'float',
                'ctrl_type': 'text',
                'width': '3',
                'value': '0.5'
            },
            {
                'id': 'into_line_wait_max',
                'show_name': '进入最大间隔时间(秒)',
                'v_type': 'float',
                'ctrl_type': 'text',
                'width': '3',
                'value': '2.0'
            },
            ]
        },
        {
            'group_name': 'Appium设置',
            'inputs': [{
                    'id': 'appium_server',
                    'show_name': 'appium服务器连接',
                    'v_type': 'str',
                    'ctrl_type': 'text',
                    'width': '4',
                    'value': 'http://localhost:4723/wd/hub'
                },
                {
                    'id': 'android_restore_ime',
                    'show_name': '群控统一刷输入法',
                    'v_type': 'str',
                    'ctrl_type': 'text',
                    'width': '4',
                    'value': 'com.microvirt.memuime/.MemuIME'
                },
                {
                    'id': 'implicitly_wait',
                    'show_name': '查找超时(秒)',
                    'v_type': 'float',
                    'ctrl_type': 'text',
                    'width': '4',
                    'value': '5.0'
                },
            ]
        },
        {
            'group_name': '安卓控制参数 - 启动',
            'inputs': [{
                    'id': 'android_apk',
                    'show_name': '应用安装包',
                    'v_type': 'str',
                    'ctrl_type': 'text',
                    'width': '3',
                    'value': 'aweme_14.1.0.apk',
                    'placeholder': '必须放置在config目录下'
                },
                {
                    'id': 'android_appPackage',
                    'show_name': '应用包名',
                    'v_type': 'str',
                    'ctrl_type': 'text',
                    'width': '3',
                    'value': 'com.ss.android.ugc.aweme'
                },
                {
                    'ctrl_type': 'newline'
                },
                {
                    'id': 'android_appActivity',
                    'show_name': '首页Activity',
                    'v_type': 'str',
                    'ctrl_type': 'text',
                    'width': '3',
                    'value': '.splash.SplashActivity'
                },
                {
                    'id': 'android_search_appActivity',
                    'show_name': '搜索Activity',
                    'v_type': 'str',
                    'ctrl_type': 'text',
                    'width': '3',
                    'value': '.search.activity.SearchResultActivity'
                },
                {
                    'id': 'android_line_appActivity',
                    'show_name': '直播间Activity(多个可用|分隔)',
                    'v_type': 'str',
                    'ctrl_type': 'text',
                    'width': '3',
                    'value': '.live.LivePlayActivity'
                },
                {
                    'ctrl_type': 'newline'
                },
                {
                    'id': 'android_desired_caps',
                    'show_name': '启动参数',
                    'v_type': 'str',
                    'ctrl_type': 'textarea',
                    'width': '6',
                    'value': '',
                    'rows': '3'
                },
            ]
        },
        {
            'group_name': '安卓控制参数 - 脚本',
            'inputs': [
                {
                    'id': 'android_chat_wait_input',
                    'show_name': '等待输入框弹出时长(秒)',
                    'v_type': 'float',
                    'ctrl_type': 'text',
                    'width': '3',
                    'value': '1'
                },
                {
                    'ctrl_type': 'newline'
                },
                {
                    'id': 'android_script_version_mapping',
                    'show_name': '版本与脚本文件的映射',
                    'v_type': 'str',
                    'ctrl_type': 'textarea',
                    'width': '6',
                    'value': '',
                    'rows': '3'
                },
            ]
        },
        {
            'group_name': '点赞设置参数',
            'inputs': [
                {
                    'id': 'give_thumbs_up_offset_x',
                    'show_name': '中心位置偏移比例(x)',
                    'v_type': 'float',
                    'ctrl_type': 'text',
                    'width': '3',
                    'value': '0.01'
                },
                {
                    'id': 'give_thumbs_up_offset_y',
                    'show_name': '中心位置偏移比例(y)',
                    'v_type': 'float',
                    'ctrl_type': 'text',
                    'width': '3',
                    'value': '0.01'
                },
                {
                    'id': 'give_thumbs_up_random_x',
                    'show_name': '随机范围比例(x)',
                    'v_type': 'float',
                    'ctrl_type': 'text',
                    'width': '3',
                    'value': '0.01'
                },
                {
                    'id': 'give_thumbs_up_random_y',
                    'show_name': '随机范围比例(y)',
                    'v_type': 'float',
                    'ctrl_type': 'text',
                    'width': '3',
                    'value': '0.01'
                },
                {
                    'id': 'give_thumbs_up_random_seed',
                    'show_name': '随机位置种子数',
                    'v_type': 'int',
                    'ctrl_type': 'text',
                    'width': '3',
                    'value': '5'
                },
                {
                    'id': 'give_thumbs_up_tap_max',
                    'show_name': '每次点击次数上限',
                    'v_type': 'int',
                    'ctrl_type': 'text',
                    'width': '3',
                    'value': '5'
                },
                {
                    'id': 'give_thumbs_up_tap_random',
                    'show_name': '是否随机点击次数',
                    'v_type': 'bool',
                    'ctrl_type': 'checkbox',
                    'width': '2',
                    'checked': 'checked'
                },
                {
                    'id': 'give_thumbs_up_random_wait',
                    'show_name': '是否随机等待时长',
                    'v_type': 'bool',
                    'ctrl_type': 'checkbox',
                    'width': '2',
                    'checked': 'checked'
                },
                {
                    'id': 'give_thumbs_up_wait_min',
                    'show_name': '随机等待最小时长(秒)',
                    'v_type': 'float',
                    'ctrl_type': 'text',
                    'width': '3',
                    'value': '0.0'
                },
                {
                    'id': 'give_thumbs_up_wait_max',
                    'show_name': '随机等待最大时长(秒)',
                    'v_type': 'float',
                    'ctrl_type': 'text',
                    'width': '3',
                    'value': '0.5'
                },
            ]
        },
    ];

    /**
     * 后台模块设置参数界面配置字典
     */
    $.douyin_fans.bg_config_ui_json = [{
        'group_name': '',
        'inputs': [
            {
                'id': 'line_name',
                'show_name': '直播间名',
                'v_type': 'str',
                'ctrl_type': 'text',
                'width': '5',
                'value': ''
            },
            {
                'id': 'send_bt_wait_min',
                'show_name': '多人操作最小间隔时间(秒)',
                'v_type': 'float',
                'ctrl_type': 'text',
                'width': '5',
                'value': '0.5'
            },
            {
                'id': 'send_bt_wait_max',
                'show_name': '多人操作最大间隔时间(秒)',
                'v_type': 'float',
                'ctrl_type': 'text',
                'width': '5',
                'value': '2.0'
            },
            {
                'id': 'give_thumbs_self_define',
                'show_name': '自定义点赞时长(秒)',
                'v_type': 'float',
                'ctrl_type': 'text',
                'width': '5',
                'value': '20'
            },
            {
                'id': 'tap_to_main',
                'show_name': '点击屏幕位置(比例)',
                'v_type': 'str',
                'ctrl_type': 'text',
                'width': '5',
                'value': '0.5,0.25'
            },
        ]
    }];

    /**
     * 设备清单表格配置的参数, 请参考 bootstrap-table 参数: https://bootstrap-table.com/docs/api/table-options/
     */
    $.douyin_fans.devices_table_json = {
        height: 600, // 指定高度, 如果不指定高度不设置值，或者设置为 undefined
        toolbar: '.devices_table_toolbar', // 表格工具栏的jquery表达式
        headerStyle: function (column) { // 设置标题行样式
            //return {css: {background: 'gray'}};
            return {};
        },
        showColumns: false, // 是否显示所有的列（选择显示的列）
        showToggle: false, // 是否显示详细视图和列表视图的切换按钮
        clickToSelect: true, // 是否启用点击选中行
        ignoreClickToSelectOn: function (e) { // 忽略点击选中行的元素，比如行里面的checkbox
            return ['A', 'LABEL', 'INPUT', 'BUTTON', 'I'].indexOf(e.tagName) > -1;
        },
        fixedColumns: true, // 是否冻结列
        fixedNumber: '3', // 冻结左边列数量，冻结3列
        fixedRightNumber: '3', // 冻结右边列数量, 冻结2列(操作列)
        sortable: true, // 是否启用排序
        sortOrder: "asc", // 排序方式
        cache: false, // 是否使用缓存，默认为true，所以一般情况下需要设置一下这个属性（*）
        classes: 'table table-bordered table-hover table-striped', // 表格样式
        uniqueId: "device_name", // 每一行的唯一标识，一般为主键列
        data: [], // 数据数组, 数组每个值为行对象字典, [{'field_name': 'field_value', ...}, ...]
        columns: [{ // 标题头内容
            field: 'selected', // 复选框
            checkbox: true,
            valign: 'middle',
            align: 'center'
        }, {
            field: 'connnect_status',
            title: '状态',
            visible: false
        }, {
            field: 'connnect_status_pic',
            title: '',
            width: '20px',
            sortable: true,
            valign: 'middle',
            align: 'center',
            formatter: function (val, row, index) {
                // 格式化图片样式
                var color_name = 'red';
                switch (row.connnect_status) {
                    case 'connected':
                        // 设备已连接
                        color_name = 'skyblue';
                        break;
                    case 'started':
                        // 已启动应用
                        color_name = 'greenyellow';
                        break;
                }
                return $.douyin_fans.devices_status_html.replace('{$=color=$}', color_name);
            }
        }, {
            field: 'device_name',
            title: '设备名',
            sortable: true
        }, {
            field: 'platform_name',
            title: '手机平台',
        }, {
            field: 'platform_version',
            title: '手机版本',
        }, {
            field: 'brand',
            title: '手机品牌',
        }, {
            field: 'model',
            title: '产品名称',
        }, {
            field: 'use_wifi',
            title: '使用wifi',
            valign: 'middle',
            align: 'center',
            width: '10px',
            formatter: function (val) {
                // 单选框
                checked = false;
                if (val !== undefined && val) {
                    checked = true;
                }
                return '<input type="checkbox"' + (checked ? ' checked="checked"' : '') + ' disabled>';
            }
        }, {
            field: 'wlan_ip',
            title: 'Wifi IP',
            sortable: true
        }, {
            field: 'wlan_port',
            title: 'Wifi端口',
            sortable: true
        }, {
            field: 'app_version',
            title: 'app版本',
            sortable: true
        }, {
            field: 'remark',
            title: '备注',
            width: 200,
            widthUnit: 'px',
        }, {
            field: 'use_anonymous',
            title: '使用匿名',
            visible: false,
        }, {
            field: 'use_anonymous_show',
            title: '匿名',
            sortable: true,
            valign: 'middle',
            align: 'center',
            formatter: function (val, row, index) {
                // 单选框
                checked = false;
                if (row.use_anonymous !== undefined && row.use_anonymous) {
                    checked = true;
                }
                return '<input type="checkbox"' + (checked ? ' checked="checked"' : '') + ' disabled>';
            }
        }, {
            field: 'user_name',
            title: '抖音号',
            sortable: true
        }, {
            field: '',
            title: '操作',
            width: 300,
            widthUnit: 'px',
            align: 'center',
            valign: 'middle',
            formatter: devices_table_actionFormatter
        }]
    };

    /**
     * 在线用户清单表格配置的参数, 请参考 bootstrap-table 参数
     */
    $.douyin_fans.online_user_table_json = {
        showHeader: false, // 不显示标题
        showColumns: false, // 是否显示所有的列（选择显示的列）
        showToggle: false, // 是否显示详细视图和列表视图的切换按钮
        clickToSelect: true, // 是否启用点击选中行
        ignoreClickToSelectOn: function (e) { // 忽略点击选中行的元素，比如行里面的checkbox
            return ['A', 'LABEL', 'INPUT', 'BUTTON', 'I'].indexOf(e.tagName) > -1;
        },
        sortable: true, // 是否启用排序
        sortOrder: "asc", // 排序方式
        cache: false, // 是否使用缓存，默认为true，所以一般情况下需要设置一下这个属性（*）
        classes: 'table table-bordered table-hover table-striped', // 表格样式
        uniqueId: "device_name", // 每一行的唯一标识，一般为主键列
        data: [], // 数据数组, 数组每个值为行对象字典, [{'field_name': 'field_value', ...}, ...]
        columns: [{ // 标题头内容
            field: 'selected', // 复选框
            checkbox: true,
            valign: 'middle',
            align: 'center',
            width: 10,
        }, {
            field: 'device_name',
            title: '设备名',
            visible: false
        }, {
            field: 'user_name',
            title: '抖音号',
            sortable: true
        }, {
            field: '',
            title: '',
            width: 20,
            align: 'center',
            valign: 'middle',
            formatter: online_user_table_actionFormatter
        }],
    };


    /**
     * 在告警框提示debug信息($.debug为true的情况下才执行)
     * @param {string} str - 要提示的信息
     */
    function debug(str) {
        if ($.debug === true) {
            alert('debug: ' + str);
        }
    };

    /** ---------------------------
     * 通用函数
     */

    /**
     * 初始化界面
     */
    $.douyin_fans.init_ui = function () {
        // 显示loading
        $.ui_tools.show_modal('loadingModal');
        $.douyin_fans.loading_ui_enable = true;
        try {
            // 初始化设备界面
            $('#devices_table').bootstrapTable($.douyin_fans.devices_table_json);
            $('#online_user_table').bootstrapTable($.douyin_fans.online_user_table_json);

            // 获取设备信息
            $.douyin_fans.get_devcies(true);

            // 初始化配置页面
            $('#form_config').generate_form_ui_by_json(
                $.douyin_fans.config_ui_json, 'form_config_button', true
            );
            $('#form_bg_config').generate_form_ui_by_json(
                $.douyin_fans.bg_config_ui_json
            );


            // 加载系统参数
            url = '/api/DyControlApi/get_config';
            json_data = {
                'interface_id': get_interface_id()
            };

            // 调用Ajax
            $.douyin_fans.ajax_call(
                url, json_data, {
                    'tips': '获取系统配置信息',
                    'success_not_alert': true,
                    'success_fun': function (result) {
                        try {
                            $.douyin_fans.sysconfig = result;
                            $('#form_config').set_form_values(result);
                            return [true, 'success'];
                        } catch (e) {
                            return [false, e.toString()];
                        }
                    }
                }
            );

            // 加载后台参数
            url = '/api/DyControlApi/get_bg_config';
            json_data = {
                'interface_id': get_interface_id()
            };

            // 调用Ajax
            $.douyin_fans.ajax_call(
                url, json_data, {
                    'tips': '获取后台配置信息',
                    'success_not_alert': true,
                    'success_fun': function (result) {
                        try {
                            $.douyin_fans.bgconfig = result;
                            $('#form_bg_config').set_form_values(result);
                            return [true, 'success'];
                        } catch (e) {
                            return [false, e.toString()];
                        }
                    }
                }
            );
        } catch (e) {
            // 进行异常提示
            $.ui_tools.alert(
                'function $.douyin_fans.init_ui exception: ' + e.toString(),
                '告警信息', 'alert'
            );
        } finally {
            // 关闭loading必须通过异步方式执行才能关闭
            setTimeout(close_loading_modal, 10);
        }
    };

    /**
     * 获取系统配置信息
     *
     * @param {bool} success_not_alert=false - 成功交易不提示
     */
    $.douyin_fans.get_config = function (success_not_alert) {
        // 默认参数
        if (success_not_alert === undefined) {
            success_not_alert = false;
        }

        // 显示loading
        $.ui_tools.show_modal('loadingModal');
        $.douyin_fans.loading_ui_enable = true;
        try {
            // 准备参数
            url = '/api/DyControlApi/get_config';
            json_data = {
                'interface_id': get_interface_id()
            };

            // 调用Ajax
            $.douyin_fans.ajax_call(
                url, json_data, {
                    'tips': '获取系统配置信息',
                    'success_not_alert': success_not_alert,
                    'success_fun': function (result) {
                        try {
                            $.douyin_fans.sysconfig = result;
                            $('#form_config').set_form_values(result);
                            return [true, 'success'];
                        } catch (e) {
                            return [false, e.toString()];
                        }
                    }
                }
            );
        } catch (e) {
            // 进行异常提示
            $.ui_tools.alert(
                'function $.douyin_fans.get_config exception: ' + e.toString(),
                '告警信息', 'alert'
            );
        } finally {
            // 关闭loading必须通过异步方式执行才能关闭
            setTimeout(close_loading_modal, 10);
        }
    };

    /**
     * 设置系统配置信息
     *
     * @param {bool} success_not_alert=false - 成功交易不提示
     */
    $.douyin_fans.set_config = function (success_not_alert) {
        // 默认参数
        if (success_not_alert === undefined) {
            para_name = false;
        }

        // 显示loading
        $.ui_tools.show_modal('loadingModal');
        $.douyin_fans.loading_ui_enable = true;
        try {
            // 准备参数
            url = '/api/DyControlApi/set_config';
            json_data = $('#form_config').get_form_values_json();
            json_data['interface_id'] = get_interface_id();

            // 调用Ajax
            $.douyin_fans.ajax_call(
                url, json_data, {
                    'tips': '设置系统配置信息',
                    'success_fun': function (result) {
                        $.douyin_fans.sysconfig = json_data;
                        return [true, 'success'];
                    },
                    'success_not_alert': success_not_alert
                }
            )
        } catch (e) {
            // 进行异常提示
            $.ui_tools.alert(
                'function $.douyin_fans.set_config exception: ' + e.toString(),
                '告警信息', 'alert'
            );
        } finally {
            // 关闭loading必须通过异步方式执行才能关闭
            setTimeout(close_loading_modal, 10);
        }

    };

    /**
     * 获取后台配置信息
     *
     * @param {bool} success_not_alert=false - 成功交易不提示
     */
    $.douyin_fans.get_bg_config = function (success_not_alert) {
        // 默认参数
        if (success_not_alert === undefined) {
            success_not_alert = false;
        }

        // 显示loading
        $.ui_tools.show_modal('loadingModal');
        $.douyin_fans.loading_ui_enable = true;
        try {
            // 准备参数
            url = '/api/DyControlApi/get_bg_config';
            json_data = {
                'interface_id': get_interface_id()
            };

            // 调用Ajax
            $.douyin_fans.ajax_call(
                url, json_data, {
                    'tips': '获取后台配置信息',
                    'success_not_alert': success_not_alert,
                    'success_fun': function (result) {
                        try {
                            $.douyin_fans.bgconfig = result;
                            $('#form_bg_config').set_form_values(result);
                            return [true, 'success'];
                        } catch (e) {
                            return [false, e.toString()];
                        }
                    }
                }
            );
        } catch (e) {
            // 进行异常提示
            $.ui_tools.alert(
                'function $.douyin_fans.get_bg_config exception: ' + e.toString(),
                '告警信息', 'alert'
            );
        } finally {
            // 关闭loading必须通过异步方式执行才能关闭
            setTimeout(close_loading_modal, 10);
        }
    };

    /**
     * 设置后台配置信息
     *
     * @param {bool} success_not_alert=false - 成功交易不提示
     */
    $.douyin_fans.set_bg_config = function (success_not_alert) {
        // 默认参数
        if (success_not_alert === undefined) {
            para_name = false;
        }

        // 显示loading
        $.ui_tools.show_modal('loadingModal');
        $.douyin_fans.loading_ui_enable = true;
        try {
            // 准备参数
            url = '/api/DyControlApi/set_bg_config';
            json_data = $('#form_bg_config').get_form_values_json();
            json_data['interface_id'] = get_interface_id();

            // 调用Ajax
            $.douyin_fans.ajax_call(
                url, json_data, {
                    'tips': '设置后台配置信息',
                    'success_fun': function (result) {
                        $.douyin_fans.bgconfig = json_data;
                        return [true, 'success'];
                    },
                    'success_not_alert': success_not_alert
                }
            )
        } catch (e) {
            // 进行异常提示
            $.ui_tools.alert(
                'function $.douyin_fans.set_bg_config exception: ' + e.toString(),
                '告警信息', 'alert'
            );
        } finally {
            // 关闭loading必须通过异步方式执行才能关闭
            setTimeout(close_loading_modal, 10);
        }

    };

    /**
     * 获取设备列表
     *
     * @param {bool} success_not_alert=false - 成功交易不提示
     */
    $.douyin_fans.get_devcies = function (success_not_alert) {
        // 默认参数
        if (success_not_alert === undefined) {
            success_not_alert = false;
        }

        // 显示loading
        $("#btn_get_devices").addClass("disabled");
        $('#devices_table').bootstrapTable('showLoading');
        try {
            // 准备参数
            url = '/api/DyControlApi/get_devcies';
            json_data = {
                'interface_id': get_interface_id()
            };

            // 调用Ajax
            $.douyin_fans.ajax_call(
                url, json_data, {
                    'tips': '获取设备列表',
                    'success_not_alert': success_not_alert,
                    'success_fun': function (result) {
                        try {
                            var devices_table = $('#devices_table');
                            devices_table.bootstrapTable('load', result.devices);

                            // 需要处理第二个页的抖音登陆用户清单
                            var user_table = $('#online_user_table');
                            var online_data = user_table.bootstrapTable('getData');

                            // 删除无效用户
                            for(i=online_data.length - 1; i>=0;i--){
                                var row = devices_table.bootstrapTable('getRowByUniqueId', online_data[i].device_name);
                                if (row === undefined || row === null || row.connnect_status != 'started'){
                                    user_table.bootstrapTable('uncheckBy', {field: 'device_name', values: [online_data[i].device_name]});
                                    user_table.bootstrapTable('removeByUniqueId', online_data[i].device_name);
                                }
                            }

                            // 添加新用户
                            for(var i=0; i<result.devices.length;i++){
                                if (result.devices[i].connnect_status == 'started'){
                                    var row = user_table.bootstrapTable('getRowByUniqueId', result.devices[i].device_name);
                                    if (row === undefined || row === null){
                                        user_table.bootstrapTable(
                                            'insertRow',
                                            {index: 1, row: {
                                                'device_name': result.devices[i].device_name,
                                                'user_name': result.devices[i].user_name
                                            }}
                                        );
                                    }
                                }
                            }
                            return [true, 'success'];
                        } catch (e) {
                            return [false, e.toString()];
                        }
                    }
                }
            );
        } catch (e) {
            // 进行异常提示
            $.ui_tools.alert(
                'function $.douyin_fans.get_devcies exception: ' + e.toString(),
                '告警信息', 'alert'
            );
        } finally {
            // 关闭loading必须通过异步方式执行才能关闭
            setTimeout(function () {
                $('#devices_table').bootstrapTable('hideLoading');
                $("#btn_get_devices").removeClass('disabled');
            }, 10);
        }
    };


    /**
     * 删除选中设备
     *
     * @param {bool} success_not_alert=false - 成功交易不提示
     */
    $.douyin_fans.remove_devices = function (success_not_alert) {
        // 默认参数
        if (success_not_alert === undefined) {
            success_not_alert = false;
        }

        // 显示loading
        $("#btn_remove_devices").addClass("disabled");
        $('#devices_table').bootstrapTable('showLoading');
        try {
            // 提示是否要删除
            var selsetions = $('#devices_table').bootstrapTable('getSelections');
            if (selsetions.length > 0) {
                if (!window.confirm("请确认是否删除选中的" + selsetions.length.toString() + "个设备?")) {
                    return;
                }
            } else {
                $.ui_tools.alert(
                    '未选中设备！', '告警信息', 'alert'
                );
                return;
            }

            // 准备参数
            var device_list = [];
            for (var i = 0; i < selsetions.length; i++) {
                device_list.push(selsetions[i].device_name);
            }

            // 执行删除
            remove_devices(device_list, success_not_alert);

            // 重新刷新清单
            $.douyin_fans.get_devcies(true);
        } catch (e) {
            // 进行异常提示
            $.ui_tools.alert(
                'function $.douyin_fans.remove_devices exception: ' + e.toString(),
                '告警信息', 'alert'
            );
        } finally {
            // 关闭loading必须通过异步方式执行才能关闭
            setTimeout(function () {
                $('#devices_table').bootstrapTable('hideLoading');
                $("#btn_remove_devices").removeClass('disabled');
            }, 10);
        }
    };

    /**
     * 连接选中设备
     *
     * @param {bool} success_not_alert=false - 成功交易不提示
     */
    $.douyin_fans.connect_devices = function (success_not_alert) {
        // 默认参数
        if (success_not_alert === undefined) {
            success_not_alert = false;
        }

        // 显示loading
        $("#btn_connect_devices").addClass("disabled");
        $('#devices_table').bootstrapTable('showLoading');
        try {
            // 提示是否要删除
            var selsetions = $('#devices_table').bootstrapTable('getSelections');
            if (selsetions.length <= 0) {
                $.ui_tools.alert(
                    '未选中设备！', '告警信息', 'alert'
                );
                return;
            }

            // 准备参数
            var device_list = [];
            for (var i = 0; i < selsetions.length; i++) {
                device_list.push(selsetions[i].device_name);
            }

            // 执行连接处理, 成功不提示
            var result = connect_devices(device_list, true);
            if (result[0]) {
                // 检查是否有失败的情况
                if (result[1].length <= 0) {
                    // 全部处理成功
                    if (!success_not_alert) {
                        $.ui_tools.alert(
                            '设备连接处理成功！', '提示', 'info', true, 1000
                        );
                    }
                } else {
                    // 部分处理成功
                    $.ui_tools.alert(
                        '部分设备连接失败:\r\n' + JSON.stringify(result[1]),
                        '告警信息', 'alert'
                    );
                }

                // 重新刷新清单
                $.douyin_fans.get_devcies(true);
            }
        } catch (e) {
            // 进行异常提示
            $.ui_tools.alert(
                'function $.douyin_fans.connect_devices exception: ' + e.toString(),
                '告警信息', 'alert'
            );
        } finally {
            // 关闭loading必须通过异步方式执行才能关闭
            setTimeout(function () {
                $('#devices_table').bootstrapTable('hideLoading');
                $("#btn_connect_devices").removeClass('disabled');
            }, 10);
        }
    };

    /**
     * 群控设置输入法
     *
     * @param {bool} success_not_alert=false - 成功交易不提示
     */
    $.douyin_fans.restore_ime = function (success_not_alert) {
        // 默认参数
        if (success_not_alert === undefined) {
            success_not_alert = false;
        }

        // 显示loading
        $("#btn_restore_ime").addClass("disabled");
        try {
            // 提示是否要删除
            var selsetions = $('#devices_table').bootstrapTable('getSelections');
            if (selsetions.length <= 0) {
                $.ui_tools.alert(
                    '未选中设备！', '告警信息', 'alert'
                );
                return;
            }

            // 准备参数
            var device_list = [];
            for (var i = 0; i < selsetions.length; i++) {
                device_list.push(selsetions[i].device_name);
            }

            // 执行连接处理, 成功不提示
            var run_result = false;
            var error_info = [];
            try {
                // 准备参数
                var url = '/api/DyControlApi/restore_ime';
                var json_data = {
                    'interface_id': get_interface_id(),
                    'devices': device_list
                };

                // 调用Ajax
                $.douyin_fans.ajax_call(
                    url, json_data, {
                        'tips': '设备设置输入法',
                        'success_not_alert': true,
                        'success_fun': function (result) {
                            run_result = true;
                            error_info = result.error_info;
                            return [true, 'success'];
                        }
                    }
                );
            } catch (e) {
                // 进行异常提示
                $.ui_tools.alert(
                    'function $.douyin_fans.connect_devices exception: ' + e.toString(),
                    '告警信息', 'alert'
                );
            }

            if (run_result) {
                // 检查是否有失败的情况
                if (error_info.length <= 0) {
                    // 全部处理成功
                    if (!success_not_alert) {
                        $.ui_tools.alert(
                            '设置设备输入法成功！', '提示', 'info', true, 1000
                        );
                    }
                } else {
                    // 部分处理成功
                    $.ui_tools.alert(
                        '部分设备输入法设置失败:\r\n' + JSON.stringify(error_info),
                        '告警信息', 'alert'
                    );
                }
            }
        } catch (e) {
            // 进行异常提示
            $.ui_tools.alert(
                'function $.douyin_fans.connect_devices exception: ' + e.toString(),
                '告警信息', 'alert'
            );
        } finally {
            // 关闭loading必须通过异步方式执行才能关闭
            setTimeout(function () {
                $("#btn_restore_ime").removeClass('disabled');
            }, 10);
        }
    };

    /**
     * 自动添加设备
     *
     * @param {bool} success_not_alert=false - 成功交易不提示
     */
    $.douyin_fans.auto_add_devices = function (success_not_alert) {
        // 默认参数
        if (success_not_alert === undefined) {
            success_not_alert = false;
        }

        // 显示loading
        $("#btn_auto_add_devices").addClass("disabled");
        $('#devices_table').bootstrapTable('showLoading');
        try {
            // 准备参数
            url = '/api/DyControlApi/auto_add_devices';
            json_data = {
                'interface_id': get_interface_id()
            };

            // 调用Ajax
            $.douyin_fans.ajax_call(
                url, json_data, {
                    'tips': '自动添加设备',
                    'success_not_alert': success_not_alert,
                    'success_fun': function (result) {
                        try {
                            $('#devices_table').bootstrapTable('load', result.devices);
                            // 待补充，需要处理第二个页的抖音登陆用户清单

                            return [true, 'success'];
                        } catch (e) {
                            return [false, e.toString()]
                        }
                    }
                }
            );
        } catch (e) {
            // 进行异常提示
            $.ui_tools.alert(
                'function $.douyin_fans.get_devcies exception: ' + e.toString(),
                '告警信息', 'alert'
            );
        } finally {
            // 关闭loading必须通过异步方式执行才能关闭
            setTimeout(function () {
                $('#devices_table').bootstrapTable('hideLoading');
                $("#btn_auto_add_devices").removeClass('disabled');
            }, 10);
        }
    };

    /**
     * 手工添加设备自动获取设备信息
     *
     * @param {bool} success_not_alert=false - 成功交易不提示
     */
    $.douyin_fans.manual_add_device_getinfo = function (success_not_alert) {
        // 默认参数
        if (success_not_alert === undefined) {
            success_not_alert = false;
        }

        try {
            // 准备参数
            var url = '/api/DyControlApi/get_device_info';
            var name = $('#manual_add_name').val();
            if (name === undefined) {
                name = '';
            }
            json_data = {
                'interface_id': get_interface_id(),
                'device_name': name
            };

            // 调用Ajax
            $.douyin_fans.ajax_call(
                url, json_data, {
                    'tips': '获取设备信息',
                    'success_not_alert': success_not_alert,
                    'success_fun': function (result) {
                        try {
                            var info = result.info;
                            // 填值
                            $('#manual_add_name').val(info.device_name);
                            $('#manual_add_wlan_ip').val(info.wlan_ip);
                            return [true, 'success']
                        } catch (e) {
                            return [false, e.toString()]
                        }
                    }
                }
            );
        } catch (e) {
            // 进行异常提示
            $.ui_tools.alert(
                'function $.douyin_fans.manual_add_device_getinfo exception: ' + e.toString(),
                '告警信息', 'alert'
            );
        }
    };

    /**
     * 手工添加设备
     *
     * @param {bool} success_not_alert=false - 成功交易不提示
     */
    $.douyin_fans.manual_add_device = function (success_not_alert) {
        // 默认参数
        if (success_not_alert === undefined) {
            success_not_alert = false;
        }

        // 显示loading
        $("#btn_manual_add_submit").addClass("disabled");
        try {
            // 准备参数
            var url = '/api/DyControlApi/add_device';
            json_data = {
                'interface_id': get_interface_id(),
                'device_name': $('#manual_add_name').val(),
                'auto_connect': $('#manual_add_auto_connect').is(":checked"),
                'use_wifi': $('#manual_add_connect_type_wifi').is(":checked"),
                'wlan_ip': $('#manual_add_wlan_ip').val(),
                'wlan_port': $('#manual_add_wlan_port').val(),
                'use_anonymous': $('#manual_add_use_anonymous').is(":checked"),
                'user_name': $('#manual_add_user_name').val()
            };

            // 检查参数
            if (json_data.device_name === undefined || json_data.device_name == '') {
                $.ui_tools.alert(
                    '必须填入设备信息!', '告警信息', 'alert'
                );
                return;
            }
            if (json_data.use_wifi) {
                if (json_data.wlan_ip === undefined || json_data.wlan_ip == '') {
                    $.ui_tools.alert(
                        'Wifi 连接方式必须填入手机的 WIFI IP !', '告警信息', 'alert'
                    );
                    return;
                }
                if (json_data.wlan_port === undefined || json_data.wlan_port == '') {
                    $.ui_tools.alert(
                        'Wifi 连接方式必须填入手机的 WIFI 端口!', '告警信息', 'alert'
                    );
                    return;
                }
            }
            // 提示是否要替换已有设备
            if ($('#devices_table').bootstrapTable('getRowByUniqueId', json_data.device_name) === undefined) {
                if (!window.confirm("设备[" + json_data.device_name + "]已在列表中, 是否进行替换?")) {
                    return;
                }
            }

            // 调用Ajax
            var call_result = false;
            $.douyin_fans.ajax_call(
                url, json_data, {
                    'tips': '自动添加设备',
                    'success_not_alert': success_not_alert,
                    'success_fun': function (result) {
                        call_result = true;
                        return [true, 'success'];
                    }
                }
            );

            if (call_result) {
                // 添加成功，关闭当前窗口
                setTimeout(function () {
                    $.ui_tools.hide_modal();
                });

                // 重新刷新列表
                $.douyin_fans.get_devcies(false);
            }
        } catch (e) {
            // 进行异常提示
            $.ui_tools.alert(
                'function $.douyin_fans.manual_add_device exception: ' + e.toString(),
                '告警信息', 'alert'
            );
        } finally {
            // 关闭loading必须通过异步方式执行才能关闭
            setTimeout(function () {
                $("#btn_manual_add_submit").removeClass('disabled');
            }, 10);
        }
    };

    /**
     * 获取设备的应用用户名
     *
     * @param {bool} success_not_alert=false - 成功交易不提示
     */
    $.douyin_fans.get_app_user = function (success_not_alert) {
        // 默认参数
        if (success_not_alert === undefined) {
            success_not_alert = false;
        }

        // 显示loading
        $("#bind_user_get_app_user").addClass("disabled");
        try {
            // 准备参数
            var url = '/api/DyControlApi/get_app_user';
            json_data = {
                'interface_id': get_interface_id(),
                'device_name': $('#bind_user_device_name').val()
            };

            // 调用Ajax
            $.douyin_fans.ajax_call(
                url, json_data, {
                    'tips': '自动获取抖音用户',
                    'success_not_alert': success_not_alert,
                    'timeout': 1000000,
                    'success_fun': function (result) {
                        if (result.user_name !== undefined && result.user_name != '') {
                            $('#bind_user_use_anonymous').prop('checked', false);
                            $('#bind_user_user_name').val(result.user_name);
                        }
                        return [true, 'success'];
                    }
                }
            );
        } catch (e) {
            // 进行异常提示
            $.ui_tools.alert(
                'function $.douyin_fans.get_app_user exception: ' + e.toString(),
                '告警信息', 'alert'
            );
        } finally {
            // 关闭loading必须通过异步方式执行才能关闭
            setTimeout(function () {
                $("#bind_user_get_app_user").removeClass('disabled');
            }, 10);
        }
    };

    /**
     * 绑定抖音用户
     *
     * @param {bool} success_not_alert=false - 成功交易不提示
     */
    $.douyin_fans.device_bind_user = function (success_not_alert) {
        // 默认参数
        if (success_not_alert === undefined) {
            success_not_alert = false;
        }

        // 显示loading
        $("#btn_bind_user_submit").addClass("disabled");
        try {
            // 准备参数
            var url = '/api/DyControlApi/device_bind_user';
            json_data = {
                'interface_id': get_interface_id(),
                'device_name': $('#bind_user_device_name').val(),
                'use_anonymous': $('#bind_user_use_anonymous').is(":checked"),
                'user_name': $('#bind_user_user_name').val(),
                'remark': $('#bind_user_remark').val()
            };

            // 检查参数
            if (!json_data.use_anonymous && json_data.user_name == '') {
                $.ui_tools.alert(
                    '请输入绑定的抖音用户名!', '告警信息', 'alert'
                );
                return;
            }

            // 调用Ajax
            var call_result = false;
            $.douyin_fans.ajax_call(
                url, json_data, {
                    'tips': '绑定抖音用户',
                    'success_not_alert': success_not_alert,
                    'success_fun': function (result) {
                        call_result = true;
                        return [true, 'success'];
                    }
                }
            );

            if (call_result) {
                // 更新当前行的抖音用户信息
                var devices_table = $('#devices_table');
                devices_table.bootstrapTable(
                    'updateCellByUniqueId', {
                        id: json_data.device_name,
                        field: 'use_anonymous',
                        value: json_data.use_anonymous
                    }
                );
                devices_table.bootstrapTable(
                    'updateCellByUniqueId', {
                        id: json_data.device_name,
                        field: 'user_name',
                        value: json_data.user_name
                    }
                );
                devices_table.bootstrapTable(
                    'updateCellByUniqueId', {
                        id: json_data.device_name,
                        field: 'remark',
                        value: json_data.remark
                    }
                );

                // 添加成功，关闭当前窗口
                setTimeout(function () {
                    $.ui_tools.hide_modal();
                });
            }
        } catch (e) {
            // 进行异常提示
            $.ui_tools.alert(
                'function $.douyin_fans.device_bind_user exception: ' + e.toString(),
                '告警信息', 'alert'
            );
        } finally {
            // 关闭loading必须通过异步方式执行才能关闭
            setTimeout(function () {
                $("#btn_bind_user_submit").removeClass('disabled');
            }, 10);
        }
    };

    /**
     * 为设备安装应用（异步调用）
     *
     * @param {string} device_name - 设备名称
     */
    $.douyin_fans.install_app = function (device_name) {
        try {
            // 准备参数
            var url = '/api/DyControlApi/install_app';
            json_data = {
                'interface_id': get_interface_id(),
                'device_name': device_name
            };

            // 异步调用Ajax
            $.douyin_fans.ajax_call(
                url, json_data, {
                    'tips': '安装抖音软件',
                    'success_not_alert': true,
                    'async': true,
                    'timeout': 1000000,
                    'success_fun': function (result) {
                        $.ui_tools.alert(
                            result.msg, '提示', 'info'
                        );
                        return [true, 'success'];
                    }
                }
            );

            $.ui_tools.alert(
                '正在后台执行安装处理！', '提示', 'info', true, 1000
            );
        } catch (e) {
            // 进行异常提示
            $.ui_tools.alert(
                'function $.douyin_fans.install_app exception: ' + e.toString(),
                '告警信息', 'alert'
            );
        }
    };

    /**
     * 选中设备进入直播间
     * @param {array} devices - 设备清单，如果传 null 则代表取选中的设备
     */
    $.douyin_fans.into_app_line = function(devices){
        // 默认参数设置
        if (devices === undefined || devices === null){
            var selsetions = $('#devices_table').bootstrapTable('getSelections');
            if (selsetions.length <= 0) {
                $.ui_tools.alert(
                    '未选中设备！', '告警信息', 'alert'
                );
                return;
            }

            // 获取设备清单
            var devices = [];
            for (var i = 0; i < selsetions.length; i++) {
                devices.push(selsetions[i].device_name);
            }
        }

        // 调用远程服务
        try {
            // 准备参数
            var url = '/api/DyControlApi/into_app_line';
            json_data = {
                'interface_id': get_interface_id(),
                'devices': devices
            };

            // 异步调用Ajax
            $.douyin_fans.ajax_call(
                url, json_data, {
                    'tips': '进入直播间处理',
                    'success_not_alert': true,
                    'async': true,
                    'timeout': 1000000,
                    'success_fun': function (result) {
                        // 执行成功，进行提示
                        if (result.error_info.length == 0 && result.warning_info.length == 0){
                            // 全部成功
                            $.ui_tools.alert(
                                '进入直播间处理: ' + result.msg, '提示', 'info', true, 1000
                            );
                        }
                        else{
                            // 部分成功
                            var tips = '';
                            if (result.error_info.length > 0){
                                tips += '以下设备进入直播间失败:\n' + JSON.stringify(result.error_info) + '\n';
                            }
                            if (result.warning_info.length > 0){
                                tips += '以下设备需手工执行进入直播间:\n' + JSON.stringify(result.warning_info) + '\n';
                            }
                            $.ui_tools.alert(
                                tips,'告警信息', 'alert'
                            );
                        }

                        // 刷新设备清单状态
                        $.douyin_fans.get_devcies(true);
                        return [true, 'success'];
                    }
                }
            );

            $.ui_tools.alert(
                '正在后台执行进入直播间处理！', '提示', 'info', true, 1000
            );
        } catch (e) {
            // 进行异常提示
            $.ui_tools.alert(
                'function $.douyin_fans.into_app_line exception: ' + e.toString(),
                '告警信息', 'alert'
            );
        }
    };

    /**
     * 选中设备退出直播间
     *
     * @param {array} devices - 设备清单，如果传 null 则代表取选中的设备
     */
    $.douyin_fans.out_app_line = function(devices){
        // 默认参数设置
        if (devices === undefined || devices === null){
            var selsetions = $('#devices_table').bootstrapTable('getSelections');
            if (selsetions.length <= 0) {
                $.ui_tools.alert(
                    '未选中设备！', '告警信息', 'alert'
                );
                return;
            }

            // 获取设备清单
            var devices = [];
            for (var i = 0; i < selsetions.length; i++) {
                devices.push(selsetions[i].device_name);
            }
        }

        if (!window.confirm("请确认是否将选中的设备"+JSON.stringify(devices)+"退出直播间？")) {
            return;
        }

        // 调用远程服务
        try {
            // 准备参数
            var url = '/api/DyControlApi/out_app_line';
            json_data = {
                'interface_id': get_interface_id(),
                'devices': devices
            };

            // 异步调用Ajax
            $.douyin_fans.ajax_call(
                url, json_data, {
                    'tips': '退出直播间处理',
                    'success_not_alert': true,
                    'async': false,
                    'timeout': 20,
                    'success_fun': function (result) {
                        if (result.error_info.length > 0){
                            $.ui_tools.alert(
                                '以下设备退出直播间失败:\n' + JSON.stringify(result.error_info),'告警信息', 'alert'
                            );
                        }
                        else{
                            $.ui_tools.alert(
                                '退出直播间处理: ' + result.msg, '提示', 'info', true, 1000
                            );
                        }

                        // 刷新设备清单状态
                        $.douyin_fans.get_devcies(true);
                        return [true, 'success'];
                    }
                }
            );
        } catch (e) {
            // 进行异常提示
            $.ui_tools.alert(
                'function $.douyin_fans.out_app_line exception: ' + e.toString(),
                '告警信息', 'alert'
            );
        }
    };

    /** ---------------------------
     * 后台管理界面的外部操作函数
     */

    /**
     * 设置已选中用户的清单文本
     *
     * @param {json} input_data - 如果传值进来，说明直接通过传值生成
     */
    $.douyin_fans.set_selected_user_text = function (input_data) {
        try {
            var data = null;
            if (input_data === undefined) {
                data = $('#online_user_table').bootstrapTable('getSelections');
            } else {
                data = input_data;
            }
            $.douyin_fans.selected_online_user = [];
            var user_text = "";
            if (data.length > 1) {
                user_text = data[0].user_name;
                $.douyin_fans.selected_online_user.push(data[0].device_name);
            }
            for (var i = 1; i < data.length; i++) {
                user_text += ', ' + data[i].user_name;
                $.douyin_fans.selected_online_user.push(data[i].device_name);
            }
            $('#selected_user_text').html(user_text);
        } catch (e) {
            // 进行异常提示
            $.ui_tools.alert(
                'function $.douyin_fans.set_selected_user_text exception: ' + e.toString(),
                '告警信息', 'alert'
            );
        }
    };

    /**
     * 选中一个用户
     *
     * @param {string} device_name - 选中用户的设备号
     */
    $.douyin_fans.select_user = function (device_name) {
        try {
            // 先判断是否已在选中清单
            if ($.douyin_fans.selected_online_user.indexOf(device_name) > -1) {
                return;
            }

            // 从在线用户清单中获取用户名
            var row = $('#online_user_table').bootstrapTable('getRowByUniqueId', device_name);

            // 更新清单和已选中用户的提示文本
            $.douyin_fans.selected_online_user.push(device_name);
            var last_val = $('#selected_user_text').html();
            if (last_val === undefined || last_val == '') {
                last_val = row.user_name;
            } else {
                last_val += ', ' + row.user_name;
            }
            $('#selected_user_text').html(last_val);
        } catch (e) {
            // 进行异常提示
            $.ui_tools.alert(
                'function $.douyin_fans.select_user exception: ' + e.toString(),
                '告警信息', 'alert'
            );
        }
    };

    /**
     * 取消选中一个用户
     *
     * @param {string} device_name - 取消选中用户的设备号
     */
    $.douyin_fans.unselect_user = function (device_name) {
        try {
            // 先判断是否已在选中清单
            var index = $.douyin_fans.selected_online_user.indexOf(device_name);
            if (index < 0) {
                return;
            }

            // 更新清单和已选中用户的提示文本
            $.douyin_fans.selected_online_user.splice(index, 1);

            // 重新生成全部提示文本
            $.douyin_fans.set_selected_user_text();
        } catch (e) {
            // 进行异常提示
            $.ui_tools.alert(
                'function $.douyin_fans.select_user exception: ' + e.toString(),
                '告警信息', 'alert'
            );
        }
    };

    /**
     * 选中指定数量的用户
     * @param {float} percent - 要选择的比例分数, 全选传入1, 一半传入0.5
     */
    $.douyin_fans.select_batch_user = function (percent) {
        try {
            var per = 1;
            if (percent !== undefined) {
                per = percent;
            }
            var data_count = Number($('#online_user_count').html());
            // 计算要获取的用户数量
            var get_num = Math.ceil(data_count * percent);

            // 处理选取
            var table = $("#online_user_table");
            if (get_num >= data_count) {
                // 选中全部，先将所有信息加入选中信息
                $.douyin_fans.set_selected_user_text(
                    table.bootstrapTable('getData')
                );
                table.bootstrapTable('checkAll');
            } else if (get_num <= 0) {
                // 全部不选，取消选中
                $.douyin_fans.set_selected_user_text([]);
                table.bootstrapTable('uncheckAll');
            } else {
                // 随机选取
                var random_array = []; // 准备随机获取到的索引
                while (random_array.length < get_num) {
                    var n = Math.floor(Math.random() * data_count); // n为随机出现的 0-在线用户数 之内的数值
                    if (random_array.indexOf(n) >= 0) {
                        // 已找到过，重新获取
                        continue;
                    }
                    // 添加到清单中
                    random_array.push(n);
                }
                // 全部取消选中，再逐个选取
                $.douyin_fans.set_selected_user_text([]);
                table.bootstrapTable('uncheckAll');
                for (var i = 0; i < random_array.length; i++) {
                    table.bootstrapTable('check', random_array[i]);
                }
            }
        } catch (e) {
            // 进行异常提示
            $.ui_tools.alert(
                'function $.douyin_fans.select_batch_user exception: ' + e.toString(),
                '告警信息', 'alert'
            );
        }
    };

    /**
     * 发送聊天文本
     *
     * @param {string} text - 要发送的文本
     * @param {dom_obj} callobj - 调用方法的DOM对象
     */
    $.douyin_fans.send_chat = function (text, callobj) {
        if (callobj !== undefined) {
            // 临时屏蔽按钮，防止多次点击
            $(callobj).addClass("disabled");
        }
        try {
            if (text === undefined || text == '') {
                $.ui_tools.alert(
                    '请输入要发送的信息！', '告警信息', 'alert'
                );
                return;
            }
            // 默认参数设置
            var para = {};
            // 是否随机发送一个用户
            para.random = $('#send_mode_type_random').is(':checked');
            // 多用户发送是否间隔随机时间
            para.wait_bt_device = $('#send_mode_type_wait').is(':checked');

            // 获取用户
            var devices = [];
            if (para.random) {
                // 随机
                var selected_data = $('#online_user_table').bootstrapTable('getData');
                var data_count = selected_data.length;
                var n = Math.floor(Math.random() * data_count);
                devices.push(selected_data[n].device_name);
            } else {
                // 选中用户
                var selected_data = $('#online_user_table').bootstrapTable('getSelections');
                for (var i = 0; i < selected_data.length; i++) {
                    devices.push(selected_data[i].device_name);
                }
            }

            // 进行输入条件判断
            para.async = true;  // 统一使用异步模式
            if (devices.length == 0) {
                $.ui_tools.alert(
                    '未找到要发送的用户！', '告警信息', 'alert'
                );
                return;
            } else if (devices.length > 1) {
                // 批量发送采取异步模式
                para.async = true;
            }

            // 准备参数
            var url = '/api/DyControlApi/app_send_chat';
            json_data = {
                'interface_id': get_interface_id(),
                'devices': devices,
                'wait_bt_device': para.wait_bt_device,
                'text': text
            };

            // 发送Ajax
            $.douyin_fans.ajax_call(
                url, json_data, {
                    'tips': '发送聊天',
                    'success_not_alert': true,
                    'async': para.async,
                    'timeout': 1000000,
                    'success_fun': function (result) {
                        // 先处理失败的对象
                        var error_devices = [];
                        for(var i=0;i<result.error_info.length;i++){
                            // 添加到清单以便后面区分
                            error_devices.push(result.error_info[i].device_name);
                        }

                        // 处理成功对象
                        for(var i=0;i<devices.length;i++){
                            if (error_devices.indexOf(devices[i]) < 0){
                                add_chat_log(devices[i], text);
                            }
                        }

                        // 处理失败对象
                        for(var i=0;i<result.error_info.length;i++){
                            add_chat_log(result.error_info[i].device_name, text, result.error_info[i].error);
                        }
                        return [true, 'success'];
                    }
                }
            );

            // 根据是否异步判断如何提示
            if (para.async) {
                // 异步模式
                $.ui_tools.alert(
                    '正在后台执行发送聊天处理！', '提示', 'info', true, 1000
                );
            }
        } catch (e) {
            // 进行异常提示
            $.ui_tools.alert(
                'function $.douyin_fans.send_chat exception: ' + e.toString(),
                '告警信息', 'alert'
            );
        } finally {
            if (callobj !== undefined) {
                // 临时屏蔽按钮，防止多次点击
                setTimeout(function () {
                    $(callobj).removeClass('disabled');
                }, 10);
            }
        }
    };

    /**
     * 送小心心
     *
     * @param {dom_obj} callobj - 调用方法的DOM对象
     */
    $.douyin_fans.send_heart = function (callobj){
        if (callobj !== undefined) {
            // 临时屏蔽按钮，防止多次点击
            $(callobj).addClass("disabled");
        }
        try {
            // 默认参数设置
            var para = {};
            // 是否随机发送一个用户
            para.random = $('#send_mode_type_random').is(':checked');
            // 多用户发送是否间隔随机时间
            para.wait_bt_device = $('#send_mode_type_wait').is(':checked');

            // 获取用户
            var devices = [];
            if (para.random) {
                // 随机
                var selected_data = $('#online_user_table').bootstrapTable('getData');
                var data_count = selected_data.length;
                var n = Math.floor(Math.random() * data_count);
                devices.push(selected_data[n].device_name);
            } else {
                // 选中用户
                var selected_data = $('#online_user_table').bootstrapTable('getSelections');
                for (var i = 0; i < selected_data.length; i++) {
                    devices.push(selected_data[i].device_name);
                }
            }

            // 进行输入条件判断
            para.async = true;  // 统一使用异步模式
            if (devices.length == 0) {
                $.ui_tools.alert(
                    '未找到要送心心的用户！', '告警信息', 'alert'
                );
                return;
            } else if (devices.length > 1) {
                // 批量发送采取异步模式
                para.async = true;
            }

            // 准备参数
            var url = '/api/DyControlApi/app_send_heart';
            json_data = {
                'interface_id': get_interface_id(),
                'devices': devices,
                'wait_bt_device': para.wait_bt_device
            };

            // 发送Ajax
            $.douyin_fans.ajax_call(
                url, json_data, {
                    'tips': '送小心心',
                    'success_not_alert': true,
                    'async': para.async,
                    'timeout': 1000000,
                    'success_fun': function (result) {
                        // 先处理失败的对象
                        var error_devices = [];
                        for(var i=0;i<result.error_info.length;i++){
                            // 添加到清单以便后面区分
                            error_devices.push(result.error_info[i].device_name);
                        }

                        // 处理成功对象
                        for(var i=0;i<devices.length;i++){
                            if (error_devices.indexOf(devices[i]) < 0){
                                add_chat_log(devices[i], '{$送小心心$}');
                            }
                        }

                        // 处理失败对象
                        for(var i=0;i<result.error_info.length;i++){
                            add_chat_log(result.error_info[i].device_name, '{$送小心心$}', result.error_info[i].error);
                        }
                        return [true, 'success'];
                    }
                }
            );

            // 根据是否异步判断如何提示
            if (para.async) {
                // 异步模式
                $.ui_tools.alert(
                    '正在后台执行送小心心处理！', '提示', 'info', true, 1000
                );
            }
        } catch (e) {
            // 进行异常提示
            $.ui_tools.alert(
                'function $.douyin_fans.send_heart exception: ' + e.toString(),
                '告警信息', 'alert'
            );
        } finally {
            if (callobj !== undefined) {
                // 临时屏蔽按钮，防止多次点击
                setTimeout(function () {
                    $(callobj).removeClass('disabled');
                }, 10);
            }
        }
    };

    /**
     * 点击购物车
     *
     * @param {dom_obj} callobj - 调用方法的DOM对象
     */
    $.douyin_fans.click_car = function (callobj){
        if (callobj !== undefined) {
            // 临时屏蔽按钮，防止多次点击
            $(callobj).addClass("disabled");
        }
        try {
            // 默认参数设置
            var para = {};
            // 是否随机发送一个用户
            para.random = $('#send_mode_type_random').is(':checked');
            // 多用户发送是否间隔随机时间
            para.wait_bt_device = $('#send_mode_type_wait').is(':checked');

            // 获取用户
            var devices = [];
            if (para.random) {
                // 随机
                var selected_data = $('#online_user_table').bootstrapTable('getData');
                var data_count = selected_data.length;
                var n = Math.floor(Math.random() * data_count);
                devices.push(selected_data[n].device_name);
            } else {
                // 选中用户
                var selected_data = $('#online_user_table').bootstrapTable('getSelections');
                for (var i = 0; i < selected_data.length; i++) {
                    devices.push(selected_data[i].device_name);
                }
            }

            // 进行输入条件判断
            para.async = true;  // 统一使用异步模式
            if (devices.length == 0) {
                $.ui_tools.alert(
                    '未找到要点击购物车的用户！', '告警信息', 'alert'
                );
                return;
            } else if (devices.length > 1) {
                // 批量发送采取异步模式
                para.async = true;
            }

            // 准备参数
            var url = '/api/DyControlApi/app_click_car';
            json_data = {
                'interface_id': get_interface_id(),
                'devices': devices,
                'wait_bt_device': para.wait_bt_device
            };

            // 发送Ajax
            $.douyin_fans.ajax_call(
                url, json_data, {
                    'tips': '点击购物车',
                    'success_not_alert': true,
                    'async': para.async,
                    'timeout': 1000000,
                    'success_fun': function (result) {
                        // 先处理失败的对象
                        var error_devices = [];
                        for(var i=0;i<result.error_info.length;i++){
                            // 添加到清单以便后面区分
                            error_devices.push(result.error_info[i].device_name);
                        }

                        // 处理成功对象
                        for(var i=0;i<devices.length;i++){
                            if (error_devices.indexOf(devices[i]) < 0){
                                add_chat_log(devices[i], '{$点击购物车$}');
                            }
                        }

                        // 处理失败对象
                        for(var i=0;i<result.error_info.length;i++){
                            add_chat_log(result.error_info[i].device_name, '{$点击购物车$}', result.error_info[i].error);
                        }
                        return [true, 'success'];
                    }
                }
            );

            // 根据是否异步判断如何提示
            if (para.async) {
                // 异步模式
                $.ui_tools.alert(
                    '正在后台执行点击购物车处理！', '提示', 'info', true, 1000
                );
            }
        } catch (e) {
            // 进行异常提示
            $.ui_tools.alert(
                'function $.douyin_fans.click_car exception: ' + e.toString(),
                '告警信息', 'alert'
            );
        } finally {
            if (callobj !== undefined) {
                // 临时屏蔽按钮，防止多次点击
                setTimeout(function () {
                    $(callobj).removeClass('disabled');
                }, 10);
            }
        }
    };

    /**
     * 点击屏幕
     *
     * @param {dom_obj} callobj - 调用方法的DOM对象
     */
    $.douyin_fans.app_tap_screen = function (callobj){
        if (callobj !== undefined) {
            // 临时屏蔽按钮，防止多次点击
            $(callobj).addClass("disabled");
        }
        try {
            // 默认参数设置
            var para = {};
            // 是否随机发送一个用户
            para.random = $('#send_mode_type_random').is(':checked');
            // 多用户发送是否间隔随机时间
            para.wait_bt_device = $('#send_mode_type_wait').is(':checked');

            // 获取用户
            var devices = [];
            if (para.random) {
                // 随机
                var selected_data = $('#online_user_table').bootstrapTable('getData');
                var data_count = selected_data.length;
                var n = Math.floor(Math.random() * data_count);
                devices.push(selected_data[n].device_name);
            } else {
                // 选中用户
                var selected_data = $('#online_user_table').bootstrapTable('getSelections');
                for (var i = 0; i < selected_data.length; i++) {
                    devices.push(selected_data[i].device_name);
                }
            }

            // 进行输入条件判断
            para.async = true;  // 统一使用异步模式
            if (devices.length == 0) {
                $.ui_tools.alert(
                    '未找到要点击屏幕的用户！', '告警信息', 'alert'
                );
                return;
            } else if (devices.length > 1) {
                // 批量发送采取异步模式
                para.async = true;
            }

            // 准备参数
            var url = '/api/DyControlApi/app_tap_screen';
            json_data = {
                'interface_id': get_interface_id(),
                'devices': devices,
                'wait_bt_device': para.wait_bt_device
            };

            // 发送Ajax
            $.douyin_fans.ajax_call(
                url, json_data, {
                    'tips': '点击屏幕',
                    'success_not_alert': true,
                    'async': para.async,
                    'timeout': 1000000,
                    'success_fun': function (result) {
                        // 先处理失败的对象
                        var error_devices = [];
                        for(var i=0;i<result.error_info.length;i++){
                            // 添加到清单以便后面区分
                            error_devices.push(result.error_info[i].device_name);
                        }

                        // 处理成功对象
                        for(var i=0;i<devices.length;i++){
                            if (error_devices.indexOf(devices[i]) < 0){
                                add_chat_log(devices[i], '{$点击屏幕$}');
                            }
                        }

                        // 处理失败对象
                        for(var i=0;i<result.error_info.length;i++){
                            add_chat_log(result.error_info[i].device_name, '{$点击屏幕$}', result.error_info[i].error);
                        }
                        return [true, 'success'];
                    }
                }
            );

            // 根据是否异步判断如何提示
            if (para.async) {
                // 异步模式
                $.ui_tools.alert(
                    '正在后台执行点击屏幕处理！', '提示', 'info', true, 1000
                );
            }
        } catch (e) {
            // 进行异常提示
            $.ui_tools.alert(
                'function $.douyin_fans.app_tap_screen exception: ' + e.toString(),
                '告警信息', 'alert'
            );
        } finally {
            if (callobj !== undefined) {
                // 临时屏蔽按钮，防止多次点击
                setTimeout(function () {
                    $(callobj).removeClass('disabled');
                }, 10);
            }
        }
    };


    /**
     * 点赞
     *
     * @param {float}} seconds - 点赞的秒数
     */
    $.douyin_fans.app_give_thumbs_up = function(seconds){
        try {
            // 默认参数设置
            var para = {};
            // 是否随机发送一个用户
            para.random = $('#send_mode_type_random').is(':checked');
            // 多用户发送是否间隔随机时间
            para.wait_bt_device = $('#send_mode_type_wait').is(':checked');

            // 获取用户
            var devices = [];
            if (para.random) {
                // 随机
                var selected_data = $('#online_user_table').bootstrapTable('getData');
                var data_count = selected_data.length;
                var n = Math.floor(Math.random() * data_count);
                devices.push(selected_data[n].device_name);
            } else {
                // 选中用户
                var selected_data = $('#online_user_table').bootstrapTable('getSelections');
                for (var i = 0; i < selected_data.length; i++) {
                    devices.push(selected_data[i].device_name);
                }
            }

            // 进行输入条件判断
            para.async = true;
            if (devices.length == 0) {
                $.ui_tools.alert(
                    '未找到要点赞的用户！', '告警信息', 'alert'
                );
                return;
            }

            // 准备参数
            var url = '/api/DyControlApi/app_give_thumbs_up';
            json_data = {
                'interface_id': get_interface_id(),
                'devices': devices,
                'wait_bt_device': para.wait_bt_device,
                'seconds': seconds
            };

            // 发送Ajax
            $.douyin_fans.ajax_call(
                url, json_data, {
                    'tips': '点赞',
                    'success_not_alert': true,
                    'async': para.async,
                    'timeout': 1000000,
                    'success_fun': function (result) {
                        // 先处理失败的对象
                        var error_devices = [];
                        for(var i=0;i<result.error_info.length;i++){
                            // 添加到清单以便后面区分
                            error_devices.push(result.error_info[i].device_name);
                        }

                        // 处理成功对象
                        for(var i=0;i<devices.length;i++){
                            if (error_devices.indexOf(devices[i]) < 0){
                                add_chat_log(devices[i], '{$点赞$}');
                            }
                        }

                        // 处理失败对象
                        for(var i=0;i<result.error_info.length;i++){
                            add_chat_log(result.error_info[i].device_name, '{$点赞$}', result.error_info[i].error);
                        }
                        return [true, 'success'];
                    }
                }
            );


            // 异步模式
            $.ui_tools.alert(
                '正在后台执行送点赞处理！', '提示', 'info', true, 1000
            );
        } catch (e) {
            // 进行异常提示
            $.ui_tools.alert(
                'function $.douyin_fans.send_heart exception: ' + e.toString(),
                '告警信息', 'alert'
            );
        }
    };


    /**
     * 切换标签执行的动作
     * @param {JQuery} new_tab - 目标Tab页签的JQuery对象
     * @param {JQuery} pre_tab - 原Tab页签的JQuery对象
     */
    $.douyin_fans.on_toggle_tab = function (new_tab, pre_tab) {
        switch (new_tab.attr('id')) {
            case 'nav-config-tab':
                // 切换到配置页面，自动加载最新的配置信息
                $.douyin_fans.get_config(true);
                break;
        }
    };

    /**
     * 设备列表操作按钮执行函数
     * @param {string} action - 操作动作
     * @param {string} device_name - 当行的设备名
     * @param {int} index - 表格中的索引
     */
    $.douyin_fans.device_row_action = function (action, device_name, index) {
        switch (action) {
            case 'remove':
                // 删除设备
                device_action_remove(action, device_name, index);
                break;
            case 'connect':
                // 连接设备
                device_action_connect(action, device_name, index);
                break;
            case 'disconnect':
                // 断开设备
                device_action_disconnect(action, device_name, index);
                break;
            case 'bind_user':
                // 绑定抖音用户
                $('#device_bind_user').attr('row-id', device_name);
                $.ui_tools.show_modal('device_bind_user');
                break;
            case 'install':
                // 安装app
                $.douyin_fans.install_app(device_name);
                break;
            case 'in_line':
                // 进入直播间
                $.douyin_fans.into_app_line([device_name]);
                break;
            case 'out_line':
                // 退出直播间
                $.douyin_fans.out_app_line([device_name]);
                break;
        }
    };

    /**
     * 执行Ajax调用
     * @param {string} url - 要调用的接口url
     * @param {json} json_data - 要上传的json数据
     * @param {json} call_para - 调用参数，支持参数如下
     *   type {string} - http协议的调用方法: 'get', 'post', 默认为'post'
     *   content_type {string} - 内容格式, 默认为'application/json'
     *   headers {json} - Http协议头内容, 默认为 {}
     *   timeout {int} - 超时时间，单位为毫秒, 默认为10000
     *   async {bool} - 是否异步执行, 默认为 false
     *   tips {string} - 送入返回处理函数的提示信息, 默认为 ''
     *   success_not_alert {bool} - 成功交易不提示, 默认为false
     *   ajax_feedback {function} - 调用成功执行的反馈处理函数, 默认为 ajax_feedback_common
     *     如果自定义函数, 函数定义如下:
     *     function ajax_feedback_common(result, success_fun, tips){...}
     *     注意：函数送入的值分别为 结果json对象, 结果成功的执行函数(参考success_fun), 提示文本信息
     *   success_fun {function} - 结果成功的执行函数, 在调用ajax_feedback时通过参数送入
     *     如果自定义函数，函数定义如下：
     *     fun(result) {...; return [bool, msg];}
     *   ajax_error {function} - 调用异常的反馈处理函数, 默认为 ajax_error_common
     *     如果自定义函数, 函数定义如下：
     *      function ajax_error_common(xhr, status, error, tips){...; return;}
     */
    $.douyin_fans.ajax_call = function (url, json_data, call_para) {
        // 默认参数
        if (call_para === undefined) {
            call_para = {};
        }
        if (call_para.type === undefined) {
            call_para.type = 'post';
        }
        if (call_para.content_type === undefined) {
            call_para.content_type = 'application/json';
        }
        if (call_para.headers === undefined) {
            call_para.headers = {};
        }
        if (call_para.timeout === undefined) {
            call_para.timeout = 10000;
        }
        if (call_para.async === undefined) {
            call_para.async = false;
        }
        // 调用后的回调函数参数
        if (call_para.tips === undefined) {
            call_para.tips = '';
        }
        if (call_para.success_not_alert === undefined) {
            call_para.success_not_alert = false;
        }

        if (call_para.ajax_feedback === undefined) {
            call_para.ajax_feedback = ajax_feedback_common;
        }
        if (call_para.success_fun === undefined) {
            call_para.success_fun = function (result) {
                return [true, 'success'];
            };
        }
        if (call_para.ajax_error === undefined) {
            call_para.ajax_error = ajax_error_common;
        }

        // 执行Ajax
        $.ajax({
            url: url,
            type: call_para.type,
            contentType: call_para.content_type,
            headers: call_para.headers,
            data: JSON.stringify(json_data),
            timeout: call_para.timeout,
            async: call_para.async, // 异步处理
            success: function (result) {
                // 通过参数传入的函数执行
                call_para.ajax_feedback(result, call_para.success_fun, call_para.tips, call_para.success_not_alert);
            },
            error: function (xhr, status, error) {
                call_para.ajax_error(xhr, status, error, call_para.tips);
            }
        });
    };



    /** ---------------------------
     * 内部函数
     */

    /**
     * 生成接口ID
     */
    function get_interface_id() {
        return Math.uuid();
    };

    /**
     * 关闭已打开的loading界面
     */
    function close_loading_modal() {
        $.ui_tools.hide_modal();
    };

    /**
     * 通用的Ajax调用返回处理函数
     * @param {object} result - 返回的json对象
     * @param {function} success_fun - 成功的执行函数, 格式为:
     *      fun(result) {...; return [bool, msg]; }
     * @param {str} tips='' - 交易提示
     * @param {bool} success_not_alert=false - 成功交易不提示
     */
    function ajax_feedback_common(result, success_fun, tips, success_not_alert) {
        // 默认值
        if (tips === undefined) {
            tips = '';
        }
        if (success_not_alert === undefined) {
            success_not_alert = false;
        }


        var retObj = result;
        if (retObj.status == "00000") {
            // 返回成功
            deal_info = success_fun(retObj);
            if (deal_info === undefined || (deal_info != null && deal_info[0])) {
                // 处理成功
                if (!success_not_alert) {
                    // 设置自动隐藏
                    $.ui_tools.alert(
                        tips + '处理成功！', '提示', 'info', true
                    );
                }
            } else {
                // 处理失败
                $.ui_tools.alert(
                    tips + '处理失败: ' + deal_info[1], '告警信息', 'alert'
                );
            }
        } else {
            // 返回失败
            $.ui_tools.alert(
                tips + '返回失败[' + retObj.status + ']: ' + retObj.msg,
                '告警信息', 'alert'
            );
        }
    };

    /**
     * 通用的Ajax调用错误处理函数
     * @param {*} xhr
     * @param {*} status
     * @param {*} error
     * @param {str} tips='' - 交易提示
     */
    function ajax_error_common(xhr, status, error, tips) {
        // 默认值
        if (tips === undefined) {
            tips = '';
        }

        // 直接调用提示就好
        $.ui_tools.alert(
            tips + '处理异常: ' + error,
            '告警信息', 'alert'
        );
    };


    /**
     * 删除指定设备
     *
     * @param {array} device_list - 要删除的设备清单 ['设备名', '设备名', ...]
     * @param {bool} success_not_alert=false - 成功交易不提示
     *
     * @returns {bool} - 是否执行成功
     */
    function remove_devices(device_list, success_not_alert) {
        // 默认参数
        if (success_not_alert === undefined) {
            success_not_alert = false;
        }

        var run_result = false;
        try {
            // 准备参数
            var url = '/api/DyControlApi/remove_devices';
            var json_data = {
                'interface_id': get_interface_id(),
                'devices': device_list
            };

            // 调用Ajax
            $.douyin_fans.ajax_call(
                url, json_data, {
                    'tips': '删除设备',
                    'success_not_alert': success_not_alert,
                    'success_fun': function (result) {
                        run_result = true;
                        return [true, 'success'];
                    }
                }
            );
        } catch (e) {
            // 进行异常提示
            $.ui_tools.alert(
                'function $.douyin_fans.remove_devices exception: ' + e.toString(),
                '告警信息', 'alert'
            );
        }

        return run_result;
    };

    /**
     * 连接指定设备
     *
     * @param {array} device_list - 要连接的设备清单 ['设备名', '设备名', ...]
     * @param {bool} success_not_alert=false - 成功交易不提示
     *
     * @returns {[bool, error_info]} - [是否执行成功, 连接失败的信息]
     */
    function connect_devices(device_list, success_not_alert) {
        // 默认参数
        if (success_not_alert === undefined) {
            success_not_alert = false;
        }

        var run_result = false;
        var error_info = [];
        try {
            // 准备参数
            var url = '/api/DyControlApi/connect_devices';
            var json_data = {
                'interface_id': get_interface_id(),
                'devices': device_list
            };

            // 调用Ajax
            $.douyin_fans.ajax_call(
                url, json_data, {
                    'tips': '连接设备',
                    'success_not_alert': success_not_alert,
                    'success_fun': function (result) {
                        run_result = true;
                        error_info = result.error_info;
                        return [true, 'success'];
                    }
                }
            );
        } catch (e) {
            // 进行异常提示
            $.ui_tools.alert(
                'function $.douyin_fans.connect_devices exception: ' + e.toString(),
                '告警信息', 'alert'
            );
        }

        return [run_result, error_info];
    };

    /**
     * 断开连接指定设备
     *
     * @param {array} device_list - 要断开连接的设备清单 ['设备名', '设备名', ...]
     * @param {bool} success_not_alert=false - 成功交易不提示
     *
     * @returns {[bool, error_info]} - [是否执行成功, 连接失败的信息]
     */
    function disconnect_devices(device_list, success_not_alert) {
        // 默认参数
        if (success_not_alert === undefined) {
            success_not_alert = false;
        }

        var run_result = false;
        var error_info = [];
        try {
            // 准备参数
            var url = '/api/DyControlApi/disconnect_devices';
            var json_data = {
                'interface_id': get_interface_id(),
                'devices': device_list
            };

            // 调用Ajax
            $.douyin_fans.ajax_call(
                url, json_data, {
                    'tips': '断开设备连接',
                    'success_not_alert': success_not_alert,
                    'success_fun': function (result) {
                        run_result = true;
                        error_info = result.error_info;
                        return [true, 'success'];
                    }
                }
            );
        } catch (e) {
            // 进行异常提示
            $.ui_tools.alert(
                'function $.douyin_fans.disconnect_devices exception: ' + e.toString(),
                '告警信息', 'alert'
            );
        }

        return [run_result, error_info];
    };


    /** ---------------------------
     * 在线用户列表的操作按钮动作
     */
    function online_user_table_actionFormatter(value, row, index) {
        var device_name = row.device_name;
        var btn_html = '<button type="button" class="btn btn-primary btn-sm text-center p-0 mr-1" style="width:2em; height:2em;" herf="#" title="{$=title=$}" onclick="$.douyin_fans.out_app_line([\'' + device_name + '\']);">' +
            '<i class="bi-{$=image=$} m-0 p-0" style="font-size: 1.2rem; color:white; line-height:0px;"></i>' +
            '</button>';

        // 设置按钮图片
        var result = "";
        result += btn_html.replace(
            '{$=image=$}', 'camera-video-off'
        ).replace(
            '{$=title=$}', '退出直播'
        ).replace(
            '{$=action=$}', 'out_line'
        )

        return result;
    };



    /** ---------------------------
     * 设备列表的操作按钮动作
     */

    /**
     * 设备清单操作按钮样式处理函数
     * @param {*} value
     * @param {*} row
     * @param {*} index
     */
    function devices_table_actionFormatter(value, row, index) {
        var device_name = row.device_name;
        var btn_html = '<button type="button" class="btn btn-primary btn-sm text-center p-0 mr-1" style="width:2em; height:2em;" herf="#" title="{$=title=$}" onclick="$.douyin_fans.device_row_action(\'{$=action=$}\', \'' + device_name + '\', ' + index + ');">' +
            '<i class="bi-{$=image=$} m-0 p-0" style="font-size: 1.2rem; color:white; line-height:0px;"></i>' +
            '</button>';

        // 设置按钮图片
        var result = "";
        switch (row.connnect_status) {
            case 'started':
                // 已进入直播，显示退出直播按钮
                result += btn_html.replace(
                    '{$=image=$}', 'camera-video-off'
                ).replace(
                    '{$=title=$}', '退出直播'
                ).replace(
                    '{$=action=$}', 'out_line'
                )
                break;
            case 'connected':
                // 已连接设备, 显示进入直播按钮和断开连接按钮
                result += btn_html.replace(
                    '{$=image=$}', 'person-check'
                ).replace(
                    '{$=title=$}', '绑定抖音用户名'
                ).replace(
                    '{$=action=$}', 'bind_user'
                )

                if (row.use_anonymous || (row.user_name !== undefined && row.user_name != '')) {
                    // 如果绑定了绑定抖音用户
                    result += btn_html.replace(
                        '{$=image=$}', 'camera-video'
                    ).replace(
                        '{$=title=$}', '进入直播'
                    ).replace(
                        '{$=action=$}', 'in_line'
                    )
                }

                result += btn_html.replace(
                    '{$=image=$}', 'wifi-off'
                ).replace(
                    '{$=title=$}', '断开连接'
                ).replace(
                    '{$=action=$}', 'disconnect'
                )

                result += btn_html.replace(
                    '{$=image=$}', 'cloud-upload'
                ).replace(
                    '{$=title=$}', '安装抖音软件'
                ).replace(
                    '{$=action=$}', 'install'
                )
                break;
            default:
                // 未连接设备, 显示连接设备按钮和删除设备按钮
                result += btn_html.replace(
                    '{$=image=$}', 'person-check'
                ).replace(
                    '{$=title=$}', '绑定抖音用户名'
                ).replace(
                    '{$=action=$}', 'bind_user'
                )
                result += btn_html.replace(
                    '{$=image=$}', 'wifi'
                ).replace(
                    '{$=title=$}', '连接设备'
                ).replace(
                    '{$=action=$}', 'connect'
                )
                result += btn_html.replace(
                    '{$=image=$}', 'x-circle-fill'
                ).replace(
                    '{$=title=$}', '删除设备'
                ).replace(
                    '{$=action=$}', 'remove'
                )
                break;
        }

        return result;
    };

    /**
     * 删除按钮动作函数
     *
     * @param {string} action - 操作动作
     * @param {string} device_name - 当行的设备名
     * @param {int} index - 表格中的索引
     */
    function device_action_remove(action, device_name, index) {
        // 提示是否删除
        if (!window.confirm("请确认是否删除设备[" + device_name + "]?")) {
            return;
        }

        // 显示loading
        $('#devices_table').bootstrapTable('showLoading');
        try {
            // 准备参数
            var device_list = [device_name, ];
            var result = remove_devices(device_list, false);
            if (result) {
                // 服务端删除成功, 终端删除设备显示
                $('#devices_table').bootstrapTable('removeByUniqueId', device_name);
            }
        } catch (e) {
            // 进行异常提示
            $.ui_tools.alert(
                'function device_action_remove exception: ' + e.toString(),
                '告警信息', 'alert'
            );
        } finally {
            // 关闭loading必须通过异步方式执行才能关闭
            setTimeout(function () {
                $('#devices_table').bootstrapTable('hideLoading');
            }, 10);
        }
    };

    /**
     * 连接按钮动作函数
     *
     * @param {string} action - 操作动作
     * @param {string} device_name - 当行的设备名
     * @param {int} index - 表格中的索引
     */
    function device_action_connect(action, device_name, index) {
        // 显示loading
        $('#devices_table').bootstrapTable('showLoading');
        try {
            // 准备参数
            var device_list = [device_name, ];
            var result = connect_devices(device_list, false);
            if (!result[0]) {
                // 调用失败
                return;
            }

            // 调用成功进行后续判断处理
            if (result[1].length > 0) {
                // 处理失败，提示
                $.ui_tools.alert(
                    '连接设备失败: ' + result[1][0].error,
                    '告警信息', 'alert'
                );
                return;
            }

            // 调用成功，刷新状态（不更新其他字段，均以服务端为准）
            $('#devices_table').bootstrapTable(
                'updateCellByUniqueId', {
                    id: device_name,
                    field: 'connnect_status',
                    value: 'connected'
                }
            );

        } catch (e) {
            // 进行异常提示
            $.ui_tools.alert(
                'function device_action_connect exception: ' + e.toString(),
                '告警信息', 'alert'
            );
        } finally {
            // 关闭loading必须通过异步方式执行才能关闭
            setTimeout(function () {
                $('#devices_table').bootstrapTable('hideLoading');
            }, 10);
        }
    };

    /**
     * 断开连接按钮动作函数
     *
     * @param {string} action - 操作动作
     * @param {string} device_name - 当行的设备名
     * @param {int} index - 表格中的索引
     */
    function device_action_disconnect(action, device_name, index) {
        // 显示loading
        $('#devices_table').bootstrapTable('showLoading');
        try {
            // 准备参数
            var device_list = [device_name, ];
            var result = disconnect_devices(device_list, false);
            if (!result[0]) {
                // 调用失败
                return;
            }

            // 调用成功进行后续判断处理
            if (result[1].length > 0) {
                // 处理失败，提示
                $.ui_tools.alert(
                    '断开设备连接失败: ' + result[1][0].error,
                    '告警信息', 'alert'
                );
                return;
            }

            // 调用成功，刷新状态（不更新其他字段，均以服务端为准）
            $('#devices_table').bootstrapTable(
                'updateCellByUniqueId', {
                    id: device_name,
                    field: 'connnect_status',
                    value: 'unconnect'
                }
            );

        } catch (e) {
            // 进行异常提示
            $.ui_tools.alert(
                'function device_action_disconnect exception: ' + e.toString(),
                '告警信息', 'alert'
            );
        } finally {
            // 关闭loading必须通过异步方式执行才能关闭
            setTimeout(function () {
                $('#devices_table').bootstrapTable('hideLoading');
            }, 10);
        }
    };


    /** ---------------------------
     * 后台管理界面的内部操作函数
     */

    /**
     * 添加发送聊天记录
     *
     * @param {string} device_name - 设备号
     * @param {string} text - 发送的文本
     * @param {string} error_msg - 发送失败的错误信息
     */
    function add_chat_log(device_name, text, error_msg){
        var html = '<div>{user_name}&nbsp;&nbsp;{send_time}' +
            '<div class="alert alert-{color}" role="alert">{send_chat}{error}</div>'+
        '</div>';
        var user_name = $('#devices_table').bootstrapTable('getRowByUniqueId', device_name).user_name;
        var d = new Date();
        var hour = d.getHours() < 10 ? '0' + d.getHours() : d.getHours();
        var minutes = d.getMinutes() < 10 ? '0' + d.getMinutes() : d.getMinutes();
        var second = d.getSeconds() < 10 ? '0' + d.getSeconds() : d.getSeconds();
        var send_time = hour + ':' + minutes + ':' + second;
        var color = 'primary';
        if (error_msg !== undefined){
            color = 'danger';
            error_msg = '<br>发送失败: ' + error_msg;
        }
        else{
            error_msg = '';
        }
        html = html.replace(
            '{user_name}', user_name
        ).replace(
            '{send_time}', send_time
        ).replace('{color}', color).replace('{send_chat}', text).replace('{error}', error_msg);

        // 添加到记录框
        $('#chat_log').append(html);
        setTimeout(function() {
            $("#chat_log").scrollTop($("#chat_log")[0].scrollHeight);
         }, 10);
    };



})(jQuery);