import tkinter as tk
from tkinter import messagebox, ttk, simpledialog
import json
import os
from datetime import datetime, date, timedelta

DATA_FILE = "study_data.json"
LOG_FILE = "pomodoro_log.txt"
data = {
    "todos": [],
    "study_records": {},
    "pomodoro_count": 0,
    "theme": "light"
}

running = False
current_time = 0
timer_type = "work"
is_top = False
drag_item = None
timer_id = None  # 新增：用来保存定时器句柄

def load_data():
    global data
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

def save_data():
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def write_log(content):
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | {content}\n")

load_data()

def play_beep():
    root.bell()

def set_light_theme():
    root.config(bg="#f0f4f8")
    left_frame.config(bg="#e8f0fe")
    right_frame.config(bg="#e8f0fe")
    status_label.config(bg="#e8f0fe", fg="#666666")
    timer_label.config(bg="#e8f0fe")
    data["theme"] = "light"
    save_data()

def set_dark_theme():
    root.config(bg="#2c2c2c")
    left_frame.config(bg="#3a3a3a")
    right_frame.config(bg="#3a3a3a")
    status_label.config(bg="#3a3a3a", fg="#cccccc")
    timer_label.config(bg="#3a3a3a")
    data["theme"] = "dark"
    save_data()

def update_timer_status_ui():
    if timer_type == "work":
        status_label.config(text="🔥 当前：专注学习中", fg="#e74c3c")
        timer_label.config(fg="#e74c3c")
    else:
        status_label.config(text="🌿 当前：放松休息中", fg="#27ae60")
        timer_label.config(fg="#27ae60")

def check_time_input(val):
    try:
        num = int(val)
        return 1 <= num <= 120
    except:
        return False

def start_pomodoro():
    global running, current_time, timer_type, timer_id
    if running:
        return
    if not check_time_input(work_entry.get()) or not check_time_input(rest_entry.get()):
        messagebox.showerror("输入错误", "时长必须是 1~120 的整数！")
        return

    # 如果当前时间为0，说明是第一次开始，才重新设置
    if current_time <= 0:
        timer_type = "work"
        current_time = int(work_entry.get()) * 60

    # 清除旧定时器
    if timer_id is not None:
        root.after_cancel(timer_id)
        timer_id = None

    running = True
    update_timer_status_ui()
    update_timer()

def update_timer():
    global running, current_time, timer_type, timer_id
    if not running:
        return
    mins, secs = divmod(current_time, 60)
    timer_label.config(text=f"{mins:02d}:{secs:02d}")
    if current_time > 0:
        current_time -= 1
        timer_id = root.after(1000, update_timer)
    else:
        play_beep()
        if timer_type == "work":
            messagebox.showinfo("提醒", "✅ 专注时间结束，进入休息模式！")
            today = str(date.today())
            add_min = int(work_entry.get())
            data["study_records"][today] = data["study_records"].get(today, 0) + add_min
            data["pomodoro_count"] += 1
            write_log(f"完成番茄：{add_min}分钟")
            save_data()
            timer_type = "rest"
            current_time = int(rest_entry.get()) * 60
            update_timer_status_ui()
            update_timer()
        else:
            messagebox.showinfo("提醒", "🔔 休息完毕，请进入专注学习！")
            timer_type = "work"
            current_time = int(work_entry.get()) * 60
            update_timer_status_ui()
            update_timer()

def stop_timer():
    global running, timer_id
    running = False
    if timer_id is not None:
        root.after_cancel(timer_id)
        timer_id = None

def reset_timer():
    global running, current_time, timer_type, timer_id
    running = False
    if timer_id is not None:
        root.after_cancel(timer_id)
        timer_id = None
    current_time = 0
    timer_label.config(text="00:00", fg="#888888")
    timer_type = "work"
    status_label.config(text="准备就绪", fg="#666666" if data.get("theme")=="light" else "#cccccc")
    root.after(50, lambda: work_entry.focus_force())

def toggle_top():
    global is_top
    is_top = not is_top
    root.attributes("-topmost", is_top)

