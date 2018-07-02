import sys
from itertools import groupby

def rotatechar(char):
    if char[-1] == "[":
        return char[:-1] + "("
    if char[-1] == "(":
        return char[:-1] + "["

    if char[-1] == "]":
        return char[:-1] + ")"
    if char[-1] == ")":
        return char[:-1] + "["

    if char[-1] == ">":
        return char[:-1] + ","
    if char[-1] == ",":
        return char[:-1] + ">"

    return char

def mirror(problem):
    lines = []
    for line in problem:
        lines.append(line.strip().split("\\")[1:])

    return [list(x) for x in zip(*lines)]

def process_problem(problem):
    problemdata = mirror(problem[1: -3])

    ret = problem[0]
    for line in problemdata:
        for char in line:
            ret += "\\" + rotatechar(char)
        ret += "\n"

    print(problem)
    ret += problem[-3]
    ret += problem[-2]
    ret += problem[-1]
    return ret

def process(collection):
    with open(collection) as f:
        content = f.readlines()
    problems = [list(group) for k, group in groupby(content, lambda x: x == "\n") if not k]

    mirrored = [process_problem(p) for p in problems]
    return "\n".join(mirrored)

def processbook(name):
    newdata = process("../books/problems/" + name + ".tex")
    with open("../books/problems/" + name + "-mirror.tex", "w") as f:
        f.write(newdata)

processbook("cho-1")
processbook("cho-2")
processbook("cho-3")
processbook("gokyoshumyo")
processbook("xxqj")
processbook("hatsuyoron")
