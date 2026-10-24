import sys, unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'backend'))
from data_structures.min_heap import MinHeap
from data_structures.priority_queue import PriorityQueue
from data_structures.hash_table import HashTable
from data_structures.linked_list import LinkedList
from data_structures.sorting import merge_sort
class DSTests(unittest.TestCase):
 def test_min_heap(self):
  h=MinHeap();h.insert((3,'Sauce'));h.insert((1,'Milk'));h.insert((2,'Paneer'));self.assertEqual(h.peek_min()[1],'Milk');self.assertEqual(h.extract_min()[1],'Milk')
 def test_priority_queue(self):
  q=PriorityQueue();q.push(40,'low');q.push(90,'high');self.assertEqual(q.pop(),'high')
 def test_hash_and_list(self):
  h=HashTable();h.insert(1,'Green Leaf');self.assertEqual(h.search(1),'Green Leaf');l=LinkedList();l.append('A');l.append('B');self.assertEqual(l.to_list(),['A','B'])
 def test_sort(self): self.assertEqual(merge_sort([3,1,2]),[1,2,3])
if __name__=='__main__': unittest.main()
