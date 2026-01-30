from typing import Union
from qualesim.plugin import *
from qualesim.host import *
from sisq.ast.modules.gate import *
from sisq.ast.variable import Variable, ListVariable
from sisq.ast import VarDecl
from sisq.ast.variable import SISQType
from typing import List
from antlr4 import *
import numpy as np


class SISQDataStack:
    def __init__(self) -> None:
        self.func_qubit = dict()
        self.func_int = dict()
        self.func_double = dict()
        self.free_list = []
        self.func_name = ""
        ## qubit_measure <--> self.qubit_measure[self.func_qubit[name][index]] = (value, prob)
        self.qubit_measure = dict()
        self.changeable_list = dict()
        self.qubit_list = dict()
        self.matrix_list = dict()
        self.qubit_now = []
        self.state_vector = []
        self.res_qubit = []
        self.res_qubit_m = []
        self.res_dict = []
        self.PC = 0
        self.pc_range = 0


def check_type(var, types):
    try:
        if isinstance(var, types):
            return True
        else:
            return False
    except:
        if hasattr(types, "__origin__") and types.__origin__ == Union:
            for t in types.__args__:
                if isinstance(var, t):
                    return True
    return False


def is_type_single_gate(instr, func_data: SISQDataStack):
    gate_list = ["H", "X", "Y", "Z", "S", "T", "Sdag", "Tdag"]
    operation_name = instr.opname
    if operation_name not in gate_list:
        return False
    instr_type = 0
    instr_dest = instr.qubit.name
    instr_index = 0
    instr_matrix = [j for i in instr.matrix for j in i]
    mat_matrix = instr.matrix
    if isinstance(instr.qubit, Variable):
        instr_type = 1
        instr_index, instr_dest = Var_index_name(instr.qubit, func_data)
    else:
        instr_type = 2
    return instr_type, instr_dest, instr_index, instr_matrix, mat_matrix


def is_type_ctrl_two_gate(instr, func_data: SISQDataStack):
    gate_list = ["CNOT", "CZ"]
    operation_name = instr.opname
    if operation_name not in gate_list:
        return False
    instr_matrix = [j for i in instr.matrix[2:, 2:] for j in i]
    mat_matrix = instr.matrix
    instr_dest_index, instr_dest, instr_ctrl_index, instr_ctrl = Var2_index_name(
        instr.t_qubit, instr.c_qubit, func_data
    )
    return (
        instr_dest,
        instr_dest_index,
        instr_ctrl,
        instr_ctrl_index,
        instr_matrix,
        mat_matrix,
    )


def is_type_ctrl_phase_two_gate(instr, func_data: SISQDataStack):
    gate_list = ["CP", "CRz"]
    operation_name = instr.opname
    if operation_name not in gate_list:
        return False
    angel_list_row = instr.angle
    angel_list = []
    for i in range(len(angel_list_row)):
        if isinstance(angel_list_row[i], Variable):
            if angel_list_row[i].type == SISQType.IntType:
                index, name = Var_index_name(angel_list_row[i], func_data)
                angel_list.append(func_data.func_int[name][index])
            elif angel_list_row[i].type == SISQType.FloatType:
                index, name = Var_index_name(angel_list_row[i], func_data)
                angel_list.append(func_data.func_double[name][index])
        else:
            angel_list.append(angel_list_row[i])
    if operation_name == "CP":
        instr_matrix = np.array(
            [
                [1, 0, 0, 0],
                [0, 1, 0, 0],
                [0, 0, 1, 0],
                [0, 0, 0, np.exp(1j * angel_list[0])],
            ]
        )
    if operation_name == "CRz":
        instr_matrix = np.array(
            [
                [1, 0, 0, 0],
                [0, 1, 0, 0],
                [0, 0, np.exp(-1j * angel_list[0] / 2), 0],
                [0, 0, 0, np.exp(1j * angel_list[0] / 2)],
            ]
        )
    mat_matrix = instr_matrix
    instr_matrix = [j for i in instr_matrix[2:, 2:] for j in i]
    instr_dest_index, instr_dest, instr_ctrl_index, instr_ctrl = Var2_index_name(
        instr.t_qubit, instr.c_qubit, func_data
    )
    return (
        instr_dest,
        instr_dest_index,
        instr_ctrl,
        instr_ctrl_index,
        instr_matrix,
        mat_matrix,
    )


