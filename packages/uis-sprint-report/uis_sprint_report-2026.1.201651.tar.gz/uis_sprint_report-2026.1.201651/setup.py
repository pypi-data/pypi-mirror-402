from setuptools import setup, find_packages


setup(
    name='uis-sprint-report',
    version='2026.01.201651',
    author='Eugene Evstafev',
    author_email='ee345@cam.ac.uk',
    description='A Python package for generating sprint reports and managing sprint activities at University Information Services.',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://gitlab.developers.cam.ac.uk/ee345/demo',
    packages=find_packages(),
    install_requires=[
        'click>=8.1.7',
        'rich>=13.7.1',
        'python-pptx>=0.6.23',
        'huggingface-hub==0.23.4',
        'langchain==0.2.6',
        'langchain-community==0.2.6',
        'langchain-core==0.2.10',
        'langchain-huggingface==0.0.3',
        'langchain-text-splitters==0.2.2',
        'faiss-cpu>=1.8.0',
        'pydantic>=2.7.4',
        'scikit-learn>=0.24.1',
        'torch>=1.9.0',
        'transformers>=4.42.3',
        'ollama==0.2.1',
        'get-gitlab-issues'
    ],
    entry_points={
        'console_scripts': [
            'uis-sprint-report=demo.main:demo'
        ]
    },
    classifiers=[
        'License :: OSI Approved :: MIT License',
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Programming Language :: Python :: 3',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.7',
)