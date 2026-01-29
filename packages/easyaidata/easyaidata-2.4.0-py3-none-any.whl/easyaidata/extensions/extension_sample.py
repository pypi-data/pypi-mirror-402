"""测试拓展文件"""

import tkinter as tk
from tkinter import ttk, messagebox
from core.viewer import SETTING_style_UI

# 拓展初始化函数
def init_extension(app):
    """初始化拓展"""
    print("初始化测试拓展")
    
    # 添加拓展工具栏
    toolbar = app.add_extension_toolbar()
    
    # 添加测试按钮
    app.add_extension_button(
        "test_button_1", 
        "测试按钮1", 
        lambda: test_function_1(app)
    )

    app.add_extension_button(
        "test_pivot_table", 
        "透视表格", 
        lambda: test_pivot_table(app)
    )
    
    app.add_extension_button(
        "test_menu", 
        "测试菜单", 
        lambda: test_menu(app)
    )
    
    app.add_extension_button(
        "test_sample_ui", 
        "测试UI界面", 
        lambda: test_sample_ui(app)
    )


# 测试透视表格和在新标签的新标签打数据功能
def test_pivot_table(app):
    """测试透视表格功能"""
    if not app.current_tab:
        return
    
    tab_info = app.tabs[app.current_tab]
    df = tab_info["data"]
    
    if df is not None and "城市" in df.columns:
        # 对城市列做数据统计
        city_counts = df["城市"].value_counts().reset_index()
        city_counts.columns = ["城市", "数量"]
        
        # 在新标签打开统计结果
        app.open_in_new_tab({
            "df": city_counts,
            "name": f"{app.current_tab}_城市统计"
        })
    else:
        print("当前表格无城市列或无数据")

# 测试菜单功能
def test_menu(app):
    """测试菜单功能"""
    if not app.current_tab:
        return
    
    # 创建菜单窗口
    menu_window = app.root
    
    # 创建菜单
    test_menu = tk.Menu(menu_window, tearoff=0, background="#333333", foreground="white")
    test_menu.add_command(label="对话框测试", command=lambda: test_dialog(app))
    
    # 显示菜单（在鼠标位置上方）
    # 计算菜单高度，假设每个菜单项高度为20像素
    menu_height = 20 * test_menu.index('end') if test_menu.index('end') is not None else 40
    # 向上偏移菜单位置
    test_menu.post(app.root.winfo_pointerx(), app.root.winfo_pointery() - menu_height)


# 测试函数1
def test_function_1(app):
    """测试函数1"""
    print("测试函数1被调用")
    messagebox.showinfo("测试", "测试函数1被调用", parent=app.root)


# 测试对话框
def test_dialog(app):
    """测试对话框"""
    messagebox.showinfo("测试", "对话框测试", parent=app.root)


# 测试UI界面
def test_sample_ui(app):
    """测试UI界面"""
    if not app.current_tab:
        return
    
    tab_info = app.tabs[app.current_tab]
    df = tab_info["data"]
    
    if df is not None:
        # 创建并显示测试界面
        test_abc(df, app)
    else:
        messagebox.showerror("错误", "当前标签页无数据", parent=app.root)


