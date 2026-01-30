Эта библиотека содержит основные функции из теории телетрафика.

Примеры команд:

import teletraffic as ttt

print(ttt.E(9, 5))

print(ttt.Hi(9, 5, 3))

print(ttt.PalmTable(9, 5))

A = ttt.M_M_V_L_an(9, 5)

B = ttt.M_M_V_L_im(9, 5, 1000000)
B = ttt.M_M_V_L_im(9, 5, 1000000, 0)

print(ttt.EngsetTable(0.4, 10, 5))

C = ttt.Mi_M_V_L_an(0.4, 10, 5)

D = ttt.VM_M_V_L_PRA_an([2, 0.4], 3)

E = ttt.M_G_V_L_an(0.2, 34, 2, 44, 10)

print(ttt.ErlangFormula2(1, 3))

F = ttt.M_M_V_W_FF_R_an(1, 2, 0.05, 0.2)

J = ttt.M_M_V_W_FF_R_im(0.7, 2, 1000000)
H = ttt.M_M_V_W_FF_R_im(0.7, 2, 1000000, 0)
K = ttt.M_M_V_W_FF_R_im(0.7, 2, 1000000, 0, 0)

L = ttt.VM_VMl_V_L_an([10, 12], [1, 5], 3, 20)

M = ttt.VM_VMl_VDg_L_an([10, 12], [1, 5], 3, 20, 2)

N = ttt.VM_VMl_VDg_L_im([10, 12], [1, 5], 3, 20, 2, 100000, 'ПервСвоб')