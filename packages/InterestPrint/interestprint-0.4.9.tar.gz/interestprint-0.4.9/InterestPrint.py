"""InterestPrint 库
作者:袁窦涵
邮箱:w111251@outlook.com"""
import sys
import ctypes
import getpass
import string
import ast
from string import Template
from ctypes import wintypes
from typing import Any
meow_print = None
MeowPrint = None
__version__ = "0.4.9"
show_welcome = False
if show_welcome:
    print("""Thanks for using InterestPrint!
    this project in pypi: https://pypi.org/project/InterestPrint/
    now version: {}""".format(__version__), flush=True)
    __import__("time").sleep(0.3)
    __import__("os").system("cls") if sys.platform == "win32" else __import__("os").system("clear")                                                                                           
class COORD(ctypes.Structure):
    """手动定义控制台坐标结构体（替代 wintypes.COORD）"""
    _fields_ = [("X", wintypes.SHORT), ("Y", wintypes.SHORT)]

class SMALL_RECT(ctypes.Structure):
    """手动定义控制台矩形区域结构体（替代 wintypes.SMALL_RECT）"""
    _fields_ = [("Left", wintypes.SHORT), ("Top", wintypes.SHORT),
                ("Right", wintypes.SHORT), ("Bottom", wintypes.SHORT)]
_USE_ANSI = False
_CONSOLE_HANDLE = None
_DEFAULT_CONSOLE_ATTR = None
WIN_FG_COLORS = {
    'black': 0x00,    
    'red': 0x04,      
    'green': 0x02,    
    'yellow': 0x06,   
    'blue': 0x01,     
    'purple': 0x05,   
    'cyan': 0x03,     
    'white': 0x07,    
}
WIN_BG_COLORS = {
    'black': 0x00,    
    'red': 0x40,      
    'green': 0x20,    
    'yellow': 0x60,   
    'blue': 0x10,     
    'purple': 0x50,   
    'cyan': 0x30,     
    'white': 0x70,    
}
ANSI_FG_COLORS = {
    'black': 30, 'red': 31, 'green': 32, 'yellow': 33,
    'blue': 34, 'purple': 35, 'cyan': 36, 'white': 37,
}
ANSI_BG_COLORS = {
    'black': 40, 'red': 41, 'green': 42, 'yellow': 43,
    'blue': 44, 'purple': 45, 'cyan': 46, 'white': 47,
}
def _init():
    """
    库初始化方法：自动检测 Windows 版本，选择兼容方案
    - Win10+：启用 ANSI 转义码
    - WinXP-Win8.1：使用 kernel32.dll API 修改控制台样式
    """
    global _USE_ANSI, _CONSOLE_HANDLE, _DEFAULT_CONSOLE_ATTR
    if sys.platform != "win32":
        _USE_ANSI = True
        return
    win_ver = sys.getwindowsversion()
    nt_major, nt_minor, nt_build = win_ver.major, win_ver.minor, win_ver.build    
    if (nt_major, nt_minor) == (10, 0) and nt_build >= 15063:
        _USE_ANSI = True
        try:
            kernel32 = ctypes.WinDLL("kernel32.dll", use_last_error=True)
            handle = kernel32.GetStdHandle(-11)  
            mode = wintypes.DWORD()
            kernel32.GetConsoleMode(handle, ctypes.byref(mode))
            mode.value |= 0x0004
            kernel32.SetConsoleMode(handle, mode)
        except:
            _USE_ANSI = False
    else:
        _USE_ANSI = False    
    if not _USE_ANSI:
        try:
            kernel32 = ctypes.WinDLL("kernel32.dll", use_last_error=True)
            
            _CONSOLE_HANDLE = kernel32.GetStdHandle(-11)
            if _CONSOLE_HANDLE == wintypes.HANDLE(-1):
                raise OSError("获取控制台句柄失败")            
            class CONSOLE_SCREEN_BUFFER_INFO(ctypes.Structure):
                _fields_ = [
                    ("dwSize", COORD),
                    ("dwCursorPosition", COORD),
                    ("wAttributes", wintypes.WORD),
                    ("srWindow", SMALL_RECT),
                    ("dwMaximumWindowSize", wintypes.COORD)
                ]            
            csbi = CONSOLE_SCREEN_BUFFER_INFO()
            kernel32.GetConsoleScreenBufferInfo(_CONSOLE_HANDLE, ctypes.byref(csbi))
            _DEFAULT_CONSOLE_ATTR = csbi.wAttributes
        except:
            _CONSOLE_HANDLE = None
            _DEFAULT_CONSOLE_ATTR = None
