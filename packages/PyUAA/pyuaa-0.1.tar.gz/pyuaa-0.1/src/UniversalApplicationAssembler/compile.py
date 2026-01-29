"""
Create easily custom assemblers specifying ISAs with a YAML configuration file
"""

import os as _os
import yaml as _yaml

from .helpers import is_number_colon_number as _is_number_colon_number
from .helpers import gradient_range as _gradient_range
import warnings as _warnings

_warnings.simplefilter("always")

class Assembler:

    def __init__(self, source_file: _os.PathLike = None, auto_update: bool = True):

        """
        Creates an instance of the assembler.
        
        :param source_file: A .toml file specifying the ISA specification, by default none is specified (can add a source later setting Assembler.source manually)
        :type source_file: _os.PathLike
        :param auto_update: If after adding a source file it automatically updates the assembler to count it.
        :type auto_update: bool
        """

        #general variables
        self.auto_update = auto_update

        #parser specifications
        self.bits: int = None
        self.instructions: dict[str, InstructionTemplate] = {}
        self.translation_context: TranslationContext = None
        self.definitions: dict[str, tuple[str, Value]] = {}

        #the famous source (specified the last because it can autotriger update)
        self.source = source_file 

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

        assert self.source, f"No source defined!"

        self.global_values: set = set()
        self.instructions: dict[str, InstructionTemplate] = {}

        with open(self.source) as file:

            yaml_config = _yaml.safe_load(file) #read the config

            self._preparser(yaml_config)

            sublevels = self._parse_one_level(yaml_config["format"]) #parse the level "format"

            sublevels.remove("definitions")
            sublevels.remove("bits")

            for sublevel in sublevels:
                self._parse_recursively(yaml_config["format"][sublevel])

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
                        pass
                        

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

    #RELATED TO PARSING
    def _preparser(self, yaml_config):

        """
        INTERNAL FUNCTION. Does all the assertions for starting correctly the configuration
        
        :param yaml_config: The yaml config
        """

        assert isinstance(yaml_config, dict), "Config file yaml is not a dictionary!"

        # ----------------------------------------------------
        # CHECK FORMAT KEY
        # ----------------------------------------------------
        # This key is mandatory. It should include at least a bits specification and definitions specification

        assert "format" in yaml_config, f"Expected key \"format\" in yaml configuration file!"
        assert "bits" in yaml_config["format"], f"Expected bit specification inside the \"format\" key of the yaml configuration file!"
        assert "definitions" in yaml_config["format"], f"Expected definitions specification inside the \"format\" key of the yaml configuration file!"

        #CHECK BITS
        assert isinstance(yaml_config["format"]["bits"], int), f"Expected bits to be an integer number, not {type(yaml_config["format"]["bits"])}"
        self.bits = yaml_config["format"]["bits"]

        #CHECK DEFINITIONS
        assert isinstance(yaml_config["format"]["definitions"], dict), f"Expected definitions to be a dictionary, not {type(yaml_config["format"]["definitions"])}"

        definitions_dict = yaml_config["format"]["definitions"] #a shortcut to the definitions dict

        for definition_name in definitions_dict:

            #check that type and format is correct
            assert isinstance(definitions_dict[definition_name], str), f"Expected each definition to be a string, not type {type(definition_name)}"

            assert _is_number_colon_number(definitions_dict[definition_name]) or definitions_dict[definition_name].isnumeric(), f"Expected each definition to follow the format \"n:n\" or \"n\""

            if _is_number_colon_number(definitions_dict[definition_name]):

                parts = definitions_dict[definition_name].split(":")
                
                parts[0] = int(parts[0])
                parts[1] = int(parts[1])

                bits = abs(parts[0] - parts[1]) + 1 #calculate number of bits

                self.definitions[definition_name] = (definitions_dict[definition_name], Value(bits)) #add the definition to the definitions dict.

            else: #a regular str

                self.definitions[definition_name] = (definitions_dict[definition_name], Value()) #add the definition to the definitions dict.

        # ----------------------------------------------------
        # CHECK PARAMETERS KEY
        # ----------------------------------------------------

        if "parameters" in yaml_config: #there is parameters specification -> translation context

            assert isinstance(yaml_config["parameters"], dict), f"Expected key \"parameters\" to be a dict, not {type(yaml_config["parameters"])}!"

            self.translation_context = TranslationContext(translation_dict=yaml_config["parameters"])

    def _parse_recursively(self, current_level: dict):

        sublevels = self._parse_one_level(current_level)

        for sublevel in sublevels:
            self._parse_recursively(current_level[sublevel])

    def _parse_one_level(self, current_level: dict):

        assert isinstance(current_level, dict), f"Expected current_level to be a dict, not {type(current_level)}"

        sub_levels = []
        there_where_instructions = False
        definition_keys = set(self.definitions.keys())

        for key in current_level:

            #Check if some definition is mentioned

            if key in definition_keys:
                
                self.global_values.add(key) #add the definition mentioned as globally affected.

                assert isinstance(current_level[key], dict) or isinstance(current_level[key], int), f"Expected definition mention to be dict or int, not {type(current_level[key])}!"

                if isinstance(current_level[key], dict): #partial value set
                    self.definitions[key][1].set_partial_value(current_level[key])
                else: #is a integer -> full value set
                    self.definitions[key][1].set_full_value(current_level[key])

            #check the presence of certain special keys
            elif key == "instructions": #this level specifies instructions -> LAST LEVEL OF RECURSION
                there_where_instructions = True #marks that there where instructions detected -> TO AVOID MORE RECURSION

                assert isinstance(current_level["instructions"], list), f"Expected instructions to be specified in a list, not in {type(current_level["instructions"])}!"

                for instruction in current_level["instructions"]:
                    self._parse_instruction(instruction)
            
            else: #another key -> POTENTIAL SUBLEVEL
                sub_levels.append(key)

        if there_where_instructions and sub_levels:
            raise RecursionError(f"There where more sublevels of recursion after instructions where declared!")
        else:
            return sub_levels
        
    def _parse_instruction(self, instruction: dict):
        
        #make checks that all is specified:
        assert "name" in instruction, f"Expected name in instruction!"
        assert isinstance(instruction["name"], str), f"Expected a str for name, not {type(instruction["name"])}"

        template = InstructionTemplate(bits=self.bits) #creates the basic template

        used_fields: dict[str, tuple[str, Value]] = {}

        for key in instruction:

            if key in {"name", "parameters"}: #skip as already processed
                continue

            assert key in self.definitions, f"Key \"{key}\" is not a defined field! Expected to make reference to a defined field in an instruction."

            assert isinstance(instruction[key], dict) or isinstance(instruction[key], int), f"Expected definition mention to be dict or int, not {type(instruction[key])}!"

            if isinstance(instruction[key], dict): #partial value set
                self.definitions[key][1].set_partial_value(instruction[key])
            else: #is a integer -> full value set
                self.definitions[key][1].set_full_value(instruction[key])

            #add to used up fields
            used_fields[key] = self.definitions[key]

        #this instruction has parameters
        if "parameters" in instruction:

            #check that parameters are in definitions
            assert "mapping" in instruction["parameters"]
            for mapping in instruction["parameters"]["mapping"]:

                if isinstance(mapping, list):
                    for sub_mapping in mapping:
                        assert isinstance(sub_mapping, str)
                        assert sub_mapping in self.definitions

                        #add as used field
                        used_fields[sub_mapping] = self.definitions[sub_mapping]
                else:
                    assert isinstance(mapping, str)
                    assert mapping in self.definitions

                    #add as used field
                    used_fields[mapping] = self.definitions[mapping]

        #define the mappings first
        template.define_mappings(used_fields) #add the fields

        #then if needed define the parameters
        if "parameters" in instruction:
            template.define_parameters(instruction["parameters"]) #define the parameters of the instruction

        #add to the instruction dictionary
        if instruction["name"] in self.instructions: #DAMN. IT ALREADY EXISTS!
            if isinstance(self.instructions[instruction["name"]], InstructionTemplate): #There is only one instruction more.
                self.instructions[instruction["name"]] = [self.instructions[instruction["name"]], template]
            else: #must be a list
                self.instructions[instruction["name"]].append(template)
        else:
            self.instructions[instruction["name"]] = template

    #RELATED TO COMPILING
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
    
