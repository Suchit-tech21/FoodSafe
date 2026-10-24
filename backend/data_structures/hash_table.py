class HashTable:
    def __init__(self,size=53): self.size=size; self.buckets=[[] for _ in range(size)]
    def _idx(self,key): return hash(key)%self.size
    def insert(self,key,value):
        b=self.buckets[self._idx(key)]
        for i,(k,_) in enumerate(b):
            if k==key:b[i]=(key,value);return
        b.append((key,value))
    def search(self,key):
        for k,v in self.buckets[self._idx(key)]:
            if k==key:return v
        return None
