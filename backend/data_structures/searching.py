def binary_search(items,target,key=lambda x:x):
    lo,hi=0,len(items)-1
    while lo<=hi:
        mid=(lo+hi)//2; v=key(items[mid])
        if v==target:return items[mid]
        if v<target:lo=mid+1
        else:hi=mid-1
    return None
