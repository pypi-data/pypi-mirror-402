from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Union
import os
import math
import numpy as np
import torch
from tqdm import tqdm
import pgenlib as pg
from wgsml.data import Dataset, VariantSelection, pvar_ids_for_indices


def bh_fdr(pvalues: np.ndarray) -> np.ndarray:
    p = np.asarray(pvalues, dtype=np.float64)
    m = int(p.size)
    if m == 0:
        return np.asarray([], dtype=np.float64)
    order = np.argsort(p, kind="mergesort")
    ranked = p[order]
    q = ranked * (m / (np.arange(1, m + 1, dtype=np.float64)))
    q = np.minimum.accumulate(q[::-1])[::-1]
    q = np.clip(q, 0.0, 1.0)
    out = np.empty_like(q)
    out[order] = q
    return out

@dataclass
class MIResults:
    pvar_path: str
    n_samples: int
    n_variants: int
    conditioned: bool
    df: Optional[int]
    mi_bits: np.ndarray
    n_eff: np.ndarray
    g_stat: Optional[np.ndarray]
    p_values: Optional[np.ndarray]
    q_values: Optional[np.ndarray]

    def has_p(self) -> bool:
        return self.p_values is not None and self.g_stat is not None and self.df is not None

    def has_q(self) -> bool:
        return self.q_values is not None

    def compute_q(self) -> "MIResults":
        if not self.has_p():
            raise ValueError("p-values are not available for this result.")
        self.q_values = bh_fdr(self.p_values)
        return self

    def filter(
        self,
        p_value: Optional[float] = None,
        fdr: Optional[float] = None,
        mi_min: Optional[float] = None,
        topk: Optional[int] = None,
        sort_by: str = "idx",
        descending: bool = True,
    ) -> VariantSelection:
        if p_value is not None and not self.has_p():
            raise ValueError("Requested p_value filtering, but p-values are not available.")

        if fdr is not None:
            if not self.has_q():
                if self.has_p():
                    self.compute_q()
                else:
                    raise ValueError("Requested fdr filtering, but q-values are not available.")

        keep = np.ones((self.n_variants,), dtype=bool)
        if mi_min is not None:
            keep &= (self.mi_bits >= float(mi_min))
        if p_value is not None:
            keep &= (self.p_values <= float(p_value))
        if fdr is not None:
            keep &= (self.q_values <= float(fdr))

        idx = np.flatnonzero(keep).astype(np.int64, copy=False)
        if idx.size == 0:
            return VariantSelection(idx=idx)

        if topk is not None:
            k = int(topk)
            if k <= 0:
                return VariantSelection(idx=np.empty((0,), dtype=np.int64))
            if idx.size > k:
                mi = self.mi_bits[idx]
                part = np.argpartition(mi, -k)[-k:]
                idx = idx[part]
                # deterministic tie-breaking, sort by (mi_bits desc, idx asc)
                ord_idx = np.lexsort((idx, -self.mi_bits[idx]))
                idx = idx[ord_idx]

        sb = str(sort_by)
        if sb == "idx":
            ord_idx = np.argsort(idx, kind="mergesort")
            if bool(descending):
                ord_idx = ord_idx[::-1]
            idx = idx[ord_idx]

        elif sb == "mi_bits":
            ord_idx = np.lexsort((idx, self.mi_bits[idx]))
            if bool(descending):
                ord_idx = ord_idx[::-1]
            idx = idx[ord_idx]

        elif sb == "p_value":
            if self.p_values is None:
                raise ValueError("Requested sort_by='p_value', but p-values are not available.")
            ord_idx = np.lexsort((idx, self.p_values[idx]))
            # smaller p is better
            idx = idx[ord_idx]

        elif sb == "q_value":
            if self.q_values is None:
                if self.has_p():
                    self.compute_q()
                else:
                    raise ValueError("Requested sort_by='q_value', but q-values are not available.")
            ord_idx = np.lexsort((idx, self.q_values[idx]))
            # smaller q is better
            idx = idx[ord_idx]

        else:
            raise ValueError("sort_by must be one of: idx, mi_bits, p_value, q_value")

        return VariantSelection(idx=idx)


    def topk(self, k: int) -> VariantSelection:
        kk = int(k)
        if kk <= 0:
            return VariantSelection(idx=np.empty((0,), dtype=np.int64))
        kk = min(kk, int(self.n_variants))
        part = np.argpartition(self.mi_bits, -kk)[-kk:].astype(np.int64, copy=False)
        ord_idx = np.argsort(self.mi_bits[part], kind="mergesort")[::-1]
        return VariantSelection(idx=part[ord_idx])

    def ids(self, selection: VariantSelection, block_size: int = 100_000) -> np.ndarray:
        return pvar_ids_for_indices(self.pvar_path, selection.indices(), block_size=block_size)

    def save(
        self,
        path: str,
        include_p: bool = True,
        include_q: bool = True,
        include_variant_ids: bool = False,
    ) -> str:
        if include_q and not self.has_q():
            if self.has_p():
                self.compute_q()
            else:
                include_q = False

        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)

        payload: Dict[str, np.ndarray] = {
            "schema": np.asarray([1], dtype=np.int32),
            "pvar_path": np.asarray([self.pvar_path], dtype=object),
            "n_samples": np.asarray([int(self.n_samples)], dtype=np.int64),
            "n_variants": np.asarray([int(self.n_variants)], dtype=np.int64),
            "conditioned": np.asarray([1 if self.conditioned else 0], dtype=np.int8),
            "df": np.asarray([-1 if self.df is None else int(self.df)], dtype=np.int32),
            "mi_bits": self.mi_bits.astype(np.float32, copy=False),
            "n_eff": self.n_eff.astype(np.uint32, copy=False),
        }

        if include_p and self.has_p():
            payload["g_stat"] = self.g_stat.astype(np.float32, copy=False)
            payload["p_values"] = self.p_values.astype(np.float64, copy=False)
        if include_q and self.has_q():
            payload["q_values"] = self.q_values.astype(np.float64, copy=False)
        if include_variant_ids:
            payload["variant_ids"] = pvar_ids_for_indices(self.pvar_path, np.arange(self.n_variants, dtype=np.int64))

        np.savez(path, **payload)
        return path

    @staticmethod
    def load(path: str, pvar_path: Optional[str] = None) -> "MIResults":
        meta = np.load(path, allow_pickle=True)

        pvar = str(meta["pvar_path"][0]) if "pvar_path" in meta else (str(pvar_path) if pvar_path is not None else "")
        if not pvar:
            raise ValueError("pvar_path is required (either stored in file or passed to load).")

        n_samples = int(meta["n_samples"][0])
        n_variants = int(meta["n_variants"][0])
        conditioned = bool(int(meta["conditioned"][0]))
        df_val = int(meta["df"][0])
        df_out = None if df_val < 0 else df_val

        mi_bits = meta["mi_bits"].astype(np.float32, copy=False)
        n_eff = meta["n_eff"].astype(np.uint32, copy=False)

        g_stat = meta["g_stat"].astype(np.float32, copy=False) if "g_stat" in meta else None
        p_values = meta["p_values"].astype(np.float64, copy=False) if "p_values" in meta else None
        q_values = meta["q_values"].astype(np.float64, copy=False) if "q_values" in meta else None

        return MIResults(
            pvar_path=pvar,
            n_samples=n_samples,
            n_variants=n_variants,
            conditioned=conditioned,
            df=df_out,
            mi_bits=mi_bits,
            n_eff=n_eff,
            g_stat=g_stat,
            p_values=p_values,
            q_values=q_values,
        )