def on_drag_start(event):
    global drag_item
    selected = todo_list.selection()
    if selected:
        drag_item = selected[0]

def on_drag_motion(event):
    if not drag_item:
        return
    target = todo_list.identify_row(event.y)
    if target and target != drag_item:
        todo_list.move(drag_item, "", todo_list.index(target))

def on_drag_end(event):
    global drag_item
    if not drag_item:
        return
    new_order = []
    for item in todo_list.get_children():
        vals = todo_list.item(item, "values")
        content = vals[3]
        create_time = vals[4]
        for t in data["todos"]:
            if t["content"] == content and t["create_time"] == create_time:
                new_order.append(t)
                break
    data["todos"] = new_order
    save_data()
    refresh_todo_list()
    drag_item = None

def refresh_todo_list():
    todo_list.delete(*todo_list.get_children())
    sorted_todos = data["todos"]
    
    todo_list.tag_configure("high", foreground="#e74c3c")
    todo_list.tag_configure("mid", foreground="#f39c12")
    todo_list.tag_configure("low", foreground="#888888")
    todo_list.tag_configure("done", font=("微软雅黑", 9, "overstrike"))
    todo_list.tag_configure("overdue", foreground="#999999")
    todo_list.tag_configure("row_white", background="white")
    todo_list.tag_configure("row_blue", background="#f0f8ff")
    now_day = date.today()
    
    for idx, todo in enumerate(sorted_todos):
        is_done = todo.get("done", False)
        status = "✅ 已完成" if is_done else "🔲 未完成"
        level = todo.get("level", "中")
        content = todo.get("content", "")
        create_time = todo.get("create_time", "")
        deadline = todo.get("deadline", "")
        
        base_tag = ""
        if level == "高":
            base_tag = "high"
        elif level == "中":
            base_tag = "mid"
        else:
            base_tag = "low"
        
        all_tags = (base_tag,)
        if is_done:
            all_tags += ("done",)
        if deadline and not is_done:
            try:
                d = datetime.strptime(deadline, "%Y-%m-%d").date()
                if d < now_day:
                    all_tags += ("overdue",)
            except:
                pass
        
        row_tag = "row_white" if idx % 2 == 0 else "row_blue"
        all_tags += (row_tag,)

        todo_list.insert("", "end", values=(
            idx+1, level, status, content, create_time, deadline
        ), tags=all_tags)

def check_expire_todo():
    try:
        now_day = date.today()
        remind_list = []
        for t in data["todos"]:
            if t.get("done"):
                continue
            dl = t.get("deadline", "")
            if not dl:
                continue
            try:
                d = datetime.strptime(dl, "%Y-%m-%d").date()
                if d <= now_day:
                    remind_list.append(f"【{dl}】{t['content']}")
            except:
                continue
        if remind_list:
            messagebox.showwarning("任务到期提醒", "有已过期/今日截止任务：\n" + "\n".join(remind_list))
    except:
        pass

def get_max_day(y, m):
    if m in [4,6,9,11]:
        return 30
    if m == 2:
        if (y % 400 == 0) or (y % 4 == 0 and y % 100 != 0):
            return 29
        else:
            return 28
    return 31

