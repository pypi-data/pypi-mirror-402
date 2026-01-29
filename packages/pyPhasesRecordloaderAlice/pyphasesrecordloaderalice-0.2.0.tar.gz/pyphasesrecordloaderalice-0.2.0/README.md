# Extension for pyPhasesRecordloader



## Usage

In a phase you can access the data through the `RecordLoader`:

Add the plugins and config values to your project.yaml::

```yaml
name: AliceProject
plugins:
  - pyPhasesML
  - pyPhasesRecordloaderAlice
  - pyPhasesRecordloader

phases:
  - name: MyPhase

config:
  alice-path: C:/datasets/recordings

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