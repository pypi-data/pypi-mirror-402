from setuptools import setup, find_packages

setup(
    name="quillsql",
    version="2.2.8",
    packages=find_packages(),
    install_requires=[
        "psycopg2-binary",
        "requests",
        "redis",
        "python-dotenv",
        "pytest",
        "google-cloud-bigquery",
        "google-auth",
    ],
    author="Quill",
    author_email="shawn@quill.co",
    description="Quill SDK for Python.",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/quill-sql/quill-python",
)
