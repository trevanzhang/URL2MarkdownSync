#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Copyright (c) 2025-present AuthorName <trevanzhang@qq.com>

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

__author__ = "TrevanZhang<trevanzhang@qq.com>"
__version__ = "0.0.1"
__license__ = "MIT"

import os
import re
import datetime
import random
import logging
from dataclasses import dataclass
from typing import Dict, Optional

import requests
from webdav4.client import Client
from dotenv import load_dotenv
from flask import Flask, request, jsonify
load_dotenv()  # 自动加载.env文件

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

@dataclass
class Markdown:
    is_success: bool = False  # 请求是否成功

    title: str = ''
    source: str = ''
    content: str = ''

class WebDav(object):
    def __init__(
            self,
            webdav_url: str,
            webdav_username: str,
            webdav_password: str,
    ):
        """
        初始化WebDav操作对象
        :param webdav_url:
        :param webdav_username:
        :param webdav_password:
        """
        logging.info("Initializing WebDav with URL: %s", webdav_url)
        self.webdav_url = webdav_url
        self.webdav_username = webdav_username
        self.webdav_password = webdav_password

        self._client: Optional[Client] = None

    @property
    def client(self) -> Client:
        if not self._client:
            logging.info("Creating WebDav client")
            self._client = Client(
                self.webdav_url,
                auth=(
                    self.webdav_username,
                    self.webdav_password
                )
            )
        return self._client

    def upload_file(
            self,
            local_file_path: str,
            remote_file_path: str,
    ) -> None:
        """
        上传文件
        :param local_file_path: 本地文件路径
        :param remote_file_path: 远程文件路径
        :return:
        """
        logging.info("Uploading file from %s to %s", local_file_path, remote_file_path)
        if not os.path.exists(local_file_path):
            logging.error("File not found: %s", local_file_path)
            raise FileNotFoundError(f'file_path: 【{local_file_path}】 not found')

        return self.client.upload_file(
            from_path=local_file_path,
            to_path=remote_file_path
        )

class Handler(object):

    def __init__(self, data: Dict, note_url: str = ''):
        logging.info("Initializing Handler with data: %s and note_url: %s", data, note_url)
        # 请求数据
        self.data: Dict = data

        self.note_url: str = note_url  # 笔记URL，若该值不为空，则忽略 note_title 和 note_content
        self.note_title: str = ''  # 笔记标题；
        self.note_content: str = ''  # 笔记内容；

        # 笔记保存路径；默认在根目录下创建
        self.save_note_path: str = os.getenv('save_note_path') or 'obsidian'
        self.note_source: str = '微信'  # 笔记来源，用于标记笔记属性

        self._webdav_handler: Optional[WebDav] = None
        self.message = ''

    @property
    def random_code(self) -> str:
        """随机生成指定长度的数字字符串"""
        code = ''.join(map(str, random.choices(range(10), k=5)))
        logging.info("Generated random code: %s", code)
        return code

    def get_note_from_url(self) -> bool:
        logging.info("Getting note from URL: %s", self.note_url)
        note_obj = self.convert_url_to_md(self.note_url)

        if not note_obj.is_success:
            logging.error("Failed to get note from URL: %s", self.note_url)
            return False

        self.note_title = f'{note_obj.title}.md'
        self.note_content = note_obj.content
        self.note_source = note_obj.source
        return True

    def is_note_valid(self) -> bool:
        logging.info("Validating note")
        if self.note_url:
            return self.get_note_from_url()

        self.note_url = self.data.get('note_url') or self.data.get('url')  # 笔记链接

        # 笔记保存路径；默认在根目录下创建
        self.save_note_path = self.data.get('save_note_path') or self.save_note_path

        if self.note_url:
            return self.get_note_from_url()

        self.note_title = self.data.get('note_title')  # 笔记标题

        if not self.note_title.endswith('.md'):
            self.note_title = f"{self.note_title}.md" if self.note_title else f"{self.random_code}.md"

        self.note_content = self.data.get('note_content')  # 字符串类型；笔记内容；
        self.note_source = self.data.get('note_source') or self.note_source  # 笔记来源，用于标记笔记属性

        return all([self.note_content, self.note_title])

    @staticmethod
    def convert_url_to_md(url: str) -> Markdown:
        """
        请求url获取html内容，转为markdown格式
        :param url:
        :return:
        """

        url = f'https://r.jina.ai/{url}'

        content_obj = Markdown()

        try:
            response = requests.get(url)

            lines = response.text.split('\n')

            title = ''
            source = ''
            for line in lines:

                if line.startswith('Title:'):
                    title = line.replace('Title:', '').strip()

                if line.startswith('URL Source:'):
                    source = line.replace('URL Source:', '').strip()

                if title and source:
                    break

            content_start_line = lines.index('Markdown Content:') + 1
            content = '\n'.join(lines[content_start_line:])

            content_obj.title = title
            content_obj.source = source
            content_obj.content = content
            content_obj.is_success = True
            # print(content_obj)
        except:
            content_obj.is_success = False
        finally:
            return content_obj   

    @staticmethod
    def get_webdav() -> Optional[WebDav]:
        logging.info("Getting WebDav configuration")
        webdav_url = os.getenv('webdav_url')
        webdav_user = os.getenv('webdav_user')
        webdav_psw = os.getenv('webdav_psw')

        if not all([webdav_url, webdav_user, webdav_psw]):
            logging.error("WebDav configuration is missing")
            return None

        return WebDav(webdav_url, webdav_user, webdav_psw)

    @property
    def webdav_handler(self) -> WebDav:
        if not self._webdav_handler:
            logging.info("Initializing WebDav handler")
            self._webdav_handler = self.get_webdav()

        if not self._webdav_handler:
            self.message = 'WebDAV存储配置初始化失败'
            logging.error("WebDAV storage configuration initialization failed")
            raise Exception('WebDAV存储配置初始化失败；本地无配置信息，请求信息中也无配置信息')

        return self._webdav_handler

    @property
    def current_data_str(self) -> str:
        return datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    def save_note_file(self) -> str:
        """
        保存笔记文件
        :return: 成功时返回笔记的路径
        """
        logging.info("Saving note file")
        note_content = f'[原文链接]({self.note_url})\n{self.note_content}' if self.note_url else self.note_content

        note_content = f"""---
date: {self.current_data_str}
source: {self.note_source}
---

{note_content}
"""

        file_path = os.path.join(self.save_note_path, self.note_title)

        try:
            # 确保目标目录存在
            os.makedirs(self.save_note_path, exist_ok=True)

            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(note_content)
            logging.info("Note file saved at: %s", file_path)
            return file_path
        except Exception as e:
            logging.error("Failed to save note file: %s", e)
            return ''

    def upload_file_to_webdav(self, local_file_path: str, remote_file_path: str) -> bool:
        """
        上传文件到webdav
        :param local_file_path:
        :param remote_file_path:
        :return:
        """
        logging.info("Uploading file to WebDav from %s to %s", local_file_path, remote_file_path)
        try:
            if not self.webdav_handler.client.exists(self.save_note_path):
                self.webdav_handler.client.mkdir(self.save_note_path)

            self.webdav_handler.upload_file(local_file_path, remote_file_path)
            return True
        except Exception as e:
            self.message = f'上传笔记到WebDAV发送未知错误，【{e}】'
            logging.error("Error uploading file to WebDav: %s", e)
            return False

    def upload_file(self, local_file_path: str, remote_file_path: str) -> bool:
        """封装WebDav上传操作"""
        logging.info("Uploading file from %s to %s", local_file_path, remote_file_path)
        try:
            self.webdav_handler.upload_file(local_file_path, remote_file_path)
            self.message = f"笔记已成功保存至：{remote_file_path}"
            logging.info("File successfully uploaded to: %s", remote_file_path)
            return True
        except Exception as e:
            self.message = f"上传失败：{str(e)}"
            logging.error("Failed to upload file: %s", e)
            return False

    def run(self) -> str:
        logging.info("Running Handler")
        if not self.is_note_valid():
            logging.error("Note content or title is empty")
            return '笔记内容或标题为空'

        local_note_path = self.save_note_file()
        if not local_note_path:
            logging.error("Failed to save note file")
            return '笔记文件保存失败'

        self.upload_file(
            local_file_path=local_note_path,
            remote_file_path=f'{self.save_note_path}/{self.note_title}'
        )

        return self.message