def choose_deadline(default_date=""):
    cal_win = tk.Toplevel(root)
    cal_win.title("选择截止日期")
    cal_win.geometry("280x200")
    cal_win.transient(root)
    cal_win.grab_set()

    if default_date:
        try:
            dt = datetime.strptime(default_date, "%Y-%m-%d")
            y0, m0, d0 = dt.year, dt.month, dt.day
        except:
            y0, m0, d0 = date.today().year, date.today().month, date.today().day
    else:
        y0, m0, d0 = date.today().year, date.today().month, date.today().day

    res = {"date": ""}
    y_var = tk.IntVar(value=y0)
    m_var = tk.IntVar(value=m0)
    d_var = tk.IntVar(value=min(d0, get_max_day(y0, m0)))

    tk.Label(cal_win, text="选择日期").pack(pady=5)
    f = tk.Frame(cal_win)
    f.pack()

    year_box  = ttk.Spinbox(f, from_=2025, to=2035, textvariable=y_var, width=6)
    month_box = ttk.Spinbox(f, from_=1, to=12, textvariable=m_var, width=4)
    day_box   = ttk.Spinbox(f, from_=1, to=get_max_day(y0, m0), textvariable=d_var, width=4)

    year_box.grid(row=0,column=0,padx=2)
    month_box.grid(row=0,column=1,padx=2)
    day_box.grid(row=0,column=2,padx=2)

    def update_day_limit(*args):
        y = y_var.get()
        m = m_var.get()
        max_d = get_max_day(y, m)
        day_box.config(from_=1, to=max_d)
        if d_var.get() > max_d:
            d_var.set(max_d)

    y_var.trace_add("write", update_day_limit)
    m_var.trace_add("write", update_day_limit)

    def confirm():
        try:
            y = y_var.get()
            m = m_var.get()
            d = d_var.get()
            date(y, m, d)
            res["date"] = f"{y}-{m:02d}-{d:02d}"
        except:
            messagebox.showerror("错误", "日期不存在，请重新选择")
            return
        cal_win.destroy()

    def no_date():
        res["date"] = ""
        cal_win.destroy()

    tk.Button(cal_win, text="确定", command=confirm).pack(pady=5)
    tk.Button(cal_win, text="不设截止日期", command=no_date).pack()

    root.wait_window(cal_win)
    return res["date"]

def add_todo_by_enter(event):
    add_todo()

def add_todo():
    content = todo_input.get().strip()
    if not content:
        messagebox.showwarning("提示", "任务内容不能为空")
        return
    level = level_combo.get()
    deadline = choose_deadline()
    new_todo = {
        "content": content,
        "done": False,
        "create_time": str(date.today()),
        "level": level,
        "deadline": deadline
    }
    data["todos"].append(new_todo)
    todo_input.delete(0, tk.END)
    save_data()
    refresh_todo_list()

def double_click_todo(event):
    selected = todo_list.selection()
    if not selected:
        return
    item_id = selected[0]
    idx = todo_list.index(item_id)
    data["todos"][idx]["done"] = not data["todos"][idx].get("done", False)
    save_data()
    refresh_todo_list()

def edit_todo():
    selected = todo_list.selection()
    if not selected:
        messagebox.showwarning("提示", "请先选择任务")
        return
    item_id = selected[0]
    idx = todo_list.index(item_id)
    todo = data["todos"][idx]

    old_content = todo["content"]
    old_level = todo["level"]
    old_deadline = todo["deadline"]

    new_content = simpledialog.askstring("修改任务名称", "输入新任务名称", initialvalue=old_content)
    if not new_content:
        return

    edit_win = tk.Toplevel(root)
    edit_win.title("修改等级和截止日期")
    edit_win.geometry("300x180")
    edit_win.transient(root)

    tk.Label(edit_win, text="重新选择优先级").pack(pady=5)
    new_level_box = ttk.Combobox(edit_win, values=["高", "中", "低"], state="readonly")
    new_level_box.set(old_level)
    new_level_box.pack()

    current_deadline = [old_deadline]
    def select_new_date():
        current_deadline[0] = choose_deadline(current_deadline[0])
    tk.Button(edit_win, text="重新选择截止日期", command=select_new_date).pack(pady=8)

    def confirm_edit():
        data["todos"][idx]["content"] = new_content
        data["todos"][idx]["level"] = new_level_box.get()
        data["todos"][idx]["deadline"] = current_deadline[0]
        save_data()
        refresh_todo_list()
        edit_win.destroy()
        messagebox.showinfo("成功", "任务已修改")

    tk.Button(edit_win, text="确认保存修改", command=confirm_edit, bg="#27ae60", fg="white").pack(pady=5)

def delete_todo():
    selected = todo_list.selection()
    if not selected:
        messagebox.showwarning("提示", "请先选择任务")
        return
    if not messagebox.askyesno("确认删除", "确定要删除选中这条任务吗？"):
        return
    item_id = selected[0]
    idx = todo_list.index(item_id)
    del data["todos"][idx]
    save_data()
    refresh_todo_list()

