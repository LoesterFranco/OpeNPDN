#BSD 3-Clause License
#
#Copyright (c) 2019, The Regents of the University of Minnesota
#
#All rights reserved.
#
#Redistribution and use in source and binary forms, with or without
#modification, are permitted provided that the following conditions are met:
#
#* Redistributions of source code must retain the above copyright notice, this
#  list of conditions and the following disclaimer.
#
#* Redistributions in binary form must reproduce the above copyright notice,
#  this list of conditions and the following disclaimer in the documentation
#  and/or other materials provided with the distribution.
#
#* Neither the name of the copyright holder nor the names of its
#  contributors may be used to endorse or promote products derived from
#  this software without specific prior written permission.
#
#THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
#AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
#IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
#DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
#FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
#DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
#SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
#CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
#OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
#OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.


#!/usr/bin/python

"""
Created on Wed May  8 22:10:01 2019

@author:Vidya A Chhabria
"""

import re
import sys
import os
import csv
from scipy import ndimage
import numpy as np
from T6_PSI_settings import T6_PSI_settings
import importlib.util


def read_power_report(pwr_file):
    print('Reading power report file ')
    power_rep = {}
    with open(pwr_file) as f:
        comp_key = "" 
        for line in f:
            if re.match(r'^[\t ]*\d+', line, flags=re.IGNORECASE):
                words = line.strip().split(' ')
                #sanity 
                assert len(words) == 5, "number of elements in power report mismatch"
                comp_key = words[4]
                power_rep[comp_key] ={}
                power_rep[comp_key]['internal_power'] = float(words[0])
                power_rep[comp_key]['switching_power'] = float(words[1])
                power_rep[comp_key]['leakage_power'] = float(words[2])
                power_rep[comp_key]['total_power'] = float(words[3])
    #unit = {'m': 1e-3, 'u': 1e-6, 'n': 1e-9, 'p': 1e-12}
    #with open(pwr_file) as f:
    #    comp_key = ""
    #    for line in f:
    #        if re.match(r'^[\t ]*Instance:', line, flags=re.IGNORECASE):
    #            _, comp_key = line.split(':', 1)
    #            comp_key = comp_key.strip()
    #            power_rep[comp_key] = {}
    #        elif re.match(r'^[\t ]*Cell:', line, flags=re.IGNORECASE):
    #            _, cell = line.split(':', 1)
    #            power_rep[comp_key]['cell'] = cell.strip()
    #        elif re.match(r'^[\t ]*Liberty file:', line, flags=re.IGNORECASE):
    #            _, lib = line.split(':', 1)
    #            power_rep[comp_key]['lib'] = lib.strip()
    #        elif re.match(r'^[\t ]*Internal power:{0,1}[\t ]+\d',
    #                      line,
    #                      flags=re.IGNORECASE):
    #            data = re.findall(r'([+-]{0,1}\s+\d+\.{0,1}\d*)([mnu]{0,1})W',
    #                              line)
    #            power_rep[comp_key]['internal_power'] = float(
    #                data[0][0].strip()) * unit[data[0][1]]
    #        elif re.match(r'^[\t ]*Switching power:{0,1}[\t ]+\d',
    #                      line,
    #                      flags=re.IGNORECASE):
    #            data = re.findall(r'([+-]{0,1}\s+\d+\.{0,1}\d*)([mnu]{0,1})W',
    #                              line)
    #            power_rep[comp_key]['switching_power'] = float(
    #                data[0][0].strip()) * unit[data[0][1]]
    #        elif re.match(r'^[\t ]*Leakage power:{0,1}[\t ]+\d',
    #                      line,
    #                      flags=re.IGNORECASE):
    #            data = re.findall(r'([+-]{0,1}\s*\d+\.{0,1}\d*)([mnu]{0,1})W',
    #                              line)
    #            power_rep[comp_key]['leakage_power'] = float(
    #                data[0][0].strip()) * unit[data[0][1]]
    #        elif re.match(r'^[\t ]*Total power:{0,1}[\t ]+\d',
    #                      line,
    #                      flags=re.IGNORECASE):
    #            data = re.findall(r'([+-]{0,1}\s+\d+\.{0,1}\d*)([mnu]{0,1})W',
    #                              line)
    #            power_rep[comp_key]['total_power'] = float(
    #                data[0][0].strip()) * unit[data[0][1]]
    return power_rep

def create_power_map(settings_obj, db, power_rep):
    chip = db.getChip()
    block = chip.getBlock()
    insts = block.getInsts()
    unit_micron = 1/block.getDefUnits()
    die_area = block.getDieArea()
    width = abs(die_area.xMax() - die_area.xMin())*unit_micron 
    height= abs(die_area.yMax() - die_area.yMin())*unit_micron 
    width = int(width)
    height = int(height)
    power_map = np.zeros((width * 10, height * 10))
    number_of_cells_wo_power=0
    for  inst in insts:
        bbox = inst.getBBox()
        ll_x = int(bbox.xMin() * 10 * unit_micron)
        ll_y = int(bbox.yMin() * 10 * unit_micron)
        ur_x = int(bbox.xMax() * 10 * unit_micron)
        ur_y = int(bbox.yMax() * 10 * unit_micron)
        area = (ur_x - ll_x) * (ur_y - ll_y)
        area = np.size(power_map[ll_x:ur_x, ll_y:ur_y])
        if area == 0:
            #print("Warning Inst %s outside bounding box, check definition for region size and number of regions"%(
            #        inst.getName()))
            number_of_cells_wo_power = number_of_cells_wo_power + 1
            power_map[ll_x:ur_x, ll_y:ur_y] = 0
        else:
            inst_name = inst.getName()
            if inst_name in power_rep:
                power_map[ll_x:ur_x, ll_y:ur_y] = (power_map[ll_x:ur_x, ll_y:ur_y] +
                power_rep[inst_name]['total_power']/ area)
            else:
                print("Warning: instance %s not found in power report"%(inst_name))
                number_of_cells_wo_power = number_of_cells_wo_power + 1
    print("Number of cells without power = %d" % number_of_cells_wo_power)
    power_map_um = power_map.reshape(width, 10, height, 10).sum((1, 3))
    return power_map_um

