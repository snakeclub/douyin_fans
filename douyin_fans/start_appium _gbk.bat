@echo off

REM ��ת���ű���ǰ�ļ���
cd  %~dp0

REM ִ��������������
appium --session-override --relaxed-security

REM ��ͣ���ȴ��ر�
@echo on
pause