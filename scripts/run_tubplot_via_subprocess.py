import os
import tarfile
import tempfile
import subprocess
import sys

from donkeycar.parts.keras import KerasLinear
from donkeycar import utils


def main():
    '''Run tubplot via subprocess to test it works as expected.'''
    tmpd = tempfile.mkdtemp(prefix='debug_tubplot_')
    model_dir = os.path.join(tmpd, 'models')
    os.mkdir(model_dir)
    model_path = os.path.join(model_dir, 'model.savedmodel')
    print('model_path:', model_path)
    KerasLinear().interpreter.model.save(model_path)
    this_dir = os.path.join(os.path.dirname(__file__),
                            '..', 'donkeycar', 'tests')
    tub_tar = os.path.join(this_dir, 'tub', 'tub.tar.gz')
    with tarfile.open(tub_tar) as f:
        f.extractall(tmpd)
    tub_dir = os.path.join(tmpd, 'tub')

    # create a config.py in the tmp dir like the test does
    cfg_file = os.path.join(tmpd, 'config.py')
    with open(cfg_file, 'w', encoding='utf-8') as f:
        f.write('# config file\nIMAGE_H = 120\nIMAGE_W = 160\nIMAGE_DEPTH = 3\n')

    cmd = [sys.executable, '-m', 'donkeycar.management.base', 'tubplot',
           '--tub', tub_dir, '--model', model_path, '--type', 'linear', '--noshow']
    print('running:', cmd)
    out, err, pid = utils.run_shell_command(cmd, cwd=tmpd)
    print('stdout:')
    print(''.join(out))
    print('stderr:')
    for e in err:
        try:
            print(e.decode())
        except Exception:
            print(e)
    print('List model dir:', os.listdir(model_dir))


if __name__ == '__main__':
    main()
