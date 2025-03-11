from setuptools import setup, find_packages

def get_requirements(file_path):
    '''
    this function will return the list of requirements
    '''
    requirements=[]
    with open(file_path) as file_obj:
        requirements=file_obj.readlines()
        requirements=[req.replace("\n","") for req in requirements]
    return requirements

setup(
name='AI_powered_Fashion_Designing_Agent',
version='1.0',
author='Manohhar Swarna',
author_email='manohharswarnaus@gmail.com',
packages=find_packages(),
install_requires=get_requirements('requirements.txt')

)