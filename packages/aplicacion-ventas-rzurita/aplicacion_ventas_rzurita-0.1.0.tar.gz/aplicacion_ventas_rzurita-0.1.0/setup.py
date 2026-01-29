from setuptools import setup,find_packages

setup(name='aplicacion_ventas_rzurita',
      version='0.1.0',
      author='Russel Zurita Quijano',
      author_email='rzurita02@gmail.com',
      description='Paquete para gestionar ventas, precios, etc.',
      long_description=open('README.md').read(), 
      long_description_content_type='text/markdown',
      url='https://github.com/rzurita02/python/',
      packages=find_packages(),
      install_requires=[],
      classifiers=[
        "Programming Language :: Python :: 3.13",
        "Operating System :: OS Independent",
    ],
      python_requires='>=3.7'
      )
