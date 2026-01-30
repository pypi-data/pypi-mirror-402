from dataclasses import dataclass
from typing import Dict, Iterator, List, Optional, Sequence, Tuple, Union

import io
import math
import os
import struct

import numpy as np
import torch
from torch.utils.data import DataLoader, Dataset as TorchDataset
from tqdm import tqdm
import pgenlib as pg


def read_text_header(path: str, sep: str = "\t") -> List[str]:
    with open(path, "r", encoding="utf-8") as file:
        for line in file:
            if not line:
                continue
            if line.startswith("##"):
                continue
            if line.startswith("#"):
                line = line.lstrip("#")
            return line.rstrip("\n").split(sep)
    raise ValueError(f"Empty file: {path}")


def iter_pvar_id_blocks(pvar_path: str, block_size: int) -> Iterator[List[str]]:
    header = read_text_header(pvar_path, sep="\t")
    try:
        id_col = header.index("ID")
    except ValueError as exc:
        raise ValueError("PVAR header must contain an ID column.") from exc

    buf: List[str] = []
    with open(pvar_path, "r", encoding="utf-8") as file:
        for line in file:
            if not line:
                continue
            if line.startswith("##"):
                continue
            if line.startswith("#"):
                continue
            parts = line.rstrip("\n").split("\t")
            if len(parts) <= id_col:
                continue
            buf.append(parts[id_col])
            if len(buf) >= block_size:
                yield buf
                buf = []
    if buf:
        yield buf


def read_all_pvar_ids(pvar_path: str, block_size: int = 200_000) -> np.ndarray:
    ids: List[str] = []
    for block in iter_pvar_id_blocks(pvar_path, block_size):
        ids.extend(block)
    return np.asarray(ids, dtype=str)


def pvar_ids_for_indices(pvar_path: str, variant_idx: np.ndarray, block_size: int = 200_000) -> np.ndarray:
    idx = np.asarray(variant_idx, dtype=np.int64)
    if idx.ndim != 1:
        raise ValueError("variant_idx must be 1D.")
    if idx.size == 0:
        return np.asarray([], dtype=str)

    order = np.argsort(idx, kind="mergesort")
    idx_sorted = idx[order]
    out_sorted: List[Optional[str]] = [None] * int(idx_sorted.size)

    pos = 0
    done = 0
    for block in iter_pvar_id_blocks(pvar_path, block_size):
        start = pos
        end = pos + len(block)

        left = int(np.searchsorted(idx_sorted, start, side="left"))
        right = int(np.searchsorted(idx_sorted, end, side="left"))
        if right > left:
            rel = idx_sorted[left:right] - start
            for j, rel_pos in enumerate(rel.tolist()):
                out_sorted[left + j] = block[int(rel_pos)]
            done = right

        pos = end
        if done >= idx_sorted.size:
            break

    missing = [i for i, value in enumerate(out_sorted) if value is None]
    if missing:
        raise ValueError(f"Failed to resolve {len(missing)} variant IDs from PVAR.")

    out = np.empty((idx.size,), dtype=object)
    for j, orig_pos in enumerate(order.tolist()):
        out[int(orig_pos)] = str(out_sorted[j])
    return out.astype(str)


def variant_idx_from_ids(pvar_path: str, variant_ids: Sequence[str], block_size: int = 200_000) -> np.ndarray:
    ids = [str(value) for value in variant_ids]
    pos_map: Dict[str, List[int]] = {}
    for i, vid in enumerate(ids):
        pos_map.setdefault(vid, []).append(i)

    out = np.full((len(ids),), -1, dtype=np.int64)
    found = 0
    pos = 0
    for block in iter_pvar_id_blocks(pvar_path, block_size):
        for j, vid in enumerate(block):
            hits = pos_map.get(vid)
            if hits is None:
                continue
            idx_val = pos + j
            for i in hits:
                if out[i] < 0:
                    out[i] = idx_val
                    found += 1
        pos += len(block)
        if found >= len(ids):
            break

    missing = np.flatnonzero(out < 0)
    if missing.size:
        examples = [ids[int(i)] for i in missing[:5]]
        raise ValueError(f"{missing.size} variant IDs were not found in PVAR. Examples: {examples}")
    return out


def read_psam_iids(psam_path: str) -> np.ndarray:
    header = read_text_header(psam_path, sep="\t")
    try:
        iid_col = header.index("IID")
    except ValueError as exc:
        raise ValueError("PSAM must contain an IID column.") from exc

    iids: List[str] = []
    with open(psam_path, "r", encoding="utf-8") as file:
        first = True
        for line in file:
            if first:
                first = False
                continue
            if not line:
                continue
            parts = line.rstrip("\n").split("\t")
            if len(parts) <= iid_col:
                continue
            iids.append(parts[iid_col])
    return np.asarray(iids, dtype=str)


def read_tfam_iid_y(tfam_path: str) -> Tuple[np.ndarray, np.ndarray]:
    iids: List[str] = []
    ys: List[int] = []
    y_col = 5
    with open(tfam_path, "r", encoding="utf-8") as file:
        for line in file:
            if not line:
                continue
            parts = line.split()
            if len(parts) <= max(1, y_col):
                continue
            iids.append(str(parts[1]))
            ys.append(int(float(parts[y_col])))
    return np.asarray(iids, dtype=str), np.asarray(ys, dtype=np.int64)


