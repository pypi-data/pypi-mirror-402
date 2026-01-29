from ..._configs.maps import ChangelingMaps
from ...core.content_managers.templates.bind_template import BindTemplate
from ...core.game_content.utils.triggers.trigger_mixin import _TriggerEnjoyer
from .rotating_bind import RotatingBind


class _ChangelingRotatingBind(_TriggerEnjoyer, RotatingBind):
    FORM: dict

    def __init__(
        self,
        trigger: str,
        power_rotation: list[str],
        is_silent: bool = True,
        absolute_path_links: bool = False,
    ):
        _TriggerEnjoyer.__init__(self, trigger)
        RotatingBind.__init__(
            self,
            is_silent=is_silent,
            absolute_path_links=absolute_path_links,
            loop_delay=1,
        )
        self.power_rotation = power_rotation
        self.changeling_template: BindTemplate = BindTemplate(trigger)

    def _build_bind_files(self):
        self._build_changeling_bind_template(self.changeling_template)
        self.add_bind_template(self.changeling_template, execute_on_up_press=True)
        return super()._build_bind_files()

    def _build_changeling_bind_template(self, template: BindTemplate):
        form_list, power_list = self._get_changeling_lists()
        template.add_toggle_off_power_pool(form_list)
        template.add_toggle_on_power_pool(form_list)
        template.add_power_pool(power_list)

    def _get_changeling_lists(self):
        form_list = []
        power_list = []
        for power in self.power_rotation:
            self.throw_error_if_unknown_form_power(power)
            form_list.append(self.FORM[power])
            power_list.append(f"{self.FORM[power]} {power}")
        return form_list, power_list

    def throw_error_if_unknown_form_power(self, power: str):
        if power.lower().strip() not in self.FORM:
            raise ValueError(
                f"Unknown kheldian power: '{power}', valid powers: {list(self.FORM.keys())}"
            )


class ChangelingWarshade(_ChangelingRotatingBind):
    FORM = ChangelingMaps.WS_FORMS


class ChangelingPeaceBringer(_ChangelingRotatingBind):
    FORM = ChangelingMaps.PB_FORMS