class tstr(str):
    """
    自定义字符串类，添加t-string风格安全插值方法
    """
    def tformat(self, *args, **kwargs) -> str:
        """
        字符串t-string风格安全插值，支持位置参数($0/$1)和关键字参数(${name})
        \$ 转义为普通 $，兼容Python全版本，变量缺失不报错
        """
        tpl_str = self.replace("\\$", "$$")
        ctx = {str(i): val for i, val in enumerate(args)}
        ctx.update(kwargs)
        if sys.version_info >= (3, 14):
            try:
                t_expr = f"t{repr(tpl_str)}"
                t_string = ast.literal_eval(t_expr)
                def safe_get(key):
                    return ctx.get(key, f"${{{key}}}" if key in ctx else f"${key}")
                return t_string.format_map(__builtins__['type']('SafeDict', (), {'__getitem__': lambda _, k: safe_get(k)})())
            except Exception as e:
                return f"[t-string解析失败] {e}"
        else:
                return Template(tpl_str).safe_substitute(ctx)
def _set_console_color(fg_color: str, bg_color: str = None, bold: bool = False):
    """
    设置控制台文本颜色
    :param fg_color: 前景色名称
    :param bg_color: 背景色名称（可选）
    :param bold: 是否加粗（高亮度）
    """
    if not _CONSOLE_HANDLE or not _DEFAULT_CONSOLE_ATTR:
        return
    try:
        kernel32 = ctypes.WinDLL("kernel32.dll", use_last_error=True)        
        fg = WIN_FG_COLORS.get(fg_color.lower(), WIN_FG_COLORS['white'])
        if bold:
            fg |= 0x08  
        bg = WIN_BG_COLORS.get(bg_color.lower(), WIN_BG_COLORS['black']) if bg_color else 0x00
        color_attr = fg | bg
        kernel32.SetConsoleTextAttribute(_CONSOLE_HANDLE, color_attr)
    except:
        pass
def _restore_console_default():
    """恢复控制台默认样式"""
    if not _CONSOLE_HANDLE or not _DEFAULT_CONSOLE_ATTR:
        return
    try:
        kernel32 = ctypes.WinDLL("kernel32.dll", use_last_error=True)
        kernel32.SetConsoleTextAttribute(_CONSOLE_HANDLE, _DEFAULT_CONSOLE_ATTR)
    except:
        pass
def colorful_print(*objects: Any, 
                  color: str = 'white', 
                  bold: bool = False, 
                  end: str = '\n', 
                  sep: str = ' ',
                  file= sys.stdout,
                  flush: bool = False) -> None:
    """
    带颜色打印
    :param objects: 要打印的内容（可变参数）
    :param color: 字体颜色,可选:black/red/green/yellow/blue/purple/cyan/white
    :param bold: 是否加粗,默认False
    :param end: 结尾字符，默认换行
    :param sep: 多个参数的分隔符，默认空格
    :param file: 输出文件，默认sys.stdout
    :param flush: 是否立即刷新输出，默认False
    """
    if color.lower() not in WIN_FG_COLORS:
        raise ValueError(f"颜色必须是以下之一：{list(WIN_FG_COLORS.keys())}")
    content = sep.join(map(str, objects))
    if _USE_ANSI:
        fg_code = ANSI_FG_COLORS.get(color.lower(), ANSI_FG_COLORS['white'])
        style = 1 if bold else 0
        ansi_prefix = f'\033[{style};{fg_code}m'
        ansi_suffix = '\033[0m'
        print(f"{ansi_prefix}{content}{ansi_suffix}", end=end, sep=sep, file=file, flush=flush)
        return
    if not _USE_ANSI and _CONSOLE_HANDLE:
        
        _set_console_color(fg_color=color, bold=bold)
        
        print(content, end=end, sep=sep, file=file, flush=flush)
        
        _restore_console_default()
        return
    print(content, end=end, sep=sep, file=file, flush=flush)
