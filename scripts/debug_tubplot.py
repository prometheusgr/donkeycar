import os
import tarfile
import tempfile
from donkeycar.parts.keras import KerasLinear
from donkeycar.management.base import ShowPredictionPlots


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
    print('tub_tar:', tub_tar)
    with tarfile.open(tub_tar) as f:
        f.extractall(tmpd)
    tub_dir = os.path.join(tmpd, 'tub')
    cfg_file = os.path.join(tmpd, 'config.py')
    with open(cfg_file, 'w') as f:
        f.write('# config file\nIMAGE_H = 120\nIMAGE_W = 160\nIMAGE_DEPTH = 3\n')

    sp = ShowPredictionPlots()
    print('calling plot_predictions...')
    sp.plot_predictions(load_config := __import__('donkeycar.management.base', fromlist=['load_config']).load_config(
        cfg_file), tub_dir, model_path, limit=1000, model_type='linear', noshow=True)
    print('done. Listing model dir:')
    print(os.listdir(model_dir))


if __name__ == '__main__':
    main()
