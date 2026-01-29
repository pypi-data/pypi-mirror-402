"""
Prototype: 对一个 signature cluster 进行局部单倍型重构并召回带基因型的候选SV

设计说明（简要）：
- 输入: 一个 signature cluster（list），每个 signature 要求至少包含字段:
    - contig (str), start (int), end (int), svlen (int), svtype (str)
    - pos_read (int) : 断点在 read 序列上的坐标（0-based）
    - read_seq (str) : 包含该断点的原始 read 序列
    - support (int, optional) : 支持数（用于合并权重）
    - alt_seq (str, optional) : 若有可用的替代序列

- 主要步骤：
    1. 从每个 signature 的 read_seq 提取断点前后 buffer(bp) 的片段
    2. 对片段去重并按相似性/支持聚成最多2簇
    3. 对每簇运行 abPOA（pyabpoa）得到 MSA，然后从 MSA 计算 consensus（候选 hap）
    4. 将每个候选 hap 比对回参考（使用 minimap2 -a 输出 SAM），解析 CIGAR 提取相对于参考的 indel
    5. 将从两个 hap 得到的变异做比较并给出基因型 (0/0,0/1,1/1)

输出：返回一个 list，每个元素为 dict，包含: contig,start,end,svtype,svlen,ref,alt,gt,support,notes

注意：这是一个原型模块，适合作为 pipeline 中的插入点。要求环境中安装:
    - pysam
    - pyabpoa
    - minimap2 (在 PATH)

"""

import os
import shutil
import tempfile
import subprocess
from collections import Counter, defaultdict
from difflib import SequenceMatcher

import pysam
import pyabpoa
from svpg.output_vcf import Candidate


def _ensure_minimap2():
    if shutil.which('minimap2') is None:
        raise RuntimeError('minimap2 not found in PATH. Please install minimap2 and ensure it is reachable.')


def _fetch_reference_window(ref_seq, start, end, buffer=300):
    s = max(0, start - buffer)
    e = end + buffer
    seq = ref_seq[s:e]
    return seq


def _extract_fragment_from_signature(sig, span_start, span_end, svtype, left_flank, right_flank, buffer=300):
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

import parasail

def align_read_to_target_parasail(read, target, match=1, mismatch=-3, gap_open=1, gap_extend=0):
    """
    使用 parasail 做局部 (Smith-Waterman) 比对，返回 (aligned_len, score)
    score 按照 match/mismatch/gap_open/gap_extend 计算，其值与原文打分体系兼容（线性 gap 用 gap_extend=0）。
    """
    # parasail 的 matrix_create 接受正 match 与负 mismatch
    # parasail.matrix_create(alphabet, match, mismatch) expects match positive, mismatch negative
    matrix = parasail.matrix_create("ACGT", match, mismatch)
    # 使用 sw_stats 或 ssw，获取 aligned length 与 score
    # sw_stats_striped_16 等是高性能实现；这里用 sw_stats（自动选择）
    # gap_open/gap_extend 都传为正数参数（parasail 使用正整数作为惩罚）
    try:
        res = parasail.sw_stats_striped_16(read.encode(), target.encode(), gap_open, gap_extend, matrix)
    except Exception:
        # 备用直接用 sw_trace
        res = parasail.sw_trace_striped_16(read.encode(), target.encode(), gap_open, gap_extend, matrix)
    # parasail 返回的 res 具有 attributes: score, matches, ref_begin1/ref_end1, read_begin1/read_end1
    # aligned_len 可用 read_end1 - read_begin1 + 1 (若使用 0-based inclusive)
    # 注意 parasail Python bindings 有差异，先尝试常见属性
    try:
        aligned_len = (res.read_end1 - res.read_begin1 + 1)
    except Exception:
        # 尝试其他属性名（防护）
        try:
            aligned_len = (res.query_end - res.query_begin + 1)
        except Exception:
            aligned_len = max(len(read), len(target))  # 兜底（不太可能）
    score = res.score
    return aligned_len, score
class POAGraph:
    """
    封装：维护该 graph 的 reads 列表与 pyabpoa aligner / 共识
    """
    def __init__(self, pa_params=None):
        # 存储入图的原始 read 序列（strings）
        self.reads = []
        # pyabpoa aligner 参数（可扩展）
        self.pa_params = pa_params or {}
        # 当前 consensus（字符串），懒更新
        self.consensus = ""
        self._dirty = True  # 若 reads 改变，标记为需要重新计算 consensus

    def add_read(self, read):
        self.reads.append(read)
        self._dirty = True

    def get_consensus(self):
        if not self._dirty and self.consensus:
            return self.consensus
        # 用 pyabpoa 做 MSA + consensus
        a = pyabpoa.msa_aligner(**self.pa_params)
        # msa expects list of sequences
        res = a.msa(self.reads, out_cons=True, out_msa=False)
        # res.cons_seq is list of consensus(s)
        if hasattr(res, "cons_seq") and res.cons_seq:
            self.consensus = res.cons_seq[0]
        else:
            # fallback: join the most frequent read or empty
            if self.reads:
                self.consensus = max(self.reads, key=lambda x: len(x))
            else:
                self.consensus = ""
        self._dirty = False
        return self.consensus

    def support_count(self):
        return len(self.reads)


