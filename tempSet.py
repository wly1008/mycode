# -*- coding: utf-8 -*-
"""
Created on Sat Dec 21 10:32:31 2024

@author: wly
"""
import os

class TempDir:
    """Context manager to temporarily change the current working directory."""
    
    def __init__(self, new_dir):
        self.new_dir = new_dir
        self.old_dir = None

    def __enter__(self):
        # Store the old directory and change to the new one
        self.old_dir = os.getcwd()
        os.chdir(self.new_dir)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # Change back to the old directory, ignoring any exceptions
        os.chdir(self.old_dir)

class set_temp_attr:
    """
    上下文管理器，用于临时设置对象的属性。
    在上下文中设置属性值，退出上下文时恢复原有状态
    """
    def __init__(self, ds, attrName, value):
        """
        :param ds: 目标对象
        :param attrName: 属性名
        :param value: 临时设置的属性值
        """
        
        self.ds = ds
        self.attrName = attrName
        self.value = value
        
        self.hasattr = hasattr(ds, attrName)
        self.should_delete_attr = not self.hasattr

    def __enter__(self):
        
        
        self.oldValue = getattr(self.ds, self.attrName) if self.hasattr else None
        setattr(self.ds, self.attrName, self.value)
        
        return self.ds

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.should_delete_attr:
            if hasattr(self.ds, self.attrName):  # 确保属性存在
                delattr(self.ds, self.attrName)
        else:
            setattr(self.ds, self.attrName, self.oldValue)



# from contextlib import contextmanager

# @contextmanager
# def set_temp_attr(ds, attr_name, value):
#     """
#     上下文管理器，用于临时设置对象的属性。
#     在上下文中设置属性值，退出上下文时恢复原有状态或删除属性。

#     :param ds: 目标对象
#     :param attr_name: 属性名
#     :param value: 临时设置的属性值
#     """
#     # 检查属性是否存在
#     has_attr = hasattr(ds, attr_name)
#     old_value = getattr(ds, attr_name) if has_attr else None

#     # 设置临时属性值
#     setattr(ds, attr_name, value)

#     try:
#         yield ds  # 进入上下文，将对象返回给 `with` 块
#     finally:
#         # 恢复原始状态或删除属性
#         if has_attr:
#             setattr(ds, attr_name, old_value)
#         else:
#             if hasattr(ds, attr_name):
#                 delattr(ds, attr_name)




# @contextmanager
# def temp_dir(new_dir):
#     """
#     Context manager to temporarily change the current working directory.

#     :param new_dir: The directory to switch to temporarily.
#     """
#     old_dir = os.getcwd()  # 保存当前工作目录
#     os.chdir(new_dir)  # 切换到新的目录

#     try:
#         yield  # 进入上下文
#     finally:
#         os.chdir(old_dir)  # 恢复原来的工作目录


















