import json
import os
import threading
import time

from DrissionPage import ChromiumPage
from PIL import Image, ImageEnhance, ImageFilter
from DrissionPage import ChromiumOptions
from excel import generateExcel, generateTxt
import concurrent.futures
import pytesseract

dictMapTop = {
    "MA3": "MA5",
    "MAS":"MA5",
}

dictMap = {
    "RS6": "RSI6",
    "RS24": "RSI24",
    "RS10": "RSI10",
    "WRI10": "WR10",
    "MA‘": "MA1",
    "CCL": "CCI",
    "CCl": "CCI",
    "RSIG": "RSI6",
    "成交量": "VOL",
    "[交量": "VOL",
    "嵌交量": "VOL",
    "成交垂": "VOL",
    "PDl": "PDI",
    "MDl": "MDI",
    "BIASG": "BIAS6",
    "BIASI2": "BIAS12",
    "HRIO": "WR10",
    "IRIO": "WR10",
    "WRG": "WR6",
    "』": "J",
    "ROCMA": "ROC_MA",
    "WRIO": "WR10",
    "BI4S6": "BIAS6",
    "80S24": "BIAS24",
    "BlAS24": "BIAS24",
    "WIRIO": "WR10",
    "OBVMA": "OBV_MA",
    "RS124": "RSI24",
    "BlAS6": "BIAS6",
    "BlAS12": "BIAS12",
    "BIA86": "BIAS6",
    "BIA812": "BIAS12",
    "BIA824": "BIAS24",
    "BlA86": "BIAS6",
    "BlA812": "BIAS12",
    "BlA824": "BIAS24",
    "MAI": "MA1",
    "RSII2": "RSI12",
    "IRG": "WR6",
    "NA10": "MA10",
    "VA5": "MA5",
    "MAZ": "MA2",
    "BlIAS24": "BIAS24",
    "DOBV": "OBV",
    "MAS": "MA3",
    "MAS5": "MA5",
    "A5": "MA5",
    "MiA5": "MA5",
    "MAS80": "MA30",
}


def cropTop(tempImagePath, img):
    width, height = img.size
    left = 0
    top = 0
    right = width / 2 + 300
    bottom = height * 0.035
    return cropImage(img, top, bottom, left, right, tempImagePath, 'charts_top.png')


def cropMid(tempImagePath, img):
    width, height = img.size
    left = 0
    # top = 743
    top = height / 2 + height * 0.142
    right = width / 2
    # bottom = height - 383
    bottom = height - height * 0.333
    return cropImage(img, top, bottom, left, right, tempImagePath, 'charts_mid.png')


def cropBottom(tempImagePath, img, name):
    width, height = img.size
    left = 0
    # top = 955
    top = height / 2 + height * 0.325
    right = width / 2
    # bottom = height - 170
    bottom = height - height * 0.1465
    return cropImage(img, top, bottom, left, right, tempImagePath,
                     'charts_btm_' + name.split("_")[1].replace(".png", "") + '.png')


def cropImage(img, top, bottom, left, right, tempImagePath, saveName):
    if "CCI" in saveName:
        right = right / 2
    cropped_img = img.crop((left, top, right, bottom))
    # cropped_img = cropped_img.convert("L")
    # cropped_img = cropped_img.resize((cropped_img.width * 3, cropped_img.height * 3), Image.Resampling.LANCZOS)
    # if "CCI" in saveName:
    #     cropped_img = cropped_img.convert("L")
    #     cropped_img = cropped_img.resize((cropped_img.width * 3, cropped_img.height * 3), Image.Resampling.LANCZOS)
    enhancer = ImageEnhance.Contrast(cropped_img)
    cropped_img = enhancer.enhance(2)
    # cropped_img = cropped_img.filter(ImageFilter.SHARPEN)
    # cropped_img = cropped_img.filter(ImageFilter.SHARPEN)

    imgPath = os.path.join(tempImagePath, saveName)
    cropped_img.save(imgPath)
    return imgPath


def startCropImage(tempImagePath, imgFileNameList):
    print("startCropImage", tempImagePath, imgFileNameList)
    for imgFileName in imgFileNameList:
        img = Image.open(os.path.join(tempImagePath, imgFileName))
        img = img.resize((1800, 1160), Image.Resampling.LANCZOS)
        if "RSI" in imgFileName:
            cropTop(tempImagePath, img),
            cropMid(tempImagePath, img),
            cropBottom(tempImagePath, img, imgFileName)
        else:
            cropBottom(tempImagePath, img, imgFileName)


