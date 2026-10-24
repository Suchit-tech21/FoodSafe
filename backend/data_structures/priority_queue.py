import heapq
class PriorityQueue:
    def __init__(self): self.heap=[]; self._seq=0
    def push(self,score,item):
        self._seq+=1; heapq.heappush(self.heap,(-score,self._seq,item))
    def pop(self): return heapq.heappop(self.heap)[2] if self.heap else None
    def ordered(self): return [x[2] for x in sorted(self.heap)]
    def __len__(self): return len(self.heap)
