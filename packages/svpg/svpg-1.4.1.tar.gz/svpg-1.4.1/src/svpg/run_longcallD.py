# #!/usr/bin/env python3
# import os
# import subprocess
# import concurrent.futures
# import re
#
# def run_longcall(part_path, ref, bam, workdir):
#     """运行 longcallD call 命令"""
#     out_vcf = os.path.join(workdir, f"{os.path.basename(part_path)}.vcf")
#     cmd = [
#         "/home/huheng/download/longcallD-v0.0.6_x64-linux/longcallD",
#         "call", "-t16", ref, bam,
#         "--region-file", part_path,
#     ]
#     try:
#         subprocess.run(cmd, check=True, stdout=open(out_vcf, "w"))
#         return out_vcf
#     except subprocess.CalledProcessError:
#         print(f"[WARN] longcallD failed on {part_path}")
#         return None
#
#
# def merge_and_filter(vcfs, merged_vcf_path):
#     """合并并过滤VCF，只保留含SVLEN且abs(SVLEN)≥50的行"""
#     header_written = False
#     with open(merged_vcf_path, "w") as out:
#         for vcf in vcfs:
#             with open(vcf) as f:
#                 for line in f:
#                     if line.startswith("#"):
#                         if not header_written:
#                             out.write(line)
#                         continue
#                     if "SVLEN=" in line:
#                         m = re.search(r"SVLEN=(-?\d+)", line)
#                         if m and abs(int(m.group(1))) >= 50:
#                             out.write(line)
#             header_written = True
#     print(f"[INFO] 合并完成: {merged_vcf_path}")
#
#
# def run_task(options, merged_intervals):
#     reg_temp = f"{options.working_dir}/reg_temp.bed"
#
#     # --- 写入合并后的 bed 文件 ---
#     with open(reg_temp, "w") as bed:
#         for contig, start, end, svt, _ in merged_intervals:
#             bed.write(f"{contig}\t{start}\t{end}\t{svt}\n")
#
#     # --- 拆分 bed 文件，每1000行 ---
#     split_cmd = (
#         f"split -l 1000 {reg_temp} {options.working_dir}/reg_part_ --additional-suffix=.bed"
#     )
#     os.system(split_cmd)
#
#     # --- 收集所有拆分的 bed 文件 ---
#     bed_parts = sorted(
#         f for f in os.listdir(options.working_dir)
#         if f.startswith("reg_part_") and f.endswith(".bed")
#     )
#
#     print(f"[INFO] 检测到 {len(bed_parts)} 个拆分区块，准备并行执行 longcallD")
#
#     # --- 并行执行 longcallD ---
#     vcfs = []
#     with concurrent.futures.ProcessPoolExecutor(max_workers=options.num_threads) as executor:
#         futures = {
#             executor.submit(run_longcall,
#                             os.path.join(options.working_dir, part),
#                             options.ref,
#                             options.bam,
#                             options.working_dir): part
#             for part in bed_parts
#         }
#
#         for fut in concurrent.futures.as_completed(futures):
#             result = fut.result()
#             if result:
#                 vcfs.append(result)
#
#     # --- 过滤和合并 ---
#     merged_vcf = os.path.join(options.working_dir, "call_regs_merged.vcf")
#     merge_and_filter(vcfs, merged_vcf)
#
#     # --- 清理临时文件 ---
#     for f in bed_parts + [reg_temp] + vcfs:
#         try:
#             os.remove(os.path.join(options.working_dir, os.path.basename(f)))
#         except FileNotFoundError:
#             pass
#
#     print("[INFO] 所有任务完成 ✅")
#
#
import pysam
import pyabpoa
from collections import defaultdict
from svpg.SVCollect import decompose_cigars
from svpg.output_vcf import Candidate
import warnings
import numpy as np
from sklearn.exceptions import ConvergenceWarning
from math import log10

