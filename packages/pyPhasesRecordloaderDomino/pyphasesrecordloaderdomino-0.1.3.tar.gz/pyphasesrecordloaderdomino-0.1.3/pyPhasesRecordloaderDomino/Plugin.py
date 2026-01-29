from pyPhases import PluginAdapter
from pyPhasesRecordloader import RecordLoader


class Plugin(PluginAdapter):
    def initPlugin(self):
        # self.project.loadConfig(self.project.loadConfig(pathlib.Path(__file__).parent.absolute().joinpath("config.yaml")))
        module = "pyPhasesRecordloaderDomino"
        rlPath = f"{module}.recordLoaders"
        RecordLoader.registerRecordLoader("RecordLoaderDomino", rlPath)
        RecordLoader.registerRecordLoader("DominoAnnotationLoader", rlPath)
        dominoPath = self.getConfig("domino-path")
        self.project.setConfig("loader.domino.filePath", dominoPath)
