import tarfile
import argparse
import os
import shutil
import numpy as np
from sklearn.model_selection import train_test_split
from torchvision.transforms import CenterCrop, Resize, Compose
from PIL import Image
from concurrent.futures import ThreadPoolExecutor
from functools import partial
from tqdm import tqdm

PATH = "data/raw/images.tar.gz"
TEST_SIZE = 0.2
N_VAL = 100

def extract_tar(tar_path, out_path):
    """
    To extract the compressed dataset
    :param tar_path: path for the compressed file
    :param out_path: path for the output directory
    :return: 0 if successfull else None
    """
    tar_path, out_path = map(os.path.abspath, (tar_path, out_path))

    if not os.path.isdir(os.path.join(out_path, 'images')):
        assert os.path.isfile(tar_path)
        tarfile.open(tar_path).extractall(path=out_path)
        os.rmdir(os.path.join(out_path, 'images', 'Train Directory', 'Predicted'))
        return 0


def split_folder(imgdir, outdir, val_num:int = 100, test_size:float = 0.2, shuffle:bool = True, stratify:bool = True,
                 random_state:int = None):
    """
    To create folders for image loader and also to process images
    :param imgdir: path of train directory
    :param val_num: number of validation images
    :param test_size: test fraction
    :param shuffle:
    :param stratify: to maintain class ratio
    :param random_state:
    :return: None
    """
    #valid is subset of test
    all_img_filenames = np.array([os.path.join(path, name) for path, subdirs, files in
                                  os.walk(os.path.abspath(imgdir)) for name in files])

    labels = os.listdir(imgdir)

    print(len(all_img_filenames), 'images found belonging to', len(labels), 'classes.')

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

    for v in var_dict: print(len(var_dict[v]), v, 'images')

    # checking for processed folder
    outdir = os.path.abspath(outdir)
    if not os.path.isdir(outdir):
        os.mkdir(outdir)

    for f in tqdm(var_dict):
        # creating train valid test folders
        folder = os.path.join(outdir, f)
        if not os.path.isdir(folder):
            os.mkdir(folder)

        for label in labels:
            cls_dir = os.path.join(folder, label)
            # creating label folders
            if not os.path.isdir(cls_dir):
                os.mkdir(cls_dir)

        _process_image = partial(process_image, dst=folder)

        with ThreadPoolExecutor(max_workers=6) as exec:
            result = exec.map(_process_image, var_dict[f])


def process_image(path, dst):
    """
    Centre crop and resize
    :param path: input image path
    :param dst: output directory
    :return: None
    """
    # shutil.copy(path, dst)

    transform = Compose([CenterCrop(299),
                         Resize(224)])
    img = Image.open(os.path.abspath(path))
    img = transform(img)

    out_path = os.path.join(os.path.abspath(dst), '/'.join(path.split('/')[-2:]))
    img.save(out_path)


def main(args):
    if args.tarInput:
        assert args.tarOutput is not None
        extract_tar(args.tarInput, args.tarOutput)

    if args.image_dir:
        assert args.output_dir is not None
        split_folder(args.image_dir, args.output_dir, val_num=N_VAL, test_size=TEST_SIZE, random_state=42)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Extract and process dataset')
    parser.add_argument('--tarInput', type=str, help='path for tar file')
    parser.add_argument('--tarOutput', type=str, help='path for tar output')
    parser.add_argument('--image_dir', type=str, help='input dataset folder')
    parser.add_argument('--output_dir', type=str, help='output dataset folder')

    args = parser.parse_args()

    main(args)

