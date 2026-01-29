from pwn import *

class LoopSearch(ELF):
    def __init__(self,path):
        '''
        初始化libc对象
        '''
        super().__init__(path, checksec=False)
        '''
        使用checksec关闭安全检查输出
        '''
    def set_base(self,address):
        '''
        设置Libc的基地址
        设置完之后，就可以使用.sym['xxx']进行计算
        '''
        self.address = address
    @property
    def system(self):
        '''
        获取libc 的system 函数的真实地址
        '''
        return self.symbols['system']
    @property
    def bin_sh(self):
        """
        获取 /bin/sh 字符串的真实地址
        """
        results = list(self.search(b'/bin/sh'))
        if results:
            return results[0]
        return None
        # 将迭代器转为列表，如果列表非空则取第一个，否则返回 None

class Looplibc(LoopSearch):
    def __init__(self, path, *args):
        """
        初始化并立即显示关键信息。
        :param path: Libc 文件路径 (str)
        :param args:
            - 如果只有 1 个参数，则视为基址 (int)
            - 如果有 2 个参数，则视为 (symbol_name, leaked_addr)
        """
        super().__init__(path)

        # 参数解析
        if len(args) == 1:
            # 模式 1: 直接传入基址
            self.address = args[0]
        elif len(args) == 2:
            # 模式 2: 传入符号名和泄露地址，自动倒推基址
            sym_name, leak_addr = args
            if sym_name not in self.symbols:
                raise ValueError(f"Symbol '{sym_name}' not found in {path}")

            offset = self.symbols[sym_name]
            self.address = leak_addr - offset
            print(f"[*] Calculated Base from '{sym_name}': {hex(leak_addr)} - {hex(offset)} = {hex(self.address)}")
        else:
            raise ValueError("Invalid arguments. Usage: loolibc(path, base) OR looplibc(path, sym_name, leak_addr)")

        print(f"\n{'=' * 30}")
        print(f"[*] Libc Base:      {hex(self.address)}")
        print(f"[+] System Address: {hex(self.system)}")

        bin_sh = self.bin_sh
        if bin_sh:
            print(f"[+] /bin/sh Address: {hex(bin_sh)}")
        else:
            print("[-] /bin/sh not found.")
        print(f"{'=' * 30}\n")