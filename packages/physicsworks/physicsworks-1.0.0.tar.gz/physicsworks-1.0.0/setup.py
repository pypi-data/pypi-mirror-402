import setuptools

setuptools.setup(name="physicsworks",
                 version="1.0.0",
                 author="PhysicsWorks",
                 author_email="contact@physicsworks.io",
                 description="PhysicsWorks Python Runner - Simulation execution and post-processing framework",
                 packages=setuptools.find_packages(),
                 classifiers=[
                     "Programming Language :: Python :: 3",
                     "License :: OSI Approved :: MIT License",
                     "Operating System :: OS Independent",
                 ],
                 python_requires='>=3.6',
                 install_requires=[
                     'setuptools',
                     'packaging',
                     'GPUtil',
                     'numpy',
                     'psutil',
                     'python-slugify',
                     'PyYAML',
                     'requests',
                     'text-unidecode',
                     'urllib3',
                     'watchdog',
                     'Pillow'
                 ])
