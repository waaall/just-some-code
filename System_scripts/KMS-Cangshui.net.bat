@echo off
mode con cols=85 lines=35
ver | find "°æ±¾" > NUL && title ²×Ë®µÄKMS½Å±¾ V24.10.24 || title Cangshui's KMS script V24.10.24
setlocal EnableDelayedExpansion&color 70 & cd /d "%~dp0"
%1 %2
ver | find "5."> NUL && goto :start

setlocal
set uac=~uac_permission_tmp_%random%
md "%SystemRoot%\system32\%uac%" 2>nul
if %errorlevel%==0 ( rd "%SystemRoot%\system32\%uac%" >nul 2>nul ) else (
    echo set uac = CreateObject^("Shell.Application"^)>"%temp%\%uac%.vbs"
    echo uac.ShellExecute "%~s0","","","runas",1 >>"%temp%\%uac%.vbs"
    echo WScript.Quit >>"%temp%\%uac%.vbs"
    "%temp%\%uac%.vbs" /f
    del /f /q "%temp%\%uac%.vbs" & exit )
endlocal

:start
chcp 936 > NUL
for /f "tokens=3 delims= " %%i in ('reg QUERY "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion" /v "CurrentBuild"') do set CurrentBuild=%%i
if  %CurrentBuild% LEQ 17762 (
  set systabs=0
) else (
  set systabs=1
)
set KMS_Sev=kms-shanghai01.cangshui.net
ver | find "6.0." > NUL &&  set winv=vista
ver | find "6.1." > NUL &&  set winv=7
ver | find "6.2." > NUL &&  set winv=8
ver | find "6.3." > NUL &&  set winv=8.1
ver | find "10.0." > NUL &&  set winv=10
ver | find "°æ±¾" >NUL && set syslang=cn
ver | find "°æ±¾" >nul && echo ÌáÎÊ½¨ÒéÇëÁôÑÔhttp://kms.cangshui.net || echo Feedback and Tip: http://kms.cangshui.net
ver | find "°æ±¾" >nul && echo ¾èÔùÔÞÖúÇë·ÃÎÊhttp://shop.cangshui.net
echo.
ver | find "°æ±¾" >nul && echo ¨X¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨TÖªÊ¶¹²ÏíÐí¿ÉÐ­Òé¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨[|| echo ¨X¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨TCreative Commons License Agreement¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨[
ver | find "°æ±¾" >nul && echo ¨U ²×Ë®µÄKMS½Å±¾ ÓÉ Cangshui ²ÉÓÃ ÖªÊ¶¹²Ïí                                          ¨U || echo ¨U Cangshui's KMS script by Cangshui is licensed under a Creative Commons           ¨U
ver | find "°æ±¾" >nul && echo ¨U ÊðÃû-·ÇÉÌÒµÐÔÊ¹ÓÃ-ÏàÍ¬·½Ê½¹²Ïí 4.0 ¹ú¼Ê Ðí¿ÉÐ­Òé½øÐÐÐí¿É¡£                       ¨U || echo ¨U Attribution-NonCommercial-ShareAlike 4.0 International License.                  ¨U
echo.
if  "%syslang%"=="cn" (
  if  "%systabs%"=="1" ( echo ¨X¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¼¤»îÑ¡Ïî¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨[ )
  echo ¨U¡¾A¡¿KMS¼¤»îWindows                                                               ¨U
  echo ¨U¡¾B¡¿KMS¼¤»îOffice                                                                ¨U
  echo ¨U¡¾C¡¿Çå³ýWindows KMS                                                              ¨U
  echo ¨U¡¾D¡¿Çå³ýOffice KMS                                                               ¨U
  echo ¨U¡¾E¡¿²é¿´Ö§³ÖµÄwindows°æ±¾                                                        ¨U
  ) else (
  if  "%systabs%"=="1" ( echo ¨X¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨TActivation option¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨[ )
  echo ¨U[A] KMS activate windows                                                          ¨U
  echo ¨U[B] KMS activate Office                                                           ¨U
  echo ¨U[C] Clear Windows KMS                                                             ¨U
  echo ¨U[D] Clear Office KMS                                                              ¨U
  echo ¨U[E] Supported windows version                                                     ¨U
)
if  "%syslang%"=="cn" (
  if  "%systabs%"=="1" ( echo ¨d¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨TÆäËû¹¤¾ß¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨g )
  echo ¨U¡¾1¡¿È¥³ýOfficeÏÔÊ¾¡°Ðí¿ÉÖ¤²¢·ÇÕý°æ¡±                                             ¨U 
  echo ¨U¡¾2¡¿È¥³ý¿ì½Ý·½Ê½Ð¡¼ýÍ·                                                           ¨U
  echo ¨U¡¾3¡¿»Ö¸´¿ì½Ý·½Ê½Ð¡¼ýÍ·                                                           ¨U
  echo ¨U¡¾4¡¿Win11ÇÐ»»¾É°æ×ÀÃæÓÒ¼ü²Ëµ¥                                                    ¨U
  echo ¨U¡¾5¡¿Win11»Ö¸´ÐÂ°æ×ÀÃæÓÒ¼ü²Ëµ¥                                                    ¨U 
  echo ¨U¡¾6¡¿È¥³ý¿ì½Ý·½Ê½Ð¡¶ÜÅÆ                                                           ¨U
  echo ¨U¡¾7¡¿»Ö¸´¿ì½Ý·½Ê½Ð¡¶ÜÅÆ                                                           ¨U 
  echo ¨U¡¾8¡¿È¥³ý´´½¨¿ì½Ý·½Ê½Ê±µÄºó×º¡°-¿ì½Ý·½Ê½¡±                                        ¨U
  echo ¨U¡¾9¡¿È¥³ýÔËÐÐ¿ÉÖ´ÐÐÎÄ¼þÊ±µÄ¾¯¸æµ¯´°                                               ¨U
  echo ¨U¡¾10¡¿Ïò×ÀÃæÌí¼Ó¡°´ËµçÄÔ¡±Í¼±ê                                                    ¨U
  if  "%systabs%"=="1" ( echo ¨d¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨TÊäÈëÑ¡Ôñ¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨g )
  ) else (
  if  "%systabs%"=="1" ( echo ¨X¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨TOther Tool¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨[ )
  echo ¨U[1] Remove Office from showing "License is not genuine"                           ¨U 
  echo ¨U[2] Removing the shortcut arrow                                                   ¨U
  echo ¨U[3] Restore shortcut small arrow                                                  ¨U
  echo ¨U[4] Win11 switch the old desktop right-click menu                                 ¨U
  echo ¨U[5] Win11 restores the new version of the desktop right-click menu                ¨U 
  echo ¨U[6] Remove shortcut small shield                                                  ¨U
  echo ¨U[7] Restore shortcut small shield                                                 ¨U 
  echo ¨U[8] Remove the suffix "-shortcut" when creating shortcuts                         ¨U
  echo ¨U[9] Remove the warning popup when running executable files                        ¨U
  echo ¨U[10]Add the "This PC" icon to the desktop                                         ¨U
  if  "%systabs%"=="1" ( echo ¨d¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨TPlease enter options¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨T¨g )
)
ver | find "°æ±¾" >nul && set /p xuanze=¨U ÇëÊäÈëÄãµÄÑ¡Ôñ: || set /p xuanze=¨U Please enter your choice:
if /i "%xuanze%"=="a" cls&goto start1
if /i "%xuanze%"=="b" cls&goto start2
if /i "%xuanze%"=="c" cls&goto start3
if /i "%xuanze%"=="d" cls&goto start4
if /i "%xuanze%"=="e" cls&goto start5
if /i "%xuanze%"=="g" cls&goto Feedback
if /i "%xuanze%"=="1" cls&goto removewarn
if /i "%xuanze%"=="2" cls&goto removearrow
if /i "%xuanze%"=="3" cls&goto recoveryarrow
if /i "%xuanze%"=="4" cls&goto classicmenu
if /i "%xuanze%"=="5" cls&goto modernmenu
if /i "%xuanze%"=="6" cls&goto removeshield
if /i "%xuanze%"=="7" cls&goto recoveshield
if /i "%xuanze%"=="8" cls&goto shortcut
if /i "%xuanze%"=="9" cls&goto removerunwarn
if /i "%xuanze%"=="10" cls&goto addmypcico

:start2
cls
echo.
ver | find "°æ±¾" >nul && echo ÌáÎÊ½¨ÒéÇëÁôÑÔhttp://kms.cangshui.net || echo Feedback and Tip: http://kms.cangshui.net
ver | find "°æ±¾" >nul && echo ¾èÔùÔÞÖúÇë·ÃÎÊhttp://shop.cangshui.net
echo.
if  "%KMS_Sev%"=="kms-shanghai01.cangshui.net" (
    ver | find "°æ±¾" >nul && echo ÕýÔÚ¼ì²éÄÜ·ñÁ¬½Óµ½KMSÖ÷·þÎñÆ÷...|| echo Checking if we can connect to the KMS master server...
    ) else (
    ver | find "°æ±¾" >nul && echo Á¬½Óµ½KMSÖ÷·þÎñÆ÷Ê§°Ü£¬ÒÑÇÐ»»ÖÁ±¸ÓÃ·þÎñÆ÷...|| echo Checking if we can connect to the KMS master server...
)
dir /a "tcping.exe" | find "258,560"  > NUL && set tcpingstatus=successful
if  "%tcpingstatus%"=="successful" (
    echo tcpingÃüÁî¿ÉÓÃ...ÈôµÈ´ýÊ±¼ä³¬¹ý60Ãë¿É³¢ÊÔÖØÐÂÔËÐÐ½Å±¾ && tcping.exe %KMS_Sev% 1688 | find "0 successful" > NUL && goto failb
    ) else (
       if  "%winv%"=="10" (
          echo ======================================ÌáÊ¾ÐÅÏ¢=======================================
          echo ÒòÏµÍ³×Ô´øµÄpingÃüÁîÎÞ·¨×¼È·ÅÐ¶Ï·þÎñÆ÷ÊÇ·ñ¿ÉÓÃ£¬Òò´Ë½«×Ô¶¯ÏÂÔØTCPing¹¤¾ß
          echo TCPingÎª°²È«µÄ¿ªÔ´¹¤¾ß£¬¿ªÔ´µØÖ·Îªhttps://github.com/jtilander/tcping
          echo ³¢ÊÔÏÂÔØTCPing²âÊÔ×é¼þ...
          echo ======================================ÌáÊ¾ÐÅÏ¢=======================================          
          curl --ssl-no-revoke --connect-timeout 3 -m 10 -s -O https://cangshui.net/-otherweb/kms/tcping.exe    
        ) else (
          echo. 
        )
) 


dir /a "tcping.exe" | find "258,560"  > NUL && set tcpingstatus2=successful
if  "%tcpingstatus2%"=="successful" (
    if "%tcpingstatus%"=="successful" ( echo. ) else ( echo tcpingÃüÁî¿ÉÓÃ...ÈôµÈ´ýÊ±¼ä³¬¹ý60Ãë¿É³¢ÊÔÖØÐÂÔËÐÐ½Å±¾ && tcping.exe %KMS_Sev% 1688 | find "0 successful" > NUL && goto failb)
) else (
        if  "%winv%"=="10" (
          echo TCPingÒòÏÂÔØÊ§°Ü»òÆäËûÔ­Òòµ¼ÖÂ²»¿ÉÓÃ£¬²ÉÓÃpingÀ´¼ì²â·þÎñÆ÷ÊÇ·ñ¿ÉÓÃ£¬ËüµÄ²âÊÔ½á¹û²¢²»Ò»¶¨×¼È·   
        ) else (
          echo ======================================ÌáÊ¾ÐÅÏ¢=======================================
          echo ÄãµÄÏµÍ³·Çwindows10¼°ÒÔÉÏ°æ±¾ ÎÞ·¨×Ô¶¯ÏÂÔØTCPing¹¤¾ß
          echo Òò´ËÖ»²ÉÓÃpingÀ´¼ì²â·þÎñÆ÷ÊÇ·ñ¿ÉÓÃ£¬ËüµÄ²âÊÔ½á¹û²¢²»Ò»¶¨×¼È·
          echo Äã¿ÉÒÔ×ÔÐÐÏÂÔØ´Ó https://cangshui.net/-otherweb/kms/tcping.exe ÏÂÔØËü
          echo ½«Æä·ÅÖÃÔÚ±¾½Å±¾Í¬Ä¿Â¼ÏÂ£¬ÖØÐÂÔËÐÐ½Å±¾¼´¿É
          echo TCPing¹¤¾ß½öÎª¼ì²â·þÎñÆ÷ÊÇ·ñ¿ÉÓÃ£¬È±Ê§Ò²¿ÉÒÔÕý³£¼¤»îÏµÍ³
          echo TCPingÎª°²È«µÄ¿ªÔ´¹¤¾ß£¬¿ªÔ´µØÖ·Îªhttps://github.com/jtilander/tcping
          echo ======================================ÌáÊ¾ÐÅÏ¢=======================================
        )
    echo.
    echo ¿ªÊ¼Ping²âÊÔ...ÈôµÈ´ýÊ±¼ä³¬¹ý60Ãë¿É³¢ÊÔÖØÐÂÔËÐÐ½Å±¾
    ping %KMS_Sev% | find "100% ¶ªÊ§"  > NUL &&  goto failb
    ping %KMS_Sev% | find "100% loss"  > NUL &&  goto failb
    ping %KMS_Sev% | find "ÕÒ²»µ½Ö÷»ú"  > NUL &&  goto failb
    ping %KMS_Sev% | find "not find host"  > NUL &&  goto failb
    ping %KMS_Sev% | find "Ê§°Ü"  > NUL &&  goto failb
    ping %KMS_Sev% | find "fail"  > NUL &&  goto failb    
)


if  "%KMS_Sev%"=="kms-shanghai01.cangshui.net" (
    echo ±¾»úÄÜ¹»Õý³£Á¬½ÓKMSÖ÷·þÎñÆ÷...
    ) else (
    echo ±¾»úÄÜ¹»Õý³£Á¬½ÓKMS±¸ÓÃ·þÎñÆ÷...
)
goto office

:office
echo ¼ì²é°²×°µÄoffice¡­¡­
call :GetOfficePath 14 Office2010
call :ActOffice 14 Office2010
call :GetOfficePath 15 Office2013
call :ActOffice 15 Office2013
if exist "%ProgramFiles%\Microsoft Office\Office16\ospp.vbs" set _Office16Path=%ProgramFiles%\Microsoft Office\Office16
if exist "%ProgramFiles(x86)%\Microsoft Office\Office16\ospp.vbs" set _Office16Path=%ProgramFiles(x86)%\Microsoft Office\Office16
if DEFINED _Office16Path (echo.&echo ÒÑ·¢ÏÖ Office2016ÏµÁÐÈí¼þ[°üÀ¨2016/2019/365/2021]
    ping 127.0.0.1 -n 2 > nul
    call :ActOffice 16 Office2016
  ) else (echo.&echo Î´·¢ÏÖ Office2016ÏµÁÐÈí¼þ[°üÀ¨2016/2019/365/2021])


echo.&pause
exit

:ActOffice
if DEFINED _Office%1Path (
    cd /d "!_Office%1Path!"
    if %1 EQU 16 call :Licens16
    echo.&echo ³¢ÊÔ¼¤»îÄúµÄOffice ...&echo.
cscript //nologo ospp.vbs /sethst:%KMS_Sev% > NUL
cscript //nologo ospp.vbs /act | find /i "successful" && (
        echo.&echo ***** ¼¤»î³É¹¦ *****   & echo.) || (echo.&echo ***** ¼¤»îÊ§°Ü ***** & echo.)
)    
cd /d "%~dp0"
goto :EOF

:GetOfficePath
echo.&echo ÕýÔÚ¼ì²â %2 ÏµÁÐ²úÆ·µÄ°²×°Â·¾¶...
set _Office%1Path=
set _Reg32=HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Office\%1.0\Common\InstallRoot
set _Reg64=HKEY_LOCAL_MACHINE\SOFTWARE\Wow6432Node\Microsoft\Office\%1.0\Common\InstallRoot
reg query "%_Reg32%" /v "Path" > nul 2>&1 && FOR /F "tokens=2*" %%a IN ('reg query "%_Reg32%" /v "Path"') do SET "_OfficePath1=%%b"
reg query "%_Reg64%" /v "Path" > nul 2>&1 && FOR /F "tokens=2*" %%a IN ('reg query "%_Reg64%" /v "Path"') do SET "_OfficePath2=%%b"
if DEFINED _OfficePath1 (if exist "%_OfficePath1%ospp.vbs" set _Office%1Path=!_OfficePath1!)
if DEFINED _OfficePath2 (if exist "%_OfficePath2%ospp.vbs" set _Office%1Path=!_OfficePath2!)
set _OfficePath1=
set _OfficePath2=
if DEFINED _Office%1Path (echo.&echo ÒÑ·¢ÏÖ %2) else (echo.&echo Î´·¢ÏÖ %2)
goto :EOF

:Licens16
cls
echo ¡¾A¡¿¼¤»îÎªOffice2021°æ±¾(½ö2021¼°ÒÔÉÏ°æ±¾¿ÉÑ¡)
echo ¡¾B¡¿¼¤»îÎªOffice2019°æ±¾(½ö2019¼°ÒÔÉÏ°æ±¾¿ÉÑ¡)
echo ¡¾C¡¿¼¤»îÎªOffice2016°æ±¾(È«°æ±¾Í¨ÓÃ)
echo PS£ºOffice365°æ±¾ÊÇÃ»ÓÐÅúÁ¿¼¤»î°æµÄ£¬Èç¹ûÄãÊÇ365°æ±¾Ñ¡C¼´¿É
set /p xuanze=ÇëÑ¡Ôñ...
if /i "%xuanze%"=="a" cls&goto installOffice21
if /i "%xuanze%"=="b" cls&goto installOffice19
if /i "%xuanze%"=="c" cls&goto installOffice16


:installOffice21
echo °²×°2021Ö¤Êé
for /f %%x in ('dir /b ..\root\Licenses16\proplus2021vl_mak*.xrm-ms') do cscript ospp.vbs /inslic:"..\root\Licenses16\%%x" > NUL
for /f %%x in ('dir /b ..\root\Licenses16\proplus2021vl_kms*.xrm-ms') do cscript ospp.vbs /inslic:"..\root\Licenses16\%%x" > NUL
for /f %%x in ('dir /b ..\root\Licenses16\proplus2021previewvl_mak*.xrm-ms') do cscript ospp.vbs /inslic:"..\root\Licenses16\%%x" > NUL
for /f %%x in ('dir /b ..\root\Licenses16\proplus2021previewvl_kms*.xrm-ms') do cscript ospp.vbs /inslic:"..\root\Licenses16\%%x" > NUL
for /f %%x in ('dir /b ..\root\Licenses16\client-issuance*.xrm-ms') do cscript ospp.vbs /inslic:"..\root\Licenses16\%%x" > NUL
for /f %%x in ('dir /b ..\root\Licenses16\pkeyconfig-office-client15.xrm-ms') do cscript ospp.vbs /inslic:"..\root\Licenses16\%%x" > NUL
for /f %%x in ('dir /b ..\root\Licenses16\pkeyconfig-office.xrm-ms') do cscript ospp.vbs /inslic:"..\root\Licenses16\%%x" > NUL
for /f %%x in ('dir /b ..\root\Licenses16\visioPro2021VL_mak*.xrm-ms') do cscript ospp.vbs /inslic:"..\root\Licenses16\%%x" > NUL
for /f %%x in ('dir /b ..\root\Licenses16\visioPro2021VL_kms*.xrm-ms') do cscript ospp.vbs /inslic:"..\root\Licenses16\%%x" > NUL
for /f %%x in ('dir /b ..\root\Licenses16\visiopro2021previewvl_mak*.xrm-ms') do cscript ospp.vbs /inslic:"..\root\Licenses16\%%x" > NUL
for /f %%x in ('dir /b ..\root\Licenses16\visiopro2021previewvl_kms*.xrm-ms') do cscript ospp.vbs /inslic:"..\root\Licenses16\%%x" > NUL
for /f %%x in ('dir /b ..\root\Licenses16\projectpro2021vl_mak*.xrm-ms') do cscript ospp.vbs /inslic:"..\root\Licenses16\%%x" > NUL
for /f %%x in ('dir /b ..\root\Licenses16\projectpro2021vl_kms*.xrm-ms') do cscript ospp.vbs /inslic:"..\root\Licenses16\%%x" > NUL
for /f %%x in ('dir /b ..\root\Licenses16\projectpro2021previewvl_mak*.xrm-ms') do cscript ospp.vbs /inslic:"..\root\Licenses16\%%x" > NUL
for /f %%x in ('dir /b ..\root\Licenses16\projectpro2021previewvl_kms*.xrm-ms') do cscript ospp.vbs /inslic:"..\root\Licenses16\%%x" > NUL
cscript "%_Office16Path%\ospp.vbs" /inpkey:FXYTK-NJJ8C-GB6DW-3DYQT-6F7TH > NUL
cscript "%_Office16Path%\ospp.vbs" /inpkey:KNH8D-FGHT4-T8RK3-CTDYJ-K2HT4 > NUL
cscript "%_Office16Path%\ospp.vbs" /inpkey:FTNWT-C6WBT-8HMGF-K9PRX-QV9H8 > NUL
goto :EOF
exit

:installOffice19
echo °²×°2019Ö¤Êé
for /f %%x in ('dir /b ..\root\Licenses16\proplus2019xc2rvl*.xrm-ms') do cscript ospp.vbs /inslic:"..\root\Licenses16\%%x" > NUL
for /f %%x in ('dir /b ..\root\Licenses16\proplus2019vl_mak*.xrm-ms') do cscript ospp.vbs /inslic:"..\root\Licenses16\%%x" > NUL
for /f %%x in ('dir /b ..\root\Licenses16\proplus2019vl_kms*.xrm-ms') do cscript ospp.vbs /inslic:"..\root\Licenses16\%%x" > NUL
for /f %%x in ('dir /b ..\root\Licenses16\client-issuance*.xrm-ms') do cscript ospp.vbs /inslic:"..\root\Licenses16\%%x" > NUL
for /f %%x in ('dir /b ..\root\Licenses16\pkeyconfig-office-client15.xrm-ms') do cscript ospp.vbs /inslic:"..\root\Licenses16\%%x" > NUL
for /f %%x in ('dir /b ..\root\Licenses16\pkeyconfig-office.xrm-ms') do cscript ospp.vbs /inslic:"..\root\Licenses16\%%x" > NUL
for /f %%x in ('dir /b ..\root\Licenses16\visioPro2019vl_mak*.xrm-ms') do cscript ospp.vbs /inslic:"..\root\Licenses16\%%x" > NUL
for /f %%x in ('dir /b ..\root\Licenses16\visioPro2019vl_kms*.xrm-ms') do cscript ospp.vbs /inslic:"..\root\Licenses16\%%x" > NUL
for /f %%x in ('dir /b ..\root\Licenses16\projectpro2019vl_kms*.xrm-ms') do cscript ospp.vbs /inslic:"..\root\Licenses16\%%x" > NUL
for /f %%x in ('dir /b ..\root\Licenses16\projectpro2019vl_mak*.xrm-ms') do cscript ospp.vbs /inslic:"..\root\Licenses16\%%x" > NUL
for /f %%x in ('dir /b ..\root\Licenses16\projectpro2019xc2rvl_kms*.xrm-ms') do cscript ospp.vbs /inslic:"..\root\Licenses16\%%x" > NUL
for /f %%x in ('dir /b ..\root\Licenses16\projectpro2019xc2rvl_makc2r*.xrm-ms') do cscript ospp.vbs /inslic:"..\root\Licenses16\%%x" > NUL
cscript "%_Office16Path%\ospp.vbs" /inpkey:NMMKJ-6RK4F-KMJVX-8D9MJ-6MWKP > NUL
cscript "%_Office16Path%\ospp.vbs" /inpkey:9BGNQ-K37YR-RQHF2-38RQ3-7VCBB > NUL
cscript "%_Office16Path%\ospp.vbs" /inpkey:B4NPR-3FKK7-T2MBV-FRQ4W-PKD2B > NUL
goto :EOF
exit


:installOffice16
echo °²×°2016Ö¤Êé
for /f %%x in ('dir /b ..\root\Licenses16\proplusvl_kms*.xrm-ms') do cscript ospp.vbs /inslic:"..\root\Licenses16\%%x" > NUL
for /f %%x in ('dir /b ..\root\Licenses16\proplusvl_mak*.xrm-ms') do cscript ospp.vbs /inslic:"..\root\Licenses16\%%x" > NUL
for /f %%x in ('dir /b ..\root\Licenses16\client-issuance*.xrm-ms') do cscript ospp.vbs /inslic:"..\root\Licenses16\%%x" > NUL
for /f %%x in ('dir /b ..\root\Licenses16\pkeyconfig-office-client15.xrm-ms') do cscript ospp.vbs /inslic:"..\root\Licenses16\%%x" > NUL
for /f %%x in ('dir /b ..\root\Licenses16\pkeyconfig-office.xrm-ms') do cscript ospp.vbs /inslic:"..\root\Licenses16\%%x" > NUL
for /f %%x in ('dir /b ..\root\Licenses16\visioProvl_mak*.xrm-ms') do cscript ospp.vbs /inslic:"..\root\Licenses16\%%x" > NUL
for /f %%x in ('dir /b ..\root\Licenses16\visioProvl_kms*.xrm-ms') do cscript ospp.vbs /inslic:"..\root\Licenses16\%%x" > NUL
for /f %%x in ('dir /b ..\root\Licenses16\projectprovl_kms*.xrm-ms') do cscript ospp.vbs /inslic:"..\root\Licenses16\%%x" > NUL
for /f %%x in ('dir /b ..\root\Licenses16\projectprovl_mak*.xrm-ms') do cscript ospp.vbs /inslic:"..\root\Licenses16\%%x" > NUL
for /f %%x in ('dir /b ..\root\Licenses16\projectproxc2rvl_kms*.xrm-ms') do cscript ospp.vbs /inslic:"..\root\Licenses16\%%x" > NUL
for /f %%x in ('dir /b ..\root\Licenses16\projectproxc2rvl_makc2r*.xrm-ms') do cscript ospp.vbs /inslic:"..\root\Licenses16\%%x" > NUL
cscript "%_Office16Path%\ospp.vbs" /inpkey:XQNVK-8JYDB-WJ9W3-YJ8YR-WFG99 > NUL
cscript "%_Office16Path%\ospp.vbs" /inpkey:PD3PC-RHNGV-FXJ29-8JK7D-RJRJK > NUL
cscript "%_Office16Path%\ospp.vbs" /inpkey:YG9NW-3K39V-2T3HJ-93F3Q-G83KT > NUL

goto :EOF
exit





:start1
cls
ver | find "°æ±¾" >nul && echo ÌáÎÊ½¨ÒéÇëÁôÑÔhttp://kms.cangshui.net || echo Feedback and Tip: http://kms.cangshui.net
ver | find "°æ±¾" >nul && echo ¾èÔùÔÞÖúÇë·ÃÎÊhttp://shop.cangshui.net 
echo.
if  "%KMS_Sev%"=="kms-shanghai01.cangshui.net" (
    ver | find "°æ±¾" >nul && echo ÕýÔÚ¼ì²éÄÜ·ñÁ¬½Óµ½KMSÖ÷·þÎñÆ÷... || echo Checking if we can connect to the KMS master server...
    ) else (
    ver | find "°æ±¾" >nul && echo Á¬½Óµ½KMSÖ÷·þÎñÆ÷Ê§°Ü£¬ÒÑÇÐ»»ÖÁ±¸ÓÃ·þÎñÆ÷... || echo Connection to KMS primary server failed, switched to standby server...
)
dir /a "tcping.exe" | find "258,560"  > NUL && set tcpingstatus=successful
if  "%tcpingstatus%"=="successful" (
    ver | find "°æ±¾" >nul && echo tcpingÃüÁî¿ÉÓÃ...ÈôµÈ´ýÊ±¼ä³¬¹ý60Ãë¿É³¢ÊÔÖØÐÂÔËÐÐ½Å±¾ || echo The tcping command is available... If you wait longer than 60 seconds, try running the script again
	tcping.exe %KMS_Sev% 1688 | find "0 successful" > NUL && goto faila
) else (
       if  "%winv%"=="10" (
          ver | find "°æ±¾" >nul && echo ======================================ÌáÊ¾ÐÅÏ¢=======================================
          ver | find "°æ±¾" >nul && echo ÒòÏµÍ³×Ô´øµÄpingÃüÁîÎÞ·¨×¼È·ÅÐ¶Ï·þÎñÆ÷ÊÇ·ñ¿ÉÓÃ£¬Òò´Ë½«×Ô¶¯ÏÂÔØTCPing¹¤¾ß
          ver | find "°æ±¾" >nul && echo TCPingÎª°²È«µÄ¿ªÔ´¹¤¾ß£¬¿ªÔ´µØÖ·Îªhttps://github.com/jtilander/tcping
          ver | find "°æ±¾" >nul && echo ³¢ÊÔÏÂÔØTCPing²âÊÔ×é¼þ...
          ver | find "°æ±¾" >nul && echo ======================================ÌáÊ¾ÐÅÏ¢=======================================     
          curl --ssl-no-revoke --connect-timeout 3 -m 10 -s -O https://cangshui.net/-otherweb/kms/tcping.exe   
        ) else (
          echo.
        )
        
) 


dir /a "tcping.exe" | find "258,560"  > NUL && set tcpingstatus2=successful
if  "%tcpingstatus2%"=="successful" (
    if "%tcpingstatus%"=="successful" ( echo. ) else ( ver | find "°æ±¾" >nul && echo tcpingÃüÁî¿ÉÓÃ...ÈôµÈ´ýÊ±¼ä³¬¹ý60Ãë¿É³¢ÊÔÖØÐÂÔËÐÐ½Å±¾ && tcping.exe %KMS_Sev% 1688 | find "0 successful" > NUL && goto faila)
) else (
    if  "%winv%"=="10" (
          ver | find "°æ±¾" >nul && echo TCPingÒòÏÂÔØÊ§°Ü»òÆäËûÔ­Òòµ¼ÖÂ²»¿ÉÓÃ£¬²ÉÓÃpingÀ´¼ì²â·þÎñÆ÷ÊÇ·ñ¿ÉÓÃ£¬ËüµÄ²âÊÔ½á¹û²¢²»Ò»¶¨×¼È·   
        ) else (
          ver | find "°æ±¾" >nul && echo ======================================ÌáÊ¾ÐÅÏ¢=======================================
          ver | find "°æ±¾" >nul && echo ÄãµÄÏµÍ³Îªwindows7 ÎÞ·¨×Ô¶¯ÏÂÔØTCPing¹¤¾ß
          ver | find "°æ±¾" >nul && echo Òò´ËÖ»²ÉÓÃpingÀ´¼ì²â·þÎñÆ÷ÊÇ·ñ¿ÉÓÃ£¬ËüµÄ²âÊÔ½á¹û²¢²»Ò»¶¨×¼È·
          ver | find "°æ±¾" >nul && echo Äã¿ÉÒÔ×ÔÐÐÏÂÔØ´Ó https://cangshui.net/-otherweb/kms/tcping.exe ÏÂÔØËü
          ver | find "°æ±¾" >nul && echo ½«Æä·ÅÖÃÔÚ±¾½Å±¾Í¬Ä¿Â¼ÏÂ£¬ÖØÐÂÔËÐÐ½Å±¾¼´¿É
          ver | find "°æ±¾" >nul && echo TCPing¹¤¾ß½öÎª¼ì²â·þÎñÆ÷ÊÇ·ñ¿ÉÓÃ£¬È±Ê§Ò²¿ÉÒÔÕý³£¼¤»îÏµÍ³
          ver | find "°æ±¾" >nul && echo TCPingÎª°²È«µÄ¿ªÔ´¹¤¾ß£¬¿ªÔ´µØÖ·Îªhttps://github.com/jtilander/tcping
          ver | find "°æ±¾" >nul && echo ======================================ÌáÊ¾ÐÅÏ¢=======================================
        )
    echo.
    ver | find "°æ±¾" >nul && echo ¿ªÊ¼Ping²âÊÔ...ÈôµÈ´ýÊ±¼ä³¬¹ý60Ãë¿É³¢ÊÔÖØÐÂÔËÐÐ½Å±¾ || echo Start Ping test... If you wait longer than 60 seconds, try running the script again
    ping %KMS_Sev% | find "100% ¶ªÊ§"  > NUL &&  goto faila
    ping %KMS_Sev% | find "100% loss"  > NUL &&  goto faila
    ping %KMS_Sev% | find "ÕÒ²»µ½Ö÷»ú"  > NUL &&  goto faila
    ping %KMS_Sev% | find "not find host"  > NUL &&  goto faila
    ping %KMS_Sev% | find "Ê§°Ü"  > NUL &&  goto faila
    ping %KMS_Sev% | find "fail"  > NUL &&  goto faila    
)

if  "%KMS_Sev%"=="kms-shanghai01.cangshui.net" (
    ver | find "°æ±¾" >nul && echo ±¾»úÄÜ¹»Õý³£Á¬½ÓKMSÖ÷·þÎñÆ÷...  || echo The machine is able to connect to the main KMS server properly...
    ) else (
    ver | find "°æ±¾" >nul && echo ±¾»úÄÜ¹»Õý³£Á¬½ÓKMS±¸ÓÃ·þÎñÆ÷...  || echo The machine is able to connect properly to the KMS standby server...  
    )

ver | find "°æ±¾" >nul && echo ======================================¼¤»îÐÅÏ¢======================================= || echo =====================================information====================================

ver | find "6.0." > NUL &&  goto winvista
ver | find "6.1." > NUL &&  goto win7
ver | find "6.2." > NUL &&  goto win8
ver | find "6.3." > NUL &&  goto win81
ver | find "10.0." > NUL &&  goto win10
ver | find "°æ±¾" >nul && echo Î´ÕÒµ½ºÏÊÊµÄNT6ÏµÍ³£¬¿ÉÄÜÊÇWinXP»òWin2003¡£  || echo No suitable NT6 system found, possibly WinXP or Win2003.
goto office

:winvista
echo µ±Ç°ÎªWindows Vista/2008¡£
set Business=YFKBB-PQJJV-G996G-VWGXY-2V3X8
set BusinessN=HMBQG-8H2RH-C77VX-27R82-VMQBT
set Enterprise=VKK3X-68KWM-X2YGT-QR4M6-4BWMV
set EnterpriseN=VTC42-BM838-43QHV-84HX6-XJXKV
set ServerWeb=WYR28-R7TFJ-3X2YQ-YCY4H-M249D
set ServerStandard=TM24T-X9RMF-VWXK6-X8JC9-BFGM2
set ServerStandardV=W7VD6-7JFBR-RX26B-YKQ3Y-6FFFJ
set ServerEnterprise=YQGMW-MPWTJ-34KDK-48M3W-X4Q6V
set ServerEnterpriseV=39BXF-X8Q23-P2WWT-38T2F-G3FPG
set ServerWeb=RCTX3-KWVHP-BR6TB-RB6DM-6X7HP
set ServerDatacenter=7M67G-PC374-GR742-YH8V4-TCBY3
set ServerDatacenterV=22XQ2-VRXRG-P8D42-K34TD-G3QQC
set ServerEnterpriseIA64=4DWFP-JF3DJ-B7DTH-78FJB-PDRHK
goto windowsstart

:win7
ver | find "°æ±¾" >nul && echo µ±Ç°ÎªWindows 7/2008 R2¡£ || echo Currently Windows 7/2008 R2.
for /f "tokens=*" %%i in ('reg QUERY "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion" /v "ProductName"') do set ProductNamea=%%i
echo "%ProductNamea%" | find "Ultimate" >nul && (  
  msg %username% /time:99999999 "Windows7 Æì½¢°æÎÞ·¨Ê¹ÓÃKMS¼¤»î£¡Çë¸ü»»ÏµÍ³°æ±¾»ò²ÉÈ¡ÆäËû·½Ê½¼¤»îÏµÍ³£¡"
  pause
  exit
  ) || (  
  echo .
)
set Professional=FJ82H-XT6CR-J8D7P-XQJJ2-GPDD4
set ProfessionalN=MRPKT-YTG23-K7D7T-X2JMM-QY7MG
set ProfessionalE=W82YF-2Q76Y-63HXB-FGJG9-GF7QX
set Enterprise=33PXH-7Y6KF-2VJC9-XBBR8-HVTHH
set EnterpriseN=YDRBP-3D83W-TY26F-D46B2-XCKRJ
set EnterpriseE=C29WB-22CC8-VJ326-GHFJW-H9DH4
set ServerWeb=6TPJF-RBVHG-WBW2R-86QPH-6RTM4
set ServerHPC=TT8MH-CG224-D3D7Q-498W2-9QCTX
set ServerStandard=YC6KT-GKW9T-YTKYR-T4X34-R7VHC
set ServerEnterprise=489J6-VHDMP-X63PK-3K798-CPX3Y
set ServerDatacenter=74YFP-3QFB3-KQT8W-PMXWJ-7M648
set ServerEnterpriseIA64=GT63C-RJFQ3-4GMB6-BRFB9-CB83V
goto windowsstart

:win8
ver | find "°æ±¾" >nul && echo µ±Ç°ÎªWindows 8/2012¡£ || echo Currently Windows 8/2012.
set Professional=NG4HW-VH26C-733KW-K6F98-J8CK4
set ProfessionalN=XCVCF-2NXM9-723PB-MHCB7-2RYQQ
set Core=BN3D2-R7TKB-3YPBD-8DRP2-27GG4
set Enterprise=32JNW-9KQ84-P47T8-D8GGY-CWCK7
set EnterpriseN=JMNMF-RHW7P-DMY6X-RF3DR-X2BQT
set CoreN=8N2M2-HWPGY-7PGT9-HGDD8-GVGGY
set CoreSingleLanguage=2WN2H-YGCQR-KFX6K-CD6TF-84YXQ
set CoreCountrySpecific=4K36P-JN4VD-GDC6V-KDT89-DYFKP
set ServerMultiPointPremium=XNH6W-2V9GX-RGJ4K-Y8X6F-QGJ2G
set ServerMultiPointStandard=HM7DN-YVMH3-46JC3-XYTG7-CYQJJ
set ServerStandard=XC9B7-NBPP2-83J2H-RHMBY-92BT4
set ServerDatacenter=48HP8-DN98B-MYWDG-T2DCC-8W83P
goto windowsstart

:win81
ver | find "°æ±¾" >nul && echo µ±Ç°ÎªWindows 8.1¡£ || echo Currently Windows 8.1.
set Professional=GCRJD-8NW9H-F2CDX-CCM8D-9D6T9
set ProfessionalN=HMCNV-VVBFX-7HMBH-CTY9B-B4FXY
set Enterprise=MHF9N-XY6XB-WVXMC-BTDCT-MKKG7
set EnterpriseN=TT4HM-HN7YT-62K67-RGRQJ-JFFXW
set ServerSolution=KNC87-3J2TX-XB4WP-VCPJV-M4FWM
set ServerStandard=D2N9P-3P6X9-2R39C-7RTCD-MDVJX
set ServerDatacenter=W3GGN-FT8W3-Y4M27-J84CP-Q3VJ9
set EmbeddedIndustry=32JNW-9KQ84-P47T8-D8GGY-CWCK7
goto windowsstart

:win10
for /f "tokens=*" %%i in ('reg QUERY "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion" /v "ProductName"') do set ProductNameb=%%i
echo "%ProductNameb%" | find "Server" >nul && (  
  goto win10Server
  ) || (  
    echo "%ProductNameb%" | find "Enterprise" >nul && (  
      goto win10Enterprise
      ) || (  
      ver | find "°æ±¾" >nul && echo µ±Ç°ÎªWindows 10¡£ || echo Currently for Windows 10.
      )
)
set Core=TX9XD-98N7V-6WMQ6-BX7FG-H8Q99
set CoreCountrySpecific=PVMJN-6DFY6-9CCP6-7BKTT-D3WVR
set CoreN=3KHY7-WNT83-DGQKR-F7HPR-844BM
set CoreSingleLanguage=7HNRX-D7KGG-3K4RQ-4WPJ4-YTDFH
set Professional=W269N-WFGWX-YVC9B-4J6C9-T83GX
set ProfessionalN=MH37W-N47XK-V7XM9-C7227-GCQG9
set Education=NW6C2-QMPVW-D7KKK-3GKT6-VCFB2
set EducationN=2WH4N-8QGBV-H22JP-CT43Q-MDWWJ
set ProfessionalEducation=6TP4R-GNPTD-KYYHQ-7B7DP-J447Y
set ProfessionalEducationN=YVWGF-BXNMC-HTQYQ-CPQ99-66QFC
set ProfessionalWorkstation=NRG8B-VKK3Q-CXVCJ-9G2XF-6Q84J
set ProfessionalWorkstations=NRG8B-VKK3Q-CXVCJ-9G2XF-6Q84J
set ProfessionalWorkstationsN=9FNHH-K3HBT-3W4TD-6383H-6XYWF
goto windowsstart


:win10Enterprise
for /f "tokens=*" %%i in ('reg QUERY "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion" /v "ProductName"') do set ProductNameh=%%i
echo "%ProductNameh%" | findstr "2024" >nul && ( 
  ver | find "°æ±¾" >nul && echo µ±Ç°ÎªWindows Enterprise LTSC 2024¡£ || echo Currently Windows Enterprise LTSC 2024.
  set IoTEnterpriseS=M7XTQ-FN8P6-TTKYV-9D4CC-J462D
  set IoTEnterpriseSN=92NFX-8DJQP-P6BBQ-THF9C-7CG2H
  set EnterpriseS=M7XTQ-FN8P6-TTKYV-9D4CC-J462D
  set EnterpriseSN=92NFX-8DJQP-P6BBQ-THF9C-7CG2H
  ) || (
     echo "%ProductNameh%" | findstr "2021" >nul && ( 
       ver | find "°æ±¾" >nul && echo µ±Ç°ÎªWindows Enterprise LTSC 2021¡£ || echo Currently Windows Enterprise LTSC 2021.
       set IoTEnterpriseS=M7XTQ-FN8P6-TTKYV-9D4CC-J462D
       set IoTEnterpriseSN=92NFX-8DJQP-P6BBQ-THF9C-7CG2H
       set EnterpriseS=M7XTQ-FN8P6-TTKYV-9D4CC-J462D
       set EnterpriseSN=92NFX-8DJQP-P6BBQ-THF9C-7CG2H
       ) || (
          echo "%ProductNameh%" | findstr "2019" >nul && ( 
           ver | find "°æ±¾" >nul && echo µ±Ç°ÎªWindows Enterprise LTSC 2019¡£  || echo Currently Windows Enterprise LTSC 2019.
           set EnterpriseS=M7XTQ-FN8P6-TTKYV-9D4CC-J462D
           set EnterpriseSN=92NFX-8DJQP-P6BBQ-THF9C-7CG2H
           ) || (
              echo "%ProductNameh%" | findstr "2016" >nul && ( 
                ver | find "°æ±¾" >nul && echo µ±Ç°ÎªWindows Enterprise LTSB 2016¡£  || echo Currently Windows Enterprise LTSB 2016.
                set EnterpriseS=DCPHK-NFMTC-H88MJ-PFHPY-QJ4BJ
               set EnterpriseSN=QFFDN-GRT3P-VKWWX-X7T3R-8B639
                ) || (
                     echo "%ProductNameh%" | findstr "2015" >nul && ( 
                       ver | find "°æ±¾" >nul && echo µ±Ç°ÎªWindows Enterprise LTSB 2015¡£ || echo Currently Windows Enterprise LTSB 2015.
                       set EnterpriseS=WNMTR-4C88C-JK8YV-HQ7T2-76DF9
                       set EnterpriseSN=2F77B-TNFGY-69QQF-B8YKP-D69TJ
                       ) || (
                       ver | find "°æ±¾" >nul && echo ¿ÉÄÜÊÇÄ³ÖÖÆóÒµ¶¨ÖÆ°æ±¾...²»±£Ö¤ÄÜ¼¤»î³É¹¦...  || echo Probably some kind of corporate customised version... Activation is not guaranteed...
                       set EnterpriseS=M7XTQ-FN8P6-TTKYV-9D4CC-J462D
                       set EnterpriseSN=92NFX-8DJQP-P6BBQ-THF9C-7CG2H
                       set EnterpriseG=YYVX9-NTFWV-6MDM3-9PT4T-4M68B
                       set EnterpriseGN=44RPN-FTY23-9VTTB-MP9BX-T84FV
                       set Enterprise=NPPR9-FWDCX-D2C8J-H872K-2YT43
                       set EnterpriseN=DPH2V-TTNVB-4X9Q3-TJR4H-KHJW4
                     )
               )
          )
     )
)       
goto windowsstart




:win10Server
for /f "tokens=*" %%i in ('reg QUERY "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion" /v "ProductName"') do set ProductNamec=%%i
echo "%ProductNamec%" | findstr "2025" >nul && ( 
  ver | find "°æ±¾" >nul && echo µ±Ç°ÎªWindows server 2025¡£ || echo Currently Windows server 2025.
  set ServerDatacenter=D764K-2NDRG-47T6Q-P8T8W-YP6DF
  set ServerStandard=TVRH6-WHNXV-R9WG3-9XRFY-MY832
  ) || ( 
      echo "%ProductNamec%" | findstr "2022" >nul && ( 
      ver | find "°æ±¾" >nul && echo µ±Ç°ÎªWindows server 2022¡£ || echo Currently Windows server 2022.
      set ServerDatacenter=WX4NM-KYWYW-QJJR4-XV3QB-6VM33
      set ServerStandard=VDYBN-27WPP-V4HQT-9VMD4-VMK7H
      ) || ( 
             echo "%ProductNamec%" | findstr "2019" >nul && ( 
             ver | find "°æ±¾" >nul && echo µ±Ç°ÎªWindows server 2019¡£  || echo Currently Windows server 2019.
             set ServerDatacenter=WMDGN-G9PQG-XVVXX-R3X43-63DFG
             set ServerStandard=N69G4-B89J2-4G8F4-WWYCC-J464C
             set ServerEssentials=WVDHN-86M7X-466P6-VHXV7-YY726
             set ServerRdsh=CPWHC-NT2C7-VYW78-DHDB2-PG3GK
             ) || ( 
                    echo "%ProductNamec%" | findstr "2016" >nul && ( 
                    ver | find "°æ±¾" >nul && echo µ±Ç°ÎªWindows server 2016¡£  || echo Currently Windows server 2016.
                    set ServerDatacenter=CB7KF-BWN84-R7R2Y-793K2-8XDDG
                    set ServerStandard=WC2BQ-8NRM3-FDDYY-2BFGV-KHKQY
                    set ServerEssentials=JCKRF-N37P4-C2D82-9YXRT-4M63B
                    ) || ( 
                    ver | find "°æ±¾" >nul && echo ÎÞ·¨Ê¶±ðÏµÍ³°æ±¾¡­¡­   || echo Unrecognized system version ......
                    goto Feedback
                )
          
            )
        )
	)
goto windowsstart



:windowsstart
ver | find "°æ±¾" >nul && echo ÉèÖÃWindows Update ·þÎñÎª×Ô¶¯²¢ÔËÐÐ... || echo Set the Windows Update service to automatic and run...
sc config wuauserv start=auto > NUL
set winupdate=0
net start | find "Windows Update" > NUL && set winupdate=1
if "%winupdate%"==0 ( echo. > NUL ) else ( net start wuauserv > NUL )
for /f "tokens=3 delims= " %%i in ('reg QUERY "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion" /v "EditionID"') do set EditionID=%%i
if defined %EditionID% (
  ver | find "°æ±¾" >nul && echo °æ±¾IDÎª%EditionID%  || echo The version ID is%EditionID%
  goto windowsstart2
) else (
  ver | find "°æ±¾" >nul && echo ÕÒ²»µ½ÐòÁÐºÅ¡­¡­ || echo Serial number not found ......
  goto Feedback
)
echo.&pause
exit

:windowsstart2
for /f "delims=" %%i in ('cscript //Nologo %windir%\system32\slmgr.vbs /ipk !%EditionID%!') do set kmsresulta=%%i
echo %kmsresulta%
echo %kmsresulta% | find "·ÇºËÐÄ°æ±¾µÄ¼ÆËã»ú" > NUL && goto keyerror
echo %kmsresulta% | find "Windows non-core edition" > NUL && goto keyerror
cscript //Nologo %windir%\system32\slmgr.vbs /skms %KMS_Sev%
for /f "delims=" %%i in ('cscript //Nologo %windir%\system32\slmgr.vbs /ato') do set kmsresultc=%%i
echo %kmsresultc%
echo %kmsresultc% | find "ÎÞ·¨ÁªÏµÈÎºÎÃÜÔ¿¹ÜÀí·þÎñ" > NUL && set retrya=1 && goto networkerror
echo %kmsresultc% | find "could be contacted" > NUL && set retrya=1 && goto networkerror 
ver | find "°æ±¾" >nul && echo ======================================¼¤»îÐÅÏ¢====================================== || echo =====================================information====================================
echo.&pause
exit

:start4
set nextunnum=0
echo ÊÇ·ñÕæµÄÒªÇå³ýOfficeµÄKMS¼¤»î(½öÖ§³ÖOffice2016¼°ÒÔÉÏ°æ±¾)£¿
set /p xuanze=¡¾Y¡¿¼ÌÐø   ¡¾N¡¿¹Ø±Õ
if /i "%xuanze%"=="y" goto nextun
if /i "%xuanze%"=="n" exit

:nextun
if exist "%ProgramFiles%\Microsoft Office\Office16\ospp.vbs"  (
goto nextun64
) else (
goto nextun32
)

:nextun64
cscript "%ProgramFiles%\Microsoft Office\Office16\ospp.vbs" /dstatus | find  /I "No installed product keys detected"  > NUL && goto nextunsuccess
for /f "tokens=*" %%i in (' cscript "%ProgramFiles%\Microsoft Office\Office16\ospp.vbs" /dstatus  ^| find /I "Last 5 characters of installed product key:" ') do set office5key=%%i
set "office5key=%office5key:~-5,5%"
cscript  "%ProgramFiles%\Microsoft Office\Office16\ospp.vbs" /unpkey:%office5key% > NUL
cscript  "%ProgramFiles%\Microsoft Office\Office16\ospp.vbs" /remhst > NUL
set /a nextunnum+=1
cls
echo Çå³ý½ø¶È%nextunnum%/10
if "%nextunnum%"=="10" ( goto nextunsuccess )
goto nextun64
pause
exit

:nextun32
cscript "%ProgramFiles(x86)%\Microsoft Office\Office16\ospp.vbs" /dstatus | find  /I "No installed product keys detected"  > NUL && goto nextunsuccess
for /f "tokens=*" %%i in (' cscript "%ProgramFiles(x86)%\Microsoft Office\Office16\ospp.vbs" /dstatus  ^| find /I "Last 5 characters of installed product key:" ') do set office5key=%%i
set "office5key=%office5key:~-5,5%"
cscript  "%ProgramFiles(x86)%\Microsoft Office\Office16\ospp.vbs" /unpkey:%office5key% > NUL
cscript  "%ProgramFiles(x86)%\Microsoft Office\Office16\ospp.vbs" /remhst > NUL
set /a nextunnum+=1
cls
echo Çå³ý½ø¶È%nextunnum%/10
if "%nextunnum%"=="10" ( goto nextunsuccess )
goto nextun32
pause
exit

:nextunsuccess
cls
echo Çå³ýÍê³É
pause
exit

:start3
set /p xuanze=ÊÇ·ñÕæµÄÒªÇå³ýWindowsµÄKMS£¿¡¾Y¡¿¼ÌÐø   ¡¾N¡¿¹Ø±Õ
if /i "%xuanze%"=="y" goto nextunw
if /i "%xuanze%"=="n" exit
:nextunw
slmgr /upk
slmgr /ckms
slmgr /rearm
cls
echo Çå³ýÍê³É£¬ÇëÖØÆôµçÄÔ
ping 127.0.0.1 -n 10 > nul



:start5
cls
echo.
echo windows 11£º
echo Windows 11 ½ÌÓý°æ                    Windows 11 ×¨Òµ½ÌÓý°æ
echo Windows 11 ÆóÒµ°æ                    Windows 11 ×¨Òµ¹¤×÷Õ¾°æ
echo Windows 11 ×¨Òµ°æ    
echo. 
echo Windows 10£º
echo Windows 10 ½ÌÓý°æ                    Windows 10 ×¨Òµ½ÌÓý°æ
echo Windows 10 ÆóÒµ°æ                    Windows 10 ×¨Òµ¹¤×÷Õ¾°æ 
echo Windows 10 ×¨Òµ°æ                 
echo. 
echo Windows Server£º
echo Windows Server version 1709-1909 Êý¾ÝÖÐÐÄ°æ  Windows Server version 1709-1909 ±ê×¼°æ
echo Windows Server 2012 Êý¾ÝÖÐÐÄ°æ                         Windows Server 2012 ±ê×¼°æ
echo Windows Server 2016 Êý¾ÝÖÐÐÄ°æ                         Windows Server 2016 ±ê×¼°æ
echo Windows Server 2019 Êý¾ÝÖÐÐÄ°æ                         Windows Server 2019 ±ê×¼°æ
echo Windows Server 2022 Êý¾ÝÖÐÐÄ°æ                         Windows Server 2022 ±ê×¼°æ
echo.
echo Windows Enterprise£º
echo Windows LTSC 2019                   Windows LTSB 2016
echo Windows LTSB 2015
echo. 
echo Windows 8.1£º
echo Windows 8.1 ×¨Òµ°æ                    Windows 8.1 ÆóÒµ°æ
echo. 
echo Windows 7£º
echo Windows 7 ×¨Òµ°æ                       Windows 7 ÆóÒµ°æ
pause
cls
goto start




:faila
cls
if  "%KMS_Sev%"=="kms-shanghai01.cangshui.net" (
    set KMS_Sev=kms-default.cangshui.net && goto start1
    ) else (
    ver | find "°æ±¾" >nul && echo Á¬½Óµ½KMSÖ÷/±¸·þÎñÆ÷½ÔÊ§°Ü£¬ÇëÖØÐÂÔËÐÐ½Å±¾»ò¼ì²é¼ÆËã»úÍøÂçÉèÖÃ... || echo Unable to connect to KMS server
    )
pause



:failb
cls
if  "%KMS_Sev%"=="kms-shanghai01.cangshui.net" (
    set KMS_Sev=kms-default.cangshui.net && goto start2
    ) else (
    ver | find "°æ±¾" >nul && echo Á¬½Óµ½KMSÖ÷/±¸·þÎñÆ÷½ÔÊ§°Ü£¬ÇëÖØÐÂÔËÐÐ½Å±¾»ò¼ì²é¼ÆËã»úÍøÂçÉèÖÃ... || echo Unable to connect to KMS server
    )
pause

:networkerror
set /a retrya=1+%retrya%
if "%retrya%" LEQ "5" (
  goto networkerror2
) else (
  echo ======================================´íÎóÐÅÏ¢=======================================
  echo ±¾»úÁ¬½ÓKMS·þÎñÆ÷¶à´ÎÊ§°Ü...Çë¼ì²éÍøÂçÉèÖÃ...
  goto Feedback
)
pause
exit

:networkerror2
echo Òò±¾»úÁ¬½ÓKMS·þÎñÆ÷Ê§°Ü£¬ÕýÔÚ½øÐÐµÚ%retrya%´ÎÖØÊÔ..
for /f "delims=" %%i in ('cscript //Nologo %windir%\system32\slmgr.vbs /ato') do set kmsresultd=%%i
echo %kmsresultd% | find "ÎÞ·¨ÁªÏµÈÎºÎÃÜÔ¿¹ÜÀí·þÎñ" > NUL  && goto networkerror
echo %kmsresultd% | find "could be contacted" > NUL &&  goto networkerror 
pause
exit

:keyerror
echo ======================================´íÎóÐÅÏ¢=======================================
echo ¼¤»îÃÜ³×´íÎó£¬¿ÉÄÜÊÇ½Å±¾²»Ö§³ÖÄãµÄÏµÍ³°æ±¾...
goto Feedback
pause
exit


:Feedback
echo.
if "!%EditionID%!"=="" ( echo. > NUL ) else ( echo windows¼¤»îÊ±Ê¹ÓÃµÄÃÜ³×Îª!%EditionID%!  )
if "%KMS_Sev%"=="" ( echo. > NUL ) else ( echo ¼¤»îÊ¹ÓÃµÄ·þÎñÆ÷Îª%KMS_Sev%  )
for /f "tokens=*" %%d in ('reg QUERY "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion" /v "ProductName"') do set ProductNamed=%%d
echo °æ±¾Îª%ProductNamed%
for /f "tokens=*" %%f in ('reg QUERY "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion" /v "EditionID"') do set EditionID=%%f
echo IDÎª%EditionID%
where curl > NUL
if "%errorlevel%"=="0" ( Echo ÏµÍ³ÒÑ°²×°curl¹¤¾ß ) else ( echo ÏµÍ³Î´°²×°curl¹¤¾ß )
where tcping > NUL
if "%errorlevel%"=="0" ( Echo ÏµÍ³ÒÑ°²×°Tcping¹¤¾ß ) else ( echo ÏµÍ³Î´°²×°Tcping¹¤¾ß )
whoami /groups | find "S-1-16-12288" >NUL && Echo ½Å±¾ÓµÓÐ¹ÜÀíÔ±È¨ÏÞ
echo ======================================´íÎóÐÅÏ¢=======================================
pause
cls
goto start

:removearrow
reg add "HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\Shell Icons" /v 29 /d "%systemroot%\system32\imageres.dll,197" /t reg_sz /f > nul
taskkill /f /im explorer.exe > nul
start explorer > nul
echo È¥³ý¿ì½Ý·½Ê½¼ýÍ·²Ù×÷Íê³É...
pause
cls
goto start

:recoveryarrow
reg delete "HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\Shell Icons" /v 29 /f > nul
taskkill /f /im explorer.exe > nul
start explorer > nul
echo »Ö¸´¿ì½Ý·½Ê½¼ýÍ·²Ù×÷Íê³É...
pause
cls
goto start



:modernmenu
reg delete "HKCU\Software\Classes\CLSID\{86ca1aa0-34aa-4e8b-a509-50c905bae2a2}" /f  > nul
taskkill /f /im explorer.exe > nul
start explorer > nul
echo ÇÐ»»ÎªÏÖ´ú×ÀÃæÓÒ¼ü²Ëµ¥²Ù×÷Íê³É...
pause
cls
goto start

:classicmenu
reg add "HKCU\Software\Classes\CLSID\{86ca1aa0-34aa-4e8b-a509-50c905bae2a2}\InprocServer32" /f  > nul
taskkill /f /im explorer.exe > nul
start explorer > nul
echo ÇÐ»»Îª¾­µä×ÀÃæÓÒ¼ü²Ëµ¥²Ù×÷Íê³É...
pause
cls
goto start


:removewarn
reg add HKLM\SOFTWARE\Microsoft\Office\ClickToRun\Configuration /v AudienceId /t REG_SZ /d "55336B82-A18D-4DD6-B5F6-9E5095C314A6" /f > nul
reg add HKLM\SOFTWARE\Microsoft\Office\ClickToRun\Configuration /v CDNBaseUrl /t REG_SZ /d "http://officecdn.microsoft.com/pr/55336B82-A18D-4DD6-B5F6-9E5095C314A6" /f > nul
reg add HKLM\SOFTWARE\Microsoft\Office\ClickToRun\Configuration /v UpdateChannel /t REG_SZ /d "http://officecdn.microsoft.com/pr/55336B82-A18D-4DD6-B5F6-9E5095C314A6" /f > nul
reg delete HKLM\SOFTWARE\Microsoft\Office\ClickToRun\Configuration /v UpdateUrl /f  > nul
reg delete HKLM\SOFTWARE\Microsoft\Office\ClickToRun\Configuration /v UpdateToVersion /f  > nul
reg delete HKLM\SOFTWARE\Microsoft\Office\ClickToRun\Updates /v UpdateToVersion /f > nul
reg delete HKLM\SOFTWARE\Policies\Microsoft\Office\16.0\Common\OfficeUpdate\ /f > nul
"%CommonProgramFiles%\microsoft shared\ClickToRun\OfficeC2RClient.exe" /update user > nul
echo ÇëµÈ´ý¡°ÕýÔÚÏÂÔØOffice¸üÐÂ´°¿Ú¡±½ø¶ÈÍê³É...
echo ÈôÌáÊ¾ÐèÒª¹Ø±Õoffice£¬Çëµã»÷¼ÌÐø£¬È»ºóÔÙ´Î´ò¿ªOffice²é¿´Ð§¹û...
pause
cls
goto start

:shortcut
reg add HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Explorer /v Link /t REG_BINARY /d "00000000" /f > nul
echo È¥³ý´´½¨¿ì½Ý·½Ê½Ê±µÄºó×º¡°-¿ì½Ý·½Ê½¡±²Ù×÷³É¹¦...
echo ¿ÉÄÜÐèÒªÖØÆô¼ÆËã»ú²ÅÄÜÉúÐ§...
pause
cls
goto start


:removeshield
reg add "HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\Shell Icons" /v 77 /d "%systemroot%\system32\imageres.dll,197" /t reg_sz /f > nul
taskkill /f /im explorer.exe > nul
start explorer > nul
echo È¥³ý¿ì½Ý·½Ê½¶ÜÅÆ²Ù×÷Íê³É...
pause
cls
goto start


:recoveshield
reg delete "HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\Shell Icons" /v 77 /f > nul
taskkill /f /im explorer.exe > nul
start explorer > nul
echo »Ö¸´¿ì½Ý·½Ê½¶ÜÅÆ²Ù×÷Íê³É...
pause
cls
goto start


:removerunwarn
reg add HKCU\Software\Microsoft\Windows\CurrentVersion\Policies\Associations /v ModRiskFileTypes /t REG_SZ /d .exe;.bat;.vbs;.py;.cmd;.msi;.ps1;.js /f
gpupdate /force
echo È¥³ý¿ÉÖ´ÐÐÎÄ¼þµÄ°²È«¾¯¸æµ¯´°²Ù×÷Íê³É...
pause
cls
goto start

:addmypcico
reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\HideDesktopIcons\NewStartPanel" /v "{20D04FE0-3AEA-1069-A2D8-08002B30309D}" /t REG_DWORD /d "0" /f
taskkill /f /im explorer.exe > nul
start explorer > nul
echo Ïò×ÀÃæÌí¼Ó¡°´ËµçÄÔ¡±Í¼±ê²Ù×÷Íê³É...
pause
cls
goto start