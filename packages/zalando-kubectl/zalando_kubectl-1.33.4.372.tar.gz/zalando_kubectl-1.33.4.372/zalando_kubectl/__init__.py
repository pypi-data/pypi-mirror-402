import importlib.metadata


APP_NAME = "zalando-kubectl"

KUBECTL_VERSION = "v1.33.4"
KUBECTL_SHA512 = {
    "linux": "e628239516ed6a3d07d47b451b7f42199fb5dcfb4d416f7b519235fd454e0fca3d0c273cc9c709f653a935a32c1f9fbd0a4be88f4c59d0ddcd674be2c289c8a5",
    "darwin": "ecd902e004a072eaa92d60ce81635519aaa93553313c808c0d27d15a07a1164b0cd586e271fe979e731e167daaed8b8816010bd018cb0ff16dcde9a46dcf0736",
}
STERN_VERSION = "1.30.0"
STERN_SHA256 = {
    "linux": "ea1bf1f1dddf1fd4b9971148582e88c637884ac1592dcba71838a6a42277708b",
    "darwin": "4eaf8f0d60924902a3dda1aaebb573a376137bb830f45703d7a0bd89e884494a",
}
KUBELOGIN_VERSION = "v1.35.2"
KUBELOGIN_SHA256 = {
    "linux": "40ccbc12a9d47ad6416ac111cbc895ed01d3cf2cad33454f1d3a035d6c21135a",
    "darwin": "b342e08b9eab45a650907c2587e418569f715ed3ba47a67dc0a73ab8f180423e",
}
ZALANDO_AWS_CLI_VERSION = "1.1.2"
ZALANDO_AWS_CLI_SHA256 = {
    "linux": "d0dc1bbbab2a5c94d5e16aa8d90f38d40dc16c03fc552ed03c57871b6ec33c2c",
    "darwin": "baae4a2b2b738f34bfa7202eb56448ded76b8ef3cca1a8990f9f334978be63f2",
}

APP_VERSION = "v" + importlib.metadata.version(APP_NAME)