def svtype_to_code(svtype: str) -> int:
    """把SV类型映射为整数"""
    sv_map = {"DEL": 0, "INS": 1}
    return sv_map.get(svtype, 2)

def normalize_position(pos, start, end):
    """把位点归一化到 [0,1]"""
    return abs(pos - start) / max(1, (end - start))

def build_read_feature_vectors(read_sigs, region_start, region_end):
    """
    输入：
      read_sigs: dict[read_name] = [ { 'svtype': 'DEL', 'start': int, 'svlen': int }, ... ]
      region_start, region_end: 当前LCR上下游区间
    输出：
      read_names, features_matrix (N×3)
    """
    read_names = []
    feature_matrix = []

    for read, sigs in read_sigs.items():
        if len(sigs) == 0:
            continue

        vecs = []
        for s in sigs:
            sv_code = svtype_to_code(s['svtype'])
            norm_pos = normalize_position(s['start'], region_start, region_end)
            norm_len = log10(abs(s['svlen']) + 1)
            vecs.append([sv_code, norm_pos, norm_len])

        # 对该read取平均特征向量
        vec = np.mean(vecs, axis=0)
        feature_matrix.append(vec)
        read_names.append(read)

    if not feature_matrix:
        return [], np.empty((0, 3))
    return read_names, np.array(feature_matrix)


def phase_reads_by_vector_distance(read_sigs, region_start, region_end, random_state=0):
    """
    基于 (svtype, start, svlen) 向量距离的相位聚类。
    输入：
      read_sigs: dict[read_name] -> list of sig dicts
    输出：
      hap_to_reads: {1: [read names], 2: [read names]}
    """
    read_names, X = build_read_feature_vectors(read_sigs, region_start, region_end)
    if len(read_names) < 2:
        return {1: read_names, 2: []}

    # 执行 KMeans
    km = KMeans(n_clusters=2, n_init=20, random_state=random_state)
    labels = km.fit_predict(X)

    hap_to_reads = {1: [], 2: []}
    for name, label in zip(read_names, labels):
        hap_to_reads[label + 1].append(name)

    return hap_to_reads

def _extract_fragment_from_signature(sig, span_start, span_end, svtype):
    """
    从 signature 的 read_seq 根据 pos_read 和 svlen 提取片段
    返回字符串；若不可得返回 None
    """
    seq = sig.read_seq
    offset_start = span_start - sig.start
    offset_end = span_end - sig.start if svtype == 'INS' else span_end - sig.end
    left = max(0, sig.pos_read + offset_start)
    right = min(len(seq), sig.pos_read + sig.svlen + offset_end) if svtype == 'INS' else min(len(seq), sig.pos_read + offset_end)
    # left = max(0, sig.pos_read + offset_start-500)
    # right = min(len(seq), sig.pos_read + sig.svlen + offset_end+500) if svtype == 'INS' else min(len(seq), sig.pos_read + offset_end)
    middle_seq = seq[left:right]

    # ------- 拼接 -------
    # fragment = left_flank + middle_seq + right_flank
    fragment = middle_seq
    return fragment

def _msa_consensus_for_cluster(cluster_seqs, max_cons=1, aligner=None):
    """
    用 pyabpoa 对一个簇的序列进行 MSA，然后从 MSA 结果计算 consensus（按列多数投票）
    返回 consensus 字符串
    """
    if not cluster_seqs:
        return None
    if len(cluster_seqs) == 1:
        return cluster_seqs

    if aligner is None:
        aligner = pyabpoa.msa_aligner(
    # aln_mode='g',
    # is_aa=False,
    # match=1,
    # mismatch=3,
    # gap_open1=1,
    # gap_ext1=1,
    # gap_open2=24,
    # gap_ext2=1,
    # extra_b=10,
    # extra_f=0.01,
    # cons_algrm='HB'
)
    # 按长度排序以优化内部表现
    parts = sorted([(len(s), s, f'seq{i}') for i, s in enumerate(cluster_seqs)], reverse=True)
    _, seqs, names = zip(*parts)

    aln_result = aligner.msa(list(seqs), out_msa=True, out_cons=True, max_n_cons=max_cons)
    return aln_result.cons_seq

