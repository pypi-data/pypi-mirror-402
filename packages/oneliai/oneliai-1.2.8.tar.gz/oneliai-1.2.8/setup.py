# from setuptools import setup, find_packages

# setup(
#     name='oneliai',
#     version='0.1',
#     packages=find_packages(),
#     install_requires=[
#         'requests>=2.31.0',
#         'PyJWT>=2.8.0'
#     ],
#     author='Your Name',
#     author_email='your.email@example.com',
#     description='SDK for AI Customer API',
#     url='https://github.com/your-repo/ai-customer-sdk'
# )


from setuptools import setup, find_packages

setup(
    name='oneliai',  
    version="1.2.8",          
    author="oneli.ai",
    description='SDK for ONELI.AI Customer API',
    # long_description=open("README.md").read(),
    # long_description_content_type="text/markdown",
    packages=find_packages(),   
    install_requires=[          
        "requests",
    ],
    python_requires=">=3.6",    
)