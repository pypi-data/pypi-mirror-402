import setuptools

setuptools.setup(
  name='pyredengine',
  version='1.0.0',
  description='A simple pygame game engine',
  long_description=open('README.txt').read() + '\n\n' + open('CHANGELOG.txt').read(),
  project_urls={
    'Source': 'https://github.com/RedEgs/PyRedEngine',
    'Roadmap': 'https://trello.com/b/310qwZMs/pyredengine',
    
  },
  author='RedEgs',
  author_email='tothemuun21@gmail.com',
  license='MIT', 
  classifiers = [
    'Development Status :: 5 - Production/Stable',
    'Intended Audience :: Education',
    'Operating System :: Microsoft :: Windows :: Windows 10',
    'License :: OSI Approved :: MIT License',
    'Programming Language :: Python :: 3.9',
  ],
  keywords='engine', 
  packages=setuptools.find_packages(),
  install_requires=['pygame-ce', 'pytweening', 'numpy'], 
  python_requires = "> 3.8",
  include_package_data=True,
  entry_points = {"console_scripts": ["pyredengine-newproject = pyredengine.tools.cli:setup_project"]},
)
