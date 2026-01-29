# RD-Compiler

## Introduction
This is a Python library that "compiles" Rhythm Doctor custom levels.

It actually rearranges level structure, making it difficult for human to read in both the game editor and text editors.

## Installation & Running
```shell
pip install rdcompiler
python -m rdcompiler -h
```

## Building
This library uses [Hatch](https://github.com/pypa/hatch) to build.

Install Hatch and run the following command in the root directory of this repository:
```shell
hatch build
```