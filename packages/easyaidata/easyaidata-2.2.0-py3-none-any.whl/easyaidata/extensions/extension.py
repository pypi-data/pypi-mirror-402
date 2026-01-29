"""测试拓展文件"""

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
        "test_button_2", 
        "测试按钮2", 
        lambda: test_function_2(app)
    )
    
    app.add_extension_button(
        "test_open_new_tab", 
        "在新标签打开数据", 
        lambda: test_open_new_tab(app)
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

# 测试函数1
def test_function_1(app):
    """测试函数1"""
    if not app.current_tab:
        return
    
    # 获取当前标签的数据
    tab_info = app.tabs[app.current_tab]
    df = tab_info["data"]
    
    if df is not None:
        print(f"当前标签: {app.current_tab}")
        print(f"数据形状: {df.shape}")
        print(f"前5行数据:\n{df.head()}")
    else:
        print("当前标签无数据")

# 测试函数2
def test_function_2(app):
    """测试函数2"""
    if not app.current_tab:
        return
    
    # 获取当前标签的数据
    tab_info = app.tabs[app.current_tab]
    df = tab_info["data"]
    
    if df is not None:
        # 对数据进行简单处理
        processed_df = df.copy()
        
        # 添加一个新列
        if "测试列" not in processed_df.columns:
            processed_df["测试列"] = range(len(processed_df))
        
        # 在新标签打开处理后的数据
        app.open_in_new_tab({
            "df": processed_df,
            "name": f"{app.current_tab}_处理后"
        })
    else:
        print("当前标签无数据")

# 测试在新标签打开数据
def test_open_new_tab(app):
    """测试在新标签打开数据"""
    import pandas as pd
    import numpy as np
    
    # 创建测试数据
    data = {
        "ID": range(1, 51),
        "姓名": [f"用户{i}" for i in range(1, 51)],
        "年龄": np.random.randint(18, 60, 50),
        "性别": np.random.choice(["男", "女"], 50),
        "城市": np.random.choice(["北京", "上海", "广州", "深圳"], 50)
    }
    
    df = pd.DataFrame(data)
    
    # 在新标签打开数据
    app.open_in_new_tab({
        "df": df,
        "name": "测试数据标签"
    })

# 测试透视表格功能
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
    
    # 显示菜单（在鼠标位置）
    test_menu.post(app.root.winfo_pointerx(), app.root.winfo_pointery())

# 测试对话框功能
def test_dialog(app):
    """测试对话框功能"""
    if not app.current_tab:
        return
    
    tab_info = app.tabs[app.current_tab]
    df = tab_info["data"]
    
    if df is not None:
        row_count = len(df)
        
        # 创建对话框
        dialog = tk.Toplevel(app.root)
        dialog.title("对话框测试")
        dialog.geometry("300x150")
        dialog.configure(bg="#121212")
        dialog.transient(app.root)
        dialog.grab_set()
        
        # 居中显示
        dialog.update_idletasks()
        width = 300
        height = 150
        x = (dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (dialog.winfo_screenheight() // 2) - (height // 2)
        dialog.geometry(f"{width}x{height}+{x}+{y}")
        
        # 标签
        label = ttk.Label(dialog, text=f"当前表格行数: {row_count}", style="Tool.TLabel")
        label.pack(pady=30)
        
        # 按钮
        button_frame = ttk.Frame(dialog, style="Main.TFrame")
        button_frame.pack(pady=10)
        
        def on_ok():
            """确定按钮回调"""
            # 在新标签打开前7行数据
            top7_df = df.head(7)
            app.open_in_new_tab({
                "df": top7_df,
                "name": f"{app.current_tab}_前7行"
            })
            dialog.destroy()
        
        # 使用标准tk按钮
        ok_button = tk.Button(button_frame, text="确定", command=on_ok)
        ok_button.config(fg="white", bg="#424242", font=('微软雅黑', 10, 'bold'), padx=15, pady=5, relief="flat")
        ok_button.pack(side=tk.LEFT, padx=10)
        
        cancel_button = tk.Button(button_frame, text="取消", command=dialog.destroy)
        cancel_button.config(fg="white", bg="#424242", font=('微软雅黑', 10, 'bold'), padx=15, pady=5, relief="flat")
        cancel_button.pack(side=tk.LEFT, padx=10)
    else:
        print("当前表格无数据")