# 需要的 import
import numpy as np
from dataclasses import dataclass
from typing import List, Optional
# bindings
try:
    import pyabpoa as pa
except Exception:
    pa = None
try:
    from pywfa import WavefrontAligner
except Exception:
    WavefrontAligner = None
try:
    import edlib
except Exception:
    edlib = None

# 一个简单的 SVCall container（你也可以用之前定义的 SVCall）
@dataclass
class SVCall:
    chrom: str
    pos: int
    svtype: str
    svlen: int
    seq: Optional[str]
    hap: Optional[int]
    info: dict

# helper: 将 cigar tuples 转回对齐（pattern=cons, text=ref）
def cigartuples_to_aligned_strings(pattern: str, text: str, cigartuples):
    """
    cigartuples: list of (opcode, length) where opcodes follow pywfa:
      0=M,1=I,2=D,8=X,7=='=' etc. (pywfa README shows mapping)
    We'll interpret 0/7/8 as aligned columns, 1 as insertion (present in pattern), 2 as deletion (present in text).
    Returns: (ref_aln_str, pattern_aln_str) where '-' denotes gap.
    """
    ref_aln = []
    pat_aln = []
    pi = 0
    ti = 0
    for op, l in cigartuples:
        # pywfa mapping: 0=M,1=I,2=D,7=='=',8='X'
        if op in (0, 7, 8):  # aligned columns (match/mismatch)
            for _ in range(l):
                if ti < len(text):
                    ref_aln.append(text[ti]); ti += 1
                else:
                    ref_aln.append('-')
                if pi < len(pattern):
                    pat_aln.append(pattern[pi]); pi += 1
                else:
                    pat_aln.append('-')
        elif op == 1:  # I : insertion to ref (present in pattern/query)
            for _ in range(l):
                ref_aln.append('-')
                if pi < len(pattern):
                    pat_aln.append(pattern[pi]); pi += 1
                else:
                    pat_aln.append('-')
        elif op == 2:  # D : deletion from ref (present in text)
            for _ in range(l):
                if ti < len(text):
                    ref_aln.append(text[ti]); ti += 1
                else:
                    ref_aln.append('-')
                pat_aln.append('-')
        else:
            # fallback: treat as M
            for _ in range(l):
                ref_aln.append(text[ti] if ti < len(text) else '-'); ti += 1
                pat_aln.append(pattern[pi] if pi < len(pattern) else '-'); pi += 1
    return ''.join(ref_aln), ''.join(pat_aln)

# parse aligned strings -> SVs (类似之前的 parse_alignment_to_sv)
def parse_alignment_to_svs(ref_aln: str, pat_aln: str, ref_region_start: int, chrom: str, hap: int, min_sv_len: int = 50):
    svs = []
    i = 0
    ref_pos = ref_region_start  # 0-based mapping of first base in ref_aln
    L = len(ref_aln)
    while i < L:
        a = ref_aln[i]; b = pat_aln[i]
        if a == '-' and b != '-':
            # insertion -> collect contiguous insertion
            j = i
            ins_seq = []
            while j < L and ref_aln[j] == '-' and pat_aln[j] != '-':
                ins_seq.append(pat_aln[j])
                j += 1
            ins_seq = ''.join(ins_seq)
            if len(ins_seq) >= min_sv_len:
                svs.append(SVCall(chrom=chrom, pos=ref_pos, svtype='INS', svlen=len(ins_seq),
                                  seq=ins_seq, hap=hap, info={}))
            i = j
            # ref_pos unchanged
        elif a != '-' and b == '-':
            # deletion
            j = i
            del_seq = []
            del_len = 0
            while j < L and ref_aln[j] != '-' and pat_aln[j] == '-':
                del_seq.append(ref_aln[j]); del_len += 1
                j += 1
            if del_len >= min_sv_len:
                svs.append(SVCall(chrom=chrom, pos=ref_pos, svtype='DEL', svlen=del_len,
                                  seq=''.join(del_seq), hap=hap, info={}))
            # advance ref_pos by del_len
            ref_pos += del_len
            i = j
        else:
            # match/mismatch: advance
            if a != '-':
                ref_pos += 1
            i += 1
    return svs