def include_url(url):
    """
    检查给定的字符串是否包含一个有效的URL。

    :param url: 需要检查的字符串
    :return: 如果是有效的URL返回True，否则返回False
    """
    # 定义正则表达式
    url_pattern = re.compile(
        r'https?://'  # 匹配 http 或 https 协议
        r'(www\.)?'  # 可选的 www. 前缀
        r'[-a-zA-Z0-9@:%._\+~#=]{1,256}'  # 域名部分
        r'\.[a-zA-Z0-9()]{1,6}'  # 顶级域名
        r'\b'  # 单词边界
        r'([-a-zA-Z0-9()@:%_\+.~#?&//=]*)'  # 路径、查询参数和片段标识符
    )

    # 使用正则表达式进行匹配
    match = url_pattern.match(url.replace('收到了聊天记录:', ''))

    # 返回匹配结果
    return bool(match)


app = Flask(__name__)

@app.route('/process_note', methods=['POST'])
def process_note():
    """
    处理笔记的接口
    请求参数：
        - note_url: 笔记链接（可选）
        - note_title: 笔记标题（可选）
        - note_content: 笔记内容（可选）
        - save_note_path: 笔记保存路径（可选）
        - note_source: 笔记来源（可选）
    返回值：
        - 成功时返回成功信息和文件路径
        - 失败时返回错误信息
    """
    try:
        # 获取请求数据
        data = request.json or {}
        logging.info("Received request data: %s", data)

        # 初始化 Handler
        handler = Handler(data=data)

        # 调用 Handler 的 run 方法处理笔记
        result = handler.run()

        # 返回结果
        return jsonify({
            "status": "success" if "成功" in result else "error",
            "message": result
        }), 200

    except Exception as e:
        logging.error("Error processing note: %s", e)
        return jsonify({
            "status": "error",
            "message": f"处理笔记时发生错误：{str(e)}"
        }), 500

if __name__ == '__main__':
    # 检查WebDav基础配置
    if not all([os.getenv('webdav_url'), os.getenv('webdav_user'), os.getenv('webdav_psw')]):
        raise ValueError("缺少WebDav环境变量配置")

    app.run(host='0.0.0.0', port=5000, debug=True)  # 启动Flask服务器
    logging.info("server started, listening on port 5000")