def convertKey(key):
    if key in dictMap:
        return dictMap[key]
    return key


def convertKeyTop(key):
    if key in dictMapTop:
        return dictMapTop[key]
    return key


def startWithThread(items, reader, onFinish, onError, output_format):
    # 记录开始时间
    start_time = time.time()

    os.makedirs("temp", exist_ok=True)

    # 记录创建temp目录的时间
    step1 = time.time()

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = []

        # 记录创建线程池的时间
        step2 = time.time()

        for i in range(len(items)):
            os.makedirs(os.path.join("temp", items[i].split(":")[0]), exist_ok=True)
            futures.append(executor.submit(getData, items[i].split(":")[0], onError))

        # 等待所有线程执行完毕
        concurrent.futures.wait(futures)

        # 记录线程任务完成的时间
        step3 = time.time()
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = []
        for i in os.listdir(os.path.join("temp")):
            futures.append(executor.submit(saveOcrJsonData,i,reader, onError))
            # saveOcrJsonData(i, reader, onError)
    concurrent.futures.wait(futures)
    # 记录保存OCR数据的时间
    step4 = time.time()

    updateStockList()
    step5 = time.time()

    with open("stock_list.json", "r", encoding="utf-8") as f:
        stockList = json.load(f)
        for i in stockList:
            if ":" not in i:
                continue
            if output_format == "excel":
                generateExcel(i.split(":")[1], i.split(":")[0], onError)
            else:
                generateTxt(i.split(":")[1], i.split(":")[0], onError)

    # 读取stock_list.json的时间
    step6 = time.time()

    # 计算每一步的耗时
    print(f"创建temp目录耗时: {step1 - start_time:.2f} 秒")
    print(f"创建线程池耗时: {step2 - step1:.2f} 秒")
    print(f"线程任务完成耗时: {step3 - step2:.2f} 秒")
    print(f"保存OCR数据耗时: {step4 - step3:.2f} 秒")
    print(f"生成Excel耗时: {step5 - step4:.2f} 秒")
    print(f"保存stock_list.json耗时: {step6 - step5:.2f} 秒")
    # 完整执行时间
    print(f"总执行时间: {step6 - start_time:.2f} 秒")

    onFinish()


def saveOcrJsonData(stockCode, reader, onError):
    tempStockDir = os.path.join("temp", stockCode)
    jsonPath = os.path.join(tempStockDir, "data.json")

    #  tempStockDir 下所有的png文件
    jsonData = []
    try:
        for i in sorted(os.listdir(tempStockDir), reverse=True):
            if ".png" not in i:
                continue
            if "data.json" in i:
                continue
            keyName = i.split("_")[-1].replace(".png", "")

            if "top" in keyName:
                keyName = "顶部"
            if "mid" in keyName:
                keyName = "中部"
            ocr_result = getImageText(reader, os.path.join(tempStockDir, i))
            print(ocr_result)
            jsonData.append({keyName: ocr_result})

        with open(jsonPath, "r", encoding="utf-8") as f:
            data = json.load(f)
            data.extend(jsonData)

            with open(jsonPath, "w", encoding="utf-8") as f:
                # 重新写入
                json.dump(data, f, ensure_ascii=False, indent=4)
    except Exception as e:
        with open("error.log", "a", encoding="utf-8") as f:
            f.write(str(e) + "\n")
        onError(stockCode + "OCR识别失败")


def startGetData(items, reader, onFinish, onError, output_format):
    threading.Thread(target=startWithThread, args=(items, reader, onFinish, onError, output_format)).start()


