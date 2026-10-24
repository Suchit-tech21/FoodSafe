class Node:
    def __init__(self,data,next_node=None): self.data=data; self.next=next_node
class LinkedList:
    def __init__(self): self.head=None; self.size=0
    def append(self,data):
        n=Node(data); self.size+=1
        if not self.head:self.head=n;return
        cur=self.head
        while cur.next:cur=cur.next
        cur.next=n
    def to_list(self):
        out=[];cur=self.head
        while cur:out.append(cur.data);cur=cur.next
        return out
