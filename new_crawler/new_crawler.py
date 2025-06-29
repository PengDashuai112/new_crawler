import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import csv
import os
import json
from bs4 import BeautifulSoup
import jieba
import jieba.analyse
from collections import Counter
import matplotlib as mpl
import matplotlib.pyplot as plt
from wordcloud import WordCloud
import re
import random
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.edge.options import Options as EdgeOptions


# 用户管理系统
class UserManager:
    def __init__(self, filename='users.json'):
        self.filename = filename
        self.users = self.load_users()

    def load_users(self):
        if os.path.exists(self.filename):
            try:
                with open(self.filename, 'r') as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def save_users(self):
        with open(self.filename, 'w') as f:
            json.dump(self.users, f)

    def register(self, username, password):
        if username in self.users:
            return False, "用户名已存在"
        self.users[username] = password
        self.save_users()
        return True, "注册成功"

    def login(self, username, password):
        if username not in self.users:
            return False, "用户名不存在"
        if self.users[username] != password:
            return False, "密码错误"
        return True, "登录成功"


# 图形化界面主应用
class NewsCrawlerApp:
    def __init__(self, root, crawler_functions):
        self.root = root
        self.root.title("新闻爬虫分析系统")
        self.root.geometry("1000x700")
        self.root.resizable(True, True)

        self.crawler_functions = crawler_functions
        self.user_manager = UserManager()
        self.current_user = None
        self.crawler_results = None

        # 创建主框架
        self.main_frame = ttk.Frame(root)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # 初始显示登录界面
        self.show_login_screen()

    def show_login_screen(self):
        """显示登录界面"""
        self.clear_frame()

        # 创建登录框架
        login_frame = ttk.LabelFrame(self.main_frame, text="用户登录")
        login_frame.pack(pady=50, padx=100, fill=tk.BOTH, expand=True)

        # 用户名标签和输入框
        ttk.Label(login_frame, text="用户名:").grid(row=0, column=0, padx=10, pady=10, sticky=tk.W)
        self.username_entry = ttk.Entry(login_frame, width=30)
        self.username_entry.grid(row=0, column=1, padx=10, pady=10)

        # 密码标签和输入框
        ttk.Label(login_frame, text="密码:").grid(row=1, column=0, padx=10, pady=10, sticky=tk.W)
        self.password_entry = ttk.Entry(login_frame, width=30, show="*")
        self.password_entry.grid(row=1, column=1, padx=10, pady=10)

        # 按钮框架
        button_frame = ttk.Frame(login_frame)
        button_frame.grid(row=2, column=0, columnspan=2, pady=20)

        # 登录按钮
        login_button = ttk.Button(button_frame, text="登录", command=self.login)
        login_button.pack(side=tk.LEFT, padx=10)

        # 注册按钮
        register_button = ttk.Button(button_frame, text="注册", command=self.show_register_screen)
        register_button.pack(side=tk.LEFT, padx=10)

        # 游客登录按钮
        guest_button = ttk.Button(button_frame, text="游客登录", command=self.guest_login)
        guest_button.pack(side=tk.LEFT, padx=10)

    def show_register_screen(self):
        """显示注册界面"""
        self.clear_frame()

        # 创建注册框架
        register_frame = ttk.LabelFrame(self.main_frame, text="用户注册")
        register_frame.pack(pady=50, padx=100, fill=tk.BOTH, expand=True)

        # 用户名标签和输入框
        ttk.Label(register_frame, text="用户名:").grid(row=0, column=0, padx=10, pady=10, sticky=tk.W)
        self.reg_username_entry = ttk.Entry(register_frame, width=30)
        self.reg_username_entry.grid(row=0, column=1, padx=10, pady=10)

        # 密码标签和输入框
        ttk.Label(register_frame, text="密码:").grid(row=1, column=0, padx=10, pady=10, sticky=tk.W)
        self.reg_password_entry = ttk.Entry(register_frame, width=30, show="*")
        self.reg_password_entry.grid(row=1, column=1, padx=10, pady=10)

        # 确认密码标签和输入框
        ttk.Label(register_frame, text="确认密码:").grid(row=2, column=0, padx=10, pady=10, sticky=tk.W)
        self.reg_confirm_entry = ttk.Entry(register_frame, width=30, show="*")
        self.reg_confirm_entry.grid(row=2, column=1, padx=10, pady=10)

        # 按钮框架
        button_frame = ttk.Frame(register_frame)
        button_frame.grid(row=3, column=0, columnspan=2, pady=20)

        # 注册按钮
        register_button = ttk.Button(button_frame, text="提交注册", command=self.register)
        register_button.pack(side=tk.LEFT, padx=10)

        # 返回按钮
        back_button = ttk.Button(button_frame, text="返回登录", command=self.show_login_screen)
        back_button.pack(side=tk.LEFT, padx=10)

    def show_main_screen(self):
        """显示主操作界面"""
        self.clear_frame()

        # 创建顶部信息栏
        info_frame = ttk.Frame(self.main_frame)
        info_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(info_frame, text=f"欢迎, {self.current_user}!", font=("Arial", 12)).pack(side=tk.LEFT)
        ttk.Button(info_frame, text="退出登录", command=self.logout).pack(side=tk.RIGHT, padx=10)

        # 创建爬取控制框架
        control_frame = ttk.LabelFrame(self.main_frame, text="爬取设置")
        control_frame.pack(fill=tk.X, padx=20, pady=10)

        # 网站选择
        ttk.Label(control_frame, text="目标网站:").grid(row=0, column=0, padx=10, pady=10, sticky=tk.W)
        self.site_var = tk.StringVar()
        site_combobox = ttk.Combobox(control_frame, textvariable=self.site_var, width=40)
        site_combobox['values'] = (
            "https://www.toutiao.com/?wid=1749629680587",
            "https://news.sina.com.cn/roll/#pageid=153&lid=2509&k=&num=50&page=1"
        )
        site_combobox.current(0)
        site_combobox.grid(row=0, column=1, padx=10, pady=10)

        # 页数选择
        ttk.Label(control_frame, text="爬取页数:").grid(row=1, column=0, padx=10, pady=10, sticky=tk.W)
        self.page_var = tk.StringVar(value="3")
        page_spinbox = ttk.Spinbox(control_frame, from_=1, to=10, textvariable=self.page_var, width=10)
        page_spinbox.grid(row=1, column=1, padx=10, pady=10, sticky=tk.W)

        # 按钮框架
        button_frame = ttk.Frame(control_frame)
        button_frame.grid(row=2, column=0, columnspan=2, pady=20)

        # 开始爬取按钮
        crawl_button = ttk.Button(button_frame, text="开始爬取", command=self.start_crawling)
        crawl_button.pack(side=tk.LEFT, padx=10)

        # 保存结果按钮
        save_button = ttk.Button(button_frame, text="保存结果", command=self.save_results)
        save_button.pack(side=tk.LEFT, padx=10)

        # 创建结果显示框架
        result_frame = ttk.Frame(self.main_frame)
        result_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 创建标签页
        self.notebook = ttk.Notebook(result_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # 词云标签页
        wordcloud_tab = ttk.Frame(self.notebook)
        self.notebook.add(wordcloud_tab, text="词云图")

        # 饼图标签页
        pie_tab = ttk.Frame(self.notebook)
        self.notebook.add(pie_tab, text="热点词汇分布")

        # 数据表格标签页
        table_tab = ttk.Frame(self.notebook)
        self.notebook.add(table_tab, text="数据表格")

        # 初始化标签页内容
        self.wordcloud_frame = ttk.Frame(wordcloud_tab)
        self.wordcloud_frame.pack(fill=tk.BOTH, expand=True)

        self.pie_frame = ttk.Frame(pie_tab)
        self.pie_frame.pack(fill=tk.BOTH, expand=True)

        self.table_frame = ttk.Frame(table_tab)
        self.table_frame.pack(fill=tk.BOTH, expand=True)

        # 添加状态栏
        self.status_var = tk.StringVar(value="就绪")
        status_bar = ttk.Label(self.main_frame, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def clear_frame(self):
        """清除主框架中的所有内容"""
        for widget in self.main_frame.winfo_children():
            widget.destroy()

    def login(self):
        """处理登录操作"""
        username = self.username_entry.get()
        password = self.password_entry.get()

        if not username or not password:
            messagebox.showerror("错误", "用户名和密码不能为空")
            return

        success, message = self.user_manager.login(username, password)
        if success:
            self.current_user = username
            self.show_main_screen()
        else:
            messagebox.showerror("登录失败", message)

    def guest_login(self):
        """游客登录"""
        self.current_user = "游客"
        self.show_main_screen()

    def logout(self):
        """退出登录"""
        self.current_user = None
        self.show_login_screen()

    def register(self):
        """处理注册操作"""
        username = self.reg_username_entry.get()
        password = self.reg_password_entry.get()
        confirm = self.reg_confirm_entry.get()

        if not username or not password:
            messagebox.showerror("错误", "用户名和密码不能为空")
            return

        if password != confirm:
            messagebox.showerror("错误", "两次输入的密码不一致")
            return

        success, message = self.user_manager.register(username, password)
        if success:
            messagebox.showinfo("注册成功", message)
            self.show_login_screen()
        else:
            messagebox.showerror("注册失败", message)

    def start_crawling(self):
        """开始爬取新闻"""
        site_url = self.site_var.get()
        max_pages = int(self.page_var.get())

        if not site_url:
            messagebox.showerror("错误", "请选择目标网站")
            return

        self.status_var.set("爬取中，请稍候...")
        self.root.update()

        try:
            # 调用爬虫函数
            titles = self.crawler_functions['fetch_toutiao_news'](site_url, max_pages)

            # 分析关键词
            keywords = self.crawler_functions['analyze_keywords'](titles)

            # 生成词云图
            wordcloud_path = 'wordcloud.png'
            self.crawler_functions['generate_wordcloud'](keywords, wordcloud_path)

            # 保存结果
            self.crawler_results = {
                'titles': titles,
                'keywords': keywords,
                'wordcloud_path': wordcloud_path
            }

            # 更新UI显示结果
            self.display_results()
            self.status_var.set("爬取完成")

        except Exception as e:
            self.status_var.set("爬取失败")
            messagebox.showerror("错误", f"爬取过程中发生错误:\n{str(e)}")

    def display_results(self):
        """显示爬取结果"""
        if not self.crawler_results:
            return

        # 显示词云图
        self.display_wordcloud()

        # 显示饼图
        self.display_pie_chart()

        # 显示数据表格
        self.display_data_table()

    def display_wordcloud(self):
        """显示词云图"""
        # 清除之前的显示
        for widget in self.wordcloud_frame.winfo_children():
            widget.destroy()

        # 创建图像显示区域
        image_label = ttk.Label(self.wordcloud_frame)
        image_label.pack(fill=tk.BOTH, expand=True)

        # 显示词云图
        try:
            from PIL import Image, ImageTk
            img = Image.open(self.crawler_results['wordcloud_path'])
            img = img.resize((600, 400), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            image_label.configure(image=photo)
            image_label.image = photo  # 保持引用
        except Exception as e:
            ttk.Label(self.wordcloud_frame, text=f"无法显示词云图: {str(e)}").pack()

    def display_pie_chart(self):
        """显示热点词汇饼图"""
        # 清除之前的显示
        for widget in self.pie_frame.winfo_children():
            widget.destroy()

        if not self.crawler_results or not self.crawler_results['keywords']:
            ttk.Label(self.pie_frame, text="没有关键词数据").pack()
            return

        # 创建饼图
        fig, ax = plt.subplots(figsize=(6, 4))

        # 准备数据 - 只取前20个关键词
        keywords = self.crawler_results['keywords'][:20]
        labels = [kw[:6] + '...' if len(kw) > 6 else kw for kw in keywords]  # 缩短长标签
        sizes = [1] * len(keywords)  # 等分饼图

        # 绘制饼图
        ax.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90)
        ax.axis('equal')  # 确保饼图是圆形

        # 在Tkinter中显示饼图
        canvas = FigureCanvasTkAgg(fig, master=self.pie_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def display_data_table(self):
        """显示数据表格"""
        # 清除之前的显示
        for widget in self.table_frame.winfo_children():
            widget.destroy()

        if not self.crawler_results or not self.crawler_results['keywords']:
            ttk.Label(self.table_frame, text="没有关键词数据").pack()
            return

        # 创建表格框架
        table_container = ttk.Frame(self.table_frame)
        table_container.pack(fill=tk.BOTH, expand=True)

        # 创建滚动条
        scrollbar = ttk.Scrollbar(table_container)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 创建表格
        columns = ("排名", "关键词", "出现频率")
        table = ttk.Treeview(table_container, columns=columns, show="headings", yscrollcommand=scrollbar.set)

        # 配置列
        table.column("排名", width=50, anchor=tk.CENTER)
        table.column("关键词", width=150, anchor=tk.W)
        table.column("出现频率", width=100, anchor=tk.CENTER)

        # 设置列标题
        table.heading("排名", text="排名")
        table.heading("关键词", text="关键词")
        table.heading("出现频率", text="出现频率")

        # 添加数据
        keywords = self.crawler_results['keywords']
        for i, kw in enumerate(keywords, 1):
            table.insert("", tk.END, values=(i, kw, "高频" if i <= 10 else "中频" if i <= 20 else "低频"))

        table.pack(fill=tk.BOTH, expand=True)
        scrollbar.config(command=table.yview)

    def save_results(self):
        """保存爬取结果"""
        if not self.crawler_results or not self.crawler_results['keywords']:
            messagebox.showwarning("警告", "没有可保存的数据")
            return

        # 请求保存文件位置
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV文件", "*.csv"), ("所有文件", "*.*")],
            title="保存热点词汇"
        )

        if not file_path:
            return

        try:
            # 保存关键词到CSV
            keywords = self.crawler_results['keywords']
            with open(file_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(["排名", "关键词"])
                for i, kw in enumerate(keywords, 1):
                    writer.writerow([i, kw])

            # 保存新闻标题到另一个文件
            titles_path = os.path.splitext(file_path)[0] + "_titles.csv"
            titles = self.crawler_results['titles']
            with open(titles_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(["序号", "新闻标题"])
                for i, title in enumerate(titles, 1):
                    writer.writerow([i, title])

            messagebox.showinfo("保存成功", f"数据已保存到:\n{file_path}\n{titles_path}")

        except Exception as e:
            messagebox.showerror("保存失败", f"保存数据时出错:\n{str(e)}")


# 主函数
def main():
    # 创建主窗口
    root = tk.Tk()

    # 爬虫功能函数
    crawler_functions = {
        'fetch_toutiao_news': fetch_toutiao_news,
        'analyze_keywords': analyze_keywords,
        'generate_wordcloud': generate_wordcloud
    }

    # 创建应用
    app = NewsCrawlerApp(root, crawler_functions)

    # 启动主循环
    root.mainloop()


if __name__ == "__main__":
    # 设置中文字体
    mpl.rcParams['font.family'] = 'SimHei'
    mpl.rcParams['axes.unicode_minus'] = False

    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36 Edg/137.0.0.0',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
        'Referer': 'https://www.toutiao.com/?wid=1749629680587',
        'Connection': 'keep-alive',
        'cookie': '__ac_signature=_02B4Z6wo00f01nrq8DQAAIDCTc40aQknxBp6yvSAAPcC18; tt_webid=7514602195262998043; ttcid=d5ff4ab5e68b44f7bb9c87892deac82121; local_city_cache=%E6%98%86%E6%98%8E; csrftoken=39c6428b3d1b7e51935cde22decf2a9f; s_v_web_id=verify_mbroc7mr_VRv6bIsa_zpqw_4kbn_9EDx_jt6kEMHV7N5K; _ga=GA1.1.1856050421.1749629686; gfkadpd=24,6457; ttwid=1%7CuZcAxZgZZfPS6UG0OuNgX05vm6CkUyZXfQxbgxUqDt8%7C1750258656%7Cab19f283c650496fbf31de472aa49057815555da11eece3b37a6a4fc9ab89d89; tt_scid=ITq8rHHUIrgxDdYxq4Vmli19XZuYOWlzdFONbOswKUsfMpibH36gSZMl5dfTBWHqaa67; _ga_QEHZPBE5HH=GS2.1.s1750258657$o9$g1$t1750258796$j60$l0$h0'
    }  # 今日头条

    # 代理设置
    PROXIES = {
        'http': 'http://127.0.0.1:8080',
    }


    def scroll_to_load_content(driver, scroll_count):
        """滚动页面加载隐藏内容"""
        print(f"开始滚动页面以加载隐藏内容（{scroll_count}次）...")
        for i in range(scroll_count):
            # 滚动到底部
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            print(f"滚动 {i + 1}/{scroll_count}，等待内容加载...")

            # 随机等待时间（1-3秒）
            time.sleep(random.uniform(1, 3))


    def fetch_toutiao_news(url, max_page):
        """使用Selenium爬取新闻标题"""
        print(f"开始爬取新闻网站，目标URL: {url}")

        # 配置浏览器选项
        options = EdgeOptions()
        options.add_argument('--headless')  # 无头模式
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument(f'user-agent={HEADERS["User-Agent"]}')

        # 创建浏览器实例
        driver = webdriver.Edge(options=options)
        all_titles = []

        try:
            # 打开网页
            driver.get(url)
            print("页面加载完成，等待内容渲染...")

            # 等待主要内容加载
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )

            # 滚动加载更多内容
            scroll_to_load_content(driver, scroll_count=max_page)

            # 获取页面源码
            html_content = driver.page_source

            # 解析HTML
            soup = BeautifulSoup(html_content, 'html.parser')

            # 解析新闻标题
            titles = parse_titles(soup)
            all_titles.extend(titles)
            print(f"获取到{len(titles)}条新闻标题")

        except Exception as e:
            print(f"爬取失败: {e}")
            raise e
        finally:
            driver.quit()

        # 去重并返回
        unique_titles = list(set(all_titles))
        print(f"共获取到{len(unique_titles)}条唯一新闻标题")
        return unique_titles


    def parse_titles(soup):
        """解析HTML获取新闻标题"""
        titles = []

        # 根据提供的HTML结构解析标题
        title_elements = soup.find_all('a', target='_blank')

        # 备用选择器
        if not title_elements:
            title_elements = soup.select('.feed-card-article-r .title')
        if not title_elements:
            title_elements = soup.select('[aria-label]')

        for elem in title_elements:
            # 提取标题文本
            title = elem.get_text().strip()

            # 清理标题中的特殊字符和多余空格
            title = re.sub(r'\s+', ' ', title)
            title = re.sub(r'[\n\t]', '', title)

            if title and len(title) > 5:  # 过滤过短标题
                titles.append(title)

        return titles


    def analyze_keywords(titles, top_n=20):
        '''分析新闻标题中的关键词'''
        if not titles:
            return []

        # 合并所有标题为一个文本
        text = ' '.join(titles)

        # 使用jieba进行关键词提取
        keywords = jieba.analyse.extract_tags(
            text,
            topK=top_n * 2,  # 提取更多关键词以便后续过滤
            withWeight=False,
            allowPOS=('ns', 'n', 'vn', 'v')  # 允许的词性：地名、名词、动名词、动词
        )

        # 过滤过短的词（长度至少为2）
        filtered_keywords = [kw for kw in keywords if len(kw) > 1]

        # 统计词频
        word_counts = Counter(filtered_keywords)

        # 获取前top_n个高频词
        top_keywords = [word for word, count in word_counts.most_common(top_n)]

        return top_keywords


    def generate_wordcloud(keywords, save_path='wordcloud.png'):
        """生成热点词汇图"""
        if not keywords:
            print("没有关键词可生成词云")
            return save_path

        # 创建关键词文本（词频越高，重复次数越多）
        text = ' '.join(keywords * 3)  # 增加重复次数以突出重要词汇

        # 设置中文字体路径
        font_path = 'simhei.ttf'  # 确保字体文件存在

        # 创建词云对象
        wordcloud = WordCloud(
            font_path=font_path,
            width=1000,
            height=700,
            background_color='white',
            max_words=100,
            colormap='viridis',
            contour_width=1,
            contour_color='steelblue'
        ).generate(text)

        # 生成并保存词云图
        plt.figure(figsize=(15, 10))
        plt.imshow(wordcloud, interpolation='bilinear')
        plt.axis('off')
        plt.title('新闻热点词汇分析', fontsize=20, pad=20)

        # 添加底部信息
        plt.figtext(0.5, 0.01,
                    f"数据来源: 新闻网站 | 生成时间: {time.strftime('%Y-%m-%d %H:%M')}",
                    ha='center', fontsize=10, color='gray')

        plt.savefig(save_path, bbox_inches='tight', dpi=300)
        print(f"热点词汇图已保存至: {save_path}")

        # 关闭图形，避免在非GUI环境中出现问题
        plt.close()

        return save_path


    # 启动GUI应用
    main()