def build_poa_consensus(reads,
                        P=2,
                        max_graphs=8,
                        min_aligned_len=100,
                        min_norm_score=0.96,
                        pa_params=None,
                        scorer_params=None):
    """
    reads: list of sequence strings (trimmed reads)
    返回: list of consensus strings (最多 P)
    """
    if pa_params is None:
        # 默认 pyabpoa 参数（可按需调整）
        pa_params = dict(aln_mode='g', is_aa=False,
                         match=1, mismatch=3, gap_open1=1, gap_ext1=0,
                         gap_open2=24, gap_ext2=1, extra_b=10, extra_f=0.01,
                         cons_algrm='HB')
    if scorer_params is None:
        # scoring: 与原文相对应的 match=1, mismatch=-3, gap linear cost -1 (we map to gap_open=1, gap_ext=0)
        scorer_params = dict(match=1, mismatch=-3, gap_open=1, gap_ext=0)

    graphs = []  # list of POAGraph
    # iterate reads sequentially
    for idx, read in enumerate(reads):
        best_norm = -1.0
        best_graph = None
        best_aligned_len = 0
        # Try to score against each existing graph's consensus
        for g in graphs:
            cons = g.get_consensus()
            if not cons:
                continue
            aligned_len, score = align_read_to_target_parasail(read, cons,
                                             match=scorer_params['match'],
                                             mismatch=scorer_params['mismatch'],
                                             gap_open=scorer_params['gap_open'],
                                             gap_extend=scorer_params['gap_ext'])
            norm = (score / aligned_len) if aligned_len > 0 else 0.0
            # only consider if meets the minimal per-read aligned_len + normalized score
            if aligned_len >= min_aligned_len and norm >= min_norm_score:
                if norm > best_norm:
                    best_norm = norm
                    best_graph = g
                    best_aligned_len = aligned_len
        if best_graph is not None:
            best_graph.add_read(read)
        else:
            # not assigned -> try to create new graph if limit not reached
            if len(graphs) < max_graphs:
                newg = POAGraph(pa_params=pa_params)
                newg.add_read(read)
                graphs.append(newg)
            else:
                # drop read (filtered out)
                continue

    # filter graphs with support < 2
    graphs = [g for g in graphs if g.support_count() >= 2]
    # sort by supporting reads count
    graphs.sort(key=lambda g: g.support_count(), reverse=True)
    # take top P, compute consensus
    consensuses = []
    for g in graphs[:P]:
        consensuses.append(g.get_consensus())
    return consensuses
def _msa_consensus_for_cluster(cluster_seqs, max_cons=1, aligner=None):
    """
    用 pyabpoa 对一个簇的序列进行 MSA，然后从 MSA 结果计算 consensus（按列多数投票）
    返回 consensus 字符串
    """
    if not cluster_seqs:
        return None
    if len(cluster_seqs) == 1:
        return cluster_seqs[0]

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
    if not cluster_seqs:
        return []
    if aligner is None:
        aligner = pyabpoa.msa_aligner()

    aln_result = aligner.msa(list(seqs), out_msa=True, out_cons=True, max_n_cons=max_cons)
    return aln_result.cons_seq
    # aln_result = aligner.msa(list(seqs), out_cons=False, out_msa=True, max_n_cons=2)
    # msa_rows = aln_result.msa_seq  # list of aligned sequences (with '-')
    # if not msa_rows:
    #     # 退化情况
    #     return cluster_seqs[0]
    #
    # L = len(msa_rows[0])
    # # 逐列做多数投票，忽略 '-'，若并列取任意非 '-' 基
    # consensus_chars = []
    # for i in range(L):
    #     col = [r[i] for r in msa_rows if i < len(r)]
    #     votes = Counter([c for c in col if c != '-'])
    #     if not votes:
    #         consensus_chars.append('-')
    #     else:
    #         consensus_chars.append(votes.most_common(1)[0][0])
    # # 去掉插入在参考前后的纯 gap（首尾可能全是 '-'), 再合并连续 '-'
    # cons = ''.join(consensus_chars).strip('-')
    # # 若全部为空（可能性低），退回第一个原始序列
    # if not cons:
    #     return cluster_seqs[0]
    # return cons.replace('-', '')
import mappy as mp


