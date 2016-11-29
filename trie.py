from itertools import combinations
from bisect import insort,bisect
import numpy as np
from collections import deque

class trie_node:
		def __init__(self,parent,item):
				self.parent=parent
				self.childs=None
				self.active=None
				self.item = item
				self.count=None
				self.support=0
		
		def __repr__(self):
				return self.item.__repr__()
		
		def __lt__(self,other):
				return self.item<other.item

		def find_index(self):
				return bisect(self.parent.active,self)-1
		
		def path(self,with_support_count=True):
				path=deque()
				n = self
				while n.parent:
						path.appendleft(n.item)
						n=n.parent
				return (list(path),self.support) if with_support_count else list(path)

		def gen_child_active_and_count(self,active,start):
				p_active = self.active
				d_index = []
				p_child_index = 0 
				temp = trie_node(None,None)
				for p_child in p_active:
						active_index = []
						c_active=[]
						index = 0
						count = 0
						for c_child in p_child.childs:
								i = c_child.item-start
								v = active[i]
								if v:
										if v==temp:
												c_active.append(c_child)
												active[i]=None
										else:
												for child in v.childs:
														if active[child.item-start]==None:
																active[child.item-start]=temp
												c_active.append(c_child)
												count+=1
												active_index.append(index)
								index+=1
						if count:
								p_child.active=c_active
								p_child.active_index = active_index
								l = len(c_active)-1
								cols = [l-index for index in active_index]
								#若active_index==len(c_acitve-1)，则可将其去除
								if cols[-1]==0:
										cols.pop()
										active_index.pop()
										count-=1
								p_child.count = [[0]*i for i in cols]
						if count==0:
								p_child.active=None
								p_child.active_index=None
								p_child.count=None
								del p_child.active_index
								d_index.append(p_child_index)
						p_child_index+=1
				

				if len(d_index):
						count = 0
						for index in d_index:
								del p_active[index-count]
								count+=1
				if len(p_active)==0:
						self.active=None
						c=self
						p = c.parent
						while p:
								index = c.find_index()
								del p.active[index]
								if len(p.active):
										break
								p.active=None
								c=p
								p=c.parent
								
		def search(self,items,start_index,active=True,extra=1):
				childs = self.active if active else self.childs
				childs_len = len(childs)
				items_len = len(items)
				child_index = 0
				child_indices=[]
				item_indices=[]
				
				if items_len ==start_index or childs_len==0:
						pass
				elif(items[-1]>=childs[0].item and items[0]<=childs[-1].item):
						for item_index in range(start_index,items_len):
								items_item = items[item_index]
								for child_index in range(child_index,childs_len):
										child_item = childs[child_index].item
										if child_item>items_item:
												break
										elif child_item==items_item:
												child_indices.append(child_index)
												item_indices.append(item_index+extra)
								else:
										break
				return (child_indices,item_indices)
								
class trie:
		def support_count(self):
				root = self.root
				for items in self.trans:		
						queue = deque(((root,0),))
						while queue:
								node,start_index = queue.popleft()
								if type(node.childs)==type(None):
										continue
								child_indices,item_indices = node.search(items,start_index,False)
								childs = [node.childs[child_index] for child_index in child_indices]
								for child in childs:
										child.support+=1
								queue.extend(zip(childs,item_indices))
		def print(self):
				queue = deque((self.root,))
				while queue:
						node = queue.popleft()
						if node.childs:
								queue.extend(node.childs)
						path = node.path()
						print(path)
								

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
				sort_index = np.argsort(support)
				sort_items = np.array(sort_items)[sort_index]
				
				"""fitems为从项到其序数的映射"""
				for rank in range(len(sort_index)):
						fitems[sort_items[rank]] = rank
				
				"""构建新的事务集，事务的项为原事务集从相应项的序数"""
				for items in trans:
						new_items=[]
						for item in items:
								insort(new_items,fitems[item])
						new_trans.append(new_items)

				return fitems,sort_items,new_trans
								
		def __init__(self,trans,minsup,reduce):
				self.root = trie_node(None,None)
				self.minsup = minsup
				self.reduce=reduce
				self.init(trans)
				
		def init(self,trans):
				minsup = self.minsup
				fitems,items,trans = trie.read(trans,minsup)
				nfitems = len(items)
				self.items = fitems
 
				support_count = [[0]*i for i in range(nfitems-1,0,-1)]
				for items in trans:
						for item1,item2 in combinations(items,2):
								support_count[item1][item2-item1-1]+=1

				root = self.root
				root.childs=[]
				root.active=[]
				active = []
				for item1 in range(nfitems):
						node = trie_node(root,item1)
						node.childs=[]
						root.childs.append(node)
						for item2 in range(item1+1,nfitems):
								if support_count[item1][item2-item1-1]>=minsup:
										cnode = trie_node(node,item2)
										node.childs.append(cnode)
						if len(node.childs):
								root.active.append(node)
								active.append(node)
						else:
								node.childs=None
								active.append(None)
				root.gen_child_active_and_count(active,0)
				
				self.k=2
				self.trans=trans
				
				if root.active:
						self.over=False
				else:
						self.over=True

		def trans_down(self):
				trans = self.trans
				root = self.root
				K = self.k
				k_node = []
				for items in trans:
						stack = [(root,0,0)]
						while len(stack):
								node,start_index,k = stack.pop()
								child_indices,item_indices = node.search(items,start_index)
								if len(child_indices) == 0:
										continue
								if (K-1==k):
										count = node.count
										current = 0
										l = len(node.active)-1
										for index in node.active_index:
												for item1,item2 in combinations(child_indices,2):
														if index < item1:
																break
														elif index > item1:
																continue;
														count[current][item2-index-1]+=1
												else:
														break
												current+=1
										continue
								childs = [node.active[index] for index in child_indices]
								stack.extend(zip(childs,item_indices,[k+1]*len(childs)))
								
		def gen_new_level(self):
				K = self.k
				minsup = self.minsup
				root = self.root
				stack = [(root,0)]
				while stack:
						node,k = stack.pop()
						if k==K-1:
								start = node.active[0].item
								is_active = [None]*(node.active[-1].item-start+1)
								active = node.active
								active_index = node.active_index
								node.active=[]
								count = node.count
								for index1 in range(len(count)):
										index = active_index[index1]
										active_node = active[index]
										childs = active_node.childs=[]
										count_node = count[index1]
										for index2 in range(len(count_node)):
												if count_node[index2]>=minsup:
														item = active[index+index2+1].item
														new = trie_node(active_node,item)
														childs.append(new)
										if len(childs)==0:
												active_node.childs=None														
										else:
												node.active.append(active_node)
												is_active[active_node.item-start]=active_node
								node.count=None
								node.gen_child_active_and_count(is_active,start)
						else:
								stack.extend(zip(node.active,[k+1]*len(node.active)))
				self.k+=1
				if root.active:
						return False
				return True
		
		def gen(self):
				while self.move_on():pass

		def move_on(self):
				if self.over:
						return False
				if self.reduce:
						self.simple_reduce_dataset()
				self.trans_down()
				self.over = self.gen_new_level()
				return True

		def simple_reduce_dataset(self):
				for items in self.trans:
						if len(items)<=self.k:
								items.clear()
				try:
						while True:
								self.trans.remove([])
				except ValueError:
						pass
