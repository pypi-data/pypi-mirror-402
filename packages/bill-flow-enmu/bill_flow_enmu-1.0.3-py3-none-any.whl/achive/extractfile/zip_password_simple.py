import zipfile
import os
import time
import datetime
import concurrent.futures
import multiprocessing

# Cleaned up hardcoded path
# zip_folder_path = config["data"]["zip_folder"]
zip_folder_path = "/Users/enmu/code/mandt/account/alipay_data"
def get_zip_path_self(dirpath) -> str:
    if not os.path.exists(dirpath): return ""
    today = datetime.date.today()
    found = []
    try:
        files = os.listdir(dirpath)
    except OSError:
        return ""

    for file in files:
        filepath = os.path.join(dirpath, file)
        if os.path.isfile(filepath) and file.lower().endswith(".zip"):
            timestamp = os.path.getmtime(filepath)
            if today == datetime.date.fromtimestamp(timestamp):
                found.append(filepath)
    if not found: return ""
    found.sort(key=lambda file: os.path.getmtime(file))
    return found[-1]

def check_password_chunk(zip_path, start, end):
    """
    Worker function to try a range of passwords.
    Returns (password, content_bytes) if found, else None.
    """
    try:
        with zipfile.ZipFile(zip_path, 'r') as zf:
            if not zf.namelist(): return None
            file_in_zip = zf.namelist()[0]

            for i in range(start, end):
                passwd = str(i).encode("utf-8")
                try:
                    with zf.open(file_in_zip, 'r', pwd=passwd) as f_src:
                        return (passwd.decode(), f_src.read())
                except (RuntimeError, zipfile.BadZipFile):
                    continue
                except Exception:
                    continue
    except Exception:
        pass
    return None

def process_zip_logic() -> bool:
    # zip_file_path = get_zip_path_self(zip_folder_path)
    zip_file_path = zip_folder_path + "/a.zip"
    if not zip_file_path:
        print("今天没有找到 ZIP 文件")
        return False

    print(f"发现文件: {zip_file_path}")
    extract_path = os.path.dirname(zip_file_path)

    # Performance optimization: Parallel processing
    # Range 0 to 1,000,000
    TOTAL_RANGE = 1000000
    cpu_count = multiprocessing.cpu_count() or 4
    chunk_size = TOTAL_RANGE // cpu_count

    found_result = None

    print(f"正在使用 {cpu_count} 个进程尝试破解密码...")

    with concurrent.futures.ProcessPoolExecutor(max_workers=cpu_count) as executor:
        futures = []
        for i in range(cpu_count):
            # 每一个线程从哪里开始
            start = i * chunk_size
            # 每一个线程从哪里结束
            end = (i + 1) * chunk_size if i != cpu_count - 1 else TOTAL_RANGE
            futures.append(executor.submit(check_password_chunk, zip_file_path, start, end))

        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            if result:
                found_result = result
                # Cancel other futures if possible (though python futures aren't easily cancellable)
                for f in futures: f.cancel()
                break

    if found_result:
        password, byte_content = found_result
        print(f"解压成功, 密码是: {password}")

        # Encoding conversion
        try:
            content_str = byte_content.decode('gb18030')
        except UnicodeDecodeError:
            content_str = byte_content.decode('utf-8', errors='ignore')

        new_name = f"{str(datetime.date.today())}.csv"
        new_file_path = os.path.join(extract_path, new_name)

        with open(new_file_path, "w", encoding="utf-8") as f_dst:
            f_dst.write(content_str)

        print(f"已生成新文件: {new_file_path}")

        try:
            os.remove(zip_file_path)
            print(f"🗑️ 已删除源压缩包: {zip_file_path}")
        except Exception as e:
            print(f"❌ 删除压缩包失败 (可能被占用): {e}")

        return True
    else:
        print("未找到正确密码或解压失败。")
        return False

if __name__ == "__main__":
  start_time = time.perf_counter()
  process_zip_logic()
  end_time = time.perf_counter()

  # 计算差值
  execution_time = end_time - start_time
  print(f"执行时间: {execution_time:.6f} 秒")