def toggle_done():
    selected = todo_list.selection()
    if not selected:
        messagebox.showwarning("提示", "请先选择任务")
        return
    item_id = selected[0]
    idx = todo_list.index(item_id)
    data["todos"][idx]["done"] = not data["todos"][idx].get("done", False)
    save_data()
    refresh_todo_list()

def clear_finished_todo():
    if not messagebox.askyesno("确认", "确定清空所有已完成任务？不可恢复！"):
        return
    data["todos"] = [t for t in data["todos"] if not t.get("done", False)]
    save_data()
    refresh_todo_list()

def clear_all_todo():
    if messagebox.askyesno("确认", "确定清空所有任务？不可恢复"):
        data["todos"] = []
        save_data()
        refresh_todo_list()

def show_statistics():
    today = str(date.today())
    today_min = data["study_records"].get(today, 0)
    now = datetime.now()
    week_total = 0
    for day_str, mins in data["study_records"].items():
        try:
            d = datetime.strptime(day_str, "%Y-%m-%d")
            if now.isocalendar()[1] == d.isocalendar()[1]:
                week_total += mins
        except:
            pass
    tomato_cnt = data.get("pomodoro_count", 0)
    w = tk.Toplevel(root)
    w.title("学习统计")
    w.geometry("450x400")
    tk.Label(w, text=f"今日专注：{today_min} 分钟", font=("微软雅黑",12)).pack(pady=3)
    tk.Label(w, text=f"本周总计：{week_total} 分钟", font=("微软雅黑",12)).pack(pady=3)
    tk.Label(w, text=f"番茄完成：{tomato_cnt} 个", font=("微软雅黑",12)).pack(pady=3)
    tk.Label(w, text="\n近7天学习时长", font=("微软雅黑",12,"bold")).pack()
    canvas = tk.Canvas(w, width=400, height=160, bg="white")
    canvas.pack()
    bar_width = 40
    spacing = 12
    start_x = 20
    for i in range(7):
        d = date.today() - timedelta(days=6-i)
        month_day = f"{d.month}/{d.day}"
        val = data["study_records"].get(str(d), 0)
        height = min(val * 2, 130)
        x0 = start_x + i * (bar_width + spacing)
        y0 = 150 - height
        x1 = x0 + bar_width
        y1 = 150
        canvas.create_rectangle(x0, y0, x1, y1, fill="#3498db", outline="white")
        canvas.create_text(x0 + bar_width//2, 145, text=month_day, font=("微软雅黑",9))

# ========== 主界面 ==========
root = tk.Tk()
root.title("豪华版番茄钟学习助手")
root.geometry("950x680")
root.config(bg="#f0f4f8")
root.resizable(False, False)

tk.Label(root, text="🎓 豪华版番茄钟学习效率助手", 
         font=("微软雅黑",20,"bold"), bg="#f0f4f8").pack(pady=10)

left_frame = tk.Frame(root, bg="#e8f0fe", bd=2, relief="groove")
left_frame.place(x=30, y=60, width=420, height=580)

right_frame = tk.Frame(root, bg="#e8f0fe", bd=2, relief="groove")
right_frame.place(x=480, y=60, width=440, height=580)

tk.Label(left_frame, text="🍅 番茄专注计时器", font=("微软雅黑",15,"bold"), bg="#e8f0fe").pack(pady=8)
status_label = tk.Label(left_frame, text="准备就绪", font=("微软雅黑",13,"bold"), bg="#e8f0fe", fg="#666666")
status_label.pack(pady=5)

tk.Label(left_frame, text="专注时长", bg="#e8f0fe").pack(pady=2)
work_entry = tk.Entry(left_frame, width=15, font=12)
work_entry.insert(0, "25")
work_entry.pack(pady=2)

tk.Label(left_frame, text="休息时长", bg="#e8f0fe").pack(pady=2)
rest_entry = tk.Entry(left_frame, width=15, font=12)
rest_entry.insert(0, "5")
rest_entry.pack(pady=2)

timer_label = tk.Label(left_frame, text="00:00", font=("Consolas",48,"bold"), bg="#e8f0fe", fg="#888888")
timer_label.pack(pady=25)

tk.Button(left_frame, text="开始专注", command=start_pomodoro, width=12, bg="#27ae60", fg="white").pack(pady=3)
tk.Button(left_frame, text="暂停", command=stop_timer, width=12, bg="#e74c3c", fg="white").pack(pady=3)
tk.Button(left_frame, text="重置", command=reset_timer, width=12, bg="#95a5a6", fg="white").pack(pady=3)
tk.Button(left_frame, text="窗口置顶", command=toggle_top, width=12, bg="#8e44ad", fg="white").pack(pady=3)

theme_frame = tk.Frame(left_frame, bg="#e8f0fe")
theme_frame.pack(pady=12)
tk.Button(theme_frame, text="浅色主题", command=set_light_theme, width=10).grid(row=0, column=0, padx=8)
tk.Button(theme_frame, text="深色主题", command=set_dark_theme, width=10).grid(row=0, column=1, padx=8)

tk.Button(left_frame, text="查看统计图表", command=show_statistics, bg="#3498db", fg="white", width=14).pack(pady=8)

tk.Label(right_frame, text="输入待办任务", bg="#e8f0fe", font=("微软雅黑",10)).pack(pady=2)
todo_input = tk.Entry(right_frame, width=24, font=11)
todo_input.pack(pady=5)
todo_input.bind("<Return>", add_todo_by_enter)

tk.Label(right_frame, text="选择优先级", bg="#e8f0fe").pack(pady=2)
level_combo = ttk.Combobox(right_frame, values=["高", "中", "低"], state="readonly", width=24)
level_combo.set("中")
level_combo.configure(takefocus=False)
level_combo.pack(pady=3)

tk.Label(right_frame, text="单击选中变蓝可拖拽 | 双击快速标记完成/取消", 
         bg="#e8f0fe", font=("微软雅黑",9), fg="#666666").pack(pady=2)

bf = tk.Frame(right_frame, bg="#e8f0fe")
bf.pack(pady=8)
tk.Button(bf, text="添加", command=add_todo, bg="#27ae60", fg="white", width=6).grid(row=0,column=0,padx=3)
tk.Button(bf, text="完成", command=toggle_done, bg="#f39c12", fg="white", width=6).grid(row=0,column=1,padx=3)
tk.Button(bf, text="修改", command=edit_todo, bg="#3498db", fg="white", width=6).grid(row=0,column=2,padx=3)
tk.Button(bf, text="删除", command=delete_todo, bg="#e74c3c", fg="white", width=6).grid(row=0,column=3,padx=3)

tk.Button(right_frame, text="清理所有已完成任务", command=clear_finished_todo, 
          bg="#16a085", fg="white", width=22).pack(pady=4)
tk.Button(right_frame, text="一键清空所有待办", command=clear_all_todo, bg="#e67e22", width=22).pack(pady=4)

cols = ("序号","优先级","状态","任务内容","创建日期","截止日期")
todo_list = ttk.Treeview(right_frame, columns=cols, show="headings", height=16)
todo_list.bind("<ButtonPress-1>", on_drag_start)
todo_list.bind("<B1-Motion>", on_drag_motion)
todo_list.bind("<ButtonRelease-1>", on_drag_end)

for c in cols:
    todo_list.heading(c, text=c)

todo_list.column("序号", width=40, anchor="center")
todo_list.column("优先级", width=55, anchor="center")
todo_list.column("状态", width=65, anchor="center")
todo_list.column("任务内容", width=90)
todo_list.column("创建日期", width=90, anchor="center")
todo_list.column("截止日期", width=100, anchor="center")

todo_list.bind("<Double-Button-1>", double_click_todo)
todo_list.pack(pady=8)

refresh_todo_list()
check_expire_todo()

root.after(100, lambda: work_entry.focus_force())

def on_close():
    save_data()
    root.destroy()

root.protocol("WM_DELETE_WINDOW", on_close)
if data.get("theme") == "dark":
    set_dark_theme()

root.mainloop()
