#!/usr/bin/python3
# ==============================================================================
#
# Copyright (C) 2022 bigtpu Technologies Inc.  All rights reserved.
#
# TPU-MLIR is licensed under the 2-Clause BSD License except for the
# third-party components.
#
# ==============================================================================

from profile_helper.bmprofile_parser import BMProfileParser, parse_data_blocks, IterRecord, parse_monitor_bd, parse_monitor_gdma, parse_monitor_cdma, parse_dyn_data, parse_dyn_extra, parse_fixed_length_items
from profile_helper.bmprofile_common import BlockType, GlobalInfo, Arch
from profile_helper.bmprofile_utils import re_key_value
from profile_helper.bm1690_defs import get_tiu_info, get_dma_info, get_tiu_info_dyn, get_dma_info_dyn
import os, re, math
import logging
from typing import List
from pathlib import Path
import itertools
import glob
import struct as st
from tqdm import tqdm

def get_cmd_id(c):
    cmd_id = -1
    if hasattr(c, 'cmd_id'):
        cmd_id = c.cmd_id
    else:
        cmd_id = c.inst_id
    return cmd_id

class DesCommon(object):
    def __init__(self, cmd_num, id, cmd) -> None:
        self.cmd_num = cmd_num
        self.id = id
        self.cmd = cmd

    def parse(self, parser):
        if isinstance(self.cmd, bytes):
            self.cmd = parser.parse(self.cmd)
        return self.cmd
    
    def __repr__(self) -> str:
        return f"DesCommon(cmd_num={self.cmd_num}, id={self.id}, cmd_len={len(self.cmd)})"

class DynCpuInfo(object):
    def __init__(self, begin_cycle, end_cycle, type, inst_id) -> None:
        self.end_cycle = end_cycle
        self.type = type
        self.inst_id = inst_id

