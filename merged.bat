@echo off
:: 设置输出文件名
set outputFile=merged.doc

:: 检查是否存在同名文件，如果存在，提示是否覆盖
if exist "%outputFile%" (
    choice /M "The file exists. Overwrite?"
    if errorlevel 2 exit
)
:: 写入 UTF-8 BOM (EF BB BF)
> "%outputFile%" ( 
    set /p ="ÿþ">nul
)

:: 合并所有 .txt 文件的内容
(
    for %%f in (*.txt) do (
        type "%%f"
        echo.  
    )
) > "%outputFile%"



exit 0

