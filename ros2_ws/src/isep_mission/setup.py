from setuptools import find_packages, setup

package_name = "isep_mission"

setup(
    name=package_name,
    version="0.1.0",
    packages=find_packages(exclude=["test"]),
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml"]),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="Équipe AIR ISEP",
    maintainer_email="equipe-air@isep.fr",
    description="Machine à états de mission du drone isep_vtol",
    license="MIT",
    tests_require=["pytest"],
    entry_points={"console_scripts": ["mission_node = isep_mission.mission_node:main"]},
)
