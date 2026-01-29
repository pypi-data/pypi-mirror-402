from abc import ABC, abstractmethod

class PatternMiner(ABC):
    def __init__(self, inputFile: str):
        self.inputFile = inputFile
        self.miner = None  # To be initialized in run()

    def showDBstats(self):
        db = self._create_database()
        db.run()
        db.printStats()
        db.plotGraphs()

    @abstractmethod
    def _create_database(self):
        """Returns the appropriate database object (Transactional or Temporal)."""
        pass

    @abstractmethod
    def run(self, *args, **kwargs):
        """Run the mining algorithm with specific parameters."""
        pass

    def printPatterns(self):
        if self.miner is not None:
            return self.miner.getPatterns()
        else:
            print("No mining results to print. Please execute run() method first.")

    def save(self, outputFile: str):
        if self.miner is not None:
            self.miner.save(outputFile)
            print(f"Frequent patterns saved to: {outputFile}")
        else:
            print("No mining results to save. Please execute run() method first.")

    def getDataframe(self):
        if self.miner is not None:
            return self.miner.getPatternsAsDataFrame()
        else:
            print("No mining results to save. Please execute run() method first.")
