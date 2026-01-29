import multiprocessing
import queue
import os



def test(tasks,result,event):
  filename = f".log_process_{os.getpid()}.txt"
  with open(filename,"a",encoding="utf-8") as f:

    while not event.is_set():
      try:
        start_index,end_index = tasks.get(block=True, timeout=0.05)
        f.write(f"进程{os.getpid()} 正在处理 {start_index} 到 {end_index} 批次任务\n")
        for i in range(start_index,end_index):
          if event.is_set(): return

          current = i
          f.write(f"当前进程{os.getpid()}处理的密码是{current}\n")
          if current == 917486:
            f.write(f"进程{os.getpid()}知道了密码，{current}")
            f.flush()
            result.put(current)
            event.set()
            return

      except queue.Empty:
        break
      except Exception as e:
        print("error",e)
        break




if __name__ == "__main__":
  manager = multiprocessing.Manager()
  tasks = manager.Queue()

  result = manager.Queue()

  stop_event = manager.Event()


  # 初始化任务
  task_count = 1000000
  chunk = 2000

  for i in range(0, task_count, chunk):
    end = min(chunk + i, task_count)
    tasks.put((i,end))


  processes = []

  for i in range(10):
    p = multiprocessing.Process(target=test, args=(tasks,result,stop_event))
    p.start()
    processes.append(p)


  f = None

  for p in processes:
    p.join()

  if not result.empty():
    f = result.get()

    print("result:",f)




