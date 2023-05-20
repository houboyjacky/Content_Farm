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

import os
import pytesseract
import random
import re
import time
import tldextract
import Tools
from GetFromNetizen import push_netizen_file, write_new_netizen_file, get_netizen_file
from io import BytesIO
from Line_Invite_URL import lineinvite_write_file, lineinvite_read_file, get_random_invite, push_random_invite
from linebot import LineBotApi
from linebot.models import TextSendMessage
from Logger import logger
from PIL import Image
from Point import read_user_point, get_user_rank
from PrintText import user_guide
from Query_Line_ID import user_query_lineid, user_add_lineid
from Query_URL import user_query_website, check_blacklisted_site, get_web_leaderboard, update_part_blacklist

image_analysis = False
line_bot_api = LineBotApi(Tools.CHANNEL_ACCESS_TOKEN)

# 回應訊息的函式
def message_reply(reply_token, text):
    message = TextSendMessage(text=text)
    line_bot_api.reply_message(reply_token, message)
    return

allowlist = { "facebook.com", "instagram.com", "google.com"}

# 管理員操作
def handle_admin_message_text(user_text):
    global setting
    rmessage = ''

    orgin_text = user_text
    lower_text = user_text.lower()

    if match := re.search(Tools.KEYWORD[5], lower_text):
        lineid = match.group(1)
        if user_query_lineid(lineid):
            rmessage = f"邀請黑名單與賴黑名單已存在{lineid}"
        else:
            # 加入新line id
            user_add_lineid(lineid)
            rmessage = f"邀請黑名單與賴黑名單更新完成{lineid}"

    elif match := re.search(Tools.KEYWORD[4], lower_text):
        r =  lineinvite_write_file(orgin_text)
        if r == 1:
            rmessage = f"邀請黑名單已存在"
        elif r == 0:
            rmessage = f"邀請黑名單更新完成"
        else:
            rmessage = f"邀請黑名單更新失敗"

    elif match := re.search(Tools.KEYWORD[0], lower_text):

        match = re.search(Tools.KEYWORD[0], lower_text)

        # 取得網址
        url = match.group(1)

        # 使用 tldextract 取得網域
        extracted = tldextract.extract(url)
        domain = extracted.domain
        suffix = extracted.suffix
        if domain in allowlist:
            rmessage = f"網址封鎖有誤，不允許{domain}.{suffix}"
            return rmessage

        # 組合成新的規則
        new_rule = "||"+ domain + "." + suffix + "^\n"

        # 將Adguard規則寫入檔案
        with open(Tools.NEW_SCAM_WEBSITE_FOR_ADG, "a", encoding="utf-8", newline='') as f:
            f.write(new_rule)

        r = check_blacklisted_site(url)
        if r:
            rmessage = f"網址黑名單已存在"
        else:
            # 提早執行更新
            update_part_blacklist(domain + "." + suffix)
            rmessage = f"網址黑名單更新完成"

    elif match := re.search(Tools.KEYWORD[1], orgin_text):

        # 取得文字
        text = match.group(1)

        # 組合成新的規則
        new_rule = "! " + text + "\n"

        # 將文字寫入
        with open(Tools.NEW_SCAM_WEBSITE_FOR_ADG, "a", encoding="utf-8", newline='') as f:
            f.write(new_rule)

        rmessage = f"網址名單更新完成"

    elif match := re.search(Tools.KEYWORD[2], lower_text):

        # 取得文字
        lineid = match.group(1)
        r = user_query_lineid(lineid)
        if r:
            rmessage = f"賴黑名單已存在" + lineid
        else:
            # 加入新line id
            user_add_lineid(lineid)
            rmessage = f"賴黑名單已加入" + lineid
    else:
        pass

    return rmessage

