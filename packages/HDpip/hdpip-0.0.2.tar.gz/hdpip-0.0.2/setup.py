import setuptools
 
with open("HDpip\\README.md", 'r', encoding="utf8") as f:
    long_description = f.read()
    
setuptools.setup(
    name = "HDpip",
    version = "0.0.2",
    author = "寒冬利刃(handongliren(hdlr))", 
    author_email = "1079489986@qq.com", 
    description = "寒冬pip(HDpip)", 
    long_description = long_description, 
    long_description_content_type = "text/Markdown", 
    license = "MPL-2.0", 
    url = "https://gitee.com/handongliren", 
    packages = setuptools.find_packages(), 
    package_data = {
        "HDpip": ["*"], 
    }, 
    python_requires = ">=3.10", 
    install_requires = [
        "pip>=25.2", 
        "maliang[opt]>=3.1.0", 
        "pyyaml", 
        "pipdeptree>=2.0.0", 
    ], 
    keywords = ["pip", "gui", "maliang", "hdlr", "寒冬利刃", "handongliren"], 
    classifiers = [
        "Development Status :: 1 - Planning", 
        "Intended Audience :: Developers", 
        "License :: OSI Approved :: Mozilla Public License 2.0 (MPL 2.0)", 
        "Intended Audience :: Developers", 
        "Operating System :: OS Independent", 
        "Programming Language :: Python :: 3.10", 
        "Programming Language :: Python :: 3.11", 
        "Programming Language :: Python :: 3.12", 
        "Programming Language :: Python :: 3.13", 
        "Programming Language :: Python :: 3.14", 
        "Topic :: Software Development :: Build Tools", 
    ], 
    entry_points = {
        "console_scripts": [
            "HDpip=HDpip.main:main", 
            "hdpip=HDpip.main:main", 
        ], 
    }, 
)