#HELPER CLASSES
class TranslationContext:

    """
    Represents a parameter translation system
    """

    def __init__(self, translation_dict: dict):
        self.translation_dict = translation_dict

    def translate(self, parameter_type: str, value: str) -> int:

        """
        Docstring for translate
        
        :param parameter_type: The type of the parameters, represented as a string separated by commas
        :type parameter_type: str
        :param value: The value itself of the paramater
        :type value: str
        :return: The value that represents the parameter
        :rtype: int
        """

        parts = parameter_type.split(".")

        current_level = self.translation_dict

        #accesses the translation
        for part in parts:

            assert part in current_level, f"\"{part}\" is not a key inside {current_level}"

            current_level = current_level[part]

        if isinstance(current_level, dict): #it is a translator
            
            assert value in current_level, f"Translator {current_level} has not key \"{value}\""

            assert isinstance(current_level[value], int), f"Expected the translator to give an integer, not {type(current_level[value])}"

            return current_level[value]

        elif isinstance(current_level, str): #it is a immediate specification

            assert _is_number_colon_number(current_level) or current_level.isnumeric(), f"Parameter immediate with argument \"{current_level}\" is not recognized"

            #calculating bits
            bits = 0
            if _is_number_colon_number(current_level):
                parts = current_level.split(":")

                parts[0] = int(parts[0])
                parts[1] = int(parts[1])

                bits = abs(parts[0] - parts[1]) + 1 #calculate number of bits

            else: #isnumeric()

                bits = 1

            #using the value
            if value.isnumeric():

                assert int(value) >= 0 and int(value) < 2**bits, f"immediate value {value} does surpass the limit of {bits} bit[s]!"

                return int(value)
            
            else: #check if it is a certain base
                if value[:2] == "0x":
                    
                    val = int(value[2:], 16)

                    assert val >= 0 and val < 2**bits, f"immediate value {value} does surpass the limit of {bits} bit[s]!"

                    return val

                elif value[:2] == "0o":
                    
                    val = int(value[2:], 8)

                    assert val >= 0 and val < 2**bits, f"immediate value {value} does surpass the limit of {bits} bit[s]!"

                    return val
                
                elif value[:2] == "0b":
                    
                    val = int(value[2:], 2)

                    assert val >= 0 and val < 2**bits, f"immediate value {value} does surpass the limit of {bits} bit[s]!"

                    return val
                
                else:
                    raise ValueError(f"\"{value}\" not recognized as a number!")
                
        elif isinstance(current_level, int): #literal number
            return current_level
        else:
            raise TypeError(f"translator in not a dict, str, or int. It is a {type(current_level)}")