@dataclass(frozen=True)
class SplitPlan:
    train: np.ndarray
    val: np.ndarray
    test: np.ndarray

    def labels(self, n_samples: int) -> np.ndarray:
        lab = np.full((n_samples,), -1, dtype=np.int8)
        lab[self.train] = 0
        lab[self.val] = 1
        lab[self.test] = 2
        return lab


@dataclass
class Phenotype:
    iid_to_y: Dict[str, int]

    @classmethod
    def from_tfam(cls, tfam_path: str) -> "Phenotype":
        iids, ys = read_tfam_iid_y(tfam_path)
        mapping: Dict[str, int] = {}
        for iid, y in zip(iids.tolist(), ys.tolist()):
            mapping[str(iid)] = int(y)
        return cls(mapping)

    def align(self, sample_ids: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        sids = sample_ids.astype(str, copy=False)
        y = np.empty((sids.size,), dtype=np.int64)
        keep = np.ones((sids.size,), dtype=bool)

        for i, sid in enumerate(sids.tolist()):
            value = self.iid_to_y.get(sid)
            if value is None:
                keep[i] = False
                y[i] = 0
                continue
            y[i] = int(value)

        y_kept = y[keep]
        if y_kept.size == 0:
            raise ValueError("All samples were filtered out by phenotype alignment/missing rules.")
        if np.unique(y_kept).size < 2:
            raise ValueError("Need at least two phenotype classes after filtering.")
        return y_kept, keep


def stratified_split_indices(y: np.ndarray, train: float, val: float, test: float, seed: int) -> SplitPlan:
    if not np.isclose(train + val + test, 1.0):
        raise ValueError("train + val + test must sum to 1.0")

    rng = np.random.default_rng(seed)
    y_arr = np.asarray(y, dtype=np.int64)
    classes = np.unique(y_arr)

    train_parts: List[np.ndarray] = []
    val_parts: List[np.ndarray] = []
    test_parts: List[np.ndarray] = []

    for c in classes.tolist():
        idx = np.flatnonzero(y_arr == int(c)).astype(np.int64, copy=False)
        rng.shuffle(idx)
        n = int(idx.size)
        n_train = int(math.floor(train * n))
        n_val = int(math.floor(val * n))
        train_parts.append(idx[:n_train])
        val_parts.append(idx[n_train : n_train + n_val])
        test_parts.append(idx[n_train + n_val :])

    train_idx = np.concatenate(train_parts).astype(np.int64, copy=False)
    val_idx = np.concatenate(val_parts).astype(np.int64, copy=False)
    test_idx = np.concatenate(test_parts).astype(np.int64, copy=False)

    rng.shuffle(train_idx)
    rng.shuffle(val_idx)
    rng.shuffle(test_idx)

    return SplitPlan(train=train_idx, val=val_idx, test=test_idx)


@dataclass
class VariantSelection:
    idx: np.ndarray

    def indices(self) -> np.ndarray:
        return np.asarray(self.idx, dtype=np.int64)


MAGIC = b"GBLK2\0\0\0"
HEADER_SIZE = 4096

# 14 items:
# magic(8s), version(u32), dtype_code(u32),
# n_samples(u64), n_variants(u64),
# block_samples(u32), block_variants(u32),
# n_sample_blocks(u32), n_variant_blocks(u32),
# dir_offset(u64), data_offset(u64), meta_offset(u64), meta_size(u64),
# reserved(u64)
HEADER_FMT = "<8s I I Q Q I I I I Q Q Q Q Q"
DIR_REC_FMT = "<Q Q Q Q"
DIR_REC_SIZE = struct.calcsize(DIR_REC_FMT)


def align_up(x: int, a: int) -> int:
    if a <= 0:
        raise ValueError("Alignment must be positive.")
    r = x % a
    return x if r == 0 else (x + (a - r))


def pack_header(
    n_samples: int,
    n_variants: int,
    block_samples: int,
    block_variants: int,
    n_sample_blocks: int,
    n_variant_blocks: int,
    dir_offset: int,
    data_offset: int,
    meta_offset: int,
    meta_size: int,
    dtype_code: int,
) -> bytes:
    reserved = 0
    payload = struct.pack(
        HEADER_FMT,
        MAGIC,
        2,
        int(dtype_code),
        int(n_samples),
        int(n_variants),
        int(block_samples),
        int(block_variants),
        int(n_sample_blocks),
        int(n_variant_blocks),
        int(dir_offset),
        int(data_offset),
        int(meta_offset),
        int(meta_size),
        int(reserved),
    )
    if len(payload) > HEADER_SIZE:
        raise ValueError("Header payload exceeds HEADER_SIZE.")
    return payload + (b"\x00" * (HEADER_SIZE - len(payload)))


def unpack_header(buf: bytes) -> Dict[str, int]:
    need = struct.calcsize(HEADER_FMT)
    if len(buf) < need:
        raise ValueError("Invalid header length.")
    parts = struct.unpack(HEADER_FMT, buf[:need])
    if parts[0] != MAGIC:
        raise ValueError("Bad magic, not a GBLK2 file.")
    return {
        "version": int(parts[1]),
        "dtype_code": int(parts[2]),
        "n_samples": int(parts[3]),
        "n_variants": int(parts[4]),
        "block_samples": int(parts[5]),
        "block_variants": int(parts[6]),
        "n_sample_blocks": int(parts[7]),
        "n_variant_blocks": int(parts[8]),
        "dir_offset": int(parts[9]),
        "data_offset": int(parts[10]),
        "meta_offset": int(parts[11]),
        "meta_size": int(parts[12]),
    }


def dtype_from_code(dtype_code: int) -> np.dtype:
    if int(dtype_code) == 1:
        return np.dtype(np.int8)
    raise ValueError(f"Unsupported dtype_code: {dtype_code}")


def code_from_dtype(dtype: np.dtype) -> int:
    dt = np.dtype(dtype)
    if dt == np.dtype(np.int8):
        return 1
    raise ValueError(f"Unsupported dtype: {dt}")


def iter_sample_blocks(n: int, block_samples: int) -> List[Tuple[int, int]]:
    if block_samples <= 0:
        raise ValueError("block_samples must be > 0.")
    out: List[Tuple[int, int]] = []
    s0 = 0
    while s0 < n:
        s1 = min(n, s0 + int(block_samples))
        out.append((s0, s1))
        s0 = s1
    return out


@dataclass
class SampleBlockRec:
    s0: int
    s1: int
    base_offset: int
    stride_bytes: int


class Dataset:
    def __init__(self, pgen_path: str, pvar_path: str, psam_path: str, phenotype: Phenotype):
        self.pgen_path = str(pgen_path)
        self.pvar_path = str(pvar_path)
        self.psam_path = str(psam_path)

        sample_ids_full = read_psam_iids(self.psam_path)
        y_used, keep_mask = phenotype.align(sample_ids_full)

        raw_keep_idx = np.flatnonzero(keep_mask).astype(np.int64, copy=False)
        sample_ids_used = sample_ids_full[raw_keep_idx]

        self.sample_ids_full = sample_ids_full
        self.raw_keep_idx = raw_keep_idx
        self.sample_ids_used = sample_ids_used
        self.y_used = y_used.astype(np.int64, copy=False)

        self.splits: Optional[SplitPlan] = None

    @classmethod
    def from_pgen(cls, prefix: str, phenotype: Phenotype) -> "Dataset":
        base = str(prefix)
        return cls(base + ".pgen", base + ".pvar", base + ".psam", phenotype=phenotype)

    def split(
        self,
        seed: int = 42,
        train: float = 0.7,
        val: float = 0.15,
        test: float = 0.15,
        stratify: bool = True,
    ) -> SplitPlan:
        if stratify:
            plan = stratified_split_indices(self.y_used, train=train, val=val, test=test, seed=seed)
        else:
            rng = np.random.default_rng(seed)
            idx = np.arange(self.y_used.size, dtype=np.int64)
            rng.shuffle(idx)
            n = int(idx.size)
            n_train = int(math.floor(train * n))
            n_val = int(math.floor(val * n))
            plan = SplitPlan(train=idx[:n_train], val=idx[n_train : n_train + n_val], test=idx[n_train + n_val :])
        self.splits = plan
        return plan

    def resolve_variants(
        self,
        variants: Optional[Union[VariantSelection, Sequence[int], Sequence[str], np.ndarray]],
        store_variant_ids: bool,
    ) -> Tuple[np.ndarray, Optional[np.ndarray]]:
        with pg.PgenReader(self.pgen_path.encode("utf-8")) as reader:
            total = int(reader.get_variant_ct())

        if variants is None:
            idx = np.arange(total, dtype=np.int64)
            if store_variant_ids:
                ids = read_all_pvar_ids(self.pvar_path)
                if ids.size != idx.size:
                    raise ValueError("PVAR variant count does not match PGEN variant count.")
                return idx, ids
            return idx, None

        if isinstance(variants, VariantSelection):
            idx = variants.indices()
            ids = pvar_ids_for_indices(self.pvar_path, idx) if store_variant_ids else None
            return idx, ids

        arr = np.asarray(variants)
        if arr.size == 0:
            raise ValueError("variants resolved to an empty set.")

        if np.issubdtype(arr.dtype, np.integer):
            idx = arr.astype(np.int64, copy=False)
            if np.unique(idx).size != idx.size:
                raise ValueError("variants contains duplicate indices.")
            ids = pvar_ids_for_indices(self.pvar_path, idx) if store_variant_ids else None
            return idx, ids

        ids_in = [str(value) for value in arr.tolist()]
        idx = variant_idx_from_ids(self.pvar_path, ids_in)
        if np.unique(idx).size != idx.size:
            raise ValueError("variants contains duplicate IDs.")
        ids = np.asarray(ids_in, dtype=str) if store_variant_ids else None
        return idx, ids

    def materialize(
        self,
        out_prefix: str,
        variants: Optional[Union[VariantSelection, Sequence[int], Sequence[str], np.ndarray]] = None,
        overwrite: bool = False,
        block_variants: int = 1024,
        block_samples: int = 4096,
        read_variants: int = 8192,
        stream_all_threshold: float = 0.6,
        store_variant_ids: bool = False,
        validate_values: bool = False,
        seed_if_no_split: int = 42,
    ) -> str:
        base = str(out_prefix)
        out_path = base + ".gblk2"

        if not overwrite and os.path.exists(out_path):
            raise FileExistsError(f"Output exists: {out_path}. Use overwrite=True.")

        if int(block_variants) <= 0 or int(block_samples) <= 0 or int(read_variants) <= 0:
            raise ValueError("block_variants, block_samples, read_variants must be positive.")
        if int(read_variants) < int(block_variants):
            read_variants = int(block_variants)

        raw_sample_cols = np.asarray(self.raw_keep_idx, dtype=np.int64)
        if raw_sample_cols.size == 0:
            raise ValueError("No samples available after phenotype filtering.")
        if not np.all(raw_sample_cols[1:] > raw_sample_cols[:-1]):
            raw_sample_cols = np.unique(raw_sample_cols)

        sample_subset = raw_sample_cols.astype(np.uint32, copy=False)
        n_samples = int(sample_subset.size)

        if self.splits is None:
            self.split(seed=seed_if_no_split)

        split_labels = self.splits.labels(n_samples=int(self.y_used.size))
        y = self.y_used.astype(np.int64, copy=False)

        variant_idx_user, variant_ids_user = self.resolve_variants(variants, store_variant_ids=store_variant_ids)
        variant_idx_user = np.asarray(variant_idx_user, dtype=np.int64)
        if variant_idx_user.size == 0:
            raise ValueError("No variants selected.")

        order = np.argsort(variant_idx_user, kind="mergesort")
        inv_order = np.empty_like(order)
        inv_order[order] = np.arange(order.size, dtype=np.int64)

        variant_idx_sorted = variant_idx_user[order]
        n_variants = int(variant_idx_sorted.size)

        n_variant_blocks = int((n_variants + int(block_variants) - 1) // int(block_variants))
        n_sample_blocks = int((n_samples + int(block_samples) - 1) // int(block_samples))
        sample_blocks = iter_sample_blocks(n_samples, int(block_samples))

        dtype = np.dtype(np.int8)
        dtype_code = code_from_dtype(dtype)
        elem_sz = int(dtype.itemsize)

        dir_offset = HEADER_SIZE
        dir_bytes = int(n_sample_blocks) * int(DIR_REC_SIZE)
        data_offset = align_up(int(dir_offset) + int(dir_bytes), 4096)

        block_recs: List[SampleBlockRec] = []
        cur = int(data_offset)
        for (s0, s1) in sample_blocks:
            s_ct = int(s1 - s0)
            stride = int(s_ct) * int(block_variants) * int(elem_sz)
            region = int(n_variant_blocks) * int(stride)
            block_recs.append(SampleBlockRec(s0=int(s0), s1=int(s1), base_offset=int(cur), stride_bytes=int(stride)))
            cur += region

        data_end = int(cur)

        if os.path.exists(out_path):
            os.remove(out_path)

        fd = os.open(out_path, os.O_CREAT | os.O_TRUNC | os.O_RDWR, 0o644)
        try:
            header = pack_header(
                n_samples=n_samples,
                n_variants=n_variants,
                block_samples=int(block_samples),
                block_variants=int(block_variants),
                n_sample_blocks=n_sample_blocks,
                n_variant_blocks=n_variant_blocks,
                dir_offset=int(dir_offset),
                data_offset=int(data_offset),
                meta_offset=0,
                meta_size=0,
                dtype_code=int(dtype_code),
            )
            os.pwrite(fd, header, 0)

            dir_buf = bytearray(dir_bytes)
            for i, rec in enumerate(block_recs):
                off = int(i) * int(DIR_REC_SIZE)
                dir_buf[off : off + DIR_REC_SIZE] = struct.pack(
                    DIR_REC_FMT,
                    int(rec.s0),
                    int(rec.s1),
                    int(rec.base_offset),
                    int(rec.stride_bytes),
                )
            os.pwrite(fd, dir_buf, int(dir_offset))

            os.lseek(fd, int(data_end - 1), os.SEEK_SET)
            os.write(fd, b"\x00")

            with pg.PgenReader(self.pgen_path.encode("utf-8"), sample_subset=sample_subset) as reader:
                total_variants = int(reader.get_variant_ct())
                raw_n = int(reader.get_raw_sample_ct())
                if raw_n <= int(raw_sample_cols.max()):
                    raise ValueError("Sample indices exceed PGEN sample axis.")
                if int(variant_idx_sorted.max()) >= total_variants:
                    raise ValueError("Variant indices exceed PGEN variant axis.")

                span_start = int(variant_idx_sorted[0])
                span_end = int(variant_idx_sorted[-1]) + 1
                span_len = int(span_end - span_start)
                frac = float(n_variants) / float(span_len) if span_len > 0 else 1.0
                stream_all = bool(frac >= float(stream_all_threshold))

                read_v = int(read_variants)
                buf_gt = np.empty((read_v, n_samples), dtype=np.int8, order="C")
                x_buf = np.empty((n_samples, read_v), dtype=np.int8, order="C")

                out_buf = np.empty((n_samples, int(block_variants)), dtype=np.int8, order="C")
                out_fill = 0
                out_block_idx = 0

                sel_idx = variant_idx_sorted
                sel_pos = 0

                def flush_out_block(fill_cols: int, block_index: int) -> None:
                    if fill_cols < int(block_variants):
                        out_buf[:, fill_cols:int(block_variants)] = 0
                    for rec in block_recs:
                        s0 = int(rec.s0)
                        s1 = int(rec.s1)
                        offset = int(rec.base_offset) + int(block_index) * int(rec.stride_bytes)
                        chunk = out_buf[s0:s1, :]
                        mv = memoryview(chunk).cast("B")
                        os.pwrite(fd, mv, int(offset))

                def push_cols(src: np.ndarray, a: int, b: int) -> None:
                    nonlocal out_fill, out_block_idx
                    left = int(a)
                    right = int(b)
                    while left < right:
                        space = int(block_variants) - int(out_fill)
                        take = min(space, right - left)
                        out_buf[:, out_fill : out_fill + take] = src[:, left : left + take]
                        out_fill += take
                        left += take
                        if int(out_fill) == int(block_variants):
                            flush_out_block(int(out_fill), int(out_block_idx))
                            out_block_idx += 1
                            out_fill = 0

                def consume_selected_in_range(v0: int, v1: int, x: np.ndarray) -> int:
                    nonlocal sel_pos
                    start_pos = int(sel_pos)
                    while sel_pos < n_variants and int(sel_idx[sel_pos]) < int(v1):
                        run_start = int(sel_idx[sel_pos])
                        run_end = run_start + 1
                        sel_pos += 1
                        while sel_pos < n_variants:
                            nxt = int(sel_idx[sel_pos])
                            if nxt != run_end or nxt >= int(v1):
                                break
                            run_end += 1
                            sel_pos += 1
                        rel0 = int(run_start - v0)
                        rel1 = int(run_end - v0)
                        push_cols(x, rel0, rel1)
                    return int(sel_pos - start_pos)

                if stream_all:
                    v0 = int(span_start)
                    v_end = int(span_end)
                    pbar = tqdm(total=int(n_variants), desc="Materializing (stream)", unit="vars")
                    while v0 < v_end:
                        v1 = min(v_end, v0 + read_v)
                        V = int(v1 - v0)
                        reader.read_range(int(v0), int(v1), buf_gt[:V, :])

                        if validate_values:
                            gt_view = buf_gt[:V, :]
                            if np.any((gt_view < 0) | (gt_view > 2)):
                                bad_ct = int(np.count_nonzero((gt_view < 0) | (gt_view > 2)))
                                raise ValueError(f"Encountered {bad_ct} invalid genotype values in read_range.")

                        x_buf[:, :V] = buf_gt[:V, :].T
                        advanced = consume_selected_in_range(int(v0), int(v1), x_buf[:, :V])
                        if advanced:
                            pbar.update(int(advanced))
                        v0 = v1
                    pbar.close()
                else:
                    pbar = tqdm(total=int(n_variants), desc="Materializing (spans)", unit="vars")
                    while sel_pos < n_variants:
                        start = int(sel_idx[sel_pos])
                        end = start + 1
                        j = sel_pos + 1
                        while j < n_variants:
                            nxt = int(sel_idx[j])
                            if nxt != end:
                                break
                            end += 1
                            j += 1

                        v0 = int(start)
                        while v0 < int(end):
                            v1 = min(int(end), v0 + read_v)
                            V = int(v1 - v0)
                            reader.read_range(int(v0), int(v1), buf_gt[:V, :])

                            if validate_values:
                                gt_view = buf_gt[:V, :]
                                if np.any((gt_view < 0) | (gt_view > 2)):
                                    bad_ct = int(np.count_nonzero((gt_view < 0) | (gt_view > 2)))
                                    raise ValueError(f"Encountered {bad_ct} invalid genotype values in read_range.")

                            x_buf[:, :V] = buf_gt[:V, :].T
                            advanced = consume_selected_in_range(int(v0), int(v1), x_buf[:, :V])
                            if advanced:
                                pbar.update(int(advanced))
                            v0 = v1

                        if sel_pos != j:
                            raise RuntimeError("Internal error: span consumption mismatch.")
                    pbar.close()

                if int(out_fill) > 0:
                    flush_out_block(int(out_fill), int(out_block_idx))
                    out_block_idx += 1
                    out_fill = 0

                if int(out_block_idx) != int(n_variant_blocks):
                    raise RuntimeError(
                        f"Internal error: wrote {out_block_idx} variant blocks, expected {n_variant_blocks}."
                    )

            meta_buf = io.BytesIO()
            sample_ids_b = self.sample_ids_used.astype("S")
            variant_ids_b = None
            if store_variant_ids and variant_ids_user is not None:
                variant_ids_b = variant_ids_user.astype("S")

            np.savez(
                meta_buf,
                schema=np.asarray([5], dtype=np.int32),
                n_samples=np.asarray([n_samples], dtype=np.int64),
                n_variants=np.asarray([n_variants], dtype=np.int64),
                block_samples=np.asarray([int(block_samples)], dtype=np.int32),
                block_variants=np.asarray([int(block_variants)], dtype=np.int32),
                n_sample_blocks=np.asarray([n_sample_blocks], dtype=np.int32),
                n_variant_blocks=np.asarray([n_variant_blocks], dtype=np.int32),
                dtype_code=np.asarray([dtype_code], dtype=np.int32),
                sample_ids=sample_ids_b,
                raw_sample_idx=raw_sample_cols.astype(np.int64),
                y=y.astype(np.int64),
                split_labels=split_labels.astype(np.int8),
                variant_pgen_idx=variant_idx_user.astype(np.int64),
                variant_storage_to_user=order.astype(np.int64),
                variant_user_to_storage=inv_order.astype(np.int64),
                variant_ids=(variant_ids_b if variant_ids_b is not None else np.asarray([], dtype="S1")),
            )
            meta_bytes = meta_buf.getvalue()
            meta_offset = int(data_end)
            os.pwrite(fd, meta_bytes, int(meta_offset))
            meta_size = int(len(meta_bytes))

            header2 = pack_header(
                n_samples=n_samples,
                n_variants=n_variants,
                block_samples=int(block_samples),
                block_variants=int(block_variants),
                n_sample_blocks=n_sample_blocks,
                n_variant_blocks=n_variant_blocks,
                dir_offset=int(dir_offset),
                data_offset=int(data_offset),
                meta_offset=int(meta_offset),
                meta_size=int(meta_size),
                dtype_code=int(dtype_code),
            )
            os.pwrite(fd, header2, 0)

        finally:
            os.close(fd)

        return out_path

    @staticmethod
    def load_materialized(path: str) -> "GenoBlocks":
        return GenoBlocks.load(path)


@dataclass
class GenoBlocks:
    path: str
    header: Dict[str, int]
    blocks: List[SampleBlockRec]
    dtype: np.dtype
    n_samples: int
    n_variants: int
    block_samples: int
    block_variants: int
    n_sample_blocks: int
    n_variant_blocks: int

    sample_ids: np.ndarray
    raw_sample_idx: np.ndarray
    y: np.ndarray
    split_labels: np.ndarray

    variant_pgen_idx: np.ndarray
    variant_user_to_storage: np.ndarray
    variant_storage_to_user: np.ndarray
    variant_ids: Optional[np.ndarray]

    file_mem: np.memmap

    @staticmethod
    def load(path: str) -> "GenoBlocks":
        p = str(path)
        with open(p, "rb") as f:
            hdr_bytes = f.read(HEADER_SIZE)
        header = unpack_header(hdr_bytes)
        dtype = dtype_from_code(int(header["dtype_code"]))

        dir_offset = int(header["dir_offset"])
        n_sample_blocks = int(header["n_sample_blocks"])
        with open(p, "rb") as f:
            f.seek(dir_offset)
            dir_raw = f.read(int(n_sample_blocks) * int(DIR_REC_SIZE))

        blocks: List[SampleBlockRec] = []
        for i in range(n_sample_blocks):
            off = int(i) * int(DIR_REC_SIZE)
            s0, s1, base_offset, stride_bytes = struct.unpack(DIR_REC_FMT, dir_raw[off : off + DIR_REC_SIZE])
            blocks.append(SampleBlockRec(int(s0), int(s1), int(base_offset), int(stride_bytes)))

        meta_offset = int(header["meta_offset"])
        meta_size = int(header["meta_size"])
        if meta_offset <= 0 or meta_size <= 0:
            raise ValueError("Missing metadata region in file.")
        with open(p, "rb") as f:
            f.seek(meta_offset)
            meta_blob = f.read(meta_size)

        meta = np.load(io.BytesIO(meta_blob), allow_pickle=False)

        sample_ids = meta["sample_ids"]
        raw_sample_idx = meta["raw_sample_idx"].astype(np.int64)
        y = meta["y"].astype(np.int64)
        split_labels = meta["split_labels"].astype(np.int8)

        variant_pgen_idx = meta["variant_pgen_idx"].astype(np.int64)
        variant_storage_to_user = meta["variant_storage_to_user"].astype(np.int64)
        variant_user_to_storage = meta["variant_user_to_storage"].astype(np.int64)

        variant_ids_arr = meta["variant_ids"]
        variant_ids = None
        if variant_ids_arr.size > 0 and variant_ids_arr.dtype.kind == "S":
            variant_ids = variant_ids_arr.astype("S")

        file_mem = np.memmap(p, dtype=np.uint8, mode="r")

        return GenoBlocks(
            path=p,
            header=header,
            blocks=blocks,
            dtype=dtype,
            n_samples=int(header["n_samples"]),
            n_variants=int(header["n_variants"]),
            block_samples=int(header["block_samples"]),
            block_variants=int(header["block_variants"]),
            n_sample_blocks=int(header["n_sample_blocks"]),
            n_variant_blocks=int(header["n_variant_blocks"]),
            sample_ids=sample_ids,
            raw_sample_idx=raw_sample_idx,
            y=y,
            split_labels=split_labels,
            variant_pgen_idx=variant_pgen_idx,
            variant_user_to_storage=variant_user_to_storage,
            variant_storage_to_user=variant_storage_to_user,
            variant_ids=variant_ids,
            file_mem=file_mem,
        )

    def indices_for_split(self, split: str) -> np.ndarray:
        name = str(split).lower()
        if name == "train":
            code = 0
        elif name == "val":
            code = 1
        elif name == "test":
            code = 2
        else:
            raise ValueError("split must be one of: train, val, test")
        return np.flatnonzero(self.split_labels == code).astype(np.int64, copy=False)

    def variant_block_view(self, block_id: int, vblock: int) -> np.ndarray:
        rec = self.blocks[int(block_id)]
        s_ct = int(rec.s1 - rec.s0)
        offset = int(rec.base_offset) + int(vblock) * int(rec.stride_bytes)
        view = np.ndarray(
            (s_ct, int(self.block_variants)),
            dtype=np.int8,
            buffer=self.file_mem,
            offset=int(offset),
            order="C",
        )
        return view

    def for_each_variant_block(
        self,
        block_id: int,
        fn,
        torch_dtype: torch.dtype = torch.float16,
        device: Union[str, torch.device] = "cpu",
    ) -> None:
        M = int(self.n_variants)
        BV = int(self.block_variants)
        for vb in range(int(self.n_variant_blocks)):
            v0 = int(vb) * int(BV)
            V = min(int(BV), int(M - v0))
            x_np = self.variant_block_view(int(block_id), int(vb))[:, :V]
            x = torch.from_numpy(x_np)
            if torch_dtype is not None:
                x = x.to(torch_dtype)
            if str(device) != "cpu":
                x = x.to(device, non_blocking=True)
            fn(int(v0), int(V), x)


class BlockIndexDataset(TorchDataset):
    def __init__(self, n_blocks: int):
        self.n_blocks = int(n_blocks)
        if self.n_blocks <= 0:
            raise ValueError("n_blocks must be > 0.")

    def __len__(self) -> int:
        return int(self.n_blocks)

    def __getitem__(self, i: int):
        return int(i)

class Gblk2Samples(TorchDataset):
    def __init__(
        self,
        g: "GenoBlocks",
        sample_idx: np.ndarray,
        out_dtype: torch.dtype = torch.float16,
        reorder_variants: bool = True,
    ):
        self.g = g
        self.sample_idx = np.asarray(sample_idx, dtype=np.int64)
        if self.sample_idx.ndim != 1 or self.sample_idx.size == 0:
            raise ValueError("sample_idx must be a non-empty 1D array.")
        if int(self.sample_idx.max()) >= int(g.n_samples):
            raise ValueError("sample_idx exceeds n_samples.")
        self.out_dtype = out_dtype

        if reorder_variants:
            self.user_to_storage = g.variant_user_to_storage.astype(np.int64, copy=False)
        else:
            self.user_to_storage = None

        self.M = int(g.n_variants)
        self.BV = int(g.block_variants)
        self.n_vblocks = int(g.n_variant_blocks)
        self.elem_sz = int(g.dtype.itemsize)

    def __len__(self) -> int:
        return int(self.sample_idx.size)

    def _locate_block(self, row: int) -> Tuple[SampleBlockRec, int]:
        blocks = self.g.blocks
        lo = 0
        hi = len(blocks)
        while lo < hi:
            mid = (lo + hi) // 2
            b = blocks[mid]
            if row < b.s0:
                hi = mid
            elif row >= b.s1:
                lo = mid + 1
            else:
                return b, int(row - b.s0)
        raise RuntimeError("Row not found in any sample block (corrupt index).")

    def __getitem__(self, i: int):
        row = int(self.sample_idx[int(i)])
        yval = int(self.g.y[row])

        b, r = self._locate_block(row)
        s_ct = int(b.s1 - b.s0)

        # Read full feature vector by concatenating contiguous per-variant-block slices.
        # Layout: for each vblock, rows are contiguous with stride:
        #   block_base + vblock*stride + r*(BV*elem_sz)
        out = np.empty((self.M,), dtype=np.int8)
        out_pos = 0

        for vb in range(self.n_vblocks):
            v0 = vb * self.BV
            V = min(self.BV, self.M - v0)
            off = int(b.base_offset) + int(vb) * int(b.stride_bytes) + int(r) * int(self.BV) * int(self.elem_sz)

            # Map (BV,) then slice to V; this is a contiguous view into the memmap.
            chunk = np.ndarray(
                (self.BV,),
                dtype=np.int8,
                buffer=self.g.file_mem,
                offset=int(off),
                order="C",
            )[:V]

            out[out_pos : out_pos + V] = chunk
            out_pos += V

        if out_pos != self.M:
            raise RuntimeError("Internal error assembling row vector.")

        if self.user_to_storage is not None:
            out = out[self.user_to_storage]

        x = torch.from_numpy(out).to(self.out_dtype)
        y_tensor = torch.tensor(yval, dtype=torch.int64)
        return x, y_tensor


def _gblk2_dataloader(
    self: "GenoBlocks",
    split: str = "train",
    batch_size: int = 256,
    shuffle: bool = True,
    num_workers: int = 0,
    out_dtype: torch.dtype = torch.float16,
    reorder_variants: bool = True,
    pin_memory: bool = True,
) -> DataLoader:
    idx = self.indices_for_split(split)
    ds = Gblk2Samples(self, idx, out_dtype=out_dtype, reorder_variants=reorder_variants)
    return DataLoader(
        ds,
        batch_size=int(batch_size),
        shuffle=bool(shuffle),
        num_workers=int(num_workers),
        pin_memory=bool(pin_memory),
        persistent_workers=(num_workers > 0),
        prefetch_factor=(2 if num_workers > 0 else None),
    )


# Monkey-patch method onto GenoBlocks (keeps your old call-site working)
GenoBlocks.dataloader = _gblk2_dataloader


def _bucket_rows_by_sample_block(g: "GenoBlocks", rows: np.ndarray) -> List[np.ndarray]:
    rows_sorted = np.asarray(rows, dtype=np.int64)
    if rows_sorted.ndim != 1:
        raise ValueError("rows must be 1D.")
    if rows_sorted.size == 0:
        return [np.empty((0,), dtype=np.int64) for _ in g.blocks]

    rows_sorted = np.sort(rows_sorted, kind="mergesort")

    out: List[np.ndarray] = []
    ptr = 0
    n = int(rows_sorted.size)

    for rec in g.blocks:
        s0 = int(rec.s0)
        s1 = int(rec.s1)

        while ptr < n and int(rows_sorted[ptr]) < s0:
            ptr += 1

        start_ptr = ptr
        while ptr < n and int(rows_sorted[ptr]) < s1:
            ptr += 1

        if ptr > start_ptr:
            local = rows_sorted[start_ptr:ptr] - s0
            out.append(local.astype(np.int64, copy=False))
        else:
            out.append(np.empty((0,), dtype=np.int64))

        if ptr >= n:
            for _ in range(len(out), len(g.blocks)):
                out.append(np.empty((0,), dtype=np.int64))
            break

    return out


def _torch_device(dev: Union[str, torch.device]) -> torch.device:
    if isinstance(dev, torch.device):
        return dev
    return torch.device(str(dev))


def _safe_var_from_sums(sum_x: torch.Tensor, sum_x2: torch.Tensor, n: int) -> torch.Tensor:
    if n <= 0:
        raise ValueError("n must be positive.")
    n_f = float(n)
    mean = sum_x / n_f
    var = (sum_x2 / n_f) - mean * mean
    return torch.clamp(var, min=0.0)


def compute_feature_mean_std(
    self: "GenoBlocks",
    split: str = "train",
    device: Union[str, torch.device] = "cuda",
    torch_dtype: torch.dtype = torch.float32,
    eps: float = 1e-6,
    use_gpu: bool = True,
) -> Tuple[np.ndarray, np.ndarray]:
    idx = self.indices_for_split(split)
    n_rows = int(idx.size)
    if n_rows <= 1:
        raise ValueError(f"Split {split} has too few samples to compute std: n={n_rows}")

    rows_by_block = _bucket_rows_by_sample_block(self, idx)

    M = int(self.n_variants)
    BV = int(self.block_variants)

    mean_out = np.empty((M,), dtype=np.float32)
    std_out = np.empty((M,), dtype=np.float32)

    dev = _torch_device(device)
    run_on_gpu = bool(use_gpu) and (dev.type == "cuda")

    pbar = tqdm(total=int(self.n_variant_blocks), desc=f"Mean/std ({split})", unit="vblocks")

    for vb in range(int(self.n_variant_blocks)):
        v0 = int(vb) * int(BV)
        V = min(int(BV), int(M - v0))

        if run_on_gpu:
            sum_x = torch.zeros((V,), device=dev, dtype=torch.float32)
            sum_x2 = torch.zeros((V,), device=dev, dtype=torch.float32)
        else:
            sum_x = torch.zeros((V,), device="cpu", dtype=torch.float64)
            sum_x2 = torch.zeros((V,), device="cpu", dtype=torch.float64)

        for block_id, local_rows in enumerate(rows_by_block):
            if local_rows.size == 0:
                continue

            x_np = self.variant_block_view(int(block_id), int(vb))[:, :V]
            x_sel = x_np[local_rows, :]

            x_t = torch.from_numpy(x_sel)
            if run_on_gpu:
                x_t = x_t.to(device=dev, dtype=torch.float32, non_blocking=True)
            else:
                x_t = x_t.to(dtype=torch.float64)

            sx = x_t.sum(dim=0)
            sx2 = (x_t * x_t).sum(dim=0)

            sum_x += sx
            sum_x2 += sx2

        if run_on_gpu:
            var = _safe_var_from_sums(sum_x, sum_x2, n_rows)
            mean = (sum_x / float(n_rows)).to(dtype=torch.float32)
            std = torch.sqrt(var + float(eps)).to(dtype=torch.float32)

            mean_out[v0 : v0 + V] = mean.detach().cpu().numpy()
            std_out[v0 : v0 + V] = std.detach().cpu().numpy()
        else:
            mean = (sum_x / float(n_rows)).to(dtype=torch.float64)
            var = _safe_var_from_sums(sum_x, sum_x2, n_rows).to(dtype=torch.float64)
            std = torch.sqrt(var + float(eps))

            mean_out[v0 : v0 + V] = mean.numpy().astype(np.float32, copy=False)
            std_out[v0 : v0 + V] = std.numpy().astype(np.float32, copy=False)

        pbar.update(1)

    pbar.close()
    return mean_out, std_out


def compute_feature_norm(
    self: "GenoBlocks",
    split: str = "train",
    device: Union[str, torch.device] = "cuda",
    torch_dtype: torch.dtype = torch.float32,
    eps: float = 1e-6,
    use_gpu: bool = True,
) -> Tuple[np.ndarray, np.ndarray]:
    mean, std = compute_feature_mean_std(
        self,
        split=split,
        device=device,
        torch_dtype=torch_dtype,
        eps=eps,
        use_gpu=use_gpu,
    )
    inv_std = (1.0 / np.maximum(std, np.float32(eps))).astype(np.float32, copy=False)
    return mean, inv_std


def normalize_batch_(
    x: torch.Tensor,
    mean_t: torch.Tensor,
    inv_std_t: torch.Tensor,
) -> torch.Tensor:
    if x.ndim != 2:
        raise ValueError("x must be a 2D tensor [batch, features].")
    if mean_t.ndim != 1 or inv_std_t.ndim != 1:
        raise ValueError("mean_t and inv_std_t must be 1D tensors [features].")
    if x.shape[1] != mean_t.shape[0] or x.shape[1] != inv_std_t.shape[0]:
        raise ValueError("Feature dimension mismatch for normalization.")
    x.sub_(mean_t).mul_(inv_std_t)
    return x


GenoBlocks.compute_feature_mean_std = compute_feature_mean_std
GenoBlocks.compute_feature_norm = compute_feature_norm
GenoBlocks.normalize_batch_ = staticmethod(normalize_batch_)