# main function: abPOA consensus + WFA realign + parse
def abpoa_consensus_and_wfa_realign(seqs: List[str], ref_seq_region: str, ref_region_start: int,
                                    chrom: str, hap: int, opt_min_sv_len: int = 50, abpoa_params: dict = None):
    """
    seqs: list of read sequences for this hap
    ref_seq_region: reference substring for the region [start:end]
    ref_region_start: reference 0-based coordinate for ref_seq_region[0]
    Returns: list of SVCall objects (with hap annotated)
    """
    if abpoa_params is None: abpoa_params = {}
    # 1) abPOA MSA -> consensus
    cons_list = None
    if pa is not None:
        # create MSA aligner with parameters similar to C defaults
        a = pa.msa_aligner(
            aln_mode = abpoa_params.get("aln_mode", 'g'),
            match = abpoa_params.get("match", 2),
            mismatch = abpoa_params.get("mismatch", 6),
            gap_open1 = abpoa_params.get("gap_open1", 11),
            gap_ext1 = abpoa_params.get("gap_ext1", 1),
            gap_open2 = abpoa_params.get("gap_open2", 100),
            gap_ext2 = abpoa_params.get("gap_ext2", 1),
            extra_b = abpoa_params.get("extra_b", 10),
            extra_f = abpoa_params.get("extra_f", 0.01),
            cons_algrm = abpoa_params.get("cons_algrm", 'MF')
        )
        # run msa
        res = a.msa(seqs, out_cons=True, out_msa=False, max_n_cons=abpoa_params.get("max_n_cons", 1),
                    min_freq=abpoa_params.get("min_freq", 0.2))
        # res.cons_seq is a list of consensus strings
        try:
            cons_list = res.cons_seq if hasattr(res, 'cons_seq') else res[0].cons_seq
        except Exception:
            # fallback minor handling
            cons_list = []
            if hasattr(res, 'cons_seq'): cons_list = res.cons_seq
    else:
        # fallback: simple majority consensus (very rough)
        L = max(len(s) for s in seqs)
        cons = []
        for i in range(L):
            cnt = {}
            for s in seqs:
                if i < len(s):
                    b = s[i]
                else:
                    b = 'N'
                cnt[b] = cnt.get(b, 0) + 1
            base = max(cnt.items(), key=lambda x:x[1])[0]
            cons.append(base)
        cons_list = [''.join(cons)]

    svs_all = []
    # 2) 对每个共识做 WFA 比对到 ref region
    for cons in cons_list:
        # prefer pywfa
        if WavefrontAligner is not None:
            # pattern = consensus, text = reference (as in pywfa README example)
            a = WavefrontAligner(cons)
            result = a(ref_seq_region)  # returns result object; result.cigartuples exists
            if getattr(result, 'status', 0) != 0:
                # failed
                continue
            cigartuples = result.cigartuples
            ref_aln, pat_aln = cigartuples_to_aligned_strings(cons, ref_seq_region, cigartuples)
            # note: pywfa example uses pattern=cons, text=ref
        else:
            # fallback -> use edlib to compute path and reconstruct aligned strings
            if edlib is None:
                raise RuntimeError("既没有 pywfa 也没有 edlib 可用，无法进行 realignment")
            # edlib.align(query, target) -> we treat query=cons, target=ref
            ed_result = edlib.align(cons, ref_seq_region, mode='NW', task='path')
            if ed_result['status'] != 'OK':
                continue
            # edlib returns alignment in ed_result['alignment'] as list of ints; but edlib has helper to convert to cigar string
            path = edlib.alignment_to_cigar(ed_result['alignment'])
            # parse path like "10M1I5M..." into tuples
            import re
            ops = re.findall(r'(\d+)([MID])', path)
            cigartuples = []
            for l_s, opc in ops:
                l = int(l_s)
                if opc == 'M':
                    cigartuples.append((0, l))
                elif opc == 'I':
                    cigartuples.append((1, l))
                elif opc == 'D':
                    cigartuples.append((2, l))
            ref_aln, pat_aln = cigartuples_to_aligned_strings(cons, ref_seq_region, cigartuples)

        # Ensure the aligned strings are ref_aln (reference) and pat_aln (consensus)
        # However our parsing function expects ref_aln,target and pattern_aln, so swap if needed
        # parse and extract SVs
        svs = parse_alignment_to_svs(ref_aln, pat_aln, ref_region_start, chrom, hap, min_sv_len=opt_min_sv_len)
        svs_all.extend(svs)
    return svs_all