def create_congest_map(settings_obj,congest_file,def_data):
    print('Reading congestion report file')
    congest_rep = {}
    res = def_data['units_per_micron']
    width = int(settings_obj.WIDTH_REGION*settings_obj.NUM_REGIONS_X*1e6)
    height = int(settings_obj.LENGTH_REGION*settings_obj.NUM_REGIONS_Y*1e6)
    congest_map = np.zeros((width * 10, height * 10))
    
    with open(congest_file) as f:
        comp_key = ""
        data = list(csv.reader(f))
        seq = iter(data)
        for row0 in seq:
            row1 = next(seq)
            # TODO works only with consequtive lines in the file. 
            ll_x = min(int(row0[0]),int(row0[2]),int(row1[0]),int(row1[2]))
            ll_y = min(int(row0[1]),int(row0[3]),int(row1[1]),int(row1[3]))
            ur_x = max(int(row0[0]),int(row0[2]),int(row1[0]),int(row1[2]))
            ur_y = max(int(row0[1]),int(row0[3]),int(row1[1]),int(row1[3]))
            ll_x = int(10*ll_x / res)
            ll_y = int(10*ll_y / res)
            ur_x = int(10*ur_x / res)
            ur_y = int(10*ur_y / res)
            if( ll_x >0 and ll_y>0 and ur_x >0 and ur_y >0 ):
                area = 100
                usd = int(row0[4]) + int(row1[4])
                tot = int(row0[5]) + int(row1[5])
                cong = usd/tot
                if cong <0 :
                    cong = 0
                congest_map[ll_x:ur_x, ll_y:ur_y] = congest_map[ll_x:ur_x,ll_y:ur_y] + cong/area
    congest_map_um = congest_map.reshape(width, 10, height, 10).sum((1, 3))
    return congest_map_um


def main():
    print(len(sys.argv))
    if len(sys.argv) != 3 and len(sys.argv) != 4 :
        print("ERROR Insufficient arguments")
        print(
            "Enter the full path names of the power report files and condition")
        print(" Format resolution_mapping.py <power_rpt> <CONGESTION_MODE>")
        sys.exit(-1)

    power_file = sys.argv[1]
    if (len(sys.argv) == 3 and sys.argv[2] == "no_congestion"):
        congestion_enabled =0 
    else:
        congestion_enabled =1 
        congest_file = sys.argv[3]
    if not os.path.isfile(power_file):
        print("ERROR unable to find " + power_file)
        sys.exit(-1)
    if congestion_enabled == 1:
        if not os.path.isfile(congest_file):
            print("ERROR unable to find " + congest_file)
            sys.exit(-1)

    settings_obj = T6_PSI_settings.load_obj()
    spec = importlib.util.spec_from_file_location("opendbpy", settings_obj.ODB_loc)
    odb = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(odb)
    db = odb.dbDatabase.create()
    db = odb.odb_import_db(db, "./work/PDN.db")
    if db == None:
        exit("Import DB Failed")


    chip = db.getChip()
    block = chip.getBlock()
    unit_micron = 1/block.getDefUnits()

    die_area = block.getDieArea()
    size_x = abs(die_area.xMax() - die_area.xMin())*unit_micron 
    size_y = abs(die_area.yMax() - die_area.yMin())*unit_micron 
    chip_width = settings_obj.WIDTH_REGION*settings_obj.NUM_REGIONS_X*1e6
    chip_length = settings_obj.LENGTH_REGION*settings_obj.NUM_REGIONS_Y*1e6
    
    #if (abs(size_x - chip_width) > settings_obj.LENGTH_REGION*1e6 or
    #    abs(size_y - chip_length) > settings_obj.LENGTH_REGION*1e6 ):
    #    print("ERROR: Area obtained from the DEF does not match the \
    #    template definition json file. Ensure the region sizes and \
    #    number of regions are defined appropriately")
    #    print("def x %f y %f json x %f y%f"%(size_x,size_y,chip_width,chip_length))
    #    exit(-1)

    power_rep = read_power_report(power_file)
    power_map = create_power_map(settings_obj,db,power_rep)
    power_map = power_map *100
    print("WARNING: currents are scaled internally by a factor of 100")
    if congestion_enabled == 1:
        congest_map = create_congest_map(settings_obj,congest_file,cell_data)
    filtered_map = ndimage.uniform_filter(power_map, size=20, mode='mirror')

    with open(settings_obj.cur_map_process_file, 'wb') as outfile:
        np.savetxt(outfile, filtered_map, delimiter=',')
    with open(settings_obj.cur_map_file, 'wb') as outfile:
        np.savetxt(outfile, power_map, delimiter=',')
    if congestion_enabled == 1:
        with open(settings_obj.cong_map_file, 'wb') as outfile:
            np.savetxt(outfile, congest_map, delimiter=',')


if __name__ == '__main__':
    main()
