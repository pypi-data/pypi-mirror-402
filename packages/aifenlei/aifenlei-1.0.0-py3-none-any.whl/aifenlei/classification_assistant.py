#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 分类选择辅助程序

import sys

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import pandas as pd
import json
import os
import threading
import requests
import time
from datetime import datetime
import tksheet


def SETTING_style_UI(popup=None):
    bg_color = "#2B313F"
    frame_color = "#5a6373"
    button_color = "#2B313F"
    text_color = "#eeedef"
    highlight_color = "#3a414d"
    border_color = "#3a414d"
    
    if popup:
        popup.configure(bg=bg_color, highlightbackground=bg_color, highlightcolor=bg_color, 
                      highlightthickness=0, bd=0)
    
    style = ttk.Style()
    style.theme_use("clam")
    
    style.configure("Main.TFrame", background=bg_color, borderwidth=1, relief="flat")
    style.configure("Tool.TButton", background=button_color, foreground=text_color, 
                  font=("微软雅黑", 10, "bold"), padding=4, borderwidth=1, relief="flat")
    style.map("Tool.TButton", background=[("active", frame_color)])
    style.configure("Tool.TLabel", background=bg_color, foreground=text_color, borderwidth=0)
    style.configure("Tool.TEntry", background=frame_color, foreground=text_color, 
                  borderwidth=1, fieldbackground=frame_color, relief="flat")
    style.configure("TLabelframe", background=bg_color, foreground=text_color, 
                  borderwidth=1, relief="flat")
    style.configure("TLabelframe.Label", background=bg_color, foreground=text_color, 
                  font=("微软雅黑", 10, "bold"))
    
    return bg_color, frame_color, button_color, text_color, highlight_color


class LLM_Functions:
    def __init__(self):
        self.cache = {}
    
    def call_api(self, api_key, content, selected_model, model_config, response_format=None):
        if not api_key:
            raise ValueError("API Key 不能为空")
        
        url = model_config.get("url", "")
        model = model_config.get("model", "")
        
        headers = {
            "Content-Type": "application/json; charset=utf-8"
        }
        
        data = {
            "model": model,
            "messages": [
                {"role": "system", "content": model_config.get("system_prompt", "")},
                {"role": "user", "content": content}
            ],
            "temperature": model_config.get("temperature", 0.3),
            "max_tokens": model_config.get("max_tokens", 2000)
        }
        
        if response_format:
            data["response_format"] = response_format
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                headers["Authorization"] = f"Bearer {api_key}"
                response = requests.post(
                    url,
                    headers=headers,
                    json=data,
                    timeout=60
                )
                response.raise_for_status()
                return response.json()
            except requests.exceptions.RequestException as e:
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                else:
                    error_msg = str(e)
                    if "401" in error_msg or "Unauthorized" in error_msg:
                        error_msg += "\n\n提示：请检查API Key是否正确。\n对于百度千帆API，请确保使用正确的Access Token。"
                    raise Exception(f"API调用失败: {error_msg}")


