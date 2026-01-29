from setuptools import setup, find_packages

setup(
    name='ryans-891',      # <--- GANTI INI BIAR UNIK! (Cek di pypi.org dulu ada gak)
    version='0.0.1',             # Versi awal
    description='Library Banner Khusus untuk Bot Discord Ryans',
    author='Ryans',
    packages=find_packages(),    # Ini akan otomatis mencari folder 'ryans'
    install_requires=[
        'colorama',              # Otomatis install colorama kalau orang install ini
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
)
