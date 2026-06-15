import os
import pyzipper

def make_zip(files, zip_name, password):
    with pyzipper.AESZipFile(zip_name, 'w', compression=pyzipper.ZIP_LZMA, encryption=pyzipper.WZ_AES) as zf:
        zf.setpassword(password.encode())

        for file_path in files:
            file_name = os.path.basename(file_path)   # <- keeps only filename
            zf.write(file_path, arcname=file_name)    # <- overrides path inside ZIP

files = ["C:/Temp/VNK-Grafana-Tokens.txt", "C:/Temp/VAB-VC-Defects.txt", "C:/Temp/tst/VAB-VC-tst.txt"]
make_zip(files, "C:/Temp/secured.zip", "MyStrongPassword123")
