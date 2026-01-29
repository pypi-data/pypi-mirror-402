
import subprocess
from setuptools import setup, Extension

subprocess.call(['make', 'clean'])
subprocess.call(['make'])

leechcorepyc = Extension(
    'leechcorepyc.leechcorepyc',
    sources = ['leechcorepyc.c', 'leechcorepyc_barrequest.c', 'oscompatibility.c'],
    libraries = ['usb-1.0', ':leechcore.so'],
    library_dirs = ['.'],
    define_macros = [("LINUX", "")],
    include_dirs = ["includes", "/usr/include/libusb-1.0/"],
    extra_compile_args=["-I.", "-L.", "-l:leechcore.so", "-shared", "-fPIC", "-fvisibility=hidden"],
    extra_link_args=["-Wl,-rpath,$ORIGIN", "-g", "-ldl", "-shared"],
    py_limited_api=True
    )

setup(
    name='leechcorepyc',
    version='2.22.6', # VERSION_END
    description='LeechCore for Python',
    long_description='LeechCore for Python : native extension for physical memory access',
    url='https://github.com/ufrisk/LeechCore',
    author='Ulf Frisk',
    author_email='pcileech@frizk.net',
    license='GNU General Public License v3.0',
    platforms='manylinux1_x86_64',
    python_requires='>=3.6',
    classifiers=[
		"Programming Language :: C",
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: POSIX :: Linux",
    ],
	packages=['leechcorepyc'],
	package_data={'leechcorepyc': ['leechcore.so', 'leechcore_ft601_driver_linux.so', 'leechcore_device_qemu.so', 'leechcore_device_rawtcp.so', 'libMSCompression.so']},
    ext_modules = [leechcorepyc],
    )