class BMProfileParserPerfAI(BMProfileParser):
    def __init__(self):
        super().__init__()
        self.gdma_pairs = []
        self.sdma_pairs = []
        self.cdma_pairs = []
        self.bd_pairs = []
        self.cdmlib_extra = []
        self.profile_sync_points = []
        self.in_dir = None
        self.out_dir = None
        self.cdma_cord_id = None
        self.is_bmodel = False

    def parse_cdma_pmu(self, file_list):
        self.cdma_pairs = [[] for _ in range(self.archlib.CDMA_NUM)]
        for infile in file_list:
            idx = eval(re.search(r'cdma\d*_(\d+)\.profile', infile).group(1))
            blocks = parse_data_blocks(infile)
            if blocks is None or blocks == []:
                continue
            blocks_factory = {
                BlockType.MONITOR_CDMA.value: (self.cdma_pairs[idx], self.__parse_monitor_cdma),
            }
            for block in blocks:
                item_list, item_func = blocks_factory.get(
                    block.type.value, (0, lambda x, y: 0))
                item_func(item_list, block.content)

    def parse_cmd(self, file_list):
        self.bdc_parser = self.archlib.BDCommandParser()
        self.gdma_parser = self.archlib.GDMACommandParser()
        self.cdma_parser = self.archlib.CDMACommandParser()
        print("Parsing...")
        core_id = 0
        for infile in tqdm(file_list):
            blocks = parse_data_blocks(infile)
            if blocks is None:
                continue
            item = IterRecord()
            item.dyn_extra = []
            item.des_kv = {}
            item.dyn_data = {}
            # bmodel
            item.des_bdc = []
            item.des_gdma = []
            item.des_sdma = []
            for e in ["tiu", "gdma", "sdma"]:
                item.dyn_data.update({e: []})
            item.dyn_data["cdma"] = [[] for _ in range(self.archlib.CDMA_NUM)]

            blocks_factory = {
                # ============= pmu =============
                BlockType.MONITOR_BD.value: (item.monitor_bd, self.__parse_monitor_tiu),
                BlockType.MONITOR_GDMA.value: (item.monitor_gdma, self.__parse_monitor_gdma),
                BlockType.MONITOR_SDMA.value: (item.monitor_sdma, self.__parse_monitor_sdma),
                # BlockType.MONITOR_CDMA.value: (item.monitor_cdma, self.__parse_monitor_cdma),
                # ============= recorded during runtime =============
                BlockType.DYN_EXTRA.value: (item.dyn_extra, self.__parse_dyn_extra),
                BlockType.DYN_DATA.value: (item, self.__parse_dyn_data),
                # ============= tpudnn des map =============
                BlockType.BLOCK_DES_KV.value: (item.des_kv, self.__parse_kvdes_data),
                # ============= bmodel =============
                BlockType.BLOCK_DES_BDC.value: (item.des_bdc, lambda l, raw_data: l.extend(self.bdc_parser.parse(raw_data))),
                BlockType.BLOCK_DES_GDMA.value: (item.des_gdma, lambda l, raw_data: l.extend(self.gdma_parser.parse(raw_data))),
                BlockType.BLOCK_DES_SDMA.value: (item.des_sdma, lambda l, raw_data: l.extend(self.gdma_parser.parse(raw_data))),
            }
            for block in blocks:
                item_list, item_func = blocks_factory.get(
                    block.type.value, (0, lambda x, y: 0))
                item_func(item_list, block.content)
            if self.is_bmodel:
                self.__match_bmodel_sections(item)
            else:
                self.__match_pmu_sections(item, core_id)

            core_id += 1

    def parse(self, in_dir):
        def sort_key_func(filename):
            numbers = re.findall(r'\d+', filename)
            return [int(num) for num in numbers]
        self.in_dir = in_dir
        if not os.path.exists(in_dir):
            logging.fatal("'{}' does not exist".format(in_dir))
            exit(-1)
        global_file_path = os.path.join(in_dir, self.global_filename)
        self.__parse_global_file(global_file_path)
        blocked_cmd = sorted(glob.glob(in_dir + "/cdmlib*.profile"), key=sort_key_func)
        cdma_cmd = sorted(glob.glob(in_dir + "/cdma*.profile"), key=sort_key_func)
        if cdma_cmd:
            self.parse_cdma_pmu(cdma_cmd)
        if blocked_cmd:
            self.parse_cmd(blocked_cmd)
        # omit_sys
        self.omit_sys(self.cdma_pairs, self.archlib.cdma_sys_code)
        remain = True
        if all(not sub for sub in self.cdma_pairs):
            remain = False
        self.omit_sys(self.bd_pairs, self.archlib.bd_sys_code, remain)
        self.omit_sys(self.gdma_pairs, self.archlib.dma_sys_code, remain)
        self.omit_sys(self.sdma_pairs, self.archlib.dma_sys_code, remain)

    def to_txt(self, out_dir):
        assert self.bd_pairs != [] and self.gdma_pairs != [], ""
        self.__align_core_time()
        self.__shift_time()
        self.out_dir = out_dir
        # make file
        Path(self.out_dir).mkdir(parents=True, exist_ok=True)
        dma_file = os.path.join(self.out_dir, "tdmaRegInfo_{}.txt")
        tiu_file = os.path.join(self.out_dir, "tiuRegInfo_{}.txt")
        cdma_file = os.path.join(self.out_dir, "cdmaRegInfo_{}.txt")
        # write engine info
        print("Write engine info...")
        for idx, pair in tqdm(enumerate(self.gdma_pairs)):
            self.__write_engine_info(dma_file, idx, pair, self.archlib.EngineType.GDMA)
        for idx, pair in tqdm(enumerate(self.sdma_pairs)):
            self.__write_engine_info(dma_file, idx, pair, self.archlib.EngineType.SDMA, False)
        for idx, pair in tqdm(enumerate(self.bd_pairs)):
            self.__write_engine_info(tiu_file, idx, pair, self.archlib.EngineType.BD)
        for idx, pair in tqdm(enumerate(self.cdma_pairs)):
            self.__write_engine_info(cdma_file, idx, pair, self.archlib.EngineType.CDMA)
        # write cpu info
        cpu_file = os.path.join(self.out_dir, "cpuInfo_{}.txt")
        for i, cdm_cpu in enumerate(self.cdmlib_extra):
            with open(cpu_file.format(i), 'w') as f:
                for j in cdm_cpu:
                    info = f"core: {i} type: {self.archlib.DynRecordType(j.type).name:<14} " \
                        f"{self.archlib.EngineType(j.engine).name:<5} " \
                        f"cmd_type: {j.des_tsk_typ:<2}:{j.des_tsk_eu_typ:>2}   " \
                        f"inst_id: {f'{j.inst_id!s:<6}' if isinstance(j.inst_id, dict) else f'{j.inst_id:<6}'}\n"
                    f.write(info)

    def __write_engine_info(self, nfile, idx, pairs, engine, new_file=True):
        g_idx = 0
        core_id = idx
        fmode = 'w'
        if not new_file:
            fmode = 'a'
        if engine in [self.archlib.EngineType.GDMA, self.archlib.EngineType.SDMA]:
            fn = self.__get_gdma_info
            arch = self.archlib.DMA_ARCH
            tag = "__TDMA_REG_INFO__\n"
        elif engine == self.archlib.EngineType.BD:
            fn = self.__get_tiu_info
            arch = self.archlib.TIU_ARCH
            tag = "__TIU_REG_INFO__\n"
        elif engine == self.archlib.EngineType.CDMA:
            fn = self.__get_gdma_info
            arch = self.archlib.DMA_ARCH
            tag = "__CDMA_REG_INFO__\n"
            core_id = self.cdma_cord_id
        else:
            raise ValueError(f"Not support parse {self.archlib.EngineType(engine).name} now.")
        if len(pairs):
            with open(nfile.format(idx), fmode) as f:
                if new_file:
                    f.write("__CHIP_ARCH_ARGS__\n")
                    f.write("".join(f"\t{key}: {value}\n" for key,
                            value in arch.items()))
                for p in pairs:
                    info, extra = fn(p, p.cmd if hasattr(p, "cmd") else None, engine.value)
                    info["Global Idx"] = g_idx
                    g_idx += 1
                    info["Core Id"] = core_id
                    f.write(tag)
                    f.write(
                        "".join(f"\t{key}: {value}\n" for key, value in info.items()))
                    if extra is not None:
                        f.write('{}:\n'.format(info["Function Type"]))
                        f.write(
                            "".join(f"\t{key}: {value}\n" for key, value in extra.items()))

    def __align_core_time(self):
        assert(len(self.profile_sync_points) == len(self.bd_pairs))
        for i, (bd_pair, gdma_pair, cycle) in enumerate(zip(self.bd_pairs, self.gdma_pairs, self.profile_sync_points)):
            if i == 0:
                continue
            delta_cyle = cycle - self.profile_sync_points[0]
            for j1 in itertools.chain(bd_pair, gdma_pair):
                j1.inst_start_time = int(j1.inst_start_time - delta_cyle)
                j1.inst_end_time = int(j1.inst_end_time - delta_cyle)
        for i, (sdma, cycle) in enumerate(zip(self.sdma_pairs, self.profile_sync_points)):
            if i == 0:
                continue
            delta_cyle = cycle - self.profile_sync_points[0]
            for j1 in sdma:
                j1.inst_start_time = int(j1.inst_start_time - delta_cyle)
                j1.inst_end_time = int(j1.inst_end_time - delta_cyle)
        for cdma in self.cdma_pairs:
            cycle = self.profile_sync_points[self.cdma_cord_id]
            delta_cyle = cycle - self.profile_sync_points[0]
            for j1 in cdma:
                j1.inst_start_time = int(j1.inst_start_time - delta_cyle)
                j1.inst_end_time = int(j1.inst_end_time - delta_cyle)

    def __shift_time(self):
        start_cycle = math.inf
        # start_cycle = self.gdma_pairs[0][0].inst_start_time
        for idx, (bd_pair, gdma_pair, sdma_pair) in enumerate(zip(self.bd_pairs, self.gdma_pairs, self.sdma_pairs)):
            if bd_pair:
                start_cycle = min(bd_pair[0].inst_start_time, start_cycle)
            if gdma_pair:
                start_cycle = min(gdma_pair[0].inst_start_time, start_cycle)
            if sdma_pair:
                start_cycle = min(sdma_pair[0].inst_start_time, start_cycle)

        for _, (bd_pair, gdma_pair) in enumerate(zip(self.bd_pairs, self.gdma_pairs)):
            for j1 in itertools.chain(bd_pair, gdma_pair):
                j1.inst_start_time = int(j1.inst_start_time - start_cycle)
                j1.inst_end_time = int(j1.inst_end_time - start_cycle)
                assert(j1.inst_start_time >= 0 and j1.inst_end_time >= 0)
        for sdma_pair in self.sdma_pairs:
            for j1 in sdma_pair:
                j1.inst_start_time = int(j1.inst_start_time - start_cycle)
                j1.inst_end_time = int(j1.inst_end_time - start_cycle)
                assert(j1.inst_start_time >= 0 and j1.inst_end_time >= 0)
        for cdma_pair in self.cdma_pairs:
            for j1 in cdma_pair:
                j1.inst_start_time = int(j1.inst_start_time - start_cycle)
                j1.inst_end_time = int(j1.inst_end_time - start_cycle)

    def __parse_dyn_data(self, item: dict, raw_data):
        # Notice:
        # pmu: bd gdma sdma start idx == 0, cdma strat idx == 1
        # des_cmd: strat idx == 1
        pio_tiu_cmd_id = 0
        pio_gdma_cmd_id = 0
        pio_sdma_cmd_id = 0
        pio_cdma_cmd_id = [0 for _ in range(self.archlib.CDMA_NUM)]

        # todo id walkaround
        tiu = item.dyn_data["tiu"]
        gdma = item.dyn_data["gdma"]
        sdma = item.dyn_data["sdma"]
        cdma = item.dyn_data["cdma"]
        tmp = parse_fixed_length_items(raw_data, self.archlib.ProfileFormat)
        dyn_extra_idx = 0
        for idx in range(len(tmp)):
            node = tmp[idx]
            if (node is None):
                continue
            node_tpye = self.archlib.DynRecordType(node.type)
            # nomal pio tiu/gdma/sdma/vsdma/cdma node
            if node_tpye == self.archlib.DynRecordType.NODE_SET:
                engine = self.archlib.EngineType(node.engine)
                if item.dyn_extra:
                    node.detailed_cmd = item.dyn_extra[dyn_extra_idx].content
                    dyn_extra_idx += 1
                if engine == self.archlib.EngineType.BD:
                    node.inst_id = pio_tiu_cmd_id
                    pio_tiu_cmd_id += 1
                    tiu.append(node)
                elif engine == self.archlib.EngineType.GDMA:
                    node.inst_id = pio_gdma_cmd_id
                    pio_gdma_cmd_id += 1
                    gdma.append(node)
                elif engine in [self.archlib.EngineType.SDMA,
                                    self.archlib.EngineType.VSDMA]:
                    node.inst_id = pio_sdma_cmd_id
                    pio_sdma_cmd_id += 1
                    sdma.append(node)
                elif engine == self.archlib.EngineType.CDMA:
                    port = node.extra_info >> 8
                    node.port = port
                    node.inst_id = pio_cdma_cmd_id[port]
                    pio_cdma_cmd_id[port] += 1
                    cdma[port].append(node)
            # id reset
            elif node_tpye == self.archlib.DynRecordType.ID_RESET:
                engine = self.archlib.EngineType(node.engine)
                if engine == self.archlib.EngineType.BD:
                    pio_tiu_cmd_id = 0
                elif engine == self.archlib.EngineType.GDMA:
                    pio_gdma_cmd_id = 0
                elif engine in [self.archlib.EngineType.SDMA,
                                    self.archlib.EngineType.VSDMA]:
                    pio_sdma_cmd_id = 0
                elif engine == self.archlib.EngineType.CDMA:
                    pio_cdma_cmd_id[node.extra_info >> 8]  = 0
            # dispatch des node
            elif self.archlib.ProfileFormat.is_des(node_tpye) :
                self.archlib.ProfileFormat.offset(node)
                self.archlib.ProfileFormat.cmd_num(node, tmp[idx + 1])
                tmp[idx + 1] = None
                pio_tiu_cmd_id = 0
                pio_gdma_cmd_id = 0
                pio_sdma_cmd_id = 0
                pio_cdma_cmd_id = [0 for _ in range(self.archlib.CDMA_NUM)]
                if node_tpye == self.archlib.DynRecordType.DES_TIU:
                    tiu.append(node)
                elif node_tpye == self.archlib.DynRecordType.DES_GDMA:
                    gdma.append(node)
                elif node_tpye == self.archlib.DynRecordType.DES_SDMA:
                    sdma.append(node)
                elif node_tpye == self.archlib.DynRecordType.DES_CDMA:
                    cdma[node.port].append(node)

    def __parse_kvdes_data(self, kv_data: List, raw_data):
        header_size = 12
        key, cmd_num, id = st.unpack(
            "III", raw_data[0:header_size])
        if key not in kv_data:
            kv_data[key] = {}
        kv_data[key].update({cmd_num: DesCommon(cmd_num, id, raw_data[header_size:])})

    def __veryfy_cmd_id(self, data):
        delta_id = 0
        last_id = 0
        for c in data:
            if last_id > 65000 and c.inst_id < 1000:
                    delta_id += 65536
            last_id = c.inst_id
            c.inst_id += delta_id

    def __veryfy_time(self, data):
        last_time = 0
        delta_time = 0
        uint32_max = 4294967295
        for c in data:
            current_time = c.inst_start_time + delta_time
            if current_time < last_time:
                delta_time += uint32_max # uint32 max
            c.inst_start_time += delta_time
            c.inst_end_time += delta_time
            if c.inst_end_time < c.inst_start_time:
               # start not overflow but end does
               c.inst_end_time += uint32_max
            last_time = c.inst_end_time

    def __veryfy_cdma_time(self, data):
        last_st = 0
        last_et = 0
        delta_time = 0
        uint32_max = 4294967295
        for c in data:
            current_st = c.inst_start_time + delta_time
            current_et = c.inst_end_time + delta_time
            if current_st < last_st and current_et < last_et:
                delta_time += uint32_max # uint32 max
            c.inst_start_time += delta_time
            c.inst_end_time += delta_time
            if c.inst_end_time < c.inst_start_time:
               # start not overflow but end does
               c.inst_end_time += uint32_max
            last_st = c.inst_start_time
            last_et = c.inst_end_time

    def __adjust_send_retire(self, data):
        n = len(data)
        for i in range(1, n-1):
            prev = data[i-1]
            curr = data[i]
            next_item = data[i+1]
            diff_curr = curr.inst_start_time - prev.inst_end_time
            diff_next = next_item.inst_start_time - prev.inst_end_time
            swap = False
            if diff_next < diff_curr and diff_curr > 0 and diff_next > 0:
                # for pattern
                # idx 5, start_time 537518, end_time 537529, id 6
                # idx 6, start_time 12597074, end_time 12597323, id 7
                # idx 7, start_time 537537, end_time 12597392, id 8
                swap = True
            elif diff_curr < 0 and diff_next > 0 and next_item.inst_start_time - next_item.inst_end_time > 0:
                # for pattern
                # idx 25, start_time 574014514, end_time 574014525, id 26
                # idx 26, start_time 409063878, end_time 409064152, id 27
                # idx 27, start_time 574014533, end_time 409064196, id 28
                swap = True
            if swap:
                data[i], data[i+1] = data[i+1], data[i]

    def __parse_monitor_tiu(self, monitor_tiu: List, raw_data):
        tmp = parse_monitor_bd(raw_data, self.archlib)
        self.__veryfy_cmd_id(tmp)
        self.__veryfy_time(tmp)
        monitor_tiu.append(tmp)

    def __parse_monitor_cdma(self, monitor_cdma: List, raw_data):
        tmp = parse_monitor_cdma(raw_data, self.archlib)
        self.__veryfy_cmd_id(tmp)
        self.__adjust_send_retire(tmp)
        self.__veryfy_cdma_time(tmp)
        self.__adjust_cmd_id(tmp)
        monitor_cdma.extend(tmp)

    def __parse_monitor_dma_base(self, raw_data):
        tmp = parse_monitor_gdma(raw_data, self.archlib)
        self.__veryfy_cmd_id(tmp)
        # self.__veryfy_time(tmp)
        return tmp

    def __parse_monitor_gdma(self, monitor_gdma: List, raw_data):
        tmp = self.__parse_monitor_dma_base(raw_data)
        self.__veryfy_time(tmp)
        monitor_gdma.append(tmp)

    def __parse_monitor_sdma(self, monitor_sdma: List, raw_data):
        tmp = self.__parse_monitor_dma_base(raw_data)
        self.__adjust_send_retire(tmp)
        self.__veryfy_time(tmp)
        self.__adjust_cmd_id(tmp)
        monitor_sdma.append(tmp)

    def __parse_dyn_extra(self, dyn_extra_data: List, raw_data):
        tmp = parse_dyn_extra(raw_data, True)
        dyn_extra_data.extend(tmp)

    def __parse_global_file(self, filename):
        assert os.path.isfile(filename), filename
        re_arch = re_key_value("", "arch")
        ginfo = GlobalInfo()
        with open(filename) as f:
            for self.line in f:
                if len(self.line) == 0:
                    continue
                if "bmodel" in self.line:
                    self.is_bmodel = True
                if self.match(re_arch) and self.archlib is None:
                    ginfo.set_arch(self.enum_val("arch", Arch))
                    self.archlib = ginfo.archlib
                    break

    @staticmethod
    def __get_cmd_type(cmd):
        des_tsk_typ, des_tsk_eu_typ = -1, -1
        if hasattr(cmd, 'reg'):
            if hasattr(cmd.reg, 'tsk_typ'):
                des_tsk_typ = cmd.reg.tsk_typ
                des_tsk_eu_typ = cmd.reg.tsk_eu_typ
            if hasattr(cmd.reg, 'cmd_type'):
                des_tsk_typ = cmd.reg.cmd_type
                des_tsk_eu_typ = cmd.reg.cmd_special_function
        else:
            des_tsk_typ = cmd.des_tsk_typ
            des_tsk_eu_typ = cmd.des_tsk_eu_typ
        return des_tsk_typ, des_tsk_eu_typ

    def correct_ids(self, data):
        data.sort(key=lambda x: x["start_time"])
        next_id = 1
        id_mapping = {}

        for record in data:
            original_id = record["id"]
            if original_id not in id_mapping:
                id_mapping[original_id] = next_id
                next_id += 1
            record["id"] = id_mapping[original_id]

        for i in range(len(data)):
            if data[i]["id"] == id_mapping[8] and data[i]["start_time"] > data[i - 1]["start_time"]:
                data[i - 1], data[i] = data[i], data[i - 1]

        return data

    @staticmethod
    def __adjust_cmd_id(monitor):
        lens = len(monitor)
        for i, m in enumerate(monitor):
            # if pre and m.inst_id < pre.inst_id and pre.thread_id == 1:
            # compatiable code for vsdma pmu receive thread_id == 0
            # 17, 18, 6, 19, 7, 8, 9, 1, 2, 0, 1, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 17, 16, 18, 21, 19, 1, 2, 3, 4, 6, 5, 7, 17, 18, 0, 19, 20, 17, 18, 0, 0, 19, 14, 15, 16, 17, 18, 0, 19, 1, 2, 3, 4, 15, 16, 17, 18, 0, 19
            # 17, 18, 19, 6, 7, 8, 9, 1, 2, 0, 1, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 21, 1, 2, 3, 4, 5, 6, 7, 17, 18, 19, 20, 0, 17, 18, 0, 0, 19, 14, 15, 16, 17, 18, 19, 0, 1, 2, 3, 4, 15, 16, 17, 18, 19, 0
            if i - 1 >= 0 and m.inst_id < monitor[i-1].inst_id:
                #  15, 17, 16, -> 15, 16, 17
                if i - 2 >= 0 and m.inst_id - monitor[i-2].inst_id == 1:
                    monitor[i], monitor[i-1] = monitor[i-1], monitor[i]
                #  18, 0, 19, 1 -> 18, 19, 0, 1
                elif i + 1 < lens and monitor[i+1].inst_id - monitor[i-1].inst_id == 1:
                    monitor[i], monitor[i+1] = monitor[i+1], monitor[i]

    def omit_sys(self, pairs, sys_code, remain=False):
        for p in pairs:
            self.__omit_sys(p, sys_code, remain, end=True)
            self.__omit_sys(p, sys_code, remain, end=False) # omit sys at begin

    def __omit_sys(self, pairs, sys_code, remain, end):
        extra_sys = []
        part = []
        idxs = range(len(pairs))
        if end:
            idxs = idxs[::-1]
        for i in idxs:
            if not hasattr(pairs[i], "cmd"):
                break
            tsk_type, _ = self.__get_cmd_type(pairs[i].cmd)
            if tsk_type != sys_code:
                break
            else:
                part.append(i)
            if end and pairs[i].inst_id == 0:
                extra_sys.extend(part)
                part = []
        if not end:
            extra_sys.extend(part)
            extra_sys = extra_sys[::-1]
        for i in extra_sys:
            if len(pairs) > 2 or not remain:
                pairs.pop(i)

    def __match_pmu_sections(self, item, core_id):
        init_num = self.archlib.profile_init_cmd_num
        if item.monitor_bd and len(item.monitor_bd[0]):
            # get alignment point
            wait_point = item.monitor_bd[0][init_num - 1]
            self.profile_sync_points.append(wait_point.inst_end_time)
        tiu_cmd = item.dyn_data["tiu"][init_num:]
        gdma_cmd = item.dyn_data["gdma"][init_num:]
        sdma_cmd = item.dyn_data["sdma"][init_num:]
        cdma_cmd = item.dyn_data["cdma"]

        tiu_pmu = item.monitor_bd[0][init_num:]
        gdma_pmu = item.monitor_gdma[0][init_num:]
        sdma_pmu = item.monitor_sdma[0][init_num:]
        # first, match cdma and omit sdma send
        if not all(not sub for sub in cdma_cmd) or core_id == self.archlib.CORE_NUM - 1:
            for port in range(len(self.cdma_pairs)):
                if len(self.cdma_pairs[port]) > 1:
                    # tx_wait (wait, nop)
                    self.cdma_pairs[port] = self.cdma_pairs[port][init_num:]
                    _cdma_cmd = cdma_cmd[port][init_num:]
                    # vsdma_send
                    sdma_pmu = sdma_pmu[1:]
                    sdma_cmd = sdma_cmd[1:]
                    self.sections_pairing(self.cdma_pairs[port], _cdma_cmd, item.des_kv, self.cdma_parser)
                    self.cdma_cord_id = core_id   
        # todo bmodel if len(tiu_cmd) == 0?
        # second match the rest engine
        self.sections_pairing(tiu_pmu, tiu_cmd, item.des_kv, self.bdc_parser)
        self.sections_pairing(gdma_pmu, gdma_cmd, item.des_kv, self.gdma_parser)
        self.sections_pairing(sdma_pmu, sdma_cmd, item.des_kv, self.gdma_parser)
        self.bd_pairs.append(tiu_pmu)
        self.gdma_pairs.append(gdma_pmu)
        self.sdma_pairs.append(sdma_pmu)

    def __match_sections(self, monitor, cmd):
        m, n = len(monitor), len(cmd)
        dp = [[float('inf')] * (n + 1) for _ in range(m + 1)]
        path = [[None] * (n + 1) for _ in range(m + 1)]

        dp[0][0] = 0
        for i in range(1, m + 1):
            dp[i][0] = i
            path[i][0] = (i - 1, 0)
        for j in range(1, n + 1):
            dp[0][j] = j
            path[0][j] = (0, j - 1)

        for i in range(1, m + 1):
            for j in range(1, n + 1):
                if monitor[i - 1][0] == cmd[j - 1][0]:
                    dp[i][j] = dp[i - 1][j - 1]
                    path[i][j] = (i - 1, j - 1)
                else:
                    options = [
                        (dp[i - 1][j] + 1, (i - 1, j)),
                        (dp[i][j - 1] + 1, (i, j - 1)),
                        (dp[i - 1][j - 1] + 2, (i - 1, j - 1))
                    ]
                    dp[i][j], path[i][j] = min(options, key=lambda x: x[0])

        i, j = m, n
        result = []
        while i > 0 or j > 0:
            prev_i, prev_j = path[i][j]
            if prev_i == i - 1 and prev_j == j - 1:
                result.append((monitor[i - 1][1], cmd[j - 1][1]))
            elif prev_i == i - 1:
                result.append((monitor[i - 1][1], None))
            # for debug purpose none_pmu, cmd
            # else:
            #     result.append((None, cmd[j - 1][1]))
            i, j = prev_i, prev_j

        result.reverse()
        return result

    def match_sections(self, monitor, des_cmd):
        def get_sections(data):
            sections = []
            id_slice = []
            idx_slice = []
            for idx, item in enumerate(data):
                if item is None:
                    continue
                if hasattr(item, "offset"): # for descmd
                    if idx_slice:
                        sections.append([id_slice[-1] - id_slice[0] + 1,  idx_slice])
                    sections.append([item.cmd_num,  [idx]])
                    idx_slice, id_slice = [], []
                elif hasattr(item, "cmd"):  # for pmu, skip matched
                    continue
                else:
                    id = get_cmd_id(item)
                    if id_slice and id < id_slice[-1]:
                        sections.append([id_slice[-1] - id_slice[0] + 1, idx_slice])
                        idx_slice, id_slice = [], []
                    id_slice.append(id)
                    idx_slice.append(idx)
            if idx_slice:
                sections.append([id_slice[-1] - id_slice[0] + 1, idx_slice])
            return sections
        _monitor = get_sections(monitor)
        _des_cmd = get_sections(des_cmd)
        # print("++++++++++++ in get_sections", len(monitor), len(des_cmd))
        # print("======= m =======: \n", [i[0] for i in _monitor])
        # print("======= c =======: \n", [i[0] for i in _des_cmd])
        pairs = self.__match_sections(_monitor, _des_cmd)
        return pairs

    def sections_pairing(self, monitor, cmd, kv_des=None, parser=None):
        if cmd is None:
            return monitor
        for monitor_idx, cmd_idx in self.match_sections(monitor, cmd):
            if monitor_idx is None:
                continue
            if cmd_idx is None:
                if self.is_bmodel:  # bmodel will drop unknow pairs
                    for idx in monitor_idx:
                        monitor[idx] = None
                continue
            # len(cmd) >= len(pmu) cause pmu will drop some data
            m_start_idx = monitor[monitor_idx[0]].inst_id
            for i, midx in enumerate(monitor_idx):
                if i == 0:
                    m_start_idx = monitor[midx].inst_id
                    _cmd = cmd
                    c = _cmd[cmd_idx[i]]
                    if hasattr(c, "offset"):
                        if kv_des is None or parser is None:
                            continue
                        offset = c.offset
                        cmd_num = c.cmd_num
                        _cmd = kv_des.get(offset, {}).get(cmd_num)
                        if _cmd:
                            _cmd = kv_des[offset][cmd_num].parse(parser)
                        else:
                            continue
                        cmd_idx = range(len(_cmd))
                relative_idx = monitor[midx].inst_id - m_start_idx # relative idx
                if relative_idx <= len(cmd_idx):
                    monitor[midx].cmd = _cmd[cmd_idx[relative_idx]]
        if self.is_bmodel:
            monitor[:] = [item for item in monitor if item is not None]

    def __match_bmodel_sections(self, item):
        init_num = self.archlib.profile_init_cmd_num
        if item.monitor_bd and len(item.monitor_bd[0]):
            # get alignment point
            wait_point = item.monitor_bd[0][init_num - 1]
            self.profile_sync_points.append(wait_point.inst_end_time)
        tiu_pmu = item.monitor_bd[0][init_num:]
        gdma_pmu = item.monitor_gdma[0][init_num:]
        sdma_pmu = item.monitor_sdma[0][init_num:]

        self.sections_pairing(tiu_pmu, item.des_bdc)
        self.sections_pairing(gdma_pmu, item.des_gdma)
        self.sections_pairing(sdma_pmu, item.des_sdma)

        self.bd_pairs.append(tiu_pmu)
        self.gdma_pairs.append(gdma_pmu)
        self.sdma_pairs.append(sdma_pmu)


    def __get_gdma_info(self, monitor_info, reg_info, engine_id=1):
        if reg_info is None:
            return get_dma_info_dyn(monitor_info, reg_info, engine_id)
        if hasattr(reg_info, "extra_info"):
            if hasattr(reg_info, 'detailed_cmd') and engine_id != 4:
                _reg_info = self.gdma_parser.parse(reg_info.detailed_cmd)[0]
                return get_dma_info(monitor_info, _reg_info, engine_id)
            return get_dma_info_dyn(monitor_info, reg_info, engine_id)
        else:
            return get_dma_info(monitor_info, reg_info, engine_id)

    def __get_tiu_info(self, monitor_info, reg_info, engine_id=0):
        if reg_info is None:
            return get_tiu_info_dyn(monitor_info, reg_info)
        if hasattr(reg_info, "extra_info"):
            if hasattr(reg_info, 'detailed_cmd'):
                _reg_info = self.bdc_parser.parse(reg_info.detailed_cmd)[0]
                return get_tiu_info(monitor_info, _reg_info)
            return get_tiu_info_dyn(monitor_info, reg_info)
        else:
            return get_tiu_info(monitor_info, reg_info)


if __name__ == "__main__":
    bmProfile = BMProfileParserPerfAI()
    bmProfile.parse("/workspace/workdir/prf/cdm_profile_data-0_core8")
    # bmProfile.to_txt('tmp')
