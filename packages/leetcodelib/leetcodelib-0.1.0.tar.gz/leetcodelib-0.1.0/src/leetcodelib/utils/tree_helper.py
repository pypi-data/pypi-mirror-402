# -*- encoding: utf-8 -*-
# @Time    :   2026/01/18 20:37:44
# @File    :   tree_helper.py
# @Author  :   ciaoyizhen
# @Contact :   yizhen.ciao@gmail.com
# @Function:   leetcode 二叉树构建相关


from collections import deque
from .load_typing import *
class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right

def build_tree(arr: List[Optional[int]]) -> Optional[TreeNode]:
    """从数组构建二叉树，使用 LeetCode 的层序遍历方式"""
    if not arr or arr[0] is None:
        return None
    
    root = TreeNode(arr[0])
    queue = deque([root])
    i = 1
    
    while queue and i < len(arr):
        node = queue.popleft()
        
        # 处理左子节点
        if i < len(arr) and arr[i] is not None:
            node.left = TreeNode(arr[i])
            queue.append(node.left)
        i += 1
        
        # 处理右子节点
        if i < len(arr) and arr[i] is not None:
            node.right = TreeNode(arr[i])
            queue.append(node.right)
        i += 1
    
    return root

def dump_tree(root):
    """
    将二叉树转回数组（层序遍历，包含 None）
    注意：这只是简化版，完美的逆向 LeetCode 格式需要去除末尾多余的 None
    """
    if not root:
        return []
    
    result = []
    queue = deque([root])
    
    while queue:
        node = queue.popleft()
        if node:
            result.append(node.val)
            queue.append(node.left)
            queue.append(node.right)
        else:
            result.append(None)
    
    # 去除末尾多余的 None
    while result and result[-1] is None:
        result.pop()
        
    return result