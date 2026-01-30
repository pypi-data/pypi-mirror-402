from setuptools import setup, find_packages

setup(
    name="pardon-dance",
    version="1769073.596.343",
    description="High-quality integration for https://supermaker.ai/video/blog/unlocking-the-magic-of-pardon-dance-the-viral-video-effect-taking-over-social-media/",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    author="SuperMaker",
    url="https://supermaker.ai/video/blog/unlocking-the-magic-of-pardon-dance-the-viral-video-effect-taking-over-social-media/",
    packages=find_packages(),
    python_requires=">=3.6",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
    ],
)
