import os
import shutil


def delete_empty_ext(ext_path: str, f_count: int) -> bool:
    # remove empty EQ-Py directory if it exists
    p = os.path.join(os.getcwd(), ext_path)
    if os.path.exists(p):
        fs = [x for x in os.listdir(p)]
        if len(fs) < f_count:
            shutil.rmtree(p, ignore_errors=True)
            return True

    return False


def run():
    to_remove = [os.path.join(os.getcwd(), "common")]
    for path in to_remove:
        shutil.rmtree(path)

    # remove empty EQ-Py directory if it exists
    delete_empty_ext('ext/EQ-Py', 2)
    if delete_empty_ext('ext/EQ-R/src', 3):
        p = os.path.join(os.getcwd(), 'ext/EQ-R')
        shutil.rmtree(p, ignore_errors=True)

if __name__ == '__main__':
    run()
