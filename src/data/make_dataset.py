import tarfile
import argparse
import os
import shutil
import numpy as np
from sklearn.model_selection import train_test_split

PATH = "data/raw/images.tar.gz"

def extract_tar(tar_path, out_path):
    tar_path, out_path = map(os.path.abspath, (tar_path, out_path))

    if not os.path.isdir(os.path.join(out_path, 'images')):
        assert os.path.isfile(tar_path)
        tarfile.open(tar_path).extractall(path=out_path)
        os.rmdir(os.path.join(out_path, 'images', 'Train Directory', 'Predicted'))
        return 0


def split_folder(path, val_num:int = 100, test_size:float = 0.2, shuffle:bool = True, stratify:bool = True,
               random_state:int = None):
    #valid is subset of test
    all_img_filenames = np.array([os.path.join(path_, name) for path_, subdirs, files in
                                  os.walk(os.path.abspath(path)) for name in files])

    print(len(all_img_filenames), 'images found.')

    if stratify:
        label_fn = lambda x: x.split('/')[-2]
        y = np.array([ label_fn(i) for i in all_img_filenames ])

        train_names, test_names, y_train, y_test = train_test_split(all_img_filenames, y, test_size=test_size, random_state=random_state,
                                                   shuffle=shuffle, stratify=y)

        val_size = val_num / len(y_test)

        _, valid_names = train_test_split(test_names, test_size=val_size, random_state=random_state,
                                                   shuffle=shuffle, stratify=y_test)
    else:
        train_names, test_names = train_test_split(all_img_filenames, test_size=test_size,
                                                                    random_state=random_state,
                                                                    shuffle=shuffle)

        val_size = val_num / len(test_names)

        _, valid_names = train_test_split(test_names, test_size=val_size, random_state=random_state,
                                          shuffle=shuffle)

    var_dict = {'train': train_names, 'valid': valid_names, 'test': test_names}

    for f in var_dict:
        folder = os.path.join(os.path.abspath('data'), 'processed', f)
        if not os.path.isdir(folder):
            os.mkdir(folder)

        for fpath in var_dict[f]:
            process_image(fpath, folder)


def process_image(path, dst):
    shutil.copy(path, dst)


def main(args):
    if args.tarInput:
        if args.tarOutput:
            extract_tar(args.tarInput, args.tarOutput)

    if args.image_dir:
        split_folder(args.image_dir, test_size=0.6, random_state=42)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Extract and process dataset')
    parser.add_argument('--tarInput', type=str, help='path for tar file')
    parser.add_argument('--tarOutput', type=str, help='path for output')
    parser.add_argument('--image_dir', type=str, help='image folder')

    args = parser.parse_args()

    main(args)
