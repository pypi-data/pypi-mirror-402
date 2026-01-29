from setuptools import find_packages, setup

# import thorpy
# print("VERSION", thorpy.__version__)

version = "2.1.13"
# assert thorpy.__version__ == version #security control

setup(name='thorpy',
      version=version,
      description='GUI library for pygame',
      long_description='ThorPy is a non-intrusive, straightforward GUI kit for Pygame.',
      long_description_content_type="text/plain",
      author='Yann Thorimbert',
      author_email='yann.thorimbert@gmail.com',
      url='http://www.thorpy.org/',
      keywords=['pygame', 'gui', 'menus', 'buttons', 'widgets', 'user interface', 'toolkit'],
      packages=find_packages(),
      include_package_data=True,
      package_data={
          'thorpy': ['data/*', 'py.typed'],
      },
      license='MIT',
      license_files=[]) # empêche l'injection License-File