def align_with_mappy(ref_seq, query_seq, preset="map-hifi"):
    """
    ref_fa: 参考基因组 fasta 文件路径
    query_seq: 待比对的序列
    返回: mappy.Alignment 对象
    """
    aligner = mp.Aligner(seq=ref_seq, preset=preset, fn_idx_in=None)
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
    # aln = []
    # for seq in query_seq:
    #     for hit in aligner.map(seq):
    #         aln.append(hit)
    # return aln
# def align_with_mappy(ref_seq, preset="map-hifi"):
#     """
#     ref_fa: 参考基因组 fasta 文件路径
#     query_seq: 待比对的序列
#     返回: mappy.Alignment 对象
#     """
#     aligner = mp.Aligner(seq=ref_seq, preset=preset, fn_idx_in=None,n_threads=64)
#     if not aligner:
#         raise Exception(f"Failed to load index {ref_seq}")
#     aln1, aln2 = [], []
#     aln_primary = None
#     for name, seq, qual in mp.fastx_read("mat.fa"):
#         for hit in aligner.map(seq):
#             # if hit.is_primary:  # 只保留 primary
#             aln_primary = (seq, hit)
#             break
#         aln1.append(aln_primary)
#     for name, seq, qual in mp.fastx_read("pat.fa"):
#         for hit in aligner.map(seq):
#             # if hit.is_primary:  # 只保留 primary
#             aln_primary = (seq, hit)
#             break
#         aln2.append(aln_primary)
#
#     return aln1, aln2

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
            # res.append({'contig': contig,
            #             'pos': ref_pos,
            #             'svtype': 'DEL',
            #             'svlen': length,
            #             'read_pos': read_pos,
            #             })
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

    return Candidate(contig, start, end, "hap", svtype, [], ref_seq, alt_seq, genotype=genotype)

def cluster_sv_lists(svs1, svs2, max_dist=500, max_len_diff_ratio=0.7):
    """
    将两个 hap 的 sv 列表聚类。
    返回 cluster 列表，每个 cluster 是 [sv1?, sv2?]，可能只有一个 sv
    """
    clusters = []
    used2 = set()

    for i, sv1 in enumerate(svs1):
        matched = False
        for j, sv2 in enumerate(svs2):
            if j in used2:
                continue
            # 判断是否属于同一个事件
            if (sv1["svtype"] == sv2["svtype"] and
                abs(sv1["pos"] - sv2["pos"]) <= max_dist and
                min(sv1['svlen'], sv2['svlen'])/max(sv1['svlen'], sv2['svlen']) >= max_len_diff_ratio):
                clusters.append((sv1, sv2))
                used2.add(j)
                matched = True
                break
        if not matched:
            clusters.append((sv1, None))

    # 把 svs2 中未匹配的也加进来, 如果sv2离sv1太远，共识序列质量太差，抛弃
    for j, sv2 in enumerate(svs2):
        # try:
        if abs(sv2["pos"] - sv1["pos"] > 2000):
            return []
        if j not in used2:
            clusters.append((None, sv2))
        # except:
        #     pass

    return clusters

def process_hap_sv(contig, ref_seq, svs1, options, svs2=None):
    """
    根据一个或两个 haplotype 的 SV 列表生成 Candidate
    svs1, svs2: list of dict (由 _extract_sv_from_alignment 得到)
    """
    sv_candidates = []
    min_sv_length, noseqs = options.min_sv_size, options.noseq
    max_sv_length = 100000 if options.max_sv_size == -1 else options.max_sv_size
    if svs2 is None or not svs2:  # 只有一个 hap
        for sv in svs1:
            cand = candidate_sv(sv, min_sv_length, max_sv_length, contig, ref_seq, noseqs, genotype="1/1")
            if cand:
                sv_candidates.append(cand)
    else:  # 两个 hap
        clusters = cluster_sv_lists(svs1, svs2, max_dist=0, max_len_diff_ratio=0.7)
        for sv1, sv2 in clusters:
            if sv1 and sv2:  # 聚类个数=1 → 认为是同一个事件
                cand = candidate_sv(sv1, min_sv_length, max_sv_length, contig, ref_seq, noseqs, genotype="1/1")
                if cand:
                    sv_candidates.append(cand)
            elif sv1:  # 只在 hap1
                cand = candidate_sv(sv1, min_sv_length, max_sv_length, contig, ref_seq, noseqs, genotype="0/1")
                if cand:
                    sv_candidates.append(cand)
            elif sv2:  # 只在 hap2
                cand = candidate_sv(sv2, min_sv_length, max_sv_length, contig, ref_seq, noseqs, genotype="0/1")
                if cand:
                    sv_candidates.append(cand)

    return sv_candidates


