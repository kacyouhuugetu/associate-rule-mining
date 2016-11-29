import numpy as np
from bisect import bisect_left,insort
from collections import namedtuple
from itertools import combinations

fp_tree_node = namedtuple('frequent_pattern_tree_node',('item','parent','childs'))

def fp_tree_print(fp_tree_node,nitems,itemconvert,items):
		node = fp_tree_node
		stack = [node]
		items_sets=[]
		iteminvert = fp_tree_iteminvert(node,nitems,itemconvert,items)
		while stack:
				node = stack.pop()
				items_sets.append(fp_get_path(node,iteminvert,items))
				if node.childs:
						stack.extend(node.childs)
		return sorted(items_sets,key=lambda l:[len(l)]+l)

def fp_get_path(fp_tree_node,iteminvert,items):
		path = []
		c,p = fp_tree_node,fp_tree_node.parent
		while p!=None:
				path.append(iteminvert[c.item])
				c = p
				p = p.parent
		path.append(items[c.item])
		return path

def fp_tree_iteminvert(root,nitems,itemconvert,items):
		iteminvert=[0]*nitems
		for index in range(len(itemconvert)):
				item_index = itemconvert[index]
				if item_index!=-1:
						iteminvert[item_index] = items[index]
		return iteminvert

class tree_node:
		def __init__(self,item,support,parent=None,childs=None,thread=None):
				c = childs if childs else []
				support = [0]*support
				self.item,self.support,self.parent,self.childs,self.thread = item,support,parent,c,thread
		
		def __repr__(self):
				return self.item.__repr__()

		def __lt__(self,other):
				return self.item<other

		def search_down(self,item):
				node = self
				while node.item!=item:node=node.childs[0]
				return node
		
		#获取从self到主干上item为start的路径
		def get_path(self,start,itemconvert=None):
				path = []
				node,support = self,self.item+1
				while len(node.support)!=support:
						nitem = itemconvert[node.item] if itemconvert else node.item
						if nitem!=-1:
								path.insert(0,nitem)
						node = node.parent
						support = node.item+1
				extend = [i for i in range(start,support) if itemconvert[i]!=-1] if itemconvert else [i for i in range(start,support)]
				return extend+path
				
		def travel_items(self,items,thread,count=0):
				node = self
				item_0,support,start,end = items[0],node.item+1,1,len(items)
				#从主干上向下搜索
				node.support[item_0]+=count
				while start<end and support==items[start]:
						start+=1
						support+=1
						#循环结束后，node将为items在主干中的项的最后一个项对应的结点
						node = node.childs[0]
						node.support[item_0]+=count
				if start==end:	
						if not count:
								node.support[item_0]+=1
						return
				
				#start为items中第一个不在主干中的项的索引
				for item in items[start:]:
						pos = bisect_left(node.childs,item)
						if len(node.childs)==0 or pos==len(node.childs) or node.childs[pos].item!=item:
								new_child = tree_node(item,support,node,thread=thread[item])
								node.childs.insert(pos,new_child)
								thread[item] = new_child
								node = new_child
						else:
								node = node.childs[pos]
						node.support[item_0]+=count

				if not count:
						node.support[item_0]+=1
						

