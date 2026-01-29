# 文件字数统计工具
## 支持文件类型
目前仅支持markdown(.md)和txt(.txt)文件

## 使用方法
1. 导入countFile函数
2. 调用countFile函数 
> 参数1：传入您的文件夹目录位置
>
> 参数2：传入您的文件类型
> 
> 可选参数
> 1. language，默认为中文,language="English"可切换为英文
> 2. mdCountCode：(True/False)是否统计代码，默认为False
```python
from mdcount.countFile import countFile
countFile("../MDCount", ["md"])
```

## 目前版本
1.0.0
参考资料：[使用Python读取markdown文件并统计字数
](https://icyhunter.blog.csdn.net/article/details/128424955)

-----

# File Word Count Tool
## Supported File Types
Currently only supports Markdown (.md) and plain text (.txt) files.

## How to Use
1. Import the countFile function.

2. Call the countFile function.

> Parameter 1: The path to your target directory.
> 
> Parameter 2: The list of file extensions you wish to count.
>
> Optional parameter: 
> 1. language, defaults to Chinese. Use language="English" to switch to English output.
> 2. is count code(True/False)? , defaults to False.
~~~python
from mdcount.countFile import countFile
countFile("../MDCount", ["md"])
~~~

## Current Version
1.0.0
Reference: [使用Python读取markdown文件并统计字数
](https://icyhunter.blog.csdn.net/article/details/128424955)