def match_and_assign_sv(svs1, svs2, contig, ref_seq, options, max_pos_diff=500,
                        max_len_diff_ratio=0.7):
    """
    根据两个单倍型的 SV 列表进行配对和单倍型分配

    Args:
        svs1, svs2: list of dict，每个 dict 至少包含 {'pos', 'svlen'}
        min_sv_length, max_sv_length: SV 长度过滤
        contig: 当前染色体名
        ref_seq: 参考序列
        noseqs: 是否输出序列 (传给 candidate_sv)
        max_pos_diff: 允许的最大坐标差
        max_len_diff_ratio: svlen 比例阈值

    Return:
        sv_candidates: list of candidate_sv
    """
    used2 = set()  # 记录 svs2 中已经配对过的
    sv_candidates = []
    min_sv_length, noseqs = options.min_sv_size, options.noseq
    max_sv_length = 100000 if options.max_sv_size == -1 else options.max_sv_size
    for i, sv1 in enumerate(svs1):
        matched = False
        for j, sv2 in enumerate(svs2):
            if j in used2:
                continue
            # 判断位置差
            if abs(sv1['pos'] - sv2['pos']) <= max_pos_diff:
                # 判断长度比例
                len1, len2 = abs(sv1['svlen']), abs(sv2['svlen'])
                ratio = min(len1, len2) / max(len1, len2) if max(len1, len2) > 0 else 0
                if ratio >= max_len_diff_ratio:
                    # 说明匹配到同一事件 → genotype=1/1
                    cand = candidate_sv(sv1, min_sv_length, max_sv_length, contig, ref_seq, noseqs, genotype="1/1")
                    if cand:
                        sv_candidates.append(cand)
                    used2.add(j)
                    matched = True
                    break
        if not matched:
            # sv1 没有匹配 → 独有 → genotype=0/1
            cand = candidate_sv(sv1, min_sv_length, max_sv_length, contig, ref_seq, noseqs, genotype="0/1")
            if cand:
                sv_candidates.append(cand)

    # 处理 svs2 中没被用到的 → 独有 → genotype=0/1
    for j, sv2 in enumerate(svs2):
        if j not in used2:
            cand = candidate_sv(sv2, min_sv_length, max_sv_length, contig, ref_seq, noseqs, genotype="0/1")
            if cand:
                sv_candidates.append(cand)

    return sv_candidates

def filter_redundant_sv(sv_candidates, close_pos, max_dist=1000):
    """
    根据 close_pos 过滤冗余 SV
    冗余定义：
        sv.start 距离 close_pos 左端 > max_dist
        或者 sv.start 距离 close_pos 右端 > max_dist
    """

    # --- 排序 ---
    sv_candidates = sorted(sv_candidates, key=lambda sv: sv.start)
    close_pos = sorted(close_pos, key=lambda x: x[0])  # (span_start, span_end)

    filtered = []
    i, j = 0, 0  # i 遍历 sv_candidates, j 遍历 close_pos
    n, m = len(sv_candidates), len(close_pos)

    while i < n and j < m:
        sv = sv_candidates[i]
        span_start, span_end = close_pos[j]

        if sv.start < span_start - max_dist:
            # SV 在当前区间左边太远 → 丢弃
            i += 1
        elif sv.start > span_end + max_dist:
            # SV 在当前区间右边太远 → 移动到下一个区间
            j += 1
        else:
            # SV 落在允许范围内 → 保留
            filtered.append(sv)
            i += 1

    return filtered

def merge_close_svs(svs, a_seq, max_dist=1000):
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
        seq = current["seq"]

        j = i + 1
        while j < len(svs):
            next_sv = svs[j]

            # 判断与当前 sv 是否相邻（链式逻辑）
            if next_sv["pos"] - (current["pos"] + current["svlen"]) < max_dist:
                # 更新合并块
                svlen = svlen + next_sv["svlen"]
                seq = seq + next_sv["seq"]

                # 更新 current，作为新的比较基准
                current = {
                    "pos": start_pos,
                    "svlen": svlen,
                    "seq": seq,
                    "svtype": "INS"
                }
                j += 1
            else:
                break

        merged.append(current)
        # 跳到不相邻的下一个 SV
        i = j

    return merged


from sklearn.cluster import KMeans
import numpy as np