def encode_labels(y: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    y_arr = np.asarray(y, dtype=np.int64)
    uniq = np.unique(y_arr)
    mapping: Dict[int, int] = {int(v): i for i, v in enumerate(uniq.tolist())}
    y_enc = np.fromiter((mapping[int(v)] for v in y_arr.tolist()), dtype=np.int64, count=y_arr.size)
    return y_enc, uniq.astype(np.int64, copy=False)


def make_condition_groups(conditions: np.ndarray, max_states: int) -> List[np.ndarray]:
    z = np.asarray(conditions)
    if z.ndim == 1:
        z = z.reshape(-1, 1)
    if z.ndim != 2:
        raise ValueError("conditional_on must be a 1D or 2D array.")

    n = int(z.shape[0])
    if n == 0:
        raise ValueError("conditional_on has zero rows.")

    codes = np.zeros((n,), dtype=np.int64)
    base = np.int64(1)

    for j in range(int(z.shape[1])):
        col = z[:, j]
        uniq, inv = np.unique(col, return_inverse=True)
        inv = inv.astype(np.int64, copy=False)

        next_base = base * np.int64(max(1, int(uniq.size)))
        if int(next_base) <= 0 or int(next_base) > (1 << 60):
            raise ValueError("conditional_on has too many states to encode safely.")
        codes = codes + inv * base
        base = next_base

    _, z_inv = np.unique(codes, return_inverse=True)
    m = int(np.max(z_inv)) + 1
    if m > int(max_states):
        raise ValueError(f"conditional_on has {m} unique states; max_states is {int(max_states)}.")

    groups: List[np.ndarray] = []
    for zi in range(m):
        groups.append(np.flatnonzero(z_inv == zi).astype(np.int64, copy=False))
    return groups


def chi2_sf(g_stat: torch.Tensor, df: int) -> torch.Tensor:
    g64 = g_stat.to(torch.float64)
    if int(df) == 2:
        return torch.exp(-0.5 * g64)
    chi2 = torch.distributions.Chi2(torch.tensor(float(df), device=g_stat.device, dtype=torch.float64))
    cdf = chi2.cdf(g64)
    return (1.0 - cdf).clamp_min(0.0).clamp_max(1.0)


def gtest_from_mi_bits(mi_bits: torch.Tensor, n_eff: torch.Tensor) -> torch.Tensor:
    ln2 = torch.tensor(float(math.log(2.0)), device=mi_bits.device, dtype=torch.float64)
    return (2.0 * n_eff.to(torch.float64) * ln2) * mi_bits.to(torch.float64)


def mi_block_no_missing(g_i8: torch.Tensor, y_enc: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
    f = int(g_i8.shape[0])
    n = int(g_i8.shape[1])

    classes = int(torch.max(y_enc).item()) + 1
    if classes < 2:
        raise ValueError("Need at least 2 phenotype classes.")

    y = y_enc.to(torch.int64)
    n_eff = torch.full((f,), n, device=g_i8.device, dtype=torch.int32)

    counts = torch.empty((f, 3, classes), device=g_i8.device, dtype=torch.int32)
    for gi in (0, 1, 2):
        mg = (g_i8 == gi)
        for c in range(classes):
            counts[:, gi, c] = (mg & (y.unsqueeze(0) == c)).sum(dim=1, dtype=torch.int32)

    nf = n_eff.to(torch.float64)
    pxy = counts.to(torch.float64) / nf[:, None, None]
    px = pxy.sum(dim=2, keepdim=True)
    py = pxy.sum(dim=1, keepdim=True)
    denom = (px * py).clamp_min(1e-300)

    term = torch.where(pxy > 0, pxy * torch.log(pxy / denom), torch.zeros_like(pxy))
    mi_bits = term.sum(dim=(1, 2)) / math.log(2.0)

    return mi_bits.to(torch.float64), n_eff


def mi_block_masked(g_i8: torch.Tensor, y_enc: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
    f = int(g_i8.shape[0])

    classes = int(torch.max(y_enc).item()) + 1
    if classes < 2:
        raise ValueError("Need at least 2 phenotype classes.")

    y = y_enc.to(torch.int64)

    counts = torch.empty((f, 3, classes), device=g_i8.device, dtype=torch.int32)
    n_eff = torch.zeros((f,), device=g_i8.device, dtype=torch.int32)

    for gi in (0, 1, 2):
        mg = (g_i8 == gi)
        n_eff += mg.sum(dim=1, dtype=torch.int32)
        for c in range(classes):
            counts[:, gi, c] = (mg & (y.unsqueeze(0) == c)).sum(dim=1, dtype=torch.int32)

    nf = n_eff.to(torch.float64).clamp_min(1.0)
    pxy = counts.to(torch.float64) / nf[:, None, None]
    px = pxy.sum(dim=2, keepdim=True)
    py = pxy.sum(dim=1, keepdim=True)
    denom = (px * py).clamp_min(1e-300)

    term = torch.where(pxy > 0, pxy * torch.log(pxy / denom), torch.zeros_like(pxy))
    mi_bits = term.sum(dim=(1, 2)) / math.log(2.0)

    return mi_bits.to(torch.float64), n_eff


def cmi_block_no_missing(
    g_i8: torch.Tensor,
    y_enc: torch.Tensor,
    group_cols: List[torch.Tensor],
) -> Tuple[torch.Tensor, torch.Tensor]:
    f = int(g_i8.shape[0])
    n = int(g_i8.shape[1])

    n_eff_total = torch.full((f,), n, device=g_i8.device, dtype=torch.int32)
    mi_total = torch.zeros((f,), device=g_i8.device, dtype=torch.float64)

    inv_n = 1.0 / float(n)
    for cols in group_cols:
        if cols.numel() == 0:
            continue
        gz = torch.index_select(g_i8, 1, cols)
        yz = torch.index_select(y_enc, 0, cols)
        mi_z, _ = mi_block_no_missing(gz, yz)
        pz = float(cols.numel()) * inv_n
        mi_total = mi_total + (pz * mi_z)

    return mi_total, n_eff_total


def cmi_block_masked(
    g_i8: torch.Tensor,
    y_enc: torch.Tensor,
    group_cols: List[torch.Tensor],
) -> Tuple[torch.Tensor, torch.Tensor]:
    f = int(g_i8.shape[0])

    n_eff_total = torch.zeros((f,), device=g_i8.device, dtype=torch.int32)
    for gi in (0, 1, 2):
        n_eff_total += (g_i8 == gi).sum(dim=1, dtype=torch.int32)
    nf_total = n_eff_total.to(torch.float64).clamp_min(1.0)

    mi_total = torch.zeros((f,), device=g_i8.device, dtype=torch.float64)

    for cols in group_cols:
        if cols.numel() == 0:
            continue
        gz = torch.index_select(g_i8, 1, cols)
        yz = torch.index_select(y_enc, 0, cols)
        mi_z, n_eff_z = mi_block_masked(gz, yz)
        pz = n_eff_z.to(torch.float64) / nf_total
        mi_total = mi_total + pz * mi_z

    return mi_total, n_eff_total


def mutual_information(
    ds: Dataset,
    subset: str = "train",
    conditional_on: Optional[Union[np.ndarray, torch.Tensor]] = None,
    device: str = "auto",
    block_variants: Union[int, str] = 4096,
    compute_p: bool = True,
    max_condition_states: int = 256,
    verbose: bool = True,
):
    subset_name = str(subset).lower()
    if subset_name not in {"train", "val", "test", "all"}:
        raise ValueError("subset must be one of: train, val, test, all")

    if subset_name != "all" and ds.splits is None:
        raise ValueError(
            f"Requested subset='{subset_name}', but ds.splits is None. "
            "Call ds.split(...) first, or use subset='all'."
        )

    if subset_name == "all":
        sel_idx = np.arange(ds.y_used.size, dtype=np.int64)
    else:
        if subset_name == "train":
            sel_idx = ds.splits.train.astype(np.int64, copy=False)
        elif subset_name == "val":
            sel_idx = ds.splits.val.astype(np.int64, copy=False)
        else:
            sel_idx = ds.splits.test.astype(np.int64, copy=False)

    if sel_idx.size == 0:
        raise ValueError(f"Selected subset '{subset_name}' is empty.")

    raw_sample_cols = ds.raw_keep_idx[sel_idx].astype(np.int64, copy=False)
    y_sel = ds.y_used[sel_idx].astype(np.int64, copy=False)

    y_enc_np, _ = encode_labels(y_sel)
    k = int(np.max(y_enc_np)) + 1
    if k < 2:
        raise ValueError(f"Phenotype must have at least two classes in subset='{subset_name}'.")

    if device == "auto":
        dev = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    else:
        dev = torch.device(str(device))

    if dev.type == "cuda":
        torch.backends.cuda.matmul.allow_tf32 = False
        torch.backends.cudnn.allow_tf32 = False
        torch.set_float32_matmul_precision("highest")

    conditioned = conditional_on is not None
    df = int(2 * (k - 1)) if (compute_p and not conditioned) else None

    group_cols: Optional[List[torch.Tensor]] = None
    if conditioned:
        cond = conditional_on
        if isinstance(cond, torch.Tensor):
            cond = cond.detach().cpu().numpy()
        cond = np.asarray(cond)

        if cond.shape[0] != int(y_enc_np.shape[0]):
            raise ValueError(
                "conditional_on must have the same number of rows as the selected subset. "
                f"Got conditional_on rows={cond.shape[0]} vs subset rows={int(y_enc_np.shape[0])}."
            )

        groups_np = make_condition_groups(cond, max_states=max_condition_states)
        group_cols = [torch.tensor(g, device=dev, dtype=torch.int64) for g in groups_np]

    y_enc_t = torch.tensor(y_enc_np, device=dev, dtype=torch.int64)

    if isinstance(block_variants, str):
        if block_variants != "auto":
            raise ValueError("block_variants must be an int or 'auto'.")
        bs = 4096
    else:
        bs = int(block_variants)
    bs = int(max(16, bs))

    with pg.PgenReader(ds.pgen_path.encode("utf-8")) as reader:
        total = int(reader.get_variant_ct())
        raw_n = int(reader.get_raw_sample_ct())

        if total <= 0:
            raise ValueError("PGEN has zero variants.")
        if raw_n <= 0:
            raise ValueError("PGEN has zero samples.")
        if raw_sample_cols.size == 0:
            raise ValueError(f"No samples in subset='{subset_name}' after phenotype filtering.")
        if int(raw_sample_cols.max()) >= raw_n:
            raise ValueError("Selected sample indices exceed PGEN sample axis.")

        n_used = int(raw_sample_cols.size)

        raw_gt = np.empty((bs, raw_n), dtype=np.int8)
        used_gt = np.empty((bs, n_used), dtype=np.int8)

        mi_bits_all = np.empty((total,), dtype=np.float32)
        n_eff_all = np.empty((total,), dtype=np.uint32)
        g_stat_all = np.empty((total,), dtype=np.float32) if (compute_p and not conditioned) else None
        p_values_all = np.empty((total,), dtype=np.float64) if (compute_p and not conditioned) else None

        for start in tqdm(range(0, total, bs), disable=not verbose, desc=f"Computing MI ({subset_name})"):
            end = min(start + bs, total)
            span = int(end - start)

            reader.read_range(int(start), int(end), raw_gt[:span])
            np.take(raw_gt[:span], raw_sample_cols, axis=1, out=used_gt[:span])

            bad = (used_gt[:span] < 0) | (used_gt[:span] > 2)
            clean = not bool(bad.any())

            g_dev = torch.from_numpy(used_gt[:span]).to(dev)

            if not conditioned:
                if clean:
                    mi_t, n_eff_t = mi_block_no_missing(g_dev, y_enc_t)
                else:
                    mi_t, n_eff_t = mi_block_masked(g_dev, y_enc_t)
            else:
                if clean:
                    mi_t, n_eff_t = cmi_block_no_missing(g_dev, y_enc_t, group_cols=group_cols or [])
                else:
                    mi_t, n_eff_t = cmi_block_masked(g_dev, y_enc_t, group_cols=group_cols or [])

            mi_bits_all[start:end] = mi_t.detach().cpu().numpy().astype(np.float32, copy=False)
            n_eff_all[start:end] = n_eff_t.detach().cpu().numpy().astype(np.uint32, copy=False)

            if compute_p and not conditioned:
                g_stat_t = gtest_from_mi_bits(mi_t, n_eff_t)
                p_t = chi2_sf(g_stat_t, df=int(df))
                g_stat_all[start:end] = g_stat_t.detach().cpu().numpy().astype(np.float32, copy=False)
                p_values_all[start:end] = p_t.detach().cpu().numpy().astype(np.float64, copy=False)

    res = MIResults(
        pvar_path=str(ds.pvar_path),
        n_samples=int(raw_sample_cols.size),
        n_variants=int(total),
        conditioned=bool(conditioned),
        df=df,
        mi_bits=mi_bits_all,
        n_eff=n_eff_all,
        g_stat=g_stat_all,
        p_values=p_values_all,
        q_values=None,
    )

    if res.has_p():
        res.compute_q()

    return res

