import os
import glob


def remove_retain():
    to_remove = glob.glob(os.path.join(os.getcwd(), '**/.retain'), recursive=True)
    for f in to_remove:
        try:
            os.remove(f)
        except OSError:
            print(f'Error while attempting to delete {f}')


def rename_gitignore():
    src = os.path.join(os.getcwd(), 'gitignore.txt')
    dst = os.path.join(os.getcwd(), '.gitignore')
    os.rename(src, dst)


if __name__ == '__main__':
    remove_retain()
    rename_gitignore()
