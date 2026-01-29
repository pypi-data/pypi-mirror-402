"""
Includes all functions related to parsing the YAML config file
"""

import yaml as _yaml
import os as _os

from .helpers.classes import TranslationContext as _TranslationContext
from .helpers.classes import InstructionTemplate as _InstructionTemplate
from .helpers.classes import Value as _Value

import copy as _copy

from .helpers.functions import is_number_colon_number as _is_number_colon_number

class ISAparser:

    """
    Class in charge of parsing a certain yaml file that represents an ISA
    """

    def __init__(self, yaml_config_path: _os.PathLike = None):

        """
        Docstring for __init__
        
        :param yaml_config_path: The path of the yaml path that specifies the ISA (optional -> can be later defined directly changing self.source)
        :type yaml_config_path: _os.PathLike
        :param auto_parse: If the file is autoparsed just after specifying (if not automatic, must call self.parse())
        :type auto_parse: bool
        """

        #parser specifications
        self.bits: int = None
        self.instructions: dict[str, _InstructionTemplate] = {}
        self.translation_context: _TranslationContext = None
        self.definitions: dict[str, tuple[str, _Value]] = {}

        #the famous source (specified the last because it can autotriger update)
        self.source = yaml_config_path

    def parse(self):

        """
        Parses the yaml file, returning the dictionary of InstructionTemplates of the ISA.
        """

        assert self.source, f"No source defined!"

        self.global_values: set = set()
        self.instructions: dict[str, _InstructionTemplate] = {}

        with open(self.source) as file:

            yaml_config = _yaml.safe_load(file) #read the config

            self._preparser(yaml_config)

            sublevels = self._parse_one_level(yaml_config["format"]) #parse the level "format"

            sublevels.remove("definitions")
            sublevels.remove("bits")

            for sublevel in sublevels:
                self._parse_recursively(yaml_config["format"][sublevel])

        return self.translation_context, self.instructions

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

                self.definitions[definition_name] = (definitions_dict[definition_name], _Value(bits)) #add the definition to the definitions dict.

            else: #a regular str

                self.definitions[definition_name] = (definitions_dict[definition_name], _Value()) #add the definition to the definitions dict.

        # ----------------------------------------------------
        # CHECK PARAMETERS KEY
        # ----------------------------------------------------

        if "parameters" in yaml_config: #there is parameters specification -> translation context

            assert isinstance(yaml_config["parameters"], dict), f"Expected key \"parameters\" to be a dict, not {type(yaml_config["parameters"])}!"

            self.translation_context = _TranslationContext(translation_dict=yaml_config["parameters"])

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

        template = _InstructionTemplate(bits=self.bits) #creates the basic template

        used_fields: dict[str, tuple[str, _Value]] = {}

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
            used_fields[key] = (self.definitions[key][0], _copy.deepcopy(self.definitions[key][1]))


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
                        used_fields[sub_mapping] = (self.definitions[sub_mapping][0], _copy.deepcopy(self.definitions[sub_mapping][1]))
                else:
                    assert isinstance(mapping, str)
                    assert mapping in self.definitions

                    #add as used field
                    used_fields[mapping] = (self.definitions[mapping][0], _copy.deepcopy(self.definitions[mapping][1]))

        #define the mappings first
        template.define_mappings(used_fields) #add the fields

        #then if needed define the parameters
        if "parameters" in instruction:
            template.define_parameters(instruction["parameters"]) #define the parameters of the instruction

        #add to the instruction dictionary
        if instruction["name"] in self.instructions: #DAMN. IT ALREADY EXISTS!
            if isinstance(self.instructions[instruction["name"]], _InstructionTemplate): #There is only one instruction more.
                self.instructions[instruction["name"]] = [self.instructions[instruction["name"]], template]
            else: #must be a list
                self.instructions[instruction["name"]].append(template)
        else:
            self.instructions[instruction["name"]] = template