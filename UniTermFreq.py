# -*- coding: utf-8 -*-
#
# UniTermFreq.py
#   using suffix array and LCP to count term frequency for unicode text
#   Copyright (C) 2009 T.C. Chou (tcchou.at.tcchou.dot.org)
#
# modified from mksa2.py : Suffix Array の構築 (Larsson-Sadakane 法)
#   Copyright (C) 2007 Makoto Hiroi
#
import time, sys, os.path, string
from array import *

class UniTermFreq:
    def __init__(self,charset='utf-8',overlap=0,limit=10):
        self.limit = limit
        self.overlap = overlap
        self.charset = charset
        self.buff = None
        self.data_size = 0
        self.elmap = {}
        self.elidx = 0
        self.idx = None
        self.rank = None
        
    def getElementIdx(self, el):
        if not self.elmap.has_key(el):
            self.elmap[el] = self.elidx
            self.elidx += 1
        return self.elmap[el]
    
    def sortElementMap(self):
        if len(self.elmap)>0:
            idx = 0
            sorted_keys = self.elmap.keys() # aviod the end char of string
            sorted_keys.remove(u'\0')
            sorted_keys.sort()
            for _ in sorted_keys:
                ## print _
                self.elmap[_] = idx
                idx += 1

    def fromunicode(self, s):
        del self.buff
        self.data_size = 0
        if s is not None and type(s) is unicode:
            self.buff = array('u')
            self.buff.fromunicode(s)
            self.data_size = len(s)
            self.buff.append(u'\0')            

    # ランクの取得
    def getrank(self, x):
        if x < self.data_size: return self.rank[x]
        return -1

    # ソート用比較関数
    def compare(self, x, y, n):
        for i in xrange(n, self.data_size - max(x, y), n):
            r = self.rank[x + i] - self.rank[y + i]
            if r != 0: return r
        return y - x
    
    # 挿入ソート
    def insert_sort(self, low, high, n):
        for i in xrange(low + 1, high + 1):
            temp = self.idx[i]
            j = i - 1
            while j >= low and self.compare(temp, self.idx[j], n) < 0:
                self.idx[j + 1] = self.idx[j]
                j -= 1
            self.idx[j + 1] = temp
        # ランクの設定
        for x in xrange(low, high + 1):
            self.rank[self.idx[x]] = x
            self.idx[x] = -1

    # 枢軸の選択
    def select_pivot(self, low, high, n):
        m = (high - low) / 4
        a = self.getrank(self.idx[low + m] + n)
        b = self.getrank(self.idx[low + m * 2] + n)
        c = self.getrank(self.idx[low + m * 3] + n)
        if a > b:
            tmp = a
            a = b
            b = tmp
        if b > c:
            b = c
            if a > b: b = a
        return b

    # マルチキークイックソート
    def mqsort(self, low, high, n = 0):
        if high - low <= self.limit:
            self.insert_sort(low, high, n)
            return
        print "=================="
        # 枢軸
        # p = getrank(idx[(low + high)/2] + n)
        p = self.select_pivot(low, high, n)
        # 4 分割
        i = m1 = low
        j = m2 = high
        while True:
            print "i: %d, j: %d" % (i, j)
            while i <= j:
                k = self.getrank(self.idx[i] + n) - p
                if k > 0: break
                if k == 0:
                    self.idx[i], self.idx[m1] = self.idx[m1], self.idx[i]
                    m1 += 1
                i += 1
            while i <= j:
                k = self.getrank(self.idx[j] + n) - p
                if k < 0: break
                if k == 0:
                    self.idx[j], self.idx[m2] = self.idx[m2], self.idx[j]
                    m2 -= 1
                j -= 1
            if i > j: break
            self.idx[i], self.idx[j] = self.idx[j], self.idx[i]
            i += 1
            j -= 1
        # 等しいデータを中央に集める
        for k in xrange(min(m1 - low, i - m1)):
            self.idx[low + k], self.idx[j - k] = self.idx[j - k], self.idx[low + k]
        m1 = low + (i - m1)
        for k in xrange(min(high - m2, m2 - j)):
            self.idx[i + k], self.idx[high - k] = self.idx[high - k], self.idx[i + k]
        m2 = high - (m2 - j) + 1
        # < の部分をソード
        if low <= m1 - 1: self.mqsort(low, m1 - 1, n)
        # 等しいデータのランクを更新
        if m2 > m1:
            if m2 - m1 == 1:
                # ソート完了
                self.rank[self.idx[m1]] = m1
                self.idx[m1] = -1
            else:
                r = m2 - 1
                for x in xrange(m1, m2): self.rank[self.idx[x]] = r
        # > の部分をソート
        if m2 <= high: self.mqsort(m2, high, n)


    def suffix_sort(self):
        # 分布数えソート
        SIZE = self.elidx * self.elidx
        ## print "SIZE: %d" % SIZE
        count = [0] * SIZE
        count_sum = [0] * (SIZE + 1)
        for x in xrange(self.data_size):
            count[(self.elmap[self.buff[x]] * self.elidx) + self.elmap[self.buff[x + 1]]] += 1
        ##print count
        ##print '*'*50
        for x in xrange(1, SIZE + 1):
            count_sum[x] = count[x - 1] + count_sum[x - 1]
        for x in xrange(1, SIZE):
            count[x] += count[x - 1]
        for x in xrange(self.data_size - 1, -1, -1):
            c = (self.elmap[self.buff[x]] * self.elidx) + self.elmap[self.buff[x + 1]]
            count[c] -= 1
            self.idx[count[c]] = x
            self.rank[x] = count_sum[c + 1] - 1
        # ランクを使って段階的にソートする
        n = 2
        while n < self.data_size:
            low = 0
            flag = True
            while low < self.data_size:
                temp = low
                # ソート済みの区間をスキップ
                while temp < self.data_size and self.idx[temp] < 0: temp -= self.idx[temp]
                if low < temp:
                    self.idx[low] = -(temp - low)
                    low = temp
                # 区間のソート
                if low < self.data_size:
                    high = self.rank[ self.idx[low] ]
                    self.mqsort(low, high, n)
                    low = high + 1
                    flag = False
            if flag: break
            n *= 2
        # idx を復元
        for x in xrange(self.data_size): self.idx[self.rank[x]] = x
        ## print self.idx
        
    def makeSuffixArray(self):
        del self.idx
        del self.rank
        self.idx = array('l')
        self.rank = array('l')
        self.elmap.clear()
        self.elidx = 0
        if self.data_size <= 0: return

        for ii in self.buff: self.getElementIdx(ii)
        self.sortElementMap()

        for _ in xrange(self.data_size):
            self.idx.append(0)
            self.rank.append(0)

        self.suffix_sort()

    def isOverlap(self, last, curr, n):
        if last < curr:
            return last + n - 1 >= curr
        elif last > curr:
            return curr + n - 1 >= last
        else:
            return False

    def markOccupied(self, lcp_map, bgn, n):
        cur_blk = self.occupied[bgn:bgn+n]
        spc_blk = 0
        for _ in cur_blk:
            if _ == 0: spc_blk += 1
            else: break
            
        if spc_blk == n:
            # normal occupying
            for _ in xrange(bgn, bgn + n): self.occupied[_] = bgn + n
            return True
        else:
            print self.occupied
            marked_end = cur_blk[spc_blk]
            marked_bgn = bgn
            if spc_blk==0:
                for _ in xrange(bgn,-1,-1): 
                    if self.occupied[_]!=marked_end: break
                    marked_bgn = _
            else:
                marked_bgn += spc_blk
            print "bgn: %d, mbgn: %d, mend: %d, spc_blk: %d, n: %d" % (bgn, marked_bgn, marked_end, spc_blk, n)
                
            if marked_end-marked_bgn < n and (self.overlap and marked_bgn>=bgn):
                for _ in xrange(marked_bgn, marked_end): self.occupied[_] = 0
                marked = self.buff[marked_bgn:marked_end].tounicode()
                print "\t\tmarked: "+marked                
                if not self.overlap: # allow overlap
                    lcp_map[marked] -= 1
                    if lcp_map[marked]<=0: lcp_map.pop(marked)
                for _ in xrange(bgn, bgn + n): self.occupied[_] = bgn + n
                return True        
            else:
                if self.overlap: # allow overlap
                    for _ in xrange(marked_bgn, marked_end): self.occupied[_] = 0            
                    for _ in xrange(bgn, bgn + n): self.occupied[_] = bgn + n
                    return True
                else:
                    return False
            
    def lcp2(self):
        last_idx = 0
        last_str = None
        last_len = 0
        last_cnt = 0
        lcp_map = {}
        self.occupied = [0] * len(self.buff)
        self.occupied_lst = [[] for i in xrange(self.data_size)]
        for _ in self.idx:
            curr_idx = _
            curr_str = self.buff[_:].tounicode()
            curr_len = len(curr_str)
            print "* %s : %s" % (last_str, curr_str)
            if last_str is not None and curr_str is not None:
                lcp_idx = 0
                for _ in xrange(len(last_str)>len(curr_str) and len(curr_str) or len(last_str)):
                    if last_str[_] != curr_str[_]: break
                    lcp_idx += 1
                lcp_str = last_str[:lcp_idx]                
                if len(lcp_str)>1:
                    for _ in xrange(len(lcp_str),1,-1):
                        print "pending lcp_str: %s" % lcp_str[:_]
                        #if not self.isOverlap(last_idx, curr_idx, _):
                        print "lcp_str: %s" % lcp_str[:_]
                        if not lcp_map.has_key(lcp_str[:_]): lcp_map[lcp_str[:_]] = 0
                        if last_cnt==0 and self.markOccupied(lcp_map, last_idx, _):
                            lcp_map[lcp_str[:_]] += 1
                            last_cnt = 1
                        else:
                            last_cnt = 0
                        if self.markOccupied(lcp_map, curr_idx, _): lcp_map[lcp_str[:_]] += 1
                        if lcp_map[lcp_str[:_]]==0: lcp_map.pop(lcp_str[:_])
                        if not self.overlap: break # allow overlap
            last_str = curr_str
            last_idx = curr_idx
            last_len = curr_len
        for _ in self.occupied_lst:
            del _
        del self.occupied_lst
        return lcp_map

    def isInterlace(self, last_idx, curr_idx, n):
        if (last_idx<curr_idx and last_idx + n -1 >= curr_idx) or (curr_idx<last_idx and curr_idx + n -1 >= last_idx): return True
        else: return False


    def lcpStr(self, str1, str2, limited=-1):
        if str1 is None or str2 is None: return None
        lcp_idx = 0
        for _ in xrange(len(str1)>len(str2) and len(str2) or len(str1)):
            if str1[_] != str2[_] or (limited!=-1 and lcp_idx>=limited): break
            lcp_idx += 1
        return str1[:lcp_idx]              

    def lcp(self):
        if len(self.idx)==0: return
        lcp_map = {}
        lcp_ary = [0]*self.data_size
        last_idx = self.idx[0]
        curr_idx = 0
        ##print self.buff.tounicode()
        ##print "%d: %s" % (last_idx, self.buff[last_idx:].tounicode().encode('utf-8'))
        for idx_i in xrange(1, self.data_size):
            curr_idx = self.idx[idx_i]
            last_str = self.buff[last_idx:].tounicode()
            curr_str = self.buff[curr_idx:].tounicode()
            ##print "%d: %s" % (curr_idx,curr_str.encode('utf-8'))
            lcp_ary[idx_i] = len(self.lcpStr(last_str, curr_str))
            last_idx = curr_idx
        ##print lcp_ary
        for _ in xrange(self.data_size-1):
            ##print "*"*50+" "+str(_)
            ##print lcp_ary
            if lcp_ary[_+1]>1 and lcp_ary[_+1] > lcp_ary[_]: 
                if self.isInterlace(self.idx[_], self.idx[_+1], lcp_ary[_+1]):
                    ##print "!"*10
                    if lcp_ary[_]<=1: lcp_ary[_]=0
                    lcp_ary[_+1] = lcp_ary[_]
                    nn = lcp_ary[_]
                else:
                    ##print "?"*10
                    lcp_ary[_]=lcp_ary[_+1]
                    nn = lcp_ary[_+1]
                for ee in xrange(_,-1,-1):
                    s1 = self.buff[self.idx[ee]:].tounicode()
                    s2 = self.buff[self.idx[ee+1]:].tounicode()
                    lcp_s1_s2 = self.lcpStr(s1,s2,nn)
                    lcp_s1_s2_len = len(lcp_s1_s2)
                    if lcp_s1_s2_len<=1: break  # ignore len <= 1
                    ##print "\t\t(%d:ee=%d) s1: %s, s2: %s ... lcp=%s" % (self.idx[ee], ee, s1, s2, lcp_s1_s2)
                    for ll in xrange((nn==-1 and lcp_ary[ee] or nn), 0, -1):
                        if not self.isInterlace(self.idx[ee], self.idx[ee+1], ll): break
                    if ll==1: lcp_ary[ee+1]=0
                    else: lcp_ary[ee+1]=ll
            elif lcp_ary[_]<=1:
                lcp_ary[_]=0
        if lcp_ary[self.data_size-1]<=1: lcp_ary[self.data_size-1] = 0
        ##print lcp_ary
        lcp_stk1 = [None]
        lcp_stk2 = [None]
        tmp_map = {}
        def lcp_str_in_ary(bgn, n):
            return self.buff[bgn:bgn+n].tounicode()
        def print_out(m):
            s=''
            for _ in m: s += _.encode('utf-8') + ":"+str(m[_]) + ","
            return s[:-1]
        last_str = None
        curr_str = None
        for ii in xrange(self.data_size):
            if lcp_ary[ii]!=0:
                curr_str = lcp_str_in_ary(self.idx[ii], lcp_ary[ii])
                lcp_str = self.lcpStr(last_str, curr_str)
                #print "%s %s" % (curr_str, lcp_str)
                #print "\t\t1. %s %s" % (repr(lcp_stk1), lcp_str)
                if lcp_str is None or len(lcp_str)<=1:
                    lcp_map[curr_str]=0
                    for _ in xrange(1, len(lcp_stk1)): lcp_stk1.pop()
                elif curr_str not in lcp_stk2:
                    lcp_map[curr_str]=0
                    if lcp_stk1[-1]!=lcp_str and lcp_str!=curr_str: lcp_stk1.append(lcp_str)
                    if lcp_str not in lcp_stk2: 
                        lcp_map[lcp_str]=0
                        for _ in xrange(len(lcp_stk2)-1,0,-1):
                            if lcp_str==lcp_stk2[_][:len(lcp_str)]: lcp_map[lcp_str] += lcp_map[lcp_stk2[_]]
                            else: break

                if lcp_stk2[-1]!=curr_str: lcp_stk2.append(curr_str)
                if lcp_str is not None and lcp_str==curr_str[:len(lcp_str)]:# and ii!=self.data_size-1:
                    for _ in xrange(len(lcp_stk1)-1,0,-1):
                        if lcp_stk1[_]==curr_str[:len(lcp_stk1[_])]:
                            lcp_map[lcp_stk1[_]] += 1
                lcp_map[curr_str] += 1
                #print "\t\t2a. %s" % repr(lcp_stk1)
                #print "\t\t2b. %s" % repr(lcp_stk2)
                #print "\t\t"+print_out(lcp_map)
            else:
                curr_str = lcp_str = None
                #print "%s %s" % (curr_str, lcp_str)

            last_str = curr_str
        
        return lcp_map

def test_term_freq():
    u"""
    >>> tf = UniTermFreq()
    >>> tf.fromunicode(u'baacbaacbaa')
    >>> tf.makeSuffixArray()
    >>> lcp_map = tf.lcp()
    >>> for _ in lcp_map:  print "* %s: %d" % (_, lcp_map[_])
    * aa: 3
    * cbaa: 2
    * baa: 2

    >>> tf.fromunicode(u'看試試測看試看試試試試試試')
    >>> tf.makeSuffixArray()
    >>> lcp_map = tf.lcp()
    >>> for _ in lcp_map:  print "* %s: %d" % (_, lcp_map[_])
    * 看試試: 2
    * 看試: 3
    * 試試: 4
    """
    
if __name__ == "__main__":
    import doctest
    doctest.testmod()
