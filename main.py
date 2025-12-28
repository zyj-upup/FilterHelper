from tkinter import *
from tkinter.simpledialog import askstring
from tkinter.messagebox import askyesno, showwarning
import tkinter.font as tkFont

import os
import json
import random
import string
from typing import List


# =========================== 数据库类 =========================== #
class FilterData:
    def __init__(self, fid: str, name: str, content: str):
        self.fid = fid
        self.name = name
        self.content = content


class CategoryData:
    def __init__(self, cid: str, name: str, filters: List[FilterData]):
        self.cid = cid
        self.name = name
        self.filters = filters

    def add_filter(self, filter_data: FilterData):
        self.filters.append(filter_data)


class DataBase:
    def __init__(self, json_path: str = None):
        self.json_path = json_path
        self.categories: List[CategoryData] = []
        # 用于记录已使用的 ID, 避免重复
        self._used_ids: set = set()
        if json_path is not None:
            self.load_json(json_path)

    def load_json(self, json_path: str = None):
        if json_path is not None:
            self.json_path = json_path
        if self.json_path is None:
            raise ValueError("JSON 文件路径不能为空")
        if not os.path.exists(self.json_path):
            raise FileNotFoundError(f"JSON 文件不存在: {self.json_path}")
        with open(self.json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        if not isinstance(data, list):
            raise ValueError("JSON 必须是一个列表")
        self.categories = []
        for cat in data:
            if not isinstance(cat, list) or len(cat) != 3:
                raise ValueError("JSON 列表元素必须是一个长度为 3 的列表")
            cid, cname, filters = cat
            if not isinstance(cid, str) or not isinstance(cname, str) or not isinstance(filters, list):
                raise ValueError("JSON 列表元素必须是字符串和列表")
            if not all(isinstance(f, list) and len(f) == 3 for f in filters):
                raise ValueError("JSON 列表元素的 filters 元素必须是一个长度为 3 的列表")
            category_data = CategoryData(cid, cname, [])
            for f in filters:
                fid, fname, fcontent = f
                if not isinstance(fid, str) or not isinstance(fname, str) or not isinstance(fcontent, str):
                    raise ValueError("JSON 列表元素的 filters 元素必须是字符串")
                filter_data = FilterData(fid, fname, fcontent)
                category_data.add_filter(filter_data)
            self.categories.append(category_data)

        self._used_ids = set()
        for cat in self.categories:
            self._used_ids.add(cat.cid)
            for f in cat.filters:
                self._used_ids.add(f.fid)

        self.print_tree()

    def save_json(self, json_path: str = None):
        if json_path is not None:
            self.json_path = json_path
        if self.json_path is None:
            raise ValueError("JSON 文件路径不能为空")
        data = []
        for cat in self.categories:
            filters = []
            for f in cat.filters:
                filters.append([f.fid, f.name, f.content])
            data.append([cat.cid, cat.name, filters])
        with open(self.json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def generate_unique_id(self, length: int = 8) -> str:
        chars = string.ascii_lowercase + string.digits
        while True:
            new_id = ''.join(random.choices(chars, k=length))
            if new_id not in self._used_ids:
                self._used_ids.add(new_id)
                return new_id

    def add_category(self, category_name: str) -> CategoryData:
        if not category_name:
            raise ValueError("类别名称不能为空")
        cid = self.generate_unique_id(8)
        category_data = CategoryData(cid, category_name, [])
        self.categories.append(category_data)
        self._used_ids.add(cid)
        return category_data

    def insert_category(self, category_name: str, next_category: CategoryData) -> CategoryData:
        if not category_name:
            raise ValueError("类别名称不能为空")
        if not next_category:
            raise ValueError("下一个类别不能为空")
        cid = self.generate_unique_id(8)
        category_data = CategoryData(cid, category_name, [])
        for i, cat in enumerate(self.categories):
            if cat.cid == next_category.cid:
                self.categories.insert(i, category_data)
                self._used_ids.add(cid)
                return category_data

    def remove_category(self, category: CategoryData) -> bool:
        for i, cat in enumerate(self.categories):
            if cat.cid == category.cid:
                self.categories.pop(i)
                self._used_ids.discard(category.cid)
                return True
        return False

    def rename_category(self, category: CategoryData, new_name: str) -> bool:
        for cat in self.categories:
            if cat.cid == category.cid:
                cat.name = new_name
                return True
        return False

    def add_filter(self, category: CategoryData, filter_name: str, content: str) -> FilterData:
        for cat in self.categories:
            if cat.cid == category.cid:
                fid = self.generate_unique_id(8)
                filter_data = FilterData(fid, filter_name, content)
                cat.add_filter(filter_data)
                self._used_ids.add(fid)
                return filter_data
        raise ValueError(f"类别不存在: {category.cid}")

    def insert_filter(self, category: CategoryData, filter_name: str, filter: FilterData) -> FilterData:
        for cat in self.categories:
            if cat.cid == category.cid:
                for i, f in enumerate(cat.filters):
                    if f.fid == filter.fid:
                        fid = self.generate_unique_id(8)
                        filter_data = FilterData(fid, filter_name, "")
                        cat.filters.insert(i, filter_data)
                        self._used_ids.add(fid)
                        return filter_data

    def remove_filter(self, category: CategoryData, filter: FilterData) -> bool:
        for cat in self.categories:
            if cat.cid == category.cid:
                for i, f in enumerate(cat.filters):
                    if f.fid == filter.fid:
                        cat.filters.pop(i)
                        self._used_ids.discard(filter.fid)
                        return True
        return False

    def rename_filter(self, category: CategoryData, filter: FilterData, new_name: str) -> bool:
        for cat in self.categories:
            if cat.cid == category.cid:
                for f in cat.filters:
                    if f.fid == filter.fid:
                        f.name = new_name
                        return True
        return False

    def get_categories(self) -> List[CategoryData]:
        return self.categories

    def get_filters(self, category: CategoryData) -> List[FilterData]:
        for cat in self.categories:
            if cat.cid == category.cid:
                return cat.filters
        return []

    def print_tree(self):
        for cat in self.categories:
            print(f"类别: {cat.name}")
            for f in cat.filters:
                print(f"  过滤器: {f.name}")
                print(f"    内容: {f.content}")
            print()

    def get_category_by_cid(self, cid: str):
        for cat in self.categories:
            if cat.cid == cid:
                return cat
        return None

    def get_filter_by_fid(self, fid: str):
        for cat in self.categories:
            for f in cat.filters:
                if f.fid == fid:
                    return f
        return None


# =========================== UI类 =========================== #

class LeftList:
    def __init__(self, root_frame: Frame, pos_x: int, pos_y: int, width: int, height: int, db: DataBase):
        self.root_frame = root_frame
        self.pos_x = pos_x
        self.pos_y = pos_y
        self.width = width
        self.height = height
        self.db = db
        self.custom_font = tkFont.Font(family="微软雅黑", size=10)
        self.lb = Listbox(self.root_frame, font=self.custom_font)
        self.lb.configure(selectmode=SINGLE)
        self.lb.place(x=self.pos_x, y=self.pos_y, width=self.width, height=self.height)
        self.categories: List[CategoryData] = []
        self.select_event_callback = None

        self.lb.bind("<<ListboxSelect>>", self.__on_select_event)
        self.lb.bind("<Button-3>", self.__on_right_click)

        self.load_data()

    def load_data(self):
        self.categories = []
        for cat in self.db.get_categories():
            self.categories.append(cat)
            self.lb.insert(END, cat.name)

    # 在最后位置前插入一个类别，并将焦点移到该位置
    def append_category(self, name: str):
        cat = self.db.add_category(name)
        self.categories.append(cat)
        self.lb.selection_clear(0, END)
        self.lb.insert(END, name)
        self.lb.select_set(END)
        self.lb.event_generate("<<ListboxSelect>>")

    # 在当前位置前插入一个类别, 并将焦点移到该位置
    def insert_category(self, name: str, index: int):
        if index < 0 or index > len(self.categories):
            return
        cat = self.db.insert_category(name, self.categories[index])
        self.categories.insert(index, cat)
        self.lb.selection_clear(0, END)
        self.lb.insert(index, name)
        self.lb.select_set(index)
        self.lb.event_generate("<<ListboxSelect>>")

    # 删除指定index的类别,并将焦点移到下一个位置，如果删除后没有类别，则将焦点移到末尾
    def remove_category(self, index: int):
        if index < 0 or index >= len(self.categories):
            return
        self.db.remove_category(self.categories[index])
        self.categories.pop(index)
        self.lb.delete(index)
        if len(self.categories) == 0:
            index = 0
        self.lb.selection_clear(0, END)
        self.lb.select_set(index-1 if index > 0 else index)
        self.lb.event_generate("<<ListboxSelect>>")

    def rename_category(self, index: int, new_name: str):
        if index < 0 or index >= len(self.categories):
            return
        if not new_name:
            showwarning("警告", "名称不能为空")
            return
        self.categories[index].name = new_name
        self.lb.delete(index)
        self.lb.insert(index, new_name)
        self.lb.select_set(index)

    def __on_select_event(self, event):
        if len(self.lb.curselection()) == 0:
            return
        index = self.lb.curselection()[0]
        if self.select_event_callback is not None:
            # 判断是否是函数
            if callable(self.select_event_callback):
                self.select_event_callback(self.categories[index])

    # 注册ListboxSelect事件处理回调函数
    def register_select_event_callback(self, func):
        self.select_event_callback = func

    # 右击鼠标事件处理函数
    def __on_right_click(self, event):
        def menu_rename(c_index: int):
            new_name = askstring("重命名", "请输入新的名称", initialvalue=self.categories[c_index].name)
            if new_name is not None:
                self.rename_category(c_index, new_name)

        def menu_add_category():
            new_name = askstring("添加类别", "请输入类别名称")
            if new_name is not None:
                self.append_category(new_name)

        def memu_insert_category(c_index: int):
            new_name = askstring("添加类别", "请输入类别名称")
            if new_name is not None:
                self.insert_category(new_name, c_index)

        def menu_remove_category(c_index: int):
            if askyesno("删除类别", f"是否删除类别: {self.categories[c_index].name}"):
                self.remove_category(c_index)

        # 判断当前listbox是否为空
        list_len = len(self.lb.get(0, END))
        if list_len == 0:
            # 弹出菜单：添加类别
            menu = Menu(self.root_frame, tearoff=0)
            menu.add_command(label="添加类别", command=lambda: menu_add_category())
            menu.post(event.x_root, event.y_root)
        else:
            # 判断当前鼠标位置是否在listbox某个item中
            item_index = self.lb.nearest(event.y)
            if item_index < 0 or item_index >= len(self.categories):
                # 弹出菜单：添加类别
                menu = Menu(self.root_frame, tearoff=0)
                menu.add_command(label="添加类别", command=lambda: menu_add_category())
                menu.post(event.x_root, event.y_root)
            else:
                # 移动焦点到当前点击位置，旧的焦点位置将被清除
                self.lb.selection_clear(0, END)
                self.lb.select_set(item_index)
                self.lb.event_generate("<<ListboxSelect>>")

                # 弹出菜单：重命名，添加类别，删除类别
                menu = Menu(self.root_frame, tearoff=0)
                menu.add_command(label="重命名", command=lambda: menu_rename(item_index))
                menu.add_command(label="插入新类别", command=lambda: memu_insert_category(item_index))
                menu.add_command(label="添加类别", command=lambda: menu_add_category())
                menu.add_command(label="删除类别", command=lambda: menu_remove_category(item_index))
                menu.post(event.x_root, event.y_root)


class RightList:
    class RightItem:
        def __init__(self, root_frame: Frame, width: int, height: int, filter_data: FilterData,
                     category_data: CategoryData, right_click_callback, delete_callback, or_and_callback):
            self.root_frame = root_frame
            self.width = width
            self.height = height
            self.filter: FilterData = filter_data
            self.category: CategoryData = category_data
            self.custom_font = tkFont.Font(family="微软雅黑", size=10)
            self.frame = Frame(root_frame, bg="#F0FFFF", relief="raised", bd=1, width=self.width, height=self.height)
            # self.frame.pack(padx=0, pady=0, fill="x")
            self.right_click_callback = right_click_callback
            self.delete_callback = delete_callback
            self.or_and_callback = or_and_callback
            self.frame.bind("<Button-3>", self.__on_frame_right_click)

            # 在每个item中添加控件
            # 复制按钮
            copy_btn_width = 20
            copy_btn_height = 20
            copy_btn_x = 10
            copy_btn_y = (self.height - copy_btn_height) // 2
            self.copy_btn = Button(self.frame, text="📋", font=self.custom_font, command=lambda: self.__on_copy())
            self.copy_btn.place(x=copy_btn_x, y=copy_btn_y, width=copy_btn_width, height=copy_btn_height)

            # 名称文本框
            name_entry_width = 100
            name_entry_height = 20
            name_entry_x = copy_btn_x + copy_btn_width + 10
            name_entry_y = (self.height - name_entry_height) // 2
            self.var_name = StringVar()
            self.var_name.set(self.filter.name)
            self.var_name.trace_add("write", lambda name, index, mode: self.__on_name_change())
            self.name_entry = Entry(self.frame, font=self.custom_font, textvariable=self.var_name)
            self.name_entry.place(x=name_entry_x, y=name_entry_y, width=name_entry_width, height=name_entry_height)

            # 内容文本框
            content_entry_width = 180
            content_entry_height = 20
            content_entry_x = name_entry_x + name_entry_width + 10
            content_entry_y = (self.height - content_entry_height) // 2
            self.var_content = StringVar()
            self.var_content.set(self.filter.content)
            self.var_content.trace_add("write", lambda name, index, mode: self.__on_content_change())
            self.content_entry = Entry(self.frame, font=self.custom_font, textvariable=self.var_content)
            self.content_entry.place(x=content_entry_x, y=content_entry_y, width=content_entry_width,
                                     height=content_entry_height)

            # |按钮
            or_btn_width = 20
            or_btn_height = 20
            or_btn_x = content_entry_x + content_entry_width + 10
            or_btn_y = (self.height - or_btn_height) // 2
            self.or_btn = Button(self.frame, text="|", font=self.custom_font, command=lambda: self.__on_or_and("or"))
            self.or_btn.place(x=or_btn_x, y=or_btn_y, width=or_btn_width, height=or_btn_height)

            # &按钮
            and_btn_width = 20
            and_btn_height = 20
            and_btn_x = or_btn_x + or_btn_width + 10
            and_btn_y = (self.height - and_btn_height) // 2
            self.and_btn = Button(self.frame, text="&", font=self.custom_font, command=lambda: self.__on_or_and("and"))
            self.and_btn.place(x=and_btn_x, y=and_btn_y, width=and_btn_width, height=and_btn_height)

            # 删除按钮
            delete_btn_width = 20
            delete_btn_height = 20
            delete_btn_x = and_btn_x + and_btn_width + 10
            delete_btn_y = (self.height - delete_btn_height) // 2
            self.delete_btn = Button(self.frame, text="❌", font=self.custom_font, command=lambda: self.__on_delete())
            self.delete_btn.place(x=delete_btn_x, y=delete_btn_y, width=delete_btn_width, height=delete_btn_height)

        def destroy_item(self):
            self.frame.destroy()

        def __on_copy(self):
            self.root_frame.clipboard_clear()
            self.root_frame.clipboard_append(self.filter.content)

        def __on_or_and(self, mode: str):
            if mode == "or" or mode == "and":
                if self.or_and_callback is not None:
                    # 判断是否是函数
                    if callable(self.or_and_callback):
                        self.or_and_callback(mode, self.filter)
            else:
                raise ValueError(f"不支持的操作: {mode}")

        def __on_delete(self):
            if askyesno("删除filter", f"是否删除filter: >{self.filter.name}<？"):
                if self.delete_callback is not None:
                    # 判断是否是函数
                    if callable(self.delete_callback):
                        self.delete_callback(self)

        def __on_name_change(self):
            self.filter.name = self.var_name.get()

        def __on_content_change(self):
            self.filter.content = self.var_content.get()

        def __on_frame_right_click(self, event):
            if self.right_click_callback is not None:
                # 判断是否是函数
                if callable(self.right_click_callback):
                    self.right_click_callback(event, self.filter)

    def __init__(self, root_frame: Frame, pos_x: int, pos_y: int, width: int, height: int, db: DataBase, or_and_callback):
        self.root_frame = root_frame
        self.pos_x = pos_x
        self.pos_y = pos_y
        self.width = width - 12
        self.height = height
        self.db = db
        self.category = None
        self.or_and_callback = or_and_callback

        self.canvas = Canvas(self.root_frame, bd=0)
        self.canvas.place(x=self.pos_x, y=self.pos_y, width=self.width, height=self.height)
        self.scroll_frame = Frame(self.canvas)
        # 给scroll_frame添加右击菜单
        self.canvas.bind("<Button-3>", self.__on_scroll_frame_right_click)
        self.canvas.create_window((0, 0), window=self.scroll_frame, anchor="nw")

        # 画布上添加滚动条
        self.vsb = Scrollbar(self.root_frame, orient="vertical", command=self.canvas.yview)
        self.vsb.place(x=self.pos_x + self.width, y=self.pos_y, width=12, height=self.height)
        self.canvas.configure(yscrollcommand=self.vsb.set)

        # 绑定鼠标滚轮事件
        self.canvas.bind("<Enter>", self._bind_to_mousewheel)
        self.canvas.bind("<Leave>", self._unbind_from_mousewheel)

        self.item_width = self.width
        self.item_height = self.height // 15
        self.item_table: List[RightList.RightItem] = []

    def _bind_to_mousewheel(self, event):
        self.canvas.bind_all("<MouseWheel>", self.on_mouse_wheel)

    def _unbind_from_mousewheel(self, event):
        self.canvas.unbind_all("<MouseWheel>")

    def on_mouse_wheel(self, event):
        if self.category is None:
            return  # 未设置分类时直接返回
        total_height = len(self.category.filters) * self.item_height
        if total_height <= self.height:
            return  # 内容不足时直接返回

        # 计算滚动方向（向上为负，向下为正）
        direction = -1 if event.delta > 0 else 1
        # 设置滚动步长（每次滚动4个单位）
        step = 2 * direction
        self.canvas.yview_scroll(step, "units")

    def set_category(self, category: CategoryData):
        self.clear_category()
        self.category = category
        self.item_table = []

        total_height = len(self.category.filters) * self.item_height
        self.scroll_frame.configure(height=total_height)

        for item in self.category.filters:
            item_obj = RightList.RightItem(self.scroll_frame, self.item_width, self.item_height, item, self.category,
                                           self.__on_item_frame_right_click,
                                           self.__on_delete_callback,
                                           self.__on_or_and_callback)
            item_obj.frame.pack(padx=0, pady=0, fill="x")
            self.item_table.append(item_obj)

        self.scroll_frame.update_idletasks()
        self.canvas.configure(scrollregion=(0, 0, self.item_width, total_height))

        if total_height > self.height:  # 仅当内容高度超过视图高度时启用滚动
            # 设置实际滚动区域为内容高度
            self.canvas.configure(scrollregion=(0, 0, self.item_width, total_height))
            # 启用滚动条
            self.canvas.configure(yscrollcommand=self.vsb.set)
            self.vsb.configure(command=self.canvas.yview)
        else:
            # 内容不足时，禁用滚动并设置滚动区域为视图大小
            self.canvas.configure(scrollregion=(0, 0, self.item_width, self.height))
            # 禁用滚动条
            self.vsb.set(0, 1)  # 固定滚动条位置
            self.canvas.configure(yscrollcommand=None)

    def update_scroll(self):
        total_height = len(self.category.filters) * self.item_height
        self.scroll_frame.configure(height=total_height)
        self.scroll_frame.update_idletasks()
        self.canvas.configure(scrollregion=(0, 0, self.item_width, total_height))

        if total_height > self.height:  # 仅当内容高度超过视图高度时启用滚动
            # 设置实际滚动区域为内容高度
            self.canvas.configure(scrollregion=(0, 0, self.item_width, total_height))
            # 启用滚动条
            self.canvas.configure(yscrollcommand=self.vsb.set)
            self.vsb.configure(command=self.canvas.yview)
        else:
            # 内容不足时，禁用滚动并设置滚动区域为视图大小
            self.canvas.configure(scrollregion=(0, 0, self.item_width, self.height))
            # 禁用滚动条
            self.vsb.set(0, 1)  # 固定滚动条位置
            self.canvas.configure(yscrollcommand=None)

    def update_ui_add_filter(self):
        filter = self.db.add_filter(self.category, "", "")

        item_obj = RightList.RightItem(self.scroll_frame, self.item_width, self.item_height, filter, self.category,
                                       self.__on_item_frame_right_click,
                                       self.__on_delete_callback,
                                       self.__on_or_and_callback)
        item_obj.frame.pack(padx=0, pady=0, fill="x")
        self.item_table.append(item_obj)

        self.update_scroll()

    def update_ui_insert_filter(self, next_filter: FilterData):
        filter = self.db.insert_filter(self.category, "", next_filter)
        index = self.category.filters.index(next_filter)
        # 查找next_filter对应的RightItem
        next_item = None
        for item in self.item_table:
            if item.filter == next_filter:
                next_item = item
                break

        item_obj = RightList.RightItem(self.scroll_frame, self.item_width, self.item_height, filter, self.category,
                                       self.__on_item_frame_right_click,
                                       self.__on_delete_callback,
                                       self.__on_or_and_callback)
        self.item_table.insert(index, item_obj)
        if next_item is not None:
            item_obj.frame.pack(padx=0, pady=0, fill="x", before=next_item.frame)

        self.update_scroll()

    def clear_category(self):
        for item in self.item_table:
            item.destroy_item()
        self.category = None
        self.item_table = []

    def __on_scroll_frame_right_click(self, event):
        if self.category is None:
            return  # 未设置分类时直接返回
        print("右击菜单")

        # 弹出菜单：添加过滤器
        def menu_add_filter():
            self.update_ui_add_filter()

        menu = Menu(self.root_frame, tearoff=0)
        menu.add_command(label="添加过滤器", command=lambda: menu_add_filter())
        menu.post(event.x_root, event.y_root)

    def __on_item_frame_right_click(self, event, filter: FilterData):
        # 弹出菜单：向上插入过滤器
        def menu_insert_filter():
            self.update_ui_insert_filter(filter)

        menu = Menu(self.root_frame, tearoff=0)
        menu.add_command(label="向上插入过滤器", command=lambda: menu_insert_filter())
        menu.post(event.x_root, event.y_root)

    def __on_delete_callback(self, right_item: RightItem):
        self.db.remove_filter(self.category, right_item.filter)
        right_item.frame.destroy()
        self.update_scroll()

    def __on_or_and_callback(self, mode: str, filter: FilterData):
        self.or_and_callback(mode, filter.content)


class EToolUI(Tk):
    def __init__(self, json_path: str = None):
        super().__init__()
        self.data_base = DataBase(json_path)
        self.current_category: CategoryData = None
        self.custom_font = tkFont.Font(family="微软雅黑", size=10)

        self.__win()
        self.menubar = self.__init_menu()

        self.output_text = self.__init_output_text()
        self.copy_output_text_btn = self.__init_copy_output_text_btn()
        self.clear_output_text_btn = self.__init_clear_output_text_btn()

        self.left_list = self.__init_left_list()
        self.right_list = self.__init_right_list()

        self.left_list.register_select_event_callback(self.__left_list_select_event)
        self.protocol("WM_DELETE_WINDOW", self.__on_closing)

    def __win(self):
        self.title("FilterHelper")
        # 设置窗口大小、居中
        width = 600
        height = 540
        screenwidth = self.winfo_screenwidth()
        screenheight = self.winfo_screenheight()
        geometry = '%dx%d+%d+%d' % (width, height, (screenwidth - width) / 2, (screenheight - height) / 2)
        self.geometry(geometry)
        self.resizable(width=False, height=False)

    def __on_closing(self):
        # 自定义关闭逻辑
        if askyesno("退出", "你确定要退出吗？退出前注意保存修改"):
            self.destroy()  # 真正关闭窗口

    def save_config(self):
        print("保存配置")
        self.data_base.save_json()

    def __init_menu(self):
        menubar = Menu(self, tearoff=False)
        menubar.add_command(label="📁保存", command=self.save_config)
        self.config(menu=menubar)
        return menubar

    def __init_output_text(self):
        text = Text(self, font=self.custom_font)
        text.place(x=154, y=460, width=337, height=70)
        return text

    def __init_copy_output_text_btn(self):
        def copy_output_text():
            output_text = self.output_text.get("1.0", END)
            self.clipboard_clear()
            self.clipboard_append(output_text)
            print("已复制输出")

        btn = Button(self, text="拷贝", font=self.custom_font, command=copy_output_text)
        btn.place(x=510, y=485, width=79, height=20)
        return btn

    def __init_clear_output_text_btn(self):
        def clear_output_text():
            self.output_text.delete("1.0", END)
            print("已清空输出")

        btn = Button(self, text="清空", font=self.custom_font, command=clear_output_text)
        btn.place(x=510, y=510, width=79, height=20)
        return btn

    def __init_left_list(self):
        return LeftList(root_frame=self, pos_x=6, pos_y=0, width=140, height=530, db=self.data_base)

    def __init_right_list(self):
        # ========== 右侧工作区（指定区域）==========
        right_panel_pos_x = 154
        right_panel_pos_y = 0
        right_panel_width = 440
        right_panel_height = 450

        return RightList(self, right_panel_pos_x, right_panel_pos_y, right_panel_width, right_panel_height,
                         self.data_base, self._or_and_callback)

    def __left_list_select_event(self, category: CategoryData):
        # 切换分类
        self.current_category = category
        self.right_list.set_category(category)

    def _or_and_callback(self, mode: str, content: str):
        if content.isspace():
            return  # 空白内容不处理
        out_text = ""
        text_str = self.output_text.get("1.0", END)
        space_str = text_str.isspace()
        if mode == "or":
            if space_str:
                out_text = content
            else:
                out_text = f"{text_str} || {content}"
        elif mode == "and":
            if space_str:
                out_text = content
            else:
                out_text = f"({text_str}) && ({content})"
        # 删除out_text的换行符
        out_text = out_text.replace('\r\n', '').replace('\n', '').replace('\r', '')
        self.output_text.delete("1.0", END)
        self.output_text.insert("1.0", out_text)


if __name__ == '__main__':
    etool_ui = EToolUI("FilterHelper.json")
    etool_ui.mainloop()
