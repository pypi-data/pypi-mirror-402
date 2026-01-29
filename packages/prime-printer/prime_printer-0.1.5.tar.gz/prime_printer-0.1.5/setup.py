from setuptools import setup
import os

# relative links to absolute
with open("./README.md", "r", encoding="utf-8") as f:
    readme = f.read()
readme = readme.replace('src="logo.png"', 'src="https://raw.githubusercontent.com//prime_printer/v_01/logo.png"')
readme = readme.replace('src="./res/example_colored_delay_sound_print.gif"', 'src="https://raw.githubusercontent.com//prime_printer/v_01/res/example_colored_delay_sound_print.gif"')
readme = readme.replace('src="./res/example_game_menu.gif"', 'src="https://raw.githubusercontent.com//prime_printer/v_01/res/example_game_menu.gif"')
readme = readme.replace('src="./res/example_input_with_condition.gif"', 'src="https://raw.githubusercontent.com//prime_printer/v_01/res/example_input_with_condition.gif"')
readme = readme.replace('src="./res/example_image_print.gif"', 'src="https://raw.githubusercontent.com//prime_printer/v_01/res/example_image_print.gif"')
readme = readme.replace('src="./res/example_progress_bar_1.gif"', 'src="https://raw.githubusercontent.com//prime_printer/v_01/res/example_progress_bar_1.gif"')
readme = readme.replace('src="./res/example_progress_bar_2.gif"', 'src="https://raw.githubusercontent.com//prime_printer/v_01/res/example_progress_bar_2.gif"')
readme = readme.replace('src="./res/example_progress_bar_3.gif"', 'src="https://raw.githubusercontent.com//prime_printer/v_01/res/example_progress_bar_3.gif"')

setup(
  name = 'prime_printer',         # How you named your package folder (MyLib)
  packages = ['prime_printer'],   # Chose the same as "name"
  include_package_data=True,
  version = '0.1.5',      # Start with a small number and increase it with every change you make
  license='MIT',        # Chose a license from here: https://help.github.com/articles/licensing-a-repository
  description = 'Console I/O Helper - Print Awesome. Make It Prime.',   # Give a short description about your library
  long_description = readme,
  long_description_content_type='text/markdown',
  author = 'Tobia Ippolito',                   # Type in your name
  url = 'https://github.com//prime_printer',   # Provide either the link to your github or to your website
  download_url = 'https://github.com//prime_printer/archive/refs/tags/v_08.zip',    
  keywords = ['Printing', 'Helper'],   # Keywords that define your package best
  install_requires=[            # used libraries
          'climage',
          'pygame',
          'opencv-python',
          'numpy',
          'matplotlib',
          'IPython',
          'psutil',
          'gputil',
          'py-cpuinfo',
          'setuptools',
          'sympy'
      ],
  platform=[
    'Windows',
    'Linux'
  ],
  classifiers=[
    'Development Status :: 4 - Beta',      # Chose either "3 - Alpha", "4 - Beta" or "5 - Production/Stable" as the current state of your package
    'Intended Audience :: Developers',      # Define that your audience are developers
    'Topic :: Software Development :: Build Tools',
    # 'License :: OSI Approved :: MIT License',   # Again, pick a license (https://autopilot-docs.readthedocs.io/en/latest/license_list.html)
    'Programming Language :: Python :: 3.7',
    'Programming Language :: Python :: 3.8',
    'Programming Language :: Python :: 3.9',      # Specify which pyhton versions that you want to support
    'Programming Language :: Python :: 3.10',
    'Programming Language :: Python :: 3.11',
    'Programming Language :: Python :: 3.12',
    'Programming Language :: Python :: 3.13'
  ],
)


