import os
import platform
import shutil
from functools import partial
import json

from easyocr import easyocr
from kivy.config import Config

from utils import startGetData

# 注册字体文件
font_path = os.path.join("font", 'SourceHanSansCN-Normal.otf')

# 设置全局默认字体 必须在 导入其他 kivy 模块之前调用
Config.set('kivy', 'default_font', str(['SourceHanSansCN', font_path]))

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup
from kivy.clock import Clock

# 文件路径用于保存列表数据
DATA_FILE = os.path.join('stock_list.json')


class MyApp(App):
    def build(self):
        self.title = '股票数据爬取'
        self.root = BoxLayout(orientation='horizontal')

        # 左侧布局（添加爬取按钮和输入框）
        left_layout = BoxLayout(orientation='vertical', size_hint=(0.55, 1), padding=[10, 10], spacing=10)

        # 添加爬取按钮
        self.scrape_button = Button(text='开始爬取', size_hint_y=None, height=60)
        self.scrape_button.bind(on_press=self.start_scraping)  # 绑定点击事件

        # 添加打开结果文件夹按钮
        self.open_button = Button(text='打开结果文件夹', size_hint_y=None, height=60)
        self.open_button.bind(on_press=self.open_folder)

        # 设置输入框的 size_hint_x 为 0.9（占用 90% 宽度）
        self.input_field = TextInput(
            hint_text='输入股票代码, 例如 sz300750 是宁德时代的代码',
            size_hint_y=None,
            height=60,
            size_hint_x=0.9,  # 输入框占用容器的 90% 宽度
            multiline=False,  # 禁止多行输入
            on_text_validate=self.add_text  # 回车触发 add_text 方法
        )

        # 将输入框和添加按钮放入水平布局
        input_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=60, spacing=10)
        add_button = Button(text='添加', size_hint_y=None, height=60, size_hint_x=0.1)  # 按钮占用 10% 宽度
        add_button.bind(on_press=self.add_text)
        use_tips = Label(
            text="使用说明:\n请在输入框中输入股票代码,然后点击添加按钮,添加好所需要的股票之后点击开始爬取,耐心等待",
            size_hint_y=0.9,
            height=60,
            size_hint_x=1,
            text_size=(300, None),  # Limit the text width to 300px, and let height adjust automatically
            halign='left',
            valign='top',
        )

        # 添加输入框和按钮到水平布局
        input_layout.add_widget(self.input_field)
        input_layout.add_widget(add_button)

        left_layout.add_widget(use_tips)

        # 在scrape_button 上方添加打开结果文件夹按钮
        left_layout.add_widget(self.open_button)
        # 在输入框上方添加爬取按钮
        left_layout.add_widget(self.scrape_button)
        left_layout.add_widget(input_layout)

        # 右侧布局（文本列表）
        right_layout = ScrollView(size_hint=(0.45, 1))
        self.text_list_layout = BoxLayout(orientation='vertical', size_hint_y=None)
        self.text_list_layout.bind(minimum_height=self.text_list_layout.setter('height'))

        right_layout.add_widget(self.text_list_layout)

        # 将左右布局添加到根布局
        self.root.add_widget(left_layout)
        self.root.add_widget(right_layout)

        # 加载已保存的列表
        self.load_data()

        return self.root

    def open_folder(self, instance):
        path = os.path.join('result')
        if platform.system() == 'Darwin':  # macOS
            os.system(f'open "{path}"')
        elif platform.system() == 'Windows':  # Windows
            os.system(f'start {path}')
        else:
            raise NotImplementedError("Unsupported operating system")

    def start_scraping(self, instance):
        self.show_loading_popup()
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                items = json.load(f)
            startGetData(items, reader, self.onFinish, self.onError)

    def onFinish(self):
        Clock.schedule_once(lambda dt: self.close_loading_popup(), 0)
        Clock.schedule_once(lambda dt: self.show_tips_popup("爬取完成", False), 0)
        Clock.schedule_once(lambda dt: self.text_list_layout.clear_widgets(), 0)
        Clock.schedule_once(lambda dt: self.load_data(), 0)

    def onError(self, text,auto_dismiss=False):
        Clock.schedule_once(lambda dt: self.show_tips_popup(text, auto_dismiss), 0)

    def show_loading_popup(self):
        # 创建弹出框
        self.popup = Popup(title='爬取中，请耐心等待...', size_hint=(None, None), size=(400, 200))
        # 不能点击外部关闭
        self.popup.auto_dismiss = False
        self.popup.open()

    def show_tips_popup(self, text, auto_dismiss):
        # 创建弹出框
        self.tips_popup = Popup(title=text, size_hint=(None, None), size=(400, 200))
        # 不显示 进度条
        self.tips_popup.separator_color = [0, 0, 0, 0]
        self.tips_popup.open()
        #     延迟三秒后关闭弹出框
        if auto_dismiss:
            Clock.schedule_once(lambda dt: self.close_loading_popup(), 3)

    def close_loading_popup(self):
        # 关闭弹出框
        self.popup.dismiss()

    def add_text(self, instance):
        # 获取输入框中的文本
        text = self.input_field.text.strip()
        if len(text) == 0:
            return
        if text:
            # 创建一个水平布局来放置 Label 和 删除按钮
            item_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=60, spacing=10)

            # 创建一个标签并添加到布局
            label = Label(text=text, size_hint_y=None, height=60)

            # 创建删除按钮并绑定事件
            delete_button = Button(
                text='删除',
                size_hint_x=0.2,
                width=60,
                size_hint_y=None,
                height=55,
                padding=[10, 10]  # 设置按钮的内边距，使其看起来更大
            )

            # 使用 partial 来绑定 delete_text 方法并传递 item_layout
            delete_button.bind(on_press=partial(self.delete_text, item_layout))

            # 将标签和删除按钮添加到布局
            item_layout.add_widget(label)
            item_layout.add_widget(delete_button)

            # 将整个布局添加到文本列表的顶部
            self.text_list_layout.add_widget(item_layout, )

            # 手动更新布局
            self.text_list_layout.canvas.ask_update()
            # 保存当前列表项到文件
            self.save_data(label.text)

            # 清除列表
            self.text_list_layout.clear_widgets()
            self.load_data()

            # 清空输入框
            self.input_field.text = ''

    def delete_text(self, item_layout, instance):
        self.text_list_layout.remove_widget(item_layout)
        self.remove_data(item_layout.children[1].text)

    def remove_data(self, text):
        textItems = []
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                items = json.load(f)

            for item in items:
                if item != text:
                    textItems.append(item)

        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(textItems, f, ensure_ascii=False, indent=4)

    def save_data(self, text):
        # 获取所有文本项
        compairList = []
        textItems = []
        #
        # textItems.append(text)
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                items = json.load(f)

            # 将保存的列表项添加到界面
            for item in items:
                textItems.append(item)
                compairList.append(item.split(":")[0])

        # 判断是否已经存在
        if text not in compairList:
            # 添加到最前面
            textItems.insert(0, text)
        else:
            Clock.schedule_once(lambda dt: self.show_tips_popup("该代码已经存在", True), 0)
            return

        # 保存为 JSON 格式
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(textItems, f, ensure_ascii=False, indent=4)

    def load_data(self):
        # 如果文件存在，加载保存的列表项
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                items = json.load(f)

            # 将保存的列表项添加到界面
            for item in items:
                item_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=60, spacing=10)

                label = Label(text=item, size_hint_y=None, height=60)

                delete_button = Button(
                    text='删除',
                    size_hint_x=0.2,
                    width=60,
                    size_hint_y=None,
                    height=55,
                    padding=[10, 10]
                )

                delete_button.bind(on_press=partial(self.delete_text, item_layout))

                item_layout.add_widget(label)
                item_layout.add_widget(delete_button)

                # 将保存的数据插入到顶部
                self.text_list_layout.add_widget(item_layout)


if __name__ == '__main__':
    # 创建 OCR 识别器对象，指定语言
    modelPath = os.path.join("model")
    reader = easyocr.Reader(['en', 'ch_sim'], model_storage_directory=os.path.join("model"),
                            download_enabled=False)  # 英文和简体中文

    # 创建result 文件夹
    if not os.path.exists("result"):
        os.makedirs("result")
    # 删除 temp 文件夹 如果存在
    if os.path.exists("temp"):
        shutil.rmtree("temp")

    MyApp().run()