import mappy as mp


def align_with_mappy(ref_seq, query_seq, preset="map-hifi"):
    """
    ref_fa: 参考基因组 fasta 文件路径
    query_seq: 待比对的序列
    返回: mappy.Alignment 对象
    """
    aligner = mp.Aligner(seq=ref_seq,  preset="map-hifi",fn_idx_in=None)
    if not aligner:
        raise Exception(f"Failed to load index {ref_seq}")
    aln1, aln2 = [], []
    for seq1, seq2 in query_seq:
        # 处理 seq1
        if not seq1:  # 空串
            aln1.append(None)
        else:
            aln_primary = None
            for hit in aligner.map(seq1):
                if hit.is_primary:  # 只保留 primary
                    aln_primary = (seq1, hit)
                    break
            aln1.append(aln_primary)

        # 处理 seq2
        if not seq2:  # 空串
            aln2.append(None)
        else:
            aln_primary = None
            for hit in aligner.map(seq2):
                if hit.is_primary:
                    aln_primary = (seq2, hit)
                    break
            aln2.append(aln_primary)

    return aln1, aln2

import pywfa

def wfa_end2end_aln(pattern: str, text: str,
                    mismatch=4, gap_open=6, gap_extend=1,
                    heuristic="none", distance="affine", gap_aln="right",
                    reverse=False, verbose=False):
    """
    WFA端到端比对（仿C版wfa_end2end_aln逻辑）
    pattern: query（通常为cons或read）
    text: target（通常为ref或cons）
    """
    if reverse:
        pattern = pattern[::-1]
        text = text[::-1]

    aligner = pywfa.WavefrontAligner(
        match=0,
        mismatch=mismatch,
        gap_open=gap_open,
        gap_extend=gap_extend,
        heuristic=heuristic,        # "none" | "adaptive" | "zdrop"
        distance=distance,          # "affine" or "affine2p"
        memory_mode="ultralow" if heuristic != "zdrop" else "default"
    )

    score = aligner.align(pattern, text)
    pat_aln, text_aln = aligner.alignment_strings()

    if verbose:
        print(f"[WFA] score={score}")
        print(">pattern:", pat_aln)
        print(">text   :", text_aln)

    return {
        "score": score,
        "pattern_aln": pat_aln,
        "text_aln": text_aln,
        "cigar": aligner.cigar
    }