class tree:
		def __repr__(self):
				node = self.root
				N = len(self.items)
				s=node.__repr__()+'\t'
				while node.childs:
						s+=node.childs[0].__repr__()+'\t'
						node=node.childs[0]
				return s
		

		"""读取事务集，并获取频繁项"""
		def read(trans,minsup):
				fitems={}
				support=[]
				sort_items=[]
				discard_items=[]
				new_trans,new_items = [],[]

				"""统计事务集中每个项的出现频数"""
				for items in trans:
						for item in items:
								if item not in fitems:
										fitems[item]=0
								fitems[item]+=1

				"""若某一项的出现频数小于minsup，则将其添加进discard_items，等候删除"""
				for key,value in fitems.items():
						if value<minsup:
								discard_items.append(key)
						else:
								sort_items.append(key)
								support.append(value)
				"""删除非频繁项"""
				for item in discard_items:
						del fitems[item]
						for items in trans:
								try:
										items.remove(item)
								except ValueError:
										pass
				del discard_items
				
				"""根据频数，对项进行升序排序"""
				sort_index = np.argsort(support)[::-1]
				sort_items = np.array(sort_items)[sort_index]
				support = np.array(support)[sort_index]

				"""fitems为从项到其序数的映射"""
				for rank in range(len(sort_index)):
						fitems[sort_items[rank]] = rank
				
				"""构建新的事务集，事务的项为原事务集从相应项的序数"""
				for items in trans:
						new_items=[]
						for item in items:
								insort(new_items,fitems[item])
						if len(new_items):
								new_trans.append(new_items)

				return fitems,sort_items,support,new_trans

		def __init__(self,trans,minsup):
				self.minsup = minsup
				self.fitems,self.items,self.support,self.trans = tree.read(trans,minsup)
				if len(self.items)==0:
						print('error')
						return
				self.root = tree_node(0,1)
				self.thread = [None]*len(self.items)
				tree.construct_main_branch(len(self.items),self.root,self.thread)
				self.travel_trans()
				self.item = len(self.items)-1
				
		def construct_main_branch(N,root,thread):
				node = root
				thread[0] = node
				for i in range(1,N):
						c = tree_node(i,i+1,node)
						thread[i] = c
						node.childs.append(c)
						node = c
		
		def travel_trans(self):
				root = self.root
				thread = self.thread
				for items in self.trans:
						node = root.search_down(items[0])
						node.travel_items(items,thread)
					
		def support_count_2_itemsets(self):
				N = len(self.items)
				countTable = [[0]*i for i in range(1,N)]
				stack = [self.root]
				while stack:
						node = stack.pop()
						support = node.support
						l_support = len(support)
						if node.item+1==l_support:
								l_support-=1
						for i in range(l_support):
								if not support[i]:
										continue
								p = node.get_path(i)
								cmb = combinations(p,2)
								for pos in cmb:
										pos2,pos1 = pos
										countTable[pos1-1][pos2]+=support[i]
						stack.extend(node.childs)
				return countTable		
		
		#创建以item结尾的子树
		def construct_subtree(self,item,countTable):
				N = len(self.items)
				minsup = self.minsup
				#树中某个item在子树中对应的item为itemconvert[item]
				itemconvert = [-1]*N
				nitems = 0
				
				#获取以item结尾的2-频繁项集
				items_count = []
				countTable_item = countTable[item-1]
				for count_index in range(len(countTable_item)):
						count = countTable_item[count_index]
						if count>=minsup:
								itemconvert[count_index] = nitems
								items_count.append(count)
								nitems+=1
				if not nitems:
						return (None,None)

				items_count = [count for count in items_count if count>=minsup]
				
				s_root = tree_node(0,1)
				s_thread = [None]*nitems
				tree.construct_main_branch(nitems,s_root,s_thread)
				
				thread = self.thread[item]
				while thread:
						support = thread.support
						l_support = len(thread.support)
						if item+1 == l_support:
								l_support-=1
						for i in range(l_support):
								count = support[i]
								if not count:
										continue
								items = thread.get_path(i,itemconvert)
								node = s_root.search_down(items[0])
								node.travel_items(items,s_thread,count)
								thread.parent.support[i]+=count
						thread = thread.thread
				
				node = s_root
				for i in range(nitems-1):
						node = node.childs[0]
						for j in range(len(node.support)-1):
								if node.support[j]!=0:break
						else:
								node.parent=None
								

				return (itemconvert,nitems,items_count,s_root,s_thread)

		def mine_subtree(item,minsup,nitems,items_count,s_root,s_thread):
				f_root = fp_tree_node(item,None,[])
				childs = [fp_tree_node(i,f_root,[]) for i in range(nitems)]
				f_root.childs.extend(childs)

				stack=[]
				if nitems>1:
						stack.append((f_root.childs[1],1))

				del childs
				
				while stack:
						f_node,index = stack.pop()
						item = f_node.item

						if len(f_node.parent.childs)>index+1:
								stack.append((f_node.parent.childs[index+1],index+1))
						#将小于f_node.item的项item_结点的support清0
						#对应项item_的item_counts和thread也清0

						for item_ in range(item):
								items_count[item_]=0
								thread = s_thread[item_]
								while thread:
										t_support = thread.support
										for i in range(len(t_support)):
												t_support[i]=0
										thread=thread.thread
								s_thread[item_]=None
						
						thread = s_thread[item]
						while thread:
								parent = thread.parent
								t_support = thread.support

								while parent:
										p_support = parent.support
										l_p_support = len(parent.support)
										p_item = parent.item

										sumc,sump = sum(t_support[:l_p_support]),sum(p_support)
										if sumc:
												if not sump:
														parent.thread = s_thread[p_item]
														s_thread[p_item] = parent
												for i in range(l_p_support):
														p_support[i]+=t_support[i]
												items_count[p_item]+=sumc
												parent = parent.parent
										else:
												parent=None

								thread=thread.thread
						
						nitems=0
						for count_index in range(item):
								if items_count[count_index]>minsup:
										f_node.childs.append(fp_tree_node(count_index,f_node,[]))
										nitems+=1
						if nitems>1:
								stack.append((f_node.childs[1],1))
				
				return f_root
			
		def gen_frequent(self):
				nitems = len(self.items)
				minsup = self.minsup
				countTable = self.support_count_2_itemsets()
				if self.item<1:
						del self.item
						return None
				itemconvert,*sub_tree = self.construct_subtree(self.item,countTable)
				if not sub_tree:
						return None
				f_root = tree.mine_subtree(self.item,minsup,*sub_tree)
				self.item-=1
				p = fp_tree_print(f_root,sub_tree[0],itemconvert,self.items)
				return f_root,p
