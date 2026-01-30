from setuptools import setup

setup(name='gromologist',
      version='0.330',
      description='Library to handle various GROMACS-related stuff',
      author='Milosz Wieczor',
      author_email='milafternoon@gmail.com',
      license='GNU GPLv3',
      packages=['gromologist'],
      install_requires=['numpy>=1.10.0'],
      entry_points={
        'console_scripts': [
            # command-name = package.module:function
            'gml-report-timings = gromologist.Gmx:report_timings',
            'gml-hydrogen-mass-repartitioning = gromologist.Utils:hydrogen_mass_repartitioning',
            'gml-grid-of-movies = gromologist.Utils:make_grid_movies',
            'gml-make-index = gromologist.Gmx:make_index',
            'gml-interpolate-structures = gromologist.Pdb:ext_interpolate_structures',
          ]
      },
      zip_safe=False)
