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

from datetime import date
from Logger import logger
import Query_API


NAME = "詐騙回報"


def Report_Cancel_Document(user_text):

    collection = Query_API.Read_Collection(NAME, NAME)
    if collection is None:
        logger.info("Report_Cancel_Document collection is empty")
        return

    query = {
        "$and": [
            {"內容": user_text
             }
        ]
    }

    document = collection.find_one(query)
    logger.info(f"document = {document}")
    if not document:
        return False

    document["失效"] = 1

    Query_API.Update_Document(collection, document, "_id")
    return True


def Report_Write_Document(user_id: str, user_name: str, user_text: str, is_system: bool) -> bool:

    collection = Query_API.Read_Collection(NAME, NAME)
    if collection is None:
        logger.info("Report_Write_Document collection is empty")
        return False

    query = {
        "$and": [
            {"內容": user_text,
                "提交者ID": user_id
             }
        ]
    }

    if collection.find_one(query):
        return True

    total_documents = collection.count_documents({})
    number = total_documents + 1

    datetime = date.today().strftime("%Y-%m-%d")

    struct = {"序號": number,
              "時間": datetime,
              "提交者": user_name,
              "提交者ID": user_id,
              "內容": user_text,
              "完成": 0,
              "失效": 0,
              "檢查者": "",
              "系統轉送": is_system
              }

    Query_API.Write_Document(collection, struct)
    return False


def Report_Read_Document(user_id: str):

    collection = Query_API.Read_Collection(NAME, NAME)
    if collection is None:
        logger.info("Report_Read_Document collection is empty")
        return "", "", ""
    total_documents = collection.count_documents({})

    query = {
        "$and": [
            {"完成": 0,
                "失效": 0
             }
        ]
    }
    result = collection.find_one(query)
    if result:
        # logger.info("result=%s", result)
        SN = f"{result['序號']}/{total_documents}"
        result['檢查者'] = user_id
        Query_API.Update_Document(collection, result, "_id")
        return SN, result["內容"], result["系統轉送"]

    return total_documents, "", ""


def Report_Finish_Document(user_id, success, disappear):

    found = False
    collection = Query_API.Read_Collection(NAME, NAME)
    document = Query_API.Search_Same_Document(collection, "檢查者", user_id)

    if not document:
        return found

    found = True

    if success:
        document['完成'] = 1
    if disappear:
        document['失效'] = 1
    document['檢查者'] = ""

    Query_API.Update_Document(collection, document, "_id")

    return found
