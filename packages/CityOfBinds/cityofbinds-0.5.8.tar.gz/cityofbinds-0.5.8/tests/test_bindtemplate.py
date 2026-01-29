from CityOfBinds import BindTemplate


class TestBindTemplate:
    def test_bindtemplate(self):
        # assemble
        powers = ["dark nova blast", "dark Nova bolt", "dark nova emmanation"]
        bind_template = (
            BindTemplate("1")
            .add_toggle_off_power("super speed")
            .add_toggle_off_power("sprint")
            .add_toggle_on_power("dark nova")
            .add_power_pool(powers)
            .add_toggle_off_power("dark nova")
        )

        # act/assert
        assert (
            str(bind_template.build())
            == '1 "powexectoggleoff super speed$$powexectoggleoff sprint$$powexectoggleon dark nova$$powexecname dark nova blast$$powexectoggleoff dark nova"'
        )
        assert (
            str(bind_template.build())
            == '1 "powexectoggleoff super speed$$powexectoggleoff sprint$$powexectoggleon dark nova$$powexecname dark nova bolt$$powexectoggleoff dark nova"'
        )
        assert (
            str(bind_template.build())
            == '1 "powexectoggleoff super speed$$powexectoggleoff sprint$$powexectoggleon dark nova$$powexecname dark nova emmanation$$powexectoggleoff dark nova"'
        )
