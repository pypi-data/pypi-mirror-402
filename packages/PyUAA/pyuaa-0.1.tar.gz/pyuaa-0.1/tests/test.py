from src.UniversalApplicationAssembler import Assembler

assembler = Assembler("base_isa.yaml")

assembler.compile_code("test.asm", "test_result.bin")