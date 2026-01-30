def getFileHandle(filepath, encoding):

    while True:
        try:
            if encoding is None:
                outfile = open(filepath, 'w', newline='',errors='ignore')
            else:
                outfile = open(filepath, 'w', newline='', errors='ignore', encoding=encoding)
            break
        except PermissionError:
            print(f'{filepath} may be locked by other programs. please release it then press Enter to try again')
            input()

    return outfile