class InstructionTemplate:

    """
    Represents a full ISA instruction
    """

    def __init__(self, bits: int, mappings: dict[str, tuple[str, "Value"]] = None, parameters: dict = None):

        """
        Creates a new InstructionTemplate
        
        :param bits: Description
        :type bits: int
        :param mappings: The mapping of Values to bit positions (optional -> can be later specified calling define_mappings)
        :type mappings: dict[str, tuple[str, "Value"]]
        :param parameters: the parameters of the instruction, represented using a dict with values and mapping (optional -> can be later specified calling define_parameters)
        :type parameters: dict
        """

        #dict -> FIELD_NAME: (BIT_RANGE, VALUE)

        self.bits = bits

        if mappings:
            self.define_mappings(mappings)

        if parameters:
            self.define_parameters(parameters)

    def define_mappings(self, mappings: dict[str, tuple[str, "Value"]] = None):
        
        """
        Adjusts the InstructionTemplate so that it uses a certain mappings
        
        :param mappings: The mappings of Values to bit positions
        :type mappings: dict[str, tuple[str, "Value"]]
        """

        self.fields: dict[str, tuple[str, Value]] = mappings #add all fields directly. Then check for errors.
        self.used_up_bits = [False for _ in range(self.bits)] #to check if bits are already used up

        for field_name in mappings:

            assert isinstance(field_name, str), f"Expected name of fields to be strings, not {type(field_name)}"

            key = mappings[field_name][0]
            value = mappings[field_name][1]

            assert _is_number_colon_number(key) or key.isnumeric(), "Expected mapping keys to be of the format \"number:number\" or \"number\""

            if _is_number_colon_number(key): #format n:n
                parts = key.split(":")

                #convert the numbers to integer
                parts[0] = int(parts[0])
                parts[1] = int(parts[1])

                bits = abs(parts[0] - parts[1]) + 1 #calculate number of bits

                assert value.bits == bits, f"Expected {bits} bit[s], not {value.bits} bit[s]!"

                for bit_position in _gradient_range(parts[0], parts[1]):
                    assert not self.used_up_bits[bit_position], f"Mapping with key \"{key}\", corresponding to {value}, is overlapping in bit {bit_position} of format!" #no overlap!
                    
                    self.used_up_bits[bit_position] = True
                    
                #if reached here -> there is no bit overlap -> add as field
                #Not added because already added
                #self.fields[field_name] = value

            else: #isnumeric()
                assert value.bits == 1, f"Expected 1 bit Value, not {value.bits} bits!"

                assert not self.used_up_bits[int(key)], f"Mapping with key \"{key}\", corresponding to {value}, is overlapping in bit {int(key)} of format!" #no overlap!

                self.used_up_bits[int(key)] = True #the bit is now used up
                #Not added because already added
                #self.fields[field_name] = value #now it is an official field

        if sum(self.used_up_bits) < self.bits:
            _warnings.warn(f"InstructionTemplate used up only {sum(self.used_up_bits)} bits out of {self.bits} bits: there is unused bits!!")

    def define_parameters(self, parameters: dict):
        
        """
        Defines parameters of the InstructionTemplate
        
        :param parameters: The dict that contains the parameters -> includes values and mapping
        :type parameters: dict
        """

        assert "values" in parameters, f"Parameters dictionary has no \"values\" key!"
        assert "mapping" in parameters, f"Parameters dictionary has no \"mapping\" key!"

        assert isinstance(parameters["values"], list), f"The values of parameters are not in a list, it is a {type(parameters["values"])}!"
        assert isinstance(parameters["mapping"], list), f"The mapping of parameters are not in a list, it is a {type(parameters["mapping"])}!"

        assert len(parameters["values"]) == len(parameters["mapping"]), f"Missmatch between number of parameters and mapping specified, respectively: {len(parameters["values"])} vs {len(parameters["mapping"])}"

        for value in parameters["values"]:
            assert isinstance(value, str), f"Expected value \"{value}\" to be a string, not a {type(value)}"

        for mapping in parameters["mapping"]:
            assert isinstance(mapping, str) or isinstance(mapping, list), f"Expected mapping \"{mapping}\" to be a string or list, not a {type(mapping)}"

            if isinstance(mapping, list):
                for sub_mapping in mapping:
                    assert isinstance(sub_mapping, str), f"Expected sub_mapping \"{sub_mapping}\" to be a string, not a {type(sub_mapping)}"
                    assert sub_mapping in self.fields, f"Parameter maps to a non-defined field: \"{sub_mapping}\"!"
            else:
                assert mapping in self.fields, f"Parameter maps to a non-defined field: \"{mapping}\"!"

        self.parameters = parameters

    def apply(self, translation_context: TranslationContext, parameters: list[str]):

        """
        Applies parameters to the instruction, following a certain translation context.
        
        :param translation_context: The translation context object that sets all parameter translations to fields
        :type translation_context: TranslationContext
        :param parameters: A list with all parameters
        :type parameters: list[str]
        """

        assert len(parameters) == len(self.parameters["values"]), f"Missmatch between number of parameters! Got {len(parameters)}, expected {len(self.parameters["values"])}"

        #iterate over each parameter
        for i in range(len(parameters)):

            translated_value = translation_context.translate(parameter_type=self.parameters["values"][i], value=parameters[i]) #translate each parameter

            if isinstance(self.parameters["mapping"][i], list):

                bits_done = 0 #counts how many bits are already set.
                
                for sub_mapping in reversed(self.parameters["mapping"][i]): #iterates over the mappings, reversed to do first the LSBs.

                    sub_mapping_bits = self.fields[sub_mapping][1].bits

                    mask = 2 ** sub_mapping_bits - 1 #creates a mask

                    final_value = (translated_value >> bits_done) & mask #the final value after applying the mask and correcting

                    self.set_full_field(sub_mapping, final_value) #set the value

                    #increase bits_done to perform the next iterations correctly
                    bits_done += sub_mapping_bits

            else: #must 100% be str because of the check in define_parameters
                self.set_full_field(self.parameters["mapping"][i], translated_value)

    #SET FUNCTIONS
    def set_partial_field(self, name: str, set_dict: dict):

        """
        Sets the some partial value to some field. 
        
        :param name: The name of the field
        :type name: str
        :param set_dict: The dict that determines the set
        :type set_dict: dict
        """

        assert name in self.fields, f"\"{name}\" is not a field out of {list(self.fields.keys())}!"

        self.fields[name][1].set_partial_value(set_dict)

    def set_full_field(self, name: str, value: int): 
        
        """
        Sets the full value of a full field
        
        :param name: The name of the field
        :type name: str
        :param value: The value itself
        :type value: int
        """

        assert name in self.fields, f"\"{name}\" is not a field out of {list(self.fields.keys())}!"

        self.fields[name][1].set_full_value(value)

    def check_completeness(self):

        """
        Checks if all the fields of the InstructionTemplate have been filled.
        """

        for field_name in self.fields:
            if not self.fields[field_name][1].check_value():
                return False
            
        return True
    
    def compile_instruction(self) -> str:

        """
        Returns the numerical value of the compiled instruction in binary.
        
        :return: The binary representation of the instruction
        :rtype: str
        """

        compiled_instruction = "?" * self.bits #the compiled final instruction
        compiled_instruction = list(compiled_instruction) #passing to list to modify

        if not self.check_completeness():
            raise ValueError(f"Compiling an instruction that is not completed!")
        
        for field_name in self.fields:
            
            key = self.fields[field_name][0] #where it is located
            value = self.fields[field_name][1] #the value itself

            if _is_number_colon_number(key):
                parts = key.split(":")

                parts[0] = int(parts[0])
                parts[1] = int(parts[1])

                for bit_n, mapped_bit in enumerate(_gradient_range(parts[1], parts[0])): #7:0 would be 0, 1, 2, 3, ...
                    compiled_instruction[-mapped_bit + 1] = (int(value.value) >> bit_n) & 0b1 #write one bit at a time -> from LSB in the order specified by the key.

            else: #is a simple str -> 1 bit

                compiled_instruction[-int(key) + 1] = int(value.value) #simply copy-paste the value directly

        return "".join(map(lambda x: str(x), compiled_instruction))

    def __repr__(self):

        return f"<InstructionTemplate. Bits: {sum(self.used_up_bits)} / {self.bits}>"  