ColorfulPrint = colorful_print
def front_back_print(*objects: Any, 
                   front: str = '^', 
                   back: str = '$', 
                   end: str = '\n', 
                   sep: str = ' ',
                   file= sys.stdout,
                   flush: bool = False) -> None:
    """
    可设置前后缀的打印
    :param objects: 要打印的内容（可变参数）
    :param front: 前缀（默认^）
    :param back: 后缀（\EQUALTOFRONT的意思是前后缀相同）
    :param end: 结尾字符，默认换行
    :param sep: 多个参数的分隔符，默认空格
    :param file: 输出文件，默认sys.stdout
    :param flush: 是否立即刷新输出，默认False
    """
    if back == r'\EQUALTOFRONT':
        back = front
    objects_str = sep.join(map(str, objects)) if objects else ''
    print(f"{front}{objects_str}{back}", end=end, sep=sep, file=file, flush=flush)
FrontBackPrint = front_back_print
def bg_colorful_print(*objects: Any, 
                    bg_color: str = 'black',
                    bold: bool = False, 
                    end: str = '\n', 
                    sep: str = ' ',
                    file= sys.stdout,
                    flush: bool = False,) -> None:
    """
    带背景色的花式打印
    :param objects: 要打印的内容（可变参数）
    :param bg_color: 背景颜色,可选:black/red/green/yellow/blue/purple/cyan/white
    :param bold: 是否加粗,默认False
    :param end: 结尾字符，默认换行
    :param sep: 多个参数的分隔符，默认空格
    :param file: 输出文件，默认sys.stdout
    :param flush: 是否立即刷新输出，默认False
    """
    if bg_color.lower() not in WIN_BG_COLORS:
        raise ValueError(f"背景颜色必须是以下之一：{list(WIN_BG_COLORS.keys())}")
    content = sep.join(map(str, objects))
    if _USE_ANSI:
        fg_code = ANSI_FG_COLORS['white']
        bg_code = ANSI_BG_COLORS.get(bg_color.lower(), ANSI_BG_COLORS['black'])
        style = 1 if bold else 0
        ansi_prefix = f'\033[{style};{fg_code};{bg_code}m'
        ansi_suffix = '\033[0m'
        print(f"{ansi_prefix}{content}{ansi_suffix}", end=end, sep=sep, file=file, flush=flush)
        return
    if not _USE_ANSI and _CONSOLE_HANDLE:
        _set_console_color(fg_color='white', bg_color=bg_color, bold=bold)
        print(content, end=end, sep=sep, file=file, flush=flush)
        _restore_console_default()
        return
    print(content, end=end, sep=sep, file=file, flush=flush)
