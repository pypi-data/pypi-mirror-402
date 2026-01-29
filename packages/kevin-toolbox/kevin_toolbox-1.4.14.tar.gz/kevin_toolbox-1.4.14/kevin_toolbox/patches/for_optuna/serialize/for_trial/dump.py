from datetime import datetime
import optuna
import kevin_toolbox.nested_dict_list as ndl


def __converter(_, v):
    if isinstance(v, optuna.distributions.BaseDistribution):
        return dict(name=f'optuna.distributions.{v.__class__.__name__}', paras=v.__dict__)
    elif isinstance(v, optuna.trial.TrialState):
        return dict(name=f'optuna.trial.TrialState', value=v.value, description=v.name)
    elif isinstance(v, datetime):
        return dict(name="datetime", timestamp=v.timestamp(), description=f'{v}')
    return v


def dump(trial):
    assert isinstance(trial, optuna.trial.BaseTrial)

    res_s = dict()
    for k, v in ndl.copy_(var=trial.__dict__, b_deepcopy=True).items():
        if k.startswith("_"):
            k = k[1:]
        res_s[k] = v

    res_s = ndl.traverse(var=res_s, match_cond=lambda _, __, v: not isinstance(v, (list, dict,)),
                         action_mode="replace", converter=__converter, b_use_name_as_idx=False)

    return res_s
