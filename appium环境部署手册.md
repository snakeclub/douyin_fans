# appium环境部署手册

## appium介绍

开源地址：https://github.com/appium/appium/

官网：http://appium.io/

appium 是一个自动化测试开源工具，支持 iOS 平台和 Android 平台上的原生应用，web应用和混合应用。

- “移动原生应用”是指那些用iOS或者 Android SDK 写的应用（Application简称app）。
- “移动web应用”是指使用移动浏览器访问的应用（appium支持iOS上的Safari和Android上的 Chrome）。
- “混合应用”是指原生代码封装网页视图——原生代码和 web 内容交互。比如，像 Phonegap，可以帮助开发者使用网页技术开发应用，然后用原生代码封装，这些就是混合应用。

重要的是，appium是一个跨平台的工具：它允许测试人员在不同的平台（iOS，Android）使用同一套API来写自动化测试脚本，这样大大增加了iOS和Android测试套件间代码的复用性。

![img](appium%E7%8E%AF%E5%A2%83%E9%83%A8%E7%BD%B2%E6%89%8B%E5%86%8C.assets/appium_principle.png)

通过上面一张图简单展示了appium的工具原理。

首先，appium支持多语言，因为它针对流的几种语言分别开发的相应的appium库。好处就是我们可以选择自己熟悉的语言编写appium脚本。

其次，appium支持多平台，包括MAC和Windows。它针对这两大平台开发了appium-Server。

最后，appium又同时支持Android 和 iOS两个操作系统。

这就使得appium变得非常灵活。



## 安装JDK

1、进入官网下载页面：https://www.oracle.com/java/technologies/javase/javase-jdk8-downloads.html