# def cluster_by_svlen(merged_sigs, span_start, span_end, svtype, left_flank, right_flank, buffer=300):
#     siglens = np.array([sig.svlen for sig in merged_sigs]).reshape(-1, 1)
#     kmeans = KMeans(n_clusters=2, random_state=0).fit(siglens)
#
#     clusters = {0: [], 1: []}
#     for sig, label in zip(merged_sigs, kmeans.labels_):
#         frag = _extract_fragment_from_signature(
#             sig, span_start, span_end, svtype, left_flank, right_flank, buffer=buffer
#         )
#         if frag:
#             clusters[label].append(frag)
#
#     return clusters
def cluster_by_svlen(sigs, span_start, span_end, svtype, left_flank, right_flank, buffer=300):
    fragments = []
    lengths = []

    # 提取片段并统计长度
    for sig in sigs:
        frag = _extract_fragment_from_signature(sig, span_start, span_end, svtype, left_flank, right_flank, buffer=buffer)
        if frag is None:
            continue
        fragments.append(frag)
        lengths.append(sig.svlen)

    if not fragments:
        return []

    # 初始化簇
    clusters = {0: [fragments[0]]}
    centers = {0: lengths[0]}

    # 顺序扫描聚类
    for frag, length in zip(fragments[1:], lengths[1:]):
        assigned = False
        for cid, center in centers.items():
            if abs(length - center) <= 2 * min(abs(center), abs(length)):  # 两倍阈值
                clusters[cid].append(frag)
                assigned = True
                break
        if not assigned:
            new_cid = len(clusters)
            clusters[new_cid] = [frag]
            centers[new_cid] = length

    # 如果有两个类，且某一类数量 < 4，则合并
    if len(clusters) == 2:
        counts = {cid: len(vals) for cid, vals in clusters.items()}
        small = [cid for cid, c in counts.items() if c < 4]
        big_candidates = [cid for cid in clusters if cid not in small]
        if big_candidates:  # 只有存在非小类才合并
            big = big_candidates[0]
            for cid in small:
                clusters[big].extend(clusters[cid])
                del clusters[cid]

    return list(clusters.values())


