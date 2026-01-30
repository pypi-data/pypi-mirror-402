from setuptools import setup
from pathlib import Path

this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding="utf-8")

xdevice_dep = "6.0.7.206"

setup(
    name="hypium",
    version="6.0.7.210",
    description="A UI test framework for HarmonyOS devices",
    long_description=long_description,
    long_description_content_type='text/markdown',
    license="",
    packages=['hypium',
              'hypium.action',
              'hypium.action.app',
              'hypium.action.host',
              'hypium.action.device',
              'hypium.checker',
              'hypium.advance',
              'hypium.advance.deveco_testing',
              'hypium.uidriver.interface',
              'hypium.uidriver.ohos',
              'hypium.uidriver.common',
              'hypium.uidriver.uitree',
              'hypium.uidriver.uitree.widget_finder',
              'hypium.model',
              'hypium.uidriver',
              'hypium.utils',
              'hypium.webdriver',
              "hypium.dfx",
              "hypium.docs"],
    package_data={
        "hypium": ["dfx/*.md", "dfx/data", "docs/*.md"],
    },
    install_requires=[
        "psutil",
        "lxml",
        "opencv-python",
        f"xdevice>={xdevice_dep}",
        f"xdevice-ohos>={xdevice_dep}",
        f"xdevice-devicetest>={xdevice_dep}"
    ],
    extras_require={
        "advance": ["opencv-python"],
        "qr": ["pyzbar", "qrcode"]
    },
    include_package_data=True
)
