"""
Create easily custom assemblers specifying ISAs with a YAML configuration file
"""

import os as _os

from .parser import ISAparser as _ISAparser
from .helpers.classes import InstructionTemplate as _InstructionTemplate
from .helpers.classes import Value as _Value

class Assembler:

    def __init__(self, yaml_config_path: _os.PathLike = None, auto_update: bool = True):

        """
        Creates an instance of the assembler.
        
        :param source_file: A .toml file specifying the ISA specification, by default none is specified (can add a source later setting Assembler.source manually)
        :type source_file: _os.PathLike
        :param auto_update: If after adding a source file it automatically updates the assembler to count it.
        :type auto_update: bool
        """

        #general variables
        self.auto_update = auto_update

        #the famous source (specified the last because it can autotriger update)
        self.source = yaml_config_path 

    @property
    def source(self):

        return self._source
    
    @source.setter
    def source(self, source_file: _os.PathLike):

        self._source = source_file

        if self.auto_update:
            self.update()

    def update(self):

        """
        Refreshes the assembler so that all sources are taken in to account
        """

        parser = _ISAparser(self.source)
        self.translation_context, self.instructions = parser.parse()

    def compile_code(self, assembly_source: _os.PathLike, end_result: _os.PathLike):

        """
        Compiles a whole assembly file and outputs the binary result
        
        :param assembly_source: The assembly source file path
        :type assembly_source: _os.PathLike
        :param end_result: The path where the binary result will be stored
        :type end_result: _os.PathLike
        """

        assembly_data: str = None
        with open(assembly_source) as file:
            assembly_data = file.read()

        preprocessed_data = self._preprocess_str(assembly_data)
        
        binary_list = []

        for instruction in preprocessed_data:

            if isinstance(self.instructions[instruction[0]], list): #multiple instructions with the same name

                correct_results = [] #all possible correct results

                for instruction_encoding in self.instructions[instruction[0]]:

                    try:
                        if len(instruction) == 1: #only opcode, no parameters
                            correct_results.append(instruction_encoding.compile_instruction())
                        else: #there is also parameters
                            instruction_encoding.apply(self.translation_context, parameters=instruction[1:])
                            correct_results.append(instruction_encoding.compile_instruction())
                    except Exception as e:
                        print("ENCODING SKIPPED, ENCODING:", instruction_encoding, "REASON:", e)

                #assert only one correct
                assert len(correct_results) == 1, f"{len(correct_results)} ambiguous encodings where found!"
                binary_list.append(correct_results[0])

            else:

                if len(instruction) == 1: #only opcode, no parameters
                    binary_list.append(self.instructions[instruction[0]].compile_instruction())
                else: #there is also parameters
                    self.instructions[instruction[0]].apply(self.translation_context, parameters=instruction[1:])
                    binary_list.append(self.instructions[instruction[0]].compile_instruction())

        with open(end_result, mode="w") as file:
            file.write("\n".join(binary_list))

    def _preprocess_str(self, string : str) -> list[str]:

        """
        INTERNAL FUNCTION. Preprocesses an assembly source to make compiling easy
        """

        #PHASE 1. REMOVE COMMENTS AND SEPARATE INSTRUCTIONS
        clean_string = "\n".join(line.split("//")[0].rstrip() for line in string.splitlines())

        clean_string = clean_string.split("\n")

        clean_string = [spli.strip() for spli in clean_string if spli.strip() != ""]

        #PHASE 2. SUBDIVIDE INSTRUCTIONS IN OPCODES AND PARAMETERS
        #first element is always opcode, the rest are parameters IN ORDER

        final_preprocessed = []

        for instruction in clean_string:
            #separating parameters
            subdivisions = instruction.split(",")

            #separate first parameters from opcode
            subdivisions = subdivisions[0].split(" ") + subdivisions[1:]

            final_preprocessed.append([e.strip() for e in subdivisions if e.strip() != ""])

        return final_preprocessed