def is_type_two_gate(instr, func_data: SISQDataStack):
    gate_list = ["SWAP"]
    operation_name = instr.opname
    if operation_name not in gate_list:
        return False
    instr_matrix = [j for i in instr.matrix for j in i]
    mat_matrix = instr.matrix
    instr_dest_index, instr_dest, instr_ctrl_index, instr_ctrl = Var2_index_name(
        instr.t_qubit, instr.c_qubit, func_data
    )
    return (
        instr_dest,
        instr_dest_index,
        instr_ctrl,
        instr_ctrl_index,
        instr_matrix,
        mat_matrix,
    )


def is_type_1QRotation_gate(instr, func_data: SISQDataStack):
    gate_list = ["Rx", "Ry", "Rz", "Rxy", "U4"]
    operation_name = instr.opname
    if operation_name not in gate_list:
        return False
    instr_type = 0
    instr_dest = instr.qubit.name
    instr_index = 0
    angel_list_row = instr.angle
    angel_list = []
    for i in range(len(angel_list_row)):
        if isinstance(angel_list_row[i], Variable):
            if angel_list_row[i].type == SISQType.IntType:
                index, name = Var_index_name(angel_list_row[i], func_data)
                angel_list.append(func_data.func_int[name][index])
            elif angel_list_row[i].type == SISQType.FloatType:
                index, name = Var_index_name(angel_list_row[i], func_data)
                angel_list.append(func_data.func_double[name][index])
        else:
            angel_list.append(angel_list_row[i])

    if operation_name == "Rx":
        instr_matrix = np.array(
            [
                [
                    np.cos(angel_list[0] / 2),
                    -1j * np.sin(angel_list[0] / 2),
                ],
                [
                    -1j * np.sin(angel_list[0] / 2),
                    np.cos(angel_list[0] / 2),
                ],
            ]
        )
    elif operation_name == "Ry":
        instr_matrix = np.array(
            [
                [np.cos(angel_list[0] / 2), -np.sin(angel_list[0] / 2)],
                [np.sin(angel_list[0] / 2), np.cos(angel_list[0] / 2)],
            ]
        )
    elif operation_name == "Rz":
        instr_matrix = np.array(
            [
                [np.exp(-1j * angel_list[0] / 2), 0],
                [0, np.exp(1j * angel_list[0] / 2)],
            ]
        )
    elif operation_name == "Rxy":
        instr_matrix = np.array(
            [
                [
                    np.cos(angel_list[0] / 2),
                    -1j * np.exp(-1j * angel_list[1]) * np.sin(angel_list[0] / 2),
                ],
                [
                    -1j * np.exp(1j * angel_list[1]) * np.sin(angel_list[0] / 2),
                    np.cos(angel_list[0] / 2),
                ],
            ]
        )
    elif operation_name == "U4":
        instr_matrix = np.array(
            [
                [
                    np.exp(1j * (angel_list[0] - angel_list[1] / 2 - angel_list[3] / 2))
                    * np.cos(angel_list[2] / 2),
                    -np.exp(
                        1j * (angel_list[0] - angel_list[1] / 2 + angel_list[3] / 2)
                    )
                    * np.sin(angel_list[2] / 2),
                ],
                [
                    np.exp(1j * (angel_list[0] + angel_list[1] / 2 - angel_list[3] / 2))
                    * np.sin(angel_list[2] / 2),
                    np.exp(1j * (angel_list[0] + angel_list[1] / 2 + angel_list[3] / 2))
                    * np.cos(angel_list[2] / 2),
                ],
            ]
        )
    mat_matrix = instr_matrix
    instr_matrix = [j for i in instr_matrix for j in i]

    if isinstance(instr.qubit, Variable):
        instr_type = 1
        instr_index, instr_dest = Var_index_name(instr.qubit, func_data)
    else:
        instr_type = 2
    return instr_type, instr_dest, instr_index, instr_matrix, mat_matrix