def wfa_collect_aln_str(target: str, query: str, full_cover: int,
                        mismatch=4, gap_open=6, gap_extend=1, ratio=1.2,
                        verbose=False):
    """
    模拟 wfa_collect_aln_str：根据full_cover选择不同的WFA模式
    full_cover:
      1/2 表示全长比对（read/cons全覆盖）
      3/4 表示部分覆盖（左或右端延伸）
    """
    if full_cover in (1, 2):  # full coverage
        return wfa_end2end_aln(query, target,
                               mismatch=mismatch, gap_open=gap_open, gap_extend=gap_extend,
                               heuristic="adaptive", distance="affine", verbose=verbose)

    else:  # partial alignment (use zdrop heuristic)
        tlen, qlen = len(target), len(query)
        # 根据partial_aln_ratio裁剪
        _tlen = min(tlen, int(qlen * ratio))
        _qlen = min(qlen, int(tlen * ratio))
        t_start = 0 if full_cover == 3 else tlen - _tlen
        q_start = 0 if full_cover == 3 else qlen - _qlen
        sub_target = target[t_start:t_start+_tlen]
        sub_query = query[q_start:q_start+_qlen]
        return wfa_end2end_aln(sub_query, sub_target,
                               mismatch=mismatch, gap_open=gap_open, gap_extend=gap_extend,
                               heuristic="zdrop", distance="affine", verbose=verbose)


def _extract_sv_from_alignment(aln):
    """
    从 pysam.AlignedSegment 中解析相对于参考的 indel，返回 list of dict:
        {'contig': aln.reference_name, 'pos': ref_pos0, 'svtype': 'DEL'/'INS', 'svlen': n, 'ref': ref_seq, 'alt': alt_seq}
    解析策略：遍历 CIGAR，从参考坐标推算 DEL；对于 INS 使用 read 中序列
    """
    a1_seq, a1_res = aln[0], aln[1]
    if a1_res.mapq < 20:
        return []
    res = []
    ref_pos = a1_res.r_st  # 0-based
    read_pos = 0
    # CIGAR tuples: (operation, length)
    cigartuples = [(length, op) for length, op in a1_res.cigar]
    for length, op in cigartuples:
        # 0=M,1=I,2=D,3=N,4=S,5=H,6=P,7==,8=X
        if op in (0, 7, 8):
            ref_pos += length
            read_pos += length
        elif op == 1 and length >= 50:  # INS in read (relative to reference)
            # extract inserted sequence from read
            insersion_seq = a1_seq[read_pos:read_pos + length]
            res.append({
                        'pos': ref_pos,  # insertion is between ref_pos-1 and ref_pos
                        'svtype': 'INS',
                        'svlen': length,
                        'read_pos': read_pos,
                        'seq': insersion_seq
                        })
            read_pos += length
        elif op == 2 and length >= 50:  # DEL from reference
            # deletion: reference bases from ref_pos .. ref_pos+length
            # we need reference sequence for ref and alt (alt is '')
            # We'll fetch reference externally by caller if needed; here just record coords
            res.append({
                        'pos': ref_pos,
                        'svtype': 'DEL',
                        'svlen': length,
                        'read_pos': read_pos,
                        })
            ref_pos += length
        elif op in (4, 5):  # soft/hard clip
            read_pos += length
        else:
            # skip others
            pass
    return res

def candidate_sv(sv, contig, ref_seq, noseqs, genotype="1/1"):
    start = sv["pos"]
    svlen = abs(sv["svlen"])
    end = start + svlen
    svtype = sv["svtype"]
    # if min_sv_length <= svlen <= max_sv_length:
    if not noseqs:
        try:
            ref_base = ref_seq[max(start - 1, 0)]
            ref_seq = ref_base if svtype == "INS" else ref_seq[max(start - 1, 0):end]
        except IndexError:
            return
        alt_seq = ref_base if svtype == "DEL" else ref_base + sv['seq']
    else:
        ref_seq = "N"
        alt_seq = "<INS>" if svtype == "INS" else "<DEL>"

    return Candidate(contig, start, end, svtype, [], ref_seq=ref_seq, alt_seq=alt_seq, genotype=genotype)

from sklearn.cluster import KMeans

