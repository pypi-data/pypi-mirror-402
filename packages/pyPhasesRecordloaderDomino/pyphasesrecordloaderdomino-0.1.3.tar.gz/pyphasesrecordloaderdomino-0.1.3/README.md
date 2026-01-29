# Extension for pyPhasesRecordloader



## Usage

In a phase you can access the data through the `RecordLoader`:

Add the plugins and config values to your project.yaml:

```yaml
name: DominoProject
plugins:
  - pyPhasesML
  - pyPhasesRecordloaderDomino
  - pyPhasesRecordloader

phases:
  - name: MyPhase

config:
  domino-path: C:/datasets/recordings

```

In a phase (`phases/MyPhase.py`) you can access the records using the `RecordLoader`:

```python
from pyPhasesRecordloader import RecordLoader
from pyPhases import Phase

class MyPhase(Phase):
    def run(self):
      recordIds = recordLoader.getRecordList()
      for recordId in recordIds:
        record = recordLoader.getRecord(recordId)
```

Run your project with `python -m phases run MyPhase`.


The RecordLoader requires EDF files (using the EDF export), annotations (using the annotation export) and ERG files from the raw Domino data. An example of our setup can be found at https://gitlab.com/sleep-is-all-you-need/dominodatasetcreator.