BgColorfulPrint = bg_colorful_print
def fg_and_bg_colorful_print(*objects: Any, 
                         fg_color: str = 'white', 
                         bg_color: str = 'black',
                        end: str = '\n', 
                        sep: str = ' ',
                        file= sys.stdout,
                        flush: bool = False) -> None:
    """
    同时设置前景色和背景色
    :param objects: 要打印的内容（可变参数）
    :param fg_color: 前景色（字体色）
    :param bg_color: 背景色
    :param end: 结尾字符，默认换行
    :param sep: 多个参数的分隔符，默认空格
    :param file: 输出文件，默认sys.stdout
    :param flush: 是否立即刷新输出，默认False
    """
    if fg_color.lower() not in WIN_FG_COLORS:
        raise ValueError(f"前景色必须是以下之一：{list(WIN_FG_COLORS.keys())}")
    if bg_color.lower() not in WIN_BG_COLORS:
        raise ValueError(f"背景色必须是以下之一：{list(WIN_BG_COLORS.keys())}")
    content = sep.join(map(str, objects))
    if _USE_ANSI:
        fg_code = ANSI_FG_COLORS.get(fg_color.lower(), ANSI_FG_COLORS['white'])
        bg_code = ANSI_BG_COLORS.get(bg_color.lower(), ANSI_BG_COLORS['black'])
        ansi_prefix = f'\033[{fg_code};{bg_code}m'
        ansi_suffix = '\033[0m'
        print(f"{ansi_prefix}{content}{ansi_suffix}", end=end, sep=sep, file=file, flush=flush)
        return
    if not _USE_ANSI and _CONSOLE_HANDLE:
        _set_console_color(fg_color=fg_color, bg_color=bg_color)
        print(content, end=end, sep=sep, file=file, flush=flush)
        _restore_console_default()
        return
    print(content, end=end, sep=sep, file=file, flush=flush)
FgAndBgColorfulPrint = fg_and_bg_colorful_print
def print_then_clear(*objects: Any, 
                   show_time=1, 
                   color: str = 'white', 
                   bold: bool = False, 
                   end: str = '\n', 
                   sep: str = ' ',
                   file= sys.stdout,
                   flush: bool = False) -> None:
    """
    打印后清屏
    :param objects: 要打印的内容（可变参数）
    :param color: 字体颜色,可选:black/red/green/yellow/blue/purple/cyan/white
    :param bold: 是否加粗,默认False
    :param end: 结尾字符，默认换行
    :param sep: 多个参数的分隔符，默认空格
    :param file: 输出文件，默认sys.stdout
    :param flush: 是否立即刷新输出，默认False
    """
    colorful_print(*objects, color=color, bold=bold, end=end, sep=sep, file=file, flush=flush)
    __import__("time").sleep(show_time)
    if sys.platform == "win32":
        __import__("os").system("cls")
    else:
        __import__("os").system("clear")
PrintThenClear = print_then_clear
def enable_meow_print():
    """
    启用meow_print函数
    """
    global MeowPrint, meow_print
    if meow_print:
        raise RuntimeError("meow_print已启用")
    def meow_print(*text:Any, 
                  meow_count:int=1, 
                  end:str='\n', 
                  sep:str=' ', 
                  front:bool=True, 
                  back:bool=True,
                  file= sys.stdout,
                  flush: bool = False)->None:
        """
        喵喵喵打印
        :param text: 要打印的内容（可变参数）
        :param meow_count: 猫咪表情数量,默认1
        :param end: 结尾字符,默认换行
        :param sep: 多个参数的分隔符,默认空格
        :param front: 是否在前面打印表情,默认True
        :param back: 是否打印后面打印表情,默认True
        :param file: 输出文件，默认sys.stdout
        :param flush: 是否立即刷新输出，默认False
        """
        front_meow = '🐱' * meow_count if front else ''
        back_meow = '🐱' * meow_count if back else ''
        text_str = sep.join(map(str, text)) if text else ''
        print(f"{front_meow}{text_str}{back_meow}", end=end, sep=sep, file=file, flush=flush)
    MeowPrint = meow_print
EnableMeowPrint = enable_meow_print
def disable_meow_print():
    """
    禁用meow_print函数
    """
    global meow_print, MeowPrint
    if not meow_print:
        raise RuntimeError("meow_print未启用")
    meow_print, MeowPrint = None, None