def handle_message_text(event):
    global image_analysis

    # 取得發訊者的 ID
    user_id = event.source.user_id
    logger.info(f'UserID = {event.source.user_id}')
    logger.info(f'UserMessage = {event.message.text}')

    # 讀取使用者傳來的文字訊息
    orgin_text = event.message.text
    lower_text = event.message.text.lower()

    if user_id in Tools.BLACKUSERID:
        warningsign=["嘿嘿等到你來了:D", "測試人員來上班了啊～","封鎖、刪除、再加入，手會痠嗎？","我已經鎖定你囉！"]
        random_sign = random.choice(warningsign)
        message_reply(event.reply_token, random_sign)
        return

    if len(orgin_text) > 1000:
        rmessage = f"謝謝你提供的情報\n請縮短長度或分段傳送"
        message_reply(event.reply_token, rmessage)
        return

    if orgin_text.startswith("使用指南"):
        message_reply(event.reply_token, user_guide)
        return

    # 管理員操作
    if user_id in Tools.ADMINS:
        if orgin_text == "重讀":
            setting = ''
            Tools.reloadSetting()
            logger.info("Reload setting.json")
            rmessage = f"設定已重新載入"
            message_reply(event.reply_token, rmessage)
            return
        elif orgin_text == "檢閱":
            content = get_netizen_file(user_id)
            if content:
                rmessage = f"內容：\n\n{content}\n\n參閱與處置後\n請輸入「完成」或「失效」"
            else:
                rmessage = f"目前沒有需要檢閱的資料"
            message_reply(event.reply_token, rmessage)
            return
        elif orgin_text == "關閉辨識":
            image_analysis = False
            rmessage = f"已關閉辨識"
            message_reply(event.reply_token, rmessage)
            return
        elif orgin_text == "開啟辨識":
            image_analysis = True
            rmessage = f"已開啟辨識"
            message_reply(event.reply_token, rmessage)
            return
        elif orgin_text.startswith("加入"):
            rmessage = handle_admin_message_text(orgin_text)
            if rmessage:
                message_reply(event.reply_token, rmessage)
                return
        else:
            pass

    if orgin_text.startswith("詐騙回報"):
        user_name = line_bot_api.get_profile(user_id).display_name
        write_new_netizen_file(user_id, user_name, orgin_text)
        rmessage = f"謝謝你提供的情報\n輸入「積分」\n可以查詢你的積分排名"
        message_reply(event.reply_token, rmessage)
        return

    if orgin_text == "網站排行榜":
        rmessage = get_web_leaderboard()
        message_reply(event.reply_token, rmessage)
        return

    if orgin_text == "遊戲":
        site = get_random_invite(user_id)
        if not site:
            rmessage = f"目前暫停檢舉遊戲喔~"
        else:
            rmessage = f"請開始你的檢舉遊戲\n{site}\n若「完成」請回報「完成」\n若「失效」請回傳「失效」"

        message_reply(event.reply_token, rmessage)
        return

    if orgin_text == "完成":
        found = push_random_invite(user_id, True, False)
        found2 = push_netizen_file(user_id, True, False)
        if found or found2:
            rmessage = f"感謝你的回報\n輸入「遊戲」\n進行下一波行動\n輸入「積分」\n可以查詢你的積分排名"
        else:
            rmessage = f"程式有誤，請勿繼續使用"

        message_reply(event.reply_token, rmessage)
        return

    if orgin_text == "失效":
        found = push_random_invite(user_id, False, True)
        found2 = push_netizen_file(user_id, False, True)
        if found or found2:
            rmessage = f"感謝你的回報\n輸入「遊戲」\n進行下一波行動\n輸入「積分」\n可以查詢你的積分排名"
        else:
            rmessage = f"程式有誤，請勿繼續使用"
        message_reply(event.reply_token, rmessage)
        return

    if orgin_text == "積分":
        point = read_user_point(user_id)
        rank = get_user_rank(user_id)

        rmessage = f"你的檢舉積分是{str(point)}分\n排名第{str(rank)}名"
        message_reply(event.reply_token, rmessage)
        return

    # 查詢line邀請網址
    if re.match(Tools.KEYWORD[7], lower_text):
        r = lineinvite_read_file(orgin_text)
        if r == -1:
            rmessage = (f"「 {orgin_text} 」\n"
                        f"輸入有誤，請重新確認\n"
                        f"感恩"
                        )
        elif r == True:
            rmessage = (f"「 {orgin_text} 」\n"
                        f"「是」已知詐騙Line邀請網址\n"
                        f"請勿輕易信任此Line ID的\n"
                        f"文字、圖像、語音和連結\n"
                        f"感恩"
                        )
        else:
            rmessage = (f"「 {orgin_text} 」\n"
                        f"「不是」已知詐騙邀請網址\n"
                        f"並不代表沒問題，請繼續觀察"
                        f"有任何問題，請補充描述\n"
                        f"讓大家繼續幫助大家"
                        f"感恩")
        message_reply(event.reply_token, rmessage)
        return

    # 如果用戶輸入的網址沒有以 http 或 https 開頭，則不回應訊息
    if re.match(Tools.KEYWORD[8], lower_text):
        if lower_text.startswith("https://lm.facebook.com"):
            url = Tools.decode_facebook_url(lower_text)
            rmessage = f"你想輸入的網址是不是\n「 {url} 」\n請複製貼上對話框\n才能正確判斷"
        else:
            rmessage = user_query_website(lower_text)
        message_reply(event.reply_token, rmessage)
        return

    # 查詢Line ID
    if re.search(Tools.KEYWORD[3], lower_text):
        lineid = lower_text.replace("賴", "")
        if user_query_lineid(lineid):
            rmessage = (f"「{lineid}」\n"
                        f"「是」詐騙Line ID\n"
                        f"請勿輕易信任此Line ID的\n"
                        f"文字、圖像、語音和連結\n"
                        f"感恩")
        else:
            rmessage = (f"「{lineid}」\n"
                        f"目前不在詐騙黑名單中\n"
                        f"並不代表沒問題，請繼續觀察\n"
                        f"有任何問題，請補充描述\n"
                        f"讓大家繼續幫助大家\n"
                        f"感恩")

        message_reply(event.reply_token, rmessage)
        return

    return

