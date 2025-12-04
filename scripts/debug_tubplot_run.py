#!/usr/bin/env python3
"""Debug helper to reproduce tubplot test locally and print stdout/stderr."""
import os
import tarfile
import tempfile
import shutil
from donkeycar import utils


def main():
    cardir = tempfile.mkdtemp(prefix='debug_tubplot_')
    try:
        model_dir = os.path.join(cardir, 'models')
        os.mkdir(model_dir)
        model_path = os.path.join(model_dir, 'model.savedmodel')
        from donkeycar.parts.keras import KerasLinear
        KerasLinear().interpreter.model.save(model_path)

        this_dir = os.path.join(os.path.dirname(__file__), '..', 'donkeycar', 'tests')
        tub_tar = os.path.join(this_dir, 'tub', 'tub.tar.gz')
        with tarfile.open(tub_tar) as file:
            file.extractall(cardir)

        tub_dir = os.path.join(cardir, 'tub')
        cfg_file = os.path.join(cardir, 'config.py')
        with open(cfg_file, 'w+') as f:
            f.writelines(["# config file\n", "IMAGE_H = 120\n", "IMAGE_W = 160\n", "IMAGE_DEPTH = 3\n", "\n"])

        cmd = ['donkey', 'tubplot', '--tub', tub_dir, '--model', model_path, '--type', 'linear', '--noshow']
        out, err, pid = utils.run_shell_command(cmd, cwd=cardir, timeout=30)
        print('STDOUT:')
        for l in out:
            print(l, end='')
        print('\nSTDERR:')
        for e in err:
            try:
                print(e.decode(), end='')
            except Exception:
                print(e, end='')

        print('\nModel dir listing:', os.listdir(model_dir))
        print('Pred file exists?', os.path.exists(model_path + '_pred.png'))

    finally:
        shutil.rmtree(cardir)


if __name__ == '__main__':
    main()
