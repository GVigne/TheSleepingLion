from setuptools import setup, find_namespace_packages
from pathlib import Path

setup(name='thesleepinglion',
    version='1.1.0',
    description='Automatic card layout creation for Gloomhaven custom classes',
    long_description=Path("README.md").read_text("utf8"),
    long_description_content_type='text/markdown',
    author='Guillaume Vigne',
    license='MIT',
    package_dir = {'' : 'src'},
    packages=find_namespace_packages('src'),
    zip_safe=False,
    install_requires = ['numpy', 'PyGObject', 'pyyaml', 'cairosvg', 'regex', 'manimpango'],
    entry_points = {'console_scripts':
                    ['thesleepinglion = thesleepinglion.main:thesleepinglion_main']},

    package_data = {'thesleepinglion.background_assets' : ["*.png", "*.svg*"],
                    'thesleepinglion.assets' : ["*.png","*.svg*"],
                    'thesleepinglion.assets.aoe' : ["*.aoe"],
                    'thesleepinglion.assets.fonts' : ["*.ttf"],
                    'thesleepinglion.docs' : ["*.pdf", "*.gml"],
                    'thesleepinglion.gui' : ["*.glade"],
                    'thesleepinglion.gui_images' : ["*.png"],
                    },

    include_package_data = True)
