import whitebox


class WhiteboxPluginTelegraf(whitebox.Plugin):
    name = "Hardware Monitoring"

    provides_capabilities = ["hardware-monitoring"]


plugin_class = WhiteboxPluginTelegraf
