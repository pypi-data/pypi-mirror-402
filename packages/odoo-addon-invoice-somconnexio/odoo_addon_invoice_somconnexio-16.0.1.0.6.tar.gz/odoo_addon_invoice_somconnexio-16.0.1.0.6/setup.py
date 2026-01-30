import setuptools

setuptools.setup(
    setup_requires=['setuptools-odoo'],
    odoo_addon={
        "external_dependencies_override": {
            "python": {
                "pyopencell": "pyopencell==0.4.10",
                "b2sdk": "b2sdk==2.5.0",
                "bi_sc_client": "bi_sc_client==0.0.5",
            }
        }
    },
)
