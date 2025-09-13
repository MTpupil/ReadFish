; ReadFish NSIS 安装脚本
; 用于创建ReadFish的Windows安装程序

; 包含现代UI
!include "MUI2.nsh"

; 应用程序信息
!define APP_NAME "ReadFish"
!define APP_VERSION "1.0.0"
!define APP_PUBLISHER "ReadFish Team"
!define APP_URL "https://github.com/readfish/readfish"
!define APP_DESCRIPTION "上班摸鱼看小说工具"

; 安装程序信息
Name "${APP_NAME} ${APP_VERSION}"
OutFile "ReadFish_Setup_${APP_VERSION}.exe"
InstallDir "$PROGRAMFILES\${APP_NAME}"
InstallDirRegKey HKCU "Software\${APP_NAME}" ""
RequestExecutionLevel admin

; 压缩设置
SetCompressor /SOLID lzma
SetCompressorDictSize 32

; 版本信息
VIProductVersion "1.0.0.0"
VIAddVersionKey "ProductName" "${APP_NAME}"
VIAddVersionKey "ProductVersion" "${APP_VERSION}"
VIAddVersionKey "CompanyName" "${APP_PUBLISHER}"
VIAddVersionKey "FileDescription" "${APP_DESCRIPTION}"
VIAddVersionKey "FileVersion" "${APP_VERSION}"
VIAddVersionKey "LegalCopyright" "© 2024 ${APP_PUBLISHER}"

; 现代UI配置
!define MUI_ABORTWARNING
!define MUI_ICON "logo.png"
!define MUI_UNICON "logo.png"

; 安装程序页面
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE "LICENSE.txt"
!insertmacro MUI_PAGE_COMPONENTS
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!define MUI_FINISHPAGE_RUN "$INSTDIR\ReadFish.exe"
!define MUI_FINISHPAGE_RUN_TEXT "启动 ReadFish"
!insertmacro MUI_PAGE_FINISH

; 卸载程序页面
!insertmacro MUI_UNPAGE_WELCOME
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_UNPAGE_FINISH

; 语言文件
!insertmacro MUI_LANGUAGE "SimpChinese"
!insertmacro MUI_LANGUAGE "English"

; 安装程序节
Section "ReadFish 主程序" SecMain
  SectionIn RO  ; 必需组件
  
  ; 设置输出路径
  SetOutPath "$INSTDIR"
  
  ; 复制主程序文件
  File "dist\ReadFish.exe"
  
  ; 复制资源文件
  File "README.md"
  File "使用说明.txt"
  
  ; 创建开始菜单快捷方式
  CreateDirectory "$SMPROGRAMS\${APP_NAME}"
  CreateShortCut "$SMPROGRAMS\${APP_NAME}\${APP_NAME}.lnk" "$INSTDIR\ReadFish.exe"
  CreateShortCut "$SMPROGRAMS\${APP_NAME}\使用说明.lnk" "$INSTDIR\使用说明.txt"
  CreateShortCut "$SMPROGRAMS\${APP_NAME}\卸载 ${APP_NAME}.lnk" "$INSTDIR\Uninstall.exe"
  
  ; 创建桌面快捷方式
  CreateShortCut "$DESKTOP\${APP_NAME}.lnk" "$INSTDIR\ReadFish.exe"
  
  ; 写入注册表信息
  WriteRegStr HKCU "Software\${APP_NAME}" "" $INSTDIR
  WriteRegStr HKCU "Software\${APP_NAME}" "Version" "${APP_VERSION}"
  
  ; 写入卸载信息
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" "DisplayName" "${APP_NAME}"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" "UninstallString" "$INSTDIR\Uninstall.exe"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" "DisplayIcon" "$INSTDIR\ReadFish.exe"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" "Publisher" "${APP_PUBLISHER}"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" "DisplayVersion" "${APP_VERSION}"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" "URLInfoAbout" "${APP_URL}"
  WriteRegDWORD HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" "NoModify" 1
  WriteRegDWORD HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" "NoRepair" 1
  
  ; 创建卸载程序
  WriteUninstaller "$INSTDIR\Uninstall.exe"
  
SectionEnd

; 可选组件：文件关联
Section "文件关联 (.txt)" SecFileAssoc
  
  ; 注册.txt文件关联（可选）
  WriteRegStr HKCU "Software\Classes\.txt\OpenWithProgids" "ReadFish.txtfile" ""
  WriteRegStr HKCU "Software\Classes\ReadFish.txtfile" "" "ReadFish 文本文件"
  WriteRegStr HKCU "Software\Classes\ReadFish.txtfile\DefaultIcon" "" "$INSTDIR\ReadFish.exe,0"
  WriteRegStr HKCU "Software\Classes\ReadFish.txtfile\shell\open\command" "" '"$INSTDIR\ReadFish.exe" "%1"'
  
SectionEnd

; 组件描述
LangString DESC_SecMain ${LANG_SIMPCHINESE} "ReadFish 主程序文件和必需组件"
LangString DESC_SecFileAssoc ${LANG_SIMPCHINESE} "将 .txt 文件与 ReadFish 关联，可以直接双击打开"

LangString DESC_SecMain ${LANG_ENGLISH} "ReadFish main program files and required components"
LangString DESC_SecFileAssoc ${LANG_ENGLISH} "Associate .txt files with ReadFish for direct opening"

!insertmacro MUI_FUNCTION_DESCRIPTION_BEGIN
  !insertmacro MUI_DESCRIPTION_TEXT ${SecMain} $(DESC_SecMain)
  !insertmacro MUI_DESCRIPTION_TEXT ${SecFileAssoc} $(DESC_SecFileAssoc)
!insertmacro MUI_FUNCTION_DESCRIPTION_END

; 卸载程序节
Section "Uninstall"
  
  ; 删除程序文件
  Delete "$INSTDIR\ReadFish.exe"
  Delete "$INSTDIR\README.md"
  Delete "$INSTDIR\使用说明.txt"
  Delete "$INSTDIR\Uninstall.exe"
  
  ; 删除快捷方式
  Delete "$SMPROGRAMS\${APP_NAME}\${APP_NAME}.lnk"
  Delete "$SMPROGRAMS\${APP_NAME}\使用说明.lnk"
  Delete "$SMPROGRAMS\${APP_NAME}\卸载 ${APP_NAME}.lnk"
  RMDir "$SMPROGRAMS\${APP_NAME}"
  Delete "$DESKTOP\${APP_NAME}.lnk"
  
  ; 删除安装目录
  RMDir "$INSTDIR"
  
  ; 删除注册表项
  DeleteRegKey HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}"
  DeleteRegKey HKCU "Software\${APP_NAME}"
  
  ; 删除文件关联（如果存在）
  DeleteRegKey HKCU "Software\Classes\ReadFish.txtfile"
  DeleteRegValue HKCU "Software\Classes\.txt\OpenWithProgids" "ReadFish.txtfile"
  
SectionEnd

; 安装程序函数
Function .onInit
  
  ; 检查是否已安装
  ReadRegStr $R0 HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" "UninstallString"
  StrCmp $R0 "" done
  
  MessageBox MB_OKCANCEL|MB_ICONEXCLAMATION "${APP_NAME} 已经安装。$\n$\n点击 '确定' 卸载之前的版本，或点击 '取消' 退出安装程序。" IDOK uninst
  Abort
  
  uninst:
    ClearErrors
    ExecWait '$R0 _?=$INSTDIR'
    
    IfErrors no_remove_uninstaller done
    no_remove_uninstaller:
  
  done:
  
FunctionEnd