def getData(stockCode, onError):
    codeFileMap = []
    co = ChromiumOptions().headless().auto_port()
    # co = ChromiumOptions().auto_port()
    chromePage = ChromiumPage(co)

    try:
        chromePage.get("https://quote.eastmoney.com/concept/" + stockCode + ".html")
        # 等待页面加载完成
        time.sleep(1)
        name = chromePage.ele("tag:span@class=name")
        zde = chromePage.ele("tag:span@class=zde")
        zdf = chromePage.ele("tag:span@class=zdf")

        detailTable = chromePage.ele("tag:div@class=stockitems").ele("tag:table")

        trList = detailTable.ele("tag:tbody").eles("tag:tr")
        detailList = []
        for tr in trList:
            tdList = tr.eles("tag:td")
            # 批除最后一个td
            for td in tdList[:-1]:
                item = td.ele("tag:div@class=item")
                key = item.ele("@class=l")
                value = item.ele("@class=r")
                detailList.append({key.text: value.text})

        charts = chromePage.ele("tag:div@class=charts")

        li = charts.ele("tag:div").eles("tag:div")[0].ele("tag:ul").eles("tag:li")
        for i in li:
            if i.text == "日K":
                i.click()
                time.sleep(0.3)
                i.click()
                break

        tablist = chromePage.ele("tag:div@class=f_zb").ele("tag:ul").eles("tag:li")
        imgFileNameList = []
        for tab in tablist[1:]:
            tab.click()
            # time.sleep(0.5)
            filename = "charts_" + tab.text + ".png"
            canvas = charts.ele("tag:canvas")
            imgFileNameList.append(filename)
            canvas.get_screenshot(path=os.path.join("temp", stockCode), name=filename)

        tempData = [
            {"名称": name.text},
            {"代码": stockCode},
            {"涨跌额": zde.text},
            {"涨跌幅": zdf.text},
        ]

        if len(detailList) > 12:
            tempData.extend(detailList[:12])
        else:
            tempData.extend(detailList)

        with open(os.path.join("temp", stockCode, "data.json"), "w", encoding="utf-8") as f:
            json.dump([{"概览": tempData}], f, ensure_ascii=False, indent=4)

        codeFileMap.append({stockCode: imgFileNameList})

    except Exception as e:
        # 将详细错误信息写入error.log日志

        with open("error.log", "a", encoding="utf-8") as f:
            f.write(str(e) + "\n")

        onError(stockCode + "获取数据失败")

    # 关闭浏览器
    chromePage.quit()

    try:
        for i in codeFileMap:
            for key in i:
                stockCode = key
                imgFileNameList = i[key]
                startCropImage(os.path.join("temp", stockCode), imgFileNameList)
                charts_files = os.listdir(os.path.join("temp", stockCode))
                for charts_file in charts_files:
                    if "charts_top" in charts_file:
                        continue
                    if "charts_mid" in charts_file:
                        continue
                    if "charts_btm" in charts_file:
                        continue
                    if "data.json" in charts_file:
                        continue
                    os.remove(os.path.join("temp", stockCode, charts_file))
    except Exception as e:
        with open("error.log", "a", encoding="utf-8") as f:
            f.write(str(e) + "\n")
        onError(stockCode + "处理图片失败")


def updateStockList():
    try:
        # 读取文件
        with open("stock_list.json", "r", encoding="utf-8") as f:
            stockList = json.load(f)

        # 处理数据
        tempStockList = []
        tempStockDir = os.path.join("temp")
        dirlist = os.listdir(tempStockDir)

        for stockCode in stockList:
            if stockCode in dirlist:
                #     打开data.json 获取 股票名称
                with open((os.path.join(tempStockDir, stockCode, "data.json")), "r", encoding="utf-8") as f:
                    dataJson = json.load(f)
                    stockName = dataJson[0]["概览"][0]["名称"]
                    tempStockList.append(stockCode + ":" + stockName)
            else:
                tempStockList.append(stockCode)

        # 写回文件
        with open("stock_list.json", "w", encoding="utf-8") as f:
            json.dump(tempStockList, f, ensure_ascii=False, indent=4)
    except Exception as e:
        with open("error.log", "a", encoding="utf-8") as f:
            f.write(str(e) + "\n")


def getImageText(reader, imageName):
    # 读取图像中的文本
    if "OBV" in imageName or "mid" in imageName:
        result = pytesseract.image_to_string(Image.open(imageName), lang='chi_sim')
    else:
        result = pytesseract.image_to_string(Image.open(imageName))
    print("result", result)
    resultList = (result.replace("|", "").replace(": ", ":").replace("\n", "")
                  .replace("{Z", "亿").replace("ROC ", "ROC_").replace("OBV ", "OBV_").replace("ROC_ ", "ROC_").replace(
        "OBV_ ", "OBV_")
                  .split(" "))
    ocrResultList = []
    for text in resultList:
        if ":" in text:
            key, value = text.split(":")
            if "top" in imageName:
                key = convertKeyTop(key)
            else:
                key = convertKey(key)
            ocrResultList.append({key: value})
    return ocrResultList