class Value:

    """
    Represents a binary value
    """

    def __init__(self, bits: int = 1):

        self.bits = bits
        self.value = "?" * bits

    def create_from_definition(self, definition: str):

        """
        Configurates the value so that it initilizes following a definition
        
        :param definition: The string that defines the value
        :type definition: str
        """

        assert isinstance(definition, str), f"\"{definition}\" is not an str!" #just in case

        if ":" in definition:
            parts = definition.split(":")
            assert len(parts) == 2
            assert parts[0].isnumeric() and parts[1].isnumeric()

            parts[0] = int(parts[0])
            parts[1] = int(parts[1])

            self.bits = abs(parts[0] - parts[1]) + 1 #set the number of bits

            self.value = "?" * self.bits

        else: #is only one number -> one bit
            assert definition.isnumeric()

            self.bits = 1
            self.value = "?"

    def set_partial_value(self, set_dict: dict):

        """
        Sets the value partially according to a set dict.
        
        :param set_dict: The dict that determines the set
        :type set_dict: dict
        """

        assert "set" in set_dict, "Set dict does not include key \"set\""
        assert isinstance(set_dict["set"], int), f"\"set\" is not a numerical value! Dict: {set_dict}"

        assert "bits" in set_dict, "Set dict does not include key \"bits\""
        assert isinstance(set_dict["bits"], str), f"\"bits\" is not a string specifying the affected bits! Dict: {set_dict}"

        if ":" in set_dict["bits"]:
            parts = set_dict["bits"].split(":")
            assert len(parts) == 2
            assert parts[0].isnumeric() and parts[1].isnumeric()

            parts[0] = int(parts[0])
            parts[1] = int(parts[1])

            bits = abs(parts[0] - parts[1]) + 1 #count number of bits expected

            assert set_dict["set"] >= 0 and set_dict["set"] < 2**bits #assert that the value is compliant

            set_value = bin(set_dict["set"]).removeprefix("0b").rjust(bits, "0")

            self.value = list(self.value) #convert to list temporally (string is immutable)

            for idx, i in enumerate(_gradient_range(parts[0], parts[1])):
                self.value[-i - 1] = set_value[idx]

            self.value = "".join(self.value) #return to string

        else:
            assert set_dict["bits"].isnumeric()
            assert set_dict["set"] == 0 or set_dict["set"] == 1

            self.value = list(self.value) #convert to list temporally (string is immutable)

            self.value[-int(set_dict["bits"]) - 1] = str(bin(set_dict["set"]).removeprefix("0b"))

            self.value = "".join(self.value) #return to string

    def set_full_value(self, value: int):

        """
        Sets the whole value
        
        :param value: The value to be set
        :type value: int
        """

        assert value >= 0 and value < 2**self.bits

        self.value = bin(value).removeprefix("0b").rjust(self.bits, "0")

    def check_value(self) -> bool:

        """
        Checks if the value is 100% set.
        
        :return: True or false
        :rtype: bool
        """

        if "?" in self.value:
            return False
        else:
            return True
        
    def __repr__(self):

        return f"<Value: value={self.value}, bits={self.bits}>"