## Get Variable's name and index
def Var_index_name(var: Variable, func_data: SISQDataStack):
    index = 0
    if hasattr(var, "index") and var.index is not None:
        if isinstance(var.index, str):
            index = func_data.func_int[var.index][0]
        else:
            index = var.index
        if var.name in func_data.changeable_list.keys():
            if func_data.changeable_list[var.name] == "int":
                l = len(func_data.func_int[var.name])
                if l <= index:
                    func_data.func_int[var.name] = func_data.func_int[var.name] + [
                        0
                    ] * (index - l + 1)
            elif func_data.changeable_list[var.name] == "float":
                l = len(func_data.func_double[var.name])
                if l <= index:
                    func_data.func_double[var.name] = func_data.func_double[
                        var.name
                    ] + [0.0] * (index - l + 1)
    return index, var.name


def Var2_index_name(var1: Variable, var2: Variable, func_data: SISQDataStack):
    index1, name1 = Var_index_name(var1, func_data)
    index2, name2 = Var_index_name(var2, func_data)
    return index1, name1, index2, name2


## Ctrl word
def ctrl_word(instr, func_data: SISQDataStack):
    ctrl_qubit = []
    try:
        if hasattr(instr, "ctrl_word") and instr.ctrl_word.ctrl:
            for var in instr.ctrl_word.ctrl_qubits:
                index, name = Var_index_name(var, func_data)
                ctrl_qubit.append(func_data.func_qubit[name][index])
    except ValueError:
        # The instruction has not been initialized with control word yet
        # This is normal for instructions without control qubits
        pass
    return ctrl_qubit


## We use the str instead of the isinstance function to avoid fatal.
def check_var_type(qtype: SISQType):
    if qtype == SISQType.QubitType:
        return 1
    elif qtype == SISQType.IntType:
        return 2
    elif qtype == SISQType.FloatType:
        return 3
    else:
        return 4


def func_initial(
    args_in: List[VarDecl],
    args_out: List[VarDecl],
    sisq_input: list,
    sisq_output: List[Variable],
):
    func_data: SISQDataStack = SISQDataStack()

    # Add the input and output args into func_data.
    for i in range(len(args_in)):
        var_size = 1
        var_name = args_in[i].vars[0].name
        if isinstance(args_in[i].vars[0], ListVariable):
            var_size = args_in[i].vars[0].size
            if isinstance(var_size, str):
                var_size = func_data.func_int[var_size][0]
                args_in[i].vars[0].size = var_size

        i_type = check_var_type(args_in[i].type)
        if i_type == 1:
            func_data.func_qubit[var_name] = sisq_input[i]
            func_data.qubit_list[var_name] = [-1] * var_size
        elif i_type == 2:
            func_data.func_int[var_name] = sisq_input[i]
        elif i_type == 3:
            func_data.func_double[var_name] = sisq_input[i]

    for i in range(len(args_out)):
        var_name = args_out[i].vars[0].name
        var_size = 1
        if isinstance(args_out[i].vars[0], ListVariable):
            var_size = args_out[i].vars[0].size
            if isinstance(var_size, str):
                var_size = func_data.func_int[var_size][0]
                args_out[i].vars[0].size = var_size

        i_type = check_var_type(args_out[i].type)
        if i_type == 1:
            func_data.func_qubit[var_name] = [0] * var_size
            func_data.qubit_list[var_name] = [-1] * var_size
        elif i_type == 2:
            func_data.func_int[var_name] = [0] * var_size
            func_data.changeable_list[var_name] = "int"
        elif i_type == 3:
            func_data.func_double[var_name] = [0.0] * var_size
            func_data.changeable_list[var_name] = "float"

    return func_data
