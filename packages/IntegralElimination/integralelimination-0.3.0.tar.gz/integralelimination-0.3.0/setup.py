from setuptools import setup

setup(
    name="IntegralElimination",
    version="0.3.0",  
    packages=['IntegralElimination'],
    install_requires=[
        "ordered-set>=4.1.0",
        "sympy>=1.11.1", 
        "typing>=3.7.4.3",
        "IPython",
        "numpy"
    ],
    author="Louis ROUSSEL",
    author_email="louis.roussel@univ-lille.fr",
    description="Algorithm for performing integral elimination for nonlinear integral equations",
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url="https://codeberg.org/louis-roussel/IntegralElimination", 
    # sympy needs python 3.8 but
    # the type annotations like tuple[IM, sp.Expr] requires
    # python 3.9
    python_requires='>=3.9', 
)