class ClassificationAssistant:
    def __init__(self, root):
        self.root = root
        self.root.title("分类选择辅助程序")
        self.root.geometry("1400x800")
        
        self.bg_color, self.frame_color, self.button_color, self.text_color, self.highlight_color = SETTING_style_UI(self.root)
        self.root.configure(bg=self.bg_color)
        
        self.llm = LLM_Functions()
        self.df = None
        self.current_step = 0
        self.selected_values = {"B": None, "C": None, "D": None}
        self.current_unique_values = []
        self.recommendation = None
        self.mode = "manual"
        
        self.config_file = "app_config.json"
        self.app_config = self._load_app_config()
        
        self.user_input_file = "user_input_history.json"
        self.saved_user_input = self._load_user_input()
        
        self.create_ui()
        self.load_data()
    
    def _load_user_input(self):
        if os.path.exists(self.user_input_file):
            try:
                with open(self.user_input_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                return None
        return None
    
    def _load_app_config(self):
        default_config = {
            "api_url": "",
            "api_key": "",
            "api_type": "openai",
            "column_b": "一级分类",
            "column_c": "二级分类",
            "column_d": "三级分类",
            "file_path": "data.xlsx",
            "parquet_path": "data.parquet"
        }
        
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    default_config.update(config)
            except Exception as e:
                pass
        
        return default_config
    
    def _save_app_config(self, config):
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            self.app_config = config
            self.log("配置已保存", "success")
        except Exception as e:
            self.log(f"保存配置失败: {str(e)}", "error")
    
    def _save_user_input(self):
        try:
            user_input = self.user_prompt.get("1.0", tk.END).strip()
            data = {
                "user_input": user_input,
                "timestamp": datetime.now().isoformat()
            }
            with open(self.user_input_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.log(f"保存用户输入失败: {str(e)}", "error")
    
    def create_ui(self):
        title_frame = tk.Frame(self.root, bg=self.bg_color)
        title_frame.pack(fill=tk.X, padx=10, pady=(10, 5))
        
        title_label = tk.Label(title_frame, 
                           text="分类选择辅助工具 V1.0",
                           bg=self.bg_color, 
                           fg=self.text_color, 
                           font=("微软雅黑", 16, "bold"))
        title_label.pack()
        
        main_frame = tk.Frame(self.root, bg=self.bg_color)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        paned_window = tk.PanedWindow(main_frame, orient=tk.HORIZONTAL, bg=self.bg_color, 
                                      bd=0, sashwidth=4, sashrelief=tk.FLAT)
        paned_window.pack(fill=tk.BOTH, expand=True)
        
        left_frame = tk.Frame(paned_window, bg=self.bg_color)
        paned_window.add(left_frame, width=600)
        
        right_frame = tk.Frame(paned_window, bg=self.bg_color)
        paned_window.add(right_frame, width=800)
        
        self.create_left_panel(left_frame)
        self.create_right_panel(right_frame)
    
    def create_left_panel(self, parent):
        system_frame = tk.LabelFrame(parent, text="系统提示词", font=("微软雅黑", 11, "bold"),
                                   bg=self.bg_color, fg=self.text_color, bd=1, relief=tk.FLAT)
        system_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        system_header = tk.Frame(system_frame, bg=self.bg_color)
        system_header.pack(fill=tk.X, padx=5, pady=(5, 0))
        
        self.system_prompt = scrolledtext.ScrolledText(system_frame, wrap=tk.WORD, height=6,
                                                     bg=self.frame_color, fg=self.text_color,
                                                     font=("微软雅黑", 10), bd=0)
        self.system_prompt.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.system_prompt.insert("1.0", self._get_default_system_prompt())
        
        restore_system_btn = tk.Button(system_header, text="恢复默认", command=self.restore_system_prompt,
                                    bg=self.button_color, fg=self.text_color, font=("微软雅黑", 9),
                                    relief=tk.FLAT, padx=10, pady=3)
        restore_system_btn.pack(side=tk.RIGHT)
        
        user_frame = tk.LabelFrame(parent, text="用户提示词", font=("微软雅黑", 11, "bold"),
                                 bg=self.bg_color, fg=self.text_color, bd=1, relief=tk.FLAT)
        user_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        self.user_prompt = scrolledtext.ScrolledText(user_frame, wrap=tk.WORD, height=6,
                                                   bg=self.frame_color, fg=self.text_color,
                                                   font=("微软雅黑", 10), bd=0)
        self.user_prompt.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        if self.saved_user_input and "user_input" in self.saved_user_input:
            self.user_prompt.insert("1.0", self.saved_user_input["user_input"])
        else:
            self.user_prompt.insert("1.0", self._get_default_user_prompt())
        
        options_frame = tk.LabelFrame(parent, text="当前可选分类（自动生成）", font=("微软雅黑", 11, "bold"),
                                  bg=self.bg_color, fg=self.highlight_color, bd=1, relief=tk.FLAT)
        options_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        self.options_text = scrolledtext.ScrolledText(options_frame, wrap=tk.WORD, height=6,
                                                  bg=self.frame_color, fg=self.text_color,
                                                  font=("Consolas", 9), bd=0)
        self.options_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        button_frame = tk.Frame(parent, bg=self.bg_color)
        button_frame.pack(fill=tk.X, pady=(0, 10))
        
        open_file_btn = tk.Button(button_frame, text="📁 打开文件", command=self.open_file_dialog,
                               bg=self.button_color, fg=self.text_color, font=("微软雅黑", 11, "bold"),
                               relief=tk.FLAT, padx=15, pady=8)
        open_file_btn.pack(side=tk.LEFT, padx=5)
        
        self.send_button = tk.Button(button_frame, text="发送并获取推荐", command=self.send_request,
                                   bg=self.button_color, fg=self.text_color, font=("微软雅黑", 11, "bold"),
                                   relief=tk.FLAT, padx=20, pady=8)
        self.send_button.pack(side=tk.LEFT, padx=5)
        
        self.prev_button = tk.Button(button_frame, text="上一步", command=self.prev_step,
                                   bg=self.button_color, fg=self.text_color, font=("微软雅黑", 11, "bold"),
                                   relief=tk.FLAT, padx=20, pady=8, state=tk.DISABLED)
        self.prev_button.pack(side=tk.LEFT, padx=5)
        
        self.next_button = tk.Button(button_frame, text="下一步", command=self.next_step,
                                   bg=self.button_color, fg=self.text_color, font=("微软雅黑", 11, "bold"),
                                   relief=tk.FLAT, padx=20, pady=8, state=tk.DISABLED)
        self.next_button.pack(side=tk.LEFT, padx=5)
        
        settings_btn = tk.Button(button_frame, text="⚙ 设置", command=self.open_settings,
                               bg=self.button_color, fg=self.text_color, font=("微软雅黑", 11, "bold"),
                               relief=tk.FLAT, padx=15, pady=8)
        settings_btn.pack(side=tk.LEFT, padx=5)
        
        log_frame = tk.LabelFrame(parent, text="操作日志", font=("微软雅黑", 11, "bold"),
                                bg=self.bg_color, fg=self.text_color, bd=1, relief=tk.FLAT)
        log_frame.pack(fill=tk.BOTH, expand=True)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD, height=8,
                                                bg=self.frame_color, fg=self.text_color,
                                                font=("Consolas", 9), bd=0)
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    
    def create_right_panel(self, parent):
        selection_frame = tk.LabelFrame(parent, text="分类选择", font=("微软雅黑", 11, "bold"),
                                       bg=self.bg_color, fg=self.text_color, bd=1, relief=tk.FLAT)
        selection_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        self.step_label = tk.Label(selection_frame, text="当前步骤: 请选择一级分类 (B列)",
                                 font=("微软雅黑", 12, "bold"), bg=self.bg_color, fg=self.highlight_color)
        self.step_label.pack(pady=10)
        
        list_frame = tk.Frame(selection_frame, bg=self.bg_color)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        scrollbar = tk.Scrollbar(list_frame, bg=self.bg_color, troughcolor=self.frame_color)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.selection_listbox = tk.Listbox(list_frame, bg=self.frame_color, fg=self.text_color,
                                          font=("微软雅黑", 11), selectmode=tk.SINGLE,
                                          yscrollcommand=scrollbar.set, bd=0, highlightthickness=0)
        self.selection_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.selection_listbox.yview)
        
        self.selection_listbox.bind('<<ListboxSelect>>', self.on_selection_change)
        
        reason_frame = tk.LabelFrame(parent, text="推荐原因", font=("微软雅黑", 11, "bold"),
                                   bg=self.bg_color, fg=self.text_color, bd=1, relief=tk.FLAT)
        reason_frame.pack(fill=tk.BOTH, expand=True)
        
        self.reason_text = scrolledtext.ScrolledText(reason_frame, wrap=tk.WORD, height=8,
                                                   bg=self.frame_color, fg=self.text_color,
                                                   font=("微软雅黑", 10), bd=0)
        self.reason_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.result_frame = tk.LabelFrame(parent, text="最终结果", font=("微软雅黑", 11, "bold"),
                                       bg=self.bg_color, fg=self.text_color, bd=1, relief=tk.FLAT)
        
        self.result_text = scrolledtext.ScrolledText(self.result_frame, wrap=tk.WORD, height=15,
                                                   bg=self.frame_color, fg=self.text_color,
                                                   font=("微软雅黑", 11), bd=0)
        self.result_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    
    def _get_default_system_prompt(self):
        return """你是一个专业的分类选择助手。你的任务是根据用户的需求和提供的选项列表，推荐最合适的分类。

请按照以下要求：
1. 仔细分析用户的需求描述
2. 查看提供的所有可选分类
3. 基于需求分析，推荐最合适的分类
4. 提供推荐理由，说明为什么选择这个分类

重要：你只能返回JSON格式，不要返回任何其他内容！

输出格式必须是严格的JSON格式（不要包含任何其他文字，字段名称必须和下面的示例保持完全一致）：
{
  "recommendation": "推荐的分类名称（必须从可选列表中选择）",
  "reason": "推荐理由的详细说明"
}"""
    
    def restore_system_prompt(self):
        self.system_prompt.delete("1.0", tk.END)
        self.system_prompt.insert("1.0", self._get_default_system_prompt())
        self.log("已恢复默认系统提示词", "system")
    
    def open_settings(self):
        self._open_settings_window()
    
    def _open_settings_window(self):
        settings_window = tk.Toplevel(self.root)
        settings_window.title("设置")
        settings_window.geometry("500x480")
        settings_window.configure(bg=self.bg_color)
        settings_window.transient(self.root)
        settings_window.grab_set()
        
        main_frame = tk.Frame(settings_window, bg=self.bg_color, padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        tk.Label(main_frame, text="API设置", font=("微软雅黑", 12, "bold"),
                bg=self.bg_color, fg=self.text_color).pack(anchor=tk.W, pady=(0, 10))
        
        api_frame = tk.Frame(main_frame, bg=self.bg_color)
        api_frame.pack(fill=tk.X, pady=(0, 20))
        
        tk.Label(api_frame, text="API URL:", bg=self.bg_color, fg=self.text_color,
                font=("微软雅黑", 10)).grid(row=0, column=0, sticky=tk.W, pady=5)
        api_url_var = tk.StringVar(value=self.app_config.get("api_url", ""))
        tk.Entry(api_frame, textvariable=api_url_var, font=("微软雅黑", 10),
                bg=self.frame_color, fg=self.text_color, relief=tk.FLAT).grid(
                row=0, column=1, sticky=tk.EW, padx=10, pady=5)
        
        tk.Label(api_frame, text="Model:", bg=self.bg_color, fg=self.text_color,
                font=("微软雅黑", 10)).grid(row=1, column=0, sticky=tk.W, pady=5)
        api_type_var = tk.StringVar(value=self.app_config.get("api_type", "openai"))
        tk.Entry(api_frame, textvariable=api_type_var, font=("微软雅黑", 10),
                bg=self.frame_color, fg=self.text_color, relief=tk.FLAT).grid(
                row=1, column=1, sticky=tk.EW, padx=10, pady=5)
        
        tk.Label(api_frame, text="API Key:", bg=self.bg_color, fg=self.text_color,
                font=("微软雅黑", 10)).grid(row=2, column=0, sticky=tk.W, pady=5)
        api_key_var = tk.StringVar(value=self.app_config.get("api_key", ""))
        tk.Entry(api_frame, textvariable=api_key_var, font=("微软雅黑", 10),
                bg=self.frame_color, fg=self.text_color, relief=tk.FLAT).grid(
                row=2, column=1, sticky=tk.EW, padx=10, pady=5)
        
        api_frame.columnconfigure(1, weight=1)
        
        tk.Label(main_frame, text="列名设置", font=("微软雅黑", 12, "bold"),
                bg=self.bg_color, fg=self.text_color).pack(anchor=tk.W, pady=(0, 10))
        
        column_frame = tk.Frame(main_frame, bg=self.bg_color)
        column_frame.pack(fill=tk.X, pady=(0, 20))
        
        if self.df is not None:
            columns = self.df.columns.tolist()
        else:
            columns = []
        
        tk.Label(column_frame, text="一级分类列:", bg=self.bg_color, fg=self.text_color,
                font=("微软雅黑", 10)).grid(row=0, column=0, sticky=tk.W, pady=5)
        column_b_var = tk.StringVar(value=self.app_config.get("column_b", "一级分类"))
        column_b_combo = ttk.Combobox(column_frame, textvariable=column_b_var, values=columns,
                                    font=("微软雅黑", 10), state="readonly")
        column_b_combo.grid(row=0, column=1, sticky=tk.EW, padx=10, pady=5)
        
        tk.Label(column_frame, text="二级分类列:", bg=self.bg_color, fg=self.text_color,
                font=("微软雅黑", 10)).grid(row=1, column=0, sticky=tk.W, pady=5)
        column_c_var = tk.StringVar(value=self.app_config.get("column_c", "二级分类"))
        column_c_combo = ttk.Combobox(column_frame, textvariable=column_c_var, values=columns,
                                    font=("微软雅黑", 10), state="readonly")
        column_c_combo.grid(row=1, column=1, sticky=tk.EW, padx=10, pady=5)
        
        tk.Label(column_frame, text="三级分类列:", bg=self.bg_color, fg=self.text_color,
                font=("微软雅黑", 10)).grid(row=2, column=0, sticky=tk.W, pady=5)
        column_d_var = tk.StringVar(value=self.app_config.get("column_d", "三级分类"))
        column_d_combo = ttk.Combobox(column_frame, textvariable=column_d_var, values=columns,
                                    font=("微软雅黑", 10), state="readonly")
        column_d_combo.grid(row=2, column=1, sticky=tk.EW, padx=10, pady=5)
        
        column_frame.columnconfigure(1, weight=1)
        
        button_frame = tk.Frame(main_frame, bg=self.bg_color)
        button_frame.pack(fill=tk.X, pady=(20, 0))
        
        def save_settings():
            config = {
                "api_url": api_url_var.get(),
                "api_key": api_key_var.get(),
                "api_type": api_type_var.get(),
                "column_b": column_b_var.get(),
                "column_c": column_c_var.get(),
                "column_d": column_d_var.get(),
                "file_path": self.app_config.get("file_path", "data.xlsx"),
                "parquet_path": self.app_config.get("parquet_path", "data.parquet")
            }
            self._save_app_config(config)
            settings_window.destroy()
        
        def cancel_settings():
            settings_window.destroy()
        
        def reset_all_settings():
            if messagebox.askyesno("确认重置", "确定要重置所有设置吗？这将恢复默认配置并清除所有保存的设置。"):
                # 重置为默认配置
                default_config = {
                    "api_url": "",
                    "api_key": "",
                    "api_type": "openai",
                    "column_b": "一级分类",
                    "column_c": "二级分类",
                    "column_d": "三级分类",
                    "file_path": "data.xlsx",
                    "parquet_path": "data.parquet"
                }
                self._save_app_config(default_config)
                # 重新加载配置
                self.app_config = self._load_app_config()
                # 重新加载数据
                self.load_data()
                # 重置GUI状态
                self.reset()
                settings_window.destroy()
                self.log("所有设置已重置为默认值", "success")
        
        tk.Button(button_frame, text="重置所有", command=reset_all_settings,
                bg=self.button_color, fg=self.text_color, font=("微软雅黑", 11),
                relief=tk.FLAT, padx=20, pady=8).pack(side=tk.LEFT, padx=5)
        
        tk.Button(button_frame, text="保存", command=save_settings,
                bg=self.button_color, fg=self.text_color, font=("微软雅黑", 11, "bold"),
                relief=tk.FLAT, padx=20, pady=8).pack(side=tk.RIGHT, padx=5)
        
        tk.Button(button_frame, text="取消", command=cancel_settings,
                bg=self.button_color, fg=self.text_color, font=("微软雅黑", 11),
                relief=tk.FLAT, padx=20, pady=8).pack(side=tk.RIGHT, padx=5)
    
    def _get_default_user_prompt(self):
        return """请根据以下产品信息帮我选择最合适的分类：

产品信息：
生抽酱油_配料：_水、非转基因大豆、小麦粉、食用盐、白砂糖、谷氨酸钠、5'-呈味核苷酸二钠、苯甲酸钠、三氯蔗糖_净含量：_1升_保质期：_18个月_储存方法：_常温保存

可选分类列表：
[分类列表将自动填充]

请推荐最合适的分类并说明理由。"""
    
    def load_data(self):
        file_path = self.app_config.get("file_path", "data.xlsx")
        parquet_path = self.app_config.get("parquet_path", "data.parquet")
        
        if os.path.exists(parquet_path):
            try:
                self.df = pd.read_parquet(parquet_path)
                self.log(f"从Parquet文件 ({os.path.basename(parquet_path)}) 加载数据成功: {len(self.df)} 行, {len(self.df.columns)} 列", "success")
                self.log(f"列名: {', '.join(self.df.columns.tolist())}")
                
                self.prepare_step_0()
                return
            except Exception as e:
                self.log(f"从Parquet文件 ({os.path.basename(parquet_path)}) 加载失败: {str(e)}", "error")
        
        if not os.path.exists(file_path):
            self.log(f"数据文件不存在: {os.path.basename(file_path)}", "error")
            return
        
        try:
            self.df = pd.read_excel(file_path)
            self.log(f"从Excel文件 ({os.path.basename(file_path)}) 加载数据成功: {len(self.df)} 行, {len(self.df.columns)} 列", "success")
            self.log(f"正在转换为Parquet格式...")
            
            try:
                self.df.to_parquet(parquet_path, index=False)
                self.log(f"已保存为Parquet格式: {os.path.basename(parquet_path)}", "success")
            except Exception as e:
                self.log(f"保存Parquet文件失败: {str(e)}", "error")
            
            self.log(f"列名: {', '.join(self.df.columns.tolist())}")
            
            self.prepare_step_0()
            
        except Exception as e:
            self.log(f"加载数据失败: {str(e)}", "error")
    
    def prepare_step_0(self):
        self.current_step = 0
        column_b = self.app_config.get("column_b", "一级分类")
        self.step_label.config(text=f"当前步骤: 请选择一级分类 ({column_b}列)")
        
        unique_b = self.df[column_b].unique().tolist()
        self.current_unique_values = unique_b
        
        self.update_listbox(unique_b)
        self.update_options_display(unique_b, "一级分类")
        self.update_user_prompt_for_step(0, unique_b)
        
        self.prev_button.config(state=tk.DISABLED)
        self.next_button.config(state=tk.DISABLED)
        self.result_frame.pack_forget()
        
        self.log(f"步骤0: 准备选择一级分类，共 {len(unique_b)} 个选项")
    
    def prepare_step_1(self):
        self.current_step = 1
        column_c = self.app_config.get("column_c", "二级分类")
        self.step_label.config(text=f"当前步骤: 请选择二级分类 ({column_c}列)")
        
        selected_b = self.selected_values["B"]
        column_b = self.app_config.get("column_b", "一级分类")
        filtered_df = self.df[self.df[column_b] == selected_b]
        
        unique_c = filtered_df[column_c].unique().tolist()
        self.current_unique_values = unique_c
        
        self.update_listbox(unique_c)
        self.update_options_display(unique_c, "二级分类")
        self.update_user_prompt_for_step(1, unique_c, selected_b)
        
        self.prev_button.config(state=tk.NORMAL)
        self.next_button.config(state=tk.DISABLED)
        self.result_frame.pack_forget()
        
        self.log(f"步骤1: 准备选择二级分类，共 {len(unique_c)} 个选项")
    
    def prepare_step_2(self):
        self.current_step = 2
        column_d = self.app_config.get("column_d", "三级分类")
        self.step_label.config(text=f"当前步骤: 请选择三级分类 ({column_d}列)")
        
        selected_b = self.selected_values["B"]
        selected_c = self.selected_values["C"]
        column_b = self.app_config.get("column_b", "一级分类")
        column_c = self.app_config.get("column_c", "二级分类")
        filtered_df = self.df[(self.df[column_b] == selected_b) & 
                             (self.df[column_c] == selected_c)]
        
        unique_d = filtered_df[column_d].unique().tolist()
        self.current_unique_values = unique_d
        
        self.update_listbox(unique_d)
        self.update_options_display(unique_d, "三级分类")
        self.update_user_prompt_for_step(2, unique_d, selected_b, selected_c)
        
        self.prev_button.config(state=tk.NORMAL)
        self.next_button.config(state=tk.DISABLED)
        self.result_frame.pack_forget()
        
        self.log(f"步骤2: 准备选择三级分类，共 {len(unique_d)} 个选项")
    
    def update_listbox(self, items):
        self.selection_listbox.delete(0, tk.END)
        for item in items:
            self.selection_listbox.insert(tk.END, item)
    
    def update_options_display(self, items, category_name):
        items_str = "\n".join([f"{i+1}. {item}" for i, item in enumerate(items)])
        display_text = f"{category_name}选项列表（共 {len(items)} 个）：\n\n{items_str}"
        
        self.options_text.delete("1.0", tk.END)
        self.options_text.insert("1.0", display_text)
    
    def update_user_prompt_for_step(self, step, items, selected_b=None, selected_c=None):
        items_str = "\n".join([f"- {item}" for item in items])
        
        # Get current content to preserve user edits
        current_content = self.user_prompt.get("1.0", tk.END).strip()
        
        # Extract product information if it exists
        product_info = ""
        if "产品信息：" in current_content:
            parts = current_content.split("可选")
            if len(parts) > 0:
                product_part = parts[0]
                if "产品信息：" in product_part:
                    product_info = product_part.split("产品信息：")[1].strip()
        
        # Build new prompt preserving product info
        if step == 0:
            if product_info:
                prompt = f"""请根据以下产品信息帮我选择最合适的分类：

产品信息：
{product_info}

可选一级分类列表：
{items_str}

请推荐最合适的一级分类并说明理由。"""
            else:
                prompt = f"""可选一级分类列表：
{items_str}

请推荐最合适的一级分类并说明理由。"""
        elif step == 1:
            if product_info:
                prompt = f"""请根据以下产品信息帮我选择最合适的分类：

产品信息：
{product_info}

已选择的一级分类: {selected_b}

可选二级分类列表：
{items_str}

请推荐最合适的二级分类并说明理由。"""
            else:
                prompt = f"""已选择的一级分类: {selected_b}

可选二级分类列表：
{items_str}

请推荐最合适的二级分类并说明理由。"""
        elif step == 2:
            if product_info:
                prompt = f"""请根据以下产品信息帮我选择最合适的分类：

产品信息：
{product_info}

已选择的一级分类: {selected_b}
已选择的二级分类: {selected_c}

可选三级分类列表：
{items_str}

请推荐最合适的三级分类并说明理由。"""
            else:
                prompt = f"""已选择的一级分类: {selected_b}
已选择的二级分类: {selected_c}

可选三级分类列表：
{items_str}

请推荐最合适的三级分类并说明理由。"""
        
        self.user_prompt.delete("1.0", tk.END)
        self.user_prompt.insert("1.0", prompt)
    
    def open_file_dialog(self):
        file_path = filedialog.askopenfilename(
            title="选择Excel文件",
            filetypes=[("Excel文件", "*.xlsx"), ("所有文件", "*.*")]
        )
        
        if file_path:
            # 保存文件路径到配置
            self.app_config["file_path"] = file_path
            # 生成对应的parquet路径
            parquet_path = os.path.splitext(file_path)[0] + ".parquet"
            self.app_config["parquet_path"] = parquet_path
            # 保存配置
            self._save_app_config(self.app_config)
            # 重新加载数据
            self.load_data()
            self.log(f"已选择文件: {os.path.basename(file_path)}", "success")
    
    def on_selection_change(self, event):
        selection = self.selection_listbox.curselection()
        if selection:
            index = selection[0]
            selected = self.current_unique_values[index]
            
            if self.current_step == 0:
                self.selected_values["B"] = selected
                self.log(f"选择了一级分类: {selected}")
            elif self.current_step == 1:
                self.selected_values["C"] = selected
                self.log(f"选择了二级分类: {selected}")
            elif self.current_step == 2:
                self.selected_values["D"] = selected
                self.log(f"选择了三级分类: {selected}")
            
            self.next_button.config(state=tk.NORMAL)
    
    def send_request(self):
        self._save_user_input()
        self.manual_send_request()
    
    def manual_send_request(self):
        user_input = self.user_prompt.get("1.0", tk.END).strip()
        if not user_input:
            messagebox.showwarning("警告", "请输入用户需求")
            return
        
        self.log("正在调用LLM获取推荐...", "system")
        self.send_button.config(state=tk.DISABLED)
        
        def call_llm_thread():
            try:
                system_prompt = self.system_prompt.get("1.0", tk.END).strip()
                
                items_str = "\n".join([f"- {item}" for item in self.current_unique_values])
                full_user_prompt = user_input.replace("[分类列表将自动填充]", items_str)
                
                print(f"\n{'='*60}")
                print(f"发送给LLM的系统提示词：")
                print(f"{'='*60}")
                print(system_prompt)
                print(f"\n{'='*60}")
                print(f"发送给LLM的用户提示词：")
                print(f"{'='*60}")
                print(full_user_prompt)
                print(f"{'='*60}\n")
                
                # 从app_config构建model_config
                model_config = {
                    "api_key": self.app_config.get("api_key", ""),
                    "url": self.app_config.get("api_url", ""),
                    "model": self.app_config.get("api_type", "openai"),
                    "system_prompt": system_prompt
                }
                
                response = self.llm.call_api(
                    api_key=model_config["api_key"],
                    content=full_user_prompt,
                    selected_model=model_config["model"],
                    model_config=model_config,
                    response_format={"type": "json_object"}
                )
                
                print(f"\n{'='*60}")
                print(f"LLM返回的响应：")
                print(f"{'='*60}")
                print(json.dumps(response, ensure_ascii=False, indent=2))
                print(f"{'='*60}\n")
                
                self.root.after(0, lambda: self.process_llm_response(response))
                
            except Exception as e:
                self.root.after(0, lambda: self.log(f"LLM调用失败: {str(e)}", "error"))
                self.root.after(0, lambda: self.send_button.config(state=tk.NORMAL))
        
        thread = threading.Thread(target=call_llm_thread)
        thread.daemon = True
        thread.start()
    
    def process_llm_response(self, response):
        try:
            if isinstance(response, dict) and 'choices' in response:
                content = response['choices'][0]['message']['content']
            else:
                content = str(response)
            
            self.log(f"LLM响应: {content[:200]}...", "system")
            
            import re
            json_match = re.search(r'\{[\s\S]*\}', content)
            if json_match:
                result = json.loads(json_match.group())
                recommendation = result.get("recommendation", result.get("recommended_category", ""))
                reason = result.get("reason", "")
                
                self.recommendation = recommendation
                
                self.reason_text.delete("1.0", tk.END)
                self.reason_text.insert("1.0", reason)
                
                if recommendation in self.current_unique_values:
                    index = self.current_unique_values.index(recommendation)
                    self.selection_listbox.selection_clear(0, tk.END)
                    self.selection_listbox.selection_set(index)
                    self.selection_listbox.see(index)
                    
                    if self.current_step == 0:
                        self.selected_values["B"] = recommendation
                    elif self.current_step == 1:
                        self.selected_values["C"] = recommendation
                    elif self.current_step == 2:
                        self.selected_values["D"] = recommendation
                    
                    self.log(f"LLM推荐: {recommendation}", "success")
                else:
                    self.log(f"推荐 '{recommendation}' 不在选项列表中", "error")
            else:
                self.log("无法解析LLM响应中的JSON", "error")
                self.reason_text.delete("1.0", tk.END)
                self.reason_text.insert("1.0", content)
            
            self.send_button.config(state=tk.NORMAL)
            self.next_button.config(state=tk.NORMAL)
            
        except Exception as e:
            self.log(f"处理LLM响应失败: {str(e)}", "error")
            self.send_button.config(state=tk.NORMAL)
    
    def next_step(self):
        if self.current_step == 0:
            selection = self.selection_listbox.curselection()
            if selection:
                self.prepare_step_1()
                self.next_button.config(state=tk.DISABLED)
            else:
                messagebox.showwarning("警告", "请先选择一个一级分类")
        elif self.current_step == 1:
            selection = self.selection_listbox.curselection()
            if selection:
                self.prepare_step_2()
                self.next_button.config(state=tk.DISABLED)
            else:
                messagebox.showwarning("警告", "请先选择一个二级分类")
        elif self.current_step == 2:
            selection = self.selection_listbox.curselection()
            if selection:
                self.show_final_result()
            else:
                messagebox.showwarning("警告", "请先选择一个三级分类")
    
    def prev_step(self):
        if self.current_step == 1:
            self.prepare_step_0()
            self.prev_button.config(state=tk.DISABLED)
        elif self.current_step == 2:
            self.prepare_step_1()
        else:
            messagebox.showinfo("提示", "已经是第一步了")
    
    def show_final_result(self):
        selected_b = self.selected_values["B"]
        selected_c = self.selected_values["C"]
        selected_d = self.selected_values["D"]
        
        column_b = self.app_config.get("column_b", "一级分类")
        column_c = self.app_config.get("column_c", "二级分类")
        column_d = self.app_config.get("column_d", "三级分类")
        
        filtered_df = self.df[(self.df[column_b] == selected_b) & 
                             (self.df[column_c] == selected_c) & 
                             (self.df[column_d] == selected_d)]
        
        self.result_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
        
        result_str = f"""选择的分类路径：
一级分类: {selected_b}
二级分类: {selected_c}
三级分类: {selected_d}

匹配的数据行数: {len(filtered_df)}
"""
        
        self.result_text.delete("1.0", tk.END)
        self.result_text.insert("1.0", result_str)
        
        # 使用PROGRAM_DataFrameViewer显示完整数据
        if len(filtered_df) > 0:
            viewer = PROGRAM_DataFrameViewer(filtered_df)
        
        self.log(f"最终结果已显示，共 {len(filtered_df)} 条匹配数据", "success")
        self.next_button.config(state=tk.DISABLED)
    
    def on_mode_change(self):
        self.mode = self.mode_var.get()
        self.log(f"切换到模式: {self.mode}", "system")
    
    def reset(self):
        self.current_step = 0
        self.selected_values = {"B": None, "C": None, "D": None}
        self.recommendation = None
        self.result_frame.pack_forget()
        self.reason_text.delete("1.0", tk.END)
        self.next_button.config(state=tk.DISABLED)
        self.prepare_step_0()
        self.log("已重置", "system")
    
    def log(self, message, tag="system"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n", tag)
        self.log_text.see(tk.END)
        
        colors = {
            "system": self.text_color,
            "success": "#4CAF50",
            "error": "#F44336",
            "warning": "#FF9800"
        }
        self.log_text.tag_config(tag, foreground=colors.get(tag, self.text_color))

class PROGRAM_DataFrameViewer:
    def __init__(self, df):
        self.root =  tk.Toplevel()
        # 隐藏窗口，避免初始化过程中的闪烁
        self.root.withdraw()

        self.df = df
        self.current_page = 1
        self.rows_per_page = 30
        
        # 计算总页数
        self.total_pages = (len(df) + self.rows_per_page - 1) // self.rows_per_page
        
        self.setup_ui()
        self.center_window()
        self.load_page()
        
        # 所有初始化操作完成后，显示窗口
        self.root.deiconify()
    
    def setup_ui(self):
        """设置UI界面"""
        self.root.title("表格查看器")
        self.root.geometry("1200x600")
        self.root.minsize(800, 600)
        self.root.resizable(True, True)
        
        # 设置样式
        bg_color, frame_color, button_color, text_color, highlight_color = SETTING_style_UI(self.root)
        self.bg_color = bg_color
        self.frame_color = frame_color
        self.text_color = text_color
        
        # 创建主框架
        main_frame = ttk.Frame(self.root, style="Main.TFrame")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 创建tksheet框架
        sheet_frame = ttk.Frame(main_frame, style="Main.TFrame")
        sheet_frame.pack(fill=tk.BOTH, expand=True)
        
        # 创建tksheet
        self.sheet = tksheet.Sheet(sheet_frame)
        
        # 设置tksheet选项
        kwargs = {
            "copy_bindings": [
                "<Control-g>",
                "<Control-G>",
            ],
            "table_font": ("微软雅黑", 10, "normal"),
            "header_font": ("微软雅黑", 10, "normal"),
            "index_font": ("微软雅黑", 10, "normal"),
            # 滚动条颜色设置
            "scroll_troughcolor": bg_color,
            "scroll_bg": frame_color,
            "scroll_fg": text_color,
            "scroll_hover_bg": frame_color,
            "scroll_selected_bg": frame_color,
            # 表格样式
            "bg": bg_color,
            "header_bg": "#444444",
            "header_fg": "white",
            "index_bg": bg_color,
            "index_fg": text_color,
            "selection_bg": "#3a414d",
            "selection_fg": text_color,
        }
        self.sheet.set_options(**kwargs)
        
        # 配置tksheet绑定
        self.sheet.enable_bindings(
            "single_select", 
            "select_rows", 
            "row_select",
            "header_select",
            "column_select",
            "move_to_cell", 
            "column_width_resize", 
            "row_height_resize",
            "treeview",
            "ctrl_select",
            "shift_select",
            "drag_select",
            "select_columns",
            "cell_double_click"
        )
        
        self.sheet.pack(fill=tk.BOTH, expand=True)
        
        # 重新定义双击事件处理函数
        def on_sheet_double_click(event):
            """双击事件处理"""
            try:
                # 获取当前选中的单元格对象
                current_cell = self.sheet.get_currently_selected()
                if current_cell:
                    # 从对象中获取行和列
                    row = current_cell.row
                    col = current_cell.column
                    
                    if row is not None:
                        # 计算实际数据行号
                        start_idx = (self.current_page - 1) * self.rows_per_page
                        actual_row = start_idx + row
                        
                        # 确保行号在有效范围内
                        if 0 <= actual_row < len(self.df):
                            # 获取该行数据
                            row_data = self.df.iloc[actual_row]
                            
                            # 将行数据转换为字符串
                            content = "\n".join([f"{col_name}: {val}" for col_name, val in row_data.items()])
                            
                            # 显示内容
                            messagebox.showinfo("行数据详情", content, parent=self.root)
            except Exception as e:
                messagebox.showerror("错误", f"双击处理失败: {str(e)}", parent=self.root)
        
        # 绑定双击事件
        self.sheet.bind("<Double-1>", on_sheet_double_click)
        
        # 创建右键菜单
        self.sheet_menu = tk.Menu(self.root, tearoff=0, 
                                  background=bg_color, 
                                  foreground=text_color, 
                                  activebackground=frame_color, 
                                  activeforeground=text_color, 
                                  relief="flat", 
                                  borderwidth=1)
        self.sheet_menu.add_command(label="复制一个单元格或单行单列", command=self.copy_cell_content)
        
        # 绑定右键点击事件
        def on_sheet_right_click(event):
            self.sheet_menu.post(event.x_root, event.y_root)
        
        self.sheet.bind("<Button-3>", on_sheet_right_click)
        
        # 创建分页控制框架
        page_frame = ttk.Frame(main_frame, style="Main.TFrame")
        page_frame.pack(fill=tk.X, pady=(10, 0))
        
        # 第一页按钮
        self.first_btn = ttk.Button(
            page_frame, 
            text="首页", 
            command=self.go_to_first_page,
            style="Tool.TButton"
        )
        self.first_btn.pack(side=tk.LEFT, padx=5)
        
        # 上一页按钮
        self.prev_btn = ttk.Button(
            page_frame, 
            text="上一页", 
            command=self.go_to_prev_page,
            style="Tool.TButton"
        )
        self.prev_btn.pack(side=tk.LEFT, padx=5)
        
        # 页码显示
        self.page_var = tk.StringVar()
        self.page_label = ttk.Label(
            page_frame, 
            textvariable=self.page_var,
            style="Tool.TLabel"
        )
        self.page_label.pack(side=tk.LEFT, padx=10)
        
        # 页码输入
        self.page_entry = ttk.Entry(page_frame, width=5, style="Tool.TEntry")
        self.page_entry.insert(0, str(self.current_page))
        self.page_entry.pack(side=tk.LEFT, padx=5)
        
        # 跳转按钮
        self.go_button = ttk.Button(page_frame, text="跳转", style="Tool.TButton", command=self.go_to_page)
        self.go_button.pack(side=tk.LEFT, padx=5)
        
        # 总数据显示
        self.total_label = ttk.Label(page_frame, text=f"共 {len(self.df)} 行数据", style="Tool.TLabel")
        self.total_label.pack(side=tk.LEFT, padx=10)
        
        # 导出为xlsx按钮
        self.export_btn = ttk.Button(
            page_frame, 
            text="导出为xlsx", 
            command=self.export_to_xlsx,
            style="Tool.TButton"
        )
        self.export_btn.pack(side=tk.RIGHT, padx=5)
        

        
        # 下一页按钮
        self.next_btn = ttk.Button(
            page_frame, 
            text="下一页", 
            command=self.go_to_next_page,
            style="Tool.TButton"
        )
        self.next_btn.pack(side=tk.RIGHT, padx=5)
        
        # 最后一页按钮
        self.last_btn = ttk.Button(
            page_frame, 
            text="末页", 
            command=self.go_to_last_page,
            style="Tool.TButton"
        )
        self.last_btn.pack(side=tk.RIGHT, padx=5)
    
    def center_window(self):
        """窗口居中"""
        self.root.update_idletasks()
        width = 1200
        height = 600
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")
    
    def load_page(self):
        """加载指定页的数据"""
        # 计算当前页的起始和结束索引
        start_idx = (self.current_page - 1) * self.rows_per_page
        end_idx = min(start_idx + self.rows_per_page, len(self.df))
        
        # 获取当前页的数据
        page_data = self.df.iloc[start_idx:end_idx]
        
        # 准备列名和数据
        columns = list(page_data.columns)
        data = page_data.values.tolist()
        
        # 为每行添加行号前缀（显示实际行号）
        for i in range(len(data)):
            data[i].insert(0, start_idx + i + 1)
        
        # 更新列名，添加行号列
        display_columns = ['行号'] + columns
        
        # 设置tksheet数据
        self.sheet.set_sheet_data(data)
        self.sheet.headers(display_columns)
        
        # 设置列宽
        self.sheet.column_width(0, 80)  # 行号列固定宽度
        for i in range(1, len(display_columns)):
            self.sheet.column_width(i, 120)  # 数据列宽度
        
        # 更新页码显示
        self.page_var.set(f"第 {self.current_page} 页，共 {self.total_pages} 页")
        # 更新页码输入框
        self.page_entry.delete(0, tk.END)
        self.page_entry.insert(0, str(self.current_page))
    
    def copy_cell_content(self):
        """复制选中的单元格内容、整行或整列到系统剪贴板"""
        try:
            # 获取各种选择信息
            selected_rows = self.sheet.get_selected_rows()
            selected_cols = self.sheet.get_selected_columns()
            selected_cells = self.sheet.get_selected_cells()
            
            copy_text = ""
            
            if selected_cells and not selected_cols:
                # 复制单个单元格
                cell = list(selected_cells)[0]
                row, col = cell
                # 获取单元格数据
                cell_value = self.sheet.get_cell_data(row, col)
                copy_text = str(cell_value)
            elif selected_rows and not selected_cols and not selected_cells:
                # 复制整行
                selected_row = list(selected_rows)[0]
                # 获取当前页数据
                start_idx = (self.current_page - 1) * self.rows_per_page
                end_idx = min(start_idx + self.rows_per_page, len(self.df))
                page_data = self.df.iloc[start_idx:end_idx]
                
                if selected_row < len(page_data):
                    # 获取整行数据
                    row_data = page_data.iloc[selected_row]
                    # 转换为逗号分隔格式
                    copy_text = ",".join([str(val) for val in row_data])
            elif selected_cols:
                # 复制整列
                selected_col = list(selected_cols)[0]
                # 跳过行号列
                if selected_col > 0:
                    actual_col = selected_col - 1
                    # 获取整列数据
                    col_data = self.df.iloc[:, actual_col]
                    # 获取列名
                    col_name = self.df.columns[actual_col]
                    # 转换为换行分隔格式，包含表头
                    col_values = [str(val) for val in col_data]
                    copy_text = f"{col_name}\n" + "\n".join(col_values)
            
            # 将数据复制到剪贴板
            if copy_text:
                self.root.clipboard_clear()
                self.root.clipboard_append(copy_text)
                self.root.update()  # 确保剪贴板内容被更新
        except Exception as e:
            messagebox.showerror("错误", f"复制失败: {str(e)}", parent=self.root)
    
    def go_to_first_page(self):
        """跳转到第一页"""
        if self.current_page != 1:
            self.current_page = 1
            self.load_page()
    
    def go_to_prev_page(self):
        """跳转到上一页"""
        if self.current_page > 1:
            self.current_page -= 1
            self.load_page()
    
    def go_to_next_page(self):
        """跳转到下一页"""
        if self.current_page < self.total_pages:
            self.current_page += 1
            self.load_page()
    
    def go_to_last_page(self):
        """跳转到最后一页"""
        if self.current_page != self.total_pages:
            self.current_page = self.total_pages
            self.load_page()
    
    def go_to_page(self):
        """跳转到指定页码"""
        try:
            page = int(self.page_entry.get())
            if 1 <= page <= self.total_pages:
                self.current_page = page
                self.load_page()
        except ValueError:
            pass
    
    def export_to_xlsx(self):
        """导出数据为xlsx文件"""
        try:
            # 让用户选择保存路径
            file_path = filedialog.asksaveasfilename(
                title="导出为xlsx",
                filetypes=[("Excel文件", "*.xlsx"), ("所有文件", "*")],
                defaultextension=".xlsx",
                parent=self.root
            )
            
            if file_path:
                # 导出为xlsx文件
                self.df.to_excel(file_path, index=False)
                messagebox.showinfo("成功", f"数据已导出到 {file_path}", parent=self.root)
        except Exception as e:
            messagebox.showerror("错误", f"导出失败: {str(e)}", parent=self.root)


def main():
    """程序入口点"""
    root = tk.Tk()
    app = ClassificationAssistant(root)
    root.mainloop()


if __name__ == "__main__":
    main()
