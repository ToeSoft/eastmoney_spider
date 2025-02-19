import os
import json
import pandas as pd
from openpyxl import load_workbook
from openpyxl.drawing.image import Image


def generateExcel(name, code,onError):

    try:
        # 读取文件夹中的所有文件
        dir = os.path.join("temp", code)
        files = os.listdir(dir)
        # print(files)

        # 读取data.json文件
        with open(os.path.join(dir, "data.json"), "r",encoding="utf-8") as f:
            jsonData = json.load(f)

        df = pd.DataFrame()

        # 创建数据
        for i in jsonData:
            for tag, value in i.items():
                row1 = []
                row2 = []

                # 处理每个条目的键值对
                for x in value:
                    for z in x.keys():
                        row1.append(z)  # 添加 key 到 row1
                        row2.append(x[z])  # 添加 value 到 row2

                # 生成 DataFrame
                temp_df = pd.DataFrame([[tag], row1, row2, [], [], []])

                # 合并数据到主 DataFrame
                df = pd.concat([df, temp_df], ignore_index=True)

        # 保存为 Excel 文件
        time = pd.Timestamp.now()
        formatTime = time.strftime('%Y-%m-%d')
        dir_path = os.path.join("result", formatTime)
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
        excel_path = os.path.join(dir_path,name + "(" + code + ")" + " " + formatTime + ".xlsx")
        df.to_excel(excel_path, index=False, header=False)

        # 使用 openpyxl 重新打开文件以插入图片
        wb = load_workbook(excel_path)
        ws = wb.active

        # 起始行
        image_start_row = 10

        for i in jsonData:
            for tag, value in i.items():
                if tag == "detail" or tag == "概览":
                    continue

                # 根据 tag 设置不同的图片路径
                if tag == "顶部":
                    img_path = os.path.join(dir, "charts_top.png")  # 确保图片路径是正确的
                elif tag == "中部":
                    img_path = os.path.join(dir, "charts_mid.png")
                else:
                    img_path = os.path.join(dir, "charts_btm_" + tag + ".png")

                # 加载图片
                img = Image(img_path)

                # 改变图片的大小
                if tag != "顶部":
                    img.width = 800
                    img.height = 30
                else:
                    img.width = 1000
                    img.height = 36


                # 计算图片插入的单元格位置
                image_cell = f"A{image_start_row}"

                # 插入图片到指定单元格
                ws.add_image(img, image_cell)

                # 更新插入位置，下一张图片下移 3 行
                image_start_row += 6

        # 保存修改后的文件
        wb.save(excel_path)
    except Exception as e:
        with open("error.log", "a", encoding="utf-8") as f:
            f.write(str(e))
        onError(code+"生成Excel失败")


# generateExcel("name", "sz300059")
