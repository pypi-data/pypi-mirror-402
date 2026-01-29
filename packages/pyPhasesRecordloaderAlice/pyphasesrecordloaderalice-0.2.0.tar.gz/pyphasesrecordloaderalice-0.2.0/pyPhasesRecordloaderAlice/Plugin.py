from pyPhases import PluginAdapter
from pyPhasesRecordloader import RecordLoader


class Plugin(PluginAdapter):
    def initPlugin(self):
        # self.project.loadConfig(self.project.loadConfig(pathlib.Path(__file__).parent.absolute().joinpath("config.yaml")))
        module = "pyPhasesRecordloaderAlice"
        rlPath = f"{module}.recordLoaders"
        RecordLoader.registerRecordLoader("RecordLoaderAlice", rlPath)
        RecordLoader.registerRecordLoader("AliceRMLLoader", rlPath)
        alicePath = self.getConfig("alice-path")
        self.project.setConfig("loader.alice.filePath", alicePath)
