import logging
import queue
import zipfile
import os
import datetime
import multiprocessing
import zlib
import io
from pathlib import Path

import pandas as pd
from achive.utils.utils import config

ali_zip_folder_path = config["data"]["ali_zip_folder"]
wechat_zip_folder_path = config["data"]["wechat_zip_foler"]
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")


rename_dict = {
    "交易时间": "交易时间",
    "金额(元)": "金额",
    "交易类型": "交易分类",
    "交易对方": "交易对方",
    "收/支": "收/支",
    "商品": "商品说明",
    "支付方式": "收/付款方式",
    "当前状态": "交易状态",
    "交易单号": "交易订单号",
    "商户单号": "商家订单号",
    "备注": "备注",
}


def get_zip_path_self(dirpath) -> list:
    if not os.path.exists(dirpath):
        return []
    today = datetime.date.today()
    found = []
    try:
        files = os.listdir(dirpath)
    except OSError:
        return []

    for file in files:
        filepath = os.path.join(dirpath, file)
        if os.path.isfile(filepath) and file.lower().endswith(".zip"):
            timestamp = os.path.getmtime(filepath)
            if today == datetime.date.fromtimestamp(timestamp):
                found.append(filepath)
    if not found:
        return []
    found.sort(key=lambda file: os.path.getmtime(file))
    # return found[-1]
    return found


def check_password_chunk(zip_path, result, tasks, event):
    try:
        with zipfile.ZipFile(zip_path, "r") as zf:
            if not zf.namelist():
                return None
            file_in_zip = zf.namelist()[0]
            while not event.is_set():
                try:
                    start, end = tasks.get(block=True, timeout=10.0)
                except queue.Empty:
                    break

                for i in range(start, end):
                    passwd_str = f"{i:06d}"
                    passwd = passwd_str.encode("utf-8")
                    try:
                        with zf.open(file_in_zip, "r", pwd=passwd) as f_src:
                            # 注：打开了压缩包不代表密码正确，这里读取如果密码错误字节对不上会进入密码错误异常
                            csv_content = f_src.read()
                            event.set()
                            result.put((passwd.decode(), csv_content))
                            return
                    except (RuntimeError, zipfile.BadZipFile, zlib.error):
                        # 密码错误异常,直接略过，重新尝试
                        continue
                    except Exception as e:
                        logging.error(f"{e}")
                        continue
    except Exception as e:
        logging.error(f"进程 {os.getpid()} 启动失败，文件无法打开: {e}")


def process_zip_pass(zp):
    p = get_zip_path_self(zp)
    for z in p:
        e_p = os.path.dirname(z)
        if not e_p:
            logging.error("没有找到文件")
            return False
        manager = multiprocessing.Manager()
        tasks = manager.Queue()
        results = manager.Queue()
        event = manager.Event()
        chunk = 2000
        task_q = 1000000
        for i in range(0, task_q, chunk):
            end = min(i + chunk, task_q)
            tasks.put((i, end))
        processes = []
        cpu_count = multiprocessing.cpu_count() or 2
        for i in range(cpu_count):
            p = multiprocessing.Process(
                target=check_password_chunk, args=(z, results, tasks, event)
            )
            p.start()
            processes.append(p)
        for p in processes:
            p.join()
    return results


def process_file():
    try:
        ali_result = process_zip_pass(ali_zip_folder_path)
        wechat_result = process_zip_pass(wechat_zip_folder_path)
        process_content(ali_result, "ali")
        process_content(wechat_result, "wechat")
    except:
        return False
    finally:
        today_str = datetime.date.today().strftime("%Y%m%d")
        ali_zip_path = str(Path(ali_zip_folder_path) / f"{today_str}.zip")
        wechat_zip_path = str(Path(wechat_zip_folder_path) / f"{today_str}.zip")
        try:
            if os.path.exists(ali_zip_path):
                os.remove(ali_zip_path)
            if os.path.exists(wechat_zip_path):
                os.remove(wechat_zip_path)
            return True
        except Exception as e:
            logging.error(f"删除出现异常: {e}")
            return False


def process_content(result, t):
    try:
        if not result.empty():
            _, content_byte = result.get()
        with io.BytesIO(content_byte) as buffer:
            handle_content(buffer, t)
    except Exception as e:
        print("发生异常", e)


def handle_content(buffer, t):
    if not t:
        raise ValueError("类型错误")
    if t == "wechat":
        new_file_path = str(
            Path(wechat_zip_folder_path) / f"{datetime.date.today()}.csv"
        )
        raw_df = pd.read_excel(buffer, header=None)
        start_row_index = raw_df[
            raw_df[0].astype(str).str.contains("交易时间", na=False)
        ].index[0]
        buffer.seek(0)

        df = pd.read_excel(buffer, header=start_row_index)  # type: ignore
        df.rename(columns=rename_dict, inplace=True)
        df["金额"] = df["金额"].str.replace("¥", "").astype(float)  # type: ignore
        df["备注"] = df["备注"].str.replace("/", "").astype(str)  # type: ignore
        df.to_csv(new_file_path, index=False, encoding="utf-8-sig")  # type: ignore
    else:
        new_file_path = str(Path(ali_zip_folder_path) / f"{datetime.date.today()}.csv")
        with open(new_file_path, "w", encoding="utf-8") as f:
            content_str = buffer.read().decode("gbk")
            f.write(content_str)
        # wrapper = io.TextIOWrapper(buffer, encoding="gbk", newline="")
        # for i, line in enumerate(wrapper):
        #     if "交易时间" in line:
        #         start_row_index_ali = i
        #         break
        # wrapper.detach()
        # buffer.seek(0)
        # df = pd.read_csv(buffer, skiprows=start_row_index_ali, encoding="gbk")
        # file_exists = os.path.exists(new_file_path)
        # df.drop(columns=["对方账号", "Unnamed: 12"], inplace=True)
        # df.to_csv(
        #     new_file_path,
        #     mode="a",
        #     header=not file_exists,
        #     index=False,
        #     encoding="utf-8-sig",
        # )
