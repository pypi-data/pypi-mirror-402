import os
import tempfile
import shutil
from pathlib import Path

# 20241009启用，从c盘到d盘回复制而不是移动，导致temp文件夹飙升
# def write_file(file_path, data):
# 	# 创建一个临时文件
# 	with tempfile.NamedTemporaryFile(delete=False, mode='w', encoding='utf-8') as tmp_file:
# 		# 写入临时文件
# 		tmp_file.write(data)
# 		tmp_file.flush()  # 确保数据被写入到磁盘
# 		os.fsync(tmp_file.file.fileno())  # 确保文件元数据被写入到磁盘
# 		tmp_file.close()  # 关闭临时文件

#     # 将临时文件重命名为目标文件名，这是原子操作

#     # 检查目标文件是否存在并删除它
# 	if os.path.exists(file_path):
# 		try:
# 			os.remove(file_path)
# 		except:
# 			pass
# 	try:
# 		os.rename(tmp_file.name, file_path)
# 	except:
# 		pass

def mkdir(path: str) -> Path:
    target_path = Path(path)
    target_path.mkdir(parents=True, exist_ok=True)
    return Path(path)

def write_file(file_path, data):
    with open(file_path, mode='w+', encoding='utf-8') as fs:
        fs.write(data)

# def mkdir(path):
# 	# 去除首位空格
# 	path = str(path).strip()
# 	# 去除尾部 \ 符号
# 	path = path.rstrip("\\")

# 	# 判断路径是否存在
# 	# 存在     True
# 	# 不存在   False
# 	isExists = os.path.exists(path)

# 	# 判断结果
# 	if not isExists:
# 		# 如果不存在则创建目录
# 		print(path+' 创建成功')
# 		# 创建目录操作函数
# 		os.makedirs(path)
# 		return True
# 	else:
# 		# 如果目录存在则不创建，并提示目录已存在
# 		#print(path+' 目录已存在')
# 		return False
	
def remove_files(folder_path):
    # 检查路径是否存在
    if not os.path.exists(folder_path):
        print(f"The folder {folder_path} does not exist.")
        return

    # 遍历文件夹中的所有文件和子文件夹
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        
        try:
            # 如果是文件，则删除
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            # 如果是文件夹，则递归删除其内容并删除文件夹
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print(f"Failed to delete {file_path}. Reason: {e}")


import signal
import sys
 
def on_ctrlc(cb):
    # 自定义信号处理函数
    def my_handler(signum, frame):
        global stop
        stop = True
        print("程序被手动终止.")
        cb()
        sys.exit()
    
    
    # 设置相应信号处理的handler
    signal.signal(signal.SIGINT, my_handler)    #读取Ctrl+c信号
   
def clear_input_buffer():
    if sys.stdin.isatty():
        try:
            import termios
            termios.tcflush(sys.stdin, termios.TCIOFLUSH)
        except ImportError:
            # fallback for Windows
            import msvcrt
            while msvcrt.kbhit():
                msvcrt.getch()

    # 调用该函数以清空输入缓冲区