def handle_message_image(event):
    # 取得發訊者的 ID
    logger.info(f'UserID = {event.source.user_id}')
    logger.info(f'UserMessage = image message')

    # 儲存照片的目錄
    IMAGE_DIR = "image/"
    rmessage = ''
    website_list = []

    # 取得照片
    message_content = line_bot_api.get_message_content(event.message.id)
    image = Image.open(BytesIO(message_content.content))

    # 儲存照片
    IMAGE = "image"
    IMAGE_DIR = f"{IMAGE}/"
    if not os.path.isdir(IMAGE_DIR):
        os.mkdir(IMAGE_DIR)

    user_id = event.source.user_id
    user_dir = f"{IMAGE}/{user_id}/"
    if not os.path.isdir(user_dir):
        os.mkdir(user_dir)

    user_files = [f for f in os.listdir(user_dir) if f.startswith(user_id)]
    num_files = len(user_files)
    filename = f"{user_dir}{user_id}_{num_files+1:02}.jpg"
    with open(filename, "wb") as f:
        f.write(message_content.content)

    if user_id in Tools.ADMINS and image_analysis:
        # 取得開始時間
        start_time = time.time()
        # 辨識文字
        text_msg = pytesseract.image_to_string(image, lang='eng+chi_tra+chi_sim', config='--psm 12')

        # 判斷是否有網址
        url_pattern = re.compile(r"(http|https)://[^\s]+")
        website_list = url_pattern.findall(text_msg)

        # 回應訊息
        if website_list:
            website_msg = "\n".join(website_list)
        else:
            website_msg = "無"

        # 取得結束時間
        end_time = time.time()

        # 計算耗時
        elapsed_time = end_time - start_time

        # 轉換格式
        elapsed_time_str = Tools.format_elapsed_time(elapsed_time)

        rmessage += f"網站：\n{website_msg}\n\n耗時：{elapsed_time_str}\n\n判斷文字：\n{text_msg}"
        message_reply(event.reply_token, rmessage)
    return

def handle_message_file(event):

    # 取得發訊者的 ID
    logger.info('UserID = '+ event.source.user_id)

    # 設定儲存檔案的目錄
    FILE_DIR = ""

    # 取得檔案內容
    message_content = line_bot_api.get_message_content(event.message.id)

    # 判斷檔案類型
    file_type = event.message.type
    file_extension = ""
    if file_type == "video":
        FILE_DIR = "video/"
        file_extension = ".mp4"
    elif file_type == "audio":
        FILE_DIR = "audio/"
        file_extension = ".m4a"
    elif file_type == "file":
        FILE_DIR = "file/"
        file_name = event.message.file_name.split(".")[0]
        file_extension = "." + file_name.split(".")[-1] # 取得最後一個'.'後的副檔名
    else:
        return

    if not os.path.isdir(FILE_DIR):
        os.mkdir(FILE_DIR)

    logger.info('UserType = '+ file_type)

    # 儲存檔案
    user_id = event.source.user_id
    user_files = [f for f in os.listdir(FILE_DIR) if f.startswith(user_id)]
    num_files = len(user_files)
    filename = f"{user_id}_{num_files+1:02}{file_extension}"
    with open(os.path.join(FILE_DIR, filename), "wb") as f:
        for chunk in message_content.iter_content():
            f.write(chunk)

    # 回覆使用者已收到檔案
    message_reply(event.reply_token, "")
    return