DisableMeowPrint = disable_meow_print
def colorful_input(message: str,
                   is_pwd: bool = False,
                   color: str = 'white',
                   bold: bool = False,
                   prompt_suffix: str = ' ',  
                   end: str = '',  
                   flush: bool = True,  
                   pwd_warn: bool = True,  
                   return_strip: bool = True) -> str:  
    """
    彩色输入：输出彩色提示信息，支持普通输入和密码隐藏输入（增强版，多参数更灵活）
    :param message: 提示信息
    :param is_pwd: 是否为密码输入（隐藏输入内容），默认False
    :param color: 提示信息字体颜色，可选:black/red/green/yellow/blue/purple/cyan/white
    :param bold: 提示信息是否加粗，默认False
    :param prompt_suffix: 提示信息后缀（用于分隔提示和输入框，默认空格）
    :param end: 提示信息结尾符（默认空字符串，保持输入框紧跟提示信息）
    :param flush: 是否立即刷新提示信息（默认True，避免提示信息延迟显示）
    :param pwd_warn: 当getpass模块不可用时，是否输出降级警告（默认True）
    :param return_strip: 是否自动去除返回结果的首尾空白符（默认True，优化输入体验）
    :return: 用户输入的内容（处理后）
    """
    if color.lower() not in WIN_FG_COLORS:
        raise ValueError(f"颜色必须是以下之一：{list(WIN_FG_COLORS.keys())}")
    full_prompt = f"{message}{prompt_suffix}"
    if _USE_ANSI:
        fg_code = ANSI_FG_COLORS.get(color.lower(), ANSI_FG_COLORS['white'])
        style = 1 if bold else 0
        ansi_prefix = f'\033[{style};{fg_code}m'
        ansi_suffix = '\033[0m'
        print(f"{ansi_prefix}{full_prompt}{ansi_suffix}", end=end, flush=flush)
    else:
        if _CONSOLE_HANDLE:
            _set_console_color(fg_color=color, bold=bold)
            print(full_prompt, end=end, flush=flush)
            _restore_console_default()
        else:
            print(full_prompt, end=end, flush=flush)
    user_input = ""
    if is_pwd:
        try:
            import getpass
            user_input = getpass.getpass(prompt='')
        except ImportError:
            if pwd_warn:
                print("\n警告：getpass 模块不可用，密码将明文显示")
            user_input = input('')
    else:
        user_input = input('')
    if return_strip and isinstance(user_input, str):
        return user_input.strip()
    return user_input
fg_colorful_print = colorful_print
FgColorfulPrint = fg_colorful_print 


__all__ = ['colorful_print',
           'ColorfulPrint',
           'bg_colorful_print',
           'BgColorfulPrint', 
           'fg_and_bg_colorful_print',
           'FgAndBgColorfulPrint',
           'front_back_print',
           'FrontBackPrint', 
           'fg_colorful_print',
           'FgColorfulPrint', 
           'print_then_clear',
           'PrintThenClear', 
           'enable_meow_print',
           'EnableMeowPrint',
           'disable_meow_print',
           'DisableMeowPrint',
           'colorful_input',
           'tstr',
           ]
_init()
if __name__ == '__main__':
    colorful_print("这是红色加粗", color='red', bold=True)
    colorful_print("这是绿色常规", color='green')
    colorful_print("多参数", "测试", color='blue', sep='|')
    colorful_print("黄色结尾无换行", color='yellow', end='')
    print(" → 看，没换行～")
    bg_colorful_print("背景色测试（红色背景）", bg_color='red')
    fg_and_bg_colorful_print("前景红+背景绿测试", fg_color='red', bg_color='green')
    fg_colorful_print("别名功能测试（白色常规）")
    front_back_print("前后缀测试", front='*', back='\EQUALTOFRONT')
    print_then_clear("打印后清屏测试", show_time=3, color='green', bold=True)
    enable_meow_print()
    meow_print("Hello, World!",meow_count=5)
    disable_meow_print()
    password = colorful_input("请输入密码：", is_pwd=True, color='yellow')
    colorful_print(f"密码输入成功！{password=}", color='green')