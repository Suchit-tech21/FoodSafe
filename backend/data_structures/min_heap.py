class MinHeap:
    def __init__(self): self.heap=[]
    def insert(self,item):
        self.heap.append(item); self._up(len(self.heap)-1)
    def _up(self,i):
        while i:
            p=(i-1)//2
            if self.heap[p][0] <= self.heap[i][0]: break
            self.heap[p],self.heap[i]=self.heap[i],self.heap[p]; i=p
    def _down(self,i):
        n=len(self.heap)
        while True:
            l,r=2*i+1,2*i+2; m=i
            if l<n and self.heap[l][0]<self.heap[m][0]: m=l
            if r<n and self.heap[r][0]<self.heap[m][0]: m=r
            if m==i: break
            self.heap[i],self.heap[m]=self.heap[m],self.heap[i]; i=m
    def peek_min(self): return self.heap[0] if self.heap else None
    def extract_min(self):
        if not self.heap:return None
        out=self.heap[0]; last=self.heap.pop()
        if self.heap:self.heap[0]=last; self._down(0)
        return out
    def heapify(self,items):
        self.heap=list(items)
        for i in range(len(self.heap)//2-1,-1,-1): self._down(i)