2、找到Windows对应版本的下载连接，进行下载：[jdk-8u271-windows-x64.exe](https://www.oracle.com/java/technologies/javase/javase-jdk8-downloads.html#license-lightbox)

3、执行下载安装文件，执行JDK的安装，使用默认安装选项即可；

4、配置系统环境变量，新增 JAVA_HOME 环境变量，值为安装目录（注意我安装的是openjdk，所以路径不一样），参考如下：C:\Program Files\RedHat\java-1.8.0-openjdk-1.8.0.232-3

5、配置系统环境变量，在 Path 环境变量中增加以下3个值：

```
%JAVA_HOME%\bin
%JAVA_HOME%\lib\tools.jar
%JAVA_HOME%\jre\bin
```

6、验证安装，在cmd窗口执行以下命令能正常出现版本信息，代表安装成功

```
java -version
javac -version
```



## 安装Android SDK

安卓app的自动化  appium server 依赖 android sdk，安装步骤如下：

1、到以下网站下载安装：https://www.androiddevtools.cn/

<img src="appium%E7%8E%AF%E5%A2%83%E9%83%A8%E7%BD%B2%E6%89%8B%E5%86%8C.assets/image-20201117130204844.png" alt="image-20201117130204844" style="zoom: 33%;" />

<img src="appium%E7%8E%AF%E5%A2%83%E9%83%A8%E7%BD%B2%E6%89%8B%E5%86%8C.assets/image-20201117130437558.png" alt="image-20201117130437558" style="zoom:33%;" />

2、执行安装操作；

3、运行安装的SDK Manager，勾选前三项，以及 Extras 的 Google USB Driver，共四项，点击右下角的 Install 4 packages... 按钮（在Win10里显示好像有点问题，不过不影响操作）：

<img src="appium%E7%8E%AF%E5%A2%83%E9%83%A8%E7%BD%B2%E6%89%8B%E5%86%8C.assets/image-20201117153644835.png" alt="image-20201117153644835" style="zoom:33%;" />

<img src="appium%E7%8E%AF%E5%A2%83%E9%83%A8%E7%BD%B2%E6%89%8B%E5%86%8C.assets/image-20201117153840947.png" alt="image-20201117153840947" style="zoom:33%;" />

<img src="appium%E7%8E%AF%E5%A2%83%E9%83%A8%E7%BD%B2%E6%89%8B%E5%86%8C.assets/image-20201117154122483.png" alt="image-20201117154122483" style="zoom:33%;" />

**注：如果执行过程中出现创建目录错误的提示，有可能是因为权限不够，可以使用管理员模式方式打开程序来执行。**

4、添加环境变量，新建 ANDROID_HOME ，取值为sdk tools的安装目录：C:\Program Files (x86)\Android\android-sdk

5、配置系统环境变量，在 Path 环境变量中增加以下2个值：

```
%ANDROID_HOME%\tools
%ANDROID_HOME%\platform-tools
```

6、验证安装，在cmd窗口执行以下命令能正常出现版本信息，代表安装成功

```
adb version
```



## 安装appium

可以通过两种方式安装appium，通过NPM安装，或者下载 [Appium Desktop](https://github.com/appium/appium-desktop) 进行图形化的安装。

### 通过NPM安装

```
npm install -g appium
```

**注：需要使用 NODE 10+ 的版本**

### 通过Appium Desktop安装

1、下载最新版本的安装包（我们下载的是win版本的安装包，exe那个），下载地址：https://github.com/appium/appium-desktop/releases/latest

2、直接执行进行安装就好

注：如果是win10出现路径过长不支持的问题，需要 “[enable long paths](https://superuser.com/questions/1119883/windows-10-enable-ntfs-long-paths-policy-option-missing)” 来支持长安装路径，参考微软的手册就好；win10家庭版不支持 “gpedit.msc” ，可以在网上找到开启的办法，不过一般不用处理。

### 支持 UiAutomator2 需要执行的操作

Appium 支持使用 UiAutomator2 引擎（启动时使用 'automationName': 'UiAutomator2' 参数），该引擎比Appium默认引擎的执行效率相对来说高一些，但是直接安装 Appium 后使用该引擎会有报错的情况，需要执行相应的操作解决该问题：

**Appium Desktop 操作方法：**

1、进入Appium Desktop的安装目录（例如：C:\Program Files\Appium\），再进入该安装目录下的以下路径  resources\app\node_modules\appium\node_modules\appium-uiautomator2-server\apks ，复制以下两个apk文件：

```
appium-uiautomator2-server-debug-androidTest.apk
appium-uiautomator2-server-v4.12.2.apk
```

2、同样找到安装目录下的 resources\app\node_modules\appium\node_modules\appium-uiautomator2-driver 目录，在该目录下新建 uiautomator2 目录，然后将上面的两个文件复制到该目录下。

**命令行的操作方法（NPM安装）：**

1、进入npm的安装目录（例如：C:\Users\用户名\AppData\Roaming\npm）再进入该安装目录下的以下路径  node_modules\appium\node_modules\appium-uiautomator2-server\apks ，复制以下两个apk文件：

```
appium-uiautomator2-server-debug-androidTest.apk
appium-uiautomator2-server-v4.12.2.apk
```

2、同样找到安装目录下的 node_modules\appium\node_modules\appium-uiautomator2-driver 目录，在该目录下新建 uiautomator2 目录，然后将上面的两个文件复制到该目录下。

**注：如果安装的是nvm，对应的安装目录应该是：C:\Users\用户名\AppData\Roaming\nvm\npm**



## 安装appium client

appium支持多种语言的客户端，支持的客户端列表清单查看地址：http://appium.io/docs/en/about-appium/appium-clients/index.html

由于习惯原因，我选择安装python版本的客户端，可以直接使用pypi安装：

```
pip install Appium-Python-Client
```



## 安装安卓模拟器

大家可以自行选择喜欢的安卓模拟器，这里选用的是逍遥模拟器：http://www.xyaz.cn/

1、下载工作室版的安装包：https://www.xyaz.cn/download.php?file_name=XYAZ-Setup-studio-7.2.9-ha5fe23789&from=home

2、运行安装包进行安装

3、复制 C:\Program Files (x86)\Android\android-sdk\platform-tools 目录下的 adb.exe 复制出来，改名为xy_adb，放置至逍遥模拟器的安装目录 C:\Program Files\Microvirt\MEmu 

4、配置环境变量，将逍遥模拟器的安装目录配置到 Path中 ：C:\Program Files\Microvirt\MEmu

注：不同模拟器的端口不一致

```
1、木木： 7555
2、夜神： 62001
3、海马：53001
4、逍遥：21503
5、天天：6555
6、雷电、genymotion、谷歌原生：5555
```



## 使用appium-desktop连接安卓模拟器

1、启动逍遥模拟器，我们启动逍遥多开器，尝试开两个模拟器：

（1）按下图操作生成两个7.1版本的模拟器：

<img src="appium%E7%8E%AF%E5%A2%83%E9%83%A8%E7%BD%B2%E6%89%8B%E5%86%8C.assets/image-20201117200626555.png" alt="image-20201117200626555" style="zoom:33%;" />

（2）勾选两个模拟器，点击设置按钮，将显示设置为手机模式，批量修改并生效：

<img src="appium%E7%8E%AF%E5%A2%83%E9%83%A8%E7%BD%B2%E6%89%8B%E5%86%8C.assets/image-20201117201121271.png" alt="image-20201117201121271" style="zoom:33%;" />

（3）勾选两个模拟器，点击启动按钮，启动两个安卓模拟器；然后人工点击关闭自动启动的桌面向导和应用市场，让模拟器状态为正常桌面：

<img src="appium%E7%8E%AF%E5%A2%83%E9%83%A8%E7%BD%B2%E6%89%8B%E5%86%8C.assets/image-20201117201455495.png" alt="image-20201117201455495" style="zoom:33%;" />



2、通过 adb 命令连接两个模拟器，正常情况这两个模拟器启动后是自动连接的，可以通过以下命令查看已连接的安卓模拟器：

```
>xy_adb devices -l
List of devices attached
127.0.0.1:21503        device product:HD1910 model:HD1910 device:HD1910
127.0.0.1:21513        device product:PCRT00 model:PCRT00 device:PCRT00
```

如果模拟器已打开，但 adb devices -l 没有连接，可以通过以下命令主动连接上设备：

```
xy_adb connect 127.0.0.1:21503
```

注意：可以通过模拟器的配置文件查看IP和端口，查看方法如下：

（1）打开模拟器目录，例如 “C:\Program Files\Microvirt\MEmu\MemuHyperv VMs\MEmu”，如果多个模拟器，后面几个模拟器的目录分别为 MEmu1、MEmu2、……

（2）用记事本打开配置文件 MEmu.memu-prev

（3）找到以下内容，其中ADB这行的 hostip 和 hostport 就是我们需要连接的设备IP和端口：

```
<NAT>
    <Forwarding name="ADB" proto="1" hostip="127.0.0.1" hostport="21503" guestip="10.0.2.15" guestport="5555"/>
    <Forwarding name="MVD" proto="1" hostip="127.0.0.1" hostport="21501" guestip="10.0.2.15" guestport="21501"/>
</NAT>
```

3、启动appium-desktop，按照默认配置点击启动服务器：

<img src="appium%E7%8E%AF%E5%A2%83%E9%83%A8%E7%BD%B2%E6%89%8B%E5%86%8C.assets/image-20201117201926637.png" alt="image-20201117201926637" style="zoom:33%;" />

4、在服务器运行窗口中，点击菜单 File -> New Session Window... ，创建一个新的会话窗口：

<img src="appium%E7%8E%AF%E5%A2%83%E9%83%A8%E7%BD%B2%E6%89%8B%E5%86%8C.assets/image-20201117202157159.png" alt="image-20201117202157159" style="zoom:33%;" />

5、点击窗口右下角的JSON编辑窗口的编辑按钮，填入连接配置JSON信息，然后保存，保存后左边的设置栏位正常显示每个值才代表成功修改，这时候点击“启动会话”按钮启动连接：

<img src="appium%E7%8E%AF%E5%A2%83%E9%83%A8%E7%BD%B2%E6%89%8B%E5%86%8C.assets/image-20201117202421978.png" alt="image-20201117202421978" style="zoom:33%;" />

JSON如下：

```
{
  "platformName": "Android",
  "platformVersion": "7.1",
  "deviceName": "127.0.0.1:21503",
  "noReset": true
}
```

详细配置参考官网文档：http://appium.io/docs/cn/writing-running-appium/caps/

注意：

- platformVersion - 安卓版本，我们连接的是7.1版本
- deviceName - 设备连接信息，可以从 adb devices -l 查看到，连接的第1台模拟器为 127.0.0.1:21503
- **必须是通过 xy_adb 命令连接的模拟器，才可以通过appium连接上**

 6、有可能因为超时的原因，adb 连接设备会失效，这时候可以通过命令 “xy_adb connect 127.0.0.1:21503” 手工进行连接，可以通过以下方式查看每个模拟器监听的端口：

（1）依次打开：任务管理器–性能–打开资源监视器–网络–侦听端口

（2）查找MEmuHeadless.exe对应的端口，可以看到端口分别是21503、21513（其他两个端口实际为模拟器占用的端口，无需处理）：

<img src="appium%E7%8E%AF%E5%A2%83%E9%83%A8%E7%BD%B2%E6%89%8B%E5%86%8C.assets/image-20201117203546490.png" alt="image-20201117203546490" style="zoom:33%;" />

7、通过同样的操作，可以连接上第二个模拟器 ”127.0.0.1:21513“，这样就可以通过 appium-desktop 分析安卓手机元素的访问路径，执行对应的操作：

<img src="appium%E7%8E%AF%E5%A2%83%E9%83%A8%E7%BD%B2%E6%89%8B%E5%86%8C.assets/image-20201117204339641.png" alt="image-20201117204339641" style="zoom:33%;" />

8、如果需要打开模拟器时自动开启要测试的app，可以通过 appPackage 和 appActivity 进行控制；要获取app的这两个参数，可以打开一个模拟器，通过 xy_adb 命令连接以后，执行以下命令查看（以打开浏览器为例）：

```
> xy_adb connect 127.0.0.1:21503
connected to 127.0.0.1:21503

> xy_adb shell dumpsys window windows | findstr mFocusedApp
  mFocusedApp=AppWindowToken{3a42810 token=Token{468dec2 ActivityRecord{4859f0d u0 com.android.browser/.BrowserActivity t16}}}
```

这样在appium的会话配置中，增加这两个信息，就可以在启动时打开相应的应用：

```
{
  "platformName": "Android",
  "platformVersion": "7.1",
  "deviceName": "127.0.0.1:21513",
  "appPackage": "com.android.browser",
  "appActivity": ".BrowserActivity",
  "noReset": true
}

{
  "platformName": "Android",
  "platformVersion": "7.1",
  "deviceName": "127.0.0.1:21503",
  "appPackage": "com.ss.android.ugc.aweme",
  "appActivity": ".splash.SplashActivity",
  "noReset": true
}
```



## 使用Appium-Python-Client连接安卓模拟器

通过以下的代码，打开安卓模拟器的浏览器，打开百度页面，并进行向上滑动：

```
import time
from appium import webdriver

desired_caps = {
    'platformName': 'Android',  # 被测手机是安卓
    'platformVersion': '7.1',  # 模拟器安卓版本
    'deviceName': '127.0.0.1:21513',  # 设备名，安卓手机可以随意填写
    'appPackage': 'com.android.browser',  # 启动APP Package名称
    'appActivity': '.BrowserActivity',  # 启动Activity名称
    'noReset': True       # 不要重置App，防止登录信息丢失
}
driver = webdriver.Remote('http://localhost:4723/wd/hub', desired_caps)  # 连接模拟器
driver.implicitly_wait(5)  # 设置隐式等待的时长（查找元素的时间）
el_url = driver.find_element_by_id("com.android.browser:id/url")  # 找到url输入框
el_url.clear()  # 清空输入框内容
el_url.click()  # 点击将焦点放置在输入框
el_url.send_keys("www.baidu.com")  # 输入要打开的网站
driver.press_keycode(66)  # 发送回车按键，执行网页浏览
time.sleep(5)  # 等待页面加载
size = driver.get_window_size()
x1 = int(size['width'] * 0.5)
y1 = int(size['height'] * 0.9)
y2 = int(size['height'] * 0.1)
driver.swipe(x1, y1, x1, y2, 500)  # 向上滑动
time.sleep(5)  # 等待展示
driver.quit()  # 关闭连接
```



## 使用appium-desktop连接安卓真机

1、打开手机的 设置 -> 系统 -> 开发人员选项 -> 调试，设置为 USB 调试模式；

2、通过数据线连接电脑的USB；

3、在命令行执行 adb devices -l ，正常情况可以识别到设备信息：

```
C:\Program Files\Microvirt\MEmu>adb devices -l
List of devices attached
WGY0217527000271       device product:LON-AL00 model:LON_AL00 device:HWLON
```

4、参照 ”使用appium-desktop连接安卓模拟器“ 章节进行连接即可，例如真机的连接JSON如下：

```
{
  "platformName": "Android",
  "platformVersion": "9",
  "deviceName": "WGY0217527000271",
  "noReset": true
}
```



## Appium Studio进行测试

这个工具的官网上是这么介绍的：让Appium测试项目在几分钟内完成，只需单击一下即可安装Appium Studio以及所有必需的开发工具。 使用直观的GUI轻松开发新测试或在任何本地或远程设备上执行现有的Appium测试项目。

这是一个可以录制脚本，可以运行测试用例，**它可以在windows电脑上，链接ios设备做ios的测试**，这样我们测试ios应用不在用ios设备也能进行测试了。

 Appium Studio目前集成在SeeTest工具包中，安装SeeTest也会同步把Appium Studio装上，安装和使用步骤如下：

1、下载软件安装包

社区版网站：https://experitest.com/mobile-test-automation/appium-studio/

社区版下载地址（版本比较低）：https://d242m5chux1g9j.cloudfront.net/12.6_Official/AppiumStudio_windows_12_6_5233.exe

企业版（只有30天试用期）：

各版本下载地址：https://experitest.com/release-notes/

镜像下载地址：https://d242m5chux1g9j.cloudfront.net/20.10_Official/SeeTest_windows-x32_20_10_7516.exe

2、执行安装程序进行安装；

3、找到安装目录，从 ”Experitest\SeeTest\bin\adb“ 中的 adb.exe 文件改名为 st_adb.exe 并移动到模拟器安装目录 C:\Program Files\Microvirt\MEmu 中（解决adb版本不匹配的问题）；

4、运行 st_adb connect 127.0.0.1:21503 连接安卓模拟器；

5、运行安装的快捷方式 AppiumStudioEnterprise 启动 AppiumStudio；

6、添加手机和录制的功能按钮见下图显示，具体操作可参考：https://blog.csdn.net/xyd_113/article/details/94746593

![image-20201118164849954](appium%E7%8E%AF%E5%A2%83%E9%83%A8%E7%BD%B2%E6%89%8B%E5%86%8C.assets/image-20201118164849954.png)

**注：连接安卓模拟器后，手机的界面不会进行刷新显示，不清楚是什么原因导致；但连接真机不会有这个问题**



## 使用adb操作多个devices

如果有多个模拟器/设备实例在运行，在发布adb命令时需要指定一个目标实例。使用adb -s实现：

```
adb -s <serialNumber> <command>`

例如：
adb -s 127.0.0.1:6555 logcat  //此命令用来查看6555设备的logcat信息
adb -s 127.0.0.1:30054 shell    //此命令进入到30054设备的shell模式
```



## 自动测试需要用到的其他工具

https://github.com/senzhk/ADBKeyBoard