from ..._configs.constants import SafeInstallValues
from ..game_content.bind_file.bind_file import BindFile
from ..game_content.macros.macro_image import MacroImage


class InstallFiles:
    def create_install_file(self) -> BindFile:
        load_macro = self._create_load_macro()
        unload_macro = self._create_unload_macro()

        install_file = BindFile()
        install_file.add_macro(load_macro)
        install_file.add_macro(unload_macro)

        return install_file

    def _create_load_macro(self) -> MacroImage:
        return MacroImage(
            SafeInstallValues.LOAD_MACRO_IMAGE, SafeInstallValues.LOAD_MACRO_NAME
        )

    def _create_unload_macro(self) -> MacroImage:
        return MacroImage(
            SafeInstallValues.UNLOAD_MACRO_IMAGE, SafeInstallValues.UNLOAD_MACRO_NAME
        )

    def create_load_file(self) -> BindFile:
        load_file = BindFile()
        return load_file

    def create_unload_file(self) -> BindFile:
        unload_file = BindFile()
        return unload_file
