# pyp
A Python Preprocessor

pyp is a very simple but powerful utility for working with text files and scripts.

Pyp can turn any text file into a template for generating customized versions of the file.

This is done by adding python code to the text file and running it through pyp to generate a customized output. 

In addition you can add python to a simple text based scripting language.

In your text file, lines starting with ! are run as python, and text in back quotes is evaluated as python. To avoid issues with indentation (python uses indentation to group statements), curly braces {} are used to start and end blocks.

Example: Say you have a file hello.txt that you need to customize, you could do this:

    !for name in ('David', 'John', 'Mary') {
    Hello `name`
    !}

In this file plain text (Hello `name`) is mixed with python.
This can be used in any system where you need to customize text files. 