import glob, pysam
from util import merge_cigar
def harmonize_cluster_and_recall(clusters, ref_seq, options, buffer=500,
                                 max_window_bp=10000, min_support=1,
                                 aligner=None):
    """
    主接口：对单个 signature cluster 进行处理并返回候选 SV 列表（含 GT）

    返回: list of dict:
        {'contig', 'start', 'end', 'svtype', 'svlen', 'ref', 'alt', 'gt', 'support', 'notes'}
    """
    haps = []
    ignore_bins = []
    haps_index = []
    fragments_ = []
    close_pos = []
    bam = pysam.AlignmentFile(options.bam, threads=options.num_threads)
    sv_candidates = []
    # hip_reads = open(os.path.join(options.working_dir, 'temp.fa'))
    for bin_index, close_bin in enumerate(clusters):
        if len(close_bin) <= 2 or 'suppl' in [sig.signature for sig_bin in close_bin for sig in sig_bin]:
            ignore_bins.extend([sig_bin for sig_bin in close_bin])
            continue

        sigs = [sig for group in close_bin for sig in group]
        # 1) 计算窗口
        contig = sigs[0].contig
        svtype = sigs[0].type
        span_start = min(s.start for s in sigs)

        span_end = max(s.start for s in sigs) if svtype == 'INS' else max(s.end for s in sigs)
        close_pos.append((span_start, span_end))
        # span_start = max(min(s.start for s in sigs) - buffer, 0)
        # span_end = min(max(s.start for s in sigs) if svtype == 'INS' else max(s.end for s in sigs) + buffer, len(ref_seq))
        left_ref_start = max(span_start - 1000, 0)
        right_ref_end = min(span_end + 1000, len(ref_seq))

        left_flank = ref_seq[left_ref_start: span_start]  # 左侧参考序列
        right_flank = ref_seq[span_end: right_ref_end]  # 右侧参考序列

        # for read in bam.fetch(contig, span_start, span_end):
        #     if read.reference_start <= span_start < read.reference_end:
        #         fragments_.append(read)
        # 2) 提取片段
        fragments = []
        # for sig in sigs:
        #     frag = _extract_fragment_from_signature(sig, span_start, span_end, svtype, buffer=buffer)
        #     fragments.append(frag)
        sigs_by_read = defaultdict(list)
        for sig in sigs:
            sigs_by_read[sig.read_name].append(sig)

        merged_sigs = []
        for read_id, sig_list in sigs_by_read.items():
            # 先排序（按起点坐标）
            sig_list.sort(key=lambda x: x.start)
            # 调用合并函数
            merged_sigs.extend(merge_cigar(sig_list, read_type='hifi'))
        hap_cluster = cluster_by_svlen(merged_sigs, span_start, span_end, svtype, left_flank, right_flank)
        # for sig in merged_sigs:
        #     frag = _extract_fragment_from_signature(sig, span_start, span_end, svtype, left_flank, right_flank, buffer=buffer)
        #     fragments.append(frag)
            # frag = sig.read_seq
            # read_name = f"{sig.read_name}_{sig.contig}_{sig.start}_{sig.svlen}_{sig.type}"
            # fragments_.append((read_name, sig.read_seq))


    # return fragments_, ignore_bins

        #4) 对每簇计算 consensus（使用 abPOA）
    #     if aligner is None:
    #         aligner = pyabpoa.msa_aligner()
    #     # hp1 = _msa_consensus_for_cluster(cluster1, aligner=aligner) if cluster1 else ''
    #     # hp2 = _msa_consensus_for_cluster(cluster2, aligner=aligner) if cluster2 else ''
    #     cons_result = _msa_consensus_for_cluster(fragments, aligner=aligner)#长度比较一致，就随机采样减少序列个数
        # cons_result = _msa_consensus_for_cluster(fragments, len(close_bin), aligner=aligner)#长度比较一致，就随机采样减少序列个数
        cons_result1 = _msa_consensus_for_cluster(hap_cluster[0], aligner=aligner)[0]
        cons_result2 = _msa_consensus_for_cluster(hap_cluster[1], aligner=aligner)[0] if len(hap_cluster)>1 else ''
        hp1 = left_flank + cons_result1 + right_flank
        hp2 = left_flank+cons_result2 + right_flank
        # hp1 = left_flank+cons_result[0]+right_flank
        # hp2 = left_flank+cons_result[1] + right_flank if len(cons_result) > 1 else ''
        haps.append((hp1, hp2))
        # haps.extend(cons_result)
        haps_index.append(bin_index)
    # work_dir = os.path.join(options.working_dir, "dipcall_workspace")
    # os.makedirs(work_dir, exist_ok=True)  # 等价于 mkdir -p
    # os.chdir(work_dir)
    # with open('recall.fa', 'w') as temp:
    #     for read in fragments_:
    #         temp.write(f">{read[0]}\n{read[1]}\n")
    # for f in glob.glob("temp.*"):
    #     os.remove(f)
    # os.system("/home/huheng/download/hifiasm/hifiasm -o temp -t64 recall.fa ")
    # os.system("awk '/^S/{print \">\"$2;print $3}' temp.bp.hap1.p_ctg.gfa > mat.fa")
    # os.system("awk '/^S/{print \">\"$2;print $3}' temp.bp.hap2.p_ctg.gfa > pat.fa")
    #
    # aln1, aln2 = align_with_mappy(ref_seq)
    #
    #
    # svs1, svs2 = [], []
    # for a1 in aln1:
    #     svs1.extend(_extract_sv_from_alignment(a1, contig))
    # for a2 in aln2:
    #     svs2.extend(_extract_sv_from_alignment(a2, contig))
    # sv_candidates = match_and_assign_sv(svs1, svs2, contig, ref_seq, options)
    # filter_sv = filter_redundant_sv(sv_candidates, close_pos)
    # return filter_sv, ignore_bins
    min_sv_length, noseqs = options.min_sv_size, options.noseq
    max_sv_length = 100000 if options.max_sv_size == -1 else options.max_sv_size
    aln1, aln2 = align_with_mappy(ref_seq, haps)
    for a1, a2, a_index in zip(aln1, aln2, haps_index):
        svs1, svs2 = None, None
        if a1:
            svs1 = _extract_sv_from_alignment(a1)
            # svs1 = merge_close_svs(svs1_ini, a1[0])
        if a2:
            svs2 = _extract_sv_from_alignment(a2)
            # svs2 = merge_close_svs(svs2_ini, a2[0])
        bin_pos = clusters[a_index][0][0].start
        hap_sv = []
        if not svs1 and not svs2:
            pass
        elif svs1 and not svs2:
            for sv in svs1:
                hap_sv.append(candidate_sv(sv, contig, ref_seq, noseqs, genotype="1/1"))
            # hap_sv = process_hap_sv(contig, ref_seq, svs1, options)
        elif svs2 and not svs1:
            for sv in svs2:
                hap_sv.append(candidate_sv(sv, contig, ref_seq, noseqs, genotype="1/1"))
            # hap_sv = process_hap_sv(contig, ref_seq, svs2, options)
        else:
            for sv in svs1:
                hap_sv.append(candidate_sv(sv, contig, ref_seq, noseqs, genotype="0/1"))
            for sv in svs2:
                hap_sv.append(candidate_sv(sv, contig, ref_seq, noseqs, genotype="0/1"))
            # hap_sv = process_hap_sv(contig, ref_seq, svs1, options, svs2)
        if hap_sv:
            for can in hap_sv:
                if abs(can.start - bin_pos) < 2000:
                    sv_candidates.append(can)
                else:
                    ignore_bins.extend([sig_bin for sig_bin in clusters[a_index]])
                    break
        else:
            ignore_bins.extend([sig_bin for sig_bin in clusters[a_index]])
    # filter_sv = filter_redundant_sv(sv_candidates, close_pos)
    return sv_candidates, ignore_bins

