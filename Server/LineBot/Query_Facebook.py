'''
Copyright (c) 2023 Jacky Hou

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
'''

import re
from Logger import logger
from typing import Optional
import Tools

FB_list = Tools.read_json_file(Tools.FB_BLACKLIST)

def analyze_FB_url(user_text:str) -> Optional[dict]:

    user_text = user_text.replace("加入", "")

    logger.info(f"user_text: {user_text}")

    if match := re.search(Tools.KEYWORD[15], user_text):
        logger.info(f"Rule = {Tools.KEYWORD[15]}")
        Username = match.group(1)
    elif match := re.search(Tools.KEYWORD[19], user_text):
        logger.info(f"Rule = {Tools.KEYWORD[19]}")
        return None
    elif match := re.search(Tools.KEYWORD[16], user_text):
        logger.info(f"Rule = {Tools.KEYWORD[16]}")
        Username = match.group(1)
    else:
        return None

    logger.info(f"Username = {Username}")

    struct =  {"帳號": Username, "原始網址": user_text, "回報次數": 0, "失效": 0, "檢查者": ""}

    return struct

def add_sort_FB(input, results):
    # 查找是否有重複的識別碼和帳號
    for r in results:
        if r['帳號'] == input['帳號']:
            return 1
    results.append(input)
    return 0

def FB_write_file(user_text:str) -> int:
    global FB_list
    result = analyze_FB_url(user_text)
    if result:
        r = add_sort_FB(result,FB_list)
        if r == 0 :
            Tools.write_json_file(Tools.FB_BLACKLIST, FB_list)
        logger.info("分析完成，結果已寫入")
        return r
    else:
        logger.info("無法分析網址")
        return -1

def FB_read_file(user_text:str) -> int:
    global FB_list
    analyze = analyze_FB_url(user_text)
    if not analyze:
        return -1
    for result in FB_list:
        if result["帳號"] == analyze["帳號"]:
            return True
    return False

def FB_check_data(filename: str) -> None:
    global FB_list
    modify = False
    for item in FB_list:
        if "帳號" not in item:
            item["帳號"] = ""
            modify = True
        if "原始網址" not in item:
            item["原始網址"] = ""
            modify = True
        if "回報次數" not in item:
            item["回報次數"] = 0
            modify = True
        if "失效" not in item:
            item["失效"] = 0
            modify = True
        if "檢查者" not in item:
            item["檢查者"] = ""
            modify = True
    if modify:
        Tools.write_json_file(filename, FB_list)

def FB_clear_data(filename: str) -> None:
    global FB_list
    modify = False
    for item in FB_list:
        if item["檢查者"]:
            item["檢查者"] = ""
            modify = True
    if modify:
        Tools.write_json_file(filename, FB_list)

FB_check_data(Tools.FB_BLACKLIST)
FB_clear_data(Tools.FB_BLACKLIST)