def phase_reads_by_cluster_similarity(current_signature_clusters):
    """
    根据 cluster 中的 sig.read_name 聚类信息进行 read 定相
    """
    # Step 1: 构建 read -> sigs 映射
    read_to_sigs = defaultdict(list)
    for cluster in current_signature_clusters:
        for sig in cluster:
            read_to_sigs[sig.read_name].append(sig)

    read_names = list(read_to_sigs.keys())
    n_reads = len(read_names)
    n_clusters = len(current_signature_clusters)

    # Step 2: 构建特征矩阵 (n_reads × n_clusters)
    # 每个元素为1表示该read出现在该cluster中，否则0
    feature_matrix = np.zeros((n_reads, n_clusters), dtype=int)

    cluster_read_names = [set(sig.read_name for sig in cluster)
                          for cluster in current_signature_clusters]

    for i, read_name in enumerate(read_names):
        for j, cluster_reads in enumerate(cluster_read_names):
            if read_name in cluster_reads:
                feature_matrix[i, j] = 1

    # Step 3: 计算相似度得分（每行即每个read的特征向量）
    # 可以看作 signature pattern
    # Step 4: 使用k-means聚类（2个hap）
    if n_reads >= 2:
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=ConvergenceWarning)
            kmeans = KMeans(n_clusters=2, random_state=42, n_init=20)
            labels = kmeans.fit_predict(feature_matrix)

    else:
        labels = np.zeros(n_reads, dtype=int)  # 只有1个read时全为hap1

    # Step 4: 生成 read_name -> hap 编号映射
    read_to_hap = {read: (label + 1) for read, label in zip(read_names, labels)}  # hap1 / hap2

    # Step 5: 聚合同一 hap 的所有 sig
    hap_to_seqs = defaultdict(list)
    for read_name, hap_id in read_to_hap.items():
        sigs = read_to_sigs[read_name]
        span_start = max(min(s.pos_read for s in sigs)-2000, 0)
        span_end = min(max(s.pos_read for s in sigs)+2000, len(sigs[-1].read_seq))
        if sigs[-1].type == 'INS':
            frag_seq = sigs[-1].read_seq[span_start: span_end+sigs[-1].svlen]
        else:
            frag_seq = sigs[-1].read_seq[span_start: span_end]
        hap_to_seqs[hap_id].append(frag_seq)  # 将该read的所有sig加入对应hap

    return list(hap_to_seqs.values())

def merge_close_svs(svs, a_seq, max_dist=500):
    """
    链式合并相邻距离小于 max_dist 的 INS SV
    svs: list[dict]，每个 dict 包含 contig, pos, read_pos, seq, svlen, svtype
    a_seq: str，完整参考或读段序列
    """
    if not svs:
        return []

    merged = []
    i = 0
    while i < len(svs):
        # 初始化当前合并块
        current = svs[i].copy()
        start_pos = current["pos"]
        svlen = current["svlen"]
        svtype = current['svtype']

        j = i + 1
        while j < len(svs):
            next_sv = svs[j]

            # 判断与当前 sv 是否相邻（链式逻辑）
            if (svtype == next_sv['svtype']) and (next_sv["pos"] - (start_pos + svlen) < max_dist):
                # 更新合并块
                svlen = svlen + next_sv["svlen"]
                if svtype == "INS":
                    seq = current["seq"] + next_sv["seq"]

                    # 更新 current，作为新的比较基准
                    current = {
                        "pos": start_pos,
                        "svlen": svlen,
                        "seq": seq,
                        "svtype": "INS"
                    }
                else:
                    current = {
                        "pos": start_pos,
                        "svlen": svlen,
                        "svtype": "DEL"
                    }
                j += 1
            else:
                break

        merged.append(current)
        # 跳到不相邻的下一个 SV
        i = j

    return merged