# def harmonize_cluster_and_recall(clusters, ref_seq, options, buffer=1000,
#                                  max_window_bp=10000, min_support=1,
#                                  aligner=None):
#     """
#     主接口：对单个 signature cluster 进行处理并返回候选 SV 列表（含 GT）
#
#     返回: list of dict:
#         {'contig', 'start', 'end', 'svtype', 'svlen', 'ref', 'alt', 'gt', 'support', 'notes'}
#     """
#     haps = []
#     ignore_bins = []
#     haps_index = []
#     fragments_ = []
#     close_pos = []
#     bam = pysam.AlignmentFile(options.bam, threads=options.num_threads)
#     sv_candidates = []
#     # hip_reads = open(os.path.join(options.working_dir, 'temp.fa'))
#     for bin_index, close_bin in enumerate(clusters):
#         if len(close_bin) <= 2 or 'suppl' in [sig.signature for sig_bin in close_bin for sig in sig_bin]:
#             ignore_bins.extend([sig_bin for sig_bin in close_bin])
#             continue
#
#         sigs = [sig for group in close_bin for sig in group]
#         # 1) 计算窗口
#         contig = sigs[0].contig
#         svtype = sigs[0].type
#         span_start = min(s.start for s in sigs)
#
#         span_end = max(s.start for s in sigs) if svtype == 'INS' else max(s.end for s in sigs)
#         close_pos.append((span_start, span_end))
#         # span_start = max(min(s.start for s in sigs) - buffer, 0)
#         # span_end = min(max(s.start for s in sigs) if svtype == 'INS' else max(s.end for s in sigs) + buffer, len(ref_seq))
#         left_ref_start = max(span_start - buffer, 0)
#         right_ref_end = min(span_end + buffer, len(ref_seq))
#
#         # left_flank = ref_seq[left_ref_start: span_start-500]  # 左侧参考序列
#         # right_flank = ref_seq[span_end+500: right_ref_end]  # 右侧参考序列
#         for read in bam.fetch(contig, span_start, span_end):
#             if read.is_unmapped:
#                 continue
#             # 判断是否真正覆盖 sig.start
#             if read.reference_start <= span_start < read.reference_end:
#                 read_name = f"{read.query_name}"
#                 fragments_.append(read.query_sequence)
#         # win_len = span_end - span_start
#         # if win_len > max_window_bp:
#         #     # 保护：直接返回空或原 cluster（此处返回空表示不处理）
#         #     return []
#
#         # 2) 提取片段
#         fragments = []
#         # for sig in sigs:
#         #     frag = _extract_fragment_from_signature(sig, span_start, span_end, svtype, buffer=buffer)
#         #     fragments.append(frag)
#         # for sig in sigs:
#             # frag = _extract_fragment_from_signature(sig, span_start, span_end, svtype, left_flank, right_flank, buffer=buffer)
#             # fragments.append(frag)
#             # frag = sig.read_seq
#             # read_name = f"{sig.read_name}_{sig.contig}_{sig.start}_{sig.svlen}_{sig.type}"
#             # fragments_.append((read_name, sig.read_seq))
#
#
#     # return fragments_, ignore_bins
#
#         #4) 对每簇计算 consensus（使用 abPOA）
#     #     if aligner is None:
#     #         aligner = pyabpoa.msa_aligner()
#     #     # hp1 = _msa_consensus_for_cluster(cluster1, aligner=aligner) if cluster1 else ''
#     #     # hp2 = _msa_consensus_for_cluster(cluster2, aligner=aligner) if cluster2 else ''
#         cons_result = _msa_consensus_for_cluster(fragments_, aligner=aligner)#长度比较一致，就随机采样减少序列个数
#         hp1 = cons_result[0]
#         hp2 = cons_result[1] if len(cons_result) > 1 else ''
#         haps.append((hp1, hp2))
#         haps_index.append(bin_index)
#     # work_dir = os.path.join(options.working_dir, "dipcall_workspace")
#     # os.makedirs(work_dir, exist_ok=True)  # 等价于 mkdir -p
#     # os.chdir(work_dir)
#     # with open('recall.fa', 'w') as temp:
#     #     for read in fragments_:
#     #         temp.write(f">{read[0]}\n{read[1]}\n")
#     # for f in glob.glob("temp.*"):
#     #     os.remove(f)
#     # os.system("/home/huheng/download/hifiasm/hifiasm -o temp -t64 recall.fa ")
#     # os.system("awk '/^S/{print \">\"$2;print $3}' temp.bp.hap1.p_ctg.gfa > mat.fa")
#     # os.system("awk '/^S/{print \">\"$2;print $3}' temp.bp.hap2.p_ctg.gfa > pat.fa")
#     #
#     # aln1, aln2 = align_with_mappy(ref_seq)
#     #
#     #
#     # svs1, svs2 = [], []
#     # for a1 in aln1:
#     #     svs1.extend(_extract_sv_from_alignment(a1, contig))
#     # for a2 in aln2:
#     #     svs2.extend(_extract_sv_from_alignment(a2, contig))
#     # sv_candidates = match_and_assign_sv(svs1, svs2, contig, ref_seq, options)
#     # filter_sv = filter_redundant_sv(sv_candidates, close_pos)
#     # return filter_sv, ignore_bins
#     aln1, aln2 = align_with_mappy(ref_seq, haps)
#     for a1, a2, a_index in zip(aln1, aln2, haps_index):
#         svs1 = _extract_sv_from_alignment(a1, contig)
#         svs2 = _extract_sv_from_alignment(a2, contig)
#         bin_pos = clusters[a_index][0][0].start
#         if not svs1 and not svs2:
#             hap_sv = None
#         elif svs1 and not svs2:
#             hap_sv = process_hap_sv(contig, ref_seq, svs1, options)
#         elif svs2 and not svs1:
#             hap_sv = process_hap_sv(contig, ref_seq, svs2, options)
#         else:
#             hap_sv = process_hap_sv(contig, ref_seq, svs1, options, svs2)
#         if hap_sv:
#             for can in hap_sv:
#                 if abs(can.start - bin_pos) < 2000:
#                     sv_candidates.append(can)
#                 else:
#                     ignore_bins.extend([sig_bin for sig_bin in clusters[a_index]])
#                     break
#         else:
#             ignore_bins.extend([sig_bin for sig_bin in clusters[a_index]])
#     filter_sv = filter_redundant_sv(sv_candidates, close_pos)
#     return filter_sv, ignore_bins
#
# def harmonize_cluster_and_recall(clusters, ref_seq, options, buffer=500,
#                                  max_window_bp=10000, min_support=1,
#                                  aligner=None):
#     """
#     主接口：对单个 signature cluster 进行处理并返回候选 SV 列表（含 GT）
#
#     返回: list of dict:
#         {'contig', 'start', 'end', 'svtype', 'svlen', 'ref', 'alt', 'gt', 'support', 'notes'}
#     """
#     haps = []
#     ignore_bins = []
#     haps_index = []
#     sigs_group_list = []
#     # hip_reads = open(os.path.join(options.working_dir, 'temp.fa'))
#     for bin_index, close_bin in enumerate(clusters):
#         if close_bin[0][0].type == 'DEL' or len(close_bin) <= 2 or 'suppl' in [sig.signature for sig_bin in close_bin for sig in sig_bin]:
#             ignore_bins.extend([sig_bin for sig_bin in close_bin])
#             continue
#         else:
#             sigs_group_list.extend([sig_bin for sig_bin in close_bin])
#
#     for group_index, sigs_group in enumerate(sigs_group_list):
#
#         # 1) 计算窗口
#         contig = sigs_group[0].contig
#         svtype = sigs_group[0].type
#         span_start = max(min(s.start for s in sigs_group) - buffer, 0)
#         span_end = min(max(s.start for s in sigs_group) if svtype == 'INS' else max(s.end for s in sigs_group) + buffer, len(ref_seq))
#         if abs(span_start-2212174)<2000:
#             pass
#         # 2) 提取片段
#         fragments = []
#         for sig in sigs_group:
#             frag = _extract_fragment_from_signature(sig, span_start, span_end, svtype, buffer=buffer)
#             fragments.append(frag)
#
#         # 4) 对每簇计算 consensus（使用 abPOA）
#         if aligner is None:
#             aligner = pyabpoa.msa_aligner()
#         # hp1 = _msa_consensus_for_cluster(cluster1, aligner=aligner) if cluster1 else ''
#         # hp2 = _msa_consensus_for_cluster(cluster2, aligner=aligner) if cluster2 else ''
#         cons_result = _msa_consensus_for_cluster(fragments, aligner=aligner)#长度比较一致，就随机采样减少序列个数
#         hp1 = cons_result[0]
#         hp2 = cons_result[1] if len(cons_result) > 1 else ''
#         haps.append((hp1, hp2))
#         haps_index.append(group_index)
#
#     aln1, aln2 = align_with_mappy(ref_seq, haps)
#     sv_candidates = []
#     #
#     for a1, a2, a_index in zip(aln1, aln2, haps_index):
#         svs1 = _extract_sv_from_alignment(a1, contig)
#         svs2 = _extract_sv_from_alignment(a2, contig)
#         bin_pos = sigs_group_list[a_index][0].start
#         if not svs1 and not svs2:
#             hap_sv = None
#         elif svs1 and not svs2:
#             hap_sv = process_hap_sv(contig, ref_seq, svs1, options)
#         elif svs2 and not svs1:
#             hap_sv = process_hap_sv(contig, ref_seq, svs2, options)
#         else:
#             hap_sv = process_hap_sv(contig, ref_seq, svs1, options, svs2)
#         if hap_sv:
#             for can in hap_sv:
#                 if abs(can.start - bin_pos) < 2000:
#                     sv_candidates.append(can)
#                 else:
#                     ignore_bins.append(sigs_group_list[a_index])
#                     break
#         else:
#             ignore_bins.append(sigs_group_list[a_index])
#
#
#     return sv_candidates, ignore_bins
