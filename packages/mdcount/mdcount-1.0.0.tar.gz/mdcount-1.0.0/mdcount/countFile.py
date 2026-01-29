import os
import re
from .stringOp import solution


class fileSearcher:
    def __init__(self,searchMenu=".",searchFile=["md","pdf"],ignore_dirName=["node_modules",".git"]):
        self.searchMenu = searchMenu
        self.searchFile = searchFile
        self.ignore_dirName = ignore_dirName
    def AllFiles(self,thePath="",ignore=False,searchAll=False):
        if(thePath == ""):
            thePath = self.searchMenu
        theResult = []
        currentContent = os.listdir(thePath)
        if(currentContent == []):
            return []
        thePathAdds = thePath
        for item in currentContent:
            fullPath = os.path.join(thePath,item)
            if os.path.isdir(fullPath) and (ignore == False or (ignore == True and item not in self.ignore_dirName)) :
                theResult.extend(self.AllFiles(thePath=fullPath,ignore=ignore,searchAll=searchAll))
            elif (os.path.isdir(fullPath) == False and searchAll == True):
                theResult.append(fullPath)
            elif (os.path.isdir(fullPath) == False and searchAll == False):
                if item.split('.')[-1] in self.searchFile:
                    theResult.append(fullPath)
            else:
                continue
        return theResult

class fileCounter:
    def __init__(self,fileList,countList=["md"],mdCountCode=False,language="Chinese"):
        self.__fileList = fileList
        self.__supportType = ["md","txt"]
        self.__countList = countList
        self.__mdCountCode = mdCountCode
        self.__language = language
    
    def setFileList(self,fileList):
        self.__fileList = fileList

    def setCountList(self,countList):
        self.__countList = countList

    def getCountList(self):
        return self.__countList

    def getFileList(self):
        return self.__fileList

    def getSupportType(self):
        return self.__supportType

    @staticmethod
    def __tagPosition(Allposition):
        start = -1
        end = -1
        for index,item in enumerate(Allposition):
            if item == Allposition[index - 1] + 1:
                start = index - 1;
            if start !=  -1 and item != Allposition[index - 1] + 1:
                end = index
                if(end + 1 < len(Allposition) and Allposition[end + 1] != Allposition[end] + 1):
                    del Allposition[start:end+1]
                start = -1
                end = -1

    @staticmethod
    def __markdownMethod(self,file):
        skips = ['.png','.jpg']
        result = []
        AllCount = 0
        with open(file,'r',encoding='utf-8') as f:
            f.seek(0)
            flagCode = 0
            sol = solution()
            for line in f:
                # 消除\n,\r
                line = line.replace("\n","")
                line = line.replace("\r","")
                flag = 0

                # 处理行内代码块和代码块
                if self.__mdCountCode == False:
                    if "```" in line or "~~~" in line:
                        ExtraCount = 0
                        AllPosition = sol.findChar(line,"```")
                        if(len(AllPosition)>1):
                            self.__tagPosition(AllPosition)
                            index = 0
                            while index+1 < len(AllPosition):
                                line = line[:AllPosition[index] - ExtraCount] + line[AllPosition[index+1] - ExtraCount:]
                                ExtraCount = AllPosition[index + 1] + 1 - AllPosition[index]
                                index += 2
                        else:
                            flagCode = 1 - flagCode
                    if flagCode == 1:
                            continue
                for skip in skips:
                    if skip in line:
                        flag == 1
                if flag == 1:
                    continue

                result.append(line)

                # 处理需要替换的前缀
                startstr = ["# ","## ","### ","#### ","##### ","###### ",
                             ">","+ ","- "]
                for start in startstr:
                    if line.startswith(start):
                        line = line.replace(start,"",1)
                        break

                # 处理需要删除的字符
                delstr = ["*","**","[","]","(",")"]
                for dels in delstr:
                    if dels in line:
                        line = line.replace(dels,"")
                # 关键修改：统计单词/字数，而不是字符数
                # 1. 统计中文字符（每个汉字算1个字）
                chinese_count = sum(1 for char in line if '\u4e00' <= char <= '\u9fff')

                # 2. 统计英文单词（使用正则表达式匹配单词）
                # 单词定义：连续的字母字符，可以包含数字但不以数字开头
                english_words = re.findall(r'\b[a-zA-Z][a-zA-Z0-9]*\b', line)
                english_count = len(english_words)

                # 3. 对于混合单词（如"Python3"、"C++"等），可以额外处理
                # 这里我们先使用简单规则

                # 总字数 = 中文字数 + 英文单词数
                line_word_count = chinese_count + english_count
                AllCount += line_word_count
        return AllCount




    @staticmethod
    def __txtMethod(file):
        with open(file,"r") as f:
            AllCount = 0
            for line in f:
                line.replace("\n","")
               # 关键修改：统计单词/字数，而不是字符数
               # 1. 统计中文字符（每个汉字算1个字）
                chinese_count = sum(1 for char in line if '\u4e00' <= char <= '\u9fff')

               # 2. 统计英文单词（使用正则表达式匹配单词）
               # 单词定义：连续的字母字符，可以包含数字但不以数字开头
                english_words = re.findall(r'\b[a-zA-Z][a-zA-Z0-9]*\b', line)
                english_count = len(english_words)

               # 3. 对于混合单词（如"Python3"、"C++"等），可以额外处理
               # 这里我们先使用简单规则

               # 总字数 = 中文字数 + 英文单词数
                line_word_count = chinese_count + english_count
                AllCount += line_word_count
        return AllCount
         
    def __switchSupport(self,fileType,file):
        if fileType == "md":
            return self.__markdownMethod(self,file)
        if fileType == "txt":
            return self.__txtMethod(file)
    def count(self,countAll=False):
        AllCount = 0
        for file in self.__fileList:   
            fileType = file.split('.')[-1]
            if fileType in self.__supportType:
                if(countAll == True or (countAll == False and fileType in self.__countList)):
                    fileCount = self.__switchSupport(fileType,file)
                    if(self.__language == "English"):
                        print("currentFile : "  + file + "，the count is : {0}".format(fileCount))
                    else:
                        print("当前文件："  + file + "，文件字数为：{0}".format(fileCount))
                    AllCount += fileCount
                else:
                    continue
            else:
                print(file + ": 目前暂不支持该类型的字数统计")
                continue
        return AllCount

def countFile(searchMenu,handleFile,language="Chinese",mdCountCode=False):
    searcher = fileSearcher(searchMenu,handleFile)
    fileList = searcher.AllFiles(ignore=True,searchAll=False)
    counter = fileCounter(fileList,countList=handleFile,language=language,mdCountCode=mdCountCode)
    if language == "English":
        print("the count of Files is：", counter.count())
    else:
        print("统计总字数为：" ,counter.count())