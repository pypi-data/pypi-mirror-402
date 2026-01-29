
from __future__ import annotations
from copy import deepcopy
from typing import TypeAlias, Union, Literal, Any

TreeType: TypeAlias = Union[
    list[dict[Literal['exec'], list[Union[str, 'TreeType']]] | Any | 'ExecComplier'],
    'ExecComplier',
    str
]

class ExecComplier:
    global_place: int = 4
    def __init__(self, tree: TreeType) -> None:
        self._tree: TreeType = deepcopy(tree)

    def __copy__(self) -> ExecComplier:
        return ExecComplier(deepcopy(self._tree))

    def __call__(self=0) -> str:
        tree: TreeType = self._tree
        if isinstance(tree, list):
            end_strlist: list[str] = []
            for _item in tree:
                item: TreeType = _item._tree if isinstance(_item, ExecComplier) else _item # pyright: ignore[reportAssignmentType]
                if isinstance(item, str):
                    end_strlist.append(item)
                    continue
                key, value = next(iter(item.items())) # pyright: ignore[reportAttributeAccessIssue]
                for i in range(len(value)):
                    if isinstance(value[i], (dict, list, ExecComplier)):
                        value[i] = ExecComplier(value[i])()
                command: str = value[0]
                args: list[Union[str, TreeType]] = value[1:]
                if key == execute:
                    if command == expr:
                        end_strlist.append(self._expr(*args))
                    elif command == pd:
                        end_strlist.append(self._pd(*args))
                    elif command == call:
                        end_strlist.append(self._call(*args))
                    elif command == func:
                        end_strlist.append(self._func(*args)) # pyright: ignore[reportArgumentType]
                    elif command == key_return:
                        end_strlist.append(self._return(*args))
                    else: raise NameError(f'Unknown command: {command}')
                else: end_strlist.append(key)
            return '\n'.join(end_strlist)
        elif isinstance(tree, str):
            return tree
        else:
            raise TypeError(f'Unknown type: {type(tree)}')

    def _expr(self, num: TreeType) -> str:
        return ExecComplier(num)()

    def _pd(self, *args: TreeType) -> str:
        arg_str = ' '.join([ExecComplier(arg)() for arg in args])
        return f'#{arg_str}'

    def _call(self, func_name: TreeType, *args: TreeType) -> str:
        arg_str = ', '.join([ExecComplier(arg)() for arg in args])
        return f'{ExecComplier(func_name)()}({arg_str});'

    def _func(self, ret_type: str, name: str, arg: list[str], body: TreeType, _place:int|None=None) -> str:
        place: int = ExecComplier.global_place if _place is None else _place
        ider: str = ' '*place
        arg_str = ', '.join(arg)
        body_str = ider + ExecComplier(body)().replace('\n', f'\n{ider}')
        return f'{ret_type} {name}({arg_str})\n{{\n{body_str}\n}}'

    def _return(self, value: TreeType) -> str:
        val_str = ExecComplier(value)()
        return f'return {val_str};'

    @property
    def num(self):
        return deepcopy(self._tree)

class CallStr(str):
    def __new__(cls, fmt: str, *args, **kwargs) -> CallStr:
        self: CallStr = super().__new__(cls, fmt)
        self._fmt = fmt # pyright: ignore[reportAttributeAccessIssue]
        return self

    def __call__(self, *args, **kwargs) -> str:
        return self._fmt.format(*args, **kwargs) # pyright: ignore[reportAttributeAccessIssue]

    @property
    def template(self):
        return self._fmt # pyright: ignore[reportAttributeAccessIssue]

preprocessing_directive: str = 'preprocessing_directive'
pd: str = preprocessing_directive
execute: str = 'exec'
expr: str = 'expr'
call: str = 'call'
func: str = 'func'

type_int = 'int'
key_return = 'return'

null_line: str = ''

cstr: CallStr = CallStr('"{0}"')
cchr: CallStr = CallStr("'{0}'")

if __name__ == '__main__':
    test: ExecComplier = ExecComplier([
        {execute: [pd, 'include', '<stdio.h>']},
        null_line,
        {execute: [func, type_int, 'main', [], [
            {execute: [call, "printf", cstr("Hello World!")]},
            {execute: [key_return, '0']},
        ]]}
    ])
    print(test())
