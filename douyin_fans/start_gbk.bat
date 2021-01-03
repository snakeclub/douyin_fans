@echo off

REM 跳转到脚本当前文件夹
cd  %~dp0

REM 执行启动服务命令
python server.py

REM 暂停，等待关闭
@echo on
pause