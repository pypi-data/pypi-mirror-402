import UniversalApplicationAssembler as UAA

#print(UAA.version)

assembler = UAA.Assembler("base_isa.yaml")

assembler.compile_code("test.asm", "test_result.bin")