def merge_sort(items,key=lambda x:x):
    if len(items)<=1:return list(items)
    m=len(items)//2; a=merge_sort(items[:m],key); b=merge_sort(items[m:],key); out=[]
    while a and b: out.append(a.pop(0) if key(a[0])<=key(b[0]) else b.pop(0))
    return out+a+b
