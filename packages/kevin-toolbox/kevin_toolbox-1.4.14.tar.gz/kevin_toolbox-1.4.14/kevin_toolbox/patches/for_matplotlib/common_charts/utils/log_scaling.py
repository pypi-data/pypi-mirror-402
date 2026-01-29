import numpy as np


def log_scaling(x_ls, log_scale=None, ticks=None, tick_labels=None, b_replace_nan_inf_with_none=True,
                label_formatter=None):
    original_x_ls = None
    if isinstance(x_ls, np.ndarray):
        original_x_ls = x_ls
        x_ls = x_ls.reshape(-1)
    if isinstance(label_formatter, (str,)):
        assert label_formatter.startswith("<eval>")
        label_formatter = eval(label_formatter[6:])
    label_formatter = label_formatter or (lambda x: f"{x:.2e}")
    raw_x_ls, x_ls = x_ls, []
    none_idx_ls = []
    for idx, i in enumerate(raw_x_ls):
        if i is None or np.isnan(i) or np.isinf(i):
            none_idx_ls.append(idx)
        else:
            x_ls.append(i)
    x_ls = np.asarray(x_ls)
    if isinstance(ticks, int):
        ticks = np.linspace(np.min(x_ls), np.max(x_ls), ticks
                            ) if log_scale is None else np.logspace(
            np.log(np.min(x_ls)) / np.log(log_scale), np.log(np.max(x_ls)) / np.log(log_scale), ticks, base=log_scale)
    #
    if log_scale is not None:
        assert log_scale > 0 and np.min(x_ls) > 0
        if ticks is None:
            ticks = sorted(list(set(x_ls.reshape(-1).tolist())))
        if tick_labels is None:
            tick_labels = [label_formatter(j) for j in ticks]
        assert len(ticks) == len(tick_labels)
        ticks = [np.log(j) / np.log(log_scale) for j in ticks]
        x_ls = np.log(x_ls) / np.log(log_scale)
    else:
        if ticks is None:
            from matplotlib.ticker import MaxNLocator
            locator = MaxNLocator()
            ticks = locator.tick_values(np.min(x_ls), np.max(x_ls))
        if ticks is not None and tick_labels is None:
            tick_labels = [label_formatter(j) for j in ticks]

    if none_idx_ls:
        x_ls = x_ls.tolist()
        for idx in none_idx_ls:
            if b_replace_nan_inf_with_none:
                x_ls.insert(idx, None)
            else:
                x_ls.insert(idx, raw_x_ls[idx])

    if original_x_ls is not None:
        x_ls = np.asarray(x_ls, dtype=original_x_ls.dtype).reshape(original_x_ls.shape)

    return x_ls, ticks, tick_labels


if __name__ == "__main__":
    x_ls_ = np.linspace(0.1, 100, 10)

    out_ls_, ticks_, tick_labels_ = log_scaling(x_ls_, log_scale=10, ticks=5)
    print(out_ls_)
    print(ticks_)
    print(tick_labels_)

    x_ls_[2] = np.inf
    x_ls_[3] = -np.inf
    x_ls_[4] = -np.nan
    print(x_ls_)
    out_ls_, ticks_, tick_labels_ = log_scaling(x_ls_, log_scale=10, ticks=5)
    print(out_ls_)
    print(ticks_)
    print(tick_labels_)
