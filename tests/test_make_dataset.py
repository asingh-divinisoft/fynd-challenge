from src.data import make_dataset

def test_extract():
    assert make_dataset.extract_tar('', '../data/raw') != 0