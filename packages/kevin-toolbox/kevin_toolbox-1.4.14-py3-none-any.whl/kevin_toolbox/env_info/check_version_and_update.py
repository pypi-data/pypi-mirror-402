import subprocess

try:
    from kevin_toolbox.env_info import version
except:
    import version


def check_version_and_update(package_name, cur_version=None, available_versions=None):
    """
        检查当前版本，并尝试更新
            - 若在 pip 的可用版本中，有比当前版本更高的版本，则更新到可以获取到的最新版本。
    """
    # try to read cur_version
    if cur_version is None:
        ex = subprocess.Popen(f'pip list | grep "{package_name} "', shell=True, stdout=subprocess.PIPE)
        out, _ = ex.communicate()
        out = out.decode().strip()
        cur_version = out.split(package_name)[-1].strip()

    # try to read available versions
    if available_versions is None:
        ex = subprocess.Popen(f'pip install {package_name}==?', shell=True, stdout=subprocess.PIPE,
                              stderr=subprocess.STDOUT)
        out, _ = ex.communicate()
        out = out.decode().strip()
        if "(from versions:" in out:
            v_ls = out.split("(from versions:")[-1].rsplit(")", 1)[0].split(",", -1)
            v_ls = [i.strip() for i in v_ls]
        else:
            v_ls = ["none"]
        available_versions = version.sort_ls(version_ls=v_ls, reverse=True)

    b_success_updated = False
    new_version = None
    if len(available_versions) > 0 and version.compare(available_versions[0], ">", cur_version):
        ex = subprocess.Popen(
            f'pip install {package_name}=={available_versions[0]} --no-dependencies',
            shell=True, stdout=subprocess.PIPE
        )
        out, _ = ex.communicate()
        msg = out.decode().strip()
        if ex.returncode == 0:
            b_success_updated = True
            new_version = available_versions[0]
    else:
        msg = "Already the latest version, no need to update"

    res_s = dict(version_before_updated=cur_version, version_after_updated=new_version,
                 available_versions=available_versions, b_success_updated=b_success_updated, msg=msg)

    return res_s


if __name__ == '__main__':
    import argparse

    out_parser = argparse.ArgumentParser(description='check_version_and_update')
    out_parser.add_argument('--package_name', type=str, required=True)
    out_parser.add_argument('--cur_version', type=str, required=False)
    out_parser.add_argument('--available_versions', nargs='+', type=str, required=False)
    out_parser.add_argument('--verbose', type=lambda x: bool(eval(x)), required=False, default=True)
    args = out_parser.parse_args().__dict__

    b_version = args.pop("verbose")

    res_s_ = check_version_and_update(**args)

    if b_version:
        for k, v in res_s_.items():
            print(f"{k}: {v}")