def run_task(merged_intervals, ref_seq, options):

    sv_candidates = []
    haps, beds = [], []
    #start,end是lcr区域的起始和结束位置
    for contig, start, end, svtype, current_signature_clusters, _ in merged_intervals:
        if abs(811404-start)<2000:
            pass
        #过滤小于2的聚类
        # current_signature_clusters = [c for c in current_signature_clusters if len(c) >= 2]
        if len(current_signature_clusters)<3:
            continue
        hap_to_seqs = phase_reads_by_cluster_similarity(current_signature_clusters)

        # ref_seq = ref_seq[start:end]
        if not hap_to_seqs:
            continue
        cons_hp1 = _msa_consensus_for_cluster(hap_to_seqs[0])[0]
        if len(hap_to_seqs) == 1:
            continue
        cons_hp2 = _msa_consensus_for_cluster(hap_to_seqs[1])[0]
        haps.append((cons_hp1, cons_hp2))
        beds.append((start, end))
        # svs = abpoa_consensus_and_wfa_realign(
            #     seqs, ref_seq_region, start, contig, hap_id,
            #     opt_min_sv_len=options.min_sv_size,
            #     abpoa_params={"max_n_cons": 1}
            # )
            # # 将 svs 加入候选集合，或进一步注释
            # for s in svs:
            #     s.info["support_reads"] = read_names
            #     sv_candidates.append(s)

    min_sv_length, noseqs = options.min_sv_size, options.noseq
    aln1, aln2 = align_with_mappy(ref_seq, haps)
    for a1, a2, bed in zip(aln1, aln2, beds):
        start, end = bed
        if start ==2775805:
            pass
        svs1 = _extract_sv_from_alignment(a1) if a1 else []
        svs2 = _extract_sv_from_alignment(a2) if a2 else []

        # ---- 过滤区间外的 SV ----
        svs1 = [sv for sv in svs1 if start-1000 <= sv['pos'] <= end+1000]
        svs2 = [sv for sv in svs2 if start-1000 <= sv['pos'] <= end+1000]

        # Case A: 两个 hap 都有 SV
        if svs1 and svs2:
            for sv1 in svs1:
                matched = False
                for sv2 in svs2:
                    if sv1['svtype'] == sv2['svtype']:
                        # 防止 svlen 为 0 报错
                        len1, len2 = abs(sv1['svlen']), abs(sv2['svlen'])
                        if min(len1, len2) / max(len1, len2) > 0.5:
                            # 认为是同一个 SV → 1/1
                            sv_candidates.append(candidate_sv(
                                sv1, contig, ref_seq, noseqs, genotype="1/1"
                            ))
                            matched = True
                            svs2.remove(sv2)  # 避免重复匹配
                            break

                if not matched:
                    # hp1 不匹配 → 0/1
                    sv_candidates.append(candidate_sv(
                        sv1, contig, ref_seq, noseqs, genotype="0/1"
                    ))

            # hp2 中那些未匹配的 SV 也要输出 0/1
            for sv2 in svs2:
                # matched = any(
                #     sv1['svtype'] == sv2['svtype'] and
                #     min(abs(sv1['svlen']), abs(sv2['svlen'])) /
                #     max(abs(sv1['svlen']), abs(sv2['svlen'])) > 0.7
                #     for sv1 in svs1
                # )
                # if not matched:
                sv_candidates.append(candidate_sv(
                    sv2, contig, ref_seq, noseqs, genotype="0/1"
                ))

        # Case B: 只有 hp1 有 SV → 全部 0/1
        elif svs1:
            for sv1 in svs1:
                sv_candidates.append(candidate_sv(
                    sv1, contig, ref_seq, noseqs, genotype="0/1"
                ))

        # Case C: 只有 hp2 有 SV → 全部 0/1
        elif svs2:
            for sv2 in svs2:
                sv_candidates.append(candidate_sv(
                    sv2, contig, ref_seq, noseqs, genotype="0/1"
                ))

        # Case D: 都没有 SV → 什么都不做

    return sv_candidates