class test_abc:
    """
    测试类，用于显示一个带有各种控件的TK界面，并支持将数据返回给app.py
    
    Args:
        df: pandas DataFrame，要显示的数据
        app: 应用实例，用于在新标签页中显示返回的数据
    """
    def __init__(self, df, app=None):
        self.df = df
        self.app = app
        self.root = None
        self.create_ui()
    
    def create_ui(self):
        """
        创建用户界面
        """
        # 创建主窗口
        if self.app and hasattr(self.app, 'root'):
            self.root = tk.Toplevel(self.app.root)
        else:
            self.root = tk.Tk()
        
        # 隐藏窗口，避免初始化过程中的闪烁
        self.root.withdraw()
        self.root.title("测试界面")
        
        # 应用主题样式
        bg_color, frame_color, button_color, text_color, highlight_color = SETTING_style_UI(self.root)
        
        # 设置窗口背景色
        self.root.configure(bg=bg_color)
        
        # 设置窗口大小并居中
        ww = 800
        wh = 600
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        x = (sw - ww) // 2
        y = (sh - wh) // 2
        self.root.geometry(f"{ww}x{wh}+{x}+{y}")
        
        # 创建主框架
        main_frame = ttk.Frame(self.root, style="Main.TFrame")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # 设置样式
        style = ttk.Style()
        style.configure("Form.TFrame", background=bg_color)
        style.configure("Form.TLabel", background=bg_color, foreground=text_color)
        # 修复下拉选择框样式，参考Tool.TCombobox样式
        style.configure("Form.TCombobox", 
                      background=bg_color, 
                      foreground=text_color, 
                      borderwidth=1, 
                      fieldbackground=frame_color,
                      relief="flat",
                      bordercolor="#5a6373"
                      )
        # 设置下拉列表样式
        style.configure("Form.TCombobox.Listbox", 
                      background=frame_color,  # 下拉列表背景
                      foreground=text_color   # 下拉列表字体
                      )
        # 添加样式映射
        style.map("Form.TCombobox", 
                  fieldbackground=[("readonly", frame_color)],
                  background=[("active", "#5a6373")],
                  foreground=[("active", text_color)])
        # 设置按钮样式，无边框
        style.configure("Form.TButton", 
                      background=button_color, 
                      foreground=text_color,
                      borderwidth=0,
                      relief="flat")
        # 设置按钮悬停效果，参考数据透视按钮
        secondary_color = "#5a6373"  # 与viewer.py中的secondary_color一致
        style.map("Form.TButton", 
                  background=[("active", secondary_color), ("disabled", "#BDBDBD")],
                  foreground=[("disabled", "#757575")])
        style.configure("Form.TLabelframe", background=bg_color, foreground=text_color)
        style.configure("Form.TLabelframe.Label", background=bg_color, foreground=text_color)
        style.configure("Form.TRadiobutton", background=bg_color, foreground=text_color)
        
        # 1. 下拉选择框（选择df的列）
        combo_frame = ttk.Frame(main_frame, style="Form.TFrame")
        combo_frame.pack(fill=tk.X, pady=(0, 20))
        
        combo_label = ttk.Label(combo_frame, text="选择列:", style="Form.TLabel")
        combo_label.pack(side=tk.LEFT, padx=10)
        
        self.column_var = tk.StringVar(self.root)
        columns = list(self.df.columns)
        self.combobox = ttk.Combobox(combo_frame, textvariable=self.column_var, values=columns, width=20, style="Form.TCombobox", state="readonly")
        self.combobox.pack(side=tk.LEFT, padx=10)
        if columns:
            self.combobox.current(0)
        
        # 2. 单选框
        radio_frame = ttk.Frame(main_frame, style="Form.TFrame")
        radio_frame.pack(fill=tk.X, pady=(0, 20))
        
        radio_label = ttk.Label(radio_frame, text="选择选项:", style="Form.TLabel")
        radio_label.pack(side=tk.LEFT, padx=10)
        
        self.radio_var = tk.StringVar(self.root)
        self.radio_var.set("选项1")
        
        # 为单选框创建并配置样式
        style.configure("Form.TRadiobutton", 
                      background=bg_color, 
                      foreground=text_color,
                      indicatorbackground=bg_color,
                      indicatorforeground=text_color,
                      borderwidth=1,
                      relief="flat",
                      bordercolor=highlight_color)
        style.map("Form.TRadiobutton", 
                  background=[("active", bg_color)],
                  foreground=[("active", text_color)],
                  indicatorbackground=[("selected", highlight_color), ("active", bg_color)])
        
        radio1 = ttk.Radiobutton(radio_frame, text="选项1", variable=self.radio_var, value="选项1", style="Form.TRadiobutton")
        radio1.pack(side=tk.LEFT, padx=10)
        
        radio2 = ttk.Radiobutton(radio_frame, text="选项2", variable=self.radio_var, value="选项2", style="Form.TRadiobutton")
        radio2.pack(side=tk.LEFT, padx=10)
        
        # 3. 文本输入框
        text_frame = ttk.Frame(main_frame, style="Form.TFrame")
        text_frame.pack(fill=tk.X, pady=(0, 20))
        
        text_label = ttk.Label(text_frame, text="文本输入:", style="Form.TLabel")
        text_label.pack(side=tk.LEFT, padx=10)
        
        self.text_var = tk.StringVar(self.root)
        self.text_entry = ttk.Entry(text_frame, textvariable=self.text_var, width=40, style="Form.TEntry")
        self.text_entry.pack(side=tk.LEFT, padx=10)
        
        # 4. Treeview 显示 df 的列
        tree_frame = ttk.LabelFrame(main_frame, text="数据列", style="Form.TLabelframe")
        tree_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 20))
        
        # 创建 Treeview
        self.tree = ttk.Treeview(tree_frame, columns=("column"), show="headings")
        self.tree.heading("column", text="列名")
        self.tree.column("column", width=200)
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.pack(fill=tk.BOTH, expand=True)
        
        # 填充数据列
        for col in columns:
            self.tree.insert("", tk.END, values=(col,))
        
        # 5. 按钮框架
        button_frame = ttk.Frame(main_frame, style="Form.TFrame")
        button_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 按钮1：提示文本输入框的内容
        def show_message():
            text = self.text_var.get()
            messagebox.showinfo("提示", f"文本输入框的内容: {text}", parent=self.root)
        
        button1 = ttk.Button(button_frame, text="显示文本内容", command=show_message, style="Form.TButton")
        button1.pack(side=tk.LEFT, padx=20)
        
        # 按钮2：把 df 返回到 app.py 的新选项卡
        def return_df():
            if self.app and hasattr(self.app, 'open_in_new_tab'):
                self.app.open_in_new_tab({"name": "测试返回数据", "df": self.df, "methon": "测试"})
                self.root.destroy()
            else:
                messagebox.showerror("错误", "无法返回数据到app.py", parent=self.root)
        
        button2 = ttk.Button(button_frame, text="返回数据到新选项卡", command=return_df, style="Form.TButton")
        button2.pack(side=tk.LEFT, padx=20)
        
        # 按钮3：使用表格查看器显示数据（在主界面新选项卡打开）
        def show_table_viewer():
            if self.app and hasattr(self.app, 'open_in_new_tab'):
                self.app.open_in_new_tab({"name": "表格查看器", "df": self.df, "methon": "查看"})
            else:
                # 如果没有app对象，回退到使用PROGRAM_DataFrameViewer
                from core.viewer import PROGRAM_DataFrameViewer
                PROGRAM_DataFrameViewer(self.df)
        
        button3 = ttk.Button(button_frame, text="表格查看器", command=show_table_viewer, style="Form.TButton")
        button3.pack(side=tk.LEFT, padx=20)
        
        # 按钮4：使用文本查看器显示数据
        def show_text_viewer():
            from core.viewer import PROGRAM_display_content_in_textbox
            # 将DataFrame转换为字符串
            content = self.df.to_string()
            PROGRAM_display_content_in_textbox(content)
        
        button4 = ttk.Button(button_frame, text="文本查看器", command=show_text_viewer, style="Form.TButton")
        button4.pack(side=tk.LEFT, padx=20)
        
        # 显示窗口
        self.root.deiconify()
        
        # 运行主循环
        self.root.mainloop()

