from gpflib import GPF
g=GPF("Corpus")
Ret=g.BCC("喜欢n{}",Command="Context",PageNo=0,WinSize=30,Number=10)
print(Ret)
