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
    "MAS": "MA5",
    "MA5S": "MA5",
    "MAS5": "MA5",
    "MAS0": "MA30",
    "VA5": "MA5",
    "MAG60": "MA60",
    "MA380": "MA30",
    "MAG0": "MA60",
    "MAG6O0": "MA60",
    "MAS80": "MA30"
}

dictMap = {
    "RS6": "RSI6",
    "RS24": "RSI24",
    "WRG6": "WR6",
    "RS10": "RSI10",
    "WRI10": "WR10",
    "MA‘": "MA1",
    "CCL": "CCI",
    "MAT": "MA1",
    "MAS3": "MA3",
    "WRO6": "WR6",
    "CCl": "CCI",
    "DBV_MA": "OBV_MA",
    "RSIG": "RSI6",
    "成交量": "VOL",
    "[交量": "VOL",
    "交量": "VOL",
    "成交量;": "VOL",
    "嵌交量": "VOL",
    "成交垂": "VOL",
    "PDl": "PDI",
    "RS112": "RSI12",
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
    "DOBV_MA": "OBV_MA",
    "DBV": "OBV",
    "RS1I24": "RSI24",
    "1K": "K"
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
    left = width * 0.05
    # top = 743
    top = height / 2 + height * 0.142
    right = width / 2 + 50
    # bottom = height - 383
    bottom = height - height * 0.328
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
    cropped_img = cropped_img.convert("L")

    if "CCI" not in saveName:
        cropped_img = cropped_img.resize((cropped_img.width * 2, cropped_img.height * 2), Image.Resampling.LANCZOS)
    # if "CCI" in saveName:
    #     cropped_img = cropped_img.convert("L")
    #     cropped_img = cropped_img.resize((cropped_img.width * 3, cropped_img.height * 3), Image.Resampling.LANCZOS)
    enhancer = ImageEnhance.Contrast(cropped_img)
    cropped_img = enhancer.enhance(1)
    cropped_img = cropped_img.filter(ImageFilter.SHARPEN)
    cropped_img = cropped_img.filter(ImageFilter.SHARPEN)
    cropped_img = cropped_img.filter(ImageFilter.SHARPEN)
    cropped_img = cropped_img.filter(ImageFilter.SMOOTH_MORE)

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


def startWithThread(items, onFinish, onError, output_format, crawlThreadCount, ocrThreadCount):
    # 记录开始时间
    start_time = time.time()

    os.makedirs("temp", exist_ok=True)

    # 记录创建temp目录的时间
    step1 = time.time()
    # **创建一个共享的浏览器实例**
    co = ChromiumOptions().headless()
    chromePage = ChromiumPage(co)
    chromePage.get_tab().close()
    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=crawlThreadCount) as executor:
            futures = []
            for item in items:
                stockCode = item.split(":")[0]
                os.makedirs(os.path.join("temp", stockCode), exist_ok=True)
                # 将浏览器对象传递给线程任务
                futures.append(executor.submit(getData, stockCode, onError, chromePage, 0))
            concurrent.futures.wait(futures)
    finally:
        # 确保任务完成后关闭浏览器
        chromePage.quit()

        # 记录线程任务完成的时间
        step2 = time.time()

    # # 进行 OCR 数据处理任务
    with concurrent.futures.ThreadPoolExecutor(max_workers=ocrThreadCount) as executor:
        futures = [executor.submit(saveOcrJsonData, i, onError) for i in os.listdir("temp")]
        concurrent.futures.wait(futures)

    # 记录保存OCR数据的时间
    step3 = time.time()

    updateStockList()
    step4 = time.time()

    with open("stock_list.json", "r", encoding="utf-8") as f:
        stockList = json.load(f)
        for i in stockList:
            if ":" not in i:
                continue
            if output_format == "excel":
                generateExcel(i.split(":")[1], i.split(":")[0], onError)
            else:
                generateTxt(i.split(":")[1], i.split(":")[0], onError)
    step5 = time.time()

    # 计算每一步的耗时
    print(f"创建temp目录耗时: {step1 - start_time:.2f} 秒")
    print(f"线程任务完成耗时: {step2 - step1:.2f} 秒")
    print(f"保存OCR数据耗时: {step3 - step2:.2f} 秒")
    print(f"保存stock_list.json耗时: {step4 - step3:.2f} 秒")
    print(f"生成{output_format}耗时: {step5 - step4:.2f} 秒")
    # 完整执行时间
    print(f"总执行时间: {step5 - start_time:.2f} 秒")

    onFinish()


