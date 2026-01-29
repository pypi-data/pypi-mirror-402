class solution:
    def rebuild(self,str="python",x=1,rebuildChar=','):
        return rebuildChar.join(str[i:i+x] for i in range(0,len(str),x));
    def findChar(self,str,findstr,beginstart=0,start=0,end=-1):
        result = str.find(findstr,start,end)
        if(end < 0):
            end = len(str)
        if start >= end or result == -1 or findstr == '':
            return []
        results = self.findChar(str,findstr,beginstart,result + 1,end)
        results.append(result)
        if(start == beginstart):
            results.reverse()
        return results;
    def countChar(self,str,targetStr):
        return str.count(targetStr,0,len(str))
if __name__ == '__main__':
    sol = solution();
    print(sol.rebuild(x=4,rebuildChar=' '))
    print(sol.findChar("I like pytho python python````` python","```"))
    print(sol.countChar("I like pytho python python python","python"))