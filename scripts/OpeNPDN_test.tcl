read_lef /home/sachin00/chhab011/OpenDB/tests/data/Nangate45/NangateOpenCellLibrary.mod.lef
puts "def"
read_def /home/sachin00/chhab011/aes/aes.def
#puts "ver"
#read_verilog /home/sachin00/chhab011/aes/aes_cipher_top.v
puts "lib"
read_liberty /home/sachin00/chhab011/aes/NangateOpenCellLibrary_typical.lib
#link_design aes_cipher_top
puts "sdc"
read_sdc /home/sachin00/chhab011/aes/aes_cipher_top.sdc

set OPDN_DIR "/home/sachin00/chhab011/OpenROAD/src/OpeNPDN/"
set OPDN_OpenDB_BUILD_DIR "/home/sachin00/chhab011/OpenDB/build/"

puts ${OPDN_DIR}
source "${OPDN_DIR}/scripts/OpeNPDN.tcl"

OpeNPDN  ${OPDN_DIR} ${OPDN_OpenDB_BUILD_DIR}