def saveOcrJsonData(stockCode, onError):
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
            ocr_result = getImageText(os.path.join(tempStockDir, i))
            print(ocr_result)
            jsonData.append({keyName: ocr_result})

            # 处理 JSON 数据
        if os.path.exists(jsonPath):
            with open(jsonPath, "r", encoding="utf-8") as f:
                existing_data = json.load(f)
            existing_data.extend(jsonData)
        else:
            existing_data = jsonData

        with open(jsonPath, "w", encoding="utf-8") as f:
            json.dump(existing_data, f, ensure_ascii=False, indent=4)

    except Exception as e:
        with open("error.log", "a", encoding="utf-8") as f:
            f.write(str(e) + "\n")
        onError(stockCode + "OCR识别失败")


def processOCR(stockCode):
    """
    单独处理 OCR 的多进程任务
    """
    try:
        saveOcrJsonData(stockCode, lambda error: print(error))
    except Exception as e:
        print(f"OCR 多进程错误: {e}")


def startGetData(items, onFinish, onError, output_format, crawlThreadCount, ocrThreadCount):
    threading.Thread(target=startWithThread,
                     args=(items, onFinish, onError, output_format, crawlThreadCount, ocrThreadCount)).start()


def getData(stockCode, onError, chromePage, retryTime):
    try:
        # 打开新的标签页，处理当前股票代码
        stockTab = chromePage.new_tab(f"https://quote.eastmoney.com/concept/{stockCode}.html?from=classic")

        # 等待页面加载并获取所需内容
        time.sleep(2)
        name = stockTab.ele("tag:span@class=name").text
        zde = stockTab.ele("tag:div@class=stockquote").ele("tag:span@class=zde").text
        zdf = stockTab.ele("tag:div@class=stockquote").ele("tag:span@class=zdf").text

        # 获取详情表格
        detailTable = stockTab.ele("tag:div@class=stockitems").ele("tag:table")
        trList = detailTable.ele("tag:tbody").eles("tag:tr")
        detailList = []
        for tr in trList:
            tdList = tr.eles("tag:td")
            for td in tdList[:-1]:  # 忽略最后一个 td
                item = td.ele("tag:div@class=item")
                key = item.ele("@class=l").text
                value = item.ele("@class=r").text
                detailList.append({key: value})

        # 切换到charts图表数据
        charts = stockTab.ele("tag:div@class=charts")
        li = charts.ele("tag:div").eles("tag:div")[0].ele("tag:ul").eles("tag:li")
        for i in li:
            if i.text == "日K":
                i.click()
                time.sleep(0.3)
                i.click()
                break

        # 保存图片和 JSON 数据
        imgFileNameList = []
        tablist = stockTab.ele("tag:div@class=f_zb").ele("tag:ul").eles("tag:li")
        for tab in tablist[1:]:
            tab.click()
            time.sleep(0.3)
            filename = f"charts_{tab.text}.png"
            canvas = charts.ele("tag:canvas")
            imgFileNameList.append(filename)
            canvas.get_screenshot(path=os.path.join("temp", stockCode), name=filename)

        stockTab.close()

        tempData = [
            {"名称": name},
            {"代码": stockCode},
            {"涨跌额": zde},
            {"涨跌幅": zdf},
        ]

        # 限制详情条目数量
        if len(detailList) > 12:
            tempData.extend(detailList[:12])
        else:
            tempData.extend(detailList)

        # 保存数据为 JSON
        os.makedirs(os.path.join("temp", stockCode), exist_ok=True)
        with open(os.path.join("temp", stockCode, "data.json"), "w", encoding="utf-8") as f:
            json.dump([{"概览": tempData}], f, ensure_ascii=False, indent=4)

        # 裁剪图片并处理
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
        if "没有找到元素。" in str(e) and retryTime < 3:
            print(f"{stockCode}: 没有找到元素，重试中...")
            time.sleep(5)
            getData(stockCode, onError, chromePage, retryTime + 1)
            return
        with open("error.log", "a", encoding="utf-8") as f:
            f.write(f"{stockCode} 错误：{str(e)}\n")
        onError(f"{stockCode} 获取数据失败")


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


def getImageText(imageName):
    # 读取图像中的文本
    if "OBV" in imageName or "mid" in imageName:
        result = pytesseract.image_to_string(Image.open(imageName), lang='chi_sim')
    else:
        result = pytesseract.image_to_string(Image.open(imageName))
    print("result", result)
    resultList = (result.replace("|", "").replace(": ", ":").replace("\n", "")
                  .replace("{Z", "亿").replace("ROC ", "ROC_").replace("OBV ", "OBV_").replace("ROC_ ", "ROC_").replace(
        "OBV_ ", "OBV_").replace("”", "").replace("“", "").replace("‘", "").replace("’", "").replace("; ", ":")
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
