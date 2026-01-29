from datetime import datetime
import optuna
import kevin_toolbox.nested_dict_list as ndl


def __converter(_, v):
    if v["name"].startswith("optuna.distributions."):
        v = eval(v["name"])(**v["paras"])
    elif v["name"] == "optuna.trial.TrialState":
        v = eval(v["name"])(v["value"])
    elif v["name"] == "datetime":
        v = datetime.fromtimestamp(v["timestamp"])

    return v


def load(var):
    assert isinstance(var, dict)

    var = ndl.traverse(var=var, match_cond=lambda _, __, v: isinstance(v, (dict,)) and "name" in v,
                       action_mode="replace", converter=__converter, b_use_name_as_idx=False)
    var.setdefault("value", None)
    var.setdefault("values", None)

    trial = optuna.trial.FrozenTrial(**var)
    trial._validate()
    return trial
