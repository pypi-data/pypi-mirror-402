# -*- encoding: utf-8 -*-
# @Time    :   2026/01/18 20:36:40
# @File    :   link_helper.py
# @Author  :   ciaoyizhen
# @Contact :   yizhen.ciao@gmail.com
# @Function:   leetcode 链表构建相关


class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next

def build_link_list(nums):
    """将数组转换为链表"""
    if not nums:
        return None
    dummy = ListNode(0)
    current = dummy
    for val in nums:
        current.next = ListNode(val)
        current = current.next
    return dummy.next

def dump_link_list(head):
    """将链表转换为数组（用于Debug）"""
    result = []
    while head:
        result.append(head.val)
